"""
Project LUCID

Artificial Mind Project

Module : Reflection

Creator : 시드
"""

from dataclasses import dataclass


@dataclass
class Reflection:

    success: bool

    summary: str

    confidence: float = 1.0