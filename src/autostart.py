import sys
import os

APP_NAME = "MattermostEmergencyClient"

class AutoStartManager:
    """Handles cross-platform application autostart on system boot."""

    @staticmethod
    def get_executable_path():
        if getattr(sys, 'frozen', False):
            # Running as compiled PyInstaller executable
            return os.path.abspath(sys.executable)
        else:
            # Running as python script
            return f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'

    @classmethod
    def is_autostart_enabled(cls):
        if os.name == 'nt':
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0,
                    winreg.KEY_READ
                )
                try:
                    val, _ = winreg.QueryValueEx(key, APP_NAME)
                    winreg.CloseKey(key)
                    return bool(val)
                except FileNotFoundError:
                    winreg.CloseKey(key)
                    return False
            except Exception as e:
                print(f"[Autostart Error] Windows registry check failed: {e}")
                return False
        else:
            # Linux autostart desktop entry check
            desktop_path = os.path.expanduser(f"~/.config/autostart/{APP_NAME}.desktop")
            return os.path.exists(desktop_path)

    @classmethod
    def set_autostart(cls, enable: bool) -> bool:
        exec_path = cls.get_executable_path()

        if os.name == 'nt':
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0,
                    winreg.KEY_ALL_ACCESS
                )
                if enable:
                    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exec_path)
                    print(f"[Autostart] Added Windows Registry entry: {APP_NAME} -> {exec_path}")
                else:
                    try:
                        winreg.DeleteValue(key, APP_NAME)
                        print(f"[Autostart] Removed Windows Registry entry: {APP_NAME}")
                    except FileNotFoundError:
                        pass
                winreg.CloseKey(key)
                return True
            except Exception as e:
                print(f"[Autostart Error] Failed to modify Windows Registry: {e}")
                return False
        else:
            # Linux desktop entry
            autostart_dir = os.path.expanduser("~/.config/autostart")
            desktop_path = os.path.join(autostart_dir, f"{APP_NAME}.desktop")

            if enable:
                os.makedirs(autostart_dir, exist_ok=True)
                content = f"""[Desktop Entry]
Type=Application
Name=Mattermost Emergency Client
Comment=Mattermost Emergency Alert System
Exec={exec_path}
Terminal=false
X-GNOME-Autostart-enabled=true
"""
                try:
                    with open(desktop_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    print(f"[Autostart] Created desktop entry at: {desktop_path}")
                    return True
                except Exception as e:
                    print(f"[Autostart Error] Failed to write desktop entry: {e}")
                    return False
            else:
                if os.path.exists(desktop_path):
                    try:
                        os.remove(desktop_path)
                        print(f"[Autostart] Removed desktop entry: {desktop_path}")
                        return True
                    except Exception as e:
                        print(f"[Autostart Error] Failed to remove desktop entry: {e}")
                        return False
                return True
