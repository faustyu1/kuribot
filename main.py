import asyncio
from dotenv import load_dotenv
from core.client import KuriBot
from core.logger import setup_logging
import os

# Load environment variables
load_dotenv()

# Setup professional logging
logger = setup_logging()

async def main():
    # Make sure modules directory exists
    if not os.path.exists("modules"):
        os.makedirs("modules")
        # Create an empty __init__.py in modules
        with open("modules/__init__.py", "w") as f:
            pass

    bot = KuriBot()
    
    try:
        await bot.start()
        # Keep the bot running
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        await bot.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
