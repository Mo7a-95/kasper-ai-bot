from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes,
)

from openai import OpenAI
import os

# التوكنات
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# تشغيل OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# أمر البداية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك 👋 أنا Kasper AI Bot")

# الرد على الرسائل
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_message = update.message.text

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "أنت مساعد ذكي وتتحدث العربية."
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ]
        )

        answer = response.choices[0].message.content

        await update.message.reply_text(answer)

    except Exception as e:
        await update.message.reply_text(f"حدث خطأ:\n{e}")

# تشغيل التطبيق
app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

# handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, reply)
)

print("Bot is running...")

app.run_polling()
