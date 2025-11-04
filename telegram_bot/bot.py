

import sys
import os
import uuid
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from llm.agent.agent import run_agent_async
from llm.transcription import transcribe_audio
from telegram_bot import db

# Read README file for /start command
with open("README.md", "r", encoding="utf-8") as f:
    README_TEXT = f.read()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message and creates a user in the database."""
    user_id = update.message.from_user.id
    db.get_or_create_user(user_id)
    await update.message.reply_text(README_TEXT)

async def process_input(user_input: str, user_id: int, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes user input (text or transcribed audio) by running the agent."""
    user_db_id = db.get_or_create_user(user_id)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    result = await run_agent_async(user_input, user_db_id)

    # Handle deferred actions returned by the agent
    if deferred_action := result.get("deferred_action"):
        if deferred_action["action"] == "send_report":
            admin_id = os.getenv("ADMIN_TELEGRAM_ID")
            if admin_id:
                report_text = deferred_action["text"]
                full_report = f"Новый репорт от пользователя {user_id}:\n\n---\n\n{report_text}"
                await context.bot.send_message(chat_id=admin_id, text=full_report)
            else:
                logger.warning("ADMIN_TELEGRAM_ID is not set. Cannot send report.")

    final_response = result["messages"][-1].content
    await update.message.reply_text(final_response)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles text messages by passing them to the agent."""
    await process_input(update.message.text, update.message.from_user.id, update, context)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles voice messages by transcribing them and passing the text to the agent."""
    user_id = update.message.from_user.id
    voice = update.message.voice
    
    # Create a unique filename
    file_name = f"{uuid.uuid4()}.oga"
    file_path = os.path.join("output", file_name)
    os.makedirs("output", exist_ok=True)

    try:
        # Download the voice message
        voice_file = await voice.get_file()
        await voice_file.download_to_drive(file_path)
        
        await update.message.reply_text("Расшифровываю голосовое...")

        # Transcribe the audio
        transcribed_text = await transcribe_audio(file_path)

        if transcribed_text:
            # Process the transcribed text
            await process_input(transcribed_text, user_id, update, context)
        else:
            await update.message.reply_text("Не удалось расшифровать голосовое сообщение. Попробуйте еще раз.")

    except Exception as e:
        logger.error(f"Error handling voice message: {e}")
        await update.message.reply_text("Произошла ошибка при обработке вашего голосового сообщения.")
    finally:
        # Clean up the downloaded file
        if os.path.exists(file_path):
            os.remove(file_path)

def main() -> None:
    """Runs the bot."""
    db.init_db()
    
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        logger.error("TELEGRAM_TOKEN environment variable not set!")
        return

    application = (
        Application.builder()
        .token(token)
        .connect_timeout(30)
        .read_timeout(30)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))

    bot_mode = os.getenv("BOT_MODE", "POLLING")
    if bot_mode == "WEBHOOK":
        webhook_url = os.getenv("WEBHOOK_URL")
        port = int(os.getenv("PORT", "8080"))
        if not webhook_url:
            logger.error("WEBHOOK_URL environment variable not set for WEBHOOK mode!")
            return
        
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=token,
            webhook_url=f"{webhook_url}/{token}"
        )
    else:
        application.run_polling()

if __name__ == "__main__":
    main()
