import requests
import urllib3

# Suppress insecure HTTPS request warnings if self-signed SSL is used
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class MattermostApiClient:
    def __init__(self, config_manager):
        self.config = config_manager
        self.user_info = None

    def get_headers(self):
        token = self.config.get_active_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def fetch_me(self):
        """Fetch current logged-in user profile from Mattermost REST API."""
        url = f"{self.config.rest_url}/users/me"
        try:
            res = requests.get(url, headers=self.get_headers(), timeout=10, verify=False)
            if res.status_code == 200:
                self.user_info = res.json()
                print(f"[API] Connected as user/bot: {self.user_info.get('username')}")
                return self.user_info
            else:
                print(f"[API Error] Failed to fetch user profile: {res.status_code} {res.text}")
        except Exception as e:
            print(f"[API Exception] fetch_me failed: {e}")
        return None

    def post_ack(self, channel_id, post_id, alert_title, alert_message):
        """Send acknowledgment message to the channel as a reply or new post."""
        if not self.config.get("auto_post_ack", True):
            return True

        if not self.user_info:
            self.fetch_me()

        user_display = "Kullanıcı"
        username = "kullanici"
        if self.user_info:
            first_name = self.user_info.get("first_name", "")
            last_name = self.user_info.get("last_name", "")
            username = self.user_info.get("username", "user")
            if first_name or last_name:
                user_display = f"{first_name} {last_name}".strip()
            else:
                user_display = username

        template = self.config.get(
            "ack_message_template",
            "✅ **{user_display_name}** ({username}) acil uyarısını okudu/onayladı: **{title}**"
        )
        msg = template.format(
            user_display_name=user_display,
            username=username,
            title=alert_title or "Acil Durum Mesajı",
            message=alert_message or ""
        )

        url = f"{self.config.rest_url}/posts"
        payload = {
            "channel_id": channel_id,
            "message": msg,
            "root_id": post_id  # Reply to thread if post_id is provided
        }

        try:
            res = requests.post(url, json=payload, headers=self.get_headers(), timeout=10, verify=False)
            if res.status_code in (200, 201):
                print(f"[API] Sent ACK post successfully to channel {channel_id}")
                return True
            else:
                print(f"[API Error] Failed to send ACK post: {res.status_code} {res.text}")
        except Exception as e:
            print(f"[API Exception] post_ack failed: {e}")
        return False
