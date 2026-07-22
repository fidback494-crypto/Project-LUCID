"""
Project LUCID

Artificial Mind Project

Module : Thought Engine

Creator : 시드
"""

from src.kernel.base_module import BaseModule
from src.utils import Logger
from src.language.ollama_client import OllamaClient

from .thought import Thought


class ThoughtEngine(BaseModule):

    def __init__(self):

        super().__init__("ThoughtEngine")

        self.client = OllamaClient()

    def start(self):
        Logger.info("Thought Engine Started")

    def update(self):
        pass

    def stop(self):
        Logger.info("Thought Engine Stopped")

    # -------------------------------------------------
    # Prompt
    # -------------------------------------------------

    def _build_prompt(self, state):

        memory = "\n".join(state.long_memory)

        if not memory:
            memory = "없음"

        return f"""
너는 LUCID의 Thought Engine이다.

사용자의 입력과 기억을 참고하여
AI 내부에서 현재 가장 적절한 생각을 만든다.

========================
사용자 입력
========================

{state.observation.content}

========================
Reason
========================

Intent : {state.reason.intent}

Summary : {state.reason.summary}

========================
Long Memory
========================

{memory}

반드시 아래 형식만 출력한다.

Thought:
Importance:
"""

    # -------------------------------------------------
    # Parse
    # -------------------------------------------------

    def _parse_response(self, reply, default_importance):

        thought = "생각을 정리한다."

        importance = default_importance

        for line in reply.splitlines():

            line = line.strip()

            if line.lower().startswith("thought"):

                thought = line.split(":", 1)[1].strip()

            elif line.lower().startswith("importance"):

                try:

                    importance = float(
                        line.split(":", 1)[1].strip()
                    )

                except ValueError:
                    pass

        return thought, importance

    # -------------------------------------------------
    # Process
    # -------------------------------------------------

    def process(self, state):

        prompt = self._build_prompt(state)

        messages = [
            {
                "role": "system",
                "content": prompt,
            }
        ]

        try:

            reply = self.client.generate(messages)

            Logger.info(f"[Thought LLM]\n{reply}")

            thought_text, importance = self._parse_response(
                reply,
                state.reason.confidence,
            )

        except Exception as e:

            Logger.error(f"Thought Error : {e}")

            thought_text = state.reason.summary
            importance = state.reason.confidence

        thought = Thought(
            type=state.reason.intent,
            content=thought_text,
            importance=importance,
        )

        Logger.info(f"[Thought] {thought.content}")

        return thought