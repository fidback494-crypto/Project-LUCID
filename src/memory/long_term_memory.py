"""
Project LUCID

Artificial Mind Project

Module : Long Term Memory

Creator : 시드
"""

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from threading import RLock

from src.utils import Logger
from .memory_record import (
    MemoryRecord,
    infer_legacy_memory,
    memory_key as build_memory_key,
    normalize_memory_value,
)


class LongTermMemory:

    def __init__(self):

        project_root = Path(__file__).resolve().parents[2]
        data_directory = Path(
            os.getenv(
                "LUCID_DATA_DIR",
                project_root / "data",
            )
        )
        data_directory.mkdir(parents=True, exist_ok=True)

        self.db_path = data_directory / "lucid_memory.db"

        self.db = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
        )
        self._lock = RLock()

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

                created_at TEXT,
                subject TEXT,
                predicate TEXT,
                value TEXT,
                confidence REAL,
                source TEXT,
                memory_key TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                updated_at TEXT
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
        additions = {
            "created_at": "TEXT",
            "subject": "TEXT",
            "predicate": "TEXT",
            "value": "TEXT",
            "confidence": "REAL",
            "source": "TEXT",
            "memory_key": "TEXT",
            "status": "TEXT NOT NULL DEFAULT 'active'",
            "updated_at": "TEXT",
        }

        with self._lock:
            try:
                self.cursor.execute("PRAGMA table_info(memories)")
                columns = {row[1] for row in self.cursor.fetchall()}

                for column, definition in additions.items():
                    if column not in columns:
                        self.cursor.execute(
                            f"ALTER TABLE memories ADD COLUMN {column} {definition}"
                        )

                now = datetime.now().isoformat()
                self.cursor.execute(
                    """
                    SELECT id, category, content, importance, created_at,
                           subject, predicate, value, confidence, source,
                           memory_key, status, updated_at
                    FROM memories
                    ORDER BY id
                    """
                )
                rows = self.cursor.fetchall()
                active_keys = {}

                for row in rows:
                    (
                        memory_id, category, content, importance, created_at,
                        subject, predicate, value, confidence, source,
                        key, status, updated_at,
                    ) = row

                    if not subject or not predicate or value is None:
                        subject, predicate, value = infer_legacy_memory(
                            category,
                            content,
                        )

                    value = str(value or content or "").strip()
                    confidence = min(
                        1.0,
                        max(
                            0.0,
                            float(confidence)
                            if confidence is not None
                            else float(importance or 0.75),
                        ),
                    )
                    key = key or build_memory_key(subject, predicate, value)
                    source = source or "legacy"
                    created_at = created_at or now
                    updated_at = updated_at or created_at
                    status = status or "active"

                    self.cursor.execute(
                        """
                        UPDATE memories
                        SET subject = ?, predicate = ?, value = ?,
                            confidence = ?, source = ?, memory_key = ?,
                            status = ?, created_at = ?, updated_at = ?
                        WHERE id = ?
                        """,
                        (
                            subject, predicate, value, confidence, source,
                            key, status, created_at, updated_at, memory_id,
                        ),
                    )

                    if status == "active":
                        previous_id = active_keys.get(key)
                        if previous_id is not None:
                            self.cursor.execute(
                                """
                                UPDATE memories
                                SET status = 'superseded', updated_at = ?
                                WHERE id = ?
                                """,
                                (now, previous_id),
                            )
                        active_keys[key] = memory_id

                self.cursor.execute(
                    """
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_memories_active_key
                    ON memories(memory_key)
                    WHERE status = 'active' AND memory_key IS NOT NULL
                    """
                )
                self.cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_memories_subject_predicate
                    ON memories(status, subject, predicate)
                    """
                )
                self.db.commit()

            except Exception:
                self.db.rollback()
                raise

        Logger.info("[SQLite] Memory schema migrated and checked")

    # ==========================================
    # Store
    # ==========================================

    def store(self, record: MemoryRecord):
        now = datetime.now().isoformat()
        subject = record.subject or "user"
        predicate = record.predicate or record.category
        value = record.value or record.content
        key = build_memory_key(subject, predicate, value)

        try:
            with self._lock:
                self.cursor.execute(
                    """
                    SELECT id, content, value
                    FROM memories
                    WHERE memory_key = ? AND status = 'active'
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (key,),
                )
                current = self.cursor.fetchone()

                if (
                    current is not None
                    and normalize_memory_value(current[2])
                    == normalize_memory_value(value)
                ):
                    self.cursor.execute(
                        """
                        UPDATE memories
                        SET importance = MAX(COALESCE(importance, 0), ?),
                            confidence = MAX(COALESCE(confidence, 0), ?),
                            source = ?, updated_at = ?
                        WHERE id = ?
                        """,
                        (
                            record.importance,
                            record.confidence,
                            record.source,
                            now,
                            current[0],
                        ),
                    )
                    self.db.commit()
                    Logger.info(f"[SQLite] Memory reaffirmed: {record.content}")
                    return "reaffirmed"

                superseded = False
                if current is not None:
                    self.cursor.execute(
                        """
                        UPDATE memories
                        SET status = 'superseded', updated_at = ?
                        WHERE memory_key = ? AND status = 'active'
                        """,
                        (now, key),
                    )
                    superseded = True

                self.cursor.execute(
                    "SELECT id FROM memories WHERE content = ? LIMIT 1",
                    (record.content,),
                )
                existing = self.cursor.fetchone()

                if existing is None:
                    self.cursor.execute(
                        """
                        INSERT INTO memories
                        (
                            category, content, importance, created_at,
                            subject, predicate, value, confidence, source,
                            memory_key, status, updated_at
                        )
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                        """,
                        (
                            record.category,
                            record.content,
                            record.importance,
                            record.timestamp or now,
                            subject,
                            predicate,
                            value,
                            record.confidence,
                            record.source,
                            key,
                            "active",
                            now,
                        ),
                    )
                else:
                    self.cursor.execute(
                        """
                        UPDATE memories
                        SET category = ?, importance = ?, subject = ?,
                            predicate = ?, value = ?, confidence = ?,
                            source = ?, memory_key = ?, status = 'active',
                            updated_at = ?
                        WHERE id = ?
                        """,
                        (
                            record.category,
                            record.importance,
                            subject,
                            predicate,
                            value,
                            record.confidence,
                            record.source,
                            key,
                            now,
                            existing[0],
                        ),
                    )

                self.db.commit()

            outcome = "superseded" if superseded else "stored"
            Logger.info(f"[SQLite] Memory {outcome}: {record.content}")
            return outcome

        except Exception as error:
            with self._lock:
                self.db.rollback()
            Logger.error(f"[SQLite] Store Error : {error}")
            return "error"

    # ==========================================
    # Search
    # ==========================================

    def search(self, keyword):
        rows = self.search_records([keyword], limit=5)
        return [row["content"] for row in rows]

    def search_records(self, keywords, limit=5):
        keywords = list(dict.fromkeys(
            str(keyword).strip().casefold()
            for keyword in keywords
            if str(keyword).strip()
        ))

        if not keywords:
            return []

        where_parts = []
        where_values = []
        score_parts = []
        score_values = []

        for keyword in keywords:
            pattern = f"%{keyword}%"
            condition = (
                "(lower(content) LIKE ? OR lower(value) LIKE ? "
                "OR lower(predicate) LIKE ?)"
            )
            where_parts.append(condition)
            where_values.extend((pattern, pattern, pattern))
            score_parts.append(f"CASE WHEN {condition} THEN 1 ELSE 0 END")
            score_values.extend((pattern, pattern, pattern))

        query = f"""
            SELECT id, category, content, importance, confidence, source,
                   created_at, updated_at, status, subject, predicate, value,
                   ({' + '.join(score_parts)}) AS relevance
            FROM memories
            WHERE status = 'active' AND ({' OR '.join(where_parts)})
            ORDER BY relevance DESC,
                     COALESCE(importance, 0) DESC,
                     COALESCE(confidence, 0) DESC,
                     updated_at DESC
            LIMIT ?
        """

        try:
            with self._lock:
                self.cursor.execute(
                    query,
                    (*score_values, *where_values, max(1, int(limit))),
                )
                rows = self.cursor.fetchall()

            keys = (
                "id", "category", "content", "importance", "confidence",
                "source", "created_at", "updated_at", "status", "subject",
                "predicate", "value", "relevance",
            )
            return [dict(zip(keys, row)) for row in rows]

        except Exception as error:
            Logger.error(f"[SQLite] Search Error : {error}")
            return []

    # ==========================================
    # All Memories
    # ==========================================

    def all(self, include_history=False):
        condition = "" if include_history else "WHERE status = 'active'"

        try:
            with self._lock:
                self.cursor.execute(
                    f"""
                    SELECT id, category, content, importance, confidence,
                           source, created_at, updated_at, status,
                           subject, predicate, value
                    FROM memories
                    {condition}
                    ORDER BY importance DESC, updated_at DESC
                    """
                )
                rows = self.cursor.fetchall()

            keys = (
                "id", "category", "content", "importance", "confidence",
                "source", "created_at", "updated_at", "status", "subject",
                "predicate", "value",
            )
            return [dict(zip(keys, row)) for row in rows]

        except Exception as error:
            Logger.error(f"[SQLite] All Error : {error}")
            return []

    # ==========================================
    # Count
    # ==========================================

    def count(self):
        try:
            with self._lock:
                self.cursor.execute(
                    "SELECT COUNT(*) FROM memories WHERE status = 'active'"
                )
                return self.cursor.fetchone()[0]
        except Exception as error:
            Logger.error(f"[SQLite] Count Error : {error}")
            return 0

    def delete(self, memory_id):
        """Soft-delete one active memory while retaining its audit history."""

        try:
            with self._lock:
                self.cursor.execute(
                    """
                    UPDATE memories
                    SET status = 'deleted', updated_at = ?
                    WHERE id = ? AND status = 'active'
                    """,
                    (datetime.now().isoformat(), int(memory_id)),
                )
                deleted = self.cursor.rowcount > 0
                self.db.commit()
                return deleted
        except (TypeError, ValueError):
            return False
        except Exception as error:
            with self._lock:
                self.db.rollback()
            Logger.error(f"[SQLite] Delete Error : {error}")
            return False

    # ==========================================
    # Inner Life
    # ==========================================

    def store_inner_experience(self, experience):
        """Persist an autonomous inner experience separately from user memory."""

        try:
            with self._lock:
                self.cursor.execute(
                    """
                    INSERT INTO inner_experiences
                    (
                        name, meaning, trigger_text, tendency,
                        persistence, created_at
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
            with self._lock:
                self.db.rollback()
            Logger.error(
                f"[Inner Life] Store Error : {e}"
            )

    def recent_inner_experiences(self, limit=12):

        try:
            with self._lock:
                self.cursor.execute(
                    """
                    SELECT
                        name, meaning, trigger_text, tendency,
                        persistence, created_at
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
            with self._lock:
                self.cursor.execute(
                    "UPDATE autonomous_goals SET active = 0 WHERE active = 1"
                )
                self.cursor.execute(
                    """
                    INSERT INTO autonomous_goals
                    (
                        interest, title, rationale, next_attention,
                        active, created_at
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
            with self._lock:
                self.db.rollback()
            Logger.error(
                f"[Autonomy] Goal Store Error : {e}"
            )

    def active_autonomous_goal(self):

        try:
            with self._lock:
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
            with self._lock:
                self.db.close()

            Logger.info(
                "[SQLite] Database Closed"
            )

        except Exception as e:

            Logger.error(
                f"[SQLite] Close Error : {e}"
            )
