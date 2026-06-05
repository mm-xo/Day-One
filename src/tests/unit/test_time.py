import pytest
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from utils.time import get_utc_now_iso, get_local_today_iso


def test_get_utc_now_iso_returns_string():
    result = get_utc_now_iso()
    assert isinstance(result, str)


def test_get_utc_now_iso_valid_iso_format():
    result = get_utc_now_iso()
    parsed = datetime.fromisoformat(result)
    assert parsed.tzinfo == timezone.utc


def test_get_utc_now_iso_no_microseconds():
    result = get_utc_now_iso()
    assert ".000000" not in result
    assert "T" in result


def test_get_local_today_iso_returns_string():
    result = get_local_today_iso("UTC")
    assert isinstance(result, str)


def test_get_local_today_iso_valid_iso_date_format():
    result = get_local_today_iso("UTC")
    parsed = datetime.fromisoformat(result).date()
    assert parsed is not None


def test_get_local_today_iso_utc():
    now_utc = datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    result = get_local_today_iso("UTC", now_utc)
    assert result == "2025-06-15"


def test_get_local_today_iso_with_positive_offset():
    now_utc = datetime(2025, 6, 15, 22, 0, 0, tzinfo=timezone.utc)
    result = get_local_today_iso("Asia/Tokyo", now_utc)
    assert result == "2025-06-16"


def test_get_local_today_iso_with_negative_offset():
    now_utc = datetime(2025, 6, 15, 4, 0, 0, tzinfo=timezone.utc)
    result = get_local_today_iso("America/New_York", now_utc)
    assert result == "2025-06-15"


def test_get_local_today_iso_midnight_boundary():
    now_utc = datetime(2025, 6, 15, 3, 59, 0, tzinfo=timezone.utc)
    result = get_local_today_iso("America/New_York", now_utc)
    assert result == "2025-06-14"


def test_get_local_today_iso_invalid_timezone():
    with pytest.raises(ValueError, match="Invalid timezone"):
        get_local_today_iso("Invalid/Timezone")


def test_get_local_today_iso_without_now_utc_parameter():
    result = get_local_today_iso("UTC")
    expected = datetime.now(timezone.utc).date().isoformat()
    assert result == expected
