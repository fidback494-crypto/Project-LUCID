# LUCID 한국어 음성 서버 (Qwen3-TTS)

이 서비스는 Project-LUCID PC와 Colab GPU 런타임 사이에서 실행한다. Ollama와 같은 T4를 쓸 수 있지만 두 모델이 GPU 메모리를 함께 사용한다. 메모리 부족이 생기면 비전 모델을 내리거나, 별도 GPU 런타임에서 TTS를 실행한다.

## Colab에서 순서대로 실행

1. Ollama를 실행 중인 Colab 노트북을 쓰거나 새 Colab 노트북을 열고 **런타임 → 런타임 유형 변경 → T4 GPU**를 선택한다.
2. `colab/lucid_korean_tts_server.py` 파일을 Colab의 `/content` 폴더에 업로드한다.
3. 새 코드 셀에서 다음을 한 줄씩 실행한다.

```python
%pip install "qwen-tts==0.1.1" "transformers==4.57.3" fastapi uvicorn soundfile
```

설치가 끝난 뒤 Python 런타임을 재시작하라는 안내가 나오면 재시작하고, 필요한 경우 설치 셀을 다시 실행한다.

4. 서버를 시작한다. 이 셀은 모델 파일을 처음 내려받고 GPU에 올리므로 시간이 걸린다.

```python
import os, secrets, subprocess, sys, time, urllib.request

os.environ["LUCID_TTS_TOKEN"] = secrets.token_urlsafe(32)
os.environ["LUCID_TTS_SPEAKER"] = "Sohee"
print("LUCID_TTS_TOKEN (PC 설정에 복사):", os.environ["LUCID_TTS_TOKEN"])
log = open("/content/lucid-tts.log", "w")
tts_process = subprocess.Popen(
    [sys.executable, "/content/lucid_korean_tts_server.py"],
    stdout=log,
    stderr=subprocess.STDOUT,
    env=os.environ.copy(),
)

for _ in range(180):
    if tts_process.poll() is not None:
        log.flush()
        print(open("/content/lucid-tts.log", encoding="utf-8").read()[-8000:])
        raise RuntimeError("TTS server stopped; inspect the error above.")
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/api/health", timeout=2) as response:
            print("TTS server ready:", response.read().decode())
        break
    except Exception:
        time.sleep(2)
else:
    raise TimeoutError("TTS server did not become ready in time.")
```

5. 다음 셀에서 Cloudflare Quick Tunnel을 설치하고 실행한다. 주소가 출력될 때까지 기다린다.

```python
!wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -O /tmp/cloudflared.deb
!dpkg -i /tmp/cloudflared.deb
!cloudflared tunnel --url http://127.0.0.1:8000
```

Quick Tunnel 주소는 세션마다 달라질 수 있다. Colab 런타임을 유지해야 음성 서버도 계속 작동한다.

## Windows에서 LUCID 연결

프로젝트 폴더에서 `python main.py`를 실행한다.

1. Ollama 주소를 입력한다.
2. `https://....trycloudflare.com` 형식으로 출력된 한국어 TTS 주소를 입력한다.
3. 서버 셀에 표시된 `LUCID_TTS_TOKEN`을 붙여 넣는다. 입력 중 토큰은 화면에 표시되지 않는다.
4. 화자는 기본값 `Sohee`를 사용한다.

Qwen3-TTS의 공식 `CustomVoice` 모델에서 `Sohee`는 한국어 화자다. 말투 스타일은 LUCID가 응답마다 고른 `speech_style`을 한국어 자연어 운율 지시문으로 변환해 전달한다. Qwen Python API의 이 호출은 음성 파일을 완성한 뒤 반환하는 방식이라, 첫 음성 재생까지 1.2초 이내라고 보장하지 않는다. 짧은 응답부터 실제 지연을 측정한 뒤 최적화한다.

## 참고

- 기본 선택: `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice`
- 한국어 화자: `Sohee`
- API 요청은 bearer token 인증을 요구한다. `/api/health`만 공개 상태 확인용으로 인증 없이 응답한다.
- TTS 출력은 채팅 모델을 학습시키지 않으며, 대화 데이터의 LoRA 학습과 별개다.
- 모델과 패키지는 Colab 런타임이 종료된 뒤에도 설치된 상태로 남는다고 가정하지 않는다.
