from pyrogram import filters, Client
from pyrogram.types import Message
import sys
import io
import traceback

@Client.on_message(filters.command("eval", prefixes=".") & filters.me)
async def eval_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.edit("<b>Give me some code to run.</b>")

    code = message.text.split(None, 1)[1]
    await message.edit("<b>Running...</b>")

    old_stderr = sys.stderr
    old_stdout = sys.stdout
    redirected_output = io.StringIO()
    redirected_error = io.StringIO()
    sys.stdout = redirected_output
    sys.stderr = redirected_error
    stdout, stderr, exc = None, None, None

    try:
        # Create a local scope for the eval
        local_vars = {"client": client, "message": message, "reply": message.reply_to_message}
        exec(
            f"async def __ex(client, message, reply): " +
            "".join(f"\n {line}" for line in code.split("\n")),
            local_vars,
        )
        await local_vars["__ex"](client, message, message.reply_to_message)
    except Exception:
        exc = traceback.format_exc()

    stdout = redirected_output.getvalue()
    stderr = redirected_error.getvalue()
    sys.stdout = old_stdout
    sys.stderr = old_stderr

    evaluation = ""
    if exc:
        evaluation = exc
    elif stderr:
        evaluation = stderr
    elif stdout:
        evaluation = stdout
    else:
        evaluation = "Success"

    final_output = f"<b>💻 Eval result:</b>\n<pre language='python'>{evaluation}</pre>"
    if len(final_output) > 4096:
        await message.edit("<b>Output too long.</b>")
    else:
        await message.edit(final_output)
