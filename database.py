import sqlite3

DB_NAME = "kasper.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        role TEXT,
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def add_user(user_id, username, first_name):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    INSERT OR REPLACE INTO users
    (user_id, username, first_name)
    VALUES (?, ?, ?)
    """, (user_id, username, first_name))

    conn.commit()
    conn.close()


def save_message(user_id, role, content):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO messages(user_id, role, content)
    VALUES (?, ?, ?)
    """, (user_id, role, content))

    conn.commit()
    conn.close()


def get_history(user_id, limit=20):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    SELECT role, content
    FROM messages
    WHERE user_id=?
    ORDER BY id DESC
    LIMIT ?
    """, (user_id, limit))

    rows = cur.fetchall()

    conn.close()

    rows.reverse()

    return [
        {
            "role": role,
            "content": content
        }
        for role, content in rows
    ]


def clear_history(user_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM messages WHERE user_id=?",
        (user_id,)
    )

    conn.commit()
    conn.close()


def get_stats():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM messages")
    messages = cur.fetchone()[0]

    conn.close()

    return users, messages
