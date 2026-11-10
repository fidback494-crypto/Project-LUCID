"""
Project LUCID

Artificial Mind Project

Module : Decision Engine

Creator : 시드
"""

import re

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

        plan = getattr(state, "plan", None)

        decision = Decision(
            action="respond",
            reason=(
                plan.goal if plan is not None
                else "사용자 입력에 반응"
            ),
            confidence=(
                plan.priority if plan is not None
                else 0.8
            ),
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

        elif self._is_calculation_request(text):

            action.need_action = True
            action.tool = "calculator"
            action.command = state.observation.content

        # -----------------------------------------
        # File
        # -----------------------------------------

        elif self._is_file_request(text):

            action.need_action = True
            action.tool = "file"
            action.command = state.observation.content

        # -----------------------------------------
        # Web
        # -----------------------------------------

        elif self._is_web_request(text):

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

        elif self._is_python_request(text):

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

    @staticmethod
    def _is_calculation_request(text):
        """Only send actual numeric expressions to the calculator.

        Punctuation such as a trailing slash in an ordinary sentence must
        remain ordinary conversation.
        """

        expression = re.fullmatch(
            r"\s*[0-9.]+(?:\s*[+\-*/]\s*[0-9.]+)+[?？]?\s*",
            text,
        )

        return expression is not None

    @staticmethod
    def _is_file_request(text):
        has_file_action = any(
            phrase in text
            for phrase in ("파일 읽", "파일 열", "파일 보여", "파일 목록", "파일 확인")
        )
        has_project_path = bool(
            re.search(
                r"(?:src|docs|training|browser_extension)[/\\][\w./\\-]+\.[a-z0-9]{1,8}",
                text,
            )
        )
        has_read_verb = any(
            phrase in text
            for phrase in ("읽어", "열어", "보여", "목록", "read", "open", "list")
        )
        return has_file_action or (has_project_path and has_read_verb)

    @staticmethod
    def _is_web_request(text):
        explicit_search = any(phrase in text for phrase in ("검색", "조사"))
        explicit_lookup = (
            any(phrase in text for phrase in ("인터넷에서", "웹에서", "온라인에서"))
            and any(phrase in text for phrase in ("찾", "알아봐", "검색"))
        )
        english_search = bool(re.search(r"\b(search|google|look up)\b", text))
        natural_search_request = any(phrase in text for phrase in ("찾아줘", "찾아봐"))
        return explicit_search or explicit_lookup or english_search or natural_search_request

    @staticmethod
    def _is_python_request(text):
        return (
            "코드 실행" in text
            or "파이썬으로" in text
            or bool(re.match(r"^\s*python\b", text))
            or ("파이썬" in text and any(verb in text for verb in ("실행해", "계산해")))
        )
