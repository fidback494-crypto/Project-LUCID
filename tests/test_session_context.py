"""다시 연 대화에서 압축 세션이 모델에 전달되고 같은 원문을 명령으로 읽을 수 있는지 검사한다."""

import json
import os
import unittest
from contextlib import closing, redirect_stdout
from datetime import datetime, timedelta
from functools import partial
from io import StringIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

from lucid.app import LucidEngine
from lucid.memory.store import LongTermMemory


class SessionContextTests(unittest.TestCase):
    """시작·검색·프롬프트·화면 출력을 함께 거치는 대화 흐름을 확인한다."""

    def test_reopened_session_uses_summary_and_can_display_original(self):
        """새 세션에 발췌 요약을 전달하고 보관된 긴 원문은 요청 시 전체를 표시한다."""
        with (
            TemporaryDirectory() as directory,
            patch.dict(
                os.environ,
                {"LUCID_DATA_DIR": directory, "LUCID_BROWSER_TOKEN": "test-only"},
                clear=True,
            ),
        ):
            when = (datetime.now() - timedelta(days=10)).isoformat()
            original = "관측 계획을 정했어. " + "밤하늘 " * 200 + "원문 끝 표시"
            with closing(LongTermMemory()) as store:
                store.store_conversation_episode(original, "기록할게.", created_at=when)

            screen = StringIO()
            engine = LucidEngine(output=partial(print, file=screen))
            engine.browser_bridge.port = 0
            response = json.dumps(
                {
                    "reply": "이전 관측 계획을 이어 가자.",
                    "intent": "conversation",
                    "experience": "반가움",
                    "meaning": "지난 계획을 떠올림",
                    "speech_style": "warm",
                },
                ensure_ascii=False,
            )
            with (
                patch.object(engine.cognitive.client, "preload", return_value=True),
                patch.object(engine.voice, "start"),
                patch.object(
                    engine.cognitive.client, "generate", return_value=response
                ) as generate,
                redirect_stdout(StringIO()),
            ):
                try:
                    engine.boot()
                    self.assertTrue(engine.handle_input("지난 관측 계획을 이어 가자."))
                    messages = generate.call_args.args[0]
                    current = messages[-1]
                    self.assertEqual(current["role"], "user")
                    self.assertIn("관측 계획을 정했어", current["content"])
                    self.assertTrue(
                        current["content"].endswith("지난 관측 계획을 이어 가자.")
                    )
                    self.assertNotIn(original, str(messages))
                    self.assertFalse(
                        engine.workspace.current().related_conversation_episodes
                    )
                    self.assertIn("LUCID >", screen.getvalue())

                    session = engine.long_memory.session_summaries("관측 계획")[0]
                    self.assertTrue(engine.handle_input("/memory sessions 관측 계획"))
                    self.assertIn(f"#{session['id']}", screen.getvalue())
                    self.assertTrue(
                        engine.handle_input(f"/memory session {session['id']}")
                    )
                    self.assertIn(original, screen.getvalue())
                    self.assertFalse(engine.handle_input("exit"))
                finally:
                    engine.shutdown()
