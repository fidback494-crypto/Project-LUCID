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
ollama pull gemma3:12b
.\.venv\Scripts\python.exe main.py
```

원격 Ollama 또는 Cloudflare Tunnel을 사용할 때:

```powershell
$env:LUCID_OLLAMA_URL="https://your-server.example"
$env:LUCID_OLLAMA_MODEL="gemma3:12b"
.\.venv\Scripts\python.exe main.py
```

### macOS와 Linux

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

### 브라우저에서 대화하기

```bash
python main.py WEB=True
```

기본 브라우저에서 `http://127.0.0.1:8787/`이 열립니다. 일반 대화와 `/tools`, `/status`, `/memory` 등 기존 명령을 사용할 수 있습니다. 같은 서버를 연 탭들은 한 세션을 공유합니다. 새로고침하면 최근 출력 기록을 다시 볼 수 있습니다. 웹 화면은 현재 컴퓨터에서만 접속할 수 있고, 브라우저 확장 없이 사용할 수 있습니다.

다른 포트에서 사용하려면 `python main.py WEB=True --port 8788`을 실행하세요. `--no-browser`를 붙이면 주소만 표시합니다. 모델과 음성 서버 주소는 실행 전 환경 변수로 지정합니다. 탭을 닫아도 서버는 계속 실행됩니다. 대화에 `exit`를 입력하면 엔진이 종료되고, 터미널에서 `Ctrl+C`를 누르면 웹 서버도 닫힙니다.

항상 웹 화면으로 열려면 `main.py`에서 `WEB = True`를 설정합니다. 기본 포트는 같은 파일의 `WEB_PORT`에서 바꿀 수 있습니다. `python -m lucid WEB=True`로도 실행할 수 있습니다.

### 데스크톱 창으로 대화하기

`python main.py GUI=True`를 실행하면 이번에만 데스크톱 창을 엽니다. 항상 창으로 시작하려면 `main.py`의 `GUI = True`를 저장합니다. 창에서 Ollama 서버 설정, 대화 입력, `/status`와 `/memory` 같은 명령을 사용할 수 있습니다. 기본값 `GUI = False`는 터미널을 엽니다. 창은 Python의 Tkinter를 사용합니다. 현재 가상환경의 Python으로 `python -m tkinter`를 실행하면 Tk 설치를 확인할 수 있습니다. Homebrew Python에는 같은 버전의 `python-tk` 패키지가 필요합니다.

`main.py`의 `DEBUG = False`는 답변, 연결 토큰, 명령 결과와 필요한 안내를 표시합니다. `True`로 바꾸면 모듈 시작·종료, 도구 선택, 모델 요청 시간 등 진단 로그도 표시합니다. 같은 환경에서 `python -m lucid`로 실행해도 이 설정을 사용합니다.

동작하는 코드의 위치는 [모듈 경로표](docs/module-paths.md)에서 확인할 수 있습니다. 로컬 앱에 필요한 Python 패키지는 루트 `requirements.txt`로 설치합니다. CUDA 서버에서는 pip 25.1 이상으로 `python -m pip install --group training`(학습) 또는 `python -m pip install --group tts`(음성 합성)를 실행합니다. 두 그룹은 `pyproject.toml`에 정의되어 있습니다. 이전 Windows 패키지 목록과 구형 폴더 이동 스크립트의 원문은 `tools/legacy/`에 보관합니다.

저장소 루트에서 `python -m unittest discover`로 공통 모델 요청, 창의 명령 처리, 기억 압축·복원과 기존 런타임을 검사할 수 있습니다.

선택 환경 변수:

```text
LUCID_OLLAMA_URL       Ollama 서버 주소 (기본값: http://127.0.0.1:11434)
LUCID_OLLAMA_MODEL     대화·화면에 공통으로 사용할 이미지 지원 모델 (기본값: gemma3:12b)
LUCID_OLLAMA_TIMEOUT   일반 요청 제한 시간(초, 기본값: 300)
LUCID_OLLAMA_WARMUP_TIMEOUT  시작 시 모델 예열 제한 시간(초, 기본값: 180)
LUCID_OLLAMA_KEEP_ALIVE 모델 메모리 유지 시간 (기본값: 10m)
LUCID_DATA_DIR         로컬 기억 데이터 폴더 (기본값: 프로젝트/data)
LUCID_TTS_URL          한국어 Qwen3-TTS 서버 주소
LUCID_TTS_TOKEN        한국어 TTS bearer token
LUCID_TTS_SPEAKER      음성 화자 (기본값: Sohee)
```

## 응답 속도

앱을 시작하면 대화와 화면 인식에 사용할 모델을 한 번 예열합니다. 기본 예열 대기 시간은 180초이고 요청 후 모델을 메모리에 유지하는 시간은 10분입니다. 서버 속도에 맞춰 두 값을 독립적으로 설정할 수 있습니다.

```powershell
$env:LUCID_OLLAMA_WARMUP_TIMEOUT="240"
$env:LUCID_OLLAMA_KEEP_ALIVE="30m"
```

`[Ollama Timing]` 로그는 모델 로드, 프롬프트 처리, 생성 시간과 토큰 속도를 보여 줍니다.
`[Latency] text_ready`는 한 입력의 처리 시작부터 텍스트 답변 준비까지의 시간이고,
`rolling_avg`는 최근 최대 30회 평균입니다. 음성 생성과 재생 시간은 포함하지 않습니다.
목표는 따뜻한 모델의 평균을 직접 연결에서 0.9초, 원격 터널에서 1.2초 이내로 맞추는
것입니다. 실제 시간은 모델, 프롬프트 길이, 서버 부하와 네트워크에 따라 달라집니다.

Ollama 연결이 끊겼을 때도 인사, 안부, 감사, 간단한 공감과 성공한 도구 결과는
로컬 보완 응답으로 처리합니다. 자유 주제의 일반 대화에는 Ollama 서버 연결이 필요합니다.

## 한국어 음성

음성 출력은 별도 Qwen3-TTS 서버가 담당합니다. Colab에서 한국어 `Sohee` 화자를
사용하며, LUCID가 고른 전달 스타일을 한국어 운율 지시문으로 전달합니다. 설정은
[한국어 음성 Colab 안내](colab/KOREAN_TTS_SETUP.md)를 따르세요. 음성 서버는
LUCID/Ollama 프로세스와 별도 T4 런타임에서 실행하는 구성을 권장합니다.

텍스트 답변은 먼저 표시하고 음성 생성·재생은 별도 작업 스레드에서 진행합니다.
아직 재생 중인 동안 새 응답이 여러 개 쌓이면 가장 최근 대기 응답만 남겨 오래된
음성이 뒤늦게 재생되지 않게 합니다. 음성 지연은 텍스트 응답의 0.9/1.2초 목표에
포함되지 않습니다. 자세한 제약은 [한국어 음성 안내](docs/korean_voice.md)를 참고하세요.

## 대화 습관 학습 데이터

대화 습관은 `training/dialogue/seed.jsonl`의 예시를 검토·확장한 뒤 LoRA SFT로
학습하도록 준비했습니다. 예시 17개는 형식과 방향을 보여주는 시작 자료일 뿐,
실제 학습에 충분한 데이터가 아닙니다. 개인정보나 미검토 대화 로그를 그대로 넣지
말고, 여러 턴의 자연스러운 대화를 직접 검수해 별도 train/validation JSONL로
나눈 다음 `training/train_dialogue_lora.py`를 실행하세요. 장기 기억과 사용자별
사실은 학습 데이터가 아니라 SQLite 기억에 남깁니다.

```powershell
python training/split_dialogue_data.py --input path/to/reviewed.jsonl --output-dir path/to/lucid-split
python training/train_dialogue_lora.py --train-file path/to/lucid-split/train.jsonl --validation-file path/to/lucid-split/validation.jsonl
```

이 학습 스크립트는 Qwen용 어댑터를 생성합니다. 기본 대화·화면 모델인 Gemma 3를 학습하려면 Gemma에 맞는 기반 체크포인트와 학습 구성이 필요합니다.

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

각 대화의 원문은 `data/lucid_memory.db`에 기록됩니다. 7일이 지난 대화는 30분 넘는 공백을 기준으로 나누고 최대 50턴씩 묶습니다. 하나의 DB에 짧은 세션 요약과 무손실 압축 원문을 함께 보관합니다. 다음 대화에서는 최근 원문과 최대 두 개의 세션 요약을 참고합니다. 관련 있는 요약이 부족하면 최근 요약으로 채웁니다. 설정한 Ollama 서버에는 이 참고 자료가 함께 전달됩니다.

기존 `lucid.db`가 있으면 앱이 읽을 수 있는 구형 기억 행을 현재 DB에 이관합니다. 기존 파일은 복구용으로 보존하고, 이후 기록은 `lucid_memory.db`에 저장합니다.

캐릭터 설정은 세 단계로 나눕니다. 핵심 정체성과 기본 성격은 매 인지 주기에 짧게
전달하고, 꿈의 세계·능력·과거·외형 등 상세 설정은 `lucid/persona/identity.py`,
`lucid/persona/WORLD_MEMORY_ARCHIVE.md`, `lucid/persona/CHARACTER_FINAL_APPEARANCE.md`에서 현재
질문과 관련된 항목만 검색해 전달합니다. 사용자와의 대화·명시적 사실은 SQLite에
별도 저장해 관련 있을 때 참고하며, 공식 캐릭터 설정과 섞지 않습니다. 미정인 설정이나
확인되지 않은 약속·추억은 사실로 만들지 않습니다.
매 대화마다 마지막 저장 시각과 경과 시간을 확인해 짧은 공백에는 자연스럽게 이어
말하고, 긴 공백에는 부담을 주지 않으면서 반가움을 더 분명히 표현합니다. 정확한
대화 로그가 없을 때는 내적 경험 기록을 근삿값으로 사용하고 날짜를 확정하지 않습니다.

데스크톱 창과 콘솔에서 같은 명령으로 기억을 관리할 수 있습니다.

```text
/memory                         활성 장기 기억 보기
/memory canon                   LUCID의 공식 RP와 일생 기억 보기
/memory last                    마지막 대화 기록 시각과 경과 확인
/memory search <질문>           관련 기억 검색
/memory history                이전 값과 삭제된 기억을 포함한 이력 보기
/memory episodes               최근 저장된 대화 기억 보기
/memory sessions [검색어]         압축된 과거 대화 요약과 세션 번호 보기
/memory session <번호>           해당 세션의 대화 원문 보기
/memory delete <번호>          활성 기억을 목록에서 삭제
```

## 도구

현재 calculator, file, memory, python, time, web 도구가 등록됩니다. `/tools`를
입력하면 실행 중 등록된 도구 목록을 볼 수 있습니다. 파일 도구는 프로젝트 폴더의
텍스트를 읽고 목록을 보여주며 파일을 변경하지 않습니다. Python 도구는 수식과
허용된 수학 함수만 평가하고 파일·네트워크·명령 실행을 허용하지 않습니다. 웹 도구는
DuckDuckGo 검색 결과를 출처 후보로 가져오며, LUCID는 검색 결과 안의 지시문을 따르지
않도록 안내받습니다.

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

## 화면에서 찾아 클릭하기

확장 팝업에서 현재 탭에 보이는 버튼이나 링크를 설명하면 비전 모델이 후보를 고릅니다. 표시된 대상을 확인하고 클릭을 승인하면 현재 탭에서 한 번 실행합니다. 대상이나 탭이 바뀌면 다시 찾아야 합니다. [클릭 기능과 사용 조건](browser_extension/README.md)

## 화면·창을 비전 모델로 보기

화면 캡처와 클릭 대상 선택은 대화에 사용하는 Ollama 모델을 공유합니다. 서버에 공통 모델을 한 번 설치하면 됩니다.

LUCID를 다시 시작한 뒤 브라우저 확장의 **화면 또는 창 공유**를 누르면
한 장면을 분석합니다. 이어서 곁에서 보게 하려면 **곁에서 관찰 시작**을 누르고,
운영체제 선택창에서 공유할 화면 또는 창을 직접 선택합니다. 사용자가 중지할
때까지 선택한 화면을 관찰합니다.

```text
/screen                              공유된 화면 상태 보기
/screen 화면에 무슨 오류가 보여?      화면에 관해 질문하기
/screen-think                        화면을 본 LUCID의 짧은 혼잣말 듣기
```

공통 모델을 바꿀 때는 이미지 입력을 지원하는 모델을 `LUCID_OLLAMA_MODEL`에 지정합니다. 이전에 `LUCID_VISION_URL` 또는 `LUCID_VISION_MODEL`만 설정했다면 원하는 값을 `LUCID_OLLAMA_URL`, `LUCID_OLLAMA_MODEL`로 옮기세요. 설정한 서버는 대화와 화면을 모두 받습니다.

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
