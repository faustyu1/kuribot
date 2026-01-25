from core.config import config
# meta developer: @faustyu
# meta description: Переводчик текста (Google Translate)

import aiohttp
from pyrogram import filters, Client
from pyrogram.types import Message
from urllib.parse import quote

@Client.on_message(filters.command(["tr", "translate"], prefixes=config.get("prefix", ".")) & filters.me)
async def translate_handler(client: Client, message: Message):
    """Переводчик сообщений"""
    lang = "ru"
    text = ""

    if message.reply_to_message:
        text = message.reply_to_message.text or message.reply_to_message.caption
        if len(message.command) > 1:
            lang = message.command[1]
    else:
        if len(message.command) < 2:
            return await message.edit("<b>⚠️ Введите текст или ответьте на сообщение!</b>\n<code>.tr [язык] [текст]</code>")
        
        # Check if first arg is a 2-letter lang code
        if len(message.command[1]) == 2:
            lang = message.command[1]
            text = " ".join(message.command[2:])
        else:
            text = " ".join(message.command[1:])

    if not text:
        return await message.edit("<b>⚠️ Текст для перевода не найден.</b>")

    await message.edit("<b>🔄 Перевожу...</b>")

    url = (
        f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={lang}&dt=t&q={quote(text)}"
    )

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                result = await resp.json()
                
                translated_text = ""
                for part in result[0]:
                    if part[0]:
                        translated_text += part[0]
                
                source_lang = result[2]
                
                out = (
                    f"<b>🌐 Перевод ({source_lang} ➔ {lang}):</b>\n\n"
                    f"<code>{translated_text}</code>"
                )
                await message.edit(out)
    except Exception as e:
        await message.edit(f"<b>❌ Ошибка перевода:</b> <code>{str(e)}</code>")