from pyrogram import filters, Client
from pyrogram.types import Message
import asyncio
import os

@Client.on_message(filters.command(["exec", "sh"], prefixes=".") & filters.me)
async def shell_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.edit("<b>Введите команду для выполнения.</b>")

    cmd = message.text.split(None, 1)[1]
    await message.edit(f"<b>📟 Выполнение:</b>\n<code>{cmd}</code>")

    try:
        # Execute shell command
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        result = (stdout.decode() + stderr.decode()).strip()

        if not result:
            result = "Команда выполнена (пустой вывод)"

        # Formatting output
        out = f"<b>📟 Результат:</b>\n<pre language='shell'>{result}</pre>"
        
        if len(out) > 4000:
            # If too large, send as file
            with open("exec_output.txt", "w", encoding="utf-8") as f:
                f.write(result)
            await client.send_document(
                chat_id=message.chat.id,
                document="exec_output.txt",
                caption=f"📟 <code>{cmd[:50]}...</code>"
            )
            os.remove("exec_output.txt")
            await message.delete()
        else:
            await message.edit(out)
            
    except Exception as e:
        await message.edit(f"<b>❌ Ошибка:</b>\n<code>{str(e)}</code>")
