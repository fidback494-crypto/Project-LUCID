class EmotionEngine:

    def __init__(self):
        self.state = {
            "happiness": 50,
            "curiosity": 50,
            "loneliness": 20,
            "anger": 0,
            "fatigue": 0,
        }

    def update(self, text):

        text = text.lower()

        if "고마워" in text:
            self.state["happiness"] += 5

        if "칭찬" in text:
            self.state["happiness"] += 3

        if "싫어" in text:
            self.state["anger"] += 5

        if "..." in text:
            self.state["loneliness"] += 2

        self.limit()

    def limit(self):

        for key in self.state:
            self.state[key] = max(
                0,
                min(100, self.state[key])
            )

    def get(self):
        return self.state