# Project-LUCID

LUCID는 기억, 내적 경험, 자율 목표, 도구 사용을 갖춘 대화형 인공 생명체 프로젝트입니다.

## 다른 컴퓨터에서 실행하기

### 준비물

- Python 3.10 이상
- Git (또는 프로젝트 폴더 전체 복사)
- Ollama 서버: 같은 컴퓨터 또는 접근 가능한 원격 서버

### Windows PowerShell

```powershell
git clone https://github.com/fidback494-crypto/Project-LUCID.git
cd Project-LUCID
.\setup.ps1
```

같은 컴퓨터에서 Ollama를 사용할 때:

```powershell
ollama pull qwen2.5:3b
python main.py
```

원격 Ollama 또는 Cloudflare Tunnel을 사용할 때:

```powershell
$env:LUCID_OLLAMA_URL="https://your-server.example"
$env:LUCID_OLLAMA_MODEL="qwen2.5:3b"
python main.py
```

선택 환경 변수:

```text
LUCID_OLLAMA_URL       Ollama 서버 주소 (기본값: http://127.0.0.1:11434)
LUCID_OLLAMA_MODEL     사용할 모델 (기본값: qwen2.5:3b)
LUCID_OLLAMA_TIMEOUT   요청 제한 시간(초, 기본값: 300)
LUCID_DATA_DIR         로컬 기억 데이터 폴더 (기본값: 프로젝트/data)
```

## 데이터 이전

기억 데이터는 Git에 포함되지 않는 로컬 파일 `data/lucid_memory.db`에 저장됩니다.
기존 기억을 새 컴퓨터로 옮기고 싶을 때만 이 파일을 새 컴퓨터의 같은 위치로 복사하세요.

## 브라우저 페이지를 LUCID와 보기

LUCID는 사용자가 명시적으로 공유한 현재 브라우저 탭의 내용만 읽습니다. 브라우저를
감시하거나 모든 방문 기록을 수집하지 않습니다.

1. `python main.py`로 LUCID를 시작합니다.
2. 콘솔의 `[Browser] Pair token:` 뒤에 표시되는 토큰을 복사합니다.
3. Chrome 또는 Edge에서 `chrome://extensions`를 열고 **개발자 모드**를 켭니다.
4. **압축해제된 확장 프로그램을 로드합니다**를 선택하고 프로젝트의
   `browser_extension` 폴더를 선택합니다.
5. 보고 있는 웹페이지에서 확장 아이콘을 열고 토큰을 붙여넣은 뒤
   **현재 페이지 공유**를 누릅니다.

공유 뒤에는 아래 명령을 사용할 수 있습니다.

```text
/page                         현재 공유된 페이지 정보 보기
/page 이 글의 핵심은 뭐야?     페이지를 바탕으로 질문하기
/page-think                   페이지를 보고 LUCID의 짧은 혼잣말 듣기
```

## 화면·창을 비전 모델로 보기

화면 캡처를 이해하려면 Ollama 서버에 비전 모델을 한 번 설치해야 합니다.

```bash
ollama pull gemma3:12b
```

LUCID를 다시 시작한 뒤 브라우저 확장의 **화면 또는 창 공유**를 누르고,
운영체제 선택창에서 공유할 화면 또는 창을 직접 선택합니다. 캡처는 사용자가
누른 한 번의 공유만 전달되며, 계속 녹화하거나 자동으로 감시하지 않습니다.

```text
/screen                              공유된 화면 상태 보기
/screen 화면에 무슨 오류가 보여?      화면에 관해 질문하기
/screen-think                        화면을 본 LUCID의 짧은 혼잣말 듣기
```

비전 모델은 기본으로 `gemma3:12b`를 사용합니다. 다른 Ollama 서버나 모델을
사용하려면 실행 전에 아래 환경 변수를 설정할 수 있습니다.

```powershell
$env:LUCID_VISION_URL="https://your-ollama-server.example"
$env:LUCID_VISION_MODEL="gemma3:12b"
```

### 곁에서 이어서 화면 보기

확장의 **곁에서 관찰 시작**을 누르면 선택한 화면 또는 창을 3초 간격으로
확인합니다. 동일한 장면은 다시 보내지 않으며, 장면 변화가 확인된 경우에만
LUCID가 기본 12초 이상의 간격으로 짧게 반응합니다. 확장의 **관찰 중지**를
누르거나 LUCID를 종료하면 즉시 멈춥니다.

화면 캡처는 현재 설정된 Ollama 서버로 비전 분석을 위해 전송됩니다. 원격
Cloudflare Tunnel을 쓰는 경우에는 캡처가 해당 원격 Ollama 서버로 전달되므로,
비밀번호·개인정보가 있는 화면은 공유하지 마세요.
