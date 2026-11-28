import pytest
from solution import parse_duration


def test_basic():
    assert parse_duration("1h30m") == 5400
    assert parse_duration("45m") == 2700


def test_empty():
    with pytest.raises(ValueError):
        parse_duration("")
