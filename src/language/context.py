"""
Project LUCID

Artificial Mind Project

Module : Language Context

Creator : 시드
"""

from dataclasses import dataclass


@dataclass
class LanguageContext:

    observation: object

    reason: object

    thought: object

    decision: object

    memory: list

    self_model: object