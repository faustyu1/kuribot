from pyrogram import filters, Client
from pyrogram.types import Message, User
from core.config import config

@Client.on_message(filters.command("whois", prefixes=config.get("prefix", ".")) & filters.me)
async def whois_handler(client: Client, message: Message):
    user = None
    if message.reply_to_message:
        user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        user_input = message.command[1]
        try:
            user = await client.get_users(user_input)
        except Exception:
            await message.edit("<b>User not found.</b>")
            return
    else:
        user = message.from_user

    if not user:
        await message.edit("<b>Could not identify user.</b>")
        return

    text = f"<b>👤 User Info:</b>\n"
    text += f"• <b>Name:</b> {user.first_name} {user.last_name or ''}\n"
    text += f"• <b>ID:</b> <code>{user.id}</code>\n"
    if user.username:
        text += f"• <b>Username:</b> @{user.username}\n"
    text += f"• <b>DC ID:</b> {user.dc_id or 'Unknown'}\n"
    text += f"• <b>Premium:</b> {'Yes' if user.is_premium else 'No'}\n"
    
    await message.edit(text)