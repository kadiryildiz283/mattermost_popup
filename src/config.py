import json
import os
import sys
from src.utils import get_resource_path

def get_app_dir():
    """Get absolute directory of executable or script."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(sys.argv[0]))

def get_user_config_path(filename="config.json"):
    """
    Get absolute path for config.json.
    First tries executable directory. If write-protected (PermissionError), uses AppData directory.
    """
    app_dir = get_app_dir()
    primary_path = os.path.join(app_dir, filename)

    if os.path.exists(primary_path):
        return primary_path

    # Try creating/writing to test file in app_dir to test permissions
    try:
        test_file = os.path.join(app_dir, ".perm_test")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        return primary_path
    except (PermissionError, OSError):
        appdata = os.environ.get("APPDATA") or os.path.expanduser("~/.config")
        user_dir = os.path.join(appdata, "MattermostEmergencyClient")
        os.makedirs(user_dir, exist_ok=True)
        return os.path.join(user_dir, filename)

DEFAULT_CONFIG = {
    "server_url": "https://mattermost.company.com",
    "pat_token": "YOUR_PERSONAL_ACCESS_TOKEN_HERE",
    "username": "",
    "password": "",
    "trigger_prefixes": ["/acil", "[ACIL]", "[URGENT]", "[EMERGENCY]", "acil", "ACIL"],
    "channels": ["*"],
    "audio_enabled": True,
    "audio_loop": False,
    "auto_post_ack": True,
    "ack_message_template": "✅ **{user_display_name}** ({username}) acil uyarısını okudu/onayladı: **{title}**",
    "window_always_on_top": True,
    "disable_esc_key": True,
    "fullscreen_for_critical": False,
    "sound_files": {
        "normal": "sounds/gentle_chime.wav",
        "warning": "sounds/gentle_alert.wav",
        "critical": "sounds/gentle_alert.wav",
        "disaster": "sounds/gentle_alert.wav"
    }
}

class ConfigManager:
    def __init__(self, config_filename="config.json"):
        if os.path.isabs(config_filename):
            self.config_path = config_filename
        else:
            self.config_path = get_user_config_path(config_filename)

        self.data = self.load_config()

    def load_config(self):
        # 1. Check existing config at self.config_path
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    merged = DEFAULT_CONFIG.copy()
                    merged.update(loaded)
                    return merged
            except Exception as e:
                print(f"Error loading config file '{self.config_path}': {e}. Using defaults.")
                return DEFAULT_CONFIG.copy()

        # 2. Fallback to embedded default template if not created yet
        embedded_path = get_resource_path("config.json")
        if os.path.exists(embedded_path) and embedded_path != self.config_path:
            try:
                with open(embedded_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    merged = DEFAULT_CONFIG.copy()
                    merged.update(loaded)
                    self.save_config(merged)
                    return merged
            except Exception:
                pass

        # 3. Create initial config file
        self.save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    def save_config(self, data=None):
        if data is None:
            data = self.data
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.data = data
            print(f"[Config] Saved config to: {self.config_path}")
        except PermissionError:
            # Fallback to AppData if permission denied
            appdata = os.environ.get("APPDATA") or os.path.expanduser("~/.config")
            user_dir = os.path.join(appdata, "MattermostEmergencyClient")
            os.makedirs(user_dir, exist_ok=True)
            self.config_path = os.path.join(user_dir, "config.json")
            try:
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                self.data = data
                print(f"[Config] Saved config to AppData fallback: {self.config_path}")
            except Exception as ex:
                print(f"Error saving config file to AppData: {ex}")
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
        token = self.get_active_token()
        if url.startswith("https://"):
            ws_base = "wss://" + url[8:]
        elif url.startswith("http://"):
            ws_base = "ws://" + url[7:]
        else:
            ws_base = "wss://" + url
        
        full_url = f"{ws_base}/api/v4/websocket"
        if token:
            full_url += f"?token={token}"
        return full_url

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
