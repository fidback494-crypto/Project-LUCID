class ConversationManager:
    def __init__(self):
        self.messages = []

    def update_system(self, text):
        system_message = {
            "role": "system",
            "content": text,
        }

        if self.messages and self.messages[0]["role"] == "system":
            self.messages[0] = system_message
        else:
            self.messages.insert(0, system_message)

    def add_user(self, text):
        self.messages.append(
            {
                "role": "user",
                "content": text,
            }
        )

    def add_assistant(self, text):
        self.messages.append(
            {
                "role": "assistant",
                "content": text,
            }
        )

    def get_messages(self):
        return self.messages

    def clear(self):
        self.messages = []