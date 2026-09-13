"""
Project LUCID

Artificial Mind Project

Module : Autonomous Goal

Creator : 시드
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AutonomousGoal:
    """A self-generated direction that remains separate from user requests."""

    interest: str
    title: str
    rationale: str
    next_attention: str
    created_at: datetime = field(default_factory=datetime.now)

    def describe(self) -> str:

        return (
            f"관심: {self.interest} | 목표: {self.title} | "
            f"이유: {self.rationale} | 다음 주의: {self.next_attention}"
        )
