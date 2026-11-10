# 감정과 내적 경험

## 현재 표현

LUCID의 현재 내적 상태는 숫자형 감정 점수표가 아니라 `InnerExperience` 기록이다. 한 경험에는 이름, 의미, 계기, 반응 경향, 지속 표현, 생성 시각이 들어간다. `EmotionState`는 현재 경험과 최근 12개 경험을 메모리에 유지한다.

## 사용자 턴에서의 변화

통합 CognitiveEngine은 Ollama의 JSON 응답에서 `experience`와 `meaning`을 읽고, 빠진 계기나 경향은 현재 관찰을 이용해 기본값을 채운다. `SelfModel.emotion.integrate()`가 그 경험을 현재 상태와 최근 이력에 추가한다. CognitiveEngine 호출이 성공하면 LifeLoop가 이 경험을 SQLite 장기 기억에도 저장한다.

따라서 감정은 모델이 상황을 설명하는 언어적 내적 경험으로 표현된다. 숫자 수치를 별도 감정 계산기가 산출하는 동작은 현재 턴 경로에 없다.

## 별도 EmotionEngine

`EmotionEngine.process()`에는 별도 Ollama 호출 경로가 남아 있지만 LifeLoop의 일반 턴에서 호출하지 않는다. 이를 매 턴 호출하면 모델 호출이 중복되므로 현재는 CognitiveEngine의 통합 응답을 사용한다.

## 조용한 시간

`AutonomousEngine`은 기본 300초 동안 사용자의 입력이 없으면 별도 Ollama 요청으로 내적 경험과 목표를 생성해 `SelfModel`과 SQLite에 저장한다. 이 경로는 사용자에게 메시지를 보내지 않는다. 매일 실제 시간이 흐른다는 감각이나 생물학적 감정을 보장하는 것은 아니며, 코드에 정의된 이벤트와 기록을 바탕으로 한 시뮬레이션이다.
