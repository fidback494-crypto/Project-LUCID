"""
Project LUCID

Artificial Mind Project

Module : Calculator Tool

Creator : 시드
"""

import re

from src.action.action_result import ActionResult
from .base_tool import BaseTool


class CalculatorTool(BaseTool):

    @property
    def name(self):

        return "calculator"

    # -----------------------------------------

    def execute(self, command: str):

        try:

            expression = command

            # 한글 표현 제거
            remove_words = [
                "계산해",
                "계산",
                "얼마",
                "는",
                "?",
            ]

            for word in remove_words:

                expression = expression.replace(word, "")

            expression = expression.strip()

            # 숫자와 연산자만 허용
            expression = re.sub(
                r"[^0-9\+\-\*\/\(\)\.\s]",
                "",
                expression,
            )

            if not expression:

                return ActionResult(
                    success=False,
                    output="계산식을 찾을 수 없어.",
                )

            result = eval(expression, {"__builtins__": {}})

            return ActionResult(
                success=True,
                output=str(result),
            )

        except Exception as e:

            return ActionResult(
                success=False,
                output=str(e),
            )