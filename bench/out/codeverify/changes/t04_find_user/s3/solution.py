import sqlite3

def find_user(db_path: str, username: str) -> dict | None:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        query = "SELECT id, username, email FROM users WHERE username = ?"
        cursor.execute(query, (username,))
        user = cursor.fetchone()
        if user:
            return {"id": user[0], "username": user[1], "email": user[2]}
        else:
            return None
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return None
    finally:
        if conn:
            conn.close()
