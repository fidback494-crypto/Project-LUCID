"""
Project LUCID

Artificial Mind Project

Module : Plan

Creator : 시드
"""

from dataclasses import dataclass, field


@dataclass
class Plan:

    goal: str

    steps: list[str] = field(default_factory=list)

    priority: float = 1.0