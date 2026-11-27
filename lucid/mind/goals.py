"""분류된 사용자 의도를 응답 목표로 변환한다."""

from dataclasses import dataclass

from lucid.core.kernel import BaseModule
from lucid.core.state import BrainState
from lucid.log import Logger


@dataclass
class Goal:
    """다음 행동을 정하는 목표 문구와 우선순위."""

    title: str
    priority: float = 1.0


class GoalEngine(BaseModule):
    """의도에 대응하는 기본 목표를 선택한다."""

    _GOALS = {
        "question": ("질문 해결", 1.0),
        "greeting": ("친근한 대화", 0.8),
        "request": ("요청 수행", 0.95),
        "emotion": ("감정 공감", 0.9),
        "exit": ("안전하게 종료", 1.0),
    }

    def process(self, state: BrainState) -> Goal:
        """state.reason.intent에 해당하는 새 목표를 반환한다. 기타 의도는 대화 유지다."""
        goal = Goal(*self._GOALS.get(state.reason.intent, ("대화 유지", 0.7)))
        Logger.info(f"[Goal] {goal.title} ({goal.priority:.2f})")
        return goal
