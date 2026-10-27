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

## 장기 기억

장기 기억은 SQLite의 `memories` 테이블에 사용자 주체(`subject`), 관계 이름
(`predicate`), 값(`value`), 신뢰도(`confidence`), 출처(`source`), 최초 저장 시각
(`created_at`), 최근 갱신 시각(`updated_at`)과 함께 저장됩니다. 기존 데이터베이스는
시작할 때 새 열과 인덱스를 추가해 옮기므로 기존 기억과 내적 경험, 자율 목표를
삭제하지 않습니다. 기존 기억의 출처는 `legacy`로 표시됩니다.

같은 이름처럼 하나만 현재 값으로 유지하는 정보가 바뀌면 이전 행은 `superseded`로
보존하고 새 값을 활성화합니다. 같은 선호를 다시 말하면 중복 행을 만들지 않고
신뢰도와 중요도를 갱신합니다. 삭제 명령은 행을 완전히 지우지 않고 `deleted`로
표시해 이력에 남깁니다. 현재 추출기는 명시적인 이름과 좋아하거나 싫어하는 대상을
저장합니다.

사용자와 LUCID가 주고받은 각 대화도 `conversation_episodes`에 시각과 함께
저장합니다. LUCID는 현재 입력과 단어가 겹치는 과거 대화를 최대 3건 검색해
인지 프롬프트에 참고 자료로 전달합니다. 검색 기간은 최소 5년이며 자동 삭제하지
않습니다. 이 기록은 `data/lucid_memory.db` 안에만 저장되고 Git에는 포함되지
않습니다. 과거 대화 로그가 이 DB에 없으면 앱을 실행한 이후의 대화부터 쌓입니다.

캐릭터의 정체성·배경·성격·RP 표현 규칙은 사용자 기억과 섞지 않고
`src/self/identity.py`의 고정 설정으로 매 인지 주기에 전달합니다. 공식 설정에
없는 과거 사건이나 사용자와의 추억은 확인 없이 사실로 추가하지 않습니다.
일생 공식 기억은 이 설정에 영구 보존되며, 최근 대화의 5년 검색 범위와 별개입니다.

실행 중 콘솔에서 기억을 관리할 수 있습니다.

```text
/memory                         활성 장기 기억 보기
/memory canon                   LUCID의 공식 RP와 일생 기억 보기
/memory search <질문>           관련 기억 검색
/memory history                이전 값과 삭제된 기억을 포함한 이력 보기
/memory episodes               최근 저장된 대화 기억 보기
/memory delete <번호>          활성 기억을 목록에서 삭제
```

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

LUCID를 다시 시작한 뒤 브라우저 확장의 **화면 또는 창 공유**를 누르면
한 장면을 분석합니다. 이어서 곁에서 보게 하려면 **곁에서 관찰 시작**을 누르고,
운영체제 선택창에서 공유할 화면 또는 창을 직접 선택합니다. 사용자가 중지할
때까지 선택한 화면을 관찰합니다.

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
비교합니다. 커서 깜빡임과 작은 인코딩 흔들림은 걸러내고, 화면이 충분히 달라진
경우에만 이미지를 Ollama로 보냅니다. 비전 모델은 직전 장면 요약과 비교해
변화를 설명하고, LUCID는 기본 12초 이상의 간격으로 짧게 반응합니다.
확장의 **관찰 중지**를 누르거나 공유가 끝나면 관찰을 멈춥니다.

장면 비교 요약은 현재 실행 중인 동안만 유지됩니다. LUCID를 재시작하면 새
장면부터 다시 관찰합니다.

화면 캡처는 현재 설정된 Ollama 서버로 비전 분석을 위해 전송됩니다. 원격
Cloudflare Tunnel을 쓰는 경우에는 캡처가 해당 원격 Ollama 서버로 전달되므로,
비밀번호·개인정보가 있는 화면은 공유하지 마세요.
