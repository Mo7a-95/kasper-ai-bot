from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes
)

from openai import OpenAI
import os

# المتغيرات من Railway
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# تشغيل OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك 👋 أنا Kasper AI Bot")

# الرد على الرسائل
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "أنت مساعد ذكي ومفيد."
            },
            {
                "role": "user",
                "content": user_message
            }
        ]
    )

    answer = response.choices[0].message.content

    await update.message.reply_text(answer)

# تشغيل البوت
app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

# الأوامر
app.add_handler(CommandHandler("start", start))

# الرسائل
app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, reply)
)

print("Bot is running...")

app.run_polling()
