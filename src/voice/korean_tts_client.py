"""Client for LUCID's Korean Qwen3-TTS Colab service."""

import os
import re
import sys

import requests

from src.utils import Logger


class KoreanTTSClient:
    """Request Korean speech from a compatible Qwen3-TTS service."""

    STYLE_INSTRUCTIONS = {
        "neutral": "",
        "warm": "따뜻하고 다정한 느낌으로, 편안한 억양으로 말해.",
        "curious": "호기심이 살짝 느껴지도록 밝고 자연스럽게 말해.",
        "cheerful": "기분 좋고 생기 있는 목소리로 말해.",
        "playful": "장난기가 은근히 묻어나도록 가볍게 말해.",
        "soothing": "상대를 안심시키듯 부드럽고 차분하게 말해.",
        "concerned": "걱정하는 마음이 느껴지되 차분하고 다정하게 말해.",
        "serious": "또렷하고 침착한 어조로 말해.",
        "shy": "조금 수줍고 조심스러운 느낌으로 말해.",
    }

    def __init__(self):
        self.base_url = (
            os.getenv("LUCID_TTS_URL")
            or os.getenv("LUCID_UTAUTTS_URL")
            or "http://127.0.0.1:8000"
        ).strip().rstrip("/")
        self.token = (
            os.getenv("LUCID_TTS_TOKEN")
            or os.getenv("LUCID_UTAUTTS_TOKEN")
            or ""
        ).strip()
        self.speaker = os.getenv("LUCID_TTS_SPEAKER", "Sohee").strip() or "Sohee"
        self.timeout = self._read_timeout()
        self.session = requests.Session()
        self.available = False

    @staticmethod
    def _read_timeout():
        try:
            return max(10, int(os.getenv("LUCID_TTS_TIMEOUT", "180")))
        except ValueError:
            return 180

    def start(self):
        """Check that the remote endpoint is the expected Korean TTS service."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/health",
                timeout=(3, 10),
            )
            response.raise_for_status()
            health = response.json()
        except (requests.RequestException, ValueError) as error:
            Logger.info(
                "[Voice] Korean TTS server is unavailable; LUCID will use text only. "
                f"({type(error).__name__})"
            )
            return False

        if health.get("engine") != "qwen3-tts" or health.get("language") != "Korean":
            Logger.warning(
                "[Voice] The configured URL is not a compatible Korean Qwen3-TTS server."
            )
            return False
        if not self.token:
            Logger.warning("[Voice] Korean TTS token is missing; voice is disabled.")
            return False

        self.available = True
        Logger.info(
            f"[Voice] Korean TTS ready: {health.get('speaker') or self.speaker}"
        )
        return True

    def speak(self, text, style="neutral"):
        if not self.available or not text or not text.strip():
            return False
        if sys.platform != "win32":
            Logger.warning("[Voice] Automatic WAV playback is currently Windows-only.")
            return False

        try:
            import winsound

            instruction = self.STYLE_INSTRUCTIONS.get(style, "")
            language = "Korean" if re.search(r"[\uac00-\ud7a3]", text) else "Auto"
            headers = {"Authorization": f"Bearer {self.token}"}
            for chunk in self._split_text(text.strip()):
                response = self.session.post(
                    f"{self.base_url}/api/synthesize/audio",
                    headers=headers,
                    json={
                        "text": chunk,
                        "language": language,
                        "speaker": self.speaker,
                        "speech_style": style,
                        "instruct": instruction,
                    },
                    timeout=(5, self.timeout),
                )
                response.raise_for_status()
                if not response.headers.get("Content-Type", "").startswith("audio/wav"):
                    Logger.warning("[Voice] Korean TTS returned a non-WAV response.")
                    return False
                winsound.PlaySound(response.content, winsound.SND_MEMORY)
            return True
        except requests.RequestException as error:
            Logger.warning(f"[Voice] Korean speech generation failed: {type(error).__name__}")
        except Exception as error:
            Logger.warning(f"[Voice] Audio playback failed: {error}")
        return False

    @staticmethod
    def _split_text(text, max_chars=240):
        """Split at sentence boundaries to keep remote generation responsive."""
        sentences = re.split(r"(?<=[.!?。！？])\s*", text)
        chunks = []
        current = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            if len(sentence) > max_chars:
                if current:
                    chunks.append(current)
                    current = ""
                chunks.extend(
                    sentence[index:index + max_chars]
                    for index in range(0, len(sentence), max_chars)
                )
                continue
            candidate = f"{current} {sentence}".strip()
            if current and len(candidate) > max_chars:
                chunks.append(current)
                current = sentence
            else:
                current = candidate
        if current:
            chunks.append(current)
        return chunks
