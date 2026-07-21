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

    def process(self, decision):

        Logger.info("[Language] Generating response...")

        system_prompt = """
너는 Project LUCID의 Language Engine이다.

규칙

- 자연스럽게 대답한다.
- 반말을 사용한다.
- 너무 길게 말하지 않는다.
- 친근하게 대답한다.
- 자신을 LUCID라고 생각한다.
"""

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": decision.reason,
            },
        ]

        reply = self.client.generate(messages)

        Logger.info("[Language] Response Complete")

        return reply