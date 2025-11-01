
import logging
from openai import AsyncOpenAI
from llm import llm_config

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=llm_config.OPENAI_API_KEY)

async def transcribe_audio(file_path: str) -> str | None:
    """
    Transcribes an audio file using OpenAI's Whisper model.

    Args:
        file_path: The path to the audio file.

    Returns:
        The transcribed text, or None if an error occurs.
    """
    try:
        with open(file_path, "rb") as audio_file:
            transcription = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        return transcription.text
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        return None
