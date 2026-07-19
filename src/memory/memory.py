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

    def get_memories(self):
        cursor = self.conn.cursor()

        cursor.execute("SELECT * FROM memories")

        return cursor.fetchall()