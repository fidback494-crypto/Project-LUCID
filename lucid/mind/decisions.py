"""사용자 요청에 필요한 도구를 선택한다."""

import re

from lucid.actions.models import Action
from lucid.actions.tools.calculator import CalculatorTool
from lucid.actions.tools.files import FileTool
from lucid.actions.tools.memory import MemoryTool
from lucid.core.kernel import BaseModule
from lucid.log import Logger
from lucid.mind.models import Decision


class DecisionEngine(BaseModule):
    """사용자 요청에 필요한 도구를 선택한다."""

    def process(self, state):
        """관찰 내용과 계획을 바탕으로 도구 실행 여부가 포함된 결정을 반환한다."""
        plan = getattr(state, "plan", None)

        decision = Decision(
            action="respond",
            reason=(plan.goal if plan is not None else "사용자 입력에 반응"),
            confidence=(plan.priority if plan is not None else 0.8),
        )

        command = state.observation.content
        tool = self._select_tool(command.lower())
        if tool is not None:
            decision.action_object = Action(
                tool=tool, command=command, need_action=True
            )
            Logger.info(f"[Decision] Tool = {tool}")

        Logger.info(f"[Decision] {decision.action}")
        return decision

    def _select_tool(self, text):
        """정규화한 입력을 검사해 도구 이름 또는 None을 반환한다."""
        time_phrases = (
            "몇 시",
            "몇시",
            "현재 시간",
            "지금 시간",
            "오늘 날짜",
            "오늘 며칠",
        )
        if any(phrase in text for phrase in time_phrases):
            return "time"
        if self._is_calculation_request(text):
            return "calculator"
        if self._is_file_request(text):
            return "file"
        if self._is_python_request(text):
            return "python"
        if MemoryTool.parse_query(text) is not None:
            return "memory"
        if self._is_web_request(text):
            return "web"
        return None

    @staticmethod
    def _is_calculation_request(text):
        """사칙 연산을 포함하는 계산 요청만 모델 밖에서 처리한다."""
        expression = CalculatorTool.expression(text)
        return bool(
            expression
            and re.search(r"[+*/-]", expression)
            and re.search(r"\d", expression)
        )

    @staticmethod
    def _is_file_request(text):
        """파일 도구가 실제로 해석할 수 있는 읽기·목록 명령인지 확인한다."""
        operation, _ = FileTool.parse_command(text)
        return bool(operation)

    @staticmethod
    def _is_web_request(text):
        """외부 검색을 명시한 요청만 웹 도구로 전달한다."""
        text = text.strip()
        if re.search(
            r"(?:검색|조사|찾)(?:은|는|을|를|해)?\s*(?:하지|지)\s*(?:마|말|않)", text
        ):
            return False
        if re.search(
            r"\b(?:don['’]t|do not|never)\s+(?:search|google|look up)\b", text
        ):
            return False
        if re.match(
            r"^(?:/search|search(?: the web)?(?: for)?|google|look up)\s+\S", text
        ):
            return True
        if re.match(r"^(?:(?:웹|인터넷|온라인)\s*검색|검색)\s*[:：]\s*\S", text):
            return True
        if re.match(
            r"^(?:웹|인터넷|온라인)(?:에서|으로)?\s+.*(?:검색|조사|찾아|알아봐)", text
        ):
            return True
        return (
            re.fullmatch(r".+\s+(?:검색|조사)해\s*(?:줘|주세요|줄래)[?？.!]?", text)
            is not None
        )

    @staticmethod
    def _is_python_request(text):
        """입력이 파이썬 표현식 실행 요청인지 확인한다."""
        return (
            "코드 실행" in text
            or "파이썬으로" in text
            or bool(re.match(r"^\s*python\b", text))
            or ("파이썬" in text and any(verb in text for verb in ("실행해", "계산해")))
        )
