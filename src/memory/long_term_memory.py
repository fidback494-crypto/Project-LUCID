"""
Project LUCID

Artificial Mind Project

Module : Long Term Memory

Creator : 시드
"""

import sqlite3
from datetime import datetime

from src.utils import Logger
from .memory_record import MemoryRecord


class LongTermMemory:

    def __init__(self):

        self.db = sqlite3.connect(
            "lucid_memory.db",
            check_same_thread=False,
        )

        self.cursor = self.db.cursor()

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS memories(

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                category TEXT,

                content TEXT UNIQUE,

                importance REAL,

                created_at TEXT
            )
            """
        )

        self.db.commit()

    # ----------------------------------
    # Store
    # ----------------------------------

    def store(self, record: MemoryRecord):

        self.cursor.execute(

            """
            INSERT OR IGNORE INTO memories
            (
                category,
                content,
                importance,
                created_at
            )

            VALUES(?,?,?,?)
            """,

            (
                record.category,
                record.content,
                record.importance,
                datetime.now().isoformat(),
            ),
        )

        self.db.commit()

        Logger.info(
            f"[SQLite] Stored : {record.content}"
        )

    # ----------------------------------
    # Search
    # ----------------------------------

    def search(self, keyword):

        self.cursor.execute(

            """
            SELECT content

            FROM memories

            WHERE content LIKE ?

            ORDER BY importance DESC

            LIMIT 5
            """,

            (f"%{keyword}%",),
        )

        rows = self.cursor.fetchall()

        return [row[0] for row in rows]

    # ----------------------------------
    # All Memories
    # ----------------------------------

    def all(self):

        self.cursor.execute(

            """
            SELECT
                category,
                content,
                importance,
                created_at

            FROM memories

            ORDER BY importance DESC
            """
        )

        return self.cursor.fetchall()

    # ----------------------------------
    # Count
    # ----------------------------------

    def count(self):

        self.cursor.execute(
            "SELECT COUNT(*) FROM memories"
        )

        return self.cursor.fetchone()[0]