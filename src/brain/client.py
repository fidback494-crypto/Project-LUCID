from ollama import Client
from config import MODEL_NAME
import time


class OllamaClient:
    def __init__(self):
        self.client = Client(host="http://127.0.0.1:11434")

    def chat(self, messages) -> str:
        start = time.time()

        try:
            response = self.client.chat(
                model=MODEL_NAME,
                messages=messages,
            )

            end = time.time()
            print(f"⏱ 응답시간 : {end-start:.2f}초")

            return response["message"]["content"]

        except Exception as e:
            return f"[Brain Error] {e}"