"""
Project LUCID

Artificial Mind Project

Module : Observation Engine

Creator : 시드
"""

from src.kernel.base_module import BaseModule
from src.utils import Logger

from .observation import Observation


class ObservationEngine(BaseModule):

    def __init__(self):
        super().__init__("ObservationEngine")

    def start(self):
        Logger.info("Observation Engine Started")

    def update(self):
        pass

    def stop(self):
        Logger.info("Observation Engine Stopped")

    def process(self, user_input: str) -> Observation:

        observation = Observation(
            source="user",
            content=user_input,
            importance=0.5,
        )

        Logger.info(f"[Observation] {observation.content}")

        return observation