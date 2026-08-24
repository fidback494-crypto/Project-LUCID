"""
Project LUCID

Artificial Mind Project

Module : Decision

Creator : 시드
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

from src.action.action import Action


@dataclass
class Decision:

    id: str = field(default_factory=lambda: str(uuid4()))

    action: str = ""

    reason: str = ""

    confidence: float = 0.5

    action_object: Action = field(default_factory=Action)

    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self):

        return (
            f"[Decision] {self.action} "
            f"(confidence={self.confidence:.2f})"
        )