"""
Project LUCID

Artificial Mind Project

Module : Thought Engine

Creator : 시드
"""

from src.kernel.base_module import BaseModule
from src.utils import Logger

from .thought import Thought
from .thought_queue import ThoughtQueue


class ThoughtEngine(BaseModule):

    def __init__(self):
        super().__init__("ThoughtEngine")
        self.queue = ThoughtQueue()

    def start(self):
        Logger.info("Thought Engine Started")

    def update(self):
        thought = self.queue.pop()

        if thought:
            Logger.info(f"[Thought] {thought.content}")

    def stop(self):
        Logger.info("Thought Engine Stopped")

    def process(self, observation):

     thought = Thought(
        type="observation",
        content=observation.content,
        importance=observation.importance,
    )

     self.queue.push(thought)

     Logger.info(f"[Thought] {thought.content}")

     return thought