import os
import time
import psutil
import platform
import asyncio
from pyrogram import filters, Client
from pyrogram.types import Message
from datetime import datetime

async def get_cmd_output(cmd):
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await process.communicate()
        return stdout.decode().strip()
    except:
        return ""

async def get_git_info():
    try:
        # Get hash
        commit_hash = await get_cmd_output(["git", "rev-parse", "--short", "HEAD"])
        # Get branch
        branch = await get_cmd_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        # Get version (tag)
        version = await get_cmd_output(["git", "describe", "--tags"])
        if not version: version = "1.0.0"
        
        # Check updates
        await get_cmd_output(["git", "fetch"])
        status = await get_cmd_output(["git", "status", "-uno"])
        
        if "Your branch is up to date" in status:
            update_status = "Up-to-date"
        elif "Your branch is ahead" in status:
            update_status = "Ahead" 
        else:
            update_status = "Update available"
            
        return version, commit_hash, branch, update_status
    except Exception:
        return "Unknown", "??????", "Unknown", "Unknown"

def get_uptime():
    try:
        p = psutil.Process(os.getpid())
        uptime_seconds = time.time() - p.create_time()
        m, s = divmod(uptime_seconds, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        
        parts = []
        if d > 0: parts.append(f"{int(d)}d")
        if h > 0: parts.append(f"{int(h)}h")
        if m > 0: parts.append(f"{int(m)}m")
        if s > 0: parts.append(f"{int(s)}s")
        
        return ":".join(parts) if parts else "0s"
    except:
        return "Unknown"

@Client.on_message(filters.command("info", prefixes=".") & filters.me)
async def info_handler(client: Client, message: Message):
    await message.edit("<b>🔄 Gathering info...</b>")
    
    # Git Info
    version, commit, branch, up_status = await get_git_info()
    
    # System Info
    process = psutil.Process(os.getpid())
    cpu_usage = psutil.cpu_percent()
    memory_usage = process.memory_info().rss / 1024 / 1024 # MB
    
    # Settings
    owner = f"{message.from_user.first_name}"
    if message.from_user.username:
        owner += f" | @{message.from_user.username}"
    prefix = "." # Assuming default, strictly we should check client.command_prefixes but '.' is standard for userbots
    
    # Formatting
    uptime = get_uptime()
    
    msg = f"""<b>😎 Owner:</b> {owner}

<b>💫 Version:</b> {version} #{commit}
<b>🌳 Branch:</b> {branch}
<b>😌 Status:</b> {up_status}

<b>⌨️ Prefix:</b> «{prefix}»
<b>⌛️ Uptime:</b> {uptime}

<b>⚡️ CPU usage:</b> ~{cpu_usage}%
<b>💼 RAM usage:</b> ~{memory_usage:.1f} MB"""

    await message.edit(msg)
