from pyrogram import filters, Client
from pyrogram.types import Message
import os
import io

@Client.on_message(filters.command(["cat", "read"], prefixes=".") & filters.me)
async def cat_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.edit(
            "<b>Использование .cat:</b>\n"
            "• <code>.cat [путь]</code> — прочитать файл в чат.\n"
            "• <code>.cat [путь] -f</code> — отправить файл документом.\n"
            "• <code>.cat [путь] -t</code> — принудительно текстом (если файл большой)."
        )

    # Parse flags and path
    flags = [arg for arg in message.command if arg.startswith("-")]
    path = next((arg for arg in message.command[1:] if not arg.startswith("-")), None)

    if not path:
        return await message.edit("<b>Укажите путь к файлу!</b>")

    if not os.path.exists(path):
        return await message.edit(f"<b>❌ Файл не найден:</b> <code>{path}</code>")
    
    if os.path.isdir(path):
        return await message.edit(f"<b>❌ Это директория.</b>")

    force_file = "-f" in flags
    force_text = "-t" in flags

    try:
        # Check size first
        size = os.path.getsize(path)
        
        # If it's a binary file or too large, force file mode unless -t is specified
        is_too_large = size > 4000
        
        if (force_file or is_too_large) and not force_text:
            await message.edit(f"<b>📤 Отправляю файлом...</b>")
            await client.send_document(
                chat_id=message.chat.id,
                document=path,
                caption=f"📄 <code>{os.path.basename(path)}</code>"
            )
            return await message.delete()

        # Text mode
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        ext = os.path.splitext(path)[1].lower().replace(".", "")
        lang = ext if ext in ["py", "json", "yml", "yaml", "txt", "md", "html", "css"] else ""

        out = f"<b>📄 Файл:</b> <code>{path}</code>\n\n"
        out += f"<pre language='{lang}'>{content}</pre>"
        
        await message.edit(out)
    except Exception as e:
        await message.edit(f"<b>❌ Ошибка:</b>\n<code>{str(e)}</code>")
