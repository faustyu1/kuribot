# meta developer: @faustyu
# meta description: Безопасность и защита от спама

import os
import aiohttp
import asyncio

from pyrogram import filters, Client
from pyrogram.types import Message
from core.auth_manager import auth_manager
from core.security import analyze_module, is_official
from core.config import config

# Temporary storage for pending installations: {msg_id: (url, content, filename)}
_PENDING = {}

@Client.on_message(filters.command(["auth", "trust"], prefixes=config.get("prefix", ".")) & filters.me)
async def auth_handler(client: Client, message: Message):
    target_id = None
    name = "Объект"

    if len(message.command) > 1:
        try:
            user = await client.get_users(message.command[1])
            target_id = user.id
            name = user.first_name
        except Exception:
            try:
                target_id = int(message.command[1])
            except ValueError:
                return await message.edit("<b>❌ Не удалось найти пользователя/чат.</b>")
    elif message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        name = message.reply_to_message.from_user.first_name
    
    if target_id:
        if auth_manager.auth_user(target_id):
            await message.edit(f"<b>✅ {name} (<code>{target_id}</code>) авторизован.</b>")
        else:
            await message.edit("<b>⚠️ Уже авторизован.</b>")
    else:
        chat_id = message.chat.id
        if auth_manager.auth_chat(chat_id):
            await message.edit(f"<b>✅ Чат <code>{chat_id}</code> авторизован.</b>")
        else:
            await message.edit("<b>⚠️ Чат уже авторизован.</b>")

@Client.on_message(filters.command(["unauth", "untrust", "ban"], prefixes=config.get("prefix", ".")) & filters.me)
async def unauth_handler(client: Client, message: Message):
    target_id = None

    if len(message.command) > 1:
        try:
            user = await client.get_users(message.command[1])
            target_id = user.id
        except Exception:
            try:
                target_id = int(message.command[1])
            except ValueError:
                return await message.edit("<b>❌ Не удалось найти пользователя/чат.</b>")
    elif message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
    
    if target_id:
        if target_id > 0:
            auth_manager.ban_user(target_id)
            await message.edit(f"<b>🚫 Пользователь <code>{target_id}</code> заблокирован (ЧС).</b>")
        else:
            if auth_manager.unauth_chat(target_id):
                await message.edit(f"<b>❌ Авторизация чата <code>{target_id}</code> отозвана.</b>")
            else:
                await message.edit("<b>⚠️ Объект не был авторизован.</b>")
    else:
        chat_id = message.chat.id
        if auth_manager.unauth_chat(chat_id):
            await message.edit(f"<b>❌ Авторизация чата <code>{chat_id}</code> отозвана.</b>")
        else:
            await message.edit("<b>⚠️ Чат не был авторизован.</b>")

@Client.on_message(filters.command(["unban"], prefixes=config.get("prefix", ".")) & filters.me)
async def unban_handler(client: Client, message: Message):
    target_id = None
    if len(message.command) > 1:
        try:
            target_id = int(message.command[1])
        except:
            try:
                user = await client.get_users(message.command[1])
                target_id = user.id
            except: pass
    elif message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        
    if target_id and auth_manager.unban_user(target_id):
        await message.edit(f"<b>✅ Пользователь <code>{target_id}</code> разблокирован.</b>")
    else:
        await message.edit("<b>⚠️ Пользователь не в ЧС.</b>")

@Client.on_message(filters.command("authlist", prefixes=config.get("prefix", ".")) & filters.me)
async def authlist_handler(client: Client, message: Message):
    users = auth_manager.data.get("users", [])
    chats = auth_manager.data.get("chats", [])
    blacklist = auth_manager.data.get("blacklist", [])
    
    out = "<b>🔐 Список авторизованных объектов:</b>\n\n"
    out += "<b>👤 Пользователи:</b>\n"
    out += "\n".join([f"• <code>{u_id}</code>" for u_id in users]) if users else "<i>Список пуст</i>"
    out += "\n\n<b>💬 Чаты:</b>\n"
    out += "\n".join([f"• <code>{c_id}</code>" for c_id in chats]) if chats else "<i>Список пуст</i>"
    out += "\n\n<b>🚫 Черный список:</b>\n"
    out += "\n".join([f"• <code>{b_id}</code>" for b_id in blacklist]) if blacklist else "<i>Список пуст</i>"
    await message.edit(out)

@Client.on_message(filters.command("dlmod", prefixes=config.get("prefix", ".")) & filters.me)
async def dlmod_handler(client, message: Message):
    if len(message.command) < 2:
        return await message.edit("<b>⚠️ Укажите ссылку на модуль.</b>")

    url = message.command[1]
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

    filename = url.split("/")[-1]
    if not filename.endswith(".py"): filename += ".py"

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
    
    await asyncio.sleep(60)
    if sent.id in _PENDING:
        del _PENDING[sent.id]
        await sent.edit("<b>⏰ Время ожидания подтверждения истекло.</b>")

@Client.on_message(filters.command("confirm", prefixes=config.get("prefix", ".")) & filters.me)
async def confirm_handler(client, message: Message):
    if not message.reply_to_message or message.reply_to_message.id not in _PENDING:
        return

    url, content, filename = _PENDING.pop(message.reply_to_message.id)
    path = os.path.join("modules", filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    module_name = filename.replace(".py", "")
    success, result = await client.load_module(module_name)

    if success:
        await message.edit(f"<b>✅ Модуль <code>{filename}</code> успешно установлен!</b>")
    else:
        await message.edit(f"<b>⚠️ Ошибка загрузки:</b>\n<code>{result}</code>")
