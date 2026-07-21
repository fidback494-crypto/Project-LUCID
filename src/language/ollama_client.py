"""
Project LUCID

Artificial Mind Project

Module : Ollama Client

Creator : 시드
"""

import time

from ollama import Client

from config import MODEL_NAME


class OllamaClient:

    def __init__(self):
        self.client = Client(host="http://127.0.0.1:11434")

    def generate(self, messages) -> str:

        start = time.time()

        try:

            response = self.client.chat(
                model=MODEL_NAME,
                messages=messages,
            )

            elapsed = time.time() - start

            print(f"[Language] Response : {elapsed:.2f}s")

            return response["message"]["content"]

        except Exception as e:

            return f"[Language Error] {e}"