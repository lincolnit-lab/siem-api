import os
import re
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("TOKEN_T")
CHAT_ID = os.getenv("CHAT_ID_T")

# Главный объект приложения бота, единый для всей системы
tg_application = None

async def start(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Бот SIEM_API работает и слушает кнопки ✅")

async def handle_unban_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Этот обработчик ТЕПЕРЬ ОФИЦИАЛЬНО поймает клик"""
    query = update.callback_query
    await query.answer()

    ip_address = query.data.replace("unban_", "")
    print(f"[!] Бот перехватил клик! Отправляем запрос на анбан IP: {ip_address}")
    
    await query.edit_message_text(text=f"⏳ Запрос на разблокировку {ip_address} отправлен в IPS...")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"http://api:8000/api/bans/unban/{ip_address}")
            
            if response.status_code == 200:
                await query.edit_message_text(text=f"✅ **IPS SUCCESS**: IP `{ip_address}` успешно разблокирован на хосте и в БД!")
            else:
                error_detail = response.json().get("detail", "Неизвестная ошибка API")
                await query.edit_message_text(text=f"❌ **IPS ERROR**: {error_detail}")
    except Exception as e:
        await query.edit_message_text(text=f"❌ **IPS CRITICAL ERROR**: Нет связи с API: {str(e)}")

async def start_telegram_bot():
    """Инициализация бота в единой сессии"""
    global tg_application
    print("[*] Инициализация единой сессии Telegram-бота...")
    
    tg_application = ApplicationBuilder().token(TOKEN).build()
    
    tg_application.add_handler(CommandHandler("start", start))
    tg_application.add_handler(CallbackQueryHandler(handle_unban_callback, pattern=r"^unban_"))

    await tg_application.initialize()
    await tg_application.start()
    await tg_application.updater.start_polling()
    
    print("[+] Поток Long Polling для кнопок успешно запущен!")
    await tg_application.bot.send_message(chat_id=CHAT_ID, text="Бот SIEM_API запущен и готов разбанивать ✅")

async def notify(text: str):
    """Отправка сообщений СТРОГО через рабочее приложение, чтобы не ломать сессию кликов"""
    global tg_application
    
    # Если бот еще не успел стартовать, защищаем код от падения
    if tg_application is None:
        print("[-] Ошибка: Попытка отправить уведомление до инициализации бота")
        return

    ip_match = re.search(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", text)
    reply_markup = None
    
    if ip_match:
        ip = ip_match.group(0)
        keyboard = [[InlineKeyboardButton("🟢 Разблокировать IP", callback_data=f"unban_{ip}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        # Отправляем сообщение через tg_application.bot, сохраняя дескриптор кнопок активным!
        await tg_application.bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown", reply_markup=reply_markup)
    except Exception as e:
        print(f"[-] Ошибка отправки алерта в Telegram: {e}")