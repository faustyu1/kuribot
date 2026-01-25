from core.config import config
# meta developer: @faustyu
# meta description: Модуль заметок и быстрых тегов

import json
import os
from pyrogram import filters, Client
from pyrogram.types import Message

NOTES_FILE = "data/notes.json"

def load_notes():
    if not os.path.exists(NOTES_FILE):
        return {}
    try:
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_notes(notes):
    os.makedirs("data", exist_ok=True)
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, indent=4, ensure_ascii=False)

@Client.on_message(filters.command("save", prefixes=config.get("prefix", ".")) & filters.me)
async def save_note_handler(client: Client, message: Message):
    """Сохранить заметку (как ответ на сообщение)"""
    if not message.reply_to_message:
        return await message.edit("<b>⚠️ Ответьте на сообщение, которое нужно сохранить!</b>\nИспользование: <code>.save [имя]</code>")

    if len(message.command) < 2:
        return await message.edit("<b>⚠️ Укажите название для заметки!</b>")

    name = message.command[1].lower()
    notes = load_notes()
    
    # Сохраняем ID сообщения и чата, или текст (для простоты сохраним текст/медиа)
    # Но лучше всего просто сохранять текст/file_id
    
    msg = message.reply_to_message
    note_data = {
        "text": msg.text or msg.caption or "",
        "type": "text"
    }
    
    if msg.photo:
        note_data["type"] = "photo"
        note_data["file_id"] = msg.photo.file_id
    elif msg.video:
        note_data["type"] = "video"
        note_data["file_id"] = msg.video.file_id
    elif msg.document:
        note_data["type"] = "document"
        note_data["file_id"] = msg.document.file_id

    notes[name] = note_data
    save_notes(notes)
    await message.edit(f"<b>✅ Заметка <code>#{name}</code> сохранена!</b>")

@Client.on_message(filters.command(["notes", "tags"], prefixes=config.get("prefix", ".")) & filters.me)
async def list_notes_handler(client: Client, message: Message):
    """Список всех заметок"""
    notes = load_notes()
    if not notes:
        return await message.edit("<b>📭 Список заметок пуст.</b>")
    
    out = "<b>📝 Ваши заметки:</b>\n\n"
    for name in sorted(notes.keys()):
        out += f"• <code>#{name}</code>\n"
    await message.edit(out)

@Client.on_message(filters.command("delnote", prefixes=config.get("prefix", ".")) & filters.me)
async def del_note_handler(client: Client, message: Message):
    """Удалить заметку"""
    if len(message.command) < 2:
        return await message.edit("<b>⚠️ Укажите имя заметки!</b>")
    
    name = message.command[1].lower()
    notes = load_notes()
    
    if name in notes:
        del notes[name]
        save_notes(notes)
        await message.edit(f"<b>❌ Заметка <code>#{name}</code> удалена.</b>")
    else:
        await message.edit("<b>⚠️ Заметка не найдена.</b>")

@Client.on_message(filters.regex(r"^#(\w+)") & filters.me)
async def trigger_note_handler(client: Client, message: Message):
    """Вызов заметки по хэштегу #имя"""
    name = message.matches[0].group(1).lower()
    notes = load_notes()
    
    if name in notes:
        note = notes[name]
        await message.delete()
        
        reply_to = message.reply_to_message.id if message.reply_to_message else None
        
        if note["type"] == "text":
            await client.send_message(message.chat.id, note["text"], reply_to_message_id=reply_to)
        elif note["type"] == "photo":
            await client.send_photo(message.chat.id, note["file_id"], caption=note["text"], reply_to_message_id=reply_to)
        elif note["type"] == "video":
            await client.send_video(message.chat.id, note["file_id"], caption=note["text"], reply_to_message_id=reply_to)
        elif note["type"] == "document":
            await client.send_document(message.chat.id, note["file_id"], caption=note["text"], reply_to_message_id=reply_to)