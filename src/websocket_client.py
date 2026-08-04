import json
import ssl
import time
import websocket
from PySide6.QtCore import QThread, Signal

from src.utils import is_mattermost_app_open

class MattermostWSThread(QThread):
    # Signals for Qt UI thread
    emergency_received = Signal(dict)
    connection_changed = Signal(bool, str)

    def __init__(self, config_manager, api_client=None, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self.api_client = api_client
        self.running = True
        self.ws = None
        self.seq = 1

    def stop(self):
        self.running = False
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
        self.wait(2000)

    def run(self):
        retry_delay = 2
        max_delay = 30

        while self.running:
            ws_url = self.config.ws_url
            token = self.config.get_active_token()

            if not token:
                self.connection_changed.emit(False, "Token yok! config.json dosyasına PAT veya Kullanıcı Adı/Şifre ekleyin.")
                time.sleep(5)
                continue

            self.connection_changed.emit(False, f"Bağlanılıyor: {ws_url}...")

            headers = [
                f"Authorization: Bearer {token}"
            ]

            try:
                self.ws = websocket.WebSocket(
                    sslopt={"cert_reqs": ssl.CERT_NONE, "check_hostname": False}
                )
                self.ws.connect(ws_url, header=headers, timeout=10)
                
                # Send auth challenge just in case
                auth_payload = {
                    "seq": self.seq,
                    "action": "authentication_challenge",
                    "data": {
                        "token": token
                    }
                }
                self.seq += 1
                self.ws.send(json.dumps(auth_payload))

                self.connection_changed.emit(True, "Mattermost Server'a Bağlandı")
                retry_delay = 2  # reset delay on success connection

                # Ensure current user info is fetched so we can filter self-messages
                if self.api_client and not self.api_client.user_info:
                    try:
                        self.api_client.fetch_me()
                    except Exception:
                        pass

                while self.running:
                    try:
                        raw_msg = self.ws.recv()
                        if not raw_msg:
                            break

                        event_data = json.loads(raw_msg)
                        self.handle_event(event_data)

                    except websocket.WebSocketTimeoutException:
                        # Send ping to keep-alive
                        ping_payload = {"seq": self.seq, "action": "ping"}
                        self.seq += 1
                        self.ws.send(json.dumps(ping_payload))
                    except Exception as e:
                        print(f"[WS Loop Error] {e}")
                        break

            except Exception as e:
                self.connection_changed.emit(False, f"Bağlantı Hatası: {e}")
                print(f"[WS Connection Error] {e}")

            if self.running:
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 1.5, max_delay)

    def is_acil_message(self, text):
        if not text:
            return False

        # 1. Check JSON payload
        if text.startswith("{") and text.endswith("}"):
            try:
                jdata = json.loads(text)
                if isinstance(jdata, dict) and ("priority" in jdata or "message" in jdata or "title" in jdata):
                    return True
            except Exception:
                pass

        # 2. Check trigger keywords (case-insensitive)
        prefixes = self.config.get("trigger_prefixes", ["/acil", "[ACIL]", "acil", "ACİL", "Acil"])
        lower_text = text.lower()
        for prefix in prefixes:
            if prefix.lower() in lower_text:
                return True
        return False

    def handle_event(self, data):
        if not isinstance(data, dict):
            return

        event_name = data.get("event")
        if event_name != "posted":
            return

        event_body = data.get("data", {})
        post_json_str = event_body.get("post")
        if not post_json_str:
            return

        try:
            post_data = json.loads(post_json_str)
        except Exception:
            return

        message_text = post_data.get("message", "").strip()
        sender_id = post_data.get("user_id", "")
        sender_name = event_body.get("sender_name", "") or post_data.get("props", {}).get("override_username", "Bilinmeyen Gönderici")
        channel_name = event_body.get("channel_display_name", "") or event_body.get("channel_name", "Genel Channel")
        channel_id = post_data.get("channel_id", "")
        post_id = post_data.get("id", "")

        # Check channel filter
        allowed_channels = self.config.get("channels", ["*"])
        if "*" not in allowed_channels and channel_id not in allowed_channels and channel_name not in allowed_channels:
            return

        # Ignore messages sent by self
        my_id = None
        if self.api_client and self.api_client.user_info:
            my_id = self.api_client.user_info.get("id")
        if my_id and sender_id == my_id:
            return

        # Check if Mattermost app is open on PC or user is online/away
        app_is_open = is_mattermost_app_open(self.api_client, my_id)
        has_acil = self.is_acil_message(message_text)

        # RULE:
        # If app is open (online/away/process running): trigger popup ONLY if message has "acil"
        # If app is closed (offline & process not running): ALWAYS trigger popup for any incoming message
        if app_is_open and not has_acil:
            print(f"[WS] Mattermost app is OPEN/active (online/away), skipping non-acil message: '{message_text[:30]}...'")
            return

        parsed_payload = self.parse_message_payload(message_text, sender_name, channel_name, has_acil)
        if parsed_payload:
            parsed_payload["post_id"] = post_id
            parsed_payload["channel_id"] = channel_id
            parsed_payload["sender_id"] = sender_id
            print(f"[WS] Popup Triggered! (App Open: {app_is_open}, Has Acil: {has_acil}) Payload: {parsed_payload}")
            self.emergency_received.emit(parsed_payload)


    def parse_message_payload(self, text, sender_name, channel_name, has_acil):
        if not text:
            return None

        # 1. Try parsing JSON format
        if text.startswith("{") and text.endswith("}"):
            try:
                jdata = json.loads(text)
                if isinstance(jdata, dict):
                    return {
                        "priority": jdata.get("priority", "critical" if has_acil else "normal").lower(),
                        "title": jdata.get("title", "🚨 ACİL DURUM BİLDİRİMİ" if has_acil else "💬 YENİ MESAJ BİLDİRİMİ"),
                        "message": jdata.get("message", text),
                        "sender": jdata.get("sender", sender_name),
                        "channel": channel_name,
                        "raw_text": text,
                        "has_acil": has_acil
                    }
            except Exception:
                pass

        if has_acil:
            priority = "critical"
            upper_text = text.upper()
            if "AFET" in upper_text or "DISASTER" in upper_text or "YANGIN" in upper_text:
                priority = "disaster"
            elif "UYARI" in upper_text or "WARNING" in upper_text:
                priority = "warning"

            title = "🚨 ACİL DURUM BİLDİRİMİ"
            clean_msg = text

            prefixes = self.config.get("trigger_prefixes", ["/acil", "[ACIL]", "acil", "ACİL", "Acil"])
            for prefix in prefixes:
                if clean_msg.lower().startswith(prefix.lower()):
                    clean_msg = clean_msg[len(prefix):].strip()
                    break

            if clean_msg.startswith("[") and "]" in clean_msg:
                idx = clean_msg.find("]")
                title = f"🚨 {clean_msg[1:idx].strip()}"
                clean_msg = clean_msg[idx+1:].strip()
            elif ":" in clean_msg and len(clean_msg.split(":", 1)[0]) < 30:
                parts = clean_msg.split(":", 1)
                title = f"🚨 {parts[0].strip()}"
                clean_msg = parts[1].strip()

            if not clean_msg:
                clean_msg = text

            return {
                "priority": priority,
                "title": title,
                "message": clean_msg,
                "sender": sender_name,
                "channel": channel_name,
                "raw_text": text,
                "has_acil": True
            }
        else:
            return {
                "priority": "normal",
                "title": "💬 YENİ MESAJ BİLDİRİMİ",
                "message": text,
                "sender": sender_name,
                "channel": channel_name,
                "raw_text": text,
                "has_acil": False
            }

