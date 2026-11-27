"""대화 턴과 애플리케이션의 상태 자료형."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class BrainState:
    """엔진이 한 턴에서 공유하는 관찰, 기억, 도구 결과와 답변을 보관한다."""

    # 인지 단계에서 생성하는 결과와 응답
    observation: object | None = None
    reason: object | None = None
    goal: object | None = None
    thought: object | None = None
    plan: object | None = None
    decision: object | None = None
    response: str = ""
    voice_response: str = ""
    speech_style: str = "neutral"

    # 세션에서 유지하는 자기 모델
    self_model: object | None = None

    # 최근 대화와 말높임
    conversation: list = field(default_factory=list)
    speech_register: str = "banmal"

    # 현재 입력과 관련된 기억과 외부 문맥
    working_memory: list = field(default_factory=list)
    long_memory: list = field(default_factory=list)
    related_inner_experiences: list = field(default_factory=list)
    related_conversation_episodes: list = field(default_factory=list)
    last_conversation_gap: dict = field(default_factory=dict)
    web_context: str = ""
    visual_observation: str = ""

    # 반성과 경험
    reflection: object | None = None
    experience: object | None = None

    # 현재 감정과 인지 결과
    emotion: object | None = None
    attention: object | None = None
    cognitive_success: bool = False

    # 도구 호출과 실행 결과
    action: object | None = None
    action_result: object | None = None

    # 감각 입력
    perception: object | None = None
    vision: object | None = None
    voice: object | None = None

    # 숙고 결과
    deliberation: object | None = None


@dataclass
class LucidState:
    """시간·욕구·행동의 수치 상태를 기록한다."""

    # 시간
    current_time: datetime = field(default_factory=datetime.now)

    # 감정
    happiness: float = 50.0
    curiosity: float = 50.0
    loneliness: float = 0.0
    tiredness: float = 0.0

    # 욕구
    talk_need: float = 50.0
    learn_need: float = 50.0
    rest_need: float = 0.0

    # 현재 상태
    current_goal: str = "Observe"
    current_action: str = "Idle"
    current_thought: str = "System Boot"

    def update_time(self) -> None:
        """현재 시각으로 상태의 시간을 갱신한다."""
        self.current_time = datetime.now()

    def status(self) -> dict:
        """현재 시간과 감정·욕구·행동 값을 표시용 사전으로 반환한다."""
        return {
            "time": self.current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "emotion": {
                "happiness": self.happiness,
                "curiosity": self.curiosity,
                "loneliness": self.loneliness,
                "tiredness": self.tiredness,
            },
            "needs": {
                "talk": self.talk_need,
                "learn": self.learn_need,
                "rest": self.rest_need,
            },
            "goal": self.current_goal,
            "action": self.current_action,
            "thought": self.current_thought,
        }


@dataclass
class Context:
    """기억, 대화, 목표, 과제, 요약을 전달하는 문맥."""

    memories: list
    conversation: list
    goal: str
    task: str
    summary: str


@dataclass
class CognitiveContext:
    """인지 단계의 중간 결과와 독립적인 기억 목록."""

    observation: object | None = None
    reason: object | None = None
    thought: object | None = None
    plan: object | None = None
    decision: object | None = None
    memory: list = field(default_factory=list)
    self_model: object | None = None
    response: str = ""


@dataclass
class LanguageContext:
    """언어 응답을 구성할 관찰, 추론, 기억을 보관한다."""

    observation: object
    reason: object
    thought: object
    decision: object
    memory: list
    self_model: object
