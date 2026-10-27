"""
Project LUCID

Artificial Mind Project

Module : Memory Extractor

Creator : 시드
"""

import re

from src.utils import Logger
from .memory_record import MemoryRecord


class MemoryExtractor:

    def extract(self, observation):

        text = observation.content.strip()
        clean_text = text.strip().rstrip(".!?。！？").strip()

        Logger.info(f"[Extractor] Input : {text}")

        name_match = re.fullmatch(
            r"(?:내|제)\s*이름\s*(?:은|이)\s*(.+?)"
            r"(?:\s*(?:이야|야|이에요|예요|입니다))?",
            clean_text,
        )

        if name_match:
            name = name_match.group(1).strip()

            if name:
                record = MemoryRecord(
                    category="user",
                    content=f"사용자의 이름은 {name}",
                    importance=0.98,
                    subject="user",
                    predicate="name",
                    value=name,
                    confidence=0.99,
                    source="user_explicit",
                )

                Logger.info(f"[Extractor] {record}")
                return record

        # Explicit positive or negative preferences only.
        preference_match = re.fullmatch(
            r"(?:(?:나는|난|저는|전)\s*)?(.+?)\s*(?:을|를)\s*"
            r"(좋아해|좋아해요|좋아합니다|싫어해|싫어해요|싫어합니다)",
            clean_text,
        )

        if preference_match:
            value = preference_match.group(1).strip()
            sentiment = preference_match.group(2)

            if value:
                predicate = "dislikes" if sentiment.startswith("싫어") else "likes"
                verb = "싫어한다" if predicate == "dislikes" else "좋아한다"
                content = f"사용자는 {value}를 {verb}"

                record = MemoryRecord(
                    category="preference",
                    content=content,
                    importance=0.82,
                    subject="user",
                    predicate=predicate,
                    value=value,
                    confidence=0.9,
                    source="user_explicit",
                )

                Logger.info(f"[Extractor] {record}")
                return record

        Logger.info("[Extractor] Nothing Extracted")
        return None
