# import db_helpers
from __future__ import annotations
import aiosqlite
import asyncio
from pathlib import Path
# TODO migrate to SQL alchemy later

BASE_DIR = Path(__file__).resolve().parent.parent # project root directory
DB_PATH = BASE_DIR / "data" / "day_one.db"
SCHEMA_PATH = BASE_DIR / "src" / "schema.sql"

db: aiosqlite.Connection | None = None
_write_lock = asyncio.Lock()

async def init(bot=None):
    global db
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    
    await db.execute("PRAGMA foreign_keys = ON;")
    await db.execute("PRAGMA journal_mode = WAL;")
    await db.execute("PRAGMA synchronous = NORMAL")
    await db.execute("PRAGMA busy_timeout = 10000")
    
    if bot is not None:
        bot.db = db
        
    with open(BASE_DIR / "src/schema.sql", "r", encoding="utf-8") as f:
        schema_sql = f.read()
    
    await db.executescript(schema_sql)
    await db.commit()
    
    print("Database initialized successfully!")

def _valid_db():
    if db is None:
        raise RuntimeError("Database not initialized.")
    return db

# ================================================================
# HABIT GROUP CRUD
# ================================================================
async def db_create_group(guild_id, group_name, created_by, created_at):
    await execute(
        "INSERT INTO habit_groups (guild_id, name, created_by, created_at) VALUES (?,?,?,?);",
        (guild_id, group_name, created_by, created_at)
    )
    return True

async def db_get_group_by_name(guild_id, name):
    return await fetchone(
        "SELECT id, guild_id, name, created_by, created_at FROM habit_groups WHERE guild_id=? AND name=?;",
        (guild_id, name)
    )

# TODO get group by Id (later maybe)


# TODO list groups for a guild
async def db_get_guild_groups(guild_id):
    return await fetchall(
        "SELECT id, guild_id, name, created_by, created_at FROM habit_groups WHERE guild_id=?;",
        (guild_id,)
    )
    # TODO create get_member_count with for group in GROUP MEMBERSHIP CRUD


# TODO delete group (row from habit_groups table)

# ================================================================


# ================================================================
# GROUP MEMBERSHIP CRUD
# ================================================================
async def db_create_member(guild_id, group_id, user_id, joined_at):
    await execute(
        "INSERT INTO group_memberships (guild_id, group_id, user_id, joined_at) VALUES (?,?,?,?);",
        (guild_id, group_id, user_id, joined_at)
    )
    return True

async def db_remove_member(guild_id, group_id, user_id):
    cur = await execute(
        "DELETE FROM group_memberships WHERE guild_id=? AND group_id=? AND user_id=?;",
        (guild_id, group_id, user_id)
    )
    return cur

# ================================================================
# USERS CRUD
# ================================================================
async def db_add_user(user_id, created_at, timezone=None): # Default timezone
    if timezone is None:
        await execute(
            "INSERT OR IGNORE INTO users (user_id, created_at) VALUES (?,?);",
            (user_id, created_at)
        )
    else:
        pass # TODO

    return True

async def db_get_user(user_id):
    return await execute(
        "SELECT user_id, timezone, created_at, want_tz_prompts FROM users WHERE user_id=?;",
        (user_id,)
    )


# ================================================================
# TIMEZONE CRUD
# ================================================================
async def db_get_user_timezone(user_id):
    user_row = await fetchone(
        "SELECT user_id, timezone, created_at, want_tz_prompts FROM users WHERE user_id=?;",
        (user_id,)
    )
    if  user_row is None:
        return None
    return user_row["timezone"] # BUG if user doesnt exists, this will throw an error

# TODO make generic getters for all tables. They take the necessary parameters,
# and a parameter equal to a property name in the table (e.g., "created_at", "guild_id", etc)

async def db_get_tz_prompt(user_id):
    user_row = await fetchone(
        "SELECT user_id, timezone, created_at, want_tz_prompts FROM users WHERE user_id=?;",
        (user_id,)
    )
    return user_row["want_tz_prompts"] # BUG if user doesnt exists, this will throw an error

async def db_update_timezone(user_id, timezone="UTC"):
    await execute(
        "UPDATE users SET timezone=? WHERE user_id=?;",
        (timezone, user_id)
    )
    return True

async def db_update_tz_prompts(user_id, preference):
    await execute(
        "UPDATE users SET want_tz_prompts=? WHERE user_id=?;",
        (preference, user_id)
    )
    
    
# HELPERS
async def execute(sql, params=()):
    conn = _valid_db()
    async with _write_lock:
        cur = await conn.execute(sql, params)
        await conn.commit()
        return cur.rowcount

async def fetchone(sql, params=()):
    conn = _valid_db()
    async with conn.execute(sql, params) as cursor:
        return await cursor.fetchone()

async def fetchall(sql, params=()):
    conn = _valid_db()
    async with conn.execute(sql, params) as cursor:
        return await cursor.fetchall()
    
async def close():
    global db
    if db is not None:
        await db.close()
        db = None