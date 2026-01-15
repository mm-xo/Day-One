import sqlite3
from db_helpers import BASE_DIR, get_db_connection


def init():
    conn = get_db_connection()
    # cur = conn.cursor()
    with open(BASE_DIR / "src/schema.sql") as f:
        conn.executescript(f.read())
    
    print("Database initialized successfully!")
    conn.commit()
    conn.close()

