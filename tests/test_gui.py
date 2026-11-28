"""GUI 작업자가 대화 명령·오류·종료를 직렬 처리하는지 외부 화면이나 모델 없이 검증한다."""

import os
import sys
import unittest
from queue import Empty, Queue
from threading import Event
from unittest.mock import patch

from lucid.cli import apply_tts_settings, normalize_server_url
from lucid.gui import main
from lucid.interactive import run_engine
from lucid.log import Logger


class GuiWorkerTests(unittest.TestCase):
    """GUI가 사용하는 엔진 계약과 서버별 토큰 처리를 검사한다."""

    def setUp(self):
        """검사 종료 후 원래 환경과 로그 설정을 복원한다."""
        self.addCleanup(Logger.configure, Logger._debug, Logger._output)
        self.environment = patch.dict(os.environ, {
            "LUCID_TTS_URL": "https://previous.example", "LUCID_TTS_TOKEN": "old",
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def test_commands_and_shutdown_share_one_engine(self):
        """대화·명령·종료가 같은 엔진으로 순서대로 가고 마지막에 한 번 정리된다."""
        calls, commands, events = [], Queue(), Queue()
        settings = ("http://localhost:11434", "https://next.example", "", "Sohee")

        class Engine:
            def __init__(self, output):
                self.output = output
                calls.append("init")

            def boot(self):
                calls.append("boot")
                Logger.notice("브라우저 준비")

            def handle_input(self, command):
                calls.append(command)
                self.output("처리", command, sep=" · ")
                return command != "exit"

            def shutdown(self):
                calls.append("shutdown")

        for value in ("안녕", "/tools", "exit"):
            commands.put(value)
        run_engine(settings, False, commands, events, Event(), Engine)
        actual = []
        while True:
            try:
                actual.append(events.get_nowait())
            except Empty:
                break
        self.assertEqual(calls, ["init", "boot", "안녕", "/tools", "exit", "shutdown"])
        self.assertEqual(actual.count(("ready", "")), 3)
        self.assertIn(("output", "처리 · /tools\n"), actual)
        self.assertIn(("log", "브라우저 준비\n"), actual)
        self.assertEqual(actual[-1], ("quit", ""))
        self.assertNotIn("LUCID_TTS_TOKEN", os.environ)

    def test_boot_failure_reaches_window_and_cleans_resources(self):
        """초기화 오류가 GUI로 전달되며 처리 명령을 기다리지 않고 정리한다."""
        cleaned, events = Event(), Queue()

        class Engine:
            def __init__(self, output):
                pass

            def boot(self):
                raise RuntimeError("부팅 실패")

            def shutdown(self):
                cleaned.set()

        run_engine(("http://localhost", "https://previous.example", "", "Sohee"),
                    False, Queue(), events, Event(), Engine)
        self.assertEqual(events.get_nowait(), ("failed", "RuntimeError: 부팅 실패"))
        self.assertTrue(cleaned.is_set())
        self.assertEqual(os.environ.get("LUCID_TTS_TOKEN"), "old")

    def test_gui_and_cli_server_validation(self):
        """GUI와 콘솔에서 쓰는 같은 검사기가 유효 주소를 정리하고 잘못된 주소를 거부한다."""
        self.assertEqual(normalize_server_url(" http://localhost:11434/ "), "http://localhost:11434")
        for value in ("localhost", "http://user:pass@host", "https://host:99999"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_server_url(value)


    def test_unset_voice_address_keeps_implicit_local_default(self):
        """GUI에서 음성 주소를 비워 두면 기본 로컬 주소가 명시 설정으로 잘못 기록되지 않는다."""
        apply_tts_settings(None, "", "Sohee")
        self.assertNotIn("LUCID_TTS_URL", os.environ)
        self.assertNotIn("LUCID_UTAUTTS_URL", os.environ)
        self.assertNotIn("LUCID_TTS_TOKEN", os.environ)

    def test_gui_explains_missing_tk(self):
        """Tk가 없는 Python에서는 콘솔로 실행하는 방법을 표시한다."""
        with patch.dict(sys.modules, {"tkinter": None}), self.assertRaisesRegex(SystemExit, "GUI = False"):
            main()
