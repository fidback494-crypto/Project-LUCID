"""
Project LUCID

Artificial Mind Project

Module : Memory Search

Creator : 시드
"""

from src.utils import Logger


class MemorySearch:

    def __init__(self, long_memory):

        self.memory = long_memory

    def search(self, observation):

        words = observation.content.split()

        results = []

        # -----------------------------
        # 모든 키워드 검색
        # -----------------------------

        for word in words:

            memories = self.memory.search(word)

            if memories:
                results.extend(memories)

        # -----------------------------
        # 중복 제거 (순서 유지)
        # -----------------------------

        unique = []

        for memory in results:

            if memory not in unique:
                unique.append(memory)

        # -----------------------------
        # 최대 5개 반환
        # -----------------------------

        unique = unique[:5]

        Logger.info(
            f"[MemorySearch] {len(unique)} Memories Found"
        )

        return unique