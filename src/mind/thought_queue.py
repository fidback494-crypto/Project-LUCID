"""
Project LUCID

Artificial Mind Project

Module : Thought Queue

Creator : 시드
"""

from collections import deque


class ThoughtQueue:
    """LUCID의 현재 생각들을 저장하는 큐"""

    def __init__(self):
        self.queue = deque()

    def push(self, thought):
        self.queue.append(thought)

    def pop(self):
        if self.queue:
            return self.queue.popleft()
        return None

    def is_empty(self):
        return len(self.queue) == 0

    def size(self):
        return len(self.queue)