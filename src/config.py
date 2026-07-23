import json
import os
from src.utils import get_resource_path

DEFAULT_CONFIG = {
    "server_url": "https://mattermost.company.com",
    "pat_token": "YOUR_PERSONAL_ACCESS_TOKEN_HERE",
    "username": "",
    "password": "",
    "trigger_prefixes": ["/acil", "[ACIL]", "[URGENT]", "[EMERGENCY]", "acil", "ACIL"],
    "channels": ["*"],
    "audio_enabled": True,
    "audio_loop": True,
    "auto_post_ack": True,
    "ack_message_template": "✅ **{user_display_name}** ({username}) acil uyarısını okudu/onayladı: **{title}**",
    "window_always_on_top": True,
    "disable_esc_key": True,
    "fullscreen_for_critical": False,
    "sound_files": {
        "normal": "sounds/ding.wav",
        "warning": "sounds/warning.wav",
        "critical": "sounds/siren.wav",
        "disaster": "sounds/airraid.wav"
    }
}

class ConfigManager:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.data = self.load_config()

    def load_config(self):
        target_path = self.config_path
        if not os.path.exists(target_path):
            target_path = get_resource_path(self.config_path)

        if not os.path.exists(target_path):
            self.save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                merged = DEFAULT_CONFIG.copy()
                merged.update(loaded)
                return merged
        except Exception as e:
            print(f"Error loading config file '{target_path}': {e}. Using defaults.")
            return DEFAULT_CONFIG.copy()

    def save_config(self, data=None):
        if data is None:
            data = self.data
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.data = data
        except Exception as e:
            print(f"Error saving config file: {e}")

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save_config()

    @property
    def ws_url(self):
        url = self.data.get("server_url", "").rstrip("/")
        if url.startswith("https://"):
            ws_base = "wss://" + url[8:]
        elif url.startswith("http://"):
            ws_base = "ws://" + url[7:]
        else:
            ws_base = "wss://" + url
        return f"{ws_base}/api/v4/websocket"

    @property
    def rest_url(self):
        url = self.data.get("server_url", "").rstrip("/")
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        return f"{url}/api/v4"

    def get_active_token(self):
        pat_token = self.get("pat_token", "")
        if pat_token and pat_token != "YOUR_PERSONAL_ACCESS_TOKEN_HERE":
            return pat_token

        username = self.get("username", "")
        password = self.get("password", "")
        if username and password:
            if hasattr(self, "_cached_token") and self._cached_token:
                return self._cached_token
            url = f"{self.rest_url}/users/login"
            payload = {"login_id": username, "password": password}
            try:
                import requests
                import urllib3
                urllib3.disable_warnings()
                res = requests.post(url, json=payload, timeout=10, verify=False)
                if res.status_code == 200:
                    token = res.headers.get("Token")
                    if token:
                        self._cached_token = token
                        print("[Config] Authenticated via Username/Password successfully!")
                        return token
                print(f"[Config Error] Username/Password login failed: {res.status_code}")
            except Exception as e:
                print(f"[Config Exception] Login error: {e}")

        return ""
