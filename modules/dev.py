from core.config import config
# meta developer: @faustyu
# meta description: Системный модуль для разработчиков (eval, shell, ls, cat)

import os
import sys
import io
import traceback
import asyncio
from pyrogram import filters, Client
from pyrogram.types import Message

@Client.on_message(filters.command("eval", prefixes=config.get("prefix", ".")) & filters.me)
async def eval_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.edit("<b>Give me some code to run.</b>")

    code = message.text.split(None, 1)[1]
    await message.edit("<b>Running...</b>")

    old_stderr, old_stdout = sys.stderr, sys.stdout
    redirected_output, redirected_error = io.StringIO(), io.StringIO()
    sys.stdout, sys.stderr = redirected_output, redirected_error
    stdout, stderr, exc = None, None, None

    try:
        local_vars = {"client": client, "message": message, "reply": message.reply_to_message}
        exec(
            f"async def __ex(client, message, reply): " +
            "".join(f"\n {line}" for line in code.split("\n")),
            local_vars,
        )
        await local_vars["__ex"](client, message, message.reply_to_message)
    except Exception:
        exc = traceback.format_exc()

    stdout, stderr = redirected_output.getvalue(), redirected_error.getvalue()
    sys.stdout, sys.stderr = old_stdout, old_stderr

    evaluation = exc or stderr or stdout or "Success"
    
    final_output = (
        f"<b>💻 Eval:</b>\n<pre language='python'>{code}</pre>\n"
        f"<b>📊 Result:</b>\n<pre language='python'>{evaluation}</pre>"
    )
    
    if len(final_output) > 4096:
        await message.edit(f"<b>📊 Result:</b>\n<pre language='python'>{evaluation[:4000]}</pre>")
    else:
        await message.edit(final_output)

@Client.on_message(filters.command(["exec", "sh"], prefixes=config.get("prefix", ".")) & filters.me)
async def shell_handler(client: Client, message: Message):
    """Выполнить команду в shell"""
    if len(message.command) < 2:
        return await message.edit("<b>⚠️ Введите команду для выполнения.</b>")

    cmd = message.text.split(None, 1)[1]
    await message.edit(f"<b>📟 Выполнение:</b>\n<code>{cmd}</code>")

    try:
        process = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        result = (stdout.decode() + stderr.decode()).strip() or "Команда выполнена (пустой вывод)"

        out = (
            f"<b>📟 Command:</b>\n<code>{cmd}</code>\n\n"
            f"<b>📊 Result:</b>\n<pre language='shell'>{result}</pre>"
        )
        
        if len(out) > 4000:
            with open("exec_output.txt", "w", encoding="utf-8") as f:
                f.write(result)
            await client.send_document(message.chat.id, "exec_output.txt", caption=f"📟 <code>{cmd[:50]}...</code>")
            os.remove("exec_output.txt")
            await message.delete()
        else:
            await message.edit(out)
    except Exception as e:
        await message.edit(f"<b>❌ Ошибка:</b>\n<code>{str(e)}</code>")

@Client.on_message(filters.command(["ls", "dir"], prefixes=config.get("prefix", ".")) & filters.me)
async def ls_handler(client: Client, message: Message):
    """Список файлов в директории"""
    path = message.command[1] if len(message.command) > 1 else "."
    if not os.path.exists(path):
        return await message.edit(f"<b>❌ Путь не найден:</b> <code>{path}</code>")

    ignored = ["__pycache__", ".git", ".gitignore", ".dockerignore", ".agent", "node_modules", "kuribot.session", "kuribot.session-journal", "venv"]
    try:
        if os.path.isfile(path):
            return await message.edit(f"<b>📄 Файл:</b> <code>{path}</code> ({os.path.getsize(path)} байт)")

        files = os.listdir(path)
        filtered = [f for f in files if f not in ignored and not f.endswith(('.pyc', '.pyo'))]
        filtered.sort(key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))

        out = f"<b>📂 Содержимое</b> <code>{path}</code>:\n\n"
        for f in filtered:
            f_path = os.path.join(path, f)
            icon = "📁" if os.path.isdir(f_path) else "📄"
            size = "" if os.path.isdir(f_path) else f" ({os.path.getsize(f_path)} байт)"
            out += f"{icon} <code>{f}</code>{size}\n"

        if not filtered:
            out += "<i>(Пусто или всё скрыто)</i>"
            
        await message.edit(out)
    except Exception as e:
        await message.edit(f"<b>❌ Ошибка:</b>\n<code>{str(e)}</code>")

@Client.on_message(filters.command(["cat", "read"], prefixes=config.get("prefix", ".")) & filters.me)
async def cat_handler(client: Client, message: Message):
    """Прочитать файл"""
    if len(message.command) < 2: 
        return await message.edit("<b>⚠️ Укажите путь к файлу!</b>")
    
    flags = [arg for arg in message.command if arg.startswith("-")]
    path = next((arg for arg in message.command[1:] if not arg.startswith("-")), None)
    
    if not path or not os.path.exists(path): 
        return await message.edit("<b>❌ Файл не найден.</b>")
    
    if os.path.isdir(path):
        return await message.edit(f"<b>❌ Это директория.</b>")

    # Проверка на конфиденциальные файлы
    SENSITIVE_FILES = [".env", "config.json", "kuribot.session"]
    is_sensitive = any(s in path.lower() for s in SENSITIVE_FILES)
    
    me = await client.get_me()
    target_chat = "me" if (is_sensitive and message.chat.id != me.id) else message.chat.id
    was_redirected = target_chat == "me" and message.chat.id != me.id

    try:
        size = os.path.getsize(path)
        force_file = "-f" in flags
        force_text = "-t" in flags

        if (force_file or size > 4000) and not force_text:
            if was_redirected:
                await message.edit("<b>🛡 Файл содержит конфиденциальную информацию. Отправляю в Избранное...</b>")
            else:
                await message.edit(f"<b>📤 Отправляю файлом...</b>")
                
            await client.send_document(target_chat, path, caption=f"📄 <code>{os.path.basename(path)}</code>")
            
            if was_redirected:
                await asyncio.sleep(2)
            return await message.delete()

        with open(path, "r", encoding="utf-8") as f: 
            content = f.read()
            
        ext = os.path.splitext(path)[1].lower().replace(".", "")
        lang = ext if ext in ["py", "json", "yml", "yaml", "txt", "md"] else ""
        
        out = f"<b>📄 Файл:</b> <code>{path}</code>\n\n<pre language='{lang}'>{content}</pre>"
        
        if was_redirected:
            await client.send_message(target_chat, out)
            await message.edit("<b>🛡 Контент отправлен в Избранное (безопасность).</b>")
            await asyncio.sleep(3)
            await message.delete()
        else:
            await message.edit(out)
    except Exception as e:
        await message.edit(f"<b>❌ Ошибка:</b>\n<code>{str(e)}</code>")