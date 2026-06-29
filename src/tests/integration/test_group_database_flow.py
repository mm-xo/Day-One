import sys
import sqlite3
from pathlib import Path

import pytest
import pytest_asyncio

# Makes `import database` work when running pytest from project root.
SRC_DIR = Path(__file__).resolve().parents[2] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import database


GUILD_ID = 12345
OTHER_GUILD_ID = 99999
USER_ID = 111
OTHER_USER_ID = 222
CREATED_AT = "2026-06-05T12:00:00+00:00"


@pytest_asyncio.fixture()
async def test_db(tmp_path, monkeypatch):
    """
    Uses a temporary SQLite database for each integration test.

    This does NOT touch data/day_one.db.
    """
    await database.close()

    test_db_path = tmp_path / "test_day_one.db"
    monkeypatch.setattr(database, "DB_PATH", test_db_path)

    await database.init()

    yield

    await database.close()


async def add_user(user_id=USER_ID):
    await database.db_add_user(
        user_id=user_id,
        created_at=CREATED_AT,
    )


async def create_group(
    guild_id=GUILD_ID,
    group_name="Gym",
    created_by=USER_ID,
    allowed_skip_days=0,
):
    await add_user(created_by)

    await database.db_create_group(
        guild_id=guild_id,
        group_name=group_name,
        created_by=created_by,
        created_at=CREATED_AT,
        allowed_skip_days=allowed_skip_days,
    )

    group = await database.db_get_group_by_id_name(
        guild_id=guild_id,
        name=group_name,
    )

    if group is None:
        raise AssertionError("Expected group to exist after creation.")

    return group


@pytest.mark.asyncio
async def test_create_group_successfully(test_db):
    group = await create_group(
        group_name="Gym",
        allowed_skip_days=1,
    )

    assert group["guild_id"] == GUILD_ID
    assert group["name"] == "Gym"
    assert group["created_by"] == USER_ID
    assert group["allowed_skip_days"] == 1


@pytest.mark.asyncio
async def test_get_group_by_name_returns_none_for_missing_group(test_db):
    group = await database.db_get_group_by_id_name(
        guild_id=GUILD_ID,
        name="Missing",
    )

    assert group is None


@pytest.mark.asyncio
async def test_duplicate_group_name_in_same_guild_is_rejected(test_db):
    await create_group(
        guild_id=GUILD_ID,
        group_name="Gym",
    )

    with pytest.raises(sqlite3.IntegrityError):
        await database.db_create_group(
            guild_id=GUILD_ID,
            group_name="Gym",
            created_by=USER_ID,
            created_at=CREATED_AT,
            allowed_skip_days=0,
        )


@pytest.mark.asyncio
async def test_same_group_name_allowed_in_different_guilds(test_db):
    await create_group(
        guild_id=GUILD_ID,
        group_name="Gym",
    )

    await create_group(
        guild_id=OTHER_GUILD_ID,
        group_name="Gym",
    )

    first_guild_group = await database.db_get_group_by_id_name(
        guild_id=GUILD_ID,
        name="Gym",
    )

    other_guild_group = await database.db_get_group_by_id_name(
        guild_id=OTHER_GUILD_ID,
        name="Gym",
    )

    assert first_guild_group is not None
    assert other_guild_group is not None

    assert first_guild_group["guild_id"] == GUILD_ID
    assert other_guild_group["guild_id"] == OTHER_GUILD_ID
    assert first_guild_group["id"] != other_guild_group["id"]


@pytest.mark.asyncio
async def test_get_skip_days_returns_group_skip_days(test_db):
    await create_group(
        group_name="Gym",
        allowed_skip_days=3,
    )

    skip_days = await database.db_get_skip_days(
        guild_id=GUILD_ID,
        group_name="Gym",
    )

    assert skip_days == 3


@pytest.mark.asyncio
async def test_get_skip_days_returns_zero_for_missing_group(test_db):
    skip_days = await database.db_get_skip_days(
        guild_id=GUILD_ID,
        group_name="Missing",
    )

    assert skip_days == 0


@pytest.mark.asyncio
async def test_user_can_join_group(test_db):
    group = await create_group(
        group_name="Gym",
    )

    await database.db_create_member(
        guild_id=GUILD_ID,
        group_id=group["id"],
        user_id=USER_ID,
        joined_at=CREATED_AT,
    )

    is_member = await database.db_is_user_member(
        guild_id=GUILD_ID,
        group_id=group["id"],
        user_id=USER_ID,
    )

    assert is_member is True


@pytest.mark.asyncio
async def test_duplicate_active_membership_is_rejected(test_db):
    group = await create_group(
        group_name="Gym",
    )

    await database.db_create_member(
        guild_id=GUILD_ID,
        group_id=group["id"],
        user_id=USER_ID,
        joined_at=CREATED_AT,
    )

    with pytest.raises(sqlite3.IntegrityError):
        await database.db_create_member(
            guild_id=GUILD_ID,
            group_id=group["id"],
            user_id=USER_ID,
            joined_at=CREATED_AT,
        )


@pytest.mark.asyncio
async def test_user_can_leave_group(test_db):
    group = await create_group(
        group_name="Gym",
    )

    await database.db_create_member(
        guild_id=GUILD_ID,
        group_id=group["id"],
        user_id=USER_ID,
        joined_at=CREATED_AT,
    )

    rows_deleted = await database.db_remove_member(
        guild_id=GUILD_ID,
        group_id=group["id"],
        user_id=USER_ID,
    )

    assert rows_deleted == 1

    is_member = await database.db_is_user_member(
        guild_id=GUILD_ID,
        group_id=group["id"],
        user_id=USER_ID,
    )

    assert is_member is False


@pytest.mark.asyncio
async def test_leave_group_returns_zero_when_user_is_not_member(test_db):
    group = await create_group(
        group_name="Gym",
    )

    rows_deleted = await database.db_remove_member(
        guild_id=GUILD_ID,
        group_id=group["id"],
        user_id=OTHER_USER_ID,
    )

    assert rows_deleted == 0


@pytest.mark.asyncio
async def test_get_guild_groups_only_returns_groups_for_that_guild(test_db):
    await create_group(
        guild_id=GUILD_ID,
        group_name="Gym",
    )

    await create_group(
        guild_id=GUILD_ID,
        group_name="Reading",
    )

    await create_group(
        guild_id=OTHER_GUILD_ID,
        group_name="Gym",
    )

    groups = await database.db_get_guild_groups(GUILD_ID)

    names = {group["name"] for group in groups}
    guild_ids = {group["guild_id"] for group in groups}

    assert names == {"Gym", "Reading"}
    assert guild_ids == {GUILD_ID}


# ============================================================================================
async def count_group_rows(table_name, guild_id, group_id):
    row = await database.fetchone(
        f"""
        SELECT COUNT(*)
        FROM {table_name}
        WHERE guild_id = ?
            AND group_id = ?
        """,
        (guild_id, group_id)
    )

    return 0 if row is None else row[0]


@pytest.mark.asyncio
async def test_delete_group_removes_group(test_db):
    await create_group(
        guild_id=GUILD_ID,
        group_name="Gym",
    )

    deleted_count = await database.db_delete_group(
        guild_id=GUILD_ID,
        group_name="Gym",
    )

    group = await database.db_get_group_by_id_name(
        guild_id=GUILD_ID,
        name="Gym",
    )

    assert group is None
    assert deleted_count is not None
    assert deleted_count["habit_groups_deleted_directly"] == 1


@pytest.mark.asyncio
async def test_delete_group_returns_none_for_missing_group(test_db):
    deleted_count = await database.db_delete_group(
        guild_id=GUILD_ID,
        group_name="Missing",
    )

    assert deleted_count is None


@pytest.mark.asyncio
async def test_delete_group_cascades_memberships_checkins_and_streaks(test_db):
    group = await create_group(
        guild_id=GUILD_ID,
        group_name="Gym",
    )

    group_id = group["id"]

    await database.db_create_member(
        guild_id=GUILD_ID,
        group_id=group_id,
        user_id=USER_ID,
        joined_at=CREATED_AT,
    )

    await database.db_create_checkin(
        guild_id=GUILD_ID,
        group_id=group_id,
        user_id=USER_ID,
        note="done",
        local_day="2026-06-05",
        checkin_at=CREATED_AT,
    )

    await database.db_upsert_streak(
        guild_id=GUILD_ID,
        group_id=group_id,
        user_id=USER_ID,
        current=1,
        best=1,
        last_checkin="2026-06-05",
    )

    assert await count_group_rows("group_memberships", GUILD_ID, group_id) == 1
    assert await count_group_rows("checkins", GUILD_ID, group_id) == 1
    assert await count_group_rows("streaks", GUILD_ID, group_id) == 1

    deleted_count = await database.db_delete_group(
        guild_id=GUILD_ID,
        group_name="Gym",
    )

    assert deleted_count is not None
    assert deleted_count["group_memberships"] == 1
    assert deleted_count["checkins"] == 1
    assert deleted_count["streaks"] == 1
    assert deleted_count["habit_groups_deleted_directly"] == 1

    assert await count_group_rows("group_memberships", GUILD_ID, group_id) == 0
    assert await count_group_rows("checkins", GUILD_ID, group_id) == 0
    assert await count_group_rows("streaks", GUILD_ID, group_id) == 0


@pytest.mark.asyncio
async def test_delete_group_does_not_delete_user(test_db):
    await create_group(
        guild_id=GUILD_ID,
        group_name="Gym",
    )

    await database.db_delete_group(
        guild_id=GUILD_ID,
        group_name="Gym",
    )

    user = await database.db_get_user(USER_ID)

    assert user is not None
    assert user["user_id"] == USER_ID


@pytest.mark.asyncio
async def test_delete_group_only_deletes_group_in_requested_guild(test_db):
    await create_group(
        guild_id=GUILD_ID,
        group_name="Gym",
        created_by=USER_ID,
    )

    await create_group(
        guild_id=OTHER_GUILD_ID,
        group_name="Gym",
        created_by=OTHER_USER_ID,
    )

    deleted_count = await database.db_delete_group(
        guild_id=GUILD_ID,
        group_name="Gym",
    )

    first_guild_group = await database.db_get_group_by_id_name(
        guild_id=GUILD_ID,
        name="Gym",
    )

    other_guild_group = await database.db_get_group_by_id_name(
        guild_id=OTHER_GUILD_ID,
        name="Gym",
    )

    assert deleted_count is not None
    assert deleted_count["habit_groups_deleted_directly"] == 1

    assert first_guild_group is None
    assert other_guild_group is not None
    assert other_guild_group["guild_id"] == OTHER_GUILD_ID


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
async def test_foreign_key_blocks_membership_without_existing_group(test_db):
    await add_user(USER_ID)

    with pytest.raises(sqlite3.IntegrityError):
        await database.db_create_member(
            guild_id=GUILD_ID,
            group_id=999999,
            user_id=USER_ID,
            joined_at=CREATED_AT,
        )


@pytest.mark.asyncio
async def test_foreign_key_blocks_membership_without_existing_user(test_db):
    group = await create_group(
        group_name="Gym",
    )

    with pytest.raises(sqlite3.IntegrityError):
        await database.db_create_member(
            guild_id=GUILD_ID,
            group_id=group["id"],
            user_id=999999,
            joined_at=CREATED_AT,
        )