"""
Project LUCID

Artificial Mind Project

Module : Reasoning Engine

Creator : 시드
"""

from src.kernel.base_module import BaseModule
from src.utils import Logger

from src.language.ollama_client import OllamaClient

from .reason import Reason
from .reasoning_prompt import ReasoningPrompt


class ReasoningEngine(BaseModule):

    def __init__(self):

        super().__init__("ReasoningEngine")

        self.client = OllamaClient()
        self.prompt = ReasoningPrompt()

    def start(self):
        Logger.info("Reasoning Engine Started")

    def update(self):
        pass

    def stop(self):
        Logger.info("Reasoning Engine Stopped")

    # -------------------------------------------------
    # Parse
    # -------------------------------------------------

    def _parse_response(self, reply):

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
                    confidence = float(
                        line.split(":", 1)[1].strip()
                    )
                except ValueError:
                    pass

        return Reason(
            summary=summary,
            intent=intent,
            confidence=confidence,
        )

    # -------------------------------------------------
    # Process
    # -------------------------------------------------

    def process(self, state):

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

        Logger.info(
            f"[Reason] {reason.intent} ({reason.confidence:.2f})"
        )

        return reason