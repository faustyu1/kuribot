import os
import aiohttp
from pyrogram import filters, Client
from pyrogram.types import Message
from core.security import analyze_module, is_official
from core.config import config

# Temporary storage for pending installations: {msg_id: (url, content, filename)}
_PENDING = {}

@Client.on_message(filters.command("dlmod", prefixes=config.get("prefix", ".")) & filters.me)
async def dlmod_handler(client, message: Message):
    if len(message.command) < 2:
        return await message.edit("<b>⚠️ Укажите ссылку на модуль.</b>")

    url = message.command[1]
    # Handle github.com links by converting to raw
    if "github.com" in url and "/blob/" in url:
        url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")

    await message.edit(f"<b>📥 Загрузка модуля из <code>{url}</code>...</b>")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    return await message.edit(f"<b>❌ Ошибка загрузки (Status {resp.status})</b>")
                content = await resp.text()
    except Exception as e:
        return await message.edit(f"<b>❌ Ошибка при скачивании:</b> <code>{e}</code>")

    # Extract filename from URL
    filename = url.split("/")[-1]
    if not filename.endswith(".py"):
        filename += ".py"

    # Security Analysis
    warnings = analyze_module(content)
    official = is_official(url)

    status_icon = "🛡" if official else "⚠️"
    status_text = "Официальный источник" if official else "Сторонний источник"
    
    warn_text = ""
    if warnings:
        warn_text = "\n\n<b>🚫 ВНИМАНИЕ! Найдены опасные функции:</b>\n"
        for w in warnings:
            warn_text += f"• <code>{w}</code>\n"
        warn_text += "\n<i>Установка этого модуля может привести к потере аккаунта!</i>"

    confirm_msg = (
        f"<b>{status_icon} Информация о модуле:</b>\n"
        f"• <b>Файл:</b> <code>{filename}</code>\n"
        f"• <b>Источник:</b> {status_text}\n"
        f"• <b>Размер:</b> {len(content)} байт"
        f"{warn_text}\n\n"
        f"<b>Вы точно хотите установить этот модуль?</b>\n"
        f"Напишите <code>.confirm</code> ответом на это сообщение в течение 60 секунд."
    )

    sent = await message.edit(confirm_msg)
    _PENDING[sent.id] = (url, content, filename)
    
    # Auto-cleanup after 60s
    import asyncio
    await asyncio.sleep(60)
    if sent.id in _PENDING:
        del _PENDING[sent.id]
        await sent.edit("<b>⏰ Время ожидания подтверждения истекло.</b>")

@Client.on_message(filters.command("confirm", prefixes=config.get("prefix", ".")) & filters.me)
async def confirm_handler(client, message: Message):
    if not message.reply_to_message or message.reply_to_message.id not in _PENDING:
        return # Ignore or show error

    url, content, filename = _PENDING.pop(message.reply_to_message.id)
    
    path = os.path.join("modules", filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    module_name = filename.replace(".py", "")
    success, result = await client.load_module(module_name)

    if success:
        await message.edit(f"<b>✅ Модуль <code>{filename}</code> успешно установлен и загружен!</b>")
    else:
        await message.edit(f"<b>⚠️ Модуль установлен, но возникла ошибка при загрузке:</b>\n<code>{result}</code>")
