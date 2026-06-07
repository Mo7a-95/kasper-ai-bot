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

ADMIN_ID = 685333833

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
    # ==========================
# COMMANDS
# ==========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton("🧠 الذاكرة", callback_data="memory"),
            InlineKeyboardButton("🗑 مسح الذاكرة", callback_data="clear")
        ],
        [
            InlineKeyboardButton("🎨 إنشاء صورة", callback_data="image_help")
        ]
    ]

    await update.message.reply_text(
        "أهلاً بك 👋\nأنا Kasper AI\nمساعد ذكي متقدم يعمل بالذكاء الاصطناعي.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = """
الأوامر المتاحة:

/start
بدء البوت

/help
المساعدة

/newchat
بدء محادثة جديدة

/memory
عرض عدد الرسائل المحفوظة

/clear
حذف الذاكرة

/image وصف الصورة
لإنشاء صورة جديدة
"""

    await update.message.reply_text(text)


async def newchat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    clear_memory(update.effective_user.id)

    await update.message.reply_text(
        "✅ تم بدء محادثة جديدة ومسح الذاكرة السابقة."
    )


async def memory(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    cursor.execute(
        "SELECT COUNT(*) FROM conversations WHERE user_id=?",
        (user_id,)
    )

    count = cursor.fetchone()[0]

    await update.message.reply_text(
        f"🧠 عدد الرسائل المحفوظة: {count}"
    )


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):

    clear_memory(update.effective_user.id)

    await update.message.reply_text(
        "🗑 تم حذف الذاكرة."
    )


# ==========================
# BUTTONS
# ==========================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    if query.data == "memory":

        user_id = query.from_user.id

        cursor.execute(
            "SELECT COUNT(*) FROM conversations WHERE user_id=?",
            (user_id,)
        )

        count = cursor.fetchone()[0]

        await query.message.reply_text(
            f"🧠 عدد الرسائل المحفوظة: {count}"
        )

    elif query.data == "clear":

        clear_memory(query.from_user.id)

        await query.message.reply_text(
            "🗑 تم حذف الذاكرة."
        )

    elif query.data == "image_help":

        await query.message.reply_text(
            "استخدم:\n/image وصف الصورة"
        )
        # ==========================
# CHAT
# ==========================

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        user_id = update.effective_user.id
        user_message = update.message.text

        save_message(
            user_id,
            "user",
            user_message
        )

        messages = get_history(user_id)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )

        answer = response.choices[0].message.content

        save_message(
            user_id,
            "assistant",
            answer
        )

        await update.message.reply_text(answer)

    except Exception as e:

        await update.message.reply_text(
            f"❌ خطأ:\n{e}"
        )
        # ==========================
# IMAGE GENERATION
# ==========================

async def generate_image(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    try:

        prompt = " ".join(context.args)

        if not prompt:

            await update.message.reply_text(
                "اكتب وصفاً بعد الأمر."
            )
            return

        await update.message.reply_text(
            "🎨 جاري إنشاء الصورة..."
        )

        result = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024"
        )

        image_base64 = result.data[0].b64_json

        import base64

        image_bytes = base64.b64decode(
            image_base64
        )

        with open(
            "generated_image.png",
            "wb"
        ) as f:
            f.write(image_bytes)

        await update.message.reply_photo(
            photo=open(
                "generated_image.png",
                "rb"
            )
        )

    except Exception as e:

        await update.message.reply_text(
            f"❌ {e}"
        )
# ==========================
# ADMIN PANEL
# ==========================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):


if update.effective_user.id != ADMIN_ID:

    await update.message.reply_text(
        "❌ هذا الأمر للمشرف فقط."
    )
    return

keyboard = [
    [
        InlineKeyboardButton(
            "📊 الإحصائيات",
            callback_data="admin_stats"
        )
    ],
    [
        InlineKeyboardButton(
            "👥 المستخدمون",
            callback_data="admin_users"
        )
    ],
    [
        InlineKeyboardButton(
            "📢 إرسال إعلان",
            callback_data="admin_broadcast"
        )
    ]
]

await update.message.reply_text(
    "👑 لوحة المشرف",
    reply_markup=InlineKeyboardMarkup(keyboard)
)


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):


await update.message.reply_text(
    f"🆔 Your ID:\n{update.effective_user.id}"
)



# ==========================
# MY ID
# ==========================

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):

await update.message.reply_text(
    f"🆔 Your ID:\n{update.effective_user.id}"
)

# ==========================
# RUN
# ==========================

app = ApplicationBuilder().token(
TELEGRAM_BOT_TOKEN
).build()

app.add_handler(
CommandHandler("start", start)
)

app.add_handler(
CommandHandler("help", help_command)
)

app.add_handler(
CommandHandler("newchat", newchat)
)

app.add_handler(
CommandHandler("memory", memory)
)

app.add_handler(
CommandHandler("clear", clear)
)

app.add_handler(
CommandHandler("image", generate_image)
)

app.add_handler(
CommandHandler("myid", myid)
)

app.add_handler(
CommandHandler("admin", admin)
)

app.add_handler(
CallbackQueryHandler(button_handler)
)

app.add_handler(
MessageHandler(
filters.TEXT & ~filters.COMMAND,
chat
)
)

print("🚀 Kasper AI Bot Started")

app.run_polling(
drop_pending_updates=True
)

