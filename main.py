import asyncio
import os
import logging
from dotenv import load_dotenv
from core.client import KuriBot
from core.assistant import init_assistant
from core.logger import setup_logging

# Load environment variables
load_dotenv()

# Setup professional logging
logger = setup_logging()

from core.config import config

async def setup_log_group(userbot: KuriBot, assistant):
    log_group_id = config.get("log_group_id")
    
    # Try to verify if group still exists
    if log_group_id:
        try:
            await userbot.get_chat(log_group_id)
            logger.info(f"Log group found: {log_group_id}")
        except:
            logger.warning("Saved log group not found, creating new one...")
            log_group_id = None

    if not log_group_id:
        try:
            group = await userbot.create_supergroup("KuriBot Logs", "Group for bot logs and security events")
            log_group_id = group.id
            config.set("log_group_id", log_group_id)
            logger.info(f"Created new log group: {log_group_id}")
        except Exception as e:
            logger.error(f"Failed to create log group: {e}")
            return

    # Add assistant bot if not there
    if assistant:
        bot_info = await assistant.get_me()
        try:
            # Resolve the bot peer first so the userbot "knows" it
            await userbot.get_users(bot_info.username)
            
            await userbot.add_chat_members(log_group_id, bot_info.id)
            from pyrogram.types import ChatPrivileges
            await userbot.promote_chat_member(
                log_group_id, 
                bot_info.id,
                privileges=ChatPrivileges(
                    can_delete_messages=True,
                    can_invite_users=True,
                    can_restrict_members=True,
                    can_pin_messages=True,
                    can_promote_members=False,
                    can_manage_chat=True,
                    can_change_info=False
                )
            )
            logger.info("Assistant bot added and promoted in log group.")
            await assistant.send_log(log_group_id, "🚀 **KuriBot запущен!**\nЛоги теперь будут приходить сюда.")
        except Exception as e:
            if "USER_ALREADY_PARTICIPANT" not in str(e):
                logger.error(f"Failed to add assistant to log group: {e}")

async def main():
    # Make sure modules directory exists
    if not os.path.exists("modules"):
        os.makedirs("modules")
        if not os.path.exists("modules/__init__.py"):
            with open("modules/__init__.py", "w") as f:
                pass

    userbot = KuriBot()
    assistant = None
    bot_token = os.getenv("BOT_TOKEN")
    
    if bot_token:
        assistant = init_assistant(bot_token)
    
    # Start bots
    await userbot.start()
    
    # Save owner ID for assistant bot security
    me = await userbot.get_me()
    config.set("owner_id", me.id)
    logger.info(f"Owner ID {me.id} saved to config.")
    if assistant:
        # Start assistant in background
        asyncio.create_task(assistant.start())
        logger.info("Assistant bot started.")

    # Setup log group
    await setup_log_group(userbot, assistant)

    try:
        # Keep running
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down...")
        await userbot.stop()
        if assistant:
            await assistant.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
