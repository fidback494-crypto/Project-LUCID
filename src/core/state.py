from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class LucidState:
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

    def update_time(self):
        self.current_time = datetime.now()

    def status(self):
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