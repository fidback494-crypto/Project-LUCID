"""
Project LUCID

Artificial Mind Project

Module : Heartbeat

Creator : 시드
"""

from src.kernel.base_module import BaseModule
from src.utils import Logger


class Heartbeat(BaseModule):
    """LUCID의 내부 시간을 관리하는 기관"""

    def __init__(self):
        super().__init__("Heartbeat")
        self.tick_count = 0

    def start(self):
        Logger.info("Heartbeat Started")

    def update(self):
        self.tick_count += 1
        Logger.info(f"Heartbeat : {self.tick_count}")

    def stop(self):
        Logger.info("Heartbeat Stopped")