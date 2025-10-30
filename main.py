import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Получаем токен
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TOKEN")
if not TOKEN:
    raise SystemExit("❌ ERROR: TELEGRAM_BOT_TOKEN not set in Render environment variables")

# Создаём планировщик
scheduler = AsyncIOScheduler()
scheduler.start()

# Простая база данных пользователей
user_data = {}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.message.chat_id
    user_data[chat_id] = {"reminders": []}

    keyboard = [["💊 Добавить курс", "📅 Мои напоминания"], ["✅ Принял таблетку", "ℹ️ Помощь"]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        f"Привет, {user.first_name}! 👋\n"
        f"Я помогу тебе не забывать принимать таблетки 💊",
        reply_markup=markup
    )

# Команда /add — добавляет напоминание через 10 секунд (для теста)
async def add_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    remind_time = datetime.now() + timedelta(seconds=10)
    scheduler.add_job(send_reminder, 'date', run_date=remind_time, args=[chat_id])
    await update.message.reply_text("✅ Напоминание установлено на ближайшие 10 секунд!")

# Функция отправки напоминания
async def send_reminder(chat_id):
    from telegram import Bot
    bot = Bot(TOKEN)
    await bot.send_message(chat_id=chat_id, text="💊 Время принять таблетку!")

# Кнопка “✅ Принял таблетку”
async def mark_taken(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отлично! 💪 Я отмечу, что ты принял таблетку.")

# Помощь
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📘 Команды:\n"
        "/start — начать работу\n"
        "/add — добавить тестовое напоминание\n"
        "Кнопка '✅ Принял таблетку' — отметить приём"
    )

# Обработка текстовых кнопок
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "Добавить курс" in text:
        await add_reminder(update, context)
    elif "Принял таблетку" in text:
        await mark_taken(update, context)
    elif "Помощь" in text:
        await help_command(update, context)
    else:
        await update.message.reply_text("Не понял 🤔 Используй кнопки внизу.")

# 🔹 Главное исправление — теперь без asyncio.run()
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_reminder))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("✅ Bot started successfully")
    app.run_polling()  # <-- теперь просто синхронный вызов

if __name__ == "__main__":
    main()
    
