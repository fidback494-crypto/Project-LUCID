"""
Project LUCID

Artificial Mind Project

Module : Inner Experience

Creator : 시드
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class InnerExperience:
    """One evolving, descriptive part of LUCID's inner life."""

    name: str
    meaning: str
    trigger: str
    tendency: str
    persistence: str = "잠시 머묾"
    created_at: datetime = field(default_factory=datetime.now)

    def describe(self) -> str:

        return (
            f"{self.name}: {self.meaning} "
            f"(계기: {self.trigger}, 방향: {self.tendency}, "
            f"지속: {self.persistence})"
        )
