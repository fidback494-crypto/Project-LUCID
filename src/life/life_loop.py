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

        self.self_model = self_model

        self.long_memory = long_memory
        self.extractor = extractor
        self.search = search

    def process(self, user_input: str):

        Logger.info("========== Life Loop ==========")

        state = BrainState()
        state.self_model = self.self_model

        # -------------------------------------------------
        # 1. Observation
        # -------------------------------------------------

        state.observation = self.observation.process(user_input)

        # -------------------------------------------------
        # 2. Working Memory
        # -------------------------------------------------

        self.memory.process(state.observation)
        state.working_memory = self.memory.recent(5)

        # -------------------------------------------------
        # 3. Memory Extraction
        # -------------------------------------------------

        record = self.extractor.extract(state.observation)

        Logger.info(f"[Debug] Extract Result : {record}")

        if record:

            self.long_memory.store(record)

            Logger.info(
                f"[LongMemory] Stored : {record.content}"
            )

        else:

            Logger.info("[LongMemory] Nothing Stored")

        # -------------------------------------------------
        # 4. Long Memory Search
        # -------------------------------------------------

        state.long_memory = self.search.search(
            state.observation
        )

        Logger.info(
            f"[LongMemory] Search Result : {state.long_memory}"
        )

        # -------------------------------------------------
        # 5. Reasoning
        # -------------------------------------------------

        state.reason = self.reasoning.process(
            state.observation
        )

        # -------------------------------------------------
        # 6. Goal
        # -------------------------------------------------

        state.goal = self.goal.process(state)

        # -------------------------------------------------
        # 7. Thought
        # -------------------------------------------------

        state.thought = self.thought.process(
            state.reason
        )

        # -------------------------------------------------
        # 8. Planning
        # -------------------------------------------------

        state.plan = self.planning.process(
            state.goal,
            state.thought,
        )

        # -------------------------------------------------
        # 9. Decision
        # -------------------------------------------------

        state.decision = self.decision.process(
            state.plan
        )

        # -------------------------------------------------
        # 10. Language
        # -------------------------------------------------

        state.response = self.language.process(state)

        # -------------------------------------------------
        # 11. Reflection
        # -------------------------------------------------

        state.reflection = self.reflection.process(state)

        # -------------------------------------------------
        # 12. Experience
        # -------------------------------------------------

        state.experience = self.experience.process(state)

        # -------------------------------------------------
        # 13. Working Memory Update
        # -------------------------------------------------

        self.memory.process(state.reflection)

        Logger.info("========== End ==========")

        return state.response