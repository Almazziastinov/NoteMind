

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

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

MAIN_KEYBOARD = [
    ["Просмотреть заметки", "Добавить заметку"],
    ["Редактировать заметку", "Удалить заметку"],
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение с клавиатурой."""
    reply_markup = ReplyKeyboardMarkup(MAIN_KEYBOARD, resize_keyboard=True)
    context.user_data['state'] = None
    await update.message.reply_text(
        "Добро пожаловать в бот для заметок! Выберите действие:", reply_markup=reply_markup
    )


async def view_notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает все заметки."""
    user_notes = context.user_data.get("notes", [])
    if not user_notes:
        await update.message.reply_text("У вас пока нет заметок.")
    else:
        message = "Ваши заметки:\n"
        for i, note in enumerate(user_notes):
            message += f"{i + 1}. {note}\n"
        await update.message.reply_text(message)


async def add_note_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начинает процесс добавления заметки."""
    context.user_data['state'] = 'adding_note'
    await update.message.reply_text("Пожалуйста, введите текст вашей заметки.")


async def delete_note_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начинает процесс удаления заметки."""
    context.user_data['state'] = 'deleting_note'
    await view_notes(update, context)
    await update.message.reply_text("Пожалуйста, введите номер заметки, которую хотите удалить.")


async def edit_note_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начинает процесс редактирования заметки."""
    context.user_data['state'] = 'editing_note_id'
    await view_notes(update, context)
    await update.message.reply_text("Пожалуйста, введите номер заметки, которую хотите отредактировать.")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает текстовые сообщения в зависимости от состояния."""
    state = context.user_data.get('state')

    if state == 'adding_note':
        note_text = update.message.text
        user_notes = context.user_data.get("notes", [])
        user_notes.append(note_text)
        context.user_data["notes"] = user_notes
        context.user_data['state'] = None
        await update.message.reply_text(f"Заметка добавлена: {note_text}")

    elif state == 'deleting_note':
        try:
            note_id = int(update.message.text)
            user_notes = context.user_data.get("notes", [])
            if 1 <= note_id <= len(user_notes):
                deleted_note = user_notes.pop(note_id - 1)
                await update.message.reply_text(f"Заметка удалена: {deleted_note}")
            else:
                await update.message.reply_text("Неверный ID заметки.")
        except (IndexError, ValueError):
            await update.message.reply_text("Пожалуйста, введите корректный номер заметки.")
        finally:
            context.user_data['state'] = None

    elif state == 'editing_note_id':
        try:
            note_id = int(update.message.text)
            user_notes = context.user_data.get("notes", [])
            if 1 <= note_id <= len(user_notes):
                context.user_data['state'] = 'editing_note_text'
                context.user_data['note_to_edit'] = note_id
                await update.message.reply_text("Пожалуйста, введите новый текст заметки.")
            else:
                await update.message.reply_text("Неверный ID заметки.")
                context.user_data['state'] = None
        except (IndexError, ValueError):
            await update.message.reply_text("Пожалуйста, введите корректный номер заметки.")
            context.user_data['state'] = None

    elif state == 'editing_note_text':
        note_id = context.user_data.get('note_to_edit')
        new_text = update.message.text
        user_notes = context.user_data.get("notes", [])
        user_notes[note_id - 1] = new_text
        await update.message.reply_text(f"Заметка {note_id} отредактирована.")
        context.user_data['state'] = None
        context.user_data['note_to_edit'] = None


def main() -> None:
    """Запускает бота."""
    persistence = PicklePersistence(filepath="output/notes.pickle")
    application = Application.builder().token(config.TOKEN).persistence(persistence).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Regex("^Просмотреть заметки$"), view_notes))
    application.add_handler(MessageHandler(filters.Regex("^Добавить заметку$"), add_note_start))
    application.add_handler(MessageHandler(filters.Regex("^Удалить заметку$"), delete_note_start))
    application.add_handler(MessageHandler(filters.Regex("^Редактировать заметку$"), edit_note_start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    application.run_polling()


if __name__ == "__main__":
    main()
