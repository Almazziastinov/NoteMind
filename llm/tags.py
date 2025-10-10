import json
import logging
from openai import AsyncOpenAI
from llm import llm_config

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=llm_config.OPENAI_API_KEY)

async def get_tags_from_openai(note_text: str) -> list[str]:
    """Gets tags for a note from OpenAI."""
    try:
        response = await client.chat.completions.create(
            model=llm_config.MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that suggests tags for notes. Respond with a JSON list of strings.",
                },
                {"role": "user", "content": f"Suggest tags for this note: {note_text}"},
            ],
        )
        tags_json = response.choices[0].message.content
        tags = json.loads(tags_json)
        return tags
    except Exception as e:
        logger.error(f"Error getting tags from OpenAI: {e}")
        return []