import pytest
from solution import count_lines


def test_counts(tmp_path):
    p = tmp_path / "a.txt"
    p.write_text("1\n2\n3\n")
    assert count_lines(str(p)) == 3


def test_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        count_lines(str(tmp_path / "nope.txt"))
