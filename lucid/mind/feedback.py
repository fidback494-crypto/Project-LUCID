"""완료된 대화 턴에서 반성 요약과 상호작용 경험을 만든다."""

from dataclasses import dataclass, field
from datetime import datetime

from lucid.core.kernel import BaseModule
from lucid.core.state import BrainState
from lucid.log import Logger


@dataclass
class Reflection:
    """반성 단계가 산출한 완료 여부, 요약, 신뢰도."""

    success: bool
    summary: str
    confidence: float = 1.0


@dataclass
class Experience:
    """한 턴의 입력과 답변, 신뢰도 및 ISO 형식 생성 시각."""

    event: str
    result: str
    confidence: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ReflectionEngine(BaseModule):
    """완료된 대화 턴에 대한 반성 기록을 생성한다."""

    def process(self, context: BrainState) -> Reflection:
        """완료된 턴을 받아 현재 정책의 고정 완료 요약을 반환한다."""
        reflection = Reflection(success=True, summary="응답을 완료했다.")
        Logger.info(f"[Reflection] {reflection.summary}")
        return reflection


class ExperienceEngine(BaseModule):
    """관찰과 응답을 경험 한 건으로 구성한다."""

    def process(self, state: BrainState) -> Experience:
        """현재 턴의 관찰 원문과 응답으로 생성 시각을 포함한 경험을 반환한다."""
        return Experience(
            event=state.observation.content, result=state.response, confidence=1.0
        )
