import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    PicklePersistence,
    MessageHandler,
    filters,
)

from telegram_bot import config
from llm.agent.agent import run_agent_async

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message and migrates data."""
    # Data migration
    user_notes = context.user_data.get("notes", [])
    migrated_notes = []
    for note in user_notes:
        if isinstance(note, str):
            migrated_notes.append({"text": note, "tags": []})
        else:
            migrated_notes.append(note)
    context.user_data["notes"] = migrated_notes

    await update.message.reply_text(
        "Добро пожаловать в бот для заметок! Просто напишите мне, что вы хотите сделать."
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles text messages by passing them to the agent."""
    user_input = update.message.text
    user_notes = context.user_data.get("notes", [])

    await update.message.reply_text("Думаю...")

    result = await run_agent_async(user_input, user_notes)

    final_response = result["messages"][-1].content
    updated_notes = result["user_notes"]

    context.user_data["notes"] = updated_notes
    await update.message.reply_text(final_response)

def main() -> None:
    """Runs the bot."""
    persistence = PicklePersistence(filepath="output/notes.pickle")
    application = (
        Application.builder()
        .token(config.TOKEN)
        .persistence(persistence)
        .connect_timeout(30)
        .read_timeout(30)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    application.run_polling()

if __name__ == "__main__":
    main()