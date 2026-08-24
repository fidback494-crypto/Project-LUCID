"""
Project LUCID

Artificial Mind Project

Module : Cognitive Result

Creator : 시드
"""

from dataclasses import dataclass


@dataclass
class CognitiveResult:

    reason: str = ""
    intent: str = "conversation"
    confidence: float = 0.8

    thought: str = ""

    goal: str = ""

    priority: float = 0.8

    steps: list[str] | None = None