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
    ):

        self.observation = observation_engine
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

    def process(self, user_input: str):

        Logger.info("========== Life Loop ==========")

        state = BrainState()
        state.self_model = self.self_model

        # =================================================
        # 1. Observation
        # =================================================

        state.observation = self.observation.process(user_input)

        # =================================================
        # 2. Conversation History
        # =================================================

        state.conversation = self.conversation.messages()

        # =================================================
        # 3. Working Memory
        # =================================================

        self.memory.process(state.observation)
        state.working_memory = self.memory.recent(5)

        # =================================================
        # 4. Memory Extraction
        # =================================================

        record = self.extractor.extract(state.observation)

        if record:

            self.long_memory.store(record)

            Logger.info(
                f"[LongMemory] Stored : {record.content}"
            )

        # =================================================
        # 5. Long Memory Search
        # =================================================

        state.long_memory = self.search.search(
            state.observation
        )

        Logger.info(
            f"[LongMemory] Search : {state.long_memory}"
        )

        # =================================================
        # 6. Reasoning (LLM)
        # =================================================

        state.reason = self.reasoning.process(state)

        # =================================================
        # 7. Thought (LLM)
        # =================================================

        state.thought = self.thought.process(state)

        # =================================================
        # 8. Goal
        # =================================================

        state.goal = self.goal.process(state)

        # =================================================
        # 9. Planning (LLM)
        # =================================================

        state.plan = self.planning.process(state)

        # =================================================
        # 10. Decision
        # =================================================

        state.decision = self.decision.process(
            state.plan
        )

        # =================================================
        # 11. Language
        # =================================================

        state.response = self.language.process(state)

        # =================================================
        # 12. Conversation Update
        # =================================================

        self.conversation.add_user(
            state.observation.content
        )

        self.conversation.add_assistant(
            state.response
        )

        # =================================================
        # 13. Reflection
        # =================================================

        state.reflection = self.reflection.process(state)

        # =================================================
        # 14. Experience
        # =================================================

        state.experience = self.experience.process(state)

        # =================================================
        # 15. Working Memory Update
        # =================================================

        self.memory.process(state.reflection)

        Logger.info("========== End ==========")

        return state.response