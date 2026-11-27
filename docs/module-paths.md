# 예전 파일의 현재 위치

이전 커밋 `d74a138`에서 내용이 있던 `src/`의 Python 파일 91개는 현재 `lucid/`의 파일 55개에 대응한다. 왼쪽에서 예전 파일명을 찾고 오른쪽 경로를 누르면 현재 소스를 열 수 있다. 콘솔 진입점은 [lucid/cli.py](../lucid/cli.py)다.

예전 모듈 최상위에서 정의한 클래스 81개의 이름이 모두 현재 소스에 있다. 브라우저 서버 내부의 중첩 클래스 `RequestHandler`는 현재 모듈 최상위의 `_RequestHandler`로 옮겼다. 호환 이름 `UtauTTSClient`는 계속 `KoreanTTSClient`를 가리킨다. 메서드 인자나 처리 방식이 필요한 경우 연결된 소스를 확인한다.

## 앱 실행과 커널

| 예전 파일 | 현재 파일 | 클래스·함수 또는 공개 이름 |
| --- | --- | --- |
| `src/app/lucid.py` | [lucid/app.py](../lucid/app.py) | `LucidEngine` |
| `src/autonomy/autonomous_engine.py`<br>`src/autonomy/autonomous_goal.py` | [lucid/autonomy.py](../lucid/autonomy.py) | `AutonomousEngine`, `AutonomousGoal` |
| `src/conversation/conversation_manager.py` | [lucid/conversation.py](../lucid/conversation.py) | `ConversationManager` |
| `src/event/event.py`<br>`src/event/event_manager.py`<br>`src/kernel/event_bus.py` | [lucid/core/events.py](../lucid/core/events.py) | `Event`, `EventManager`, `EventBus` |
| `src/kernel/base_module.py`<br>`src/kernel/kernel.py` | [lucid/core/kernel.py](../lucid/core/kernel.py) | `BaseModule`, `Kernel` |
| `src/context/cognitive_context.py`<br>`src/context/context.py`<br>`src/core/brain_state.py`<br>`src/core/state.py`<br>`src/language/context.py` | [lucid/core/state.py](../lucid/core/state.py) | `CognitiveContext`, `Context`, `BrainState`, `LucidState`, `LanguageContext` |
| `src/workspace/workspace.py`<br>`src/workspace/workspace_engine.py`<br>`src/workspace/workspace_manager.py` | [lucid/core/workspace.py](../lucid/core/workspace.py) | `Workspace`, `WorkspaceEngine`, `WorkspaceManager` |
| `src/life/life_loop.py` | [lucid/life/loop.py](../lucid/life/loop.py) | `LifeLoop` |
| `src/life/consciousness.py`<br>`src/life/heartbeat.py` | [lucid/life/signals.py](../lucid/life/signals.py) | `Consciousness`, `Heartbeat` |
| `src/utils/__init__.py`<br>`src/utils/logger.py` | [lucid/log.py](../lucid/log.py) | `Logger` |

## 행동과 도구

| 예전 파일 | 현재 파일 | 클래스·함수 또는 공개 이름 |
| --- | --- | --- |
| `src/action/action_engine.py`<br>`src/action/action_registry.py` | [lucid/actions/engine.py](../lucid/actions/engine.py) | `ActionEngine`, `ActionRegistry` |
| `src/action/action.py`<br>`src/action/action_result.py` | [lucid/actions/models.py](../lucid/actions/models.py) | `Action`, `ActionResult` |
| `src/action/tools/__init__.py` | [lucid/actions/tools/__init__.py](../lucid/actions/tools/__init__.py) | `CalculatorTool`, `FileTool`, `MemoryTool`, `PythonTool`, `TimeTool`, `WebTool` |
| `src/action/tools/base_tool.py` | [lucid/actions/tools/base.py](../lucid/actions/tools/base.py) | `BaseTool` |
| `src/action/tools/calculator.py`<br>`src/action/tools/calculator_tool.py` | [lucid/actions/tools/calculator.py](../lucid/actions/tools/calculator.py) | `CalculatorTool` |
| `src/action/tools/file_tool.py` | [lucid/actions/tools/files.py](../lucid/actions/tools/files.py) | `FileTool` |
| `src/action/tools/memory_tool.py` | [lucid/actions/tools/memory.py](../lucid/actions/tools/memory.py) | `MemoryTool` |
| `src/action/tools/python_tool.py` | [lucid/actions/tools/python.py](../lucid/actions/tools/python.py) | `PythonTool` |
| `src/action/tools/time_tool.py` | [lucid/actions/tools/time.py](../lucid/actions/tools/time.py) | `TimeTool` |
| `src/action/tools/web_tool.py` | [lucid/actions/tools/web.py](../lucid/actions/tools/web.py) | `_SearchResultsParser`, `WebTool` |

## 인지·사고·언어

| 예전 파일 | 현재 파일 | 클래스·함수 또는 공개 이름 |
| --- | --- | --- |
| `src/cognitive/cognitive_engine.py` | [lucid/cognition/engine.py](../lucid/cognition/engine.py) | `CognitiveEngine` |
| `src/cognitive/basic_conversation.py` | [lucid/cognition/fallback.py](../lucid/cognition/fallback.py) | `BasicConversationFallback` |
| `src/cognitive/cognitive_prompt.py` | [lucid/cognition/prompt.py](../lucid/cognition/prompt.py) | `CognitivePrompt` |
| `src/emotion/emotion_engine.py`<br>`src/emotion/emotion_prompt.py` | [lucid/emotion/engine.py](../lucid/emotion/engine.py) | `EmotionEngine`, `EmotionPrompt` |
| `src/emotion/emotion_state.py`<br>`src/emotion/inner_experience.py` | [lucid/emotion/model.py](../lucid/emotion/model.py) | `EmotionState`, `InnerExperience` |
| `src/language/language_engine.py` | [lucid/language/engine.py](../lucid/language/engine.py) | `LanguageEngine` |
| `src/language/ollama_client.py` | [lucid/language/ollama.py](../lucid/language/ollama.py) | `OllamaClient` |
| `src/language/prompt_builder.py` | [lucid/language/prompts.py](../lucid/language/prompts.py) | `PromptBuilder` |
| `src/mind/decision_engine.py` | [lucid/mind/decisions.py](../lucid/mind/decisions.py) | `DecisionEngine` |
| `src/reflection/reflection.py`<br>`src/reflection/reflection_engine.py`<br>`src/self/experience.py`<br>`src/self/experience_engine.py` | [lucid/mind/feedback.py](../lucid/mind/feedback.py) | `Reflection`, `ReflectionEngine`, `Experience`, `ExperienceEngine` |
| `src/goal/goal.py`<br>`src/goal/goal_engine.py` | [lucid/mind/goals.py](../lucid/mind/goals.py) | `Goal`, `GoalEngine` |
| `src/cognitive/cognitive_result.py`<br>`src/mind/decision.py`<br>`src/mind/plan.py`<br>`src/mind/reason.py`<br>`src/mind/thought.py` | [lucid/mind/models.py](../lucid/mind/models.py) | `CognitiveResult`, `Decision`, `Plan`, `Reason`, `Thought` |
| `src/world/observation.py`<br>`src/world/observation_engine.py` | [lucid/mind/observation.py](../lucid/mind/observation.py) | `Observation`, `ObservationEngine` |
| `src/mind/planner.py`<br>`src/mind/planning_engine.py` | [lucid/mind/planning.py](../lucid/mind/planning.py) | `Planner`, `PlanningEngine` |
| `src/mind/reasoning_engine.py` | [lucid/mind/reasoning.py](../lucid/mind/reasoning.py) | `ReasoningEngine` |
| `src/mind/reasoning_prompt.py` | [lucid/mind/reasoning_prompt.py](../lucid/mind/reasoning_prompt.py) | `ReasoningPrompt` |
| `src/skill/skill.py` | [lucid/mind/skills.py](../lucid/mind/skills.py) | `Skill` |
| `src/mind/thought_engine.py`<br>`src/mind/thought_queue.py` | [lucid/mind/thinking.py](../lucid/mind/thinking.py) | `ThoughtEngine`, `ThoughtQueue` |

## 기억과 캐릭터

| 예전 파일 | 현재 파일 | 클래스·함수 또는 공개 이름 |
| --- | --- | --- |
| `src/memory/__init__.py` | [lucid/memory/__init__.py](../lucid/memory/__init__.py) | `MemoryEngine`, `MemoryExtractor`, `MemorySearch` |
| `src/memory/extractor.py`<br>`src/memory/memory_extractor.py`<br>`src/memory/memory_record.py` | [lucid/memory/facts.py](../lucid/memory/facts.py) | `MemoryExtractor`, `MemoryRecord`, `normalize_memory_value`, `memory_key`, `infer_legacy_memory` |
| `src/memory/database.py`<br>`src/memory/memory.py` | [lucid/memory/legacy.py](../lucid/memory/legacy.py) | `get_connection`, `MemoryEngine` |
| `src/memory/memory_search.py`<br>`src/memory/search.py` | [lucid/memory/search.py](../lucid/memory/search.py) | `MemorySearch` |
| `src/memory/long_term_memory.py` | [lucid/memory/store.py](../lucid/memory/store.py) | `LongTermMemory` |
| `src/memory/working_memory.py` | [lucid/memory/working.py](../lucid/memory/working.py) | `WorkingMemory` |
| `src/self/__init__.py` | [lucid/persona/__init__.py](../lucid/persona/__init__.py) | `SelfModel` |
| `src/self/identity.py` | [lucid/persona/identity.py](../lucid/persona/identity.py) | `Identity` |
| `src/self/attention.py`<br>`src/self/needs.py`<br>`src/self/self_model.py` | [lucid/persona/model.py](../lucid/persona/model.py) | `Attention`, `Needs`, `SelfModel` |

## 브라우저·화면·음성

| 예전 파일 | 현재 파일 | 클래스·함수 또는 공개 이름 |
| --- | --- | --- |
| `src/browser/__init__.py` | [lucid/browser/__init__.py](../lucid/browser/__init__.py) | `BrowserBridge`, `PageContextStore` |
| `src/browser/local_bridge.py` | [lucid/browser/bridge.py](../lucid/browser/bridge.py) | `BrowserBridge`, `_RequestHandler` |
| `src/browser/page_context.py` | [lucid/browser/context.py](../lucid/browser/context.py) | `PageContext`, `PageContextStore` |
| `src/vision/__init__.py` | [lucid/vision/__init__.py](../lucid/vision/__init__.py) | `VisionEngine`, `VisualPresence` |
| `src/vision/vision_client.py`<br>`src/vision/vision_engine.py` | [lucid/vision/engine.py](../lucid/vision/engine.py) | `VisionClient`, `VisionEngine` |
| `src/vision/visual_presence.py` | [lucid/vision/presence.py](../lucid/vision/presence.py) | `VisualPresence` |
| `src/voice/__init__.py` | [lucid/voice/__init__.py](../lucid/voice/__init__.py) | `KoreanTTSClient` |
| `src/voice/korean_tts_client.py`<br>`src/voice/utautts_client.py` | [lucid/voice/tts.py](../lucid/voice/tts.py) | `KoreanTTSClient`, `UtauTTSClient` |

## 캐릭터 설정 자료

두 설정 문서는 이전 커밋과 바이트 단위로 내용이 같다.

| 예전 파일 | 현재 파일 |
| --- | --- |
| `src/self/CHARACTER_FINAL_APPEARANCE.md` | [lucid/persona/CHARACTER_FINAL_APPEARANCE.md](../lucid/persona/CHARACTER_FINAL_APPEARANCE.md) |
| `src/self/WORLD_MEMORY_ARCHIVE.md` | [lucid/persona/WORLD_MEMORY_ARCHIVE.md](../lucid/persona/WORLD_MEMORY_ARCHIVE.md) |

예전 구현도 로컬에서 대조할 수 있다. 예를 들어 `git show d74a138:src/app/lucid.py`로 당시 앱 진입점을 읽는다.


## 실행·설정·개발 파일

| 예전 파일 | 현재 위치와 용도 |
| --- | --- |
| `main.py` | [main.py](../main.py)에 실행 진입점과 `DEBUG`가 있고, [lucid/cli.py](../lucid/cli.py)가 서버 설정과 콘솔 실행을 맡는다. |
| `config.py` | [lucid/settings.py](../lucid/settings.py)에 기본 모델과 데이터 경로, 이전 기본 프롬프트가 있다. |
| `test_logger.py`, `test_reasoning.py` | [tests/test_runtime.py](../tests/test_runtime.py)에서 로그·추론·작업 상태를 검사한다. |
| `requirements-portable.txt`, `requirements.txt` | [requirements.txt](../requirements.txt)에 앱 의존성을, [이전 Windows 패키지 목록](../tools/legacy/requirements-windows.txt)에 당시 환경을 보관한다. |
| `requirements-training.txt` | [pyproject.toml](../pyproject.toml)의 `training` 그룹에 GPU 학습 의존성이 있다. |
| `migrate_to_brain.ps1` | [이전 PowerShell 스크립트](../tools/legacy/migrate_to_brain.ps1.txt)는 과거 폴더 구조의 이동 기록이다. |
