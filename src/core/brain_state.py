"""
Project LUCID

Artificial Mind Project

Module : Brain State

Creator : 시드
"""

from dataclasses import dataclass, field


@dataclass
class BrainState:
    """
    LUCID의 중앙 인지 상태.
    모든 Engine은 BrainState를 읽고 수정한다.
    """

    # =====================================
    # Cognitive Pipeline
    # =====================================

    observation: object | None = None
    reason: object | None = None
    goal: object | None = None
    thought: object | None = None
    plan: object | None = None
    decision: object | None = None
    response: str = ""

    # =====================================
    # Self
    # =====================================

    self_model: object | None = None

    # =====================================
    # Memory
    # =====================================

    working_memory: list = field(default_factory=list)
    long_memory: list = field(default_factory=list)

    # =====================================
    # Learning
    # =====================================

    reflection: object | None = None
    experience: object | None = None

    # =====================================
    # Internal State
    # =====================================

    emotion: object | None = None
    attention: object | None = None

    # =====================================
    # Future Expansion
    # =====================================

    perception: object | None = None
    vision: object | None = None
    voice: object | None = None
    action: object | None = None