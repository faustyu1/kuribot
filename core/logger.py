import logging
import sys
import os
import asyncio
import html
from rich.logging import RichHandler
from rich.console import Console
from logging.handlers import RotatingFileHandler
import time

class TelegramLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.buffer = []
        self.last_msg_id = None
        self.last_msg_text = ""
        self.last_msg_time = 0
        self._lock = asyncio.Lock()

    def format_log(self, record):
        name = html.escape(record.name)
        msg = html.escape(record.getMessage())
        level = record.levelname
        emoji = "ℹ️"
        if level == "WARNING": emoji = "⚠️"
        elif level == "ERROR": emoji = "❌"
        elif level == "CRITICAL": emoji = "🚫"
        
        return f"{emoji} <code>{name}</code> — {msg}"

    async def _flush_buffer(self):
        from core.assistant import get_assistant
        from core.config import config
        
        assistant = get_assistant()
        chat_id = config.get("log_group_id")
        if not assistant or not chat_id: return

        async with self._lock:
            if not self.buffer: return
            
            new_logs_raw = "\n".join(self.buffer)
            self.buffer = []
            
            now = time.time()
            
            # Check if we can edit the last message
            can_edit = (
                self.last_msg_id is not None and 
                (now - self.last_msg_time < 300) and 
                (len(self.last_msg_text) + len(new_logs_raw) < 3800)
            )

            if can_edit:
                updated_text = self.last_msg_text + "\n" + new_logs_raw
                full_content = f"<b>🪵 Логи KuriBot:</b>\n<blockquote>{updated_text}</blockquote>"
                
                if await assistant.edit_log(chat_id, self.last_msg_id, full_content):
                    self.last_msg_text = updated_text
                    self.last_msg_time = now
                    return
                # If edit failed (e.g. message deleted), fall through to send a new one

            # Send a new message
            self.last_msg_text = new_logs_raw
            self.last_msg_time = now
            full_content = f"<b>🪵 Логи KuriBot:</b>\n<blockquote>{self.last_msg_text}</blockquote>"
            
            msg = await assistant.send_log(chat_id, full_content)
            if msg:
                self.last_msg_id = msg.message_id

    def emit(self, record):
        from core.config import config
        
        # Check filtered levels from config (default to INFO)
        min_level = config.get("tg_log_level", "INFO")
        try:
            if record.levelno < logging.getLevelName(min_level.upper()):
                return
        except:
            if record.levelno < logging.INFO: return

        formatted = self.format_log(record)
        
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_running(): return
        except RuntimeError:
            return

        self.buffer.append(formatted)
        
        # Schedule flush if not already scheduled
        if len(self.buffer) == 1:
            loop.call_later(1.5, lambda: asyncio.ensure_future(self._flush_buffer()))

def setup_logging():
    # Create logs directory if it doesn't exist
    if not os.path.exists("logs"):
        os.makedirs("logs")

    # Base format
    LOG_FORMAT = "%(name)s: %(message)s"
    FILE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Console with Rich
    console = Console()
    rich_handler = RichHandler(
        console=console,
        rich_tracebacks=True,
        markup=True,
        show_path=False
    )

    # File handler with rotation
    file_handler = RotatingFileHandler(
        filename="logs/kuribot.log",
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(FILE_FORMAT))

    # Telegram logger
    tg_handler = TelegramLogHandler()

    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        datefmt="[%X]",
        handlers=[rich_handler, file_handler, tg_handler]
    )

    # Specific levels for some libraries to avoid spam
    logging.getLogger("pyrogram").setLevel(logging.ERROR)
    logging.getLogger("aiohttp").setLevel(logging.ERROR)
    logging.getLogger("aiogram").setLevel(logging.ERROR)
    logging.getLogger("aiogram.dispatcher").setLevel(logging.ERROR)

    return logging.getLogger("kuribot")
