import sys
from pathlib import Path

import pytest

# Makes `import database` work when running pytest from project root.
SRC_DIR = Path(__file__).resolve().parents[2]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import database


# ================================================================
# calculate_next_streak unit tests
# ================================================================

def test_first_checkin_starts_streak():
    current, best, continued = database.calculate_next_streak(
        last_checkin=None,
        old_current=0,
        old_best=0,
        local_day="2026-06-05",
        allowed_skip_days=0,
    )

    assert current == 1
    assert best == 1
    assert continued is True


def test_same_day_checkin_does_not_increase_streak():
    current, best, continued = database.calculate_next_streak(
        last_checkin="2026-06-05",
        old_current=3,
        old_best=5,
        local_day="2026-06-05",
        allowed_skip_days=0,
    )

    assert current == 3
    assert best == 5
    assert continued is True


def test_next_day_checkin_continues_streak():
    current, best, continued = database.calculate_next_streak(
        last_checkin="2026-06-05",
        old_current=1,
        old_best=1,
        local_day="2026-06-06",
        allowed_skip_days=0,
    )

    assert current == 2
    assert best == 2
    assert continued is True


def test_missed_day_with_no_skips_resets_streak():
    current, best, continued = database.calculate_next_streak(
        last_checkin="2026-06-05",
        old_current=4,
        old_best=4,
        local_day="2026-06-07",
        allowed_skip_days=0,
    )

    assert current == 1
    assert best == 4
    assert continued is False


def test_missed_one_day_with_one_skip_continues_streak():
    current, best, continued = database.calculate_next_streak(
        last_checkin="2026-06-05",
        old_current=4,
        old_best=4,
        local_day="2026-06-07",
        allowed_skip_days=1,
    )

    assert current == 5
    assert best == 5
    assert continued is True


def test_gap_bigger_than_allowed_skips_resets_streak():
    current, best, continued = database.calculate_next_streak(
        last_checkin="2026-06-05",
        old_current=4,
        old_best=7,
        local_day="2026-06-09",
        allowed_skip_days=1,
    )

    assert current == 1
    assert best == 7
    assert continued is False


def test_best_streak_does_not_decrease_after_reset():
    current, best, continued = database.calculate_next_streak(
        last_checkin="2026-06-01",
        old_current=10,
        old_best=12,
        local_day="2026-06-10",
        allowed_skip_days=0,
    )

    assert current == 1
    assert best == 12
    assert continued is False


def test_best_streak_updates_when_current_passes_best():
    current, best, continued = database.calculate_next_streak(
        last_checkin="2026-06-05",
        old_current=5,
        old_best=5,
        local_day="2026-06-06",
        allowed_skip_days=0,
    )

    assert current == 6
    assert best == 6
    assert continued is True


def test_future_or_older_local_day_does_not_change_streak():
    current, best, continued = database.calculate_next_streak(
        last_checkin="2026-06-10",
        old_current=4,
        old_best=6,
        local_day="2026-06-09",
        allowed_skip_days=0,
    )

    assert current == 4
    assert best == 6
    assert continued is True


# ================================================================
# db_update_streak_after_checkin unit tests
# These do not touch the real database.
# ================================================================

@pytest.mark.asyncio
async def test_update_streak_after_first_checkin(monkeypatch):
    captured_upsert = {}

    async def fake_get_streak(guild_id, group_id, user_id):
        return None

    async def fake_upsert_streak(
        guild_id,
        group_id,
        user_id,
        current,
        best,
        last_checkin,
    ):
        captured_upsert.update(
            {
                "guild_id": guild_id,
                "group_id": group_id,
                "user_id": user_id,
                "current": current,
                "best": best,
                "last_checkin": last_checkin,
            }
        )

    monkeypatch.setattr(database, "db_get_streak", fake_get_streak)
    monkeypatch.setattr(database, "db_upsert_streak", fake_upsert_streak)

    current, best, continued = await database.db_update_streak_after_checkin(
        guild_id=1,
        group_id=10,
        user_id=100,
        local_day="2026-06-05",
        allowed_skip_days=0,
    )

    assert current == 1
    assert best == 1
    assert continued is True

    assert captured_upsert == {
        "guild_id": 1,
        "group_id": 10,
        "user_id": 100,
        "current": 1,
        "best": 1,
        "last_checkin": "2026-06-05",
    }


@pytest.mark.asyncio
async def test_update_streak_after_next_day_checkin(monkeypatch):
    captured_upsert = {}

    async def fake_get_streak(guild_id, group_id, user_id):
        return {
            "current": 2,
            "best": 3,
            "last_checkin": "2026-06-05",
        }

    async def fake_upsert_streak(
        guild_id,
        group_id,
        user_id,
        current,
        best,
        last_checkin,
    ):
        captured_upsert.update(
            {
                "current": current,
                "best": best,
                "last_checkin": last_checkin,
            }
        )

    monkeypatch.setattr(database, "db_get_streak", fake_get_streak)
    monkeypatch.setattr(database, "db_upsert_streak", fake_upsert_streak)

    current, best, continued = await database.db_update_streak_after_checkin(
        guild_id=1,
        group_id=10,
        user_id=100,
        local_day="2026-06-06",
        allowed_skip_days=0,
    )

    assert current == 3
    assert best == 3
    assert continued is True

    assert captured_upsert == {
        "current": 3,
        "best": 3,
        "last_checkin": "2026-06-06",
    }


@pytest.mark.asyncio
async def test_update_streak_after_missed_day_without_skip(monkeypatch):
    captured_upsert = {}

    async def fake_get_streak(guild_id, group_id, user_id):
        return {
            "current": 5,
            "best": 8,
            "last_checkin": "2026-06-05",
        }

    async def fake_upsert_streak(
        guild_id,
        group_id,
        user_id,
        current,
        best,
        last_checkin,
    ):
        captured_upsert.update(
            {
                "current": current,
                "best": best,
                "last_checkin": last_checkin,
            }
        )

    monkeypatch.setattr(database, "db_get_streak", fake_get_streak)
    monkeypatch.setattr(database, "db_upsert_streak", fake_upsert_streak)

    current, best, continued = await database.db_update_streak_after_checkin(
        guild_id=1,
        group_id=10,
        user_id=100,
        local_day="2026-06-07",
        allowed_skip_days=0,
    )

    assert current == 1
    assert best == 8
    assert continued is False

    assert captured_upsert == {
        "current": 1,
        "best": 8,
        "last_checkin": "2026-06-07",
    }


@pytest.mark.asyncio
async def test_update_streak_after_missed_day_with_skip(monkeypatch):
    captured_upsert = {}

    async def fake_get_streak(guild_id, group_id, user_id):
        return {
            "current": 5,
            "best": 5,
            "last_checkin": "2026-06-05",
        }

    async def fake_upsert_streak(
        guild_id,
        group_id,
        user_id,
        current,
        best,
        last_checkin,
    ):
        captured_upsert.update(
            {
                "current": current,
                "best": best,
                "last_checkin": last_checkin,
            }
        )

    monkeypatch.setattr(database, "db_get_streak", fake_get_streak)
    monkeypatch.setattr(database, "db_upsert_streak", fake_upsert_streak)

    current, best, continued = await database.db_update_streak_after_checkin(
        guild_id=1,
        group_id=10,
        user_id=100,
        local_day="2026-06-07",
        allowed_skip_days=1,
    )

    assert current == 6
    assert best == 6
    assert continued is True

    assert captured_upsert == {
        "current": 6,
        "best": 6,
        "last_checkin": "2026-06-07",
    }


@pytest.mark.asyncio
async def test_update_streak_same_day_does_not_increase(monkeypatch):
    captured_upsert = {}

    async def fake_get_streak(guild_id, group_id, user_id):
        return {
            "current": 3,
            "best": 5,
            "last_checkin": "2026-06-05",
        }

    async def fake_upsert_streak(
        guild_id,
        group_id,
        user_id,
        current,
        best,
        last_checkin,
    ):
        captured_upsert.update(
            {
                "current": current,
                "best": best,
                "last_checkin": last_checkin,
            }
        )

    monkeypatch.setattr(database, "db_get_streak", fake_get_streak)
    monkeypatch.setattr(database, "db_upsert_streak", fake_upsert_streak)

    current, best, continued = await database.db_update_streak_after_checkin(
        guild_id=1,
        group_id=10,
        user_id=100,
        local_day="2026-06-05",
        allowed_skip_days=0,
    )

    assert current == 3
    assert best == 5
    assert continued is True

    assert captured_upsert == {
        "current": 3,
        "best": 5,
        "last_checkin": "2026-06-05",
    }