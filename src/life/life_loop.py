"""
Project LUCID

Artificial Mind Project

Module : Life Loop

Creator : 시드
"""

from src.core.brain_state import BrainState
from src.utils import Logger


class LifeLoop:

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
    ):

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

    # =================================================
    # Process
    # =================================================

    def process(self, user_input: str):

        Logger.info("========== Life Loop ==========")

        state = BrainState()

        # =================================================
        # Workspace
        # =================================================

        workspace = self.workspace.current()

        workspace.clear()

        workspace.self_model = self.self_model

        state.self_model = self.self_model

        # =================================================
        # Observation
        # =================================================

        state.observation = self.observation.process(
            user_input
        )

        workspace.observation = state.observation

        # =================================================
        # Conversation
        # =================================================

        state.conversation = self.conversation.messages()

        workspace.conversation = state.conversation

        # =================================================
        # Working Memory
        # =================================================

        self.memory.process(
            state.observation
        )

        state.working_memory = self.memory.recent(5)

        workspace.working_memory = state.working_memory

        # =================================================
        # Memory Extraction
        # =================================================

        record = self.extractor.extract(
            state.observation
        )

        if record:

            self.long_memory.store(record)

            Logger.info(
                f"[LongMemory] Stored : {record.content}"
            )

        # =================================================
        # Long Memory Search
        # =================================================

        state.long_memory = self.search.search(
            state.observation
        )

        workspace.long_memory = state.long_memory

        # =================================================
        # Decision and Action
        #
        # Tool selection is rule-based so it does not require an LLM call.
        # =================================================

        state.decision = self.decision.process(
            state
        )

        workspace.decision = state.decision

        # =================================================
        # Action
        # =================================================

        state.action = state.decision.action_object

        workspace.action = state.action

        state.action_result = self.action.process(
            state.action
        )

        workspace.action_result = state.action_result

        # =================================================
        # Action Log
        # =================================================

        if state.action_result is not None:

            Logger.info(
                "[ActionResult] "
                f"success={state.action_result.success} "
                f"output={state.action_result.output}"
            )

        # =================================================
        # Unified Cognitive Cycle
        #
        # One LLM call creates inner experience, reasoning, thought, plan,
        # and the final response after any action result is available.
        # =================================================

        state.response = self.cognitive.process(state)

        workspace.response = state.response
        workspace.emotion = state.emotion
        workspace.reason = state.reason
        workspace.thought = state.thought
        workspace.goal = state.goal
        workspace.plan = state.plan

        if state.emotion.current is not None:

            self.long_memory.store_inner_experience(
                state.emotion.current
            )

        # =================================================
        # Conversation Update
        # =================================================

        self.conversation.add_user(
            state.observation.content
        )

        self.conversation.add_assistant(
            state.response
        )

        # =================================================
        # Reflection
        # =================================================

        state.reflection = self.reflection.process(
            state
        )

        workspace.reflection = state.reflection

        # =================================================
        # Experience
        # =================================================

        state.experience = self.experience.process(
            state
        )

        workspace.experience = state.experience

        # =================================================
        # Working Memory Update
        # =================================================

        self.memory.process(
            state.reflection
        )

        Logger.info(
            "========== End =========="
        )

        return state.response
