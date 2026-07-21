"""
Project LUCID

Artificial Mind Project

Module : Cognitive Context

Creator : 시드
"""

from dataclasses import dataclass, field


@dataclass
class CognitiveContext:

    observation = None

    reason = None

    thought = None

    plan = None

    decision = None

    memory = field(default_factory=list)

    self_model = None

    response = ""