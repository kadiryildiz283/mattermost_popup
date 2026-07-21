import sys
import os
from PySide6.QtWidgets import QApplication

from src.config import ConfigManager
from src.api_client import MattermostApiClient
from src.sound_manager import SoundManager
from src.websocket_client import MattermostWSThread
from src.ui.emergency_window import EmergencyWindow
from src.ui.system_tray import SystemTrayApp
from src.autostart import AutoStartManager
from audio_generator import generate_all_sounds

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Mattermost Emergency Client")

    # Ensure sound files exist
    if not os.path.exists("sounds/siren.wav"):
        print("[Main] Sound files missing. Generating default WAV sounds...")
        generate_all_sounds()

    # Load Configuration
    config = ConfigManager("config.json")

    # Sync Autostart setting if configured in config.json
    if config.get("autostart_enabled", False):
        AutoStartManager.set_autostart(True)

    # Initialize Services
    sound_mgr = SoundManager(config)
    api_client = MattermostApiClient(config)

    # Initialize UI Window & System Tray
    window = EmergencyWindow(config, sound_mgr, api_client)
    tray = SystemTrayApp(config)

    # Initialize WebSocket Listener Thread
    ws_thread = MattermostWSThread(config)

    # Connect Signals
    ws_thread.emergency_received.connect(window.display_alert)
    ws_thread.connection_changed.connect(tray.set_connection_status)

    def trigger_test_alert():
        test_payload = {
            "priority": "critical",
            "title": "🚨 TEST ACİL DURUM ALARMI",
            "message": "Bu bir sistem test uyarısıdır.\n\nSunucu Odası: Duman ve yüksek sıcaklık algılandı!\n\nLütfen 'OKUDUM' butonuna basarak uyarının onaylandığını bildirin.",
            "sender": "Sistem Yöneticisi (Test)",
            "channel": "acil-duyuru",
            "channel_id": "test_channel_123",
            "post_id": "test_post_456"
        }
        window.display_alert(test_payload)

    def restart_ws():
        ws_thread.stop()
        ws_thread.start()

    tray.test_alert_requested.connect(trigger_test_alert)
    tray.reconnect_requested.connect(restart_ws)
    tray.quit_requested.connect(ws_thread.stop)

    # Start WebSocket Thread
    ws_thread.start()

    # Handle --test flag
    if "--test" in sys.argv:
        trigger_test_alert()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
