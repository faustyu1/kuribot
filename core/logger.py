import logging
import sys
from rich.logging import RichHandler
from rich.console import Console
from logging.handlers import RotatingFileHandler
import os

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

    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        datefmt="[%X]",
        handlers=[rich_handler, file_handler]
    )

    # Specific levels for some libraries to avoid spam
    logging.getLogger("pyrogram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)

    return logging.getLogger("kuribot")
