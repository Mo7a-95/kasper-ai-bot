from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from openai import OpenAI

import sqlite3
import os
import requests
import tempfile

# ==========================
# TOKENS
# ==========================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# ==========================
# DATABASE
# ==========================

db = sqlite3.connect(
    "memory.db",
    check_same_thread=False
)

cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS conversations(
    user_id INTEGER,
    role TEXT,
    content TEXT
)
""")

db.commit()

MAX_MEMORY = 20

# ==========================
# MEMORY FUNCTIONS
# ==========================

def save_message(user_id, role, content):
    cursor.execute(
        "INSERT INTO conversations VALUES (?, ?, ?)",
        (user_id, role, content)
    )
    db.commit()

def get_history(user_id):

    cursor.execute("""
    SELECT role, content
    FROM conversations
    WHERE user_id=?
    ORDER BY rowid DESC
    LIMIT ?
    """, (user_id, MAX_MEMORY))

    rows = cursor.fetchall()

    rows.reverse()

    messages = [
        {
            "role": "system",
            "content":
            """
            أنت Kasper AI.

            مساعد ذكي متقدم.
            تتحدث العربية بطلاقة.
            تجيب باحترافية.
            تساعد في البرمجة.
            تساعد في الأعمال.
            تساعد في التصميم.
            تساعد في الدراسة.
            تساعد في كتابة المحتوى.
            """
        }
    ]

    for role, content in rows:
        messages.append({
            "role": role,
            "content": content
        })

    return messages

def clear_memory(user_id):

    cursor.execute(
        "DELETE FROM conversations WHERE user_id=?",
        (user_id,)
    )

    db.commit()
