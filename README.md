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
