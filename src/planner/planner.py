class Planner:
    def decide(self, emotion, memories, event):
        """
        현재 감정, 기억, 이벤트를 바탕으로
        어떤 행동을 할지 결정한다.
        """

        if emotion.happiness >= 70:
            return "friendly_reply"

        if emotion.loneliness >= 50:
            return "start_conversation"

        return "normal_reply"