from pyrogram import filters, Client
from pyrogram.types import Message
import asyncio

@Client.on_message(filters.command("del", prefixes=".") & filters.me)
async def delete_message(client: Client, message: Message):
    if message.reply_to_message:
        await message.reply_to_message.delete()
    await message.delete()

@Client.on_message(filters.command("purge", prefixes=".") & filters.me)
async def purge_messages(client: Client, message: Message):
    if not message.reply_to_message:
        await message.edit("<b>Reply to a message to start purging from there.</b>")
        return

    chat_id = message.chat.id
    from_message = message.reply_to_message.id
    to_message = message.id

    messages_to_delete = []
    async for msg in client.get_chat_history(chat_id, offset_id=from_message - 1):
        messages_to_delete.append(msg.id)
        if msg.id == to_message:
            break
        if len(messages_to_delete) >= 100: # Delete in batches
            await client.delete_messages(chat_id, messages_to_delete)
            messages_to_delete = []
            await asyncio.sleep(0.5)

    if messages_to_delete:
        await client.delete_messages(chat_id, messages_to_delete)

    status = await message.edit("<b>Purge completed!</b>")
    await asyncio.sleep(2)
    await status.delete()
