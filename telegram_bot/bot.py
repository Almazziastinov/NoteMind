import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    PicklePersistence,
    MessageHandler,
    filters,
)

import config
from llm.tags import get_tags_from_openai

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

MAIN_KEYBOARD = [
    ["Просмотреть заметки", "Добавить заметку"],
    ["Редактировать заметку", "Удалить заметку"],
    ["Найти по тегу"],
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение с клавиатурой и мигрирует данные."""
    # Data migration
    user_notes = context.user_data.get("notes", [])
    migrated_notes = []
    for note in user_notes:
        if isinstance(note, str):
            migrated_notes.append({"text": note, "tags": []})
        else:
            migrated_notes.append(note)
    context.user_data["notes"] = migrated_notes

    reply_markup = ReplyKeyboardMarkup(MAIN_KEYBOARD, resize_keyboard=True)
    context.user_data["state"] = None
    await update.message.reply_text(
        "Добро пожаловать в бот для заметок! Выберите действие:",
        reply_markup=reply_markup,
    )


async def view_notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает все заметки."""
    user_notes = context.user_data.get("notes", [])
    if not user_notes:
        await update.message.reply_text("У вас пока нет заметок.")
    else:
        message = "Ваши заметки:\n"
        for i, note in enumerate(user_notes):
            tags = ", ".join(note.get("tags", []))
            message += f"{i + 1}. {note['text']}\n   Tags: {tags}\n"
        await update.message.reply_text(message)


async def add_note_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начинает процесс добавления заметки."""
    context.user_data["state"] = "adding_note"
    await update.message.reply_text("Пожалуйста, введите текст вашей заметки.")


async def delete_note_start(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Начинает процесс удаления заметки."""
    context.user_data["state"] = "deleting_note"
    await view_notes(update, context)
    await update.message.reply_text(
        "Пожалуйста, введите номер заметки, которую хотите удалить."
    )


async def edit_note_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начинает процесс редактирования заметки."""
    context.user_data["state"] = "editing_note_id"
    await view_notes(update, context)
    await update.message.reply_text(
        "Пожалуйста, введите номер заметки, которую хотите отредактировать."
    )


async def find_by_tag_start(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Начинает процесс поиска по тегу."""
    context.user_data["state"] = "finding_by_tag"
    await update.message.reply_text("Пожалуйста, введите тег для поиска.")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает текстовые сообщения в зависимости от состояния."""
    state = context.user_data.get("state")

    if state == "adding_note":
        note_text = update.message.text
        await update.message.reply_text("Генерирую теги...")
        tags = await get_tags_from_openai(note_text)
        user_notes = context.user_data.get("notes", [])
        user_notes.append({"text": note_text, "tags": tags})
        context.user_data["notes"] = user_notes
        context.user_data["state"] = None
        await update.message.reply_text(
            f"Заметка добавлена: {note_text}\nТеги: {', '.join(tags)}"
        )

    elif state == "deleting_note":
        try:
            note_id = int(update.message.text)
            user_notes = context.user_data.get("notes", [])
            if 1 <= note_id <= len(user_notes):
                deleted_note = user_notes.pop(note_id - 1)
                await update.message.reply_text(
                    f"Заметка удалена: {deleted_note['text']}"
                )
            else:
                await update.message.reply_text("Неверный ID заметки.")
        except (IndexError, ValueError):
            await update.message.reply_text(
                "Пожалуйста, введите корректный номер заметки."
            )
        finally:
            context.user_data["state"] = None

    elif state == "editing_note_id":
        try:
            note_id = int(update.message.text)
            user_notes = context.user_data.get("notes", [])
            if 1 <= note_id <= len(user_notes):
                context.user_data["state"] = "editing_note_text"
                context.user_data["note_to_edit"] = note_id
                await update.message.reply_text(
                    "Пожалуйста, введите новый текст заметки."
                )
            else:
                await update.message.reply_text("Неверный ID заметки.")
                context.user_data["state"] = None
        except (IndexError, ValueError):
            await update.message.reply_text(
                "Пожалуйста, введите корректный номер заметки."
            )
            context.user_data["state"] = None

    elif state == "editing_note_text":
        note_id = context.user_data.get("note_to_edit")
        new_text = update.message.text
        user_notes = context.user_data.get("notes", [])
        await update.message.reply_text("Обновляю теги...")
        tags = await get_tags_from_openai(new_text)
        user_notes[note_id - 1] = {"text": new_text, "tags": tags}
        await update.message.reply_text(
            f"Заметка {note_id} отредактирована.\nНовые теги: {', '.join(tags)}"
        )
        context.user_data["state"] = None
        context.user_data["note_to_edit"] = None

    elif state == "finding_by_tag":
        tag_to_find = update.message.text.lower()
        user_notes = context.user_data.get("notes", [])
        found_notes = [
            note
            for note in user_notes
            if tag_to_find in [tag.lower() for tag in note.get("tags", [])]
        ]

        if not found_notes:
            await update.message.reply_text(f"Заметок с тегом '{tag_to_find}' не найдено.")
        else:
            message = f"Заметки с тегом '{tag_to_find}':\n"
            for i, note in enumerate(found_notes):
                message += f"{i + 1}. {note['text']}\n"
            await update.message.reply_text(message)
        context.user_data["state"] = None

def main() -> None:
    """Запускает бота."""
    persistence = PicklePersistence(filepath="output/notes.pickle")
    application = (
        Application.builder().token(config.TOKEN).persistence(persistence).build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(filters.Regex("^Просмотреть заметки$"), view_notes)
    )
    application.add_handler(
        MessageHandler(filters.Regex("^Добавить заметку$"), add_note_start)
    )
    application.add_handler(
        MessageHandler(filters.Regex("^Удалить заметку$"), delete_note_start)
    )
    application.add_handler(
        MessageHandler(filters.Regex("^Редактировать заметку$"), edit_note_start)
    )
    application.add_handler(
        MessageHandler(filters.Regex("^Найти по тегу$"), find_by_tag_start)
    )
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    application.run_polling()

if __name__ == "__main__":
    main()