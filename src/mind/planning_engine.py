"""
Project LUCID

Artificial Mind Project

Module : Planning Engine

Creator : 시드
"""

from src.kernel.base_module import BaseModule
from src.utils import Logger

from .plan import Plan


class PlanningEngine(BaseModule):

    def __init__(self):
        super().__init__("PlanningEngine")

    def start(self):
        Logger.info("Planning Engine Started")

    def update(self):
        pass

    def stop(self):
        Logger.info("Planning Engine Stopped")

    def process(self, thought):

        if thought.type == "greeting":

            plan = Plan(
                goal="친근하게 인사한다.",
                steps=[
                    "인사한다",
                    "대화를 시작한다",
                ],
                priority=1.0,
            )

        elif thought.type == "question":

            plan = Plan(
                goal="질문에 답한다.",
                steps=[
                    "질문 이해",
                    "정보 제공",
                ],
                priority=0.95,
            )

        else:

            plan = Plan(
                goal="대화를 이어간다.",
                steps=[
                    "응답 생성",
                ],
                priority=0.8,
            )

        Logger.info(f"[Planning] {plan.goal}")

        return plan