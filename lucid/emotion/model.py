"""대화 중 생긴 내적 경험과 최근 이력."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class InnerExperience:
    """경험의 이름, 의미, 계기, 행동 경향, 지속 기간과 기록 시각."""

    name: str
    meaning: str
    trigger: str
    tendency: str
    persistence: str = "잠시 머묾"
    created_at: datetime = field(default_factory=datetime.now)

    def describe(self) -> str:
        """경험과 그 계기·방향·지속 기간을 한 문장으로 반환한다."""
        return (
            f"{self.name}: {self.meaning} "
            f"(계기: {self.trigger}, 방향: {self.tendency}, 지속: {self.persistence})"
        )


class EmotionState:
    """현재 경험과 최근 12건의 이력을 유지한다."""

    def __init__(self) -> None:
        """현재 경험과 최근 이력을 비운 상태로 시작한다."""
        self.current: InnerExperience | None = None
        self.history: list[InnerExperience] = []

    def integrate(self, experience: InnerExperience) -> None:
        """experience를 현재 경험으로 정하고 최근 이력에 추가한다."""
        self.current = experience
        self.history.append(experience)
        del self.history[:-12]

    def summary(self) -> str:
        """현재 경험의 설명을 반환한다. 이력이 없으면 초기 상태 문구를 반환한다."""
        return (
            self.current.describe()
            if self.current is not None
            else "아직 형성된 내적 경험이 없음"
        )

    def recent(self, limit: int = 4) -> list[InnerExperience]:
        """가장 최근 limit건의 경험을 오래된 순서로 반환한다."""
        return self.history[-limit:] if limit > 0 else []
