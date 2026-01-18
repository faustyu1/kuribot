from pyrogram import filters, Client
from pyrogram.types import Message
from core.auth_manager import auth_manager

@Client.on_message(filters.command(["auth", "trust"], prefixes=".") & filters.me)
async def auth_handler(client: Client, message: Message):
    target_id = None
    name = "Объект"

    if len(message.command) > 1:
        try:
            user = await client.get_users(message.command[1])
            target_id = user.id
            name = user.first_name
        except Exception:
            # Maybe it's a chat ID
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
        # Auth current chat
        chat_id = message.chat.id
        if auth_manager.auth_chat(chat_id):
            await message.edit(f"<b>✅ Чат <code>{chat_id}</code> авторизован.</b>")
        else:
            await message.edit("<b>⚠️ Чат уже авторизован.</b>")

@Client.on_message(filters.command(["unauth", "untrust", "ban"], prefixes=".") & filters.me)
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
        # Check if it looks like a user ID (positive and not a known chat format)
        # We'll try to ban if it's a person
        if target_id > 0:
            auth_manager.ban_user(target_id)
            await message.edit(f"<b>🚫 Пользователь <code>{target_id}</code> заблокирован (ЧС).</b>")
        else:
            # Handle chat unauth
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

@Client.on_message(filters.command(["unban"], prefixes=".") & filters.me)
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

@Client.on_message(filters.command("authlist", prefixes=".") & filters.me)
async def authlist_handler(client: Client, message: Message):
    users = auth_manager.data.get("users", [])
    chats = auth_manager.data.get("chats", [])
    blacklist = auth_manager.data.get("blacklist", [])
    
    out = "<b>🔐 Список авторизованных объектов:</b>\n\n"
    
    out += "<b>👤 Пользователи:</b>\n"
    if users:
        for u_id in users:
            out += f"• <code>{u_id}</code>\n"
    else:
        out += "<i>Список пуст</i>\n"
    
    out += "\n<b>💬 Чаты:</b>\n"
    if chats:
        for c_id in chats:
            out += f"• <code>{c_id}</code>\n"
    else:
        out += "<i>Список пуст</i>\n"
        
    out += "\n<b>🚫 Черный список:</b>\n"
    if blacklist:
        for b_id in blacklist:
            out += f"• <code>{b_id}</code>\n"
    else:
        out += "<i>Список пуст</i>\n"
        
    await message.edit(out)
