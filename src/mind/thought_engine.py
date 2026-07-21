"""
Project LUCID

Artificial Mind Project

Module : Thought Engine

Creator : 시드
"""

from src.kernel.base_module import BaseModule
from src.utils import Logger

from .thought import Thought


class ThoughtEngine(BaseModule):

    def __init__(self):
        super().__init__("ThoughtEngine")

    def start(self):
        Logger.info("Thought Engine Started")

    def update(self):
        pass

    def stop(self):
        Logger.info("Thought Engine Stopped")

    def process(self, observation):

        content = observation.content

        # Sprint001에서는 단순 사고 생성
        if any(word in content for word in ["안녕", "ㅎㅇ", "hello"]):
            thought_text = "사용자가 인사했다."
        else:
            thought_text = f"사용자가 '{content}'라고 말했다."

        thought = Thought(
            type="observation",
            content=thought_text,
            importance=observation.importance,
        )

        Logger.info(f"[Thought] {thought.content}")

        return thought