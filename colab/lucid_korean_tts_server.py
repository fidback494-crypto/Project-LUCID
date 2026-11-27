"""페어링한 클라이언트의 문장을 Qwen3-TTS로 합성해 한국어 WAV를 반환한다."""

import hmac
import io
import os
import threading
import time
from typing import Literal

import soundfile as sf
import torch
import uvicorn
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from qwen_tts import Qwen3TTSModel

MODEL_ID = os.getenv(
    "LUCID_TTS_MODEL",
    "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
)
SPEAKER = os.getenv("LUCID_TTS_SPEAKER", "Sohee")
API_TOKEN = os.getenv("LUCID_TTS_TOKEN", "").strip()
if not API_TOKEN:
    raise RuntimeError("Set LUCID_TTS_TOKEN before starting the server.")
if not torch.cuda.is_available():
    raise RuntimeError("No CUDA GPU is available. Select a Colab GPU runtime first.")

print(f"Loading {MODEL_ID} on CUDA (fp16, SDPA)...", flush=True)
model = Qwen3TTSModel.from_pretrained(
    MODEL_ID,
    device_map="cuda:0",
    dtype=torch.float16,
    attn_implementation="sdpa",
)
supported_speakers = model.get_supported_speakers() or []
speaker_lookup = {speaker.lower(): speaker for speaker in supported_speakers}
if SPEAKER.lower() not in speaker_lookup:
    raise RuntimeError(
        f"Speaker {SPEAKER!r} is unavailable. Supported speakers: {supported_speakers}"
    )
print(f"Model ready. Korean speaker: {SPEAKER}", flush=True)

app = FastAPI(title="LUCID Korean TTS", docs_url=None, redoc_url=None)
inference_lock = threading.Lock()


class SpeechRequest(BaseModel):
    """합성할 문장, 언어, 화자와 음성 스타일 지시를 검증하는 요청 본문."""

    text: str = Field(min_length=1, max_length=600)
    language: Literal["Korean", "Auto"] = "Korean"
    speaker: str = Field(default=SPEAKER, min_length=1, max_length=40)
    speech_style: Literal[
        "neutral",
        "warm",
        "curious",
        "cheerful",
        "playful",
        "soothing",
        "concerned",
        "serious",
        "shy",
    ] = "neutral"
    instruct: str = Field(default="", max_length=160)


def require_token(authorization: str | None):
    """Authorization 헤더가 서버 토큰과 일치하는지 확인하고 실패하면 401을 반환한다."""
    supplied = ""
    if authorization and authorization.lower().startswith("bearer "):
        supplied = authorization[7:].strip()
    if not supplied or not hmac.compare_digest(supplied.encode(), API_TOKEN.encode()):
        raise HTTPException(status_code=401, detail="Invalid or missing bearer token")


@app.get("/api/health")
def health():
    """현재 모델·언어·기본 화자·인증 여부를 JSON 객체로 반환한다."""
    return {
        "status": "ok",
        "engine": "qwen3-tts",
        "model": MODEL_ID,
        "language": "Korean",
        "speaker": SPEAKER,
        "auth_required": True,
    }


@app.post("/api/synthesize/audio")
def synthesize_audio(
    request: SpeechRequest,
    authorization: str | None = Header(default=None),
):
    """인증된 문장을 지정 화자로 합성해 WAV 바이트와 처리 시간 헤더를 반환한다."""
    require_token(authorization)
    text = request.text.strip()
    if not text:
        raise HTTPException(
            status_code=422, detail="Text cannot consist only of whitespace"
        )
    selected_speaker = speaker_lookup.get(request.speaker.lower())
    if selected_speaker is None:
        raise HTTPException(
            status_code=400, detail="Speaker is not supported by this model"
        )

    started = time.perf_counter()
    try:
        with inference_lock, torch.inference_mode():
            waveforms, sample_rate = model.generate_custom_voice(
                text=text,
                language=request.language,
                speaker=selected_speaker,
                instruct=request.instruct.strip() or None,
                do_sample=True,
                temperature=0.7,
                top_k=50,
                top_p=0.9,
                repetition_penalty=1.05,
                max_new_tokens=768,
            )
        if not waveforms:
            raise RuntimeError("Qwen3-TTS returned no audio")
        audio_buffer = io.BytesIO()
        sf.write(
            audio_buffer,
            waveforms[0],
            sample_rate,
            format="WAV",
            subtype="PCM_16",
        )
        elapsed = time.perf_counter() - started
        print(
            f"Generated {len(request.text)} characters in {elapsed:.2f}s "
            f"(style={request.speech_style})",
            flush=True,
        )
        return Response(
            content=audio_buffer.getvalue(),
            media_type="audio/wav",
            headers={"X-Generation-Seconds": f"{elapsed:.3f}"},
        )
    except HTTPException:
        raise
    except Exception as error:
        print(f"TTS generation failed: {type(error).__name__}: {error}", flush=True)
        raise HTTPException(
            status_code=500, detail="Speech generation failed"
        ) from error


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
