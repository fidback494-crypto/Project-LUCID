"""
Project LUCID

Artificial Mind Project

Module : Language Engine
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

        messages = [
            {
                "role": "system",
                "content": (
                    "너는 LUCID다. "
                    "항상 자연스럽고 반말로 대답한다."
                ),
            },
            {
                "role": "user",
                "content": decision.reason,
            },
        ]

        return self.client.generate(messages)