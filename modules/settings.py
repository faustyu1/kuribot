from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import os

@Client.on_message(filters.command("settings", prefixes=".") & filters.me)
async def settings_handler(client: Client, message: Message):
    text = (
        "<b>⚙️ Настройки KuriBot</b>\n\n"
        "Здесь вы можете управлять установленными модулями и конфигурацией бота."
    )
    
    # Simple settings menu (visual for now, logic can be added)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📂 Управление модулями", callback_data="manage_modules")],
        [InlineKeyboardButton("🔄 Перезагрузить", callback_data="reboot_bot")],
        [InlineKeyboardButton("❌ Закрыть", callback_data="close_settings")]
    ])
    
    # Note: KuriBots don't always support sending buttons to themselves in private, 
    # but they work in groups or if sent from a bot. 
    # For a self-bot, we usually just edit the message text with info.
    
    modules_count = len([f for f in os.listdir("modules") if f.endswith(".py")])
    
    status_text = (
        f"<b>⚙️ Настройки KuriBot</b>\n\n"
        f"• <b>Модулей загружено:</b> {modules_count}\n"
        f"• <b>Python:</b> 3.11\n"
        f"• <b>Библиотека:</b> Kurigram (Pyrogram)\n\n"
        f"<i>Для установки нового модуля просто закиньте .py файл в папку modules/ и перезапустите контейнер.</i>"
    )
    
    await message.edit(status_text)

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
