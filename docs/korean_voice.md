# Korean speech output

LUCID sends the same Korean sentence shown in the console to the Qwen3-TTS
CustomVoice model. The old Kokoro English prototype is no longer used by the
application. The selected preset is `Sohee`, a Korean speaker in the official
Qwen3-TTS model family. LUCID passes its selected `speech_style` as a short
Korean prosody instruction; it does not translate the reply to English.

## Start the service

Follow [the Colab setup guide](../colab/KOREAN_TTS_SETUP.md). You can share the
Ollama T4 runtime if there is enough free GPU memory; otherwise use a separate
runtime. Copy the
current Quick Tunnel address and the one-time bearer token into `python main.py`
when prompted.

The service loads the model once, serializes synthesis requests, limits request
length, and requires bearer-token authentication for audio generation. Keep the
runtime open while LUCID is using it. Quick Tunnel addresses and the token are
temporary and should be entered again when a new session starts.

## Latency

Text generation and speech generation are separate steps. This service currently
returns a completed WAV file, so audio playback begins after synthesis finishes.
Qwen's Python `generate_custom_voice` API does not provide true streamed audio in
this call. Measure its first-response and warm-response latency on the actual
Colab GPU before setting a target; the earlier 1.2-second goal is not guaranteed
for speech output.
