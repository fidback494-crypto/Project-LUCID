"""
Project LUCID

Artificial Mind Project

Module : Decision Engine

Creator : 시드
"""

from src.kernel.base_module import BaseModule
from src.utils import Logger

from .decision import Decision
from src.action.action import Action


class DecisionEngine(BaseModule):

    def __init__(self):

        super().__init__("DecisionEngine")

    def start(self):

        Logger.info("Decision Engine Started")

    def update(self):
        pass

    def stop(self):

        Logger.info("Decision Engine Stopped")

    # -------------------------------------------------

    def process(self, state):

        decision = Decision(
            action="respond",
            reason=state.plan.goal,
            confidence=state.plan.priority,
        )

        action = Action()

        text = state.observation.content.lower()

        # -----------------------------------------
        # Time
        # -----------------------------------------

        if (
            "몇 시" in text
            or "몇시" in text
            or "현재 시간" in text
            or "지금 시간" in text
            or "오늘 날짜" in text
            or "오늘 며칠" in text
        ):

            action.need_action = True
            action.tool = "time"
            action.command = state.observation.content

        # -----------------------------------------
        # Calculator
        # -----------------------------------------

        elif (
            "계산" in text
            or "+" in text
            or "-" in text
            or "*" in text
            or "/" in text
        ):

            action.need_action = True
            action.tool = "calculator"
            action.command = state.observation.content

        # -----------------------------------------
        # File
        # -----------------------------------------

        elif (
            "파일" in text
            or "읽어" in text
            or "열어" in text
        ):

            action.need_action = True
            action.tool = "file"
            action.command = state.observation.content

        # -----------------------------------------
        # Web
        # -----------------------------------------

        elif (
            "검색" in text
            or "찾아" in text
            or "조사" in text
        ):

            action.need_action = True
            action.tool = "web"
            action.command = state.observation.content

        # -----------------------------------------
        # Memory
        # -----------------------------------------

        elif (
            "기억" in text
            or "메모리" in text
        ):

            action.need_action = True
            action.tool = "memory"
            action.command = state.observation.content

        # -----------------------------------------
        # Python
        # -----------------------------------------

        elif (
            "파이썬" in text
            or "python" in text
            or "코드 실행" in text
        ):

            action.need_action = True
            action.tool = "python"
            action.command = state.observation.content

        # -----------------------------------------
        # Normal Conversation
        # -----------------------------------------

        else:

            action.need_action = False

        decision.action_object = action

        Logger.info(f"[Decision] {decision.action}")

        if action.need_action:

            Logger.info(
                f"[Decision] Tool = {action.tool}"
            )

        return decision
