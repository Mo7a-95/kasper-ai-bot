from telegram import BotCommand
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

import tempfile
import sqlite3
import os
import requests
from pypdf import PdfReader
import base64
from pdf2image import convert_from_path

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

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

    cursor.execute(
        """
        INSERT OR IGNORE INTO users
        (user_id, username, first_name)
        VALUES (?, ?, ?)
        """,
        (
            user.id,
            user.username,
            user.first_name
        )
    )

    db.commit()
    
# ==========================
# COMMANDS
# ==========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    save_user(update.effective_user)

    keyboard = [
        [
            InlineKeyboardButton(
                "🧠 الذاكرة",
                callback_data="memory"
            ),
            InlineKeyboardButton(
                "🗑 مسح الذاكرة",
                callback_data="clear"
            )
        ],
        [
            InlineKeyboardButton(
                "🎨 إنشاء صورة",
                callback_data="image_help"
            )
        ]
    ]

    if update.effective_user.id == ADMIN_ID:
        keyboard.append([
            InlineKeyboardButton(
                "👑 لوحة المشرف",
                callback_data="open_admin"
            )
        ])

    await update.message.reply_text(
    "مرحباً بك،... 👋 \n\n"
    "أنا مساعدك الذكي { AI Bot 🤖 } والذي يعمل بالذكاء الإصطناعي .\n\n"
    "✨ يمكنني مساعدتك في :\n\n"
    "💬 الإجابة على الأسئلة\n"
    "💻 البرمجة وكتابة الأكواد\n"
    "📝 كتابة وتلخيص النصوص\n"
    "🌍 الترجمة\n"
    "🎨 إنشاء الصور\n"
    "📄 تحليل الصور وملفات PDF\n\n"
    "                                             ━━━━━━━━━━━━━━━\n\n"
    "💡 إكتب رسالتك في الأسفل للبدء ..."
        
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = """
الأوامر المتاحة:

/newchat
بدء محادثة جديدة ومسح الذاكرة السابقة

/image 
أذكر وصفاً للصورة لإنشائها 

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


def clear_memory(user_id):

    cursor.execute(
        "DELETE FROM conversations WHERE user_id=?",
        (user_id,)
    )

    db.commit()


def save_user(user):

    cursor.execute(
        """
        INSERT OR REPLACE INTO users
        (user_id, username, first_name)
        VALUES (?, ?, ?)
        """,
        (
            user.id,
            user.username,
            user.first_name
        )
    )

    db.commit()

# ==========================
# BUTTONS
# ==========================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    if query.data == "admin_stats":

        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM conversations")
        total_messages = cursor.fetchone()[0]

        await query.message.reply_text(
            f"📊 الإحصائيات\n\n"
            f"👥 عدد المستخدمين: {total_users}\n"
            f"🧠 عدد الرسائل المحفوظة: {total_messages}"
        )

    elif query.data == "admin_users":

        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        await query.message.reply_text(
            f"👥 عدد المستخدمين: {total_users}"
        )

    elif query.data == "admin_broadcast":

        await query.message.reply_text(
            "📢 ميزة الإذاعة قيد التطوير."
        )

    elif query.data == "clear":

        clear_memory(query.from_user.id)

        await query.message.reply_text(
            "🗑 تم حذف الذاكرة."

    elif query.data == "image_help":

        await query.message.reply_text(
            "استخدم:\n/image وصف الصورة"
        )

# ==========================
# CHAT
# ==========================

async def send_long_message(message, text):

    MAX_LENGTH = 4000

    for i in range(0, len(text), MAX_LENGTH):
        await message.reply_text(
            text[i:i + MAX_LENGTH]
        )


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        save_user(update.effective_user)

        user_id = update.effective_user.id
        user_message = update.message.text

        save_message(
            user_id,
            "user",
            user_message
        )

        messages = get_history(user_id)

        response = client.responses.create(
            model="gpt-5",
            input=messages
        )

        answer = response.output_text

        save_message(
            user_id,
            "assistant",
            answer
        )

        await send_long_message(
            update.message,
            answer
        )

    except Exception as e:

        import traceback

        print(traceback.format_exc())

        await update.message.reply_text(
            f"❌ {e}"
        )

# ==========================
# IMAGE GENERATION
# ==========================

async def analyze_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    try:

        await update.message.reply_text(
            "🖼 جاري تحليل الصورة..."
        )

        photo = update.message.photo[-1]

        file = await context.bot.get_file(
            photo.file_id
        )

        image_url = file.file_path

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "صف هذه الصورة بالتفصيل"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
            ]
        )

        answer = response.choices[0].message.content

        await update.message.reply_text(answer)

    except Exception as e:

        print("VISION ERROR:", e)

        await update.message.reply_text(
            f"❌ {e}"
        )
    
# ==========================
# ADMIN PANEL
# ==========================

ADMIN_ID = 685333833

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:

        await update.message.reply_text(
            "❌ هذا الأمر للمشرف فقط."
        )
        return

    cursor.execute(
        "SELECT COUNT(*) FROM users"
    )
    users = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM conversations"
    )
    messages = cursor.fetchone()[0]

    keyboard = [
        [
            InlineKeyboardButton(
                "📊 الإحصائيات",
                callback_data="admin_stats"
            )
        ],
        [
            InlineKeyboardButton(
                f"👥 المستخدمون ({users})",
                callback_data="admin_users"
            )
        ],
        [
            InlineKeyboardButton(
                f"📢 الإذاعة ({messages})",
                callback_data="admin_broadcast"
            )
        ]
    ]

    await update.message.reply_text(
        "👑 لوحة المشرف",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ==========================
# MY ID
# ==========================

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        f"🆔 Your ID:\n{update.effective_user.id}"
    )

# ==========================
# SMART COMMANDS
# ==========================

SMART_COMMANDS = {
    "think": """
فكر بعمق قبل الإجابة.
حلل الموضوع خطوة بخطوة.
""",

    "research": """
قم ببحث وتحليل شامل للموضوع.
اعرض التفاصيل المهمة.
""",

    "debate": """
ناقش الموضوع من عدة وجهات نظر.
اعرض الإيجابيات والسلبيات.
""",

    "translate": """
ترجم النص باحترافية.
""",

    "rewrite": """
أعد صياغة النص بشكل احترافي.
""",

    "seo": """
حسن النص لمحركات البحث SEO.
""",

    "code": """
أنت مبرمج خبير.
اكتب أكواد احترافية.
""",
}

async def smart_command(update, context):

    command = update.message.text.split()[0][1:]
    user_text = " ".join(context.args)

    if not user_text:
        await update.message.reply_text(
            f"استخدم:\n/{command} النص"
        )
        return

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": SMART_COMMANDS[command]
            },
            {
                "role": "user",
                "content": user_text
            }
        ]
    )

    await update.message.reply_text(
        response.choices[0].message.content
    )

async def agent(update, context):

    task = " ".join(context.args)

    if not task:
        await update.message.reply_text(
            "استخدم:\n/agent المهمة"
        )
        return

    await update.message.reply_text(
        "🧠 جاري تحليل المهمة..."
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """
أنت وكيل ذكاء اصطناعي مستقل.

قبل الإجابة:

1. افهم الهدف النهائي.
2. قسم المهمة إلى خطوات.
3. نفذ كل خطوة بالتفصيل.
4. راجع النتيجة.
5. قدم أفضل إجابة نهائية.

لا تعط إجابة سريعة.
فكر وخطط أولاً.
"""
            },
            {
                "role": "user",
                "content": task
            }
        ]
    )

    await update.message.reply_text(
        response.choices[0].message.content
    )

# ==========================
# PDF READER
# ==========================

async def analyze_pdf(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    try:

        await update.message.reply_text(
            "📄 جاري قراءة الملف..."
        )

        document = update.message.document

        file = await context.bot.get_file(
            document.file_id
        )

        with tempfile.NamedTemporaryFile(
            suffix=".pdf",
            delete=False
        ) as temp_file:

            pdf_path = temp_file.name

        await file.download_to_drive(pdf_path)

        text = ""

        try:

            with open(pdf_path, "rb") as pdf_file:

                reader = PdfReader(pdf_file)

                for page in reader.pages:

                    page_text = page.extract_text()

                    if page_text:
                        text += page_text + "\n"

        except Exception as pdf_error:

            print("PDF READ ERROR:", pdf_error)

        # ==========================
        # PDF يحتوي نصاً
        # ==========================

        if text.strip():

            if len(text) > 15000:
                text = text[:15000]

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "لخص الملف بشكل احترافي مع أهم النقاط."
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ]
            )

            await update.message.reply_text(
                response.choices[0].message.content
            )

            os.remove(pdf_path)
            return

        # ==========================
        # PDF عبارة عن صورة
        # ==========================

        await update.message.reply_text(
            "🖼 الملف يحتوي صوراً، جارٍ تحليل المحتوى..."
        )

        pages = convert_from_path(
            pdf_path,
            first_page=1,
            last_page=1
        )

        image_path = pdf_path + ".png"

        pages[0].save(
            image_path,
            "PNG"
        )

        with open(image_path, "rb") as img:

            image_b64 = base64.b64encode(
                img.read()
            ).decode()

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text":
                            """
استخرج النص من الصورة إن وجد.
إذا لم يوجد نص فاشرح محتوى الصفحة
ولخصها بشكل احترافي.
"""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url":
                                f"data:image/png;base64,{image_b64}"
                            }
                        }
                    ]
                }
            ]
        )

        await update.message.reply_text(
            response.choices[0].message.content
        )

        os.remove(pdf_path)
        os.remove(image_path)

    except Exception as e:

        import traceback

        print(traceback.format_exc())

        await update.message.reply_text(
            f"❌ {e}"
        )

async def generate_image(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    try:

        prompt = " ".join(context.args)

        if not prompt:
            await update.message.reply_text(
                "اكتب وصف الصورة بعد الأمر /image"
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

        import base64

        image_bytes = base64.b64decode(
            result.data[0].b64_json
        )

        image_path = "generated.png"

        with open(image_path, "wb") as f:
            f.write(image_bytes)

        with open(image_path, "rb") as photo:
            await update.message.reply_photo(photo)

        os.remove(image_path)

    except Exception as e:
        await update.message.reply_text(
            f"❌ {e}"
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

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = """
🤖 Kasper AI

الأوامر الأساسية:

/start
بدء البوت

/help
المساعدة

/newchat
بدء محادثة جديدة

/memory
عرض الذاكرة

/clear
مسح الذاكرة

/image وصف الصورة
إنشاء صورة

🧠 الأوامر الذكية:

/think سؤال
تفكير عميق

/research موضوع
بحث وتحليل شامل

/debate موضوع
مناقشة من عدة زوايا

/translate نص
ترجمة

/rewrite نص
إعادة صياغة

/seo نص
تحسين SEO

/code طلب
كتابة أكواد برمجية
"""

    await update.message.reply_text(text)

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
    CommandHandler("agent", agent)
)

for cmd in SMART_COMMANDS:
    app.add_handler(
        CommandHandler(
            cmd,
            smart_command
        )
    )
    
app.add_handler(
CallbackQueryHandler(button_handler)
)

app.add_handler(
    MessageHandler(
        filters.PHOTO,
        analyze_photo
    )
)

app.add_handler(
    MessageHandler(
        filters.Document.PDF,
        analyze_pdf
    )
)

app.add_handler(
MessageHandler(
filters.TEXT & ~filters.COMMAND,
chat
)
)

async def set_commands(app):

    commands = [
    BotCommand("start", "بدء الإستخدام"),
    BotCommand("help", "مساعدة"),

    ]

    await app.bot.set_my_commands(commands)
    
print("🚀 Kasper AI Bot Started")

app.post_init = set_commands

async def error_handler(update, context):

    print("ERROR OCCURRED")

    print(context.error)

app.add_error_handler(error_handler)

app.run_polling(
    drop_pending_updates=True
)

