import pytest
from solution import read_upload


@pytest.fixture
def base(tmp_path):
    b = tmp_path / "uploads"
    (b / "2026").mkdir(parents=True)
    (b / "a.txt").write_bytes(b"A")
    (b / "2026" / "r.txt").write_bytes(b"R")
    return b


def test_reads(base):
    assert read_upload(str(base), "a.txt") == b"A"
    assert read_upload(str(base), "2026/r.txt") == b"R"


def test_missing(base):
    with pytest.raises(FileNotFoundError):
        read_upload(str(base), "nope.txt")
