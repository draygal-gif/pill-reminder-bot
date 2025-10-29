import logging
import os
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    CallbackQueryHandler, ContextTypes
)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

# Хранилище расписаний для каждого пользователяimport os
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

# Запуск приложения
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_reminder))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("✅ Bot started successfully")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
user_schedules = {}

scheduler = AsyncIOScheduler()


# ✅ Напоминание
async def remind(user_id, text, application):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Принял", callback_data="done")]
    ])
    await application.bot.send_message(
        chat_id=user_id,
        text=f"🔔 Напоминание: {text}",
        reply_markup=keyboard
    )


# ✅ Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    keyboard = [
        [InlineKeyboardButton("➕ Добавить курс", callback_data="add_course")],
        [InlineKeyboardButton("📅 Мои курсы", callback_data="my_courses")]
    ]

    await update.message.reply_text(
        "Привет! Я помогу тебе не забывать о таблетках 💊\n"
        "Добавь курс и я поставлю напоминания!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    if user_id not in user_schedules:
        user_schedules[user_id] = []


# ✅ Обработка нажатий кнопок
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    await query.answer()

    if query.data == "add_course":
        context.user_data["state"] = "waiting_course"
        await query.edit_message_text(
            "Введи название курса и схему так:\n\n"
            "Название, кол-во дней, кол-во раз в день, время первого приёма (ЧЧ:ММ)\n"
            "Пример:\n"
            "Антибиотик, 5, 3, 09:00"
        )

    if query.data == "my_courses":
        if not user_schedules.get(user_id):
            await query.edit_message_text("Пока нет активных курсов 😌")
        else:
            text = "📅 Твои активные курсы:\n\n"
            for c in user_schedules[user_id]:
                text += f"• {c['name']} — {c['days']} дней × {c['times']} раз в день\n"
            await query.edit_message_text(text)

    if query.data == "done":
        await query.edit_message_text("✅ Отлично! Продолжай по расписанию!")


# ✅ Обработка текста после кнопки
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("state") == "waiting_course":
        try:
            name, days, times, start_time = update.message.text.split(",")
            name = name.strip()
            days = int(days.strip())
            times = int(times.strip())
            start_time = start_time.strip()

            user_id = update.effective_user.id
            start_dt = datetime.strptime(start_time, "%H:%M").time()

            course = {
                "name": name,
                "days": days,
                "times": times,
                "start": start_dt
            }

            user_schedules[user_id].append(course)

            # Планируем напоминания
            for d in range(days):
                for t in range(times):
                    remind_time = (
                        datetime.now() +
                        timedelta(days=d)
                    ).replace(
                        hour=start_dt.hour + t * (12 // max(times, 1)),
                        minute=start_dt.minute,
                        second=0
                    )
                    scheduler.add_job(
                        remind,
                        trigger="date",
                        run_date=remind_time,
                        args=[user_id, name, context.application]
                    )

            context.user_data["state"] = None

            await update.message.reply_text("✅ Курс добавлен!")

        except Exception:
            await update.message.reply_text("Ошибка ввода ❌ Попробуй ещё раз")


# ✅ MAIN
async def main():
    if not TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN environment variable is not set!")
        print("Please set your Telegram bot token in the Secrets tab.")
        return

    scheduler.start()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("menu", start))
    app.add_handler(CommandHandler("courses", button))
    app.add_handler(CommandHandler("done", button))
    app.add_handler(CommandHandler("cancel", start))
    app.add_handler(CommandHandler("reset", start))
    app.add_handler(CommandHandler("stop", start))
    app.add_handler(CommandHandler("add", button))
    app.add_handler(CommandHandler("my", button))
    app.add_handler(CommandHandler("time", button))
    app.add_handler(CommandHandler("course", button))
    app.add_handler(CommandHandler("pills", button))
    app.add_handler(CommandHandler("med", button))
    app.add_handler(CommandHandler("pill", button))
    app.add_handler(CommandHandler("tablet", button))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(CommandHandler("schedule", start))
    app.add_handler(CommandHandler("next", start))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("confirm", button))
    app.add_handler(CommandHandler("note", button))

    app.add_handler(CommandHandler("echo", start))
    app.add_handler(CommandHandler("list", button))
    app.add_handler(CommandHandler("info", start))
    app.add_handler(CommandHandler("use", start))
    app.add_handler(CommandHandler("status", start))

    # Обработка обычного текста
    app.add_handler(CommandHandler("text", handle_text))
    app.add_handler(CommandHandler("message", handle_text))
    app.add_handler(CommandHandler("msg", handle_text))
    app.add_handler(CommandHandler("send", handle_text))
    app.add_handler(CommandHandler("input", handle_text))
    app.add_handler(CommandHandler("write", handle_text))

    # Главный обработчик
    app.add_handler(CommandHandler("start", start))

    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("menu", start))
    app.add_handler(CommandHandler("courses", button))

    app.add_handler(CommandHandler("med", start))

    app.add_handler(CommandHandler("pill", start))


    app.add_handler(CommandHandler("course", start))


    app.add_handler(CommandHandler("list", start))


    app.add_handler(CommandHandler("my", start))


    app.add_handler(CommandHandler("schedule", start))


    app.add_handler(CommandHandler("calendar", start))

    app.add_handler(CommandHandler("reset", start))

    # текст как fallback
    from telegram.ext import MessageHandler, filters
    app.add_handler(MessageHandler(filters.TEXT, handle_text))

    print("✅ Бот запущен!")

    async with app:
        await app.start()
        await app.updater.start_polling()

        try:
            import asyncio
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            print("\n👋 Stopping bot...")
        finally:
            await app.updater.stop()
            await app.stop()


if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
        
