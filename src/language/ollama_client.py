"""
Project LUCID

Artificial Mind Project

Module : Ollama Client

Creator : 시드
"""

import requests

from src.utils import Logger


class OllamaClient:

    def __init__(self):

        # =========================================
        # Google Colab Ollama
        # =========================================

        self.base_url = (
            "https://pet-provided-bookmarks-stomach.trycloudflare.com"
        )

        self.api_url = f"{self.base_url}/api/chat"

        self.generate_url = f"{self.base_url}/api/generate"

        self.timeout = 300

        # =========================================
        # Model
        # =========================================

        self.model = "qwen2.5:3b"

    # =============================================
    # Connection Test
    # =============================================

    def check_connection(self):

        try:

            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=10,
            )

            response.raise_for_status()

            return True

        except Exception as e:

            Logger.error(
                f"[Ollama] Connection Error : {e}"
            )

            return False

    # =============================================
    # Chat
    # =============================================

    def chat(
        self,
        messages,
        think=False,
    ):

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }

        try:

            response = requests.post(
                self.api_url,
                json=payload,
                timeout=self.timeout,
            )

            response.raise_for_status()

            data = response.json()

            message = data.get("message", {})

            content = message.get(
                "content",
                "",
            )

            if not content:

                Logger.warning(
                    "[Ollama] Empty response"
                )

                return ""

            return content.strip()

        except requests.exceptions.Timeout:

            Logger.error(
                "[Ollama] Request Timeout"
            )

            return (
                "미안해. 응답 시간이 너무 오래 걸렸어."
            )

        except requests.exceptions.ConnectionError:

            Logger.error(
                "[Ollama] Failed to connect to "
                "Google Colab Ollama"
            )

            return (
                "미안해. 현재 LUCID의 AI 서버에 "
                "연결할 수 없어."
            )

        except Exception as e:

            Logger.error(
                f"[Ollama] Error : {e}"
            )

            return (
                "미안해. AI 처리 중 문제가 발생했어."
            )

    # =============================================
    # Generate
    # =============================================

    def generate(
        self,
        messages,
    ):

        # -----------------------------------------
        # messages가 문자열인 경우
        # -----------------------------------------

        if isinstance(messages, str):

            prompt = messages

        else:

            # -------------------------------------
            # Chat 형식 → 하나의 Prompt로 변환
            # -------------------------------------

            parts = []

            for message in messages:

                role = message.get(
                    "role",
                    "user",
                )

                content = message.get(
                    "content",
                    "",
                )

                parts.append(
                    f"{role}: {content}"
                )

            prompt = "\n\n".join(parts)

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }

        try:

            response = requests.post(
                self.generate_url,
                json=payload,
                timeout=self.timeout,
            )

            response.raise_for_status()

            data = response.json()

            result = data.get(
                "response",
                "",
            )

            if not result:

                Logger.warning(
                    "[Ollama] Empty generate response"
                )

                return ""

            return result.strip()

        except requests.exceptions.Timeout:

            Logger.error(
                "[Ollama] Generate Timeout"
            )

            return (
                "미안해. 응답 시간이 너무 오래 걸렸어."
            )

        except requests.exceptions.ConnectionError:

            Logger.error(
                "[Ollama] Generate Connection Error"
            )

            return (
                "미안해. 현재 AI 서버에 "
                "연결할 수 없어."
            )

        except Exception as e:

            Logger.error(
                f"[Ollama] Generate Error : {e}"
            )

            return (
                "미안해. AI 처리 중 문제가 발생했어."
            )
