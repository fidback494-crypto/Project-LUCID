"""한 세션의 최근 관찰과 반성을 임시 보관한다."""

from collections import deque

from lucid.core.kernel import BaseModule
from lucid.log import Logger


class WorkingMemory(BaseModule):
    """세션 동안 최근 관찰과 반성 결과를 개수 제한이 있는 큐에 유지한다."""

    def __init__(self, capacity: int = 20):
        """최대 capacity개의 항목을 보관할 큐를 준비한다."""
        super().__init__("WorkingMemory")

        self.capacity = capacity
        self.memories = deque(maxlen=capacity)

    def process(self, item):
        """관찰이나 반성 항목을 최근 기억에 추가하고 같은 객체를 반환한다."""
        self.memories.append(item)

        Logger.info(f"[WorkingMemory] Stored ({type(item).__name__})")

        return item

    def add(self, item):
        """이전 호출자를 위해 process와 동일하게 항목을 추가하고 반환한다."""
        return self.process(item)

    def recent(self, limit=None):
        """최근 limit개를 오래된 순서대로 반환한다. 생략하면 전체를 반환한다."""
        memories = list(self.memories)

        if limit is None:
            return memories

        return memories[-limit:] if limit > 0 else []

    def latest(self):
        """가장 최근 항목을 반환하며 큐가 비었으면 None을 반환한다."""
        if not self.memories:
            return None

        return self.memories[-1]

    def clear(self):
        """이 세션의 작업 기억을 모두 비운다."""
        self.memories.clear()

    def size(self):
        """현재 보관 중인 항목 수를 반환한다."""
        return len(self.memories)
