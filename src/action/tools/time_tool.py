"""
Project LUCID

Artificial Mind Project

Module : Time Tool

Creator : 시드
"""

from datetime import datetime

from src.action.action_result import ActionResult

from .base_tool import BaseTool


class TimeTool(BaseTool):
    """LUCID가 실행 중인 시스템의 현재 시각을 읽는다."""

    @property
    def name(self):

        return "time"

    def execute(self, command: str):

        try:

            now = datetime.now().astimezone()

            return ActionResult(
                success=True,
                output=(
                    f"현재 시스템 시간: "
                    f"{now.strftime('%Y-%m-%d %H:%M:%S %Z')}"
                ),
            )

        except Exception as e:

            return ActionResult(
                success=False,
                output=f"현재 시간을 읽지 못했어: {e}",
            )
