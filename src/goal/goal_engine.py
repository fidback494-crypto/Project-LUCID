"""
Project LUCID

Artificial Mind Project

Module : Goal Engine

Creator : 시드
"""

from src.kernel.base_module import BaseModule
from src.utils import Logger

from .goal import Goal


class GoalEngine(BaseModule):

    def __init__(self):
        super().__init__("GoalEngine")

    def start(self):
        Logger.info("Goal Engine Started")

    def update(self):
        pass

    def stop(self):
        Logger.info("Goal Engine Stopped")

    def process(self, state):

        intent = state.reason.intent

        if intent == "question":

            goal = Goal(
                title="질문 해결",
                priority=1.0,
            )

        elif intent == "greeting":

            goal = Goal(
                title="친근한 대화",
                priority=0.8,
            )

        elif intent == "request":

            goal = Goal(
                title="요청 수행",
                priority=0.95,
            )

        elif intent == "emotion":

            goal = Goal(
                title="감정 공감",
                priority=0.9,
            )

        elif intent == "exit":

            goal = Goal(
                title="안전하게 종료",
                priority=1.0,
            )

        else:

            goal = Goal(
                title="대화 유지",
                priority=0.7,
            )

        Logger.info(
            f"[Goal] {goal.title} ({goal.priority:.2f})"
        )

        return goal