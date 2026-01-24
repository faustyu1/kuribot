import os
import sys
import io
import traceback
import asyncio
from pyrogram import filters, Client
from pyrogram.types import Message

@Client.on_message(filters.command("eval", prefixes=".") & filters.me)
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
    final_output = f"<b>💻 Eval result:</b>\n<pre language='python'>{evaluation}</pre>"
    
    if len(final_output) > 4096:
        await message.edit("<b>Output too long.</b>")
    else:
        await message.edit(final_output)

@Client.on_message(filters.command(["exec", "sh"], prefixes=".") & filters.me)
async def shell_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.edit("<b>Введите команду для выполнения.</b>")

    cmd = message.text.split(None, 1)[1]
    await message.edit(f"<b>📟 Выполнение:</b>\n<code>{cmd}</code>")

    try:
        process = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        result = (stdout.decode() + stderr.decode()).strip() or "Команда выполнена (пустой вывод)"

        out = f"<b>📟 Результат:</b>\n<pre language='shell'>{result}</pre>"
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

@Client.on_message(filters.command(["ls", "dir"], prefixes=".") & filters.me)
async def ls_handler(client: Client, message: Message):
    path = message.command[1] if len(message.command) > 1 else "."
    if not os.path.exists(path):
        return await message.edit(f"<b>❌ Path not found:</b> <code>{path}</code>")

    ignored = ["__pycache__", ".git", ".gitignore", ".dockerignore", ".env", ".agent", "node_modules", "kuribot.session", "venv"]
    try:
        if os.path.isfile(path):
            return await message.edit(f"<b>📄 File:</b> <code>{path}</code> ({os.path.getsize(path)} bytes)")

        files = os.listdir(path)
        filtered = [f for f in files if f not in ignored and not f.endswith(('.pyc', '.pyo'))]
        filtered.sort(key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))

        out = f"<b>📂 Contents of</b> <code>{path}</code>:\n\n"
        for f in filtered:
            f_path = os.path.join(path, f)
            icon = "📁" if os.path.isdir(f_path) else "📄"
            size = "" if os.path.isdir(f_path) else f" ({os.path.getsize(f_path)} bytes)"
            out += f"{icon} <code>{f}</code>{size}\n"

        await message.edit(out or "<i>(Пусто)</i>")
    except Exception as e:
        await message.edit(f"<b>❌ Error:</b>\n<code>{str(e)}</code>")

@Client.on_message(filters.command(["cat", "read"], prefixes=".") & filters.me)
async def cat_handler(client: Client, message: Message):
    if len(message.command) < 2: return await message.edit("<b>Укажите путь к файлу!</b>")
    flags, path = [arg for arg in message.command if arg.startswith("-")], next((arg for arg in message.command[1:] if not arg.startswith("-")), None)
    if not path or not os.path.exists(path): return await message.edit("<b>❌ Файл не найден.</b>")
    
    try:
        size = os.path.getsize(path)
        if ("-f" in flags or size > 4000) and "-t" not in flags:
            await client.send_document(message.chat.id, path, caption=f"📄 <code>{os.path.basename(path)}</code>")
            return await message.delete()

        with open(path, "r", encoding="utf-8") as f: content = f.read()
        ext = os.path.splitext(path)[1].lower().replace(".", "")
        lang = ext if ext in ["py", "json", "yml", "yaml", "txt", "md"] else ""
        await message.edit(f"<b>📄 Файл:</b> <code>{path}</code>\n\n<pre language='{lang}'>{content}</pre>")
    except Exception as e:
        await message.edit(f"<b>❌ Ошибка:</b>\n<code>{str(e)}</code>")
