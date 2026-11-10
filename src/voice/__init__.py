"""Optional speech output integrations."""

from .korean_tts_client import KoreanTTSClient

# Keep the historical import name available for external integrations.
UtauTTSClient = KoreanTTSClient

__all__ = ["KoreanTTSClient", "UtauTTSClient"]
