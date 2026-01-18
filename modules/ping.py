from pyrogram import filters, Client
from pyrogram.types import Message
import time

@Client.on_message(filters.command("ping", prefixes=".") & filters.me)
async def ping_handler(client: Client, message: Message):
    start = time.time()
    reply = await message.edit("🏓 Pinging...")
    end = time.time()
    duration = (end - start) * 1000
    await reply.edit(f"<b>🏓 Pong!</b>\n⏱ <code>{duration:.2f}ms</code>")

@Client.on_message(filters.command("uptime", prefixes=".") & filters.me)
async def uptime_handler(client: Client, message: Message):
    # This is a dummy uptime, in real app we would track it
    await message.edit("<b>🚀 KuriBot is running!</b>")
