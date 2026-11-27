"""사용자 입력을 인지 파이프라인의 관찰 값으로 변환한다."""

from dataclasses import dataclass

from lucid.core.kernel import BaseModule
from lucid.log import Logger


@dataclass
class Observation:
    """관찰의 출처, 원문, 상대적 중요도."""

    source: str
    content: str
    importance: float = 0.5


class ObservationEngine(BaseModule):
    """입력 문자열을 해석하기 전의 관찰로 기록한다."""

    def process(self, user_input: str) -> Observation:
        """입력 원문을 보존한 사용자 관찰을 반환한다."""
        observation = Observation(source="user", content=user_input)
        Logger.info("[Observation] User input received")
        return observation
