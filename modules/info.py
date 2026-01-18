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

_GIT_CACHE = None
_LAST_GIT_CHECK = 0
CACHE_TIME = 60000 # 10 minutes

async def get_git_info():
    global _GIT_CACHE, _LAST_GIT_CHECK
    now = time.time()
    
    if _GIT_CACHE and (now - _LAST_GIT_CHECK < CACHE_TIME):
        return _GIT_CACHE

    try:
        # Get hash
        commit_hash = await get_cmd_output(["git", "rev-parse", "--short", "HEAD"])
        # Get branch
        branch = await get_cmd_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        # Get version (tag)
        version = await get_cmd_output(["git", "describe", "--tags"])
        if not version: version = "1.0.0"
        
        # Check updates (silent fetch)
        await get_cmd_output(["git", "fetch"])
        status = await get_cmd_output(["git", "status", "-uno"])
        
        if "Your branch is up to date" in status:
            update_status = "Up-to-date"
        elif "Your branch is ahead" in status:
            update_status = "Ahead" 
        else:
            update_status = "Update available"
            
        # Get remote URL
        remote = await get_cmd_output(["git", "remote", "get-url", "origin"])
        if "github.com" in remote:
            # Handle both https and ssh formats
            if "@" in remote: # SSH
                remote = remote.split(":")[-1].replace(".git", "")
            else: # HTTPS
                remote = remote.split("github.com/")[1].replace(".git", "")
        else:
            remote = "Local"
            
        _GIT_CACHE = (version, commit_hash, branch, update_status, remote)
        _LAST_GIT_CHECK = now
        return _GIT_CACHE
    except Exception:
        return "Unknown", "??????", "Unknown", "Unknown", "Unknown"

def get_uptime():
    try:
        p = psutil.Process(os.getpid())
        uptime_seconds = time.time() - p.create_time()
        m, s = divmod(uptime_seconds, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        
        parts = []
        if d > 0: parts.append(f"{int(d)}")
        if h > 0: parts.append(f"{int(h)}")
        if m > 0: parts.append(f"{int(m)}")
        if s > 0: parts.append(f"{int(s)}")
        
        return ":".join(parts) if parts else "0s"
    except:
        return "Unknown"

@Client.on_message(filters.command("info", prefixes=".") & filters.me)
async def info_handler(client: Client, message: Message):
    await message.edit("<b>🔄 Gathering info...</b>")
    
    # Git Info
    version, commit, branch, up_status, remote = await get_git_info()
    
    # System Info
    process = psutil.Process(os.getpid())
    cpu_usage = psutil.cpu_percent()
    memory_usage = process.memory_info().rss / 1024 / 1024 # MB
    
    # Settings
    owner = f"{message.from_user.first_name}"
    if message.from_user.username:
        owner += f" | @{message.from_user.username}"
    repo_name = remote if remote != "Unknown" else "faustyu1/kuribot"
    prefix = "." # Assuming default, strictly we should check client.command_prefixes but '.' is standard for userbots
    
    # Formatting
    uptime = get_uptime()
    
    # Version Link
    version_display = f"{version} <a href='https://github.com/{repo_name}'>#{commit}</a>" if "/" in repo_name else f"{version} #{commit}"
    
    msg = f"""<b>😎 Owner:</b> {owner}

<b>💫 Version:</b> {version_display}
<b>🌳 Branch:</b> {branch}
<b>😌 Status:</b> {up_status}

<b>⌨️ Prefix:</b> «{prefix}»
<b>⌛️ Uptime:</b> {uptime}

<b>⚡️ CPU usage:</b> ~{cpu_usage}%
<b>💼 RAM usage:</b> ~{memory_usage:.1f} MB"""

    await message.edit(msg, disable_web_page_preview=True)
