"""한 대화 턴의 추론, 생각, 계획, 결정을 표현한다."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

from lucid.actions.models import Action


@dataclass
class Reason:
    """관찰에서 얻은 요약, 의도, 신뢰도를 보관한다."""

    summary: str
    intent: str
    confidence: float = 1.0


@dataclass
class Thought:
    """생각의 내용과 중요도, 만들어진 시각을 보관한다."""

    id: str = field(default_factory=lambda: str(uuid4()))
    type: str = "observation"
    content: str = ""
    importance: float = 0.5
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self):
        """생각의 종류, 내용, 중요도를 로그에 표시할 문장으로 반환한다."""
        return f"[{self.type}] {self.content} (importance={self.importance:.2f})"


@dataclass
class Plan:
    """목표를 수행할 단계와 우선순위를 담는다."""

    goal: str
    steps: list[str] = field(default_factory=list)
    priority: float = 1.0


@dataclass
class Decision:
    """선택한 행동과 이유, 실행할 도구 명령을 보관한다."""

    id: str = field(default_factory=lambda: str(uuid4()))
    action: str = ""
    reason: str = ""
    confidence: float = 0.5
    action_object: Action = field(default_factory=Action)
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self):
        """선택한 행동과 신뢰도를 한 줄로 표시한다."""
        return f"[Decision] {self.action} (confidence={self.confidence:.2f})"


@dataclass
class CognitiveResult:
    """인지 처리 결과의 추론, 목표와 계획 단계를 보관한다."""

    reason: str = ""
    intent: str = "conversation"
    confidence: float = 0.8

    thought: str = ""

    goal: str = ""

    priority: float = 0.8

    steps: list[str] | None = None
