"""
Project LUCID

Artificial Mind Project

Module : Thought

Creator : 시드
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4


@dataclass
class Thought:
    """LUCID의 생각 하나를 표현하는 객체"""

    id: str = field(default_factory=lambda: str(uuid4()))

    type: str = "observation"

    content: str = ""

    importance: float = 0.5

    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self):
        return (
            f"[{self.type}] "
            f"{self.content} "
            f"(importance={self.importance:.2f})"
        )