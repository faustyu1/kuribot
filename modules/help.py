from pyrogram import filters, Client
from pyrogram.types import Message

HELP_TEXT = """
<b>🛠 KuriBot Help</b>

<b>Commands:</b>
• <code>.ping</code> - Latency check
• <code>.ls</code> - Files structure
• <code>.cat [path]</code> - Read file
• <code>.exec [cmd]</code> - Shell run
• <code>.eval [code]</code> - Python run
• <code>.summarize [N]</code> - AI summary
• <code>.auth</code> / <code>.unauth</code> / <code>.authlist</code>
• <code>.modules</code> - List modules
• <code>.reload [mod]</code> - Hot reload module
• <code>.settings</code> - Bot info
• <code>.help</code> - Show this

<b>About:</b>
Modern KuriBot built with <code>Kurigram</code>.
📂 <b>Repo:</b> <a href='https://github.com/faustyu1/kuribot'>faustyu1/kuribot</a>
"""

@Client.on_message(filters.command("help", prefixes=".") & filters.me)
async def help_handler(client: Client, message: Message):
    await message.edit(HELP_TEXT)
