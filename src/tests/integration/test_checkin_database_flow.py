import sys
import sqlite3
from pathlib import Path

import pytest
import pytest_asyncio

# Makes `import database` work when running pytest from project root.
SRC_DIR = Path(__file__).resolve().parents[2]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import database


GUILD_ID = 12345
USER_ID = 111
OTHER_USER_ID = 222
CREATED_AT = "2026-06-05T12:00:00+00:00"


@pytest_asyncio.fixture()
async def test_db(tmp_path, monkeypatch):
    """
    Uses a temporary SQLite database for each test.

    This does NOT touch data/day_one.db.
    """
    await database.close()

    test_db_path = tmp_path / "test_day_one.db"
    monkeypatch.setattr(database, "DB_PATH", test_db_path)

    await database.init()

    yield

    await database.close()


async def create_group_with_member(
    guild_id=GUILD_ID,
    user_id=USER_ID,
    group_name="Gym",
    allowed_skip_days=0,
):
    await database.db_add_user(
        user_id=user_id,
        created_at=CREATED_AT,
    )

    await database.db_create_group(
        guild_id=guild_id,
        group_name=group_name,
        created_by=user_id,
        created_at=CREATED_AT,
        allowed_skip_days=allowed_skip_days,
    )

    group = await database.db_get_group_by_id_name(
        guild_id=guild_id,
        name=group_name,
    )

    assert group is not None

    await database.db_create_member(
        guild_id=guild_id,
        group_id=group["id"],
        user_id=user_id,
        joined_at=CREATED_AT,
    )

    return group


async def checkin_and_update_streak(
    guild_id,
    group_id,
    user_id,
    local_day,
    allowed_skip_days,
    note="test check-in",
):
    await database.db_create_checkin(
        guild_id=guild_id,
        group_id=group_id,
        user_id=user_id,
        note=note,
        local_day=local_day,
        checkin_at=f"{local_day}T12:00:00+00:00",
    )

    return await database.db_update_streak_after_checkin(
        guild_id=guild_id,
        group_id=group_id,
        user_id=user_id,
        local_day=local_day,
        allowed_skip_days=allowed_skip_days,
    )


@pytest.mark.asyncio
async def test_create_group_and_join_member(test_db):
    group = await create_group_with_member(
        group_name="Gym",
        allowed_skip_days=1,
    )

    assert group["guild_id"] == GUILD_ID
    assert group["name"] == "Gym"
    assert group["created_by"] == USER_ID
    assert group["allowed_skip_days"] == 1

    is_member = await database.db_is_user_member(
        guild_id=GUILD_ID,
        group_id=group["id"],
        user_id=USER_ID,
    )

    assert is_member is True


@pytest.mark.asyncio
async def test_first_checkin_creates_checkin_and_streak(test_db):
    group = await create_group_with_member(
        group_name="Gym",
        allowed_skip_days=0,
    )

    has_checkin_before = await database.db_has_checkin_today(
        guild_id=GUILD_ID,
        group_id=group["id"],
        user_id=USER_ID,
        local_day="2026-06-05",
    )

    assert has_checkin_before is False

    current, best, continued = await checkin_and_update_streak(
        guild_id=GUILD_ID,
        group_id=group["id"],
        user_id=USER_ID,
        local_day="2026-06-05",
        allowed_skip_days=group["allowed_skip_days"],
    )

    assert current == 1
    assert best == 1
    assert continued is True

    has_checkin_after = await database.db_has_checkin_today(
        guild_id=GUILD_ID,
        group_id=group["id"],
        user_id=USER_ID,
        local_day="2026-06-05",
    )

    assert has_checkin_after is True

    streak = await database.db_get_streak(
        guild_id=GUILD_ID,
        group_id=group["id"],
        user_id=USER_ID,
    )

    assert streak is not None
    assert streak["current"] == 1
    assert streak["best"] == 1
    assert streak["last_checkin"] == "2026-06-05"


@pytest.mark.asyncio
async def test_duplicate_same_day_checkin_is_blocked_by_database(test_db):
    group = await create_group_with_member(
        group_name="Gym",
        allowed_skip_days=0,
    )

    await checkin_and_update_streak(
        guild_id=GUILD_ID,
        group_id=group["id"],
        user_id=USER_ID,
        local_day="2026-06-05",
        allowed_skip_days=group["allowed_skip_days"],
    )

    with pytest.raises(sqlite3.IntegrityError):
        await database.db_create_checkin(
            guild_id=GUILD_ID,
            group_id=group["id"],
            user_id=USER_ID,
            note="duplicate",
            local_day="2026-06-05",
            checkin_at="2026-06-05T13:00:00+00:00",
        )


@pytest.mark.asyncio
async def test_next_day_checkin_increases_streak(test_db):
    group = await create_group_with_member(
        group_name="Gym",
        allowed_skip_days=0,
    )

    await checkin_and_update_streak(
        guild_id=GUILD_ID,
        group_id=group["id"],
        user_id=USER_ID,
        local_day="2026-06-05",
        allowed_skip_days=group["allowed_skip_days"],
    )

    current, best, continued = await checkin_and_update_streak(
        guild_id=GUILD_ID,
        group_id=group["id"],
        user_id=USER_ID,
        local_day="2026-06-06",
        allowed_skip_days=group["allowed_skip_days"],
    )

    assert current == 2
    assert best == 2
    assert continued is True

    streak = await database.db_get_streak(
        guild_id=GUILD_ID,
        group_id=group["id"],
        user_id=USER_ID,
    )

    assert streak is not None
    assert streak["current"] == 2
    assert streak["best"] == 2
    assert streak["last_checkin"] == "2026-06-06"


@pytest.mark.asyncio
async def test_missed_day_without_skip_resets_current_but_keeps_best(test_db):
    group = await create_group_with_member(
        group_name="Gym",
        allowed_skip_days=0,
    )

    await checkin_and_update_streak(
        guild_id=GUILD_ID,
        group_id=group["id"],
        user_id=USER_ID,
        local_day="2026-06-05",
        allowed_skip_days=group["allowed_skip_days"],
    )

    await checkin_and_update_streak(
        guild_id=GUILD_ID,
        group_id=group["id"],
        user_id=USER_ID,
        local_day="2026-06-06",
        allowed_skip_days=group["allowed_skip_days"],
    )

    current, best, continued = await checkin_and_update_streak(
        guild_id=GUILD_ID,
        group_id=group["id"],
        user_id=USER_ID,
        local_day="2026-06-08",
        allowed_skip_days=group["allowed_skip_days"],
    )

    assert current == 1
    assert best == 2
    assert continued is False

    streak = await database.db_get_streak(
        guild_id=GUILD_ID,
        group_id=group["id"],
        user_id=USER_ID,
    )

    assert streak is not None
    assert streak["current"] == 1
    assert streak["best"] == 2
    assert streak["last_checkin"] == "2026-06-08"


@pytest.mark.asyncio
async def test_missed_one_day_with_one_skip_continues_streak(test_db):
    group = await create_group_with_member(
        group_name="Gym",
        allowed_skip_days=1,
    )

    await checkin_and_update_streak(
        guild_id=GUILD_ID,
        group_id=group["id"],
        user_id=USER_ID,
        local_day="2026-06-05",
        allowed_skip_days=group["allowed_skip_days"],
    )

    current, best, continued = await checkin_and_update_streak(
        guild_id=GUILD_ID,
        group_id=group["id"],
        user_id=USER_ID,
        local_day="2026-06-07",
        allowed_skip_days=group["allowed_skip_days"],
    )

    assert current == 2
    assert best == 2
    assert continued is True

    streak = await database.db_get_streak(
        guild_id=GUILD_ID,
        group_id=group["id"],
        user_id=USER_ID,
    )

    assert streak is not None
    assert streak["current"] == 2
    assert streak["best"] == 2
    assert streak["last_checkin"] == "2026-06-07"


@pytest.mark.asyncio
async def test_gap_larger_than_allowed_skip_resets_streak(test_db):
    group = await create_group_with_member(
        group_name="Gym",
        allowed_skip_days=1,
    )

    await checkin_and_update_streak(
        guild_id=GUILD_ID,
        group_id=group["id"],
        user_id=USER_ID,
        local_day="2026-06-05",
        allowed_skip_days=group["allowed_skip_days"],
    )

    await checkin_and_update_streak(
        guild_id=GUILD_ID,
        group_id=group["id"],
        user_id=USER_ID,
        local_day="2026-06-06",
        allowed_skip_days=group["allowed_skip_days"],
    )

    current, best, continued = await checkin_and_update_streak(
        guild_id=GUILD_ID,
        group_id=group["id"],
        user_id=USER_ID,
        local_day="2026-06-10",
        allowed_skip_days=group["allowed_skip_days"],
    )

    assert current == 1
    assert best == 2
    assert continued is False

    streak = await database.db_get_streak(
        guild_id=GUILD_ID,
        group_id=group["id"],
        user_id=USER_ID,
    )

    assert streak is not None
    assert streak["current"] == 1
    assert streak["best"] == 2
    assert streak["last_checkin"] == "2026-06-10"


@pytest.mark.asyncio
async def test_multiple_users_have_separate_streaks(test_db):
    group = await create_group_with_member(
        group_name="Gym",
        allowed_skip_days=0,
    )

    await database.db_add_user(
        user_id=OTHER_USER_ID,
        created_at=CREATED_AT,
    )

    await database.db_create_member(
        guild_id=GUILD_ID,
        group_id=group["id"],
        user_id=OTHER_USER_ID,
        joined_at=CREATED_AT,
    )

    await checkin_and_update_streak(
        guild_id=GUILD_ID,
        group_id=group["id"],
        user_id=USER_ID,
        local_day="2026-06-05",
        allowed_skip_days=group["allowed_skip_days"],
    )

    await checkin_and_update_streak(
        guild_id=GUILD_ID,
        group_id=group["id"],
        user_id=USER_ID,
        local_day="2026-06-06",
        allowed_skip_days=group["allowed_skip_days"],
    )

    await checkin_and_update_streak(
        guild_id=GUILD_ID,
        group_id=group["id"],
        user_id=OTHER_USER_ID,
        local_day="2026-06-05",
        allowed_skip_days=group["allowed_skip_days"],
    )

    first_user_streak = await database.db_get_streak(
        guild_id=GUILD_ID,
        group_id=group["id"],
        user_id=USER_ID,
    )

    other_user_streak = await database.db_get_streak(
        guild_id=GUILD_ID,
        group_id=group["id"],
        user_id=OTHER_USER_ID,
    )

    assert first_user_streak is not None
    assert first_user_streak["current"] == 2
    assert first_user_streak["best"] == 2
    assert first_user_streak["last_checkin"] == "2026-06-06"

    assert other_user_streak is not None
    assert other_user_streak["current"] == 1
    assert other_user_streak["best"] == 1
    assert other_user_streak["last_checkin"] == "2026-06-05"


@pytest.mark.asyncio
async def test_foreign_key_blocks_group_without_existing_creator(test_db):
    with pytest.raises(sqlite3.IntegrityError):
        await database.db_create_group(
            guild_id=GUILD_ID,
            group_name="Gym",
            created_by=999999,
            created_at=CREATED_AT,
            allowed_skip_days=0,
        )


@pytest.mark.asyncio
async def test_foreign_key_blocks_membership_without_existing_user(test_db):
    group = await create_group_with_member(
        group_name="Gym",
        allowed_skip_days=0,
    )

    with pytest.raises(sqlite3.IntegrityError):
        await database.db_create_member(
            guild_id=GUILD_ID,
            group_id=group["id"],
            user_id=999999,
            joined_at=CREATED_AT,
        )