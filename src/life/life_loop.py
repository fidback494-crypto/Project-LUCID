"""
Project LUCID

Artificial Mind Project

Module : Life Loop

Creator : 시드
"""

from src.utils import Logger
from src.language.context import LanguageContext


class LifeLoop:

    def __init__(
        self,
        observation_engine,
        working_memory,
        reasoning_engine,
        thought_engine,
        planning_engine,
        decision_engine,
        language_engine,
        self_model,
    ):

        self.observation = observation_engine
        self.memory = working_memory
        self.reasoning = reasoning_engine
        self.thought = thought_engine
        self.planning = planning_engine
        self.decision = decision_engine
        self.language = language_engine
        self.self_model = self_model

    def process(self, user_input):

        Logger.info("========== Life Loop ==========")

        observation = self.observation.process(user_input)

        self.memory.process(observation)

        reason = self.reasoning.process(observation)

        thought = self.thought.process(reason)

        plan = self.planning.process(thought)

        decision = self.decision.process(plan)

        context = LanguageContext(
            observation=observation,
            reason=reason,
            thought=thought,
            decision=decision,
            memory=self.memory.recent(5),
            self_model=self.self_model,
        )

        reply = self.language.process(context)

        Logger.info("========== End ==========")

        return reply