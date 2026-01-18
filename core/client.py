import logging
import os
from pyrogram import Client, filters
from typing import Optional

class KuriBot(Client):
    def __init__(
        self,
        name: str = "kuribot",
        api_id: Optional[int] = None,
        api_hash: Optional[str] = None,
        plugins: Optional[dict] = None,
        **kwargs
    ):
        self._logger = logging.getLogger("kuribot.client")
        # Use environment variables if not provided
        api_id = api_id or int(os.getenv("API_ID", 0))
        api_hash = api_hash or os.getenv("API_HASH")
        
        if not api_id or not api_hash:
            raise ValueError("API_ID and API_HASH must be provided in config or env")

        # Disable default plugins to manage them manually via our handler map
        super().__init__(
            name=name,
            api_id=api_id,
            api_hash=api_hash,
            plugins=None,
            **kwargs
        )
        # Map to track handlers: {module_name: [(handler, group), ...]}
        self._handlers_map = {}

    def _get_module_handlers(self, module):
        """Extract handlers from a module, including decorated ones."""
        import pyrogram.handlers
        handlers = []
        for name in dir(module):
            obj = getattr(module, name)
            # Support for Pyrogram decorators (@Client.on_message etc)
            # Most decorated functions store their handlers in a list called 'handlers'
            if hasattr(obj, "handlers") and isinstance(getattr(obj, "handlers"), list):
                for h in getattr(obj, "handlers"):
                    if isinstance(h, (list, tuple)) and len(h) >= 1:
                        handler = h[0]
                        group = h[1] if len(h) > 1 else 0
                        if isinstance(handler, pyrogram.handlers.Handler):
                            handlers.append((handler, group))
            # Support for direct Handler objects
            elif isinstance(obj, pyrogram.handlers.Handler):
                group = getattr(obj, "group", 0)
                handlers.append((obj, group))
        return handlers

    async def load_module(self, module_name: str):
        """Dynamically load or reload a module."""
        import importlib
        full_name = f"modules.{module_name}"
        
        if module_name in self._handlers_map:
            await self.unload_module(module_name)

        try:
            if full_name in importlib.sys.modules:
                module = importlib.reload(importlib.sys.modules[full_name])
            else:
                module = importlib.import_module(full_name)
            
            handlers = self._get_module_handlers(module)
            for handler, group in handlers:
                self.add_handler(handler, group)
            
            self._handlers_map[module_name] = handlers
            return True, len(handlers)
        except Exception as e:
            self._logger.error(f"Failed to load module {module_name}: {e}")
            return False, str(e)

    async def unload_module(self, module_name: str):
        """Dynamically unload a module."""
        if module_name not in self._handlers_map:
            return False, "Module not loaded or not tracked."

        handlers = self._handlers_map.pop(module_name)
        for handler, group in handlers:
            try:
                self.remove_handler(handler, group)
            except Exception as e:
                self._logger.warning(f"Failed to remove a handler from {module_name}: {e}")
        
        return True, len(handlers)

    async def start(self):
        self._logger.info("Starting KuriBot...")
        await super().start()
        
        # Manually load all modules from the modules directory
        if os.path.exists("modules"):
            for file in os.listdir("modules"):
                if file.endswith(".py") and not file.startswith("__"):
                    module_name = file[:-3]
                    success, count = await self.load_module(module_name)
                    if success:
                        self._logger.info(f"Loaded module: {module_name} ({count} handlers)")
                    else:
                        self._logger.error(f"Failed to auto-load {module_name}: {count}")

        me = await self.get_me()
        self._logger.info(f"Bot started as {me.first_name} (@{me.username})")

        # Global command logger
        @self.on_message(filters.me & (filters.text | filters.caption) & filters.regex(r"^\."), group=-100)
        async def cmd_log_handler(_, message):
            chat = message.chat.title or message.chat.first_name or message.chat.id
            text = message.text or message.caption
            self._logger.info(f"[CMD] {text} | Chat: {chat}")

    async def stop(self, *args):
        self._logger.info("Stopping KuriBot...")
        await super().stop()
