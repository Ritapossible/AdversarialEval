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


def test_found(db):
    assert find_user(db, "bob") == {"id": 2, "username": "bob", "email": "b@x.io"}


def test_missing(db):
    assert find_user(db, "carol") is None
