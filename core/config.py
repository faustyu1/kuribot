import json
import os
from typing import Any

class ConfigManager:
    def __init__(self, filename: str = "data/config.json"):
        self.filename = filename
        self._ensure_dir()
        self.config = self._load()

    def _ensure_dir(self):
        folder = os.path.dirname(self.filename)
        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)

    def _load(self) -> dict:
        if not os.path.exists(self.filename):
            return {}
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save(self):
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4)

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        self.config[key] = value
        self._save()

    def delete(self, key: str):
        if key in self.config:
            del self.config[key]
            self._save()

    def all(self) -> dict:
        return self.config

# Global instance
config = ConfigManager()
