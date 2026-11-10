"""
Project LUCID

Artificial Mind Project

Module : Ollama Client

Creator : 시드
"""

import os
from time import monotonic

import requests

from src.utils import Logger


class OllamaClient:

    def __init__(self):

        # =========================================
        # Ollama endpoint
        #
        # A local Ollama server is the portable default. Set
        # LUCID_OLLAMA_URL to use a remote server or a temporary tunnel.
        # =========================================

        self.base_url = (
            os.getenv(
                "LUCID_OLLAMA_URL",
                "http://127.0.0.1:11434",
            ).strip().rstrip("/")
        )

        self.api_url = f"{self.base_url}/api/chat"

        self.generate_url = f"{self.base_url}/api/generate"

        self.timeout = self._read_timeout()
        self.keep_alive = os.getenv(
            "LUCID_OLLAMA_KEEP_ALIVE",
            "10m",
        ).strip() or "10m"

        # =========================================
        # Model
        # =========================================

        self.model = os.getenv(
            "LUCID_OLLAMA_MODEL",
            "qwen2.5:3b",
        )
        self.session = requests.Session()
        self.last_metrics = {}

    @staticmethod
    def _read_timeout():
        try:
            return max(5, min(int(os.getenv("LUCID_OLLAMA_TIMEOUT", "300")), 3600))
        except ValueError:
            return 300

    def close(self):
        self.session.close()

    def preload(self, timeout=15):
        """Load the text model during startup so its first user turn is warm."""

        started_at = monotonic()

        try:
            response = self.session.post(
                self.generate_url,
                json={
                    "model": self.model,
                    "prompt": "",
                    "stream": False,
                    "keep_alive": self.keep_alive,
                },
                timeout=(3, timeout),
            )
            response.raise_for_status()
            data = response.json()
            self._record_metrics(data, monotonic() - started_at, "warmup")
            Logger.info(f"[Ollama] Model warmup completed: {self.model}")
            return True

        except requests.RequestException as error:
            self.last_metrics = {
                "request_wall_seconds": monotonic() - started_at,
                "error": True,
            }
            Logger.warning(
                "[Ollama] Model warmup skipped; the first response may be slower. "
                f"({type(error).__name__})"
            )
        except (ValueError, TypeError) as error:
            self.last_metrics = {
                "request_wall_seconds": monotonic() - started_at,
                "error": True,
            }
            Logger.warning(f"[Ollama] Invalid warmup response: {error}")

        return False

    def _record_metrics(self, data, request_wall_seconds, label="generate"):
        """Retain Ollama's timing counters and log them beside HTTP wall time."""

        def seconds(field):
            try:
                return float(data.get(field) or 0) / 1_000_000_000
            except (TypeError, ValueError):
                return 0.0

        eval_count = int(data.get("eval_count") or 0)
        eval_seconds = seconds("eval_duration")
        self.last_metrics = {
            "request_wall_seconds": request_wall_seconds,
            "total_seconds": seconds("total_duration"),
            "load_seconds": seconds("load_duration"),
            "prompt_seconds": seconds("prompt_eval_duration"),
            "generation_seconds": eval_seconds,
            "prompt_tokens": int(data.get("prompt_eval_count") or 0),
            "output_tokens": eval_count,
            "tokens_per_second": (
                eval_count / eval_seconds if eval_seconds > 0 else 0.0
            ),
        }
        metrics = self.last_metrics
        Logger.info(
            f"[Ollama Timing] {label} wall={metrics['request_wall_seconds']:.3f}s "
            f"load={metrics['load_seconds']:.3f}s "
            f"prompt={metrics['prompt_seconds']:.3f}s "
            f"generate={metrics['generation_seconds']:.3f}s "
            f"tokens={metrics['prompt_tokens']}+{metrics['output_tokens']} "
            f"speed={metrics['tokens_per_second']:.1f} tok/s"
        )

    # =============================================
    # Connection Test
    # =============================================

    def check_connection(self):

        try:

            response = self.session.get(
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
        options=None,
        response_format=None,
    ):

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "keep_alive": self.keep_alive,
        }
        if options:
            payload["options"] = options
        if response_format is not None:
            payload["format"] = response_format
        if think:
            payload["think"] = True

        started_at = monotonic()

        try:

            response = self.session.post(
                self.api_url,
                json=payload,
                timeout=(5, self.timeout),
            )

            response.raise_for_status()

            data = response.json()
            self._record_metrics(data, monotonic() - started_at, "chat")

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

            self.last_metrics = {
                "request_wall_seconds": monotonic() - started_at,
                "error": True,
            }

            Logger.error(
                "[Ollama] Chat Timeout"
            )

            return (
                "미안해. 응답 시간이 너무 오래 걸렸어."
            )

        except requests.exceptions.ConnectionError:

            self.last_metrics = {
                "request_wall_seconds": monotonic() - started_at,
                "error": True,
            }

            Logger.error(
                "[Ollama] Failed to connect to the configured server"
            )

            return (
                "미안해. 현재 AI 서버에 연결할 수 없어."
            )

        except Exception as e:

            self.last_metrics = {
                "request_wall_seconds": monotonic() - started_at,
                "error": True,
            }

            Logger.error(
                f"[Ollama] Chat Error : {e}"
            )

            return "미안해. AI 처리 중 문제가 발생했어."

    # =============================================
    # Generate
    # =============================================

    def generate(
        self,
        messages,
        options=None,
        response_format=None,
    ):

        self.last_metrics = {}

        # Preserve message roles through Ollama's chat endpoint. Plain prompts
        # still use /api/generate for callers that intentionally pass a string.
        if not isinstance(messages, str):
            return self.chat(
                messages,
                options=options,
                response_format=response_format,
            )

        prompt = messages

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": self.keep_alive,
        }
        if options:
            payload["options"] = options
        if response_format is not None:
            payload["format"] = response_format

        started_at = monotonic()

        try:

            response = self.session.post(
                self.generate_url,
                json=payload,
                timeout=(5, self.timeout),
            )

            response.raise_for_status()

            data = response.json()
            self._record_metrics(data, monotonic() - started_at)

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

            self.last_metrics = {
                "request_wall_seconds": monotonic() - started_at,
                "error": True,
            }

            Logger.error(
                "[Ollama] Generate Timeout"
            )

            return (
                "미안해. 응답 시간이 너무 오래 걸렸어."
            )

        except requests.exceptions.ConnectionError:

            self.last_metrics = {
                "request_wall_seconds": monotonic() - started_at,
                "error": True,
            }

            Logger.error(
                "[Ollama] Generate Connection Error"
            )

            return (
                "미안해. 현재 AI 서버에 "
                "연결할 수 없어."
            )

        except Exception as e:

            self.last_metrics = {
                "request_wall_seconds": monotonic() - started_at,
                "error": True,
            }

            Logger.error(
                f"[Ollama] Generate Error : {e}"
            )

            return (
                "미안해. AI 처리 중 문제가 발생했어."
            )
