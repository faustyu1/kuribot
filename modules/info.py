# meta developer: @faustyu
# meta description: Информация о системе и юзерботе

import os
import time
import psutil
import platform
import sys
from pyrogram import filters, Client, __version__ as pyro_version
from pyrogram.types import Message, LinkPreviewOptions
from core.config import config
from core.utils import get_cmd_output, get_uptime

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


@Client.on_message(filters.command("info", prefixes=config.get("prefix", ".")) & filters.me)
async def info_handler(client: Client, message: Message):
    # Retrieve banner from config
    banner = config.get("info_banner")
    
    # If using banner, we might need to delete original message and send new one
    # If no banner, we modify existing
    
    if not banner:
        await message.edit("<b>🔄 Gathering info...</b>")
    
    # Git Info
    version, commit, branch, up_status, remote = await get_git_info()
    
    # System Info
    process = psutil.Process(os.getpid())
    cpu_usage = psutil.cpu_percent()
    memory_usage = process.memory_info().rss / 1024 / 1024 # MB
    
    # Platform Info
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    os_info = f"{platform.system()} {platform.release()}"
    
    # Settings
    owner = f"{message.from_user.first_name}"
    if message.from_user.username:
        owner += f" | @{message.from_user.username}"
    repo_name = remote if remote != "Unknown" else "faustyu1/kuribot"
    
    # Formatting
    uptime = get_uptime()
    
    # Version Link
    version_display = f"<a href='https://github.com/{repo_name}'>Kuribot {version}</a>"
    
    msg = f"""<b>👾 {version_display}</b>
    
<b>😎 Owner:</b> {owner}
<b>⏳ Uptime:</b> {uptime}
<b>🌲 Branch:</b> {branch} ({commit})

<b>📊 Stats:</b>
• <b>CPU:</b> {cpu_usage}%
• <b>RAM:</b> {memory_usage:.1f} MB
"""

    if banner:
        try:
            # Prepare reply parameters
            reply_to = message.reply_to_message.id if message.reply_to_message else None
            
            # Delete the command message
            await message.delete()
            
            # Send with banner
            if banner.endswith((".mp4", ".gif")):
                 await client.send_animation(message.chat.id, banner, caption=msg, reply_to_message_id=reply_to)
            else:
                try:
                    await client.send_photo(message.chat.id, banner, caption=msg, reply_to_message_id=reply_to)
                except Exception as e:
                    # Fallback for file_ids that are not photos
                    err_str = str(e).upper()
                    if "ANIMATION" in err_str:
                        await client.send_animation(message.chat.id, banner, caption=msg, reply_to_message_id=reply_to)
                    elif "VIDEO" in err_str:
                        await client.send_video(message.chat.id, banner, caption=msg, reply_to_message_id=reply_to)
                    else:
                        raise e
        except Exception as e:
            # Fallback if banner fails
            await client.send_message(message.chat.id, f"{msg}\n\n<i>⚠️ Failed to load banner: {e}</i>")
    else:
        await message.edit(msg, link_preview_options=LinkPreviewOptions(is_disabled=True))

@Client.on_message(filters.command("setbanner", prefixes=config.get("prefix", ".")) & filters.me)
async def set_banner_handler(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.edit("<b>⚠️ Reply to a photo or GIF to set it as banner!</b>")
        
    media = message.reply_to_message.photo or message.reply_to_message.animation or message.reply_to_message.video
    
    if not media:
        return await message.edit("<b>⚠️ Please reply to a valid photo or animation.</b>")
    
    file_id = media.file_id
    config.set("info_banner", file_id)
    await message.edit("<b>✅ Banner updated!</b> Try <code>.info</code>")

@Client.on_message(filters.command("delbanner", prefixes=config.get("prefix", ".")) & filters.me)
async def del_banner_handler(client: Client, message: Message):
    config.delete("info_banner")
    await message.edit("<b>🗑 Banner removed!</b>")
