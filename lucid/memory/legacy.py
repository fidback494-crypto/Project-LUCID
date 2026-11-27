"""초기 LUCID에서 사용한 lucid.db 형식의 저장 API."""

import os
import sqlite3
from pathlib import Path

DB_PATH = Path("data")
DATABASE = DB_PATH / "lucid.db"


def get_connection():
    """환경 변수 또는 기존 상대 경로에 있는 lucid.db를 열고 연결을 반환한다."""
    directory = os.getenv("LUCID_DATA_DIR")
    path = Path(directory) / DATABASE.name if directory else DATABASE
    path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(path)


class MemoryEngine:
    """초기 스키마를 사용하는 코드의 사실·목표 조회와 기록을 지원한다."""

    def __init__(self):
        """로컬 저장소 연결을 열고 구형 기억 테이블을 준비한다."""
        self.conn = get_connection()
        self.create_table()

    def create_table(self):
        """기존 행을 유지하면서 필요한 기억 테이블을 만든다."""
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS memories(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    memory_type TEXT, content TEXT, importance REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def add_memory(self, memory_type, content, importance=0.5):
        """종류·내용·중요도를 받아 새 기억 한 건을 저장한다."""
        with self.conn:
            self.conn.execute(
                "INSERT INTO memories(memory_type, content, importance) VALUES (?, ?, ?)",
                (memory_type, content, importance),
            )

    def exists(self, content):
        """본문이 정확히 일치하는 기억이 있는지 반환한다."""
        return (
            self.conn.execute(
                "SELECT 1 FROM memories WHERE content = ? LIMIT 1", (content,)
            ).fetchone()
            is not None
        )

    def get_memories(self):
        """원본 스키마의 모든 행을 최신순으로 반환한다."""
        return self.conn.execute(
            "SELECT * FROM memories ORDER BY created_at DESC, id DESC"
        ).fetchall()

    def get_recent_memories(self, limit=10):
        """최근 기억을 최대 limit개까지 본문 목록으로 반환한다."""
        rows = self.conn.execute(
            "SELECT content FROM memories ORDER BY created_at DESC, id DESC LIMIT ?",
            (limit,),
        )
        return [row[0] for row in rows]

    def _latest(self, kind):
        """해당 종류의 최신 기억 본문을 반환하고 없으면 None을 반환한다."""
        row = self.conn.execute(
            "SELECT content FROM memories WHERE memory_type = ? ORDER BY created_at DESC, id DESC LIMIT 1",
            (kind,),
        ).fetchone()
        return row[0] if row else None

    def get_name(self):
        """가장 최근 이름을 반환한다. 저장된 이름이 없으면 None이다."""
        return self._latest("name")

    def get_favorite_animal(self):
        """가장 최근에 저장한 선호 동물 이름 또는 None을 반환한다."""
        return self._latest("favorite_animal")

    def get_project(self):
        """가장 최근 프로젝트 본문 또는 None을 반환한다."""
        return self._latest("project")

    def set_goal(self, goal):
        """기존 목표를 입력받은 목표로 한 트랜잭션에서 교체한다."""
        with self.conn:
            self.conn.execute("DELETE FROM memories WHERE memory_type = 'goal'")
            self.conn.execute(
                "INSERT INTO memories(memory_type, content, importance) VALUES ('goal', ?, 1.0)",
                (goal,),
            )

    def get_goal(self):
        """현재 목표 본문을 반환하고 없으면 None을 반환한다."""
        return self._latest("goal")

    def has_goal(self):
        """현재 목표가 저장되어 있는지 반환한다."""
        return self.get_goal() is not None

    def clear_goal(self):
        """목표에 속하는 행만 삭제한다."""
        with self.conn:
            self.conn.execute("DELETE FROM memories WHERE memory_type = 'goal'")
