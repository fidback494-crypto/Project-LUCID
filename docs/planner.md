# 목표·계획·행동

## 턴 안의 순서

현재 계획 생성은 도구 선택 전에 별도 Plan LLM을 부르는 방식이 아니다. `DecisionEngine`이 입력 문구를 규칙으로 분류해 calculator, file, memory, python, time, web 중 도구를 고르거나 일반 응답으로 표시한다. 도구가 필요하면 `ActionEngine`이 등록된 도구를 실행하고 `ActionResult`를 만든다.

그 다음 CognitiveEngine의 단일 Ollama 호출이 답변과 `intent`, `experience`, `meaning`, `speech_style`을 생성한다. 현재 JSON 스키마는 이 다섯 키만 허용하므로 `goal`, `plan1`, `plan2`는 응답에 들어갈 수 없다. CognitiveEngine은 내부 기본 목표와 1단계 기본 계획 객체를 만들어 BrainState와 Workspace에 보관한다.

## 제한

- 도구 선택은 자연어 이해 모델이 아니라 키워드/정규식 분기다.
- 행동은 현재 입력에 필요한 단일 도구 실행이며, 계획 여러 단계를 차례로 실행하는 TaskEngine 루프는 일반 대화에 연결되어 있지 않다.
- 별도 `GoalEngine`과 `PlanningEngine`의 `process()`는 일반 LifeLoop 경로에서 호출되지 않는다.
- `DecisionEngine`이 이름을 아는 도구라도 `LucidEngine`에 등록되어 있지 않으면 실행할 수 없다.
