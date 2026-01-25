from core.config import config
# meta developer: @faustyu
# meta description: Помощь и список команд

from pyrogram import filters, Client
from pyrogram.types import Message, LinkPreviewOptions
import os

# Emoji mapping for modules
MODULE_EMOJIS = {
    "system": "⚙️", 
    "security": "🛡",
    "dev": "🛠",
    "chat": "💬",
    "ai": "🤖",
    "help": "❓"
}

# Grouping definition
GROUPS = {
    "⚙️ Системные": ["system", "help"],
    "🛡 Безопасность": ["security"],
    "🛠 Инструменты": ["dev"],
    "💬 Общение": ["chat"],
    "🤖 Искусственный интеллект": ["ai"]
}

def get_commands(filt):
    """Recursively extract commands from Pyrogram filters."""
    if not filt: return []
    if hasattr(filt, "commands"):
        return list(filt.commands)
    
    res = []
    if hasattr(filt, "base"): res.extend(get_commands(filt.base))
    if hasattr(filt, "other"): res.extend(get_commands(filt.other))
    return res

@Client.on_message(filters.command("help", prefixes=config.get("prefix", ".")) & filters.me)
async def help_handler(client: Client, message: Message):
    if len(message.command) > 1:
        module_name = message.command[1].lower().replace(".py", "")
        if module_name in client._handlers_map:
            handlers = client._handlers_map[module_name]
            cmds = []
            for h, _ in handlers:
                cmds.extend(get_commands(getattr(h, "filters", None)))
            
            cmds = sorted(list(set(cmds)))
            emoji = MODULE_EMOJIS.get(module_name, "📦")
            text = f"<b>{emoji} Модуль <code>{module_name}</code></b>\n\n"
            text += f"<blockquote expandable>"
            text += " | ".join([f"<code>.{c}</code>" for c in cmds]) if cmds else "<i>Команд не найдено</i>"
            text += "</blockquote>"
            return await message.edit(text, link_preview_options=LinkPreviewOptions(is_disabled=True))
        else:
            return await message.edit(f"<b>❌ Модуль <code>{module_name}</code> не найден.</b>")

    loaded_mods = set(client._handlers_map.keys())
    header = "<b>✨ KuriBot <code>Help</code></b>\n\n"
    content = ""

    # Group 1: Core/System modules (system, help, etc.)
    system_mods_list = ["system", "help", "security"]
    system_content = ""
    for mod in sorted(system_mods_list):
        if mod in loaded_mods:
            emoji = MODULE_EMOJIS.get(mod, "📦")
            handlers = client._handlers_map[mod]
            cmds = []
            for h, _ in handlers:
                cmds.extend(get_commands(getattr(h, "filters", None)))
            cmds = sorted(list(set(cmds)))
            if cmds:
                cmd_line = " | ".join([f"<code>{c}</code>" for c in cmds])
                system_content += f"{emoji} <b>{mod}</b>: ( {cmd_line} )\n"
                loaded_mods.discard(mod)

    if system_content:
        content += f"<blockquote expandable>{system_content}</blockquote>\n"

    # Group 2: Everything else
    other_content = ""
    for mod in sorted(loaded_mods):
        emoji = MODULE_EMOJIS.get(mod, "📦")
        handlers = client._handlers_map[mod]
        cmds = []
        for h, _ in handlers:
            cmds.extend(get_commands(getattr(h, "filters", None)))
        cmds = sorted(list(set(cmds)))
        if cmds:
            cmd_line = " | ".join([f"<code>{c}</code>" for c in cmds])
            other_content += f"{emoji} <b>{mod}</b>: ( {cmd_line} )\n"

    if other_content:
        content += f"<blockquote expandable>{other_content}</blockquote>"

    links = f"\n📂 <b>Repo:</b> <a href='https://github.com/faustyu1/kuribot'>faustyu1/kuribot</a>"
    await message.edit(header + content + links, link_preview_options=LinkPreviewOptions(is_disabled=True))