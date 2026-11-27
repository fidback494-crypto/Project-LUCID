"""대화 중 유지하는 정체성, 관심 대상, 욕구와 내적 상태."""

from dataclasses import dataclass

from lucid.emotion.model import EmotionState
from lucid.persona.identity import Identity


@dataclass
class Attention:
    """현재 관심 대상과 집중 정도."""

    target: str = "꿈과 현실의 경계에서 이어지는 대화"
    focus: float = 1.0

    def set(self, target: str, focus: float = 1.0) -> None:
        """관심 대상을 target으로 바꾸고 집중 정도를 focus로 기록한다."""
        self.target = target
        self.focus = focus


@dataclass
class Needs:
    """대화와 휴식 등 캐릭터의 기본 욕구 수치."""

    curiosity: float = 0.8
    communication: float = 0.7
    achievement: float = 0.9
    safety: float = 1.0
    rest: float = 0.2


class SelfModel:
    """캐릭터 설정과 대화 중 갱신되는 상태를 함께 보관한다."""

    def __init__(self) -> None:
        """정체성과 관심, 욕구, 감정 상태의 독립적인 초기값을 만든다."""
        self.identity = Identity()
        self.attention = Attention()
        self.needs = Needs()
        self.emotion = EmotionState()
        self.autonomous_goal = None

    def status(self) -> dict:
        """현재 정체성, 관심, 내적 경험 및 자율 목표를 표시용 사전으로 반환한다."""
        return {
            "name": self.identity.name,
            "alias": self.identity.alias,
            "species": self.identity.species,
            "creator": self.identity.creator,
            "version": self.identity.version,
            "home": self.identity.home,
            "focus": self.attention.target,
            "curiosity": self.needs.curiosity,
            "inner_life": self.emotion.summary(),
            "autonomous_goal": self.autonomous_goal.describe()
            if self.autonomous_goal is not None
            else "없음",
        }
