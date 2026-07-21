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

    def process(self, context):

        Logger.info("[Language] Generating Response")

        system_prompt = f"""
너는 {context.self_model.identity.name}이다.

Creator : {context.self_model.identity.creator}

Version : {context.self_model.identity.version}

현재 집중 대상 :
{context.self_model.attention.target}

규칙

- 자연스럽게 말한다.
- 반말을 사용한다.
- 너무 길게 말하지 않는다.
- 친절하게 대답한다.
"""

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": context.observation.content,
            },
        ]

        reply = self.client.generate(messages)

        Logger.info("[Language] Complete")

        return reply