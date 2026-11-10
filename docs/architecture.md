# 현재 실행 구조

이 문서는 현재 `main.py`에서 실제로 이어지는 경로를 설명한다. 디렉터리에 같은 이름의 기관이 있어도, 모든 기관이 매 입력마다 독립 실행되는 것은 아니다.

## 시작

1. `main.py`에서 Ollama와 한국어 음성 서버 주소를 설정한다.
2. `LucidEngine`이 LifeLoop, 기억, 도구, 브라우저·화면, 음성 기관을 만든다.
3. `boot()`가 Kernel에 기관을 등록하고 각 `start()`를 호출한다.
4. `CognitiveEngine.start()`가 Ollama 모델을 미리 불러온다. 이는 대화 턴의 생성 호출과 별개다.
5. 음성 서버 연결을 확인하고 브라우저 브리지, 화면 관찰, 자율 내적 경험 스레드를 시작한다.

## 입력 한 턴

```text
콘솔 또는 공유 화면
  → BrainState와 Workspace 초기화
  → 관찰, 최근 대화, 작업 기억 구성
  → 명시적 사용자 사실 저장 및 관련 기억 검색
  → 규칙 기반 도구 선택과 실행
  → CognitivePrompt가 기억·화면·도구 결과를 묶음
  → CognitiveEngine이 역할이 구분된 문맥을 Ollama /api/chat에 전송
  → JSON 응답을 reply, 내적 경험, 의도, 생각, 목표, 계획, 음성 스타일로 반영
  → 최근 대화와 SQLite 대화 에피소드 저장
  → Reflection/Experience 기록
  → 콘솔 출력 및 선택적 한국어 TTS
```

일반 텍스트 턴에서 CognitiveEngine은 Ollama를 한 번 호출해 답변과 내부 상태를 함께 만든다. 기본으로 최근 대화 10개 메시지를 보내며, `LUCID_CHAT_HISTORY_MESSAGES`로 0~20개까지 조정한다. 기억 검색과 액션 선택은 로컬 규칙/SQLite를 사용한다. 사용자가 화면을 공유하면 비전 분석 호출이 먼저 추가될 수 있고, 음성 출력은 별도 TTS 서버 호출이다.

## 실제 사용되는 기관과 준비 상태

- 매 턴 호출: `ObservationEngine`, `WorkingMemory`, `MemoryExtractor`, `MemorySearch`, `DecisionEngine`, `ActionEngine`, `CognitiveEngine`, `ReflectionEngine`, `ExperienceEngine`.
- CognitiveEngine의 한 JSON 응답을 바탕으로 현재는 `InnerExperience`, `Reason`, `Thought`, `Goal`, `Plan` 객체를 만든다. 이 방식은 각 기관이 Ollama를 따로 부르지 않아 호출 횟수를 줄인다.
- `CognitivePrompt`는 별도 Ollama 호출 없이 기억·화면·도구 결과를 한 번의 응답 요청에 조립한다. 도구 결과에는 성공 여부와 내용을 함께 넣는다.
- Ollama가 일시적으로 연결되지 않아도 인사·안부·감사·간단한 공감은 `BasicConversationFallback`이 응답한다. 도구 결과가 이미 성공했다면 해당 결과를 바로 전달한다. 이 로컬 보완 경로는 자유 주제의 일반 답변을 대신하지 않으므로, 그때는 Ollama 연결이 필요하다.
- `EmotionEngine`, `ReasoningEngine`, `ThoughtEngine`, `GoalEngine`, `PlanningEngine`, `LanguageEngine`은 Kernel에 등록되고 시작되지만, 일반 턴에서 각자의 `process()`는 호출되지 않는다. 이들의 역할 일부는 통합 CognitiveEngine 경로가 맡는다.
- `Kernel.update()`는 사용자의 텍스트·화면 처리 전에 호출되어 등록된 기관의 업데이트 훅을 실행한다. Heartbeat와 Consciousness는 이 시점마다 이벤트 기반으로 갱신된다.
- `AutonomousEngine`은 별도 백그라운드 스레드에서 상호작용 없이 기본 300초가 지난 뒤 내부 경험과 자율 목표를 만든다.
- 일반 콘솔 턴의 Reflection 결과는 현재 고정 요약이며, 응답 품질을 채점하거나 자동으로 모델을 학습시키지는 않는다.

## 도구

현재 등록되는 도구는 calculator, file, memory, python, time, web이다. 파일 도구는 프로젝트 폴더 안의 텍스트 파일을 읽거나 목록만 보여준다. Python 도구는 표현식과 제한된 수학 함수만 평가한다. Web 도구는 DuckDuckGo HTML 검색 결과를 가져오며, 결과 텍스트는 신뢰되지 않는 참고 자료로 프롬프트에 전달한다.

`DecisionEngine`은 사용자의 표현에서 도구를 고르는 규칙 기반 분기다. 이 단계는 모델이 직접 임의 코드를 호출하는 tool-calling 구조가 아니다.

도구 연결은 `LucidEngine` 등록 → `DecisionEngine` 선택 → `ActionEngine`의 `ActionResult` → `BrainState.action_result` → `CognitivePrompt` 순서다. 파일 도구는 프로젝트 바깥 경로, 비밀 설정, 로컬 데이터베이스, 학습 자료를 읽지 않도록 제한한다. Python 도구는 파일·네트워크·명령 실행을 허용하지 않는다.

## 아직 연결하지 않은 빈 스캐폴드

현재 실행 경로에서 사용되지 않는 `attention`, `brain`, `context`, `deliberation`, `imagination`, `learning`, `metacognition`, `monologue`, `skill`, `task` 등의 구형·실험용 스캐폴드 파일은 별도 동작을 임의로 만들어 연결하지 않았다. 일부 활성 패키지 안의 빈 보조 파일(`goal_manager.py`, `workspace_item.py` 등)도 같은 상태다. 이 파일들은 `main.py`에서 import되지 않으며, 현재 동작은 `src/life`, `src/mind`, `src/cognitive`, `src/goal`, `src/workspace`의 구현 경로를 따른다. 빈 `__init__.py`는 Python 패키지 표식이므로 그대로 둔다.

## 실패 처리

Ollama 시간 초과 또는 연결 실패 때는 인지 상태 생성을 건너뛰고 기본 대화·성공한 도구 결과·연결 안내 중 적절한 응답을 반환한다. 한국어 입력에 비한국어 답변이 오면 한국어 fallback을 쓴다. 도구 실행 실패는 `ActionResult`로 CognitiveEngine 문맥에 전달된다.
