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

    def process(self, goal, thought):

        # ---------------------------------
        # Goal 기반 계획 생성
        # ---------------------------------

        if goal.title == "질문 해결":

            plan = Plan(
                goal=goal.title,
                steps=[
                    "질문 분석",
                    "관련 기억 검색",
                    "답변 생성",
                ],
                priority=goal.priority,
            )

        elif goal.title == "친근한 대화":

            plan = Plan(
                goal=goal.title,
                steps=[
                    "인사",
                    "친근한 말투 유지",
                    "대화 이어가기",
                ],
                priority=goal.priority,
            )

        else:

            plan = Plan(
                goal=goal.title,
                steps=[
                    "사용자 의도 파악",
                    "자연스럽게 응답",
                ],
                priority=goal.priority,
            )

        Logger.info(f"[Planning] {plan.goal}")

        for i, step in enumerate(plan.steps, start=1):
            Logger.info(f"  Step {i}: {step}")

        return plan