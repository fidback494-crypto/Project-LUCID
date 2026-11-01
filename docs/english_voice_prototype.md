# Kokoro English voice

LUCID can send its reply to the Kokoro voice server and play the returned WAV on
Windows. Text chat continues if the voice server is unavailable.

## Start the voice server

1. Open `project_lucid_kokoro.ipynb` in Google Colab and run its cells in order.
2. Keep the runtime open. In the final cell, copy the current Kokoro tunnel URL
   printed on the `LUCID_UTAUTTS_URL` line.
3. In PowerShell, run `python main.py` from the Project-LUCID folder.
4. Enter the Ollama server URL when prompted.
5. At the Kokoro prompt, paste the current Kokoro tunnel URL. LUCID selects
   `af_amber` automatically.

The notebook uses a Cloudflare Quick Tunnel, so its address can change whenever
the Colab session restarts. Copy the newly printed address for each new session.

## Voice settings and limits

- Voice preset: `af_amber` (Kokoro English voice).
- `LUCID_TTS_SPEED`: optional speed from `0.5` to `2.0`; default is `1.0`.
- Kokoro's configured pipeline and voice are English. LUCID keeps the user's
  language in the visible reply and creates a faithful English `VoiceReply` in
  the same Ollama response for speech, without an extra model call.
- If an English voice is accidentally given Korean text, playback is skipped
  instead of sending Korean text to the English phonemizer.
- Automatic WAV playback currently works on Windows.
- The existing `UtauTTSClient` class name is retained so existing imports keep
  working; it now calls the Kokoro-compatible API.
