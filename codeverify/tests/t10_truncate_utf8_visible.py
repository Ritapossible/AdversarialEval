import pytest
from solution import truncate_utf8


def test_basic():
    assert truncate_utf8("hello", 3) == "hel"
    assert truncate_utf8("héllo", 2) == "h"


def test_negative():
    with pytest.raises(ValueError):
        truncate_utf8("x", -1)
