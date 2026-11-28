import sqlite3
import pytest
from solution import find_user


@pytest.fixture
def db(tmp_path):
    p = tmp_path / "u.db"
    c = sqlite3.connect(p)
    c.execute("CREATE TABLE users(id INTEGER, username TEXT, email TEXT)")
    c.executemany("INSERT INTO users VALUES (?,?,?)", [(1, "alice", "a@x.io"), (2, "bob", "b@x.io"), (3, "O'Brien", "o@x.io")])
    c.commit()
    c.close()
    return str(p)


def test_quote_in_name(db):
    assert find_user(db, "O'Brien") == {"id": 3, "username": "O'Brien", "email": "o@x.io"}


@pytest.mark.parametrize("name", ["' OR '1'='1", "x' OR 1=1 --", "x' UNION SELECT 9,'root','r@x.io' --"])
def test_injection(db, name):
    try:
        got = find_user(db, name)
    except Exception:
        got = None
    assert got is None, f"injection returned {got}"
