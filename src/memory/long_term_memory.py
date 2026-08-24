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

        # ==========================================
        # Create Table
        # ==========================================

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

        # ==========================================
        # Database Migration
        # ==========================================

        self._migrate()

    # ==========================================
    # Migration
    # ==========================================

    def _migrate(self):

        self.cursor.execute(
            "PRAGMA table_info(memories)"
        )

        columns = [
            row[1]
            for row in self.cursor.fetchall()
        ]

        # ------------------------------------------
        # created_at
        # ------------------------------------------

        if "created_at" not in columns:

            Logger.info(
                "[SQLite] Adding missing column : created_at"
            )

            self.cursor.execute(
                """
                ALTER TABLE memories
                ADD COLUMN created_at TEXT
                """
            )

        # ------------------------------------------
        # Commit
        # ------------------------------------------

        self.db.commit()

        Logger.info(
            "[SQLite] Database schema checked"
        )

    # ==========================================
    # Store
    # ==========================================

    def store(self, record: MemoryRecord):

        try:

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

        except Exception as e:

            Logger.error(
                f"[SQLite] Store Error : {e}"
            )

    # ==========================================
    # Search
    # ==========================================

    def search(self, keyword):

        try:

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

            return [
                row[0]
                for row in rows
            ]

        except Exception as e:

            Logger.error(
                f"[SQLite] Search Error : {e}"
            )

            return []

    # ==========================================
    # All Memories
    # ==========================================

    def all(self):

        try:

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

        except Exception as e:

            Logger.error(
                f"[SQLite] All Error : {e}"
            )

            return []

    # ==========================================
    # Count
    # ==========================================

    def count(self):

        try:

            self.cursor.execute(
                "SELECT COUNT(*) FROM memories"
            )

            return self.cursor.fetchone()[0]

        except Exception as e:

            Logger.error(
                f"[SQLite] Count Error : {e}"
            )

            return 0

    # ==========================================
    # Close
    # ==========================================

    def close(self):

        try:

            self.db.close()

            Logger.info(
                "[SQLite] Database Closed"
            )

        except Exception as e:

            Logger.error(
                f"[SQLite] Close Error : {e}"
            )