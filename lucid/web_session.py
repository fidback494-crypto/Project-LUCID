"""브라우저 탭들이 한 대화 작업자를 공유하도록 입력 순서, 출력 기록, 작업자 수명을 관리한다."""

import multiprocessing
import os
import signal
from collections import deque
from multiprocessing.connection import wait
from queue import Full
from threading import Lock, Thread
from uuid import uuid4

from lucid.interactive import run_engine
from lucid.settings import DEFAULT_OLLAMA_URL, MODEL_NAME

MAX_EVENTS = 256
MAX_EVENT_CHARS = 16_384
STOP_GRACE_SECONDS = 6


def _display_text(text):
    """표시 기록에 들어갈 긴 문자열을 길이 제한 안에서 자른다."""
    if len(text) <= MAX_EVENT_CHARS:
        return text
    marker = "\n… (이전 출력의 일부를 생략했습니다)"
    return text[: MAX_EVENT_CHARS - len(marker)] + marker


class _EventWriter:
    """엔진 및 주변 작업 스레드의 출력을 동시에 섞이지 않게 단방향 파이프로 보낸다."""

    def __init__(self, connection):
        """출력 전용 파이프와 이 프로세스의 쓰기 잠금을 보관한다."""
        self.connection = connection
        self.lock = Lock()

    def put(self, event):
        """공용 작업자가 보낸 상태 또는 문자열을 UI 수집기로 전달한다."""
        kind, text = event
        with self.lock:
            self.connection.send((kind, _display_text(text)))


def _serve_engine(settings, model, debug, commands, writer, stopping):
    """별도 프로세스 환경에 모델 설정을 적용하고 공용 대화 작업자를 실행한다."""
    # 터미널에서 누른 Ctrl+C는 부모 서버가 받아 close()로 작업자를 정리한다.
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    os.environ["LUCID_OLLAMA_MODEL"] = model
    # 생성 시점과 spawn 시점 사이에 부모 환경의 음성 인증값이 바뀔 수 있다.
    for name in ("LUCID_TTS_TOKEN", "LUCID_UTAUTTS_TOKEN"):
        os.environ.pop(name, None)
    with writer:
        run_engine(settings, debug, commands, _EventWriter(writer), stopping)


class WebSession:
    """브라우저 새로고침과 여러 요청 스레드 사이에서 유지되는 단일 대화 세션."""

    def __init__(self, debug=False):
        """환경의 서버·음성·모델 설정을 캡처한다. 실제 작업자는 start에서 시작한다."""
        self._debug = debug
        self._model = os.getenv("LUCID_OLLAMA_MODEL", "").strip() or MODEL_NAME
        self._settings = (
            os.getenv("LUCID_OLLAMA_URL", "").strip() or DEFAULT_OLLAMA_URL,
            os.getenv("LUCID_TTS_URL") or os.getenv("LUCID_UTAUTTS_URL") or None,
            os.getenv("LUCID_TTS_TOKEN") or os.getenv("LUCID_UTAUTTS_TOKEN") or "",
            os.getenv("LUCID_TTS_SPEAKER") or "Sohee",
        )
        self._id = uuid4().hex
        self._lock = Lock()
        self._lifecycle = Lock()
        self._status = "starting"
        self._events = deque(maxlen=MAX_EVENTS)
        self._cursor = 0
        self._started = False
        self._closed = False
        self._worker = self._commands = self._stopping = self._reader = None

    def _append(self, kind, text):
        """상태 잠금을 가진 호출자가 보낸 UI 이벤트에 단조 증가 번호를 부여한다."""
        self._cursor += 1
        self._events.append(
            {"id": self._cursor, "kind": kind, "text": _display_text(text)}
        )

    def start(self):
        """spawn으로 엔진을 한 번만 시작하고 브라우저 폴링과 독립적으로 출력을 수집한다."""
        with self._lifecycle:
            if self._started or self._closed:
                return
            self._started = True
            context = multiprocessing.get_context("spawn")
            reader = writer = None
            try:
                self._commands = context.Queue(maxsize=1)
                self._stopping = context.Event()
                reader, writer = context.Pipe(duplex=False)
                self._worker = context.Process(
                    name="LUCIDWebEngine",
                    target=_serve_engine,
                    args=(
                        self._settings,
                        self._model,
                        self._debug,
                        self._commands,
                        writer,
                        self._stopping,
                    ),
                )
                self._worker.start()
                writer.close()
                self._reader = Thread(
                    target=self._collect,
                    args=(reader, self._worker),
                    name="lucid-web-events",
                    daemon=True,
                )
                self._reader.start()
            except (OSError, RuntimeError, ValueError) as error:
                if writer is not None:
                    writer.close()
                if reader is not None:
                    reader.close()
                self._shutdown_worker()
                self._release()
                with self._lock:
                    self._status = "failed"
                    self._append("error", f"대화 엔진을 시작하지 못했습니다. {error}")

    def _collect(self, reader, worker):
        """상태·출력을 순서대로 반영하고 예기치 않은 작업자 종료를 브라우저에 알린다."""
        try:
            with reader:
                while True:
                    kind, text = reader.recv()
                    with self._lock:
                        if kind in {"log", "output", "error"}:
                            self._append(kind, text)
                        elif (
                            kind == "ready"
                            and not self._closed
                            and self._status in {"starting", "busy"}
                        ):
                            self._status = "ready"
                        elif kind == "quit":
                            self._status = "stopped"
                        elif kind == "failed":
                            self._status = "failed"
                            self._append("error", text)
        except (EOFError, OSError):
            pass
        # 파이프를 닫자마자 작업자가 아직 종료 절차에 있을 수 있다.
        wait([worker.sentinel])
        with self._lock:
            worker.join(0)
            if not self._closed and self._status not in {"failed", "stopped"}:
                self._status = "failed"
                self._append(
                    "error",
                    f"대화 작업자가 예기치 않게 종료되었습니다 (종료 코드 {worker.exitcode}).",
                )

    def submit(self, text):
        """대화 가능한 동안 하나의 명령을 수락한다. 빈 입력이나 사용 중인 세션은 False다."""
        if not isinstance(text, str) or not (text := text.strip()):
            return False
        with self._lock:
            if self._closed or self._status != "ready":
                return False
            try:
                self._commands.put_nowait(text)
            except (Full, OSError, ValueError):
                return False
            self._status = "busy"
            self._append("user", text)
            return True

    def snapshot(self, after=0):
        """커서 이후 이벤트와 상태를 복사한다. 보관 범위 밖 커서는 전체 보관분으로 재설정한다."""
        with self._lock:
            oldest = self._events[0]["id"] if self._events else 1
            reset = (
                not isinstance(after, int) or not oldest - 1 <= after <= self._cursor
            )
            return {
                "status": self._status,
                "cursor": self._cursor,
                "reset": reset,
                "events": [e.copy() for e in self._events if reset or e["id"] > after],
                "session": self._id,
                "model": self._model,
            }

    def _shutdown_worker(self):
        """정상 종료 시간을 준 뒤 멈추지 않은 자식만 terminate·kill 순으로 회수한다."""
        worker = self._worker
        if worker is None or worker.pid is None:
            return
        self._stopping.set()
        try:
            self._commands.put_nowait(None)
        except Full:
            # 이미 승인한 입력이 작업자를 깨우며 작업자는 명령 처리 전 중단 플래그를 본다.
            pass
        if not wait([worker.sentinel], timeout=STOP_GRACE_SECONDS):
            worker.terminate()
            if not wait([worker.sentinel], timeout=1):
                worker.kill()
                if not wait([worker.sentinel], timeout=2):
                    raise RuntimeError("대화 작업자 종료를 확인할 수 없습니다.")

    def _release(self):
        """마지막 이벤트까지 모은 뒤 프로세스 핸들과 입력 큐를 닫는다."""
        if self._reader is not None and self._reader.ident is not None:
            self._reader.join()
        if self._worker is not None:
            if self._worker.pid is not None:
                self._worker.join(0)
            self._worker.close()
        if self._commands is not None:
            self._commands.cancel_join_thread()
            self._commands.close()
        self._worker = self._reader = self._commands = self._stopping = None

    def close(self):
        """새 입력을 막고 작업자를 회수한다. 수집된 기록은 브라우저에서 계속 읽을 수 있다."""
        with self._lifecycle:
            with self._lock:
                if self._closed and self._worker is None:
                    return
                self._closed = True
                if self._status != "failed":
                    self._status = "stopped"
            self._shutdown_worker()
            self._release()
