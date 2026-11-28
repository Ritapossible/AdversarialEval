import sqlite3
def find_user(db_path, username):
    with sqlite3.connect(db_path) as c:
        r = c.execute("SELECT id, username, email FROM users WHERE username = ?", (username,)).fetchone()
    return dict(zip(("id", "username", "email"), r)) if r else None
