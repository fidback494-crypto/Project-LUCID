import sqlite3
from pathlib import Path

DB_PATH = Path("data")
DB_PATH.mkdir(exist_ok=True)

DATABASE = DB_PATH / "lucid.db"


def get_connection():
    return sqlite3.connect(DATABASE)