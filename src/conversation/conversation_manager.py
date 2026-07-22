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