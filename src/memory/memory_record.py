"""
Project LUCID

Artificial Mind Project

Module : Memory Record

Creator : 시드
"""

from dataclasses import dataclass


@dataclass
class MemoryRecord:

    category: str

    content: str

    importance: float

    timestamp: str = ""