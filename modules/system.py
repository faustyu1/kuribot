import os
import time
from pyrogram import filters, Client
from pyrogram.types import Message
from core.utils import get_uptime
from core.config import config

@Client.on_message(filters.command(["load", "reload"], prefixes=config.get("prefix", ".")) & filters.me)
async def reload_module_handler(client, message: Message):
    if len(message.command) < 2: return await message.edit("<b>Введите название модуля.</b>")
    module_name = message.command[1].replace(".py", "")
    await message.edit(f"<b>🔄 Перезагрузка <code>{module_name}</code>...</b>")
    success, result = await client.load_module(module_name)
    if success:
        await message.edit(f"<b>✅ Модуль <code>{module_name}</code> загружен!</b>\nОбработчиков: <code>{result}</code>")
    else:
        await message.edit(f"<b>❌ Ошибка:</b>\n<code>{result}</code>")

@Client.on_message(filters.command("unload", prefixes=config.get("prefix", ".")) & filters.me)
async def unload_module_handler(client, message: Message):
    if len(message.command) < 2: return await message.edit("<b>Введите название модуля.</b>")
    module_name = message.command[1].replace(".py", "")
    await message.edit(f"<b>📥 Выгрузка <code>{module_name}</code>...</b>")
    success, result = await client.unload_module(module_name)
    if success:
        await message.edit(f"<b>✅ Модуль <code>{module_name}</code> выгружен.</b>")
    else:
        await message.edit(f"<b>❌ Ошибка:</b> <code>{result}</code>")

@Client.on_message(filters.command(["modlist", "modules"], prefixes=config.get("prefix", ".")) & filters.me)
async def modlist_handler(client, message: Message):
    loaded = list(client._handlers_map.keys())
    all_files = sorted([f.replace(".py", "") for f in os.listdir("modules") if f.endswith(".py") and not f.startswith("__")])
    out = "<b>📂 Список модулей:</b>\n\n"
    for mod in all_files:
        status = "🟢" if mod in loaded else "⚪"
        info = f"(<code>{len(client._handlers_map[mod])}</code>)" if mod in loaded else "<i>(не загружен)</i>"
        out += f"{status} <code>{mod}</code> {info}\n"
    out += f"\n📊 Всего: <b>{len(all_files)}</b> | Загружено: <b>{len(loaded)}</b>"
    await message.edit(out)

@Client.on_message(filters.command("settings", prefixes=config.get("prefix", ".")) & filters.me)
async def settings_handler(client: Client, message: Message):
    from core.assistant import get_assistant
    assistant = get_assistant()
    if not assistant: return await message.edit("<b>⚠️ Ассистент не настроен.</b>")
    bot_info = await assistant.get_me()
    await message.delete()
    try:
        results = await client.get_inline_bot_results(bot_info.username, "settings")
        await client.send_inline_bot_result(message.chat.id, results.query_id, results.results[0].id)
    except Exception as e:
        await client.send_message(message.chat.id, f"<b>❌ Ошибка inline:</b> <code>{e}</code>")

@Client.on_message(filters.command("info", prefixes=config.get("prefix", ".")) & filters.me)
async def info_handler(client: Client, message: Message):
    # Retrieve banner from config
    from core.config import config
    banner = config.get("info_banner")
    from core.utils import get_uptime
    uptime = get_uptime()
    
    msg = f"<b>✨ KuriBot Status</b>\n\n" \
          f"<b>⏳ Uptime:</b> {uptime}\n" \
          f"<b>📊 Modules:</b> {len(client._handlers_map)}\n" \
          f"<b>🐍 Python:</b> 3.11\n"
    
    if banner:
        try:
            await message.delete()
            if banner.endswith((".mp4", ".gif")): await client.send_animation(message.chat.id, banner, caption=msg)
            else: await client.send_photo(message.chat.id, banner, caption=msg)
        except: await client.send_message(message.chat.id, msg)
    else:
        from pyrogram.types import LinkPreviewOptions
        await message.edit(msg, link_preview_options=LinkPreviewOptions(is_disabled=True))

@Client.on_message(filters.command("ping", prefixes=config.get("prefix", ".")) & filters.me)
async def ping_handler(client: Client, message: Message):
    start = time.time()
    await message.edit("🏓 Pinging...")
    duration = (time.time() - start) * 1000
    await message.edit(f"<b>🏓 Pong!</b>\n⏱ <code>{duration:.2f}ms</code>")

@Client.on_message(filters.command("install", prefixes=config.get("prefix", ".")) & filters.me)
async def install_handler(client: Client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.document:
        return await message.edit("<b>⚠️ Ответьте на .py файл.</b>")
    doc = message.reply_to_message.document
    if not doc.file_name.endswith(".py"): return await message.edit("<b>❌ Это не Python файл.</b>")
    path = os.path.join("modules", doc.file_name)
    await message.edit(f"<b>📥 Установка <code>{doc.file_name}</code>...</b>")
    await client.download_media(message.reply_to_message, file_name=path)
    module_name = doc.file_name.replace(".py", "")
    success, result = await client.load_module(module_name)
    if success: await message.edit(f"<b>✅ Модуль <code>{doc.file_name}</code> установлен!</b>")
    else: await message.edit(f"<b>❌ Ошибка:</b>\n<code>{result}</code>")
