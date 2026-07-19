from dataclasses import dataclass


@dataclass
class EmotionEngine:

    happiness: float = 50
    curiosity: float = 50
    loneliness: float = 0
    tiredness: float = 0

    def praise(self):
        """칭찬받았을 때"""

        self.happiness += 10
        self.curiosity += 2

    def ignore(self):
        """오랫동안 대화가 없을 때"""

        self.loneliness += 5

    def rest(self):
        """쉬었을 때"""

        self.tiredness = max(0, self.tiredness - 10)

    def show(self):
        return {
            "happiness": self.happiness,
            "curiosity": self.curiosity,
            "loneliness": self.loneliness,
            "tiredness": self.tiredness,
        }