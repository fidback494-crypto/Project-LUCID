"""관찰과 기억을 바탕으로 사용자 입력의 의도를 분류한다."""

from lucid.language.ollama import OllamaModule
from lucid.log import Logger
from lucid.mind.models import Reason
from lucid.mind.reasoning_prompt import ReasoningPrompt


class ReasoningEngine(OllamaModule):
    """관찰과 기억을 바탕으로 사용자 입력의 의도를 분류한다."""

    def __init__(self):
        """모델 세션과 의도 분류 프롬프트 생성기를 준비한다."""
        super().__init__()
        self.prompt = ReasoningPrompt()

    def _parse_response(self, reply):
        """Category, Reason, Confidence 항목을 읽어 의도와 신뢰도가 담긴 Reason을 반환한다."""
        intent = "conversation"
        summary = "사용자의 의도를 분석했다."
        confidence = 0.8

        mapping = {
            "question": "question",
            "greeting": "greeting",
            "conversation": "conversation",
            "request": "request",
            "emotion": "emotion",
            "exit": "exit",
        }

        for line in reply.splitlines():
            line = line.strip()

            if line.lower().startswith("category"):
                value = line.split(":", 1)[1].strip().lower()

                intent = mapping.get(value, "conversation")

            elif line.lower().startswith("reason"):
                summary = line.split(":", 1)[1].strip()

            elif line.lower().startswith("confidence"):
                try:
                    confidence = float(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
        return Reason(
            summary=summary,
            intent=intent,
            confidence=confidence,
        )

    def process(self, state):
        """인지 상태에서 사용자 입력의 의도와 신뢰도를 추론해 반환한다."""
        messages = [
            {
                "role": "system",
                "content": self.prompt.build(state),
            }
        ]

        try:
            reply = self.client.generate(messages)

            Logger.info(f"[Reasoning LLM]\n{reply}")

            reason = self._parse_response(reply)

        except Exception as e:
            Logger.error(f"Reasoning Error : {e}")

            reason = Reason(
                summary="사용자의 의도를 분석하지 못했다.",
                intent="conversation",
                confidence=0.5,
            )

        Logger.info(f"[Reason] {reason.intent} ({reason.confidence:.2f})")
        return reason
