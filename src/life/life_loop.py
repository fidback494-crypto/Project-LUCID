"""
Project LUCID

Artificial Mind Project

Module : Life Loop

Creator : 시드
"""

from src.utils import Logger


class LifeLoop:

    def __init__(
        self,
        observation_engine,
        working_memory,
        thought_engine,
        decision_engine,
        language_engine,
    ):

        self.observation = observation_engine
        self.memory = working_memory
        self.thought = thought_engine
        self.decision = decision_engine
        self.language = language_engine

    def process(self, user_input: str) -> str:

        Logger.info("===== Life Cycle =====")

        observation = self.observation.process(user_input)

        self.memory.add(observation)

        thought = self.thought.process(observation)

        decision = self.decision.process(thought)

        reply = self.language.process(decision)

        Logger.info("===== End Cycle =====")

        return reply