"""Rank active long-term memories against a Korean user query."""

import re

from src.utils import Logger


class MemorySearch:
    STOPWORDS = {
        "나는", "난", "내", "제", "저는", "전", "너", "네", "그", "저",
        "뭐", "뭐야", "무엇", "어떻게", "알려", "말해", "좀", "해줘",
        "해", "했어", "인가", "있어", "없어", "기억해", "기억나",
    }
    PARTICLES = (
        "으로", "에서", "에게", "한테", "까지", "부터", "처럼", "보다",
        "은", "는", "이", "가", "을", "를", "의", "에", "와", "과",
        "도", "만", "야", "요", "죠", "까",
    )

    def __init__(self, long_memory):
        self.memory = long_memory

    def search(self, observation):
        text = (
            observation.content
            if hasattr(observation, "content")
            else str(observation)
        )
        keywords = self._keywords(text)
        results = self.memory.search_records(keywords, limit=5)

        Logger.info(f"[MemorySearch] {len(results)} Memories Found")
        return [record["content"] for record in results]

    @classmethod
    def _keywords(cls, text):
        tokens = re.findall(r"[0-9a-z가-힣]+", text.casefold())
        keywords = []

        for token in tokens:
            normalized = token

            for particle in cls.PARTICLES:
                if len(normalized) > len(particle) + 1 and normalized.endswith(particle):
                    normalized = normalized[:-len(particle)]
                    break

            if normalized and normalized not in cls.STOPWORDS and len(normalized) > 1:
                keywords.append(normalized)

            if normalized.startswith("좋아"):
                keywords.extend(("likes", "좋아한다"))
            elif normalized.startswith("싫어"):
                keywords.extend(("dislikes", "싫어한다"))
            elif normalized.startswith("이름"):
                keywords.append("name")

        return list(dict.fromkeys(keywords))[:20]
