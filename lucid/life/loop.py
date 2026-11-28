"""한 번의 입력에서 관찰·기억·도구·인지·응답으로 이어지는 대화 주기."""

from collections import deque
from time import monotonic

from lucid.log import Logger


class LifeLoop:
    """대화와 자동 관찰의 처리 경로를 공유하되 사용자 대화 이력을 구분한다."""

    def __init__(
        self,
        observation_engine,
        emotion_engine,
        working_memory,
        reasoning_engine,
        thought_engine,
        goal_engine,
        planning_engine,
        decision_engine,
        language_engine,
        reflection_engine,
        experience_engine,
        conversation_manager,
        self_model,
        long_memory,
        extractor,
        search,
        workspace_engine,
        action_engine,
        cognitive_engine,
        browser_context_store=None,
    ):
        """주입된 엔진과 저장소를 한 세션의 처리 순서에 연결한다."""
        self.observation = observation_engine
        self.emotion = emotion_engine
        self.memory = working_memory
        self.reasoning = reasoning_engine
        self.thought = thought_engine
        self.goal = goal_engine
        self.planning = planning_engine
        self.decision = decision_engine
        self.language = language_engine
        self.reflection = reflection_engine
        self.experience = experience_engine
        self.conversation = conversation_manager

        self.self_model = self_model

        self.long_memory = long_memory
        self.extractor = extractor
        self.search = search

        self.workspace = workspace_engine
        self.action = action_engine
        self.cognitive = cognitive_engine
        self.browser_context_store = browser_context_store
        self._recent_text_latencies = deque(maxlen=30)

    def process(
        self,
        user_input: str,
        visual_observation="",
        *,
        allow_tools=True,
        record_dialogue=True,
        conversation_text=None,
    ) -> str:
        """입력과 선택적 화면 설명으로 답변 문자열을 반환한다.

        allow_tools는 도구 호출을, record_dialogue는 대화 이력 저장을 제어한다.
        명령을 모델용 문장으로 바꾼 경우 conversation_text에 사용자 원문을 전달한다.
        """
        started = monotonic()
        state = self.workspace.current()
        state.clear()
        state.self_model = self.self_model
        state.emotion = self.self_model.emotion
        state.observation = self.observation.process(user_input)
        transcript = conversation_text if conversation_text is not None else user_input

        state.speech_register = self.conversation.update_speech_register(transcript)
        state.conversation = self.conversation.messages()
        if self.browser_context_store is not None:
            state.web_context = self.browser_context_store.prompt_context()
        state.visual_observation = visual_observation

        if record_dialogue:
            self.memory.process(state.observation)
            if conversation_text is None:
                record = self.extractor.extract(state.observation)
                if record is not None:
                    self.long_memory.store(record)
        state.working_memory = self.memory.recent(5)
        state.long_memory = self.search.search(state.observation)
        state.related_inner_experiences = self.long_memory.search_inner_experiences(
            transcript, limit=3
        )
        state.related_conversation_episodes = (
            self.long_memory.search_conversation_episodes(
                transcript,
                limit=3,
                years=self.long_memory.MIN_CONVERSATION_MEMORY_YEARS,
                include_archived=False,
            )
        )
        state.session_summaries = self.long_memory.session_summaries(
            transcript, limit=2
        )
        state.last_conversation_gap = self.long_memory.last_conversation_gap()

        state.decision = self.decision.process(state)
        state.action = state.decision.action_object
        if not allow_tools:
            state.action.need_action = False
        state.action_result = self.action.process(state.action)

        state.response = self.cognitive.process(state)
        if record_dialogue:
            if state.cognitive_success and state.emotion.current is not None:
                self.long_memory.store_inner_experience(state.emotion.current)
            self.conversation.add_user(transcript)
            self.conversation.add_assistant(state.response)
            self.long_memory.store_conversation_episode(
                user_text=transcript,
                assistant_text=state.response,
                intent=state.reason.intent
                if state.reason is not None
                else "conversation",
            )
        state.reflection = self.reflection.process(state)
        state.experience = self.experience.process(state)
        if record_dialogue:
            self.memory.process(state.reflection)
        self._log_latency(monotonic() - started)
        return state.response

    def _log_latency(self, seconds):
        """텍스트 응답 시간을 초 단위로 받아 최근 30회 평균과 모델 상태를 기록한다."""
        self._recent_text_latencies.append(seconds)
        average_seconds = sum(self._recent_text_latencies) / len(
            self._recent_text_latencies
        )
        metrics = getattr(getattr(self.cognitive, "client", None), "last_metrics", {})
        if metrics.get("error"):
            model_state = "unavailable"
        elif metrics.get("load_seconds", 0) >= 0.5:
            model_state = "cold"
        else:
            model_state = "warm"
        Logger.info(
            f"[Latency] text_ready={seconds:.3f}s "
            f"rolling_avg_{len(self._recent_text_latencies)}={average_seconds:.3f}s model={model_state}"
        )
