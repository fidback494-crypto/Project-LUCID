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

    def process(self, item):
        """
        LifeLoop가 사용하는 공식 인터페이스
        """

        self.memories.append(item)

        Logger.info(
            f"[WorkingMemory] Stored ({type(item).__name__})"
        )

        return item

    def add(self, item):
        """
        기존 코드와의 호환
        """

        return self.process(item)

    def recent(self, limit=None):

        memories = list(self.memories)

        if limit is None:
            return memories

        return memories[-limit:]

    def latest(self):

        if not self.memories:
            return None

        return self.memories[-1]

    def clear(self):

        self.memories.clear()

    def size(self):

        return len(self.memories)