from pyrogram import filters, Client
from pyrogram.types import Message
import os

@Client.on_message(filters.command(["ls", "dir"], prefixes=".") & filters.me)
async def ls_handler(client: Client, message: Message):
    path = "."
    if len(message.command) > 1:
        path = message.command[1]

    if not os.path.exists(path):
        return await message.edit(f"<b>❌ Path not found:</b> <code>{path}</code>")

    # List of files/folders to hide (basic version of ignore)
    ignored = [
        "__pycache__", ".git", ".gitignore", ".dockerignore", 
        ".env", ".agent", "node_modules", "kuribot.session", 
        "kuribot.session-journal", "venv", "env"
    ]

    try:
        if os.path.isfile(path):
            size = os.path.getsize(path)
            return await message.edit(f"<b>📄 File:</b> <code>{path}</code> ({size} bytes)")

        files = os.listdir(path)
        if not files:
            return await message.edit(f"<b>📂 Directory</b> <code>{path}</code> <b>is empty.</b>")

        # Filter out ignored files
        filtered_files = [f for f in files if f not in ignored and not f.endswith(('.pyc', '.pyo'))]

        # Sort: Directories first, then by name
        filtered_files.sort(key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))

        out = f"<b>📂 Contents of</b> <code>{path}</code>:\n\n"
        for f in filtered_files:
            f_path = os.path.join(path, f)
            icon = "📁" if os.path.isdir(f_path) else "📄"
            size = "" if os.path.isdir(f_path) else f" ({os.path.getsize(f_path)} bytes)"
            out += f"{icon} <code>{f}</code>{size}\n"

        if not filtered_files:
            out += "<i>(All files are hidden by ignore list)</i>"

        if len(out) > 4096:
            await message.edit("<b>Output too long to display.</b>")
        else:
            await message.edit(out)
    except Exception as e:
        await message.edit(f"<b>❌ Error:</b>\n<code>{str(e)}</code>")
