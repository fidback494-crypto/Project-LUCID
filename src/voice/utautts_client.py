"""Optional English speech output through the Kokoro-compatible voice API."""

import os
import re
import sys

import requests

from src.utils import Logger


class UtauTTSClient:
    """Render English replies as WAV; retain the class name for existing imports."""

    def __init__(self):
        self.base_url = os.getenv(
            "LUCID_UTAUTTS_URL",
            "http://127.0.0.1:8080",
        ).strip().rstrip("/")
        self.voicebank_id = os.getenv("LUCID_UTAUTTS_VOICEBANK_ID", "").strip()
        self.timeout = int(os.getenv("LUCID_UTAUTTS_TIMEOUT", "120"))
        self.session = requests.Session()
        self.available = False

    def start(self):
        """Check the local server and select its configured voicebank once."""
        try:
            health = self.session.get(
                f"{self.base_url}/api/health",
                timeout=(2, 5),
            )
            health.raise_for_status()

            response = self.session.get(
                f"{self.base_url}/api/voicebanks",
                timeout=(2, 10),
            )
            response.raise_for_status()
            voicebanks = response.json().get("voicebanks") or []
        except requests.RequestException as error:
            Logger.info(
                "[Voice] Kokoro voice server is unavailable; LUCID will use text only. "
                f"({type(error).__name__})"
            )
            return False
        except (ValueError, TypeError) as error:
            Logger.warning(f"[Voice] Invalid UtauTTS response: {error}")
            return False

        if not voicebanks:
            Logger.warning("[Voice] Kokoro server has no available voices.")
            return False

        if self.voicebank_id:
            selected = next(
                (
                    bank for bank in voicebanks
                    if bank.get("id") == self.voicebank_id
                ),
                None,
            )
            if selected is None:
                Logger.warning(
                    "[Voice] Configured voicebank ID was not found. "
                    "Use an ID listed by the Kokoro server's /api/voicebanks endpoint."
                )
                return False
        else:
            selected = voicebanks[0]
            self.voicebank_id = str(selected.get("id", "")).strip()

        if not self.voicebank_id:
            Logger.warning("[Voice] Selected voicebank has no ID.")
            return False

        self.available = True
        Logger.info(
            "[Voice] Kokoro English voice ready: "
            f"{selected.get('name') or self.voicebank_id}"
        )
        if len(voicebanks) > 1 and not os.getenv("LUCID_UTAUTTS_VOICEBANK_ID"):
            Logger.info(
                "[Voice] Using the first installed voicebank. "
                "Set LUCID_UTAUTTS_VOICEBANK_ID to choose another."
            )
        return True

    def speak(self, text):
        if not self.available or not text or not text.strip():
            return False

        if sys.platform != "win32":
            Logger.warning("[Voice] Automatic WAV playback is currently Windows-only.")
            return False

        try:
            import winsound

            for chunk in self._split_text(text.strip()):
                response = self.session.post(
                    f"{self.base_url}/api/synthesize/audio",
                    json={
                        "text": chunk,
                        "language": "en",
                        "voicebank_id": self.voicebank_id,
                        "speed": float(os.getenv("LUCID_TTS_SPEED", "1.0")),
                    },
                    timeout=self.timeout,
                )
                response.raise_for_status()

                if not response.headers.get("Content-Type", "").startswith("audio/wav"):
                    Logger.warning("[Voice] Kokoro returned a non-WAV response.")
                    return False

                winsound.PlaySound(response.content, winsound.SND_MEMORY)

            return True
        except requests.RequestException as error:
            Logger.warning(
                f"[Voice] Kokoro synthesis failed: {type(error).__name__}"
            )
        except Exception as error:
            Logger.warning(f"[Voice] Audio playback failed: {error}")

        return False

    @staticmethod
    def _split_text(text, max_chars=450):
        """Keep each synthesis request under the voice server's 500-character limit."""
        chunks = []
        current = ""

        for sentence in re.split(r"(?<=[.!?])\s+", text):
            words = sentence.split()
            for word in words:
                if len(word) > max_chars:
                    if current:
                        chunks.append(current)
                        current = ""
                    chunks.extend(
                        word[index:index + max_chars]
                        for index in range(0, len(word), max_chars)
                    )
                    continue

                candidate = f"{current} {word}".strip()
                if len(candidate) > max_chars and current:
                    chunks.append(current)
                    current = word
                else:
                    current = candidate

            if current:
                chunks.append(current)
                current = ""

        return chunks
