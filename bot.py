import logging
import asyncio
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))
PORT = int(os.getenv("PORT", "10000"))
RENDER_EXTERNAL_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")

STEP_AGE = "age"
STEP_CITY = "city"
STEP_ACTIVITY = "activity"
STEP_STATUS = "status"
STEP_EXPERIENCE = "experience"
STEP_BEST_MONTH = "best_month"
STEP_TIME = "time_origin"
STEP_PROJECT_EXP = "project_exp"
STEP_VALUE_MULTI = "value_multi"
STEP_VALUE_OTHER = "value_other"
STEP_REQUEST = "main_request"
STEP_REQUEST_OTHER = "main_request_other"

STATUS_OPTIONS = {
    "entrepreneur": "Предприниматель",
    "freelancer": "Фрилансер",
    "hybrid": "Совмещаю с наймом",
    "employment": "В найме",
}

EXPERIENCE_OPTIONS = {
    "lt1": "До 1 года",
    "1_2": "1–2 года",
    "3_5": "3–5 лет",
    "5p": "5+ лет",
}

BEST_MONTH_OPTIONS = {
    "lt100": "До 100 000 ₽",
    "100_300": "100 000–300 000 ₽",
    "300_1000": "300 000–1 000 000 ₽",
    "1000p": "1 000 000 ₽+",
}

TIME_OPTIONS = {
    "lt5": "До 5 часов",
    "5_10": "5–10 часов",
    "10_20": "10–20 часов",
    "20p": "20+ часов",
}

PROJECT_EXP_OPTIONS = {
    "many": "Да, неоднократно",
    "few": "Да, 1–2 раза",
    "partial": "Частично участвовал",
    "none": "Нет",
}

VALUE_OPTIONS = {
    "sales": "Продажи",
    "marketing": "Маркетинг",
    "ads": "Реклама",
    "reels": "Съёмка рилсов / контент",
    "design": "Дизайн",
    "dev": "Разработка",
    "mvp": "Запуск MVP",
    "prod": "Продюсирование",
    "legal": "Юридические вопросы",
    "finance": "Финансы / инвестиции",
    "network": "Сильный нетворк",
}

REQUEST_OPTIONS = {
    "grow": "Хочу кратно вырасти за год",
    "circle": "Хочу найти сильное окружение",
    "launch": "Хочу запускать новые проекты в команде",
    "focus": "Хочу усилить дисциплину и фокус",
    "income": "Хочу выйти на новый уровень дохода",
    "env": "Хочу войти в сильную среду предпринимателей",
}


def make_single_keyboard(prefix: str, options: dict[str, str]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(label, callback_data=f"{prefix}:{code}")]
        for code, label in options.items()
    ]
    return InlineKeyboardMarkup(rows)


def make_multi_value_keyboard(selected: list[str]) -> InlineKeyboardMarkup:
    rows = []
    for code, label in VALUE_OPTIONS.items():
        text = f"✅ {label}" if code in selected else label
        rows.append([InlineKeyboardButton(text, callback_data=f"valtoggle:{code}")])

    rows.append([InlineKeyboardButton("Другое", callback_data="valother")])
    rows.append([InlineKeyboardButton("Готово", callback_data="valdone")])
    return InlineKeyboardMarkup(rows)


async def send_intro(target, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "Привет. Это предварительный отбор в клуб Origin.\n\n"
        "Origin — закрытая группа предпринимателей и сильных фрилансеров, "
        "которые вместе создают IT-проекты и работают на общий результат.\n\n"
        "Анкета займёт 3–5 минут.\n"
        "Отвечай честно: мы отбираем не идеальных, а подходящих людей."
    )
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Начать анкету", callback_data="start_form")]]
    )
    await target.reply_text(text, reply_markup=keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.clear()
    await send_intro(update.message, context)


async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "start_form":
        context.user_data.clear()
        context.user_data["step"] = STEP_AGE
        await query.message.reply_text("Сколько тебе лет?")
        return

    if data.startswith("status:"):
        code = data.split(":", 1)[1]
        context.user_data["status"] = STATUS_OPTIONS[code]

        if code == "employment":
            context.user_data.clear()
            await query.message.reply_text(
                "Спасибо за анкету.\n\n"
                "Сейчас Origin ориентирован в первую очередь на предпринимателей "
                "и сильных фрилансеров с высокой степенью свободы по времени."
            )
            return

        context.user_data["step"] = STEP_EXPERIENCE
        await query.message.reply_text(
            "Сколько лет ты в бизнесе / фрилансе?",
            reply_markup=make_single_keyboard("exp", EXPERIENCE_OPTIONS),
        )
        return

    if data.startswith("exp:"):
        code = data.split(":", 1)[1]
        context.user_data["experience"] = EXPERIENCE_OPTIONS[code]
        context.user_data["step"] = STEP_BEST_MONTH
        await query.message.reply_text(
            "Какой у тебя был лучший месяц по чистой прибыли?",
            reply_markup=make_single_keyboard("best", BEST_MONTH_OPTIONS),
        )
        return

    if data.startswith("best:"):
        code = data.split(":", 1)[1]
        context.user_data["best_month"] = BEST_MONTH_OPTIONS[code]
        context.user_data["step"] = STEP_TIME
        await query.message.reply_text(
            "Сколько времени в неделю ты реально готов вкладывать в Origin?",
            reply_markup=make_single_keyboard("time", TIME_OPTIONS),
        )
        return

    if data.startswith("time:"):
        code = data.split(":", 1)[1]
        context.user_data["time_origin"] = TIME_OPTIONS[code]
        context.user_data["step"] = STEP_PROJECT_EXP
        await query.message.reply_text(
            "Есть ли у тебя опыт запуска проектов с нуля?",
            reply_markup=make_single_keyboard("proj", PROJECT_EXP_OPTIONS),
        )
        return

    if data.startswith("proj:"):
        code = data.split(":", 1)[1]
        context.user_data["project_exp"] = PROJECT_EXP_OPTIONS[code]
        context.user_data["step"] = STEP_VALUE_MULTI
        context.user_data["value_to_club"] = []
        await query.message.reply_text(
            "Что ты можешь дать клубу кроме своего присутствия?\n\n"
            "Можно выбрать несколько вариантов. Когда закончишь — нажми «Готово».",
            reply_markup=make_multi_value_keyboard(context.user_data["value_to_club"]),
        )
        return

    if data.startswith("valtoggle:"):
        code = data.split(":", 1)[1]
        selected = context.user_data.setdefault("value_to_club", [])
        if code in selected:
            selected.remove(code)
        else:
            selected.append(code)

        await query.message.edit_reply_markup(
            reply_markup=make_multi_value_keyboard(selected)
        )
        return

    if data == "valother":
        context.user_data["step"] = STEP_VALUE_OTHER
        await query.message.reply_text(
            "Напиши одним сообщением, что ещё ты можешь дать клубу."
        )
        return

    if data == "valdone":
        selected = context.user_data.get("value_to_club", [])
        if not selected:
            await query.answer("Выбери хотя бы один вариант.", show_alert=True)
            return

        context.user_data["step"] = STEP_REQUEST
        await query.message.reply_text(
            "С каким главным запросом ты хочешь зайти в клуб Origin?",
            reply_markup=make_single_keyboard("req", REQUEST_OPTIONS)
        )
        return

    if data.startswith("req:"):
        code = data.split(":", 1)[1]
        context.user_data["main_request"] = REQUEST_OPTIONS[code]
        await finish_application(update, context)
        return


async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    step = context.user_data.get("step")
    text = update.message.text.strip()

    if not step:
        await update.message.reply_text("Нажми /start, чтобы начать анкету.")
        return

    if step == STEP_AGE:
        context.user_data["age"] = text
        context.user_data["step"] = STEP_CITY
        await update.message.reply_text("Из какого ты города?")
        return

    if step == STEP_CITY:
        context.user_data["city"] = text
        context.user_data["step"] = STEP_ACTIVITY
        await update.message.reply_text(
            "Чем ты занимаешься сейчас? "
            "Опиши коротко свой бизнес или фриланс-направление."
        )
        return

    if step == STEP_ACTIVITY:
        context.user_data["activity"] = text
        context.user_data["step"] = STEP_STATUS
        await update.message.reply_text(
            "Ты сейчас:",
            reply_markup=make_single_keyboard("status", STATUS_OPTIONS),
        )
        return

    if step == STEP_VALUE_OTHER:
        other_values = context.user_data.setdefault("value_other_texts", [])
        other_values.append(text)
        context.user_data["step"] = STEP_VALUE_MULTI
        await update.message.reply_text(
            "Добавил. Можешь выбрать ещё варианты или нажать «Готово».",
            reply_markup=make_multi_value_keyboard(
                context.user_data.get("value_to_club", [])
            ),
        )
        return

    if step == STEP_REQUEST:
        await update.message.reply_text(
            "Выбери один из вариантов кнопками ниже."
        )
        return

    if step == STEP_PROJECT_EXP:
        await update.message.reply_text(
            "Выбери один из вариантов кнопками ниже."
        )
        return

    if step == STEP_BEST_MONTH:
        await update.message.reply_text(
            "Выбери один из вариантов кнопками ниже."
        )
        return

    if step == STEP_TIME:
        await update.message.reply_text(
            "Выбери один из вариантов кнопками ниже."
        )
        return

    if step == STEP_EXPERIENCE:
        await update.message.reply_text(
            "Выбери один из вариантов кнопками ниже."
        )
        return

    if step == STEP_STATUS:
        await update.message.reply_text(
            "Выбери один из вариантов кнопками ниже."
        )
        return

    await update.message.reply_text("Нажми /start, чтобы начать заново.")


async def finish_application(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user

    selected_codes = context.user_data.get("value_to_club", [])
    selected_values = [VALUE_OPTIONS[code] for code in selected_codes]

    other_values = context.user_data.get("value_other_texts", [])
    if other_values:
        selected_values.extend([f"Другое: {item}" for item in other_values])

    admin_text = (
        "Новая анкета Origin\n\n"
        f"Имя: {user.full_name}\n"
        f"Username: @{user.username if user.username else 'нет'}\n"
        f"Telegram ID: {user.id}\n"
        f"Возраст: {context.user_data.get('age', '')}\n"
        f"Город: {context.user_data.get('city', '')}\n"
        f"Чем занимается: {context.user_data.get('activity', '')}\n"
        f"Статус: {context.user_data.get('status', '')}\n"
        f"Опыт: {context.user_data.get('experience', '')}\n"
        f"Лучший месяц: {context.user_data.get('best_month', '')}\n"
        f"Время в неделю: {context.user_data.get('time_origin', '')}\n"
        f"Опыт запусков: {context.user_data.get('project_exp', '')}\n"
        f"Что может дать клубу: {', '.join(selected_values)}\n"
        f"Главный запрос: {context.user_data.get('main_request', '')}"
    )

    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_text)

    await update.effective_chat.send_message(
        "Спасибо. Анкета принята.\n\n"
        "Мы смотрим не только на опыт и доход, но и на зрелость, мотивацию "
        "и ценность человека для среды.\n"
        "Если твой профиль подходит Origin, мы свяжемся с тобой лично."
    )

    context.user_data.clear()


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не задан")
    if not ADMIN_CHAT_ID:
        raise RuntimeError("ADMIN_CHAT_ID не задан")
    if not RENDER_EXTERNAL_HOSTNAME:
        raise RuntimeError("RENDER_EXTERNAL_HOSTNAME не задан")

    webhook_path = BOT_TOKEN
    webhook_url = f"https://{RENDER_EXTERNAL_HOSTNAME}/{webhook_path}"

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_router))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path=webhook_path,
    webhook_url=webhook_url,
    drop_pending_updates=True,
    close_loop=False,
)


if __name__ == "__main__":
    main()
def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не задан")
    if not ADMIN_CHAT_ID:
        raise RuntimeError("ADMIN_CHAT_ID не задан")
    if not RENDER_EXTERNAL_HOSTNAME:
        raise RuntimeError("RENDER_EXTERNAL_HOSTNAME не задан")

    webhook_path = BOT_TOKEN
    webhook_url = f"https://{RENDER_EXTERNAL_HOSTNAME}/{webhook_path}"

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_router))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=webhook_path,
        webhook_url=webhook_url,
        drop_pending_updates=True,
        close_loop=False,
    )


if __name__ == "__main__":
    main()
