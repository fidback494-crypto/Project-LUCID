"""현재 시스템의 현지 시각과 시간대를 조회한다."""

from datetime import datetime

from lucid.actions.models import ActionResult
from lucid.actions.tools.base import BaseTool


class TimeTool(BaseTool):
    """LUCID가 실행 중인 시스템의 현재 시각을 읽는다."""

    @property
    def name(self):
        """레지스트리에서 도구를 식별하는 이름을 반환한다."""
        return "time"

    def execute(self, command: str):
        """명령 문구와 무관하게 시스템 현지 시각과 시간대가 담긴 결과를 반환한다."""
        try:
            now = datetime.now().astimezone()
            return ActionResult(
                success=True,
                output=(f"현재 시스템 시간: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}"),
            )

        except Exception as e:
            return ActionResult(
                success=False,
                output=f"현재 시간을 읽지 못했어: {e}",
            )
