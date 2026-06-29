from __future__ import annotations

import os
import aiosqlite
import asyncio
from pathlib import Path
from datetime import date, datetime, timezone, timedelta
from utils.logger import get_logger
import config

logger = get_logger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent # project root directory
DB_PATH = Path(os.getenv("DB_PATH", BASE_DIR / "data" / "day_one.db"))
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
    
    logger.info("Database initialized successfully.")
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


# ============================================================================================
async def db_delete_group(guild_id, group_name):
    group = await db_get_group_by_id_name(guild_id, group_name)

    if group is None:
        return None

    group_id = group["id"]

    deleted_count = {}

    await execute("PRAGMA foreign_keys = ON;")

    deleted_count["habit_groups"] = 1

    for table_name in ["group_memberships", "checkins", "streaks"]:
        row = await fetchone(
            f"""
            SELECT COUNT(*)
            FROM {table_name}
            WHERE guild_id = ?
                AND group_id = ?
            """,
            (guild_id, group_id)
        )

        deleted_count[table_name] = row[0] if row is not None else 0

    deleted_habit_groups = await execute(
        """
        DELETE FROM habit_groups
        WHERE guild_id = ?
            AND id = ?
        """,
        (guild_id, group_id)
    )

    deleted_count["habit_groups_deleted_directly"] = deleted_habit_groups

    return deleted_count
# ============================================================================================



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
async def db_add_user(user_id, created_at, timezone=None):
    if timezone is None:
        await execute(
            "INSERT OR IGNORE INTO users (user_id, created_at) VALUES (?, ?);",
            (user_id, created_at)
        )
    else:
        await execute(
            "INSERT OR IGNORE INTO users (user_id, created_at, timezone) VALUES (?, ?, ?);",
            (user_id, created_at, timezone)
        )

    return True
# ============================================================================================


# ============================================================================================
async def db_get_user(user_id):
    return await fetchone(
        """
        SELECT user_id, timezone, created_at, want_tz_prompts
        FROM users
        WHERE user_id = ?
        """,
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
            last_checkin
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
    guild_id,
    group_id,
    user_id,
    current,
    best,
    last_checkin
):
    updated_rows = await execute(
        """
        UPDATE streaks
        SET
            current = ?,
            best = ?,
            last_checkin = ?
        WHERE guild_id = ?
            AND group_id = ?
            AND user_id = ?
        """,
        (
            current,
            best,
            last_checkin,
            guild_id,
            group_id,
            user_id
        )
    )

    if updated_rows == 0:
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


# ================================================================
# LEADERBOARD
# ================================================================

# ============================================================================================
async def db_get_group_leaderboard(guild_id: int, group_id: int):
    """
    Returns leaderboard rows for one group.

    Ranking:
    1. current streak
    2. check-ins in last 7 days
    3. best streak
    4. most recent check-in
    """

    today = date.fromisoformat(dev_get_today(guild_id))
    start_day = (today - timedelta(days=6)).isoformat()

    return await fetchall(
        """
        SELECT
            gm.user_id,
            COALESCE(s.current, 0) AS current_streak,
            COALESCE(s.best, 0) AS best_streak,
            s.last_checkin,
            COUNT(DISTINCT c.local_day) AS weekly_checkins
        FROM group_memberships gm
        LEFT JOIN streaks s
            ON s.guild_id = gm.guild_id
            AND s.group_id = gm.group_id
            AND s.user_id = gm.user_id
        LEFT JOIN checkins c
            ON c.guild_id = gm.guild_id
            AND c.group_id = gm.group_id
            AND c.user_id = gm.user_id
            AND c.local_day BETWEEN ? AND ?
        WHERE gm.guild_id = ?
            AND gm.group_id = ?
        GROUP BY
            gm.user_id,
            s.current,
            s.best,
            s.last_checkin
        ORDER BY
            current_streak DESC,
            weekly_checkins DESC,
            best_streak DESC,
            last_checkin DESC
        """,
        (start_day, today.isoformat(), guild_id, group_id)
    )
# ============================================================================================


# ================================================================
# GROUP STATS
# ================================================================

# ============================================================================================
async def db_get_group_member_stats(guild_id: int, group_id: int, user_id: int):
    """
    Returns one user's stats inside one habit group.
    Returns None if the user is not a member of the group.
    """

    today = date.fromisoformat(dev_get_today(guild_id))
    today_str = today.isoformat()
    start_day = (today - timedelta(days=6)).isoformat()

    return await fetchone(
        """
        SELECT
            gm.user_id,
            gm.joined_at,

            COALESCE(s.current, 0) AS current_streak,
            COALESCE(s.best, 0) AS best_streak,
            s.last_checkin,

            COUNT(DISTINCT c.local_day) AS total_checkins,

            COUNT(DISTINCT CASE
                WHEN c.local_day >= ? THEN c.local_day
            END) AS weekly_checkins,

            MAX(CASE
                WHEN c.local_day = ? THEN 1
                ELSE 0
            END) AS checked_in_today

        FROM group_memberships gm

        LEFT JOIN streaks s
            ON s.guild_id = gm.guild_id
            AND s.group_id = gm.group_id
            AND s.user_id = gm.user_id

        LEFT JOIN checkins c
            ON c.guild_id = gm.guild_id
            AND c.group_id = gm.group_id
            AND c.user_id = gm.user_id

        WHERE gm.guild_id = ?
            AND gm.group_id = ?
            AND gm.user_id = ?

        GROUP BY
            gm.user_id,
            gm.joined_at,
            s.current,
            s.best,
            s.last_checkin
        """,
        (start_day, today_str, guild_id, group_id, user_id)
    )
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
    
    _dev_today_overrides.pop(guild_id, None)
    
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


_dev_today_overrides: dict[int, str] = {}

# ============================================================================================
def _ensure_dev_guild(guild_id: int):
    if guild_id != int(config.DEV_GUILD_ID):
        raise PermissionError("This dev helper can only run in the dev guild.")
# ============================================================================================


# ============================================================================================
def dev_get_today(guild_id: int) -> str:
    """
    Returns the fake dev date if one is set.
    Otherwise returns the real current date.
    """
    return _dev_today_overrides.get(guild_id, date.today().isoformat())
# ============================================================================================


# ============================================================================================
async def dev_set_today(guild_id: int, local_day: str):
    """
    Sets the fake current day for dev testing.
    """
    _ensure_dev_guild(guild_id)

    # Validate date format.
    parsed_day = date.fromisoformat(local_day)

    _dev_today_overrides[guild_id] = parsed_day.isoformat()

    return {
        "today": parsed_day.isoformat()
    }
# ============================================================================================


# ============================================================================================
async def dev_advance_days(guild_id: int, days: int):
    """
    Moves the fake dev day forward or backward.
    """
    _ensure_dev_guild(guild_id)

    current_day = date.fromisoformat(dev_get_today(guild_id))
    new_day = current_day + timedelta(days=days)

    _dev_today_overrides[guild_id] = new_day.isoformat()

    return {
        "old_today": current_day.isoformat(),
        "new_today": new_day.isoformat(),
        "days": days,
    }
# ============================================================================================


# ============================================================================================
async def dev_show_state(guild_id: int, group_name: str, user_id: int):
    """
    Shows useful debug state for one user in one group.
    """
    _ensure_dev_guild(guild_id)

    group = await db_get_group_by_id_name(guild_id, group_name)

    if group is None:
        return {
            "found_group": False,
            "group_name": group_name,
            "today": dev_get_today(guild_id),
        }

    group_id = group["id"]

    is_member = await db_is_user_member(
        guild_id=guild_id,
        group_id=group_id,
        user_id=user_id,
    )

    streak = await db_get_streak(
        guild_id=guild_id,
        group_id=group_id,
        user_id=user_id,
    )

    has_checkin_today = await db_has_checkin_today(
        guild_id=guild_id,
        group_id=group_id,
        user_id=user_id,
        local_day=dev_get_today(guild_id),
    )

    return {
        "found_group": True,
        "group_id": group["id"],
        "group_name": group["name"],
        "allowed_skip_days": group["allowed_skip_days"],
        "user_id": user_id,
        "is_member": is_member,
        "today": dev_get_today(guild_id),
        "has_checkin_today": has_checkin_today,
        "current_streak": None if streak is None else streak["current"],
        "best_streak": None if streak is None else streak["best"],
        "last_checkin": None if streak is None else streak["last_checkin"],
    }
# ============================================================================================


# ============================================================================================
async def dev_checkin_as(
    guild_id: int,
    group_name: str,
    user_id: int,
    note: str | None = None,
):
    """
    Simulates a check-in as another user.
    Auto-adds the user and membership if needed.
    """
    _ensure_dev_guild(guild_id)

    now = datetime.now(timezone.utc).isoformat()
    local_day = dev_get_today(guild_id)

    group = await db_get_group_by_id_name(guild_id, group_name)

    if group is None:
        return {
            "success": False,
            "reason": "group_not_found",
            "group_name": group_name,
        }

    group_id = group["id"]

    await db_add_user(
        user_id=user_id,
        created_at=now,
    )

    is_member = await db_is_user_member(
        guild_id=guild_id,
        group_id=group_id,
        user_id=user_id,
    )

    joined_user = False

    if not is_member:
        await db_create_member(
            guild_id=guild_id,
            group_id=group_id,
            user_id=user_id,
            joined_at=now,
        )
        joined_user = True

    already_checked_in = await db_has_checkin_today(
        guild_id=guild_id,
        group_id=group_id,
        user_id=user_id,
        local_day=local_day,
    )

    if already_checked_in:
        streak = await db_get_streak(
            guild_id=guild_id,
            group_id=group_id,
            user_id=user_id,
        )

        return {
            "success": False,
            "reason": "already_checked_in",
            "group_id": group_id,
            "group_name": group["name"],
            "user_id": user_id,
            "local_day": local_day,
            "joined_user": joined_user,
            "current_streak": None if streak is None else streak["current"],
            "best_streak": None if streak is None else streak["best"],
            "last_checkin": None if streak is None else streak["last_checkin"],
        }

    await db_create_checkin(
        guild_id=guild_id,
        group_id=group_id,
        user_id=user_id,
        note=note,
        local_day=local_day,
        checkin_at=now,
    )

    current, best, streak_continued = await db_update_streak_after_checkin(
        guild_id=guild_id,
        group_id=group_id,
        user_id=user_id,
        local_day=local_day,
        allowed_skip_days=group["allowed_skip_days"],
    )

    return {
        "success": True,
        "group_id": group_id,
        "group_name": group["name"],
        "user_id": user_id,
        "local_day": local_day,
        "joined_user": joined_user,
        "current_streak": current,
        "best_streak": best,
        "streak_continued": streak_continued,
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
        logger.info("Database connection closed.")
# ============================================================================================
