"""실제 spawn과 임시 설정으로 웹 세션을 검사한다. 모델과 사용자 기억을 열지 않는다."""

import os
import signal
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from multiprocessing import active_children
from tempfile import TemporaryDirectory
from threading import Barrier
from unittest.mock import patch

from lucid.settings import MODEL_NAME
from lucid.web_session import MAX_EVENT_CHARS, MAX_EVENTS, WebSession, _EventWriter
from tests.test_model_config import _model_server


def _test_worker(settings, model, debug, commands, writer, stopping):
    """테스트 프로세스에서 준비·응답·오류·중단을 결정적으로 재현한다."""
    with writer:
        events = _EventWriter(writer)
        if model == "startup-failure":
            events.put(("failed", "모의 부팅 실패"))
            return
        events.put(("log", f"{model} / {settings[0]} / debug={debug}"))
        events.put(("ready", ""))
        while not stopping.is_set():
            command = commands.get()
            if command is None or stopping.is_set():
                break
            if command == "exit":
                events.put(("quit", ""))
                return
            if command == "crash":
                return
            if command == "hold":
                stopping.wait()
                return
            if command == "hang":
                events.put(("output", "처리 중"))
                time.sleep(30)
                return
            if command == "/burst":
                for index in range(MAX_EVENTS + 5):
                    events.put(("output", str(index)))
                events.put(("output", "가" * (MAX_EVENT_CHARS + 300)))
            else:
                events.put(("output", f"엔진: {command}"))
            events.put(("ready", ""))


class WebSessionTests(unittest.TestCase):
    """같은 세션에 대한 여러 브라우저 요청과 작업자 수명 주기를 검증한다."""

    def setUp(self):
        """각 테스트에 별도 데이터 경로를 지정한다."""
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        config = patch.dict(os.environ, {"LUCID_DATA_DIR": directory.name})
        config.start()
        self.addCleanup(config.stop)

    def _start(self, model="test-model"):
        """모델 설정을 캡처한 세션을 시작해 정리 함수에 등록한다."""
        with patch.dict(
            os.environ,
            {"LUCID_OLLAMA_MODEL": model, "LUCID_OLLAMA_URL": "http://localhost:12345"},
        ):
            session = WebSession(debug=True)
        self.addCleanup(session.close)
        with patch("lucid.web_session._serve_engine", _test_worker):
            session.start()
        return session

    def _until(self, session, condition):
        """spawn 시작 지연을 허용하면서 요청한 상태 또는 이벤트를 기다린다."""
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            state = session.snapshot()
            if condition(state):
                return state
            time.sleep(0.01)
        self.fail(
            f"세션 상태를 기다리는 시간이 초과되었습니다: {session.snapshot()['status']}"
        )

    def test_refresh_commands_and_exit(self):
        """기존 대화 명령과 출력 순서가 새 폴링 요청 및 종료 후에도 보존된다."""
        session = self._start()
        initial = self._until(session, lambda state: state["status"] == "ready")
        self.assertIn("http://localhost:12345", initial["events"][0]["text"])
        self.assertEqual(initial["model"], "test-model")
        session.start()
        for command in (" 안녕 ", "/memory history"):
            self.assertTrue(session.submit(command))
            self._until(session, lambda state: state["status"] == "ready")
        fresh = session.snapshot()
        delta = session.snapshot(initial["cursor"])
        self.assertEqual(delta["session"], initial["session"])
        self.assertFalse(delta["reset"])
        self.assertEqual(
            [e["kind"] for e in delta["events"]], ["user", "output", "user", "output"]
        )
        self.assertEqual(
            [e["text"] for e in delta["events"]],
            ["안녕", "엔진: 안녕", "/memory history", "엔진: /memory history"],
        )
        self.assertEqual(fresh["cursor"], initial["cursor"] + 4)
        delta["events"][0]["text"] = "복사본 변경"
        self.assertEqual(
            session.snapshot(initial["cursor"])["events"][0]["text"], "안녕"
        )
        self.assertFalse(session.submit("   "))
        self.assertTrue(session.submit("exit"))
        self._until(session, lambda state: state["status"] == "stopped")
        self.assertFalse(session.submit("다음 입력"))
        session.close()
        self.assertEqual(session.snapshot()["events"][-1]["text"], "exit")

    def test_concurrent_submission_has_one_winner(self):
        """여러 탭이 같은 준비 상태를 보고 보내도 하나만 큐와 사용자 기록에 추가된다."""
        session = self._start()
        self._until(session, lambda state: state["status"] == "ready")
        gate = Barrier(8)

        def submit():
            gate.wait(timeout=3)
            return session.submit("hold")

        with ThreadPoolExecutor(max_workers=8) as pool:
            attempts = [pool.submit(submit) for _ in range(8)]
            self.assertEqual(sum(f.result(timeout=4) for f in attempts), 1)
        state = session.snapshot()
        self.assertEqual(state["status"], "busy")
        self.assertEqual(
            [e["text"] for e in state["events"] if e["kind"] == "user"], ["hold"]
        )

    def test_truncated_history_resets_stale_and_future_cursors(self):
        """오래된 커서를 재설정하고, 보관 범위 안의 커서에는 다음 이벤트만 반환한다."""
        session = self._start()
        self._until(session, lambda state: state["status"] == "ready")
        self.assertTrue(session.submit("/burst"))
        state = self._until(session, lambda state: state["status"] == "ready")
        self.assertTrue(state["reset"])
        self.assertEqual(len(state["events"]), MAX_EVENTS)
        self.assertEqual(len(state["events"][-1]["text"]), MAX_EVENT_CHARS)
        ids = [e["id"] for e in state["events"]]
        self.assertEqual(ids, list(range(ids[0], state["cursor"] + 1)))
        for old in (-1, ids[0] - 2, state["cursor"] + 100):
            self.assertEqual(session.snapshot(old), state)
        self.assertFalse(session.snapshot(ids[0] - 1)["reset"])
        self.assertEqual(session.snapshot(ids[-1] - 1)["events"], state["events"][-1:])
        self.assertEqual(session.snapshot(ids[-1])["events"], [])

    def test_startup_failure_and_unexpected_worker_exit(self):
        """부팅 실패와 예기치 않은 종료는 사용자에게 읽을 수 있는 오류로 남는다."""
        failed = self._start("startup-failure")
        state = self._until(failed, lambda state: state["status"] == "failed")
        self.assertEqual(state["events"][-1]["kind"], "error")
        self.assertIn("부팅 실패", state["events"][-1]["text"])
        self.assertFalse(failed.submit("재시도"))
        crashed = self._start()
        self.assertNotEqual(crashed.snapshot()["session"], failed.snapshot()["session"])
        self._until(crashed, lambda state: state["status"] == "ready")
        self.assertTrue(crashed.submit("crash"))
        self.assertEqual(
            self._until(crashed, lambda state: state["status"] == "failed")["events"][
                -1
            ]["kind"],
            "error",
        )

    def test_close_can_stop_a_worker_blocked_inside_a_turn(self):
        """응답 대기 중인 작업자는 제한 시간 후 종료하고 반복 close에도 자식이 남지 않는다."""
        session = self._start()
        self._until(session, lambda state: state["status"] == "ready")
        worker_pid = session._worker.pid
        self.assertTrue(session.submit("hang"))
        self._until(
            session, lambda state: any(e["text"] == "처리 중" for e in state["events"])
        )
        with patch("lucid.web_session.STOP_GRACE_SECONDS", 0.05):
            session.close()
        session.close()
        self.assertNotIn(worker_pid, {worker.pid for worker in active_children()})
        self.assertEqual(session.snapshot()["status"], "stopped")

    def test_close_before_start_and_default_model(self):
        """명시적 모델이 없으면 기본값을 쓰고 시작 전에 닫은 세션은 입력을 받지 않는다."""
        with patch.dict(os.environ, {"LUCID_OLLAMA_MODEL": ""}):
            session = WebSession()
        self.assertEqual(session.snapshot()["model"], MODEL_NAME)
        self.assertFalse(session.submit("/tools"))
        session.close()
        session.start()
        self.assertEqual(session.snapshot()["status"], "stopped")

    def test_shared_engine_process_handles_commands_after_terminal_interrupt(self):
        """실제 작업자가 부모 전용 Ctrl+C를 넘기고 명령·대화·종료까지 처리한다."""
        with _model_server() as (server, url):
            env = {
                "LUCID_OLLAMA_URL": url,
                "LUCID_OLLAMA_MODEL": "fixture:session",
                "LUCID_TTS_URL": url,
                # 바인딩된 테스트 포트를 사용해 기존 사용자 브리지와 격리한다.
                "LUCID_BROWSER_PORT": str(server.server_port),
                "LUCID_BROWSER_TOKEN": "test-session-token",
                "NO_PROXY": "127.0.0.1",
            }
            with patch.dict(os.environ, env), closing(WebSession()) as session:
                session.start()
                self._until(session, lambda s: s["status"] == "ready")
                if os.name == "posix":
                    os.kill(session._worker.pid, signal.SIGINT)
                for command, expected in (
                    ("/tools", "calculator"),
                    ("반가워", "LUCID >"),
                ):
                    self.assertTrue(session.submit(command))
                    state = self._until(session, lambda s: s["status"] == "ready")
                    self.assertTrue(
                        any(
                            expected in e["text"]
                            for e in state["events"]
                            if e["kind"] == "output"
                        )
                    )
                self.assertTrue(session.submit("exit"))
                self._until(session, lambda s: s["status"] == "stopped")
                self.assertTrue(
                    any(
                        path == "/api/chat" and body.get("model") == "fixture:session"
                        for path, body in server.calls
                    )
                )
