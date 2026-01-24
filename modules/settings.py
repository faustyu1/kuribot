from pyrogram import filters, Client
from pyrogram.types import Message
import os

@Client.on_message(filters.command("settings", prefixes=".") & filters.me)
async def settings_handler(client: Client, message: Message):
    from core.assistant import get_assistant
    assistant = get_assistant()
    
    if not assistant:
        return await message.edit("<b>⚠️ Ассистент не настроен (BOT_TOKEN отсутствует).</b>")

    bot_info = await assistant.get_me()
    
    # Delete the command message
    await message.delete()
    
    try:
        # Get inline results from assistant
        results = await client.get_inline_bot_results(bot_info.username, "settings")
        
        # Send the first result (our settings menu)
        await client.send_inline_bot_result(
            chat_id=message.chat.id,
            query_id=results.query_id,
            result_id=results.results[0].id
        )
    except Exception as e:
        # Fallback if inline fails
        await client.send_message(message.chat.id, f"<b>❌ Ошибка вызова inline-меню:</b> <code>{e}</code>")

@Client.on_message(filters.command("install", prefixes=".") & filters.me)
async def install_handler(client: Client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.document:
        return await message.edit("<b>Ответьте на .py файл сообщения, чтобы установить его как модуль.</b>")
    
    doc = message.reply_to_message.document
    if not doc.file_name.endswith(".py"):
        return await message.edit("<b>Это не Python файл!</b>")
    
    path = os.path.join("modules", doc.file_name)
    await message.edit(f"<b>📥 Устанавливаю модуль <code>{doc.file_name}</code>...</b>")
    
    await client.download_media(message.reply_to_message, file_name=path)
    
    # Hot-load the newly installed module
    module_name = doc.file_name.replace(".py", "")
    success, result = await client.load_module(module_name)
    
    if success:
        await message.edit(
            f"<b>✅ Модуль <code>{doc.file_name}</code> установлен и загружен!</b>\n"
            f"Обработчиков: <code>{result}</code>"
        )
    else:
        await message.edit(
            f"<b>⚠️ Модуль <code>{doc.file_name}</code> скачан, но не загружен автоматически:</b>\n"
            f"<code>{result}</code>\n\n"
            f"Попробуйте <code>.reload {module_name}</code> позже."
        )
