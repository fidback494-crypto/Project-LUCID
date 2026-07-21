"""
Project LUCID

Artificial Mind Project

Module : Working Memory

Creator : 시드
"""

from collections import deque

from src.kernel.base_module import BaseModule
from src.utils import Logger


class WorkingMemory(BaseModule):
    """
    LUCID의 단기 기억
    """

    def __init__(self, capacity: int = 20):
        super().__init__("WorkingMemory")
        self.capacity = capacity
        self.memories = deque(maxlen=capacity)

    def start(self):
        Logger.info("Working Memory Started")

    def update(self):
        pass

    def stop(self):
        Logger.info("Working Memory Stopped")

    def add(self, item):
        self.memories.append(item)
        Logger.info(f"[WorkingMemory] + {item}")

    def recent(self):
        return list(self.memories)

    def clear(self):
        self.memories.clear()

    def size(self):
        return len(self.memories)