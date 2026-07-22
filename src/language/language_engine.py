"""
Project LUCID

Artificial Mind Project

Module : Language Engine

Creator : 시드
"""

from src.kernel.base_module import BaseModule
from src.utils import Logger

from .ollama_client import OllamaClient


class LanguageEngine(BaseModule):

    def __init__(self):
        super().__init__("LanguageEngine")
        self.client = OllamaClient()

    def start(self):
        Logger.info("Language Engine Started")

    def update(self):
        pass

    def stop(self):
        Logger.info("Language Engine Stopped")

    def process(self, state):

        Logger.info("[Language] Generating Response")

        # ----------------------------------
        # Long-Term Memory
        # ----------------------------------

        memory_text = (
            "\n".join(state.long_memory)
            if state.long_memory
            else "없음"
        )

        # ----------------------------------
        # Working Memory
        # ----------------------------------

        working_text = (
            "\n".join(str(x) for x in state.working_memory)
            if state.working_memory
            else "없음"
        )

        # ----------------------------------
        # Prompt
        # ----------------------------------

        system_prompt = f"""
너는 {state.self_model.identity.name}이다.

Creator : {state.self_model.identity.creator}
Version : {state.self_model.identity.version}

========================
사용자에 대해 알고 있는 사실
========================

{memory_text}

위 내용은 사실이다.

절대로 기억과 모순되는 답을 하지 않는다.

사용자가 관련 질문을 하면
위 기억을 먼저 사용하여 대답한다.

========================
최근 작업 기억
========================

{working_text}

========================
응답 규칙
========================

- 항상 한국어만 사용한다.
- 중국어, 일본어, 영어를 섞지 않는다.
- 반말을 사용한다.
- 기억을 적극 활용한다.
- 모르면 모른다고 말한다.
- 사실을 지어내지 않는다.
"""

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "assistant",
                "content": f"""
현재 기억

{memory_text}
""",
            },
            {
                "role": "user",
                "content": state.observation.content,
            },
        ]

        try:

            reply = self.client.generate(messages)

        except Exception as e:

            Logger.error(f"Language Error : {e}")

            reply = "미안, 지금은 생각을 정리하지 못하고 있어."

        Logger.info("[Language] Complete")

        return reply