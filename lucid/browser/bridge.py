"""페어링 토큰을 확인한 뒤 로컬 브라우저가 공유한 페이지와 화면을 받는다."""

import json
import os
import secrets
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from requests import RequestException

from lucid.log import Logger
from lucid.settings import data_directory
from lucid.vision import VisionClient


class _RequestHandler(BaseHTTPRequestHandler):
    """로컬 확장의 공유 요청을 검증해 서버에 연결된 저장소에 전달한다."""

    def _reply(self, status, payload=None):
        """HTTP 상태와 선택적인 본문을 받아 JSON 응답을 보낸다."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        origin = self.headers.get("Origin", "")
        if origin.startswith("chrome-extension://"):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.end_headers()
        if payload is not None:
            self.wfile.write(json.dumps(payload).encode())

    def do_OPTIONS(self):
        """확장이 전송할 수 있는 HTTP 메서드와 헤더를 반환한다."""
        self._reply(204)

    def do_POST(self):
        """JSON 본문의 토큰을 검증하고 화면 공유 또는 중지 결과를 반환한다."""
        if self.path not in {"/context", "/stop", "/click-target"}:
            self._reply(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 7_000_000:
                raise ValueError("invalid payload size")
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError("expected a JSON object")

            bridge = self.server.bridge
            token = payload.get("token")
            if not isinstance(token, str) or not secrets.compare_digest(
                token.encode(), bridge.token.encode()
            ):
                self._reply(403, {"error": "invalid token"})
                return

            if self.path == "/click-target":
                self._select_click_target(payload)
                return

            session_id = payload.get("session_id", "")
            if not isinstance(session_id, str) or len(session_id) > 128:
                raise ValueError("invalid session id")
            if self.path == "/stop":
                bridge.store.stop_continuous(session_id)
            else:
                image = payload.get("image_base64", "")
                continuous = payload.get("continuous", False)
                if not isinstance(image, str) or len(image) > 6_500_000:
                    raise ValueError("invalid image")
                if not isinstance(continuous, bool) or (continuous and not image):
                    raise ValueError("invalid capture state")
                context = bridge.store.update(
                    title=payload.get("title", ""),
                    url=payload.get("url", ""),
                    text=payload.get("text", ""),
                    selection=payload.get("selection", ""),
                    image_base64=image,
                    image_mime=payload.get("image_mime", "image/jpeg"),
                    continuous=continuous,
                    session_id=session_id,
                )
                if not context.continuous:
                    Logger.info(
                        f"[Browser] Page shared: {context.title or context.url}"
                    )
        except (ValueError, RecursionError):
            self._reply(400, {"error": "invalid request"})
            return
        self._reply(200, {"ok": True})

    def _select_click_target(self, payload):
        """한 번의 선택 요청을 검증해 모델이 고른 후보 번호만 반환한다. 캡처는 저장하지 않는다."""
        image = payload.get("image_base64")
        instruction = payload.get("instruction")
        labels = payload.get("candidates")
        if not isinstance(image, str) or not 0 < len(image) <= 6_500_000:
            raise ValueError("invalid image")
        if not isinstance(instruction, str) or not 0 < len(instruction.strip()) <= 500:
            raise ValueError("invalid instruction")
        if not isinstance(labels, list) or not 1 <= len(labels) <= 60:
            raise ValueError("invalid candidates")
        if not all(
            isinstance(label, str) and 0 < len(label) <= 180 for label in labels
        ):
            raise ValueError("invalid candidate label")
        candidates = [
            {"번호": index, "이름": label}
            for index, label in enumerate(labels, start=1)
        ]
        client = VisionClient()
        try:
            target = client.select_click_target(image, instruction.strip(), candidates)
        except (RequestException, ValueError):
            self._reply(502, {"error": "비전 모델 연결 또는 응답을 확인해 줘."})
            return
        finally:
            client.close()
        self._reply(200, {"target": target})

    def log_message(self, _format, *_args):
        """기본 HTTP 로그를 생략하고 공유 이벤트만 애플리케이션 로그에 남긴다."""


class BrowserBridge:
    """로컬 HTTP 서버를 열고 입력을 지정된 PageContextStore에 전달한다."""

    def __init__(self, store):
        """공유 데이터를 받을 저장소와 로컬 포트·인증 토큰을 준비한다."""
        self.store = store
        try:
            port = int(os.getenv("LUCID_BROWSER_PORT", "8765"))
            self.port = port if 1 <= port <= 65535 else 8765
        except ValueError:
            self.port = 8765
        self.token = self._load_token()
        self._server = None
        self._thread = None

    @staticmethod
    def _data_directory():
        """설정된 데이터 디렉터리를 만들고 절대 또는 사용자 지정 경로를 반환한다."""
        directory = data_directory()
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def _load_token(self):
        """설정된 토큰이나 저장한 토큰을 반환하고 빈 토큰 파일은 안전하게 교체한다."""
        configured = os.getenv("LUCID_BROWSER_TOKEN", "").strip()
        if configured:
            return configured
        token_file = self._data_directory() / "browser_bridge_token.txt"
        try:
            saved = token_file.read_text(encoding="utf-8").strip()
            if saved:
                return saved
        except (FileNotFoundError, UnicodeDecodeError):
            pass

        token = secrets.token_urlsafe(24)
        with tempfile.NamedTemporaryFile(
            mode="w", dir=token_file.parent, encoding="utf-8", delete=False
        ) as staged:
            staged.write(token)
        temporary = Path(staged.name)
        try:
            try:
                os.link(temporary, token_file)
            except FileExistsError:
                # 동시에 다른 프로세스가 먼저 유효한 토큰을 기록했으면 그 값을 공유한다.
                try:
                    saved = token_file.read_text(encoding="utf-8").strip()
                except UnicodeDecodeError:
                    saved = ""
                if saved:
                    return saved
                temporary.replace(token_file)
            except OSError:
                # 하드 링크를 지원하지 않는 파일시스템에서도 콘솔의 임시 토큰으로 페어링한다.
                Logger.warning("[Browser] 페어링 토큰을 이번 실행에서만 사용합니다.")
        finally:
            temporary.unlink(missing_ok=True)
        return token

    def start(self):
        """루프백 주소에서 서버를 시작하고 브라우저에 입력할 포트와 토큰을 표시한다."""
        if self._server is not None:
            return
        try:
            self._server = ThreadingHTTPServer(
                ("127.0.0.1", self.port), _RequestHandler
            )
        except OSError as error:
            Logger.notice(
                f"[Browser] Local bridge could not start on port {self.port}: {error}"
            )
            return

        self._server.bridge = self
        self._thread = threading.Thread(
            target=self._server.serve_forever, name="LUCIDBrowserBridge", daemon=True
        )
        self._thread.start()
        Logger.info(f"[Browser] Local bridge started: 127.0.0.1:{self.port}")
        Logger.notice(f"[Browser] Pair token: {self.token}")

    def stop(self):
        """HTTP 요청 접수를 중단하고 서버 포트와 작업 스레드를 정리한다."""
        if self._server is None:
            return
        self._server.shutdown()
        self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=2)
        self._server = None
        self._thread = None
        Logger.info("[Browser] Local bridge stopped")
