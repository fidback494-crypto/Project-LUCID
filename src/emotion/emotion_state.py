"""
Project LUCID

Artificial Mind Project

Module : Inner Life State

Creator : 시드
"""

from .inner_experience import InnerExperience


class EmotionState:
    """A non-numeric, evolving record of LUCID's generated inner experience."""

    def __init__(self):

        self.current = None
        self.history = []

    def integrate(self, experience: InnerExperience):

        self.current = experience
        self.history.append(experience)

        # Keep a compact but meaningful recent inner history in memory.
        self.history = self.history[-12:]

    def summary(self) -> str:

        if self.current is None:

            return "아직 형성된 내적 경험이 없음"

        return self.current.describe()

    def recent(self, limit=4) -> list[InnerExperience]:

        return self.history[-limit:]
