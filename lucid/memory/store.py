"""장기 기억의 SQLite 스키마, 조회 및 상태 전이를 관리한다."""

import sqlite3
from datetime import datetime
from threading import RLock

from lucid.log import Logger
from lucid.memory.facts import (
    MemoryRecord,
    infer_legacy_memory,
    normalize_memory_value,
)
from lucid.memory.facts import (
    memory_key as build_memory_key,
)
from lucid.memory.search import query_terms
from lucid.settings import data_directory


class LongTermMemory:
    """SQLite에서 사용자 사실, 대화, 내적 경험과 자율 목표를 관리한다."""

    MIN_CONVERSATION_MEMORY_YEARS = 5

    def __init__(self):
        """설정된 데이터 폴더에서 SQLite를 열고 필요한 테이블과 인덱스를 준비한다."""
        directory = data_directory()
        directory.mkdir(parents=True, exist_ok=True)
        self.db_path = directory / "lucid_memory.db"

        self.db = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
        )
        self.db.row_factory = sqlite3.Row
        self._lock = RLock()

        self.cursor = self.db.cursor()

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

        self._migrate()

    def _migrate(self):
        """이전 기억 행에 구조화된 필드를 채우고 같은 키의 현재 값을 한 건만 유지한다."""
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
                self.db.execute("BEGIN IMMEDIATE")
                self.cursor.execute("PRAGMA table_info(memories)")
                columns = {row[1] for row in self.cursor.fetchall()}

                for column, definition in additions.items():
                    if column not in columns:
                        self.cursor.execute(
                            f"ALTER TABLE memories ADD COLUMN {column} {definition}"
                        )

                indexes = {
                    row[1] for row in self.cursor.execute("PRAGMA index_list(memories)")
                }
                if {
                    "idx_memories_active_key",
                    "idx_memories_subject_predicate",
                } <= indexes:
                    incomplete = self.cursor.execute(
                        """SELECT 1 FROM memories WHERE subject IS NULL OR predicate IS NULL
                           OR value IS NULL OR confidence IS NULL OR source IS NULL
                           OR memory_key IS NULL OR status IS NULL OR created_at IS NULL
                           OR updated_at IS NULL LIMIT 1"""
                    ).fetchone()
                    if incomplete is None:
                        self.db.commit()
                        return

                self.cursor.execute("DROP INDEX IF EXISTS idx_memories_active_key")
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
                        memory_id,
                        category,
                        content,
                        importance,
                        created_at,
                        subject,
                        predicate,
                        value,
                        confidence,
                        source,
                        key,
                        status,
                        updated_at,
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
                            subject,
                            predicate,
                            value,
                            confidence,
                            source,
                            key,
                            status,
                            created_at,
                            updated_at,
                            memory_id,
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

    def store(self, record: MemoryRecord):
        """사실을 저장하거나 확인 시각을 갱신하고 stored, reaffirmed, superseded, error 중 하나를 반환한다."""
        now = datetime.now().isoformat()
        subject = record.subject or "user"
        predicate = record.predicate or record.category
        value = record.value or record.content
        key = build_memory_key(subject, predicate, value)

        try:
            with self._lock, self.db:
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
                if predicate in {"likes", "dislikes"}:
                    opposite = "likes" if predicate == "dislikes" else "dislikes"
                    self.cursor.execute(
                        """UPDATE memories SET status = 'superseded', updated_at = ?
                           WHERE status = 'active' AND memory_key = ?""",
                        (now, build_memory_key(subject, opposite, value)),
                    )

                if current is not None and normalize_memory_value(
                    current[2]
                ) == normalize_memory_value(value):
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

            outcome = "superseded" if superseded else "stored"
            Logger.info(f"[SQLite] Memory {outcome}: {record.content}")
            return outcome

        except Exception as error:
            Logger.notice(
                "장기 기억을 저장하지 못했습니다. 데이터 폴더의 권한과 여유 공간을 확인해 주세요."
            )
            Logger.error(f"[SQLite] Store Error : {error}")
            return "error"

    def search(self, keyword):
        """단일 검색어와 일치하는 활성 기억 본문을 최대 다섯 건 반환한다."""
        rows = self.search_records([keyword], limit=5)
        return [row["content"] for row in rows]

    def search_records(self, keywords, limit=5):
        """검색어별 일치 수와 중요도를 기준으로 순위를 매긴 기억 행을 limit개까지 반환한다."""
        keywords = list(
            dict.fromkeys(
                str(keyword).strip().casefold()
                for keyword in keywords
                if str(keyword).strip()
            )
        )

        keywords = keywords[:20]
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
                   ({" + ".join(score_parts)}) AS relevance
            FROM memories
            WHERE status = 'active' AND ({" OR ".join(where_parts)})
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
            return [dict(row) for row in rows]

        except Exception as error:
            Logger.error(f"[SQLite] Search Error : {error}")
            return []

    def all(self, include_history=False):
        """활성 기억을 사전 목록으로 반환한다. include_history가 참이면 삭제·교체 이력을 포함한다."""
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
            return [dict(row) for row in rows]

        except Exception as error:
            Logger.error(f"[SQLite] All Error : {error}")
            return []

    def count(self):
        """현재 활성 상태인 기억 개수를 반환한다."""
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
        """지정한 활성 기억을 삭제 상태로 바꾸고 실제 행이 변경되었는지 반환한다."""
        try:
            with self._lock, self.db:
                self.cursor.execute(
                    """
                    UPDATE memories
                    SET status = 'deleted', updated_at = ?
                    WHERE id = ? AND status = 'active'
                    """,
                    (datetime.now().isoformat(), int(memory_id)),
                )
                deleted = self.cursor.rowcount > 0
                return deleted
        except (TypeError, ValueError):
            return False
        except Exception as error:
            Logger.error(f"[SQLite] Delete Error : {error}")
            return False

    def _insert_experience(self, experience):
        """호출자가 연 트랜잭션에 내적 경험 한 건을 추가한다."""
        self.db.execute(
            """INSERT INTO inner_experiences(name, meaning, trigger_text, tendency, persistence, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                experience.name,
                experience.meaning,
                experience.trigger,
                experience.tendency,
                experience.persistence,
                experience.created_at.isoformat(),
            ),
        )

    def store_inner_experience(self, experience):
        """사용자의 사실과 별개로 한 번의 내적 경험을 기록한다."""
        try:
            with self._lock, self.db:
                self._insert_experience(experience)
        except sqlite3.Error as error:
            Logger.error(f"[Inner Life] Store Error : {error}")

    def recent_inner_experiences(self, limit=12):
        """최근 내적 경험을 limit개 골라 오래된 순서대로 반환한다."""
        try:
            with self._lock:
                self.cursor.execute(
                    """
                    SELECT
                        name, meaning, trigger_text AS "trigger", tendency,
                        persistence, created_at
                    FROM inner_experiences
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (limit,),
                )
                rows = self.cursor.fetchall()
            return [dict(row) for row in reversed(rows)]

        except Exception as e:
            Logger.error(f"[Inner Life] Load Error : {e}")

            return []

    def store_conversation_episode(
        self,
        user_text,
        assistant_text,
        intent="conversation",
        created_at=None,
    ):
        """사용자·응답 문장과 의도, 시각을 저장하고 행 번호를 반환한다. 실패하면 None이다."""
        timestamp = created_at or datetime.now().isoformat()

        try:
            with self._lock, self.db:
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

            Logger.info(f"[Conversation Memory] Stored episode #{episode_id}")
            return episode_id

        except Exception as error:
            Logger.notice(
                "이번 대화를 기록하지 못했습니다. 데이터 폴더의 권한과 여유 공간을 확인해 주세요."
            )
            Logger.error(f"[Conversation Memory] Store Error : {error}")
            return None

    def search_conversation_episodes(self, query, limit=3, years=5):
        """최소 5년의 조회 범위에서 질문과 관련된 과거 대화를 관련성순으로 반환한다."""
        terms = query_terms(query)
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
            # 윤년 2월 29일은 조회 기준 연도에 맞춰 2월 28일로 조정한다.
            cutoff = now.replace(year=cutoff_year, month=2, day=28).isoformat()
        searchable_text = (
            "lower(COALESCE(user_text, '') || ' ' || "
            "COALESCE(assistant_text, '') || ' ' || COALESCE(intent, ''))"
        )
        score = " + ".join(
            f"CASE WHEN {searchable_text} LIKE ? THEN 1 ELSE 0 END" for _ in terms
        )
        conditions = " OR ".join(f"{searchable_text} LIKE ?" for _ in terms)
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
            return [dict(row) for row in rows]

        except Exception as error:
            Logger.error(f"[Conversation Memory] Search Error : {error}")
            return []

    def recent_conversation_episodes(self, limit=10):
        """최근 대화 중 지정한 개수를 시간 순서대로 반환한다."""
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
            return [dict(row) for row in reversed(rows)]

        except (TypeError, ValueError):
            Logger.error("[Conversation Memory] Invalid recent episode limit")
            return []
        except Exception as error:
            Logger.error(f"[Conversation Memory] Load Error : {error}")
            return []

    @staticmethod
    def _elapsed_text(seconds):
        """경과 초를 대화에 사용할 한국어 시간 표현으로 변환한다."""
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
        """마지막 대화의 시각, 경과 시간과 출처를 반환하고 대화가 없으면 근사치를 구분한다."""
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
                guidance = (
                    "바로 이어지는 대화처럼 맥락을 잇고, 오랜만이라고 하지 않는다."
                )
            elif elapsed_seconds < 86400:
                guidance = (
                    "같은 날의 대화처럼 자연스럽게 이어가고, 긴 공백을 과장하지 않는다."
                )
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
            Logger.error(
                f"[Conversation Memory] Last conversation lookup failed : {error}"
            )
            return {
                "last_at": "확인할 수 없음",
                "elapsed_seconds": None,
                "elapsed_text": "기록 시각을 계산하지 못함",
                "source": "unavailable",
                "is_approximate": True,
                "reaction_guidance": "시간 간격을 추측하지 말고 현재 대화에 집중한다.",
            }

    def search_inner_experiences(self, query, limit=3):
        """질문과 관련 있는 내적 경험을 최대 limit개까지 관련성순으로 반환한다."""
        keywords = query_terms(query)

        if not keywords:
            return []

        searchable_text = (
            "lower(COALESCE(name, '') || ' ' || "
            "COALESCE(meaning, '') || ' ' || COALESCE(trigger_text, '') || ' ' || "
            "COALESCE(tendency, '') || ' ' || COALESCE(persistence, ''))"
        )
        score = " + ".join(
            f"CASE WHEN {searchable_text} LIKE ? THEN 1 ELSE 0 END" for _ in keywords
        )
        conditions = " OR ".join(f"{searchable_text} LIKE ?" for _ in keywords)
        parameters = [f"%{keyword}%" for keyword in keywords]

        try:
            with self._lock:
                self.cursor.execute(
                    f"""
                    SELECT id, name, meaning, trigger_text AS "trigger", tendency,
                           persistence, created_at, ({score}) AS relevance
                    FROM inner_experiences
                    WHERE {conditions}
                    ORDER BY relevance DESC, id DESC
                    LIMIT ?
                    """,
                    (*parameters, *parameters, max(1, min(int(limit), 8))),
                )
                rows = self.cursor.fetchall()
            return [dict(row) for row in rows]

        except (TypeError, ValueError):
            Logger.error("[Inner Life] Invalid experience search limit")
            return []
        except Exception as error:
            Logger.error(f"[Inner Life] Search Error : {error}")
            return []

    def _replace_goal(self, goal):
        """호출자가 연 트랜잭션에서 이전 목표를 비활성화하고 새 목표를 추가한다."""
        self.db.execute("UPDATE autonomous_goals SET active = 0 WHERE active = 1")
        self.db.execute(
            """INSERT INTO autonomous_goals(interest, title, rationale, next_attention, active, created_at)
               VALUES (?, ?, ?, ?, 1, ?)""",
            (
                goal.interest,
                goal.title,
                goal.rationale,
                goal.next_attention,
                goal.created_at.isoformat(),
            ),
        )

    def set_autonomous_goal(self, goal):
        """새 목표를 활성화하고 이전 목표를 이력으로 남긴다."""
        try:
            with self._lock, self.db:
                self._replace_goal(goal)
        except sqlite3.Error as error:
            Logger.error(f"[Autonomy] Goal Store Error : {error}")

    def store_reflection(self, experience, goal):
        """한 번의 자율 성찰로 생긴 경험과 목표를 함께 저장하며 실패 시 모두 되돌린다."""
        with self._lock, self.db:
            self._insert_experience(experience)
            self._replace_goal(goal)

    def active_autonomous_goal(self):
        """현재 활성 자율 목표 한 건을 사전으로 반환하고 없으면 None을 반환한다."""
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

            return dict(row) if row is not None else None

        except Exception as e:
            Logger.error(f"[Autonomy] Goal Load Error : {e}")

            return None

    def close(self):
        """호출 중인 저장 작업과 겹치지 않도록 잠금 안에서 SQLite 연결을 닫는다."""
        try:
            with self._lock:
                self.db.close()

            Logger.info("[SQLite] Database Closed")

        except Exception as e:
            Logger.error(f"[SQLite] Close Error : {e}")
