"""
Project LUCID

Artificial Mind Project

Module : Conversation Manager

Creator : 시드
"""

from collections import deque


class ConversationManager:

    def __init__(self, capacity=10):

        self.history = deque(maxlen=capacity)
        self.speech_register = "banmal"

    def update_speech_register(self, user_text):
        """Keep one conversational speech level until the user clearly changes it."""
        normalized = "".join(
            character
            for character in str(user_text or "").casefold()
            if character.isalnum()
        )

        # Requests to write or revise a specific artifact only affect that
        # artifact; they do not change LUCID's ongoing conversational voice.
        artifact_markers = (
            "문장", "이메일", "메일", "대사", "번역", "공지",
            "문구", "예문", "보고서", "안내문", "편지", "자소서",
        )
        if any(marker in normalized for marker in artifact_markers):
            return self.speech_register

        requests = (
            (
                "half_polite",
                (
                    "앞으로반존대", "계속반존대", "이제부터반존대",
                    "반존대로말해", "반존대로해줘", "반존대로해",
                    "반존대써", "말투를반존대",
                ),
            ),
            (
                "polite",
                (
                    "앞으로존댓말", "계속존댓말", "이제부터존댓말",
                    "존댓말로말해", "존댓말로해줘", "존댓말로해",
                    "존댓말써", "존댓말부탁", "존댓말로대화",
                    "나한테존댓말", "말투를존댓말", "존댓말로답해",
                    "높임말로말해", "공손하게말해줘", "정중하게대화해",
                ),
            ),
            (
                "banmal",
                (
                    "앞으로반말", "계속반말", "이제부터반말",
                    "반말로말해", "반말로해줘", "반말로해",
                    "반말써", "반말부탁", "반말로대화", "나한테반말",
                    "말투를반말", "말놔줘", "말편하게해줘", "편하게대화해",
                ),
            ),
        )
        explicit_requests = [
            (normalized.rfind(marker), register)
            for register, markers in requests
            for marker in markers
            if marker in normalized
        ]
        if explicit_requests:
            self.speech_register = max(explicit_requests)[1]

        return self.speech_register

    def add_user(self, text):

        self.history.append(
            {
                "role": "user",
                "content": text,
            }
        )

    def add_assistant(self, text):

        self.history.append(
            {
                "role": "assistant",
                "content": text,
            }
        )

    def messages(self):

        return list(self.history)

    def clear(self):

        self.history.clear()
        self.speech_register = "banmal"
