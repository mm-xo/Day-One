import sqlite3
from datetime import datetime, timezone

from database import init, execute, fetchone

def utc_now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def main():
    init()
    
    guild_id = "123"
    name = "Gym"
    created_by = "456"
    created_at = utc_now_iso()
    
    # TODO insert a group (works)
    # execute(
    #     "INSERT INTO habit_groups (guild_id, name, created_by, created_at) VALUES (?,?,?,?)",
    #     (guild_id, name, created_by, created_at),
    # )
    
    row = fetchone(
        "SELECT id, guild_id, name, created_by, created_at FROM habit_groups WHERE guild_id=? AND name=?",
        (guild_id, name),
    )
    
    print("Inserted row:", dict(row) if row else None)
    
    # TODO try duplicate insert (works)
    try:
        execute(
            "INSERT INTO habit_groups (guild_id, name, created_by, created_at) VALUES (?, ?, ?, ?)",
            (guild_id, name, "999", utc_now_iso()),
        )
        print("ADDED (Should not have happened)")
    except sqlite3.IntegrityError as e:
        print("duplicate insertion rejected! OK")


if __name__ == "__main__":
    main()