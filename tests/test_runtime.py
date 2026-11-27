"""로그 출력, 추론 입력, 턴 사이의 작업 공간 초기화를 검증한다."""

import re
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from lucid.core.state import BrainState
from lucid.core.workspace import Workspace
from lucid.log import Logger
from lucid.mind.models import Reason
from lucid.mind.observation import Observation
from lucid.mind.reasoning import ReasoningEngine
from lucid.persona import SelfModel


class LoggerTests(unittest.TestCase):
    """두 출력 모드에서 진단 로그와 사용자 안내가 보이는 조건을 검사한다."""

    def setUp(self):
        """각 검사에서 변경한 전역 출력 모드를 종료 후 복원한다."""
        self.addCleanup(Logger.configure, Logger._debug)

    def _capture_messages(self, debug):
        """같은 메시지들을 지정한 모드로 출력하고 줄 단위로 반환한다."""
        Logger.configure(debug)
        output = StringIO()
        with redirect_stdout(output):
            Logger.info("LUCID Online")
            Logger.warning("Memory Offline")
            Logger.error("Camera Error")
            Logger.notice("브라우저 연결 안내")
        return output.getvalue().splitlines()

    def test_quiet_mode_keeps_user_notice(self):
        """일반 모드에서는 사용자 안내 하나만 원문 그대로 출력된다."""
        self.assertEqual(self._capture_messages(False), ["브라우저 연결 안내"])

    def test_debug_mode_labels_logs_and_notice(self):
        """상세 모드에서는 시각과 정확한 수준이 붙고 안내도 한 번만 출력된다."""
        expected = [
            "[INFO] LUCID Online",
            "[WARNING] Memory Offline",
            "[ERROR] Camera Error",
            "[INFO] 브라우저 연결 안내",
        ]
        actual = self._capture_messages(True)
        self.assertEqual(len(actual), len(expected))
        for line, message in zip(actual, expected):
            with self.subTest(message=message):
                self.assertRegex(
                    line, r"^\[\d{2}:\d{2}:\d{2}\] " + re.escape(message) + "$"
                )


class ReasoningTests(unittest.TestCase):
    """실제 프롬프트 생성과 응답 파싱 사이에서 모델 호출만 대체한다."""

    def test_reason_from_observation_and_memory(self):
        """관찰·기억·자기 모델을 갖춘 상태에서 인사 의도와 신뢰도를 읽는다."""
        state = BrainState(
            observation=Observation(source="user", content="안녕, 오늘 또 왔어."),
            self_model=SelfModel(),
            working_memory=[
                Observation(source="user", content="지난번에는 비가 왔어.")
            ],
            long_memory=["사용자는 맑은 날을 좋아한다."],
            conversation=[{"role": "assistant", "content": "다음에 또 봐."}],
        )
        engine = ReasoningEngine()
        self.addCleanup(engine.stop)
        model_reply = (
            "Category: greeting\nReason: 다시 만나 인사했다.\nConfidence: 0.92"
        )
        with patch.object(
            engine.client, "generate", return_value=model_reply
        ) as generate:
            reason = engine.process(state)

        self.assertEqual(
            reason,
            Reason(summary="다시 만나 인사했다.", intent="greeting", confidence=0.92),
        )
        generate.assert_called_once()
        (messages,) = generate.call_args.args
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["role"], "system")
        for text in (
            state.observation.content,
            state.working_memory[0].content,
            state.long_memory[0],
            state.conversation[0]["content"],
        ):
            with self.subTest(text=text):
                self.assertIn(text, messages[0]["content"])


class WorkspaceTests(unittest.TestCase):
    """새 턴에서 이어지는 객체와 비워지는 상태를 검사한다."""

    def test_clear_preserves_identity_and_reuses_memory_lists(self):
        """자기 모델과 공유 목록의 참조를 보존하고 지난 턴의 내용만 지운다."""
        model = SelfModel()
        conversation = [{"role": "user", "content": "이전 대화"}]
        working = ["최근 관찰"]
        long_memory = ["관련 사실"]
        state = Workspace(
            self_model=model,
            conversation=conversation,
            working_memory=working,
            long_memory=long_memory,
            observation=Observation("user", "이전 메시지"),
            response="이전 답변",
            voice_response="이전 음성",
            speech_style="warm",
            action_result="이전 결과",
            visual_observation="이전 장면",
            related_conversation_episodes=[{"id": 3}],
            cognitive_success=True,
        )
        state.clear()
        self.assertIs(state.self_model, model)
        self.assertIs(state.conversation, conversation)
        self.assertIs(state.working_memory, working)
        self.assertIs(state.long_memory, long_memory)
        self.assertEqual(state, Workspace(self_model=model))
