"""
Project LUCID

Artificial Mind Project

Module : Action

Creator : 시드
"""

from dataclasses import dataclass


@dataclass
class Action:

    tool: str = "none"

    command: str = ""

    need_action: bool = False