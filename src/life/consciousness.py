"""
Project LUCID

Artificial Mind Project

Module : Consciousness

Creator : 시드
"""

from src.kernel.base_module import BaseModule
from src.utils import Logger


class Consciousness(BaseModule):
    """LUCID의 의식을 담당하는 기관"""

    def __init__(self):
        super().__init__("Consciousness")
        self.thought_count = 0

    def start(self):
        Logger.info("Consciousness Started")

    def update(self):
        self.thought_count += 1
        Logger.info(f"Thinking... ({self.thought_count})")

    def stop(self):
        Logger.info("Consciousness Stopped")