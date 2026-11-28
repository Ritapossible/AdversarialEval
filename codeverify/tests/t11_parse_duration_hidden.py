import pytest
from solution import parse_duration


def test_full():
    assert parse_duration("1d2h30m15s") == 95415
    assert parse_duration("0s") == 0
    assert parse_duration("2h") == 7200


@pytest.mark.parametrize("bad", ["30m1h", "1h1h", "h", "1x", "-1h", "1.5h", "1h\n", " 1h", "1h 30m", "s"])
def test_invalid(bad):
    with pytest.raises(ValueError):
        parse_duration(bad)
