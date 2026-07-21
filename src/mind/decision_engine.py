"""
Project LUCID

Artificial Mind Project

Module : Decision Engine

Creator : 시드
"""

from src.kernel.base_module import BaseModule
from src.utils import Logger

from .decision import Decision


class DecisionEngine(BaseModule):

    def __init__(self):
        super().__init__("DecisionEngine")

    def start(self):
        Logger.info("Decision Engine Started")

    def update(self):
        pass

    def stop(self):
        Logger.info("Decision Engine Stopped")

    def process(self, thought):

        text = thought.content.lower()

        # Sprint001 규칙 기반 판단
        if "인사" in text:
            action = "respond_greeting"

        elif "질문" in text:
            action = "answer"

        else:
            action = "respond"

        decision = Decision(
            action=action,
            reason=thought.content,
            confidence=0.95,
        )

        Logger.info(
            f"[Decision] {decision.action}"
        )

        return decision