"""Telegram-бот: раз в N часов собирает новости рынка покемонов,
присылает владельцу черновик поста на апрув, после апрува публикует в канал.

Кнопки под черновиком:
  ✅ Опубликовать   🔁 Перегенерировать   ✖️ Пропустить
"""

import os
import uuid

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputFile, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

import config
import content
import images
import news
import state


def _keyboard(draft_id):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Опубликовать", callback_data=f"pub:{draft_id}"),
        InlineKeyboardButton("🔁 Перегенерировать", callback_data=f"regen:{draft_id}"),
        InlineKeyboardButton("✖️ Пропустить", callback_data=f"skip:{draft_id}"),
    ]])


def _drafts(context):
    return context.application.bot_data.setdefault("drafts", {})


def _photo_arg(image):
    """image — путь к файлу или URL. Возвращает то, что примет send_photo."""
    if image and os.path.exists(image):
        return InputFile(open(image, "rb"))
    return image  # URL строкой


async def process_news(context: ContextTypes.DEFAULT_TYPE, notify_empty=False):
    """Основной цикл: собрать новости → сгенерировать черновик → прислать на апрув."""
    owner = config.TG_OWNER_CHAT_ID
    print("🔄 Проверка новостей рынка покемонов...")

    items = news.fetch_items()
    seen = state.get_seen_ids()
    new_items = [it for it in items if it["id"] not in seen]

    if not new_items:
        print("ℹ️ Новых новостей нет.")
        if notify_empty:
            await context.bot.send_message(owner, "ℹ️ Новых новостей рынка пока нет.")
        return

    # Помечаем как показанные, чтобы не предлагать те же новости повторно.
    state.mark_seen([it["id"] for it in new_items])

    try:
        data = content.build_digest(new_items)
    except Exception as e:  # noqa: BLE001
        print(f"⚠️ Ошибка генерации: {e}")
        await context.bot.send_message(owner, f"⚠️ Ошибка генерации сводки: {e}")
        return

    if not data.get("has_news") or not data.get("post", "").strip():
        print("ℹ️ Модель не нашла значимых рыночных новостей.")
        if notify_empty:
            await context.bot.send_message(owner, "ℹ️ Значимых рыночных новостей не нашлось.")
        return

    fallback_img = next((it["image"] for it in new_items if it.get("image")), None)
    image = images.get_image(data.get("image_prompt", ""), fallback_img)

    draft_id = uuid.uuid4().hex[:12]
    _drafts(context)[draft_id] = {
        "post": data["post"].strip(),
        "summary": data.get("summary", "").strip(),
        "image": image,
        "item_ids": [it["id"] for it in new_items],
        "items": new_items,
    }

    preview = (
        "🔔 Черновик поста для канала\n\n"
        f"📋 СВОДКА:\n{data.get('summary', '').strip()}\n\n"
        "— — — — —\n"
        f"📝 ПОСТ:\n{data['post'].strip()}"
    )
    await context.bot.send_message(owner, preview, reply_markup=_keyboard(draft_id))
    if image:
        try:
            await context.bot.send_photo(owner, _photo_arg(image), caption="🖼 Картинка к посту")
        except Exception as e:  # noqa: BLE001
            print(f"⚠️ Не удалось показать превью картинки: {e}")


async def _publish(context, draft):
    channel = config.TG_CHANNEL_ID
    post = draft["post"]
    image = draft.get("image")

    if image and len(post) <= 1024:
        await context.bot.send_photo(channel, _photo_arg(image), caption=post)
    elif image:
        await context.bot.send_photo(channel, _photo_arg(image))
        await context.bot.send_message(channel, post)
    else:
        await context.bot.send_message(channel, post)

    state.mark_posted(draft["item_ids"])


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, _, draft_id = query.data.partition(":")
    draft = _drafts(context).get(draft_id)

    if not draft:
        await query.edit_message_text("⚠️ Черновик устарел (бот перезапускался). Дождись следующей проверки или вызови /check.")
        return

    if action == "pub":
        try:
            await _publish(context, draft)
            await query.edit_message_text(query.message.text + "\n\n✅ Опубликовано в канал.")
        except Exception as e:  # noqa: BLE001
            await query.edit_message_text(query.message.text + f"\n\n⚠️ Ошибка публикации: {e}")
        _drafts(context).pop(draft_id, None)

    elif action == "skip":
        await query.edit_message_text(query.message.text + "\n\n✖️ Пропущено.")
        _drafts(context).pop(draft_id, None)

    elif action == "regen":
        await query.edit_message_text(query.message.text + "\n\n🔁 Перегенерирую...")
        try:
            data = content.build_digest(
                draft["items"],
                variation_hint="Перепиши пост иначе: другой заход, другая подача, тот же смысл.",
            )
        except Exception as e:  # noqa: BLE001
            await context.bot.send_message(config.TG_OWNER_CHAT_ID, f"⚠️ Ошибка перегенерации: {e}")
            return

        draft["post"] = data.get("post", draft["post"]).strip()
        draft["summary"] = data.get("summary", draft["summary"]).strip()

        preview = (
            "🔔 Черновик поста (перегенерирован)\n\n"
            f"📋 СВОДКА:\n{draft['summary']}\n\n"
            "— — — — —\n"
            f"📝 ПОСТ:\n{draft['post']}"
        )
        await context.bot.send_message(
            config.TG_OWNER_CHAT_ID, preview, reply_markup=_keyboard(draft_id)
        )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🃏 Агент новостей рынка покемонов запущен.\n"
        f"Твой chat_id: {update.effective_chat.id}\n\n"
        "Раз в {h} ч. я присылаю черновик поста на апрув.\n"
        "Команды: /check — проверить прямо сейчас.".format(h=config.CHECK_INTERVAL_HOURS)
    )


async def cmd_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 Проверяю новости...")
    await process_news(context, notify_empty=True)


async def _scheduled_job(context: ContextTypes.DEFAULT_TYPE):
    await process_news(context, notify_empty=False)


def build_app():
    missing = config.check_required()
    if missing:
        raise SystemExit("❌ Не заданы переменные окружения: " + ", ".join(missing))

    app = Application.builder().token(config.TG_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("check", cmd_check))
    app.add_handler(CallbackQueryHandler(on_button))

    interval = config.CHECK_INTERVAL_HOURS * 3600
    app.job_queue.run_repeating(_scheduled_job, interval=interval, first=15)
    return app
