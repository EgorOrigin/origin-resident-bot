import json
import logging
import os
from datetime import datetime
from pathlib import Path

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# =========================
# НАСТРОЙКИ
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))

DATA_FILE = Path("responses.json")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# =========================
# СОСТОЯНИЯ АНКЕТЫ
# =========================
(
    AGE,
    CITY,
    ACTIVITY,
    STATUS,
    EXPERIENCE,
    BEST_MONTH,
    TIME_ORIGIN,
    PROJECT_EXP,
    VALUE_TO_CLUB,
    WHY_ORIGIN,
    MAIN_REQUEST,
) = range(11)


def append_response(payload: dict) -> None:
    records = []
    if DATA_FILE.exists():
        try:
            records = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            records = []

    records.append(payload)
    DATA_FILE.write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def build_keyboard(options: list[str]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[option] for option in options],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Начать анкету", callback_data="start_form")]]
    )

    text = (
        "Привет. Это предварительный отбор в клуб Origin.\n\n"
        "Origin — закрытая группа предпринимателей и сильных фрилансеров, "
        "которые вместе создают IT-проекты и работают на общий результат.\n\n"
        "Анкета займёт 3–5 минут.\n"
        "Отвечай честно: мы отбираем не идеальных, а подходящих людей."
    )

    if update.message:
        await update.message.reply_text(text, reply_markup=keyboard)
    else:
        await update.callback_query.message.reply_text(text, reply_markup=keyboard)


async def begin_form(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    context.user_data.clear()

    await query.message.reply_text(
        "Сколько тебе лет?",
        reply_markup=ReplyKeyboardRemove(),
    )
    return AGE


async def age_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["age"] = update.message.text.strip()
    await update.message.reply_text("Из какого ты города?")
    return CITY


async def city_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["city"] = update.message.text.strip()
    await update.message.reply_text(
        "Чем ты занимаешься сейчас? Опиши коротко свой бизнес или фриланс-направление."
    )
    return ACTIVITY


async def activity_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["activity"] = update.message.text.strip()

    keyboard = build_keyboard(
        ["Предприниматель", "Фрилансер", "Совмещаю с наймом", "В найме"]
    )
    await update.message.reply_text("Ты сейчас:", reply_markup=keyboard)
    return STATUS


async def status_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    status = update.message.text.strip()
    context.user_data["status"] = status

    if status == "В найме":
        await update.message.reply_text(
            "Спасибо за анкету.\n\n"
            "Сейчас Origin ориентирован в первую очередь на предпринимателей "
            "и сильных фрилансеров с высокой степенью свободы по времени.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END

    keyboard = build_keyboard(["До 1 года", "1–2 года", "3–5 лет", "5+ лет"])
    await update.message.reply_text(
        "Сколько лет ты в бизнесе / фрилансе?",
        reply_markup=keyboard,
    )
    return EXPERIENCE


async def experience_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["experience"] = update.message.text.strip()

    keyboard = build_keyboard(
        ["До 100 000 ₽", "100 000–300 000 ₽", "300 000–1 000 000 ₽", "1 000 000 ₽+"]
    )
    await update.message.reply_text(
        "Какой у тебя был лучший месяц по чистой прибыли?",
        reply_markup=keyboard,
    )
    return BEST_MONTH


async def best_month_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["best_month"] = update.message.text.strip()

    keyboard = build_keyboard(["До 5 часов", "5–10 часов", "10–20 часов", "20+ часов"])
    await update.message.reply_text(
        "Сколько времени в неделю ты реально готов вкладывать в Origin?",
        reply_markup=keyboard,
    )
    return TIME_ORIGIN


async def time_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["time_origin"] = update.message.text.strip()

    keyboard = build_keyboard(
        ["Да, неоднократно", "Да, 1–2 раза", "Частично участвовал", "Нет"]
    )
    await update.message.reply_text(
        "Есть ли у тебя опыт запуска проектов с нуля?",
        reply_markup=keyboard,
    )
    return PROJECT_EXP


async def project_exp_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["project_exp"] = update.message.text.strip()
    await update.message.reply_text(
        "Что ты можешь дать клубу кроме своего присутствия?",
        reply_markup=ReplyKeyboardRemove(),
    )
    return VALUE_TO_CLUB


async def value_to_club_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["value_to_club"] = update.message.text.strip()
    await update.message.reply_text("Почему ты хочешь попасть в Origin?")
    return WHY_ORIGIN


async def why_origin_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["why_origin"] = update.message.text.strip()
    await update.message.reply_text(
        "С каким главным запросом ты хочешь зайти в Origin на ближайший год?"
    )
    return MAIN_REQUEST


async def main_request_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["main_request"] = update.message.text.strip()

    user = update.effective_user
    payload = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "telegram_user_id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        **context.user_data,
    }

    append_response(payload)

    admin_text = (
        "Новая анкета Origin\n\n"
        f"Имя: {user.full_name}\n"
        f"Username: @{user.username if user.username else 'нет'}\n"
        f"Telegram ID: {user.id}\n"
        f"Возраст: {payload['age']}\n"
        f"Город: {payload['city']}\n"
        f"Чем занимается: {payload['activity']}\n"
        f"Статус: {payload['status']}\n"
        f"Опыт: {payload['experience']}\n"
        f"Лучший месяц: {payload['best_month']}\n"
        f"Время в неделю: {payload['time_origin']}\n"
        f"Опыт запусков: {payload['project_exp']}\n"
        f"Что может дать клубу: {payload['value_to_club']}\n"
        f"Почему хочет в Origin: {payload['why_origin']}\n"
        f"Главный запрос: {payload['main_request']}"
    )

    try:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_text)
    except Exception as exc:
        logger.exception("Не удалось отправить анкету админу: %s", exc)

    await update.message.reply_text(
        "Спасибо. Анкета принята.\n\n"
        "Мы смотрим не только на опыт и доход, но и на зрелость, мотивацию "
        "и ценность человека для среды.\n"
        "Если твой профиль подходит Origin, мы свяжемся с тобой лично.",
        reply_markup=ReplyKeyboardRemove(),
    )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Анкета остановлена. Можешь начать заново командой /start",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


def main() -> None:
    if BOT_TOKEN == "ВСТАВЬ_СЮДА_НОВЫЙ_ТОКЕН_БОТА":
        raise ValueError("Нужно вставить реальный токен бота в BOT_TOKEN.")
    if ADMIN_CHAT_ID == 123456789:
        raise ValueError("Нужно вставить свой Telegram ID в ADMIN_CHAT_ID.")

    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(begin_form, pattern="^start_form$"),
        ],
        states={
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age_step)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, city_step)],
            ACTIVITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, activity_step)],
            STATUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, status_step)],
            EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, experience_step)],
            BEST_MONTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, best_month_step)],
            TIME_ORIGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, time_step)],
            PROJECT_EXP: [MessageHandler(filters.TEXT & ~filters.COMMAND, project_exp_step)],
            VALUE_TO_CLUB: [MessageHandler(filters.TEXT & ~filters.COMMAND, value_to_club_step)],
            WHY_ORIGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, why_origin_step)],
            MAIN_REQUEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_request_step)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(conv_handler)
    app.run_polling()


if __name__ == "__main__":
    main()
