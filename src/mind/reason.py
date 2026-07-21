"""
Project LUCID

Artificial Mind Project

Module : Reason

Creator : 시드
"""

from dataclasses import dataclass


@dataclass
class Reason:
    summary: str
    intent: str
    confidence: float = 1.0