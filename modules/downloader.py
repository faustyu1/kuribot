from core.config import config
# meta developer: @faustyu
# meta description: Загрузчик видео из TikTok, Instagram, YouTube

import aiohttp
import os
from pyrogram import filters, Client
from pyrogram.types import Message

@Client.on_message(filters.command(["dl", "download"], prefixes=config.get("prefix", ".")) & filters.me)
async def download_handler(client: Client, message: Message):
    """Скачать видео по ссылке"""
    if len(message.command) < 2:
        return await message.edit("<b>⚠️ Введите ссылку на видео!</b>")

    url = message.command[1]
    await message.edit("<b>📥 Обработка ссылки...</b>")

    # Список активных инстансов Cobalt (v10) для надежности
    COBALT_INSTANCES = [
        "https://cobalt.lucasvtiradentes.com",
        "https://cobalt.perennialte.ch",
        "https://api.cobalt.tools", # Иногда падает, но оставляем
    ]
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "KuriBot/1.0"
    }
    
    # Новая структура payload для v10
    payload = {
        "url": url,
        "videoQuality": "720",
        "downloadMode": "auto"
    }

    try:
        success = False
        for instance in COBALT_INSTANCES:
            try:
                api_url = f"{instance}/"
                async with aiohttp.ClientSession() as session:
                    async with session.post(api_url, json=payload, headers=headers, timeout=15) as resp:
                        if resp.status != 200:
                            continue
                            
                        data = await resp.json()
                        status = data.get("status")
                        
                        if status == "error":
                            continue
                        
                        # Cobalt v10 может вернуть прямую ссылку (stream) или тип "picker"
                        stream_url = data.get("url")
                        if not stream_url:
                            continue

                        await message.edit("<b>⬇️ Скачиваю и отправляю...</b>")
                        
                        async with session.get(stream_url) as file_resp:
                            if file_resp.status != 200:
                                continue
                            
                            filename = "downloaded_media.mp4"
                            with open(filename, "wb") as f:
                                f.write(await file_resp.read())

                        # Отправляем
                        await client.send_video(
                            chat_id=message.chat.id,
                            video=filename,
                            caption=f"<b>✅ Успешно скачано!</b>\n🔗 <code>{url}</code>"
                        )
                        
                        os.remove(filename)
                        await message.delete()
                        success = True
                        break
            except Exception:
                continue

        if not success:
            await message.edit("<b>❌ Не удалось скачать медиа. Все инстансы недоступны или ссылка не поддерживается.</b>")

    except Exception as e:
        await message.edit(f"<b>❌ Ошибка модуля:</b> <code>{str(e)}</code>")