"""같은 컴퓨터의 브라우저에 LUCID 대화 페이지와 세션 API를 제공한다."""

import errno
import json
import signal
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

from lucid.web_session import WebSession

_ASSETS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
}
_MAX_BODY_BYTES = 64 * 1024
_MAX_MESSAGE_LENGTH = 8000


class ChatServer(ThreadingHTTPServer):
    """정적 화면과 동일 출처의 요청을 한 대화 세션에 연결하는 루프백 서버."""

    def __init__(self, port: int, session: WebSession):
        """정적 파일을 미리 읽고 지정한 로컬 포트를 연다. 0이면 빈 포트를 배정한다."""
        directory = Path(__file__).with_name("web_ui")
        self.assets = {
            route: ((directory / filename).read_bytes(), content_type)
            for route, (filename, content_type) in _ASSETS.items()
        }
        self.session = session
        super().__init__(("127.0.0.1", port), _Handler)
        self.authorities = {
            f"127.0.0.1:{self.server_port}",
            f"localhost:{self.server_port}",
        }
        if self.server_port == 80:
            self.authorities.update({"127.0.0.1", "localhost"})


class _Handler(BaseHTTPRequestHandler):
    """페이지와 JSON API를 제공하고 로컬 페이지에서 보낸 메시지만 세션에 전달한다."""

    server: ChatServer
    timeout = 10

    def _send(self, status: int, content_type: str, body: bytes) -> None:
        """상태 코드와 콘텐츠 유형, 본문 바이트를 캐시 없이 응답한다."""
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; frame-ancestors 'none'; "
            "base-uri 'none'; form-action 'none'; object-src 'none'",
        )
        try:
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            # 새로고침으로 이미 닫힌 응답은 다음 상태 조회에서 다시 전달한다.
            self.close_connection = True

    def _json(self, status: int, value: dict) -> None:
        """객체를 UTF-8 JSON 응답으로 보낸다."""
        self._send(
            status,
            "application/json; charset=utf-8",
            json.dumps(value, ensure_ascii=False).encode("utf-8"),
        )

    def _is_local_request(self) -> bool:
        """Host와 브라우저가 보낸 출처가 이 서버의 주소를 가리키는지 검사한다."""
        host = self.headers.get("Host", "").lower()
        origin = self.headers.get("Origin")
        landing = self.command == "GET" and self.path.partition("?")[0] == "/"
        if (
            host not in self.server.authorities
            or (origin is not None and origin != f"http://{host}")
            or (self.headers.get("Sec-Fetch-Site") == "cross-site" and not landing)
        ):
            self._json(403, {"error": "터미널에 표시한 로컬 주소에서 열어 주세요."})
            return False
        return True

    def do_GET(self) -> None:
        """HTML·CSS·JS 또는 지정한 이벤트 번호 이후의 대화 상태를 반환한다."""
        if not self._is_local_request():
            return
        route, _, query = self.path.partition("?")
        if route in self.server.assets:
            body, content_type = self.server.assets[route]
            self._send(200, content_type, body)
        elif route == "/api/state":
            try:
                params = parse_qs(query, max_num_fields=4, keep_blank_values=True)
                after = int(params.get("after", ["0"])[0])
                if after < 0:
                    raise ValueError
            except ValueError:
                self._json(400, {"error": "이벤트 번호가 올바르지 않습니다."})
                return
            self._json(200, self.server.session.snapshot(after))
        else:
            self._json(404, {"error": "페이지를 찾을 수 없습니다."})

    def do_POST(self) -> None:
        """단일 사용자 메시지를 검사해 엔진이 준비됐을 때 큐에 추가한다."""
        if not self._is_local_request():
            return
        if self.path != "/api/message":
            self._json(404, {"error": "경로를 찾을 수 없습니다."})
            return
        if self.headers.get("X-Lucid-Client") != "web":
            self._json(403, {"error": "LUCID 대화 페이지에서 보내 주세요."})
            return
        if self.headers.get_content_type() != "application/json":
            self._json(415, {"error": "JSON 형식의 메시지가 필요합니다."})
            return
        try:
            size = int(self.headers.get("Content-Length", ""))
        except ValueError:
            size = -1
        if size < 0 or size > _MAX_BODY_BYTES:
            self._json(
                413 if size > _MAX_BODY_BYTES else 400,
                {"error": "요청 크기를 확인해 주세요."},
            )
            return
        try:
            payload = json.loads(self.rfile.read(size).decode("utf-8"))
            text = payload.get("text") if isinstance(payload, dict) else None
            if (
                not isinstance(text, str)
                or not text.strip()
                or len(text) > _MAX_MESSAGE_LENGTH
            ):
                raise ValueError
            # UTF-8로 표현할 수 있는 발화만 로그와 SQLite에 저장한다.
            text.encode("utf-8")
        except (ValueError, RecursionError):
            self._json(400, {"error": "1~8,000자의 메시지를 입력해 주세요."})
            return
        if not self.server.session.submit(text.strip()):
            self._json(409, {"error": "엔진 상태를 확인한 뒤 다시 보내 주세요."})
            return
        self._json(202, {"accepted": True})

    def log_message(self, format, *args) -> None:
        """상태 조회가 반복되어도 콘솔에 매 요청을 출력하지 않는다."""


def main(*, debug: bool = False, port: int = 8787, open_browser: bool = True) -> None:
    """세션을 시작하고 로컬 페이지를 제공한다. 종료 시 HTTP 서버와 엔진을 함께 닫는다."""
    session = WebSession(debug=debug)
    try:
        server = ChatServer(port, session)
    except OSError as error:
        if error.errno == errno.EADDRINUSE:
            raise SystemExit(
                f"포트 {port}를 사용 중입니다. --port 8788처럼 다른 포트를 지정해 주세요."
            ) from None
        raise

    def interrupt(signum, frame):
        """종료 신호를 받으면 서버 루프를 빠져나와 작업 프로세스를 정리한다."""
        raise KeyboardInterrupt

    with server:
        previous = signal.signal(signal.SIGTERM, interrupt)
        try:
            session.start()
            url = f"http://127.0.0.1:{server.server_port}/"
            print(
                f"LUCID 웹 대화  {url}\n종료하려면 이 터미널에서 Ctrl+C를 누르세요.",
                flush=True,
            )
            if open_browser:
                threading.Thread(
                    target=webbrowser.open, args=(url,), daemon=True
                ).start()
            server.serve_forever(poll_interval=0.2)
        except KeyboardInterrupt:
            pass
        finally:
            try:
                session.close()
            finally:
                signal.signal(signal.SIGTERM, previous)
