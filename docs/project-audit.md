# Project LUCID 코드 점검 보고서

이 보고서는 구조 개편 전의 점검 기록이다. 아래 소스 링크는 점검 당시 버전을 가리킨다. 현재 코드 위치는 [모듈 경로표](module-paths.md)에서 확인할 수 있다.

2026년 11월 27일 기준, 48개 항목을 확인했다. 개인정보나 인증 정보가 사용자가 선택한 범위를 벗어나는 경로, 사용자 기억을 바꾸는 오류, 테스트와 학습을 막는 오류의 우선순위가 높다. 아래 각 항목에는 확인 방법과 소스 위치를 표시했다.

## 실행 검증과 정리 결과

| 확인 항목 | 결과 |
| --- | --- |
| 앱 기본 흐름 | 삭제 전후의 독립 복사본에서 각각 로컬 모델 연결 실패와 모의 Ollama 정상 응답을 시험했다. 총 네 번 모두 기동, 인사, 계산 입력, 대화 두 건의 SQLite 저장, `exit` 종료를 확인했다. 오프라인 계산 결과는 5였다. |
| 소스와 테스트 | 정리 후 Python 99개 파일을 컴파일하고, 내용이 있는 `src` 모듈 91개를 import했다. 89개 성공, 2개 실패였다. 확장 JavaScript 두 파일은 `node --check`를 통과했다. 기존 pytest 수집 오류는 정리 전후에 동일했다. |
| 빈 항목 | Git이 추적하던 0바이트 파일 74개를 제거했다. 이 중 11개는 빈 `__init__.py`였다. 파일 삭제로 비게 된 소스 폴더 8개도 제거했다. 검사 도중 구형 기억 모듈이 생성한 빈 `data/`도 별도 정리했다. `.git`과 `.venv`는 관리 영역으로 제외했다. |
| 데이터·장치 | 실행 검증에는 임시 DB와 합성 입력을 썼다. 실제 Ollama 추론, Colab GPU 학습, 브라우저의 실제 화면 선택, Windows 음성 재생은 검증 범위 밖이다. |

높음은 개인정보 노출, 데이터 훼손 또는 주요 작업 중단을, 중간은 특정 사용 흐름에서 잘못된 결과나 실패가 발생하는 경우를 가리킨다. 낮음은 제한된 조건의 표시·설정·대화 품질 문제다.

## 정보 보호와 화면 공유

**1. Colab에서 Ollama API 전체가 인증 없이 공개된다.** (높음 · 코드·공식 문서)

노트북의 마지막 셀은 로컬 Ollama 포트를 공개 터널에 직접 연결한다. 실행 중에는 주소를 아는 사람이 사용자 인증 없이 추론 자원을 쓸 수 있다. 터널 앞에서 사용자를 인증하고 앱에 필요한 경로만 공개해야 한다. [Project-LUCID_Colab_Optimized.ipynb 250행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/colab/Project-LUCID_Colab_Optimized.ipynb#L250) · [Ollama 인증 문서](https://docs.ollama.com/api/authentication)

**2. 로컬 기억을 찾는 요청이 외부 웹 검색으로 넘어간다.** (높음 · 입력 분류 재현)

‘내 기억에서 찾아줘’와 ‘검색하지 마’가 모두 웹 도구를 선택했다. 실제 도구는 검색어를 DuckDuckGo에 전송한다. `/page`로 검색 범위를 한정해도 같은 분기를 탄다. 로컬·부정 표현을 먼저 판별해야 한다. [decision_engine.py 100행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/mind/decision_engine.py#L100) · [web_tool.py 83행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/action/tools/web_tool.py#L83)

**3. 기억력에 대한 일반 질문이 사용자의 저장 정보를 불러낸다.** (높음 · 임시 기억으로 재현)

‘기억력이 어떻게 작동해?’에 기억 도구가 활성 기록 전체를 꺼냈다. 전체 결과를 콘솔에 남기고 최대 5,000자를 설정된 모델에 보내며, 오프라인이면 답변에도 기록이 나온다. 명시적인 조회 요청에만 범위를 정해 검색해야 한다. [decision_engine.py 111행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/mind/decision_engine.py#L111) · [memory_tool.py 32행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/action/tools/memory_tool.py#L32) · [life_loop.py 233행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/life/life_loop.py#L233) · [cognitive_prompt.py 51행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/cognitive/cognitive_prompt.py#L51)

**4. TTS 서버를 바꾸면 이전 서버의 인증 토큰이 따라갈 수 있다.** (높음 · 모의 설정·코드)

기존 토큰이 있는 상태에서 새 주소를 입력하고 토큰 입력을 비워 두면 이전 값이 유지됐다. Windows에서 새 서비스가 준비 상태로 판정되면 합성 요청의 인증 헤더에 그 값이 들어간다. 서버 주소와 토큰을 함께 갱신해야 한다. [main.py 68행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/main.py#L68) · [korean_tts_client.py 173행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/voice/korean_tts_client.py#L173)

**5. 브라우저 연결 토큰 파일이 비어 있으면 인증 검사가 무력해진다.** (높음 · 코드)

저장된 토큰이 비었을 때 재발급하지 않고 요청 자격 정보와 비교한다. 손상된 토큰을 거부하거나 안전하게 재발급해야 한다. [local_bridge.py 42행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/browser/local_bridge.py#L42) · [local_bridge.py 81행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/browser/local_bridge.py#L81)

**6. 관찰 중지를 확인한 뒤에도 로컬 화면 캡처가 켜질 수 있다.** (높음 · 모의 미디어 장치로 재현)

장치를 여는 중에 중지를 누르면 UI는 성공을 표시하지만, 뒤늦게 열린 트랙이 비디오에 연결된 채 남았다. 이 순서에서 후속 이미지 전송은 관찰되지 않았다. 취소된 시작 작업이 받은 트랙도 즉시 정지해야 한다. [offscreen.js 41행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/browser_extension/offscreen.js#L41) · [offscreen.js 192행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/browser_extension/offscreen.js#L192) · [offscreen.js 204행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/browser_extension/offscreen.js#L204)

**7. 다른 앱 창을 공유할 때 활성 브라우저 탭의 URL도 전송한다.** (중간 · 코드)

화면 선택 결과와 관계없이 현재 탭에서 읽은 전체 주소를 한 장 공유와 연속 공유에 붙인다. 선택한 창과 무관한 페이지 경로나 쿼리가 로컬 브리지에 전달된다. 화면 공유와 탭 공유의 메타데이터를 분리해야 한다. [popup.js 129행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/browser_extension/popup.js#L129) · [popup.js 152행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/browser_extension/popup.js#L152) · [offscreen.js 154행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/browser_extension/offscreen.js#L154)

**8. 자동 화면 감상을 실제 사용자 대화로 저장한다.** (중간 · 모의 모델·SQLite로 재현)

사용자 입력 없이 관찰 이벤트 두 번으로 대화 행 두 개가 생겼다. 화면에서 유래한 답변이 재시작 후에도 남고 `/memory last`의 시각이 갱신된다. 화면 관찰의 출처와 저장 정책을 사용자 대화와 구분해야 한다. [lucid.py 628행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/app/lucid.py#L628) · [life_loop.py 264행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/life/life_loop.py#L264) · [life_loop.py 272행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/life/life_loop.py#L272)

**9. 사용자 지정 데이터 폴더에서는 브라우저 토큰 보호가 달라진다.** (중간 · 코드)

`LUCID_DATA_DIR`를 프로젝트 안의 일반 폴더로 바꾸면 토큰 파일이 기본 Git 제외 규칙 및 파일 도구 차단 목록을 벗어날 수 있다. 설정된 실제 데이터 경로와 토큰 파일명을 양쪽에서 보호해야 한다. [local_bridge.py 30행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/browser/local_bridge.py#L30) · [file_tool.py 15행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/action/tools/file_tool.py#L15) · [.gitignore 223행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/.gitignore#L223)

**10. 원격 HTTP 연결로도 대화·화면·TTS 자격 정보를 보낼 수 있다.** (중간 · 코드)

서버 주소 검사에서 원격 호스트의 평문 HTTP를 허용한다. 해당 주소를 사용하면 대화와 공유 화면 또는 Windows TTS 인증 헤더가 암호화되지 않은 연결을 지난다. 로컬 기본 주소와 원격 서버의 전송 요건을 구분해야 한다. [main.py 22행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/main.py#L22) · [main.py 56행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/main.py#L56) · [vision_client.py 65행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/vision/vision_client.py#L65) · [korean_tts_client.py 173행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/voice/korean_tts_client.py#L173)

**11. 기억 데이터가 전송되는 범위를 사용 안내에서 파악하기 어렵다.** (중간 · 코드·문서)

README는 대화 기록이 로컬 DB에만 저장된다고 설명한다. 원격 Ollama를 선택하면 관련 과거 발언과 답변도 모델 입력으로 전송된다. 원격 서버가 이 내용을 보존하는지는 서버 정책에 달려 있다. 화면 전송처럼 텍스트와 기억의 전송 범위도 안내해야 한다. [README.md 117행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/README.md#L117) · [cognitive_prompt.py 32행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/cognitive/cognitive_prompt.py#L32) · [ollama_client.py 193행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/language/ollama_client.py#L193)

**12. 공유 페이지와 검색 결과를 모델의 시스템 지시문에 넣는다.** (중간 · 모의 입력으로 확인)

가상 페이지 본문·화면 관찰·검색 결과가 모두 `system` 메시지에 포함됐다. 관찰 자료로 취급하라는 문구는 있지만 메시지 역할은 앱의 상위 지시와 같다. 외부 콘텐츠를 별도의 데이터 메시지로 전달해야 한다. 실제 모델이 지시를 잘못 따른 사례까지 검증한 것은 아니다. [cognitive_engine.py 226행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/cognitive/cognitive_engine.py#L226) · [cognitive_prompt.py 167행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/cognitive/cognitive_prompt.py#L167) · [cognitive_prompt.py 180행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/cognitive/cognitive_prompt.py#L180)

## 실행과 자동 테스트

**13. 현재 프로젝트 가상환경에서는 앱을 시작할 수 없다.** (높음 · 실행 재현)

이 작업 폴더의 `.venv`에서 앱을 import하면 `requests`가 없어 실패했다. 런타임 모듈들이 직접 쓰는 패키지는 `requirements-portable.txt`에 있지만 일반 `requirements.txt`에는 직접 선언되지 않았다. Windows 설치 스크립트는 가상환경에 설치하지만 README의 다음 실행 예시는 기본 `python`을 호출한다. [web_tool.py 6행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/action/tools/web_tool.py#L6) · [requirements.txt](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/requirements.txt) · [requirements-portable.txt 1행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/requirements-portable.txt#L1) · [setup.ps1 14행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/setup.ps1#L14) · [README.md 25행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/README.md#L25)

**14. pytest가 테스트를 한 건도 실행하기 전에 실패한다.** (높음 · 삭제 전후 재현)

`test_reasoning.py`가 `BrainState`를 받는 엔진에 `Observation`을 넘겨 수집 중 `AttributeError`가 발생한다. `test_logger.py`만 실행하면 테스트 0건이다. 두 파일 모두 import 시 코드를 실행하고 결과를 검증하는 테스트 함수가 없다. [test_reasoning.py 11행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/test_reasoning.py#L11) · [reasoning_prompt.py 22행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/mind/reasoning_prompt.py#L22) · [test_logger.py 3행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/test_logger.py#L3)

**15. 데모가 첫 import에서 종료된다.** (중간 · 실행 재현)

관찰 엔진은 `src/world`에 있지만 데모는 없는 `src.mind.observation_engine`을 가져온다. import를 고쳐도 `observe`, `create`, `decide`는 현재 엔진의 메서드가 아니다. [demo.py 1행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/demo.py#L1) · [demo.py 17행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/demo.py#L17) · [observation_engine.py 31행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/world/observation_engine.py#L31)

**16. 대화 중 표준 입력이 닫히면 오류를 계속 출력한다.** (중간 · 실행 재현)

`Ctrl-D` 또는 파이프 입력 종료 시 `EOFError`가 일반 예외 처리로 들어가 다시 `input()`을 호출한다. 모의 입력에서 연속 다섯 번 확인했다. EOF를 정상 종료로 처리해야 한다. [lucid.py 259행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/app/lucid.py#L259) · [lucid.py 572행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/app/lucid.py#L572)

**17. 문맥 모듈 두 개는 유효한 Python 문법인데도 로드에 실패한다.** (중간 · 모듈 import 재현)

`Context`는 `dataclass`를 import하지 않아 `NameError`가 발생한다. `CognitiveContext.memory`에는 필드 타입 선언이 없어 `TypeError`가 발생한다. 현재 주 실행 경로는 두 모듈을 사용하지 않는다. [context.py 1행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/context/context.py#L1) · [cognitive_context.py 27행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/context/cognitive_context.py#L27)

**18. 예상과 다른 JSON을 받으면 모델 예열 중 앱 전체가 종료된다.** (중간 · 모의 서버 응답 재현)

예열 응답이 JSON 배열이면 지표 수집에서 `.get()`을 호출하다 `AttributeError`가 발생한다. 실패 시 로컬 대화를 제공하는 시작 경로를 사용하려면 먼저 응답 자료형을 검사해야 한다. [ollama_client.py 86행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/language/ollama_client.py#L86) · [cognitive_engine.py 61행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/cognitive/cognitive_engine.py#L61)

**19. 기억 모듈을 가져오기만 해도 현재 작업 폴더에 `data/`가 생긴다.** (중간 · 실행 재현)

별도의 `LUCID_DATA_DIR`를 설정해도 구형 모듈이 import 단계에서 상대 경로를 만든다. 쓰기 금지된 작업 폴더에서는 실제 DB를 열기 전부터 기동에 실패할 수 있다. 저장소 생성은 명시된 데이터 위치에서 초기화할 때 수행해야 한다. [__init__.py 1행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/memory/__init__.py#L1) · [database.py 4행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/memory/database.py#L4)

**20. Windows 설치 실패가 완료 메시지로 표시될 수 있다.** (중간 · 코드·공식 문서)

`pip`의 종료 코드를 확인하지 않고 설치 완료를 출력한다. PowerShell 기본 설정에서는 외부 명령의 비정상 종료가 `$ErrorActionPreference`만으로 예외가 되지 않는다. 가상환경 생성과 각 설치 명령의 결과를 확인해야 한다. [setup.ps1 10행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/setup.ps1#L10) · [setup.ps1 14행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/setup.ps1#L14) · [setup.ps1 17행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/setup.ps1#L17) · [Microsoft PowerShell 문서](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_preference_variables#psnativecommanduseerroractionpreference)

**21. 마이그레이션 중 오류가 나도 소스 전체를 다시 쓰고 성공을 출력할 수 있다.** (중간 · 코드·공식 문서)

기존 백업이 있으면 최신 상태를 백업하지 않고 진행한다. 이동이나 파일 처리 실패 시 중단·복원 절차 없이 모든 Python 파일을 기본 인코딩으로 다시 쓴다. Windows PowerShell 5.1에서는 BOM 없는 UTF-8 한글 소스가 시스템 코드 페이지로 해석될 수 있다. [migrate_to_brain.ps1 13행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/migrate_to_brain.ps1#L13) · [migrate_to_brain.ps1 52행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/migrate_to_brain.ps1#L52) · [migrate_to_brain.ps1 75행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/migrate_to_brain.ps1#L75) · [migrate_to_brain.ps1 82행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/migrate_to_brain.ps1#L82) · [Microsoft 인코딩 문서](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_character_encoding)

**22. 루트 설정 파일에서 모델이나 시스템 프롬프트를 바꿔도 적용되지 않는다.** (낮음 · 코드)

`config.py`에 정의한 두 설정값을 읽는 호출부가 없다. 실행 모델은 Ollama 클라이언트의 환경 변수와 기본값으로 결정되고 시스템 프롬프트는 별도 인지 모듈에서 생성한다. [config.py 2행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/config.py#L2) · [ollama_client.py 52행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/language/ollama_client.py#L52) · [cognitive_prompt.py 128행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/cognitive/cognitive_prompt.py#L128)

## 대화와 장기 기억

**23. 이름을 물으면 이미 저장한 이름이 바뀐다.** (높음 · 임시 SQLite로 재현)

‘내 이름은 유진이야’ 뒤에 ‘내 이름은 뭐야?’를 입력하자 활성 이름이 ‘유진’에서 ‘뭐’로 바뀌고 신뢰도는 0.99가 됐다. 같은 추출기는 ‘너는 피자를 좋아해?’도 사용자의 선호로 저장한다. 질문과 발화 주체를 판별한 뒤 사실을 저장해야 한다. [memory_extractor.py 22행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/memory/memory_extractor.py#L22) · [memory_extractor.py 51행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/memory/memory_extractor.py#L51)

**24. 선호가 바뀌어도 이전과 현재 선호가 모두 활성이다.** (중간 · 임시 SQLite로 재현)

같은 대상의 `likes`와 `dislikes`를 별개의 키로 만들어 둘 다 현재 기억으로 검색한다. 동일 대상에 대해 반대되는 진술이 들어오면 이전 값을 이력으로 넘겨야 한다. [memory_record.py 64행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/memory/memory_record.py#L64) · [long_term_memory.py 283행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/memory/long_term_memory.py#L283)

**25. 삭제하거나 변경한 사실을 다시 말하면 변경 이력이 소실된다.** (중간 · 임시 SQLite로 재현)

이름을 A→B→A로 바꾸면 행은 두 개만 남는다. 삭제한 사실을 다시 말해도 기존 행을 활성화해서 `/memory history`에서 그 행이 삭제됐던 상태를 확인할 수 없다. [long_term_memory.py 330행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/memory/long_term_memory.py#L330) · [long_term_memory.py 365행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/memory/long_term_memory.py#L365)

**26. 한 글자짜리 기억을 검색할 수 없다.** (중간 · 임시 SQLite로 재현)

빵 선호를 저장한 뒤 `/memory search 빵` 결과가 비었다. 한 글자 한국어 검색어가 제거되며 대화 에피소드 검색도 같은 제한이 있다. [memory_search.py 48행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/memory/memory_search.py#L48) · [long_term_memory.py 626행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/memory/long_term_memory.py#L626)

**27. 경험과 이벤트 여러 개에 같은 생성 시각이 기록된다.** (중간 · 실행·코드)

기본값이 클래스 정의 시 한 번 계산된다. 서로 다른 턴에서 생성한 `Experience.timestamp`가 일치했다. 각 객체를 만들 때 시각을 구해야 한다. [experience.py 24행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/self/experience.py#L24) · [event.py 9행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/event/event.py#L9)

**28. 자율 추론이 사용자 대화와 겹쳐 오래된 목표를 저장할 수 있다.** (중간 · 코드)

유휴 판정 뒤 요청을 보낸다. 응답을 기다리는 동안 사용자가 대화를 시작하고 끝내면, 저장 시점의 활성 대화 수는 다시 0이어서 대화 이전에 만든 결과를 적용할 수 있다. 대화로 인해 결과를 버린 경우도 실패 재시도로 계산한다. [autonomous_engine.py 135행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/autonomy/autonomous_engine.py#L135) · [autonomous_engine.py 169행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/autonomy/autonomous_engine.py#L169) · [autonomous_engine.py 216행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/autonomy/autonomous_engine.py#L216)

**29. 자율 경험과 목표를 반만 저장해도 성공으로 처리할 수 있다.** (중간 · 코드)

메모리 상태를 먼저 바꾸고 경험과 목표를 별도 트랜잭션으로 저장한다. 각 저장 메서드가 오류를 내부에서 처리하므로 한쪽만 실패해도 성공 로그를 낼 수 있고, 재시작 전후 상태가 달라진다. [autonomous_engine.py 172행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/autonomy/autonomous_engine.py#L172) · [long_term_memory.py 563행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/memory/long_term_memory.py#L563) · [long_term_memory.py 972행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/memory/long_term_memory.py#L972)

**30. 백그라운드 작업이 오래 걸리면 SQLite 연결을 닫을 기회가 사라진다.** (중간 · 코드)

종료 대기 시간을 넘기면 연결을 열어 둔 채 종료 완료 플래그를 설정한다. 같은 프로세스에서 작업이 끝난 뒤 `shutdown()`을 다시 호출해도 연결 정리를 건너뛴다. [lucid.py 577행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/app/lucid.py#L577) · [lucid.py 602행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/app/lucid.py#L602) · [lucid.py 611행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/app/lucid.py#L611)

**31. 일반적인 소개·별자리 요청을 엉뚱한 답변으로 바꾼다.** (중간 · 입력 재현)

‘책을 소개해줘’는 LUCID의 자기소개로 분류됐다. ‘오늘 배운 별자리 이름 정리해 줘’는 모델 호출 전에 운세와 밤하늘 중 하나를 고르라는 응답으로 끝났다. [cognitive_engine.py 75행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/cognitive/cognitive_engine.py#L75) · [cognitive_engine.py 289행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/cognitive/cognitive_engine.py#L289) · [cognitive_engine.py 474행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/cognitive/cognitive_engine.py#L474)

**32. 말투 변경의 부정 표현과 영어 축약형을 놓친다.** (낮음 · 입력 재현)

‘존댓말로 말해 주지 마’가 존댓말 설정을 켰다. 오프라인 대화에서는 입력의 아포스트로피를 지운 뒤 아포스트로피가 있는 표현과 비교해 “I'm tired”와 “How's it going?”이 준비된 답변에 도달하지 못했다. [conversation_manager.py 67행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/conversation/conversation_manager.py#L67) · [basic_conversation.py 32행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/cognitive/basic_conversation.py#L32)

**33. 안내한 세 번째 과거 대화가 모델 입력에서 빠진다.** (낮음 · 코드·문서)

검색은 세 건까지 하지만 인지 프롬프트에는 처음 두 건만 담는다. README에 설명한 검색·전달 범위와 실제 한도가 다르다. [README.md 117행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/README.md#L117) · [life_loop.py 178행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/life/life_loop.py#L178) · [cognitive_prompt.py 38행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/cognitive/cognitive_prompt.py#L38)

**34. 대화가 누적될수록 매 턴의 기억 검색 비용이 늘어난다.** (중간 · 합성 데이터로 측정)

기간 안의 대화 본문을 검색어마다 결합·정규화하고 부분 일치를 계산한 뒤 상위 세 건을 고른다. 같은 네 단어로 로컬 SQLite에서 측정한 검색 시간 중앙값은 합성 기록 1천 건에서 1.13ms, 2만 건에서 21.69ms였다. 첫 실행을 제외하고 각 다섯 번 측정한 값이다. [long_term_memory.py 693행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/memory/long_term_memory.py#L693) · [long_term_memory.py 714행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/memory/long_term_memory.py#L714) · [life_loop.py 177행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/life/life_loop.py#L177)

## 파일과 계산 도구

**35. 도구가 안내한 명령을 콘솔에서 그대로 쓸 수 없다.** (중간 · 입력 분류 재현)

파일 도구의 `read README.md`와 `list docs`는 도구 선택기를 통과하지 못한다. ‘docs 폴더 파일 목록’은 프로젝트 루트를 가리킨다. 계산도 `(2+3)*4`나 ‘2+3은 얼마야?’를 인식하지 못해 오프라인에서 계산 결과를 제공하지 못한다. [decision_engine.py 157행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/mind/decision_engine.py#L157) · [decision_engine.py 166행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/mind/decision_engine.py#L166) · [file_tool.py 33행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/action/tools/file_tool.py#L33) · [file_tool.py 53행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/action/tools/file_tool.py#L53)

**36. Python 도구의 출력 제한이 메모리 사용 제한으로 작동하지 않는다.** (중간 · 코드)

중첩 컨테이너를 전부 문자열로 만든 뒤 4,000자 제한을 확인한다. 바깥 컨테이너 길이만 검사해 문자열을 만드는 과정에서 메모리가 먼저 소진될 수 있다. 표현 크기에 맞춰 순회·출력을 중단해야 한다. [python_tool.py 80행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/action/tools/python_tool.py#L80) · [python_tool.py 173행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/action/tools/python_tool.py#L173)

**37. 웹 검색 결과 링크의 경로나 매개변수가 변형된다.** (낮음 · 오프라인 URL 처리 재현)

검색 결과의 목적지 URL을 `parse_qs`로 디코딩한 뒤 `unquote`를 다시 적용한다. 원래 주소에서 인코딩한 구분 문자까지 풀려 다른 대상을 가리킬 수 있다. [web_tool.py 63행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/action/tools/web_tool.py#L63)

## 화면 관찰과 음성

**38. 화면이 한 번 바뀐 뒤 멈추면 마지막 장면을 놓친다.** (중간 · 모의 시계로 재현)

반응 대기 시간 안에 받은 프레임을 처리 완료로 표시한다. 화면이 그대로면 확장이 새 프레임을 보내지 않아 대기 시간이 지나도 마지막 장면을 분석하지 않는다. [visual_presence.py 70행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/vision/visual_presence.py#L70) · [offscreen.js 141행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/browser_extension/offscreen.js#L141)

**39. 공유 창을 바꾸면 이전 창의 관찰이 새 창에 섞인다.** (중간 · 코드)

추론 완료 시 연속 공유가 켜져 있는지만 검사한다. 이전 창을 중지하고 새 창을 공유하는 사이에 오래된 결과가 돌아오면 그 결과를 말하거나 다음 비교 문맥으로 전달할 수 있다. [visual_presence.py 76행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/vision/visual_presence.py#L76) · [visual_presence.py 87행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/vision/visual_presence.py#L87) · [visual_presence.py 100행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/vision/visual_presence.py#L100)

**40. 브리지 포트를 바꾸면 확장에서 연결할 수 없다.** (중간 · 코드)

서버는 `LUCID_BROWSER_PORT`를 따르지만 확장의 페이지·화면 전송과 중지 주소는 8765로 고정돼 있다. [local_bridge.py 19행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/browser/local_bridge.py#L19) · [popup.js 20행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/browser_extension/popup.js#L20) · [offscreen.js 148행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/browser_extension/offscreen.js#L148)

**41. 프로그램 종료 뒤에도 진행 중인 Windows 음성이 이어질 수 있다.** (중간 · 코드)

음성 스레드를 1초만 기다린 뒤 세션을 닫는다. 이미 진행 중인 작업은 합성이 끝난 뒤나 다음 문장으로 넘어갈 때 중지 상태를 확인하지 않고 전송·재생을 계속할 수 있다. [korean_tts_client.py 158행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/voice/korean_tts_client.py#L158) · [korean_tts_client.py 174행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/voice/korean_tts_client.py#L174) · [korean_tts_client.py 191행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/voice/korean_tts_client.py#L191)

**42. 화면 캡처 시각이 중지 시각으로 바뀐다.** (낮음 · 코드)

관찰 중지 시 마지막 이미지의 `received_at`만 현재 시각으로 다시 기록해 `/screen`이 실제보다 늦은 캡처 시각을 표시한다. [page_context.py 86행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/browser/page_context.py#L86) · [lucid.py 507행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/app/lucid.py#L507)

**43. 음성을 재생할 수 없는 플랫폼에서도 준비 완료로 표시한다.** (낮음 · 코드·문서)

서버가 정상인 경우 macOS·Linux에서도 준비 메시지와 작업 스레드를 만들지만 실제 비동기 합성·재생 요청은 조용히 건너뛴다. 별도의 영어 음성 가이드는 저장소에 없는 노트북과 폐기된 Kokoro 입력 안내를 여전히 제공한다. [korean_tts_client.py 82행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/voice/korean_tts_client.py#L82) · [korean_tts_client.py 122행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/voice/korean_tts_client.py#L122) · [english_voice_prototype.md 8행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/docs/english_voice_prototype.md#L8)

**44. 웹페이지와 화면 이미지가 서로의 공유 상태를 덮어쓴다.** (중간 · 코드)

콘솔은 `/page`와 `/screen`에 같은 최신 항목을 쓴다. 페이지를 공유하고 화면을 공유하면 기존 페이지 본문이 없어지고, 반대로 페이지를 공유하면 마지막 화면 이미지에 질문할 수 없다. 이미지 하나만 있어도 `/page`의 준비 확인을 통과한다. [page_context.py 68행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/browser/page_context.py#L68) · [lucid.py 470행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/app/lucid.py#L470) · [lucid.py 515행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/app/lucid.py#L515)

**45. 동시 응답에서 음성의 말투가 다른 답변의 말투와 섞일 수 있다.** (낮음 · 코드)

콘솔 답변과 자동 화면 감상은 같은 작업 공간을 사용한다. 출력 직전에 잠금을 풀고 그 뒤 공유 상태에서 `speech_style`을 다시 읽으므로, 그 사이 다른 턴이 실행되면 먼저 만든 답변에 다음 턴의 음성 스타일이 적용된다. [lucid.py 565행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/app/lucid.py#L565) · [lucid.py 647행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/src/app/lucid.py#L647)

## 학습 데이터와 검증

**46. 제공된 학습 예제로 데이터 분할을 실행할 수 없다.** (높음 · 기본 데이터로 재현)

`seed.jsonl` 17줄을 개별 검사하면 1~4줄만 유효하다. 5~17줄은 문자열이 닫히지 않아 실패하고 기본 분할기는 5줄에서 중단한다. 안내에 적힌 예시 개수도 15개다. [seed.jsonl 5행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/training/dialogue/seed.jsonl#L5) · [split_dialogue_data.py 26행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/training/split_dialogue_data.py#L26) · [README.md 82행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/README.md#L82)

**47. 분할 출력과 원본의 경로가 겹치면 원본을 덮어쓴다.** (높음 · 임시 파일로 재현)

유효한 4행짜리 `train.jsonl`을 같은 폴더로 분할하자 원본 경로에 3행만 남고 1행은 검증 파일로 이동했다. 출력 과정에서 `scene_id`도 제거된다. 두 출력은 순차 기록되므로 두 번째 쓰기 실패 시 서로 다른 실행의 결과가 섞일 수 있다. [split_dialogue_data.py 97행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/training/split_dialogue_data.py#L97) · [split_dialogue_data.py 111행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/training/split_dialogue_data.py#L111)

**48. 학습과 검증에 같은 파일을 넣어도 검증을 통과할 수 있다.** (중간 · 코드)

학습기는 두 경로의 존재와 행 수를 확인하지만 같은 파일이나 서로 겹치는 예시를 거부하지 않는다. 또 직접 제공한 JSONL의 응답이 실제 인지 출력 스키마와 일치하는지 분할기처럼 검사하지 않아 검증 점수나 학습 목표를 신뢰하기 어렵다. [train_dialogue_lora.py 32행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/training/train_dialogue_lora.py#L32) · [train_dialogue_lora.py 53행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/training/train_dialogue_lora.py#L53) · [split_dialogue_data.py 59행](https://github.com/fidback494-crypto/Project-LUCID/blob/5ea128620b5663d94bdaff9982c9efe32dd80eb4/training/split_dialogue_data.py#L59)

