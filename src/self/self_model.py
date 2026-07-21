"""
Project LUCID

Artificial Mind Project

Module : Self Model

Creator : 시드
"""

from .identity import Identity
from .attention import Attention
from .needs import Needs


class SelfModel:

    def __init__(self):

        self.identity = Identity()

        self.attention = Attention()

        self.needs = Needs()

    def status(self):

        return {
            "name": self.identity.name,
            "creator": self.identity.creator,
            "version": self.identity.version,
            "focus": self.attention.target,
            "curiosity": self.needs.curiosity,
        }