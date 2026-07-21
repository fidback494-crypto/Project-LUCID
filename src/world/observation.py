"""
Project LUCID

Artificial Mind Project

Module : Observation

Creator : 시드
"""

from dataclasses import dataclass


@dataclass
class Observation:

    source: str

    content: str

    importance: float = 0.5