"""
Project LUCID

Artificial Mind Project

Module : Identity

Creator : 시드
"""

from dataclasses import dataclass


@dataclass
class Identity:

    name: str = "LUCID"

    creator: str = "시드"

    version: str = "Alpha 0.1"

    project: str = "Project-LUCID"