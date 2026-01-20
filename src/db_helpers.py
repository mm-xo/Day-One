import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent # project root directory
DB_PATH = BASE_DIR / "data" / "day_one.db"

def get_db_connection():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def execute(sql, params=()):
    conn = get_db_connection()
    cursor = conn.execute(sql, params)
    conn.commit()
    conn.close()
    return cursor

def fetchone(sql, params=()):
    conn = get_db_connection()
    cursor = conn.execute(sql, params)
    row = cursor.fetchone()
    conn.close()
    return row

def fetchall(sql, params=()):
    conn = get_db_connection()
    cursor = conn.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    return rows