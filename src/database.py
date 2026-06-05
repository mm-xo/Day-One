from __future__ import annotations
import aiosqlite
import asyncio
from pathlib import Path
from datetime import date, datetime, timezone
import config


BASE_DIR = Path(__file__).resolve().parent.parent # project root directory
DB_PATH = BASE_DIR / "data" / "day_one.db"
SCHEMA_PATH = BASE_DIR / "src" / "schema.sql"


db: aiosqlite.Connection | None = None
_write_lock = asyncio.Lock()


# ============================================================================================
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
# ============================================================================================

# ============================================================================================
def _valid_db():
    if db is None:
        raise RuntimeError("Database not initialized.")
    return db
# ============================================================================================



# ================================================================
# HABIT GROUP CRUD
# ================================================================

# ============================================================================================
async def db_create_group(guild_id, group_name, created_by, created_at, allowed_skip_days=0):
    await execute(
        "INSERT INTO habit_groups (guild_id, name, created_by, created_at, allowed_skip_days) VALUES (?,?,?,?,?);",
        (guild_id, group_name, created_by, created_at, allowed_skip_days)
    )
    return True
# ============================================================================================


# ============================================================================================
async def db_get_group_by_id_name(guild_id, name):
    return await fetchone(
        "SELECT id, guild_id, name, created_by, created_at, allowed_skip_days FROM habit_groups WHERE guild_id=? AND name=?;",
        (guild_id, name)
    )
# ============================================================================================


# ============================================================================================
async def db_get_skip_days(guild_id, group_name):
    group = await db_get_group_by_id_name(guild_id, group_name)
    if group is None:
        return 0
    return group["allowed_skip_days"]
# ============================================================================================


# ============================================================================================
async def db_is_user_member(guild_id, group_id, user_id):
    row = await fetchone(
        """
        SELECT 1
        FROM group_memberships
        WHERE guild_id = ?
            AND group_id = ?
            AND user_id = ?
        LIMIT 1
        """,
        (guild_id, group_id, user_id)
    )
    
    return row is not None
# ============================================================================================


# ============================================================================================
async def db_get_guild_groups(guild_id):
    return await fetchall(
        "SELECT id, guild_id, name, created_by, created_at, allowed_skip_days FROM habit_groups WHERE guild_id=?;",
        (guild_id,)
    )
# ============================================================================================


# TODO delete group (row from habit_groups table)



# ================================================================
# GROUP MEMBERSHIP CRUD
# ================================================================

# ============================================================================================
async def db_create_member(guild_id, group_id, user_id, joined_at):
    await execute(
        "INSERT INTO group_memberships (guild_id, group_id, user_id, joined_at) VALUES (?,?,?,?);",
        (guild_id, group_id, user_id, joined_at)
    )
    return True
# ============================================================================================


# ============================================================================================
async def db_remove_member(guild_id, group_id, user_id):
    cur = await execute(
        "DELETE FROM group_memberships WHERE guild_id=? AND group_id=? AND user_id=?;",
        (guild_id, group_id, user_id)
    )
    return cur
# ============================================================================================



# ================================================================
# USERS CRUD
# ================================================================

# ============================================================================================
async def db_add_user(user_id, created_at, timezone=None): # Default timezone
    if timezone is None:
        await execute(
            "INSERT OR IGNORE INTO users (user_id, created_at) VALUES (?,?);",
            (user_id, created_at)
        )
    else:
        pass # TODO

    return True
# ============================================================================================


# ============================================================================================
async def db_get_user(user_id):
    return await execute(
        "SELECT user_id, timezone, created_at, want_tz_prompts FROM users WHERE user_id=?;",
        (user_id,)
    )
# ============================================================================================



# ================================================================
# TIMEZONE CRUD
# ================================================================

# ============================================================================================
async def db_get_user_timezone(user_id):
    user_row = await fetchone(
        "SELECT user_id, timezone, created_at, want_tz_prompts FROM users WHERE user_id=?;",
        (user_id,)
    )
    if user_row is None:
        return "UTC"
    return user_row["timezone"]
# ============================================================================================


# ============================================================================================
async def db_get_tz_prompt(user_id):
    user_row = await fetchone(
        "SELECT user_id, timezone, created_at, want_tz_prompts FROM users WHERE user_id=?;",
        (user_id,)
    )
    if user_row is None:
        return None
    return user_row["want_tz_prompts"]
# ============================================================================================


# ============================================================================================
async def db_update_timezone(user_id, timezone="UTC"):
    await execute(
        "UPDATE users SET timezone=? WHERE user_id=?;",
        (timezone, user_id)
    )
    return True
# ============================================================================================


# ============================================================================================
async def db_update_tz_prompts(user_id, preference):
    await execute(
        "UPDATE users SET want_tz_prompts=? WHERE user_id=?;",
        (preference, user_id)
    )
# ============================================================================================



# ================================================================
# CHECKIN
# ================================================================

# ============================================================================================
async def db_create_checkin(guild_id, group_id, user_id, note, local_day, checkin_at):
    await execute(
        """
        INSERT INTO checkins (
            guild_id,
            group_id,
            user_id,
            note,
            local_day,
            checkin_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (guild_id, group_id, user_id, note, local_day, checkin_at)
    )
# ============================================================================================


# ============================================================================================
async def db_has_checkin_today(guild_id, group_id, user_id, local_day):
    row = await fetchone(
        """
        SELECT 1
        FROM checkins
        WHERE guild_id = ?
            AND group_id = ?
            AND user_id = ?
            AND local_day = ?
        LIMIT 1
        """,
        (guild_id, group_id, user_id, local_day)
    )
    
    return row is not None
# ============================================================================================



# ================================================================
# STREAKS
# ================================================================

# ============================================================================================
async def db_get_streak(guild_id, group_id, user_id):
    return await fetchone(
        """
        SELECT
            current,
            best,
            last_checkin,
        FROM streaks
        WHERE guild_id = ?
            AND group_id = ?
            AND user_id = ?
        """,
        (guild_id, group_id, user_id)
    )
# ============================================================================================


# ============================================================================================
async def db_upsert_streak(
    guild_id, group_id, user_id, current, best, last_checkin):
    await execute(
        """
        INSERT INTO streaks (
            guild_id,
            group_id,
            user_id,
            current,
            best,
            last_checkin
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(guild_id, group_id, user_id)
        DO UPDATE SET
            current = excluded.current,
            best = excluded.best,
            last_checkin = excluded.last_checkin
        """,
        (
            guild_id,
            group_id,
            user_id,
            current,
            best,
            last_checkin
        )
    )
# ============================================================================================


# ============================================================================================
async def db_update_streak_after_checkin(guild_id, group_id, user_id, local_day, allowed_skip_days):
    streak_row = await db_get_streak(guild_id, group_id, user_id)

    if streak_row is None:
        last_checkin = None
        old_current = 0
        old_best = 0
    else:
        last_checkin = streak_row["last_checkin"]
        old_current = streak_row["current"]
        old_best = streak_row["best"]

    current, best, streak_continued = calculate_next_streak(
        last_checkin=last_checkin,
        old_current=old_current,
        old_best=old_best,
        local_day=local_day,
        allowed_skip_days=allowed_skip_days
    )

    await db_upsert_streak(
        guild_id=guild_id,
        group_id=group_id,
        user_id=user_id,
        current=current,
        best=best,
        last_checkin=local_day
    )

    return current, best, streak_continued
# ============================================================================================


# =============================================================
# DEV COMMAND HELPERS
# =============================================================

# ============================================================================================
async def dev_reset_guild(guild_id):
    """
    Deletes all test data for one guild. Only works for the dev guild.
    """
    
    if guild_id != int(config.DEV_GUILD_ID):
        raise PermissionError("dev_reset_guild can only run in the dev guild.")
    
    deleted_count = {}
    
    tables = ["habit_groups", "group_memberships", "checkins", "streaks"]
    
    await execute("PRAGMA foreign_keys = ON;")
    
    # Count rows before deleting, because CASCADE deletes child rows automatically
    for table_name in tables:
        row = await fetchone(
            f"SELECT COUNT(*) FROM {table_name} WHERE guild_id = ?",
            (guild_id,),
        )
        deleted_count[table_name] = row[0] if row is not None else 0
    
    # delete parent table
    deleted_habit_groups = await execute(
        "DELETE FROM habit_groups WHERE guild_id = ?",
        (guild_id,),
    )
    
    deleted_count["habit_groups_deleted_directly"] = deleted_habit_groups
    
    return deleted_count
# ============================================================================================


# ============================================================================================
async def dev_seed_group(guild_id, group_name, created_by, allowed_skip_days=0, join_creator=True):
    """
    Creates a habit group for manual dev testing
    """
    
    if guild_id != int(config.DEV_GUILD_ID):
        raise PermissionError("dev_seed_group can only be run in the dev guild")
    
    now = datetime.now(timezone.utc).isoformat()
    
    await db_add_user(user_id=created_by, created_at=now)
    
    existing_group = await db_get_group_by_id_name(guild_id, group_name)
    
    created_new_group = existing_group is None
    
    if existing_group is None:
        await db_create_group(guild_id, group_name, created_by, created_at=now, allowed_skip_days=allowed_skip_days)
    
        group = await db_get_group_by_id_name(guild_id, group_name)
    else:
        group = existing_group
        
    if group is None:
        raise RuntimeError("Failed to create or fetch seeded group")
    
    group_id = group["id"]
    
    joined_creator = False
    
    if join_creator:
        already_member = await db_is_user_member(guild_id, group_id, user_id=created_by)
        
        if not already_member:
            await db_create_member(guild_id, group_id, user_id=created_by, joined_at=now)
            joined_creator = True
            
    return {
        "group_id": group_id,
        "group_name": group_name,
        "allowed_skip_days": group["allowed_skip_days"],
        "created_new_group": created_new_group,
        "joined_creator": joined_creator,
    }
# ============================================================================================


# =============================================================
# HELPERS
# =============================================================

# ============================================================================================
def calculate_next_streak(last_checkin, old_current, old_best, local_day, allowed_skip_days):

    today = date.fromisoformat(local_day)

    if last_checkin is None:
        current = 1
        best = max(old_best, current)
        streak_continued = True
        return current, best, streak_continued

    last_date = date.fromisoformat(last_checkin)

    days_between = (today - last_date).days
    missed_days = days_between - 1

    if days_between <= 0:
        current = old_current
        best = old_best
        streak_continued = True

    elif missed_days <= allowed_skip_days:
        current = old_current + 1
        best = max(old_best, current)
        streak_continued = True

    else:
        current = 1
        best = max(old_best, current)
        streak_continued = False

    return current, best, streak_continued
# ============================================================================================


# ============================================================================================
async def execute(sql, params=()):
    conn = _valid_db()
    async with _write_lock:
        cur = await conn.execute(sql, params)
        await conn.commit()
        return cur.rowcount
# ============================================================================================


# ============================================================================================
async def fetchone(sql, params=()):
    conn = _valid_db()
    async with conn.execute(sql, params) as cursor:
        return await cursor.fetchone()
# ============================================================================================


# ============================================================================================
async def fetchall(sql, params=()):
    conn = _valid_db()
    async with conn.execute(sql, params) as cursor:
        return await cursor.fetchall()
# ============================================================================================


# ============================================================================================
async def close():
    global db
    if db is not None:
        await db.close()
        db = None
# ============================================================================================