"""숫자와 산술 연산자로 이루어진 식을 계산한다."""

import re

from lucid.actions.models import ActionResult
from lucid.actions.tools.base import BaseTool
from lucid.actions.tools.python import PythonTool


class CalculatorTool(BaseTool):
    """계산기 입력을 숫자 수식으로 제한한 뒤 공통 평가기로 계산한다."""

    def __init__(self):
        """산술식을 계산할 제한된 표현식 평가기를 준비한다."""
        self._evaluator = PythonTool()

    @property
    def name(self):
        """레지스트리에서 도구를 식별하는 이름을 반환한다."""
        return "calculator"

    @staticmethod
    def expression(command):
        """계산 요청 문구를 제외한 산술식만 반환하고 다른 입력에는 None을 반환한다."""
        text = str(command or "").strip().rstrip("?？").strip()
        text = re.sub(r"^(?:계산해\s*줘|계산)\s*[:：]?\s*", "", text)
        text = re.sub(
            r"\s*(?:[은는]\s*)?(?:얼마(?:야|예요)?|계산해(?:\s*줘)?)$", "", text
        )
        expression = text.strip()
        if not re.fullmatch(r"[0-9+*/().\s-]+", expression):
            return None
        return expression

    def execute(self, command: str) -> ActionResult:
        """입력에서 산술식을 찾아 계산 결과 또는 오류를 돌려준다."""
        expression = self.expression(command)
        if not expression:
            return ActionResult(success=False, output="계산식을 찾을 수 없어.")
        return self._evaluator.evaluate_expression(expression)
