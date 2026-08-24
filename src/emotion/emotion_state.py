"""
Project LUCID

Artificial Mind Project

Module : Emotion State

Creator : 시드
"""


class EmotionState:

    def __init__(self):

        self.joy = 0.5
        self.curiosity = 0.5
        self.confidence = 0.5

        self.sadness = 0.0
        self.anger = 0.0
        self.fear = 0.0

        self.fatigue = 0.0

    def summary(self):

        return {
            "joy": self.joy,
            "curiosity": self.curiosity,
            "confidence": self.confidence,
            "sadness": self.sadness,
            "anger": self.anger,
            "fear": self.fear,
            "fatigue": self.fatigue,
        }