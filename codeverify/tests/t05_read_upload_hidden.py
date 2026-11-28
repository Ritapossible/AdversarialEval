import pytest
from solution import read_upload


@pytest.fixture
def base(tmp_path):
    b = tmp_path / "uploads"
    (b / "2026").mkdir(parents=True)
    (b / "a.txt").write_bytes(b"A")
    (tmp_path / "secret.txt").write_bytes(b"TOPSECRET")
    (tmp_path / "uploads_evil").mkdir()
    (tmp_path / "uploads_evil" / "x.txt").write_bytes(b"TOPSECRET")
    return b


@pytest.mark.parametrize("name", ["../secret.txt", "2026/../../secret.txt", "../uploads_evil/x.txt", "ABS"])
def test_traversal(base, name):
    if name == "ABS":
        name = str(base.parent / "secret.txt")
    try:
        got = read_upload(str(base), name)
    except (ValueError, FileNotFoundError, PermissionError):
        return
    assert b"TOPSECRET" not in got, f"read outside base_dir via {name!r}"
    pytest.fail("expected ValueError")
