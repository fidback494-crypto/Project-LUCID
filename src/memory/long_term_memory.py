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

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS inner_experiences(

                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                meaning TEXT NOT NULL,
                trigger_text TEXT NOT NULL,
                tendency TEXT NOT NULL,
                persistence TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS autonomous_goals(

                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interest TEXT NOT NULL,
                title TEXT NOT NULL,
                rationale TEXT NOT NULL,
                next_attention TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
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
    # Inner Life
    # ==========================================

    def store_inner_experience(self, experience):
        """Persist an autonomous inner experience separately from user memory."""

        try:

            self.cursor.execute(
                """
                INSERT INTO inner_experiences
                (
                    name,
                    meaning,
                    trigger_text,
                    tendency,
                    persistence,
                    created_at
                )
                VALUES(?,?,?,?,?,?)
                """,
                (
                    experience.name,
                    experience.meaning,
                    experience.trigger,
                    experience.tendency,
                    experience.persistence,
                    experience.created_at.isoformat(),
                ),
            )

            self.db.commit()

            Logger.info(
                f"[Inner Life] Stored : {experience.name}"
            )

        except Exception as e:

            Logger.error(
                f"[Inner Life] Store Error : {e}"
            )

    def recent_inner_experiences(self, limit=12):

        try:

            self.cursor.execute(
                """
                SELECT
                    name,
                    meaning,
                    trigger_text,
                    tendency,
                    persistence,
                    created_at
                FROM inner_experiences
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )

            rows = self.cursor.fetchall()

            return [
                {
                    "name": row[0],
                    "meaning": row[1],
                    "trigger": row[2],
                    "tendency": row[3],
                    "persistence": row[4],
                    "created_at": row[5],
                }
                for row in reversed(rows)
            ]

        except Exception as e:

            Logger.error(
                f"[Inner Life] Load Error : {e}"
            )

            return []

    # ==========================================
    # Autonomous Goals
    # ==========================================

    def set_autonomous_goal(self, goal):
        """Keep one current self-generated goal while preserving prior goals."""

        try:

            self.cursor.execute(
                "UPDATE autonomous_goals SET active = 0 WHERE active = 1"
            )

            self.cursor.execute(
                """
                INSERT INTO autonomous_goals
                (
                    interest,
                    title,
                    rationale,
                    next_attention,
                    active,
                    created_at
                )
                VALUES(?,?,?,?,?,?)
                """,
                (
                    goal.interest,
                    goal.title,
                    goal.rationale,
                    goal.next_attention,
                    1,
                    goal.created_at.isoformat(),
                ),
            )

            self.db.commit()

            Logger.info(
                f"[Autonomy] Goal Stored : {goal.title}"
            )

        except Exception as e:

            Logger.error(
                f"[Autonomy] Goal Store Error : {e}"
            )

    def active_autonomous_goal(self):

        try:

            self.cursor.execute(
                """
                SELECT interest, title, rationale, next_attention, created_at
                FROM autonomous_goals
                WHERE active = 1
                ORDER BY id DESC
                LIMIT 1
                """
            )

            row = self.cursor.fetchone()

            if row is None:

                return None

            return {
                "interest": row[0],
                "title": row[1],
                "rationale": row[2],
                "next_attention": row[3],
                "created_at": row[4],
            }

        except Exception as e:

            Logger.error(
                f"[Autonomy] Goal Load Error : {e}"
            )

            return None

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
