from core.config import config
# meta developer: @faustyu
# meta description: Управление чатом (удаление, очистка, инфо)

import asyncio
from pyrogram import filters, Client
from pyrogram.types import Message

@Client.on_message(filters.command("del", prefixes=config.get("prefix", ".")) & filters.me)
async def delete_message(client: Client, message: Message):
    if message.reply_to_message: await message.reply_to_message.delete()
    await message.delete()

@Client.on_message(filters.command("purge", prefixes=config.get("prefix", ".")) & filters.me)
async def purge_messages(client: Client, message: Message):
    if not message.reply_to_message: return await message.edit("<b>Ответьте на сообщение, чтобы начать чистку.</b>")
    chat_id = message.chat.id
    from_id, to_id = message.reply_to_message.id, message.id
    msgs = []
    async for msg in client.get_chat_history(chat_id, offset_id=from_id - 1):
        msgs.append(msg.id)
        if msg.id == to_id: break
        if len(msgs) >= 100:
            await client.delete_messages(chat_id, msgs)
            msgs = []
            await asyncio.sleep(0.5)
    if msgs: await client.delete_messages(chat_id, msgs)
    status = await client.send_message(chat_id, "<b>✅ Очистка завершена!</b>")
    await asyncio.sleep(2)
    await status.delete()

@Client.on_message(filters.command("whois", prefixes=config.get("prefix", ".")) & filters.me)
async def whois_handler(client: Client, message: Message):
    user = message.reply_to_message.from_user if message.reply_to_message else \
           (await client.get_users(message.command[1]) if len(message.command) > 1 else message.from_user)
    
    if not user: return await message.edit("<b>❌ Пользователь не найден.</b>")

    text = f"<b>👤 Информация:</b>\n" \
           f"• <b>Имя:</b> {user.first_name} {user.last_name or ''}\n" \
           f"• <b>ID:</b> <code>{user.id}</code>\n" \
           f"• <b>Юзернейм:</b> @{user.username if user.username else 'нет'}\n" \
           f"• <b>DC ID:</b> {user.dc_id or '?'}\n" \
           f"• <b>Premium:</b> {'Да' if user.is_premium else 'Нет'}\n"
    await message.edit(text)