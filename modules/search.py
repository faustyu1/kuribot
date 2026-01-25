from core.config import config
# meta developer: @faustyu
# meta description: Поиск в Википедии и Google

import aiohttp
import asyncio
from pyrogram import filters, Client
from pyrogram.types import Message
from urllib.parse import quote

@Client.on_message(filters.command("wiki", prefixes=config.get("prefix", ".")) & filters.me)
async def wiki_handler(client: Client, message: Message):
    """Поиск в Википедии"""
    if len(message.command) < 2:
        return await message.edit("<b>⚠️ Введите запрос для поиска!</b>")

    query = " ".join(message.command[1:])
    await message.edit(f"<b>🔍 Ищу в Wikipedia:</b> <code>{query}</code>...")

    # Wikipedia API requires a descriptive User-Agent
    url = f"https://ru.wikipedia.org/api/rest_v1/page/summary/{quote(query)}"
    headers = {"User-Agent": "KuriBot/1.0 (https://github.com/faustyu1/kuribot; contact@example.com)"}
    
    attempts = 3
    for attempt in range(attempts):
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url) as resp:
                    if resp.status == 404:
                        return await message.edit("<b>❌ Ничего не найдено.</b>")
                    if resp.status != 200:
                        if attempt < attempts - 1:
                            await asyncio.sleep(1)
                            continue
                        return await message.edit(f"<b>❌ Ошибка API Википедии:</b> <code>{resp.status}</code>")
                    
                    data = await resp.json(content_type=None)
                    title = data.get("title")
                    extract = data.get("extract")
                    page_url = data.get("content_urls", {}).get("desktop", {}).get("page")
                    thumbnail = data.get("thumbnail", {}).get("source")

                    text = f"<b>📖 {title}</b>\n\n{extract}\n\n🔗 <a href='{page_url}'>Читать полностью</a>"
                    
                    if thumbnail:
                        await client.send_photo(message.chat.id, thumbnail, caption=text)
                        await message.delete()
                    else:
                        await message.edit(text, disable_web_page_preview=False)
                    return # Success
        except Exception as e:
            if attempt < attempts - 1:
                await asyncio.sleep(1)
                continue
            await message.edit(f"<b>❌ Ошибка после {attempts} попыток:</b> <code>{str(e)}</code>")
            break

@Client.on_message(filters.command(["google", "g"], prefixes=config.get("prefix", ".")) & filters.me)
async def google_handler(client: Client, message: Message):
    """Быстрая ссылка на поиск в Google"""
    if len(message.command) < 2:
        return await message.edit("<b>⚠️ Введите запрос!</b>")
    
    query = " ".join(message.command[1:])
    link = f"https://www.google.com/search?q={quote(query)}"
    await message.edit(f"<b>🔍 Результаты поиска Google:</b>\n👉 <a href='{link}'>{query}</a>")