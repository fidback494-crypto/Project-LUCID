"""
Project LUCID

Artificial Mind Project

Module : Memory Tool

Creator : 시드
"""

from src.action.action_result import ActionResult
from .base_tool import BaseTool


class MemoryTool(BaseTool):

    def __init__(self, long_memory):

        self.long_memory = long_memory

    @property
    def name(self):

        return "memory"

    # -----------------------------------------

    def execute(self, command: str):

        try:

            memories = self.long_memory.all()

            if not memories:

                return ActionResult(
                    success=True,
                    output="기억이 비어있다.",
                )

            result = []

            for memory in memories:

                result.append(str(memory))

            return ActionResult(
                success=True,
                output="\n".join(result),
            )

        except Exception as e:

            return ActionResult(
                success=False,
                output=str(e),
            )