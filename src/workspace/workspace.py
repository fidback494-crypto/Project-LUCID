"""
Project LUCID

Artificial Mind Project

Module : Workspace

Creator : 시드
"""


class Workspace:

    def __init__(self):

        # 현재 입력
        self.observation = None

        # 대화 기록
        self.conversation = []

        # 작업 기억
        self.working_memory = []

        # 장기 기억
        self.long_memory = []

        # 현재 감정
        self.emotion = None

        # 주의
        self.attention = None

        # Context
        self.context = None

        # 추론
        self.reason = None

        # 생각
        self.thought = None

        # 목표
        self.goal = None

        # 계획
        self.plan = None

        # 결정
        self.decision = None

        # 응답
        self.response = None

        # 반성
        self.reflection = None

        # 경험
        self.experience = None

        # Self
        self.self_model = None

    def clear(self):

        self.observation = None
        self.conversation.clear()
        self.working_memory.clear()
        self.long_memory.clear()

        self.emotion = None
        self.attention = None
        self.context = None

        self.reason = None
        self.thought = None
        self.goal = None
        self.plan = None
        self.decision = None

        self.response = None
        self.reflection = None
        self.experience = None

    def summary(self):

        return {
            "observation": self.observation,
            "reason": self.reason,
            "thought": self.thought,
            "goal": self.goal,
            "plan": self.plan,
            "decision": self.decision,
        }