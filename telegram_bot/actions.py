import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from llm.tags import get_tags_from_openai

async def view_notes(user_notes: list) -> str:
    """Shows all notes."""
    if not user_notes:
        return "У вас пока нет заметок."
    else:
        message = "Ваши заметки:\n"
        for i, note in enumerate(user_notes):
            tags = ", ".join(note.get("tags", []))
            message += f"{i + 1}. {note['text']}\n   Tags: {tags}\n"
        return message

async def add_note(user_notes: list, note_text: str) -> tuple[list, str]:
    """Adds a note."""
    tags = await get_tags_from_openai(note_text)
    user_notes.append({"text": note_text, "tags": tags})
    return user_notes, f"Заметка добавлена: {note_text}\nТеги: {', '.join(tags)}"

async def delete_note(user_notes: list, note_id: int) -> tuple[list, str]:
    """Deletes a note."""
    if 1 <= note_id <= len(user_notes):
        deleted_note = user_notes.pop(note_id - 1)
        return user_notes, f"Заметка удалена: {deleted_note['text']}"
    else:
        return user_notes, "Неверный ID заметки."

async def edit_note(user_notes: list, note_id: int, new_text: str) -> tuple[list, str]:
    """Edits a note."""
    if 1 <= note_id <= len(user_notes):
        tags = await get_tags_from_openai(new_text)
        user_notes[note_id - 1] = {"text": new_text, "tags": tags}
        return user_notes, f"Заметка {note_id} отредактирована.\nНовые теги: {', '.join(tags)}"
    else:
        return user_notes, "Неверный ID заметки."

async def find_by_tag(user_notes: list, tag: str) -> str:
    """Finds notes by tag."""
    found_notes = [
        note
        for note in user_notes
        if tag.lower() in [t.lower() for t in note.get("tags", [])]
    ]

    if not found_notes:
        return f"Заметок с тегом '{tag}' не найдено."
    else:
        message = f"Заметки с тегом '{tag}':\n"
        for i, note in enumerate(found_notes):
            message += f"{i + 1}. {note['text']}\n"
        return message
