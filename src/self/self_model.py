"""
Project LUCID

Artificial Mind Project

Module : Self Model

Creator : 시드
"""

from .identity import Identity
from .attention import Attention
from .needs import Needs

from src.emotion.emotion_state import EmotionState


class SelfModel:

    def __init__(self):

        # ============================
        # Identity
        # ============================

        self.identity = Identity()

        # ============================
        # Attention
        # ============================

        self.attention = Attention()

        # ============================
        # Needs
        # ============================

        self.needs = Needs()

        # ============================
        # Emotion
        # ============================

        self.emotion = EmotionState()

    def status(self):

        return {
            "name": self.identity.name,
            "creator": self.identity.creator,
            "version": self.identity.version,
            "focus": self.attention.target,
            "curiosity": self.needs.curiosity,

            # Inner life
            "inner_life": self.emotion.summary(),
        }
