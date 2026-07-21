"""
Project LUCID

Artificial Mind Project

Module : Decision
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4


@dataclass
class Decision:
    id: str = field(default_factory=lambda: str(uuid4()))
    action: str = ""
    reason: str = ""
    confidence: float = 0.5
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self):
        return (
            f"[Decision] {self.action} "
            f"(confidence={self.confidence:.2f})"
        )