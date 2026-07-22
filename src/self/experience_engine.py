"""
Project LUCID

Artificial Mind Project

Module : Experience Engine

Creator : 시드
"""

from src.kernel.base_module import BaseModule
from src.utils import Logger

from .experience import Experience


class ExperienceEngine(BaseModule):

    def __init__(self):
        super().__init__("ExperienceEngine")

    def start(self):
        Logger.info("Experience Engine Started")

    def update(self):
        pass

    def stop(self):
        Logger.info("Experience Engine Stopped")

    def process(self, state):

        experience = Experience(
            event=state.observation.content,
            result=state.response,
            confidence=1.0,
        )

        Logger.info(
            f"[Experience] {experience.event}"
        )

        return experience