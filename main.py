import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from PySide6.QtCore import QLockFile, QDir
from src.config import ConfigManager, get_app_dir
from src.utils import get_resource_path
from src.api_client import MattermostApiClient
from src.sound_manager import SoundManager
from src.websocket_client import MattermostWSThread
from src.ui.emergency_window import EmergencyWindow
from src.ui.tray_banner import AppleTrayBanner
from src.ui.system_tray import SystemTrayApp
from src.autostart import AutoStartManager
from audio_generator import generate_all_sounds

def main():
    # Ensure current working directory is set to app root directory
    app_dir = get_app_dir()
    if app_dir and os.path.exists(app_dir):
        try:
            os.chdir(app_dir)
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Mattermost Emergency Client")

    # Single Instance Guard using QLockFile
    lock_path = os.path.join(QDir.tempPath(), "mattermost_emergency_client.lock")
    lock_file = QLockFile(lock_path)
    lock_file.setStaleLockTime(0)
    if not lock_file.tryLock(100):
        print("[Main] Application is already running in background. Exiting duplicate instance.")
        sys.exit(0)

    ico_path = get_resource_path("app.ico")
    if os.path.exists(ico_path):
        app.setWindowIcon(QIcon(ico_path))

    # Ensure default sound files exist
    siren_path = get_resource_path("sounds/siren.wav")
    if not os.path.exists(siren_path):
        print("[Main] Sound files missing. Generating default WAV sounds...")
        generate_all_sounds()

    # Load Configuration
    config = ConfigManager("config.json")

    # Automatically register autostart (Task Scheduler if Admin during setup, HKCU Registry/Startup shortcut for Standard Users)
    AutoStartManager.set_autostart(True)

    # Initialize Services
    sound_mgr = SoundManager(config)
    api_client = MattermostApiClient(config)

    # Initialize Both UI Windows (Central Apple Modal + Small Bottom-Right Persistent Tray Banner)
    central_window = EmergencyWindow(config, sound_mgr, api_client)
    tray_banner = AppleTrayBanner(config, sound_mgr)
    tray = SystemTrayApp(config)

    # Initialize WebSocket Listener Thread
    ws_thread = MattermostWSThread(config, api_client=api_client)

    # Alert Routing Logic based on User/App state
    def handle_incoming_alert(payload):
        is_app_open = payload.get("is_app_open", False)
        if is_app_open:
            print("[Main Router] App is OPEN/Active -> Displaying small persistent bottom-right Apple popup.")
            tray_banner.display_alert(payload)
        else:
            print("[Main Router] App is CLOSED/Inactive -> Displaying central Apple modal popup.")
            central_window.display_alert(payload)

    # Connect WebSocket Signals
    ws_thread.emergency_received.connect(handle_incoming_alert)
    ws_thread.connection_changed.connect(tray.set_connection_status)

    def trigger_test_alert():
        test_payload = {
            "priority": "critical",
            "title": "🚨 TEST ACİL DURUM ALARMI",
            "message": "Bu bir sistem test uyarısıdır.\n\nSunucu Odası: Duman ve yüksek sıcaklık algılandı!\n\nLütfen uyarının onaylandığını bildirin.",
            "sender": "Sistem Yöneticisi (Test)",
            "channel": "acil-duyuru",
            "channel_id": "test_channel_123",
            "post_id": "test_post_456",
            "has_acil": True,
            "is_app_open": False
        }
        handle_incoming_alert(test_payload)

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
