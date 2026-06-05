from services.group_logic import (
    normalize_group_name,
    is_valid_group_name,
    is_valid_allowed_skip_days,
)


def test_group_name_is_normalized():
    assert normalize_group_name("gym") == "GYM"
    assert normalize_group_name(" Gym ") == "GYM"
    assert normalize_group_name("gYm") == "GYM"


def test_group_name_rejects_empty_name():
    assert is_valid_group_name("") is False
    assert is_valid_group_name("   ") is False


def test_group_name_rejects_too_short_name():
    assert is_valid_group_name("A") is False


def test_group_name_rejects_too_long_name():
    assert is_valid_group_name("A" * 33) is False


def test_group_name_accepts_valid_names():
    assert is_valid_group_name("GYM") is True
    assert is_valid_group_name("READING") is True
    assert is_valid_group_name("NO SUGAR") is True


def test_allowed_skip_days_accepts_valid_values():
    assert is_valid_allowed_skip_days(0) is True
    assert is_valid_allowed_skip_days(1) is True
    assert is_valid_allowed_skip_days(7) is True


def test_allowed_skip_days_rejects_invalid_values():
    assert is_valid_allowed_skip_days(-1) is False
    assert is_valid_allowed_skip_days(8) is False
    assert is_valid_allowed_skip_days(999) is False