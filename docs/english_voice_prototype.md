# English voice prototype

LUCID replies in English in this prototype. If a local UtauTTS server is running,
LUCID also synthesizes each reply as a WAV and plays it on Windows. Without the
server, text chat continues normally.

## Start UtauTTS

1. Download and extract the Windows x64 package from the
   [UtauTTS releases](https://github.com/yh2237/UtauTTS/releases).
2. Install an English-capable voicebank and check its own license and usage rules.
3. From the extracted folder, start the local server:

   ```powershell
   .\utautts-server.exe --voice-dir ".\voice" --port 8080
   ```

4. In another PowerShell window, check the voicebank IDs:

   ```powershell
   (Invoke-RestMethod http://127.0.0.1:8080/api/voicebanks).voicebanks |
     Select-Object id, name
   ```

5. If the first listed voicebank is not the English voicebank you want, set its ID
   before starting LUCID:

   ```powershell
   $env:LUCID_UTAUTTS_VOICEBANK_ID = "voicebank-id"
   ```

6. Run `python main.py`. The UtauTTS server must remain running in its own window.

UtauTTS uses a local HTTP server on `127.0.0.1:8080`. LUCID sends the English
reply to `/api/synthesize/audio` and plays the returned WAV. The synthesis API
supports English and pitch-related settings; voicebank support and sound quality
depend on the selected voicebank.

## Pitch settings

The default pitch follows the voicebank. Set a note such as `C4` or `D4` to choose
the synthesis reference pitch for the next LUCID process:

```powershell
$env:LUCID_UTAUTTS_TONE = "D4"
```

The pitch reference must fit the voicebank's recorded range. The default
intonation strength is `4.0`; change it with `LUCID_UTAUTTS_INTONATION_STRENGTH`
to adjust how strongly pitch moves through a sentence.

## Settings

- `LUCID_UTAUTTS_URL`: server URL; default `http://127.0.0.1:8080`.
- `LUCID_UTAUTTS_VOICEBANK_ID`: selected voicebank ID; if unset, LUCID selects the
  first bank reported by the server.
- `LUCID_UTAUTTS_TIMEOUT`: synthesis timeout in seconds; default `120`.
- `LUCID_UTAUTTS_TONE`: optional base pitch such as `C4` or `D4`.
- `LUCID_UTAUTTS_INTONATION_STRENGTH`: pitch contour strength from `0` to `8`;
  default `4.0`.
