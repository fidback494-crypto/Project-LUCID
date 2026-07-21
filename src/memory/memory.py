from .database import get_connection


class MemoryEngine:
    def __init__(self):
        self.conn = get_connection()
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS memories(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            memory_type TEXT,
            content TEXT,
            importance REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        self.conn.commit()

    def add_memory(self, memory_type, content, importance=0.5):
        cursor = self.conn.cursor()

        cursor.execute(
            """
            INSERT INTO memories(memory_type, content, importance)
            VALUES (?, ?, ?)
            """,
            (memory_type, content, importance),
        )

        self.conn.commit()

    def exists(self, content):
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM memories
            WHERE content = ?
            """,
            (content,),
        )

        return cursor.fetchone()[0] > 0

    def get_memories(self):
        cursor = self.conn.cursor()

        cursor.execute("""
        SELECT *
        FROM memories
        ORDER BY created_at DESC
        """)

        return cursor.fetchall()

    def get_recent_memories(self, limit=10):
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT content
            FROM memories
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )

        return [row[0] for row in cursor.fetchall()]

    def get_name(self):
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT content
            FROM memories
            WHERE memory_type='name'
            ORDER BY created_at DESC
            LIMIT 1
            """
        )

        row = cursor.fetchone()
        return row[0] if row else None

    def get_favorite_animal(self):
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT content
            FROM memories
            WHERE memory_type='favorite_animal'
            ORDER BY created_at DESC
            LIMIT 1
            """
        )

        row = cursor.fetchone()
        return row[0] if row else None

    def get_project(self):
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT content
            FROM memories
            WHERE memory_type='project'
            ORDER BY created_at DESC
            LIMIT 1
            """
        )

        row = cursor.fetchone()
        return row[0] if row else None

    # -----------------------------
    # Goal API
    # -----------------------------

    def set_goal(self, goal):
        cursor = self.conn.cursor()

        cursor.execute(
            """
            DELETE FROM memories
            WHERE memory_type='goal'
            """
        )

        cursor.execute(
            """
            INSERT INTO memories(memory_type, content, importance)
            VALUES (?, ?, ?)
            """,
            (
                "goal",
                goal,
                1.0,
            ),
        )

        self.conn.commit()

    def get_goal(self):
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT content
            FROM memories
            WHERE memory_type='goal'
            ORDER BY created_at DESC
            LIMIT 1
            """
        )

        row = cursor.fetchone()
        return row[0] if row else None

    def has_goal(self):
        return self.get_goal() is not None

    def clear_goal(self):
        cursor = self.conn.cursor()

        cursor.execute(
            """
            DELETE FROM memories
            WHERE memory_type='goal'
            """
        )

        self.conn.commit()