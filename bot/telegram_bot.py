from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os

TOKEN = os.getenv("TOKEN_T")
CHAT_ID = os.getenv("CHAT_ID_T")

bot = Bot(token=TOKEN)

async def start(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Бот работает ✅")

async def start_telegram_bot():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    await app.initialize()

    await app.bot.send_message(chat_id=CHAT_ID, text="Бот SIEM_API запущен ✅")
    await app.start()
    
async def notify(text: str):
    await bot.send_message(chat_id=CHAT_ID, text=text)