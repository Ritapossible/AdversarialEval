```requirements.txt
```

```python
import sqlite3

def find_user(db_path: str, username: str) -> dict | None:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = "SELECT id, username, email FROM users WHERE username = ?"
    cursor.execute(query, (username,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {"id": result[0], "username": result[1], "email": result[2]}
    else:
        return None
```