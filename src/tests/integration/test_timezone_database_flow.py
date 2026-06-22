import sys
from pathlib import Path

import pytest
import pytest_asyncio

# Makes `import database` work when running pytest from project root.
SRC_DIR = Path(__file__).resolve().parents[2] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import database


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


@pytest.mark.asyncio
async def test_missing_user_timezone_defaults_to_utc(test_db):
    timezone = await database.db_get_user_timezone(USER_ID)

    assert timezone == "UTC"


@pytest.mark.asyncio
async def test_new_user_timezone_defaults_to_utc(test_db):
    await add_user(USER_ID)

    timezone = await database.db_get_user_timezone(USER_ID)

    assert timezone == "UTC"


@pytest.mark.asyncio
async def test_update_timezone_changes_user_timezone(test_db):
    await add_user(USER_ID)

    result = await database.db_update_timezone(
        user_id=USER_ID,
        timezone="America/Winnipeg",
    )

    timezone = await database.db_get_user_timezone(USER_ID)

    assert result is True
    assert timezone == "America/Winnipeg"


@pytest.mark.asyncio
async def test_update_timezone_only_changes_target_user(test_db):
    await add_user(USER_ID)
    await add_user(OTHER_USER_ID)

    await database.db_update_timezone(
        user_id=USER_ID,
        timezone="America/Winnipeg",
    )

    first_user_timezone = await database.db_get_user_timezone(USER_ID)
    other_user_timezone = await database.db_get_user_timezone(OTHER_USER_ID)

    assert first_user_timezone == "America/Winnipeg"
    assert other_user_timezone == "UTC"


@pytest.mark.asyncio
async def test_update_timezone_for_missing_user_does_not_create_user(test_db):
    await database.db_update_timezone(
        user_id=USER_ID,
        timezone="America/Winnipeg",
    )

    timezone = await database.db_get_user_timezone(USER_ID)

    assert timezone == "UTC"


@pytest.mark.asyncio
async def test_missing_user_tz_prompt_returns_none(test_db):
    prompt_preference = await database.db_get_tz_prompt(USER_ID)

    assert prompt_preference is None


@pytest.mark.asyncio
async def test_new_user_has_timezone_prompt_preference(test_db):
    await add_user(USER_ID)

    prompt_preference = await database.db_get_tz_prompt(USER_ID)

    assert prompt_preference is not None


@pytest.mark.asyncio
async def test_update_tz_prompt_to_false(test_db):
    await add_user(USER_ID)

    await database.db_update_tz_prompts(
        user_id=USER_ID,
        preference=False,
    )

    prompt_preference = await database.db_get_tz_prompt(USER_ID)

    assert prompt_preference in (False, 0)


@pytest.mark.asyncio
async def test_update_tz_prompt_to_true(test_db):
    await add_user(USER_ID)

    await database.db_update_tz_prompts(
        user_id=USER_ID,
        preference=False,
    )

    await database.db_update_tz_prompts(
        user_id=USER_ID,
        preference=True,
    )

    prompt_preference = await database.db_get_tz_prompt(USER_ID)

    assert prompt_preference in (True, 1)


@pytest.mark.asyncio
async def test_update_tz_prompt_only_changes_target_user(test_db):
    await add_user(USER_ID)
    await add_user(OTHER_USER_ID)

    await database.db_update_tz_prompts(
        user_id=USER_ID,
        preference=False,
    )

    first_user_prompt = await database.db_get_tz_prompt(USER_ID)
    other_user_prompt = await database.db_get_tz_prompt(OTHER_USER_ID)

    assert first_user_prompt in (False, 0)
    assert other_user_prompt is not None
    assert other_user_prompt not in (False, 0)


@pytest.mark.asyncio
async def test_get_user_returns_user_row(test_db):
    await database.db_add_user(
        user_id=USER_ID,
        created_at=CREATED_AT,
    )

    user = await database.db_get_user(USER_ID)

    assert user is not None
    assert user["user_id"] == USER_ID
    assert user["timezone"] == "UTC"
    assert user["created_at"] == CREATED_AT


@pytest.mark.asyncio
async def test_add_user_with_timezone_sets_timezone(test_db):
    await database.db_add_user(
        user_id=USER_ID,
        created_at=CREATED_AT,
        timezone="America/Winnipeg",
    )

    timezone = await database.db_get_user_timezone(USER_ID)

    assert timezone == "America/Winnipeg"