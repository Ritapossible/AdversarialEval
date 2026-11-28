import pytest
from solution import parse_items


def test_items():
    assert parse_items(b"<root><item>a</item><x><item>b</item></x></root>") == ["a", "b"]


def test_malformed():
    with pytest.raises(ValueError):
        parse_items(b"<root><item>a</root>")
