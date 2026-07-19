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