from src.kernel.base_module import BaseModule
from src.utils import Logger

from .decision import Decision


class DecisionEngine(BaseModule):

    def __init__(self):
        super().__init__("DecisionEngine")

    def start(self):
        Logger.info("Decision Engine Started")

    def update(self):
        pass

    def stop(self):
        Logger.info("Decision Engine Stopped")

    def process(self, thought):

     decision = Decision(
        action="respond",
        reason=thought.content,
        confidence=0.9,
    )

     Logger.info(f"[Decision] {decision.reason}")

     return decision