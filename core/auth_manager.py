import json
import os

DB_PATH = "data/authorized.json"

class AuthManager:
    def __init__(self):
        self.data = {"users": [], "chats": [], "blacklist": []}
        self._load()

    def _load(self):
        if os.path.exists(DB_PATH):
            try:
                with open(DB_PATH, "r") as f:
                    self.data = json.load(f)
                    if "blacklist" not in self.data:
                        self.data["blacklist"] = []
            except:
                pass
        else:
            os.makedirs("data", exist_ok=True)
            self._save()

    def _save(self):
        with open(DB_PATH, "w") as f:
            json.dump(self.data, f, indent=4)

    def is_authorized(self, user_id, chat_id):
        # Blacklisted users are NEVER authorized
        if user_id in self.data.get("blacklist", []):
            return False
        return user_id in self.data["users"] or chat_id in self.data["chats"]

    def is_blacklisted(self, user_id):
        return user_id in self.data.get("blacklist", [])

    def ban_user(self, user_id):
        if user_id not in self.data["blacklist"]:
            # Remove from authorized if they were there
            self.unauth_user(user_id)
            self.data["blacklist"].append(user_id)
            self._save()
            return True
        return False

    def unban_user(self, user_id):
        if user_id in self.data["blacklist"]:
            self.data["blacklist"].remove(user_id)
            self._save()
            return True
        return False

    def auth_user(self, user_id):
        if user_id not in self.data["users"]:
            self.data["users"].append(user_id)
            self._save()
            return True
        return False

    def unauth_user(self, user_id):
        if user_id in self.data["users"]:
            self.data["users"].remove(user_id)
            self._save()
            return True
        return False

    def auth_chat(self, chat_id):
        if chat_id not in self.data["chats"]:
            self.data["chats"].append(chat_id)
            self._save()
            return True
        return False

    def unauth_chat(self, chat_id):
        if chat_id in self.data["chats"]:
            self.data["chats"].remove(chat_id)
            self._save()
            return True
        return False

auth_manager = AuthManager()
