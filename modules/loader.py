from pyrogram import filters, Client
from pyrogram.types import Message
import os

@Client.on_message(filters.command(["load", "reload"], prefixes=".") & filters.me)
async def reload_module_handler(client, message: Message):
    if len(message.command) < 2:
        return await message.edit("<b>Введите название модуля.</b>")
    
    module_name = message.command[1].replace(".py", "")
    await message.edit(f"<b>🔄 Перезагрузка модуля <code>{module_name}</code>...</b>")
    
    success, count_or_err = await client.load_module(module_name)
    
    if success:
        await message.edit(f"<b>✅ Модуль <code>{module_name}</code> успешно загружен!</b>\nОбработчиков: <code>{count_or_err}</code>")
    else:
        await message.edit(f"<b>❌ Ошибка при загрузке:</b>\n<code>{count_or_err}</code>")

@Client.on_message(filters.command("unload", prefixes=".") & filters.me)
async def unload_module_handler(client, message: Message):
    if len(message.command) < 2:
        return await message.edit("<b>Введите название модуля для выгрузки.</b>")
    
    module_name = message.command[1].replace(".py", "")
    await message.edit(f"<b>📥 Выгрузка модуля <code>{module_name}</code>...</b>")
    
    success, result = await client.unload_module(module_name)
    
    if success:
        await message.edit(f"<b>✅ Модуль <code>{module_name}</code> выгружен.</b>")
    else:
        await message.edit(f"<b>❌ Ошибка:</b> <code>{result}</code>")

@Client.on_message(filters.command(["modlist", "modules"], prefixes=".") & filters.me)
async def modlist_handler(client, message: Message):
    loaded = list(client._handlers_map.keys())
    all_files = sorted([f.replace(".py", "") for f in os.listdir("modules") if f.endswith(".py") and not f.startswith("__")])
    
    out = "<b>📂 Список модулей:</b>\n\n"
    for mod in all_files:
        if mod in loaded:
            handlers_count = len(client._handlers_map[mod])
            status = "🟢"
            info = f"(<code>{handlers_count}</code>)"
        else:
            status = "⚪"
            info = "<i>(не загружен)</i>"
        
        out += f"{status} <code>{mod}</code> {info}\n"
    
    out += f"\n📊 Всего: <b>{len(all_files)}</b> | Загружено: <b>{len(loaded)}</b>"
    await message.edit(out)
