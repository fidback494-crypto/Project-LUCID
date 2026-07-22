"""
Project LUCID

Artificial Mind Project

Module : Memory Extractor

Creator : 시드
"""

from src.utils import Logger
from .memory_record import MemoryRecord


class MemoryExtractor:

    def extract(self, observation):

        text = observation.content.strip()

        Logger.info(f"[Extractor] Input : {text}")

        # -----------------------------
        # 이름 기억
        # -----------------------------

        if "내 이름은" in text:

            name = text.split("내 이름은", 1)[1].strip()

            record = MemoryRecord(
                category="user",
                content=f"사용자의 이름은 {name}",
                importance=0.95,
            )

            Logger.info(f"[Extractor] {record}")

            return record

        # -----------------------------
        # 좋아하는 것
        # -----------------------------

        if "좋아해" in text:

            fact = (
                text.replace("나는 ", "")
                    .replace("전 ", "")
                    .replace("저는 ", "")
                    .strip()
            )

            record = MemoryRecord(
                category="preference",
                content=f"사용자는 {fact}",
                importance=0.80,
            )

            Logger.info(f"[Extractor] {record}")

            return record

        Logger.info("[Extractor] Nothing Extracted")

        return None