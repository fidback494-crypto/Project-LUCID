"""
Project LUCID

Artificial Mind Project

Module : Long Term Memory

Creator : 시드
"""

import os
import re
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

    MIN_CONVERSATION_MEMORY_YEARS = 5

    _MEMORY_STOPWORDS = {
        "나는", "난", "나", "내", "제", "저는", "전", "너", "네",
        "그", "저", "이", "뭐", "뭐야", "무엇", "어떻게", "어떤",
        "좀", "지금", "정말", "말해", "들려줘", "해줘", "했어",
        "있어", "없어", "인가", "그리고", "그런", "저런",
    }
    _MEMORY_PARTICLES = (
        "으로", "에서", "에게", "한테", "까지", "부터", "처럼",
        "보다", "은", "는", "이", "가", "을", "를", "의", "에",
        "와", "과", "도", "만", "야", "요", "죠", "까",
    )

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

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation_episodes(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_text TEXT NOT NULL,
                assistant_text TEXT NOT NULL,
                intent TEXT NOT NULL DEFAULT 'conversation',
                created_at TEXT NOT NULL
            )
            """
        )

        self.cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_conversation_episodes_created_at
            ON conversation_episodes(created_at)
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

    @classmethod
    def _query_terms(cls, query):
        tokens = re.findall(r"[0-9a-z가-힣]+", str(query).casefold())
        terms = []

        for token in tokens:
            term = token

            for particle in cls._MEMORY_PARTICLES:
                if len(term) > len(particle) + 1 and term.endswith(particle):
                    term = term[:-len(particle)]
                    break

            if len(term) > 1 and term not in cls._MEMORY_STOPWORDS:
                terms.append(term)

        return list(dict.fromkeys(terms))[:20]

    def store_conversation_episode(
        self,
        user_text,
        assistant_text,
        intent="conversation",
        created_at=None,
    ):
        """Persist one exchange so LUCID can recall it in later sessions."""

        timestamp = created_at or datetime.now().isoformat()

        try:
            with self._lock:
                self.cursor.execute(
                    """
                    INSERT INTO conversation_episodes
                    (user_text, assistant_text, intent, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        str(user_text),
                        str(assistant_text),
                        str(intent or "conversation"),
                        timestamp,
                    ),
                )
                episode_id = self.cursor.lastrowid
                self.db.commit()

            Logger.info(f"[Conversation Memory] Stored episode #{episode_id}")
            return episode_id

        except Exception as error:
            with self._lock:
                self.db.rollback()
            Logger.error(f"[Conversation Memory] Store Error : {error}")
            return None

    def search_conversation_episodes(self, query, limit=3, years=5):
        """Search a minimum five-year window without deleting older records."""

        terms = self._query_terms(query)
        if not terms:
            return []

        try:
            years = max(
                self.MIN_CONVERSATION_MEMORY_YEARS,
                min(int(years), datetime.now().year - 1),
            )
            limit = max(1, min(int(limit), 8))
        except (TypeError, ValueError):
            Logger.error("[Conversation Memory] Invalid search window or limit")
            return []

        now = datetime.now()
        cutoff_year = now.year - years
        try:
            cutoff = now.replace(year=cutoff_year).isoformat()
        except ValueError:
            # Preserve the same month/day when the target year is not a leap year.
            cutoff = now.replace(year=cutoff_year, month=2, day=28).isoformat()
        searchable_text = (
            "lower(COALESCE(user_text, '') || ' ' || "
            "COALESCE(assistant_text, '') || ' ' || COALESCE(intent, ''))"
        )
        score = " + ".join(
            f"CASE WHEN {searchable_text} LIKE ? THEN 1 ELSE 0 END"
            for _ in terms
        )
        conditions = " OR ".join(
            f"{searchable_text} LIKE ?"
            for _ in terms
        )
        patterns = [f"%{term}%" for term in terms]

        try:
            with self._lock:
                self.cursor.execute(
                    f"""
                    SELECT id, user_text, assistant_text, intent, created_at,
                           ({score}) AS relevance
                    FROM conversation_episodes
                    WHERE created_at >= ? AND ({conditions})
                    ORDER BY relevance DESC, id DESC
                    LIMIT ?
                    """,
                    (*patterns, cutoff, *patterns, limit),
                )
                rows = self.cursor.fetchall()

            return [
                {
                    "id": row[0],
                    "user_text": row[1],
                    "assistant_text": row[2],
                    "intent": row[3],
                    "created_at": row[4],
                    "relevance": row[5],
                }
                for row in rows
            ]

        except Exception as error:
            Logger.error(f"[Conversation Memory] Search Error : {error}")
            return []

    def recent_conversation_episodes(self, limit=10):
        try:
            limit = max(1, min(int(limit), 50))

            with self._lock:
                self.cursor.execute(
                    """
                    SELECT id, user_text, assistant_text, intent, created_at
                    FROM conversation_episodes
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (limit,),
                )
                rows = self.cursor.fetchall()

            return [
                {
                    "id": row[0],
                    "user_text": row[1],
                    "assistant_text": row[2],
                    "intent": row[3],
                    "created_at": row[4],
                }
                for row in reversed(rows)
            ]

        except (TypeError, ValueError):
            Logger.error("[Conversation Memory] Invalid recent episode limit")
            return []
        except Exception as error:
            Logger.error(f"[Conversation Memory] Load Error : {error}")
            return []

    @staticmethod
    def _elapsed_text(seconds):
        minutes = int(seconds // 60)
        hours = int(seconds // 3600)
        days = int(seconds // 86400)

        if seconds < 120:
            return "방금"
        if minutes < 60:
            return f"약 {minutes}분 전"
        if hours < 24:
            return f"약 {hours}시간 전"
        if days < 2:
            return "하루쯤 전"
        if days < 7:
            return f"약 {days}일 전"
        if days < 60:
            return f"약 {max(1, round(days / 7))}주 전"
        if days < 365:
            return f"약 {max(2, round(days / 30))}개월 전"

        years = days // 365
        months = round((days % 365) / 30)
        if months >= 12:
            years += 1
            months = 0
        if months:
            return f"약 {years}년 {months}개월 전"
        return f"약 {years}년 전"

    def last_conversation_gap(self):
        """Describe time since the latest saved exchange, with a safe fallback."""

        try:
            with self._lock:
                self.cursor.execute(
                    """
                    SELECT created_at
                    FROM conversation_episodes
                    ORDER BY id DESC
                    LIMIT 1
                    """
                )
                row = self.cursor.fetchone()
                source = "conversation"

                if row is None:
                    self.cursor.execute(
                        """
                        SELECT created_at
                        FROM inner_experiences
                        ORDER BY id DESC
                        LIMIT 1
                        """
                    )
                    row = self.cursor.fetchone()
                    source = "inner_experience_estimate"

            if row is None or not row[0]:
                return {
                    "last_at": "기록 없음",
                    "elapsed_seconds": None,
                    "elapsed_text": "확인된 이전 기록이 없음",
                    "source": "none",
                    "reaction_guidance": "처음 만난 것처럼 자연스럽게 인사한다.",
                }

            recorded_at = datetime.fromisoformat(str(row[0]))
            now = datetime.now()
            if recorded_at.tzinfo is not None and now.tzinfo is None:
                recorded_at = recorded_at.astimezone().replace(tzinfo=None)
            elif recorded_at.tzinfo is None and now.tzinfo is not None:
                recorded_at = recorded_at.replace(tzinfo=now.tzinfo)

            elapsed_seconds = max(0.0, (now - recorded_at).total_seconds())
            if elapsed_seconds < 3600:
                guidance = "바로 이어지는 대화처럼 맥락을 잇고, 오랜만이라고 하지 않는다."
            elif elapsed_seconds < 86400:
                guidance = "같은 날의 대화처럼 자연스럽게 이어가고, 긴 공백을 과장하지 않는다."
            elif elapsed_seconds < 7 * 86400:
                guidance = "며칠 만의 대화라면 반가움을 가볍게 드러낸다."
            elif elapsed_seconds < 30 * 86400:
                guidance = "몇 주 만의 대화라면 오랜만이라는 반가움을 자연스럽게 표현하되, 과장하지 않는다."
            elif elapsed_seconds < 180 * 86400:
                guidance = "한두 달의 공백 뒤라면 오랜만에 만난 듯 따뜻하게 맞이하고, 최근 이야기를 궁금해한다."
            elif elapsed_seconds < 365 * 86400:
                guidance = "몇 달의 공백 뒤라면 반가움을 조금 더 분명히 드러내되, 기억하지 못하는 일을 아는 척하지 않는다."
            else:
                guidance = "1년 이상 만의 재회라면 의미 있게 반가워하고 지금의 이야기를 궁금해하되, 기다렸다고 압박하거나 죄책감을 주지 않는다."

            approximate = source != "conversation"
            if approximate:
                guidance += " 이 날짜는 대화 기록이 없어 내적 경험 시각으로 추정한 값이므로 정확한 마지막 대화일처럼 말하지 않는다."

            return {
                "last_at": recorded_at.isoformat(timespec="minutes"),
                "elapsed_seconds": elapsed_seconds,
                "elapsed_text": self._elapsed_text(elapsed_seconds),
                "source": source,
                "is_approximate": approximate,
                "reaction_guidance": guidance,
            }

        except Exception as error:
            Logger.error(f"[Conversation Memory] Last conversation lookup failed : {error}")
            return {
                "last_at": "확인할 수 없음",
                "elapsed_seconds": None,
                "elapsed_text": "기록 시각을 계산하지 못함",
                "source": "unavailable",
                "is_approximate": True,
                "reaction_guidance": "시간 간격을 추측하지 말고 현재 대화에 집중한다.",
            }

    def search_inner_experiences(self, query, limit=3):
        """Return recent, keyword-relevant experiences without an LLM call."""
        keywords = self._query_terms(query)

        if not keywords:
            return []

        searchable_text = "lower(COALESCE(name, '') || ' ' || " \
            "COALESCE(meaning, '') || ' ' || COALESCE(trigger_text, '') || ' ' || " \
            "COALESCE(tendency, '') || ' ' || COALESCE(persistence, ''))"
        score = " + ".join(
            f"CASE WHEN {searchable_text} LIKE ? THEN 1 ELSE 0 END"
            for _ in keywords
        )
        conditions = " OR ".join(
            f"{searchable_text} LIKE ?"
            for _ in keywords
        )
        parameters = [f"%{keyword}%" for keyword in keywords]

        try:
            with self._lock:
                self.cursor.execute(
                    f"""
                    SELECT id, name, meaning, trigger_text, tendency,
                           persistence, created_at, ({score}) AS relevance
                    FROM inner_experiences
                    WHERE {conditions}
                    ORDER BY relevance DESC, id DESC
                    LIMIT ?
                    """,
                    (*parameters, *parameters, max(1, min(int(limit), 8))),
                )
                rows = self.cursor.fetchall()

            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "meaning": row[2],
                    "trigger": row[3],
                    "tendency": row[4],
                    "persistence": row[5],
                    "created_at": row[6],
                    "relevance": row[7],
                }
                for row in rows
            ]

        except (TypeError, ValueError):
            Logger.error("[Inner Life] Invalid experience search limit")
            return []
        except Exception as error:
            Logger.error(f"[Inner Life] Search Error : {error}")
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
