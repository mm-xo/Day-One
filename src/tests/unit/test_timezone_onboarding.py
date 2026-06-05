from zoneinfo import ZoneInfoNotFoundError
from services.timezone_onboarding import validate_timezone


def test_validate_timezone_with_valid_timezones():
    assert validate_timezone("UTC") is True
    assert validate_timezone("America/New_York") is True
    assert validate_timezone("Europe/London") is True
    assert validate_timezone("Asia/Tokyo") is True
    assert validate_timezone("Australia/Sydney") is True


def test_validate_timezone_with_invalid_timezones():
    assert validate_timezone("Invalid/Timezone") is False
    assert validate_timezone("NotATimezone") is False
    assert validate_timezone("America/InvalidCity") is False


def test_validate_timezone_accepts_utc_lowercase():
    assert validate_timezone("utc") is True
    assert validate_timezone("UTC") is True
