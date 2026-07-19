class Planner:

    def decide(self, emotion, memories, event):

        if emotion.happiness >= 70:
            return "friendly_reply"

        if emotion.loneliness >= 50:
            return "start_conversation"

        return "normal_reply"