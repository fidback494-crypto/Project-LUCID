"""
Project LUCID

Artificial Mind Project

Module : Thought Engine

Creator : 시드
"""

from src.kernel.base_module import BaseModule
from src.utils import Logger

from .thought import Thought


class ThoughtEngine(BaseModule):

    def __init__(self):
        super().__init__("ThoughtEngine")

    def start(self):
        Logger.info("Thought Engine Started")

    def update(self):
        pass

    def stop(self):
        Logger.info("Thought Engine Stopped")

    def process(self, reason):

        if reason.intent == "greeting":

            thought_text = "인사에 응답하는 것이 적절하다."

        elif reason.intent == "question":

            thought_text = "질문에 정확하게 답해야 한다."

        elif reason.intent == "exit":

            thought_text = "사용자가 종료를 원한다."

        else:

            thought_text = reason.summary

        thought = Thought(
            type=reason.intent,
            content=thought_text,
            importance=reason.confidence,
        )

        Logger.info(f"[Thought] {thought.content}")

        return thought