"""
Project LUCID

Artificial Mind Project

Module : Goal

Creator : 시드
"""

from dataclasses import dataclass


@dataclass
class Goal:
    """
    LUCID의 현재 목표
    """

    title: str
    priority: float = 1.0