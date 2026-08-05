import sys
import os
import shutil
import subprocess
from src.utils import is_admin

APP_NAME = "MattermostEmergencyClient"

class AutoStartManager:
    """Handles cross-platform application autostart, Task Scheduler admin elevation, and Mattermost shortcut synchronization."""

    @staticmethod
    def get_executable_path():
        if getattr(sys, 'frozen', False):
            path = os.path.abspath(sys.executable)
        else:
            path = os.path.abspath(sys.argv[0])
        return path

    @staticmethod
    def get_windows_startup_folder():
        if os.name == 'nt':
            appdata = os.environ.get("APPDATA")
            if appdata:
                return os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs\Startup")
        return ""

    @classmethod
    def create_windows_task_scheduler_job(cls, target_path):
        """
        Creates a high-privilege Task Scheduler task for Administrator autostart at Windows logon.
        When run by Task Scheduler, Windows bypasses UAC prompts for standard users.
        """
        if not is_admin():
            return False

        try:
            cmd = f'schtasks /create /tn "{APP_NAME}" /tr "\"{target_path}\"" /sc onlogon /rl highest /f'
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            if res.returncode == 0:
                print(f"[Autostart] Task Scheduler job '{APP_NAME}' created successfully with HIGHEST admin rights.")
                return True
            else:
                print(f"[Autostart TaskScheduler Warning] schtasks output: {res.stderr}")
        except Exception as e:
            print(f"[Autostart Error] Task scheduler creation failed: {e}")
        return False

    @classmethod
    def remove_windows_task_scheduler_job(cls):
        if not is_admin():
            return
        try:
            cmd = f'schtasks /delete /tn "{APP_NAME}" /f'
            subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        except Exception:
            pass

    @classmethod
    def create_windows_shortcut(cls, target_path, shortcut_path):
        """Creates a .lnk shortcut using PowerShell WScript.Shell."""
        try:
            cmd = f"$s=(New-Object -COM WScript.Shell).CreateShortcut('{shortcut_path}');$s.TargetPath='{target_path}';$s.Save()"
            subprocess.run(["powershell", "-Command", cmd], capture_output=True, timeout=5)
            print(f"[Autostart] Created shortcut '{shortcut_path}' -> '{target_path}'")
            return True
        except Exception as e:
            print(f"[Autostart Error] Failed to create shortcut: {e}")
            return False

    @classmethod
    def sync_desktop_mattermost_to_startup(cls):
        """
        Finds any 'Mattermost*.lnk' on user's Desktop / Public Desktop and copies it to Windows shell:startup.
        Ensures official Mattermost app also launches on boot.
        """
        if os.name != 'nt':
            return

        startup_dir = cls.get_windows_startup_folder()
        if not startup_dir or not os.path.exists(startup_dir):
            return

        desktop_paths = []
        user_profile = os.environ.get("USERPROFILE")
        if user_profile:
            desktop_paths.append(os.path.join(user_profile, "Desktop"))
            desktop_paths.append(os.path.join(user_profile, "Masaüstü"))
        public_desktop = os.environ.get("PUBLIC")
        if public_desktop:
            desktop_paths.append(os.path.join(public_desktop, "Desktop"))

        found_shortcuts = []
        for dpath in desktop_paths:
            if os.path.exists(dpath):
                try:
                    for fname in os.listdir(dpath):
                        if fname.lower().startswith("mattermost") and fname.lower().endswith(".lnk"):
                            found_shortcuts.append(os.path.join(dpath, fname))
                except Exception:
                    pass

        for src_lnk in found_shortcuts:
            try:
                dest_lnk = os.path.join(startup_dir, os.path.basename(src_lnk))
                shutil.copy2(src_lnk, dest_lnk)
                print(f"[Autostart] Synced Desktop shortcut '{src_lnk}' to startup: '{dest_lnk}'")
            except Exception as e:
                print(f"[Autostart Error] Could not copy '{src_lnk}' to startup: {e}")

    @classmethod
    def is_autostart_enabled(cls):
        if os.name == 'nt':
            startup_dir = cls.get_windows_startup_folder()
            if startup_dir:
                app_shortcut = os.path.join(startup_dir, f"{APP_NAME}.lnk")
                if os.path.exists(app_shortcut):
                    return True
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
            except Exception:
                pass
            return False
        else:
            desktop_path = os.path.expanduser(f"~/.config/autostart/{APP_NAME}.desktop")
            return os.path.exists(desktop_path)

    @classmethod
    def set_autostart(cls, enable: bool) -> bool:
        exec_path = cls.get_executable_path()

        if os.name == 'nt':
            startup_dir = cls.get_windows_startup_folder()
            if enable:
                # 1. Task Scheduler (If running as Admin during initial setup/installation)
                if is_admin():
                    cls.create_windows_task_scheduler_job(exec_path)

                # 2. Startup Folder Shortcut fallback (No UAC required for standard user)
                if startup_dir:
                    os.makedirs(startup_dir, exist_ok=True)
                    shortcut_path = os.path.join(startup_dir, f"{APP_NAME}.lnk")
                    cls.create_windows_shortcut(exec_path, shortcut_path)

                # 3. Sync official Mattermost desktop shortcut to startup
                cls.sync_desktop_mattermost_to_startup()

                # 4. HKCU Registry Fallback (No UAC required for standard user)
                try:
                    import winreg
                    key = winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER,
                        r"Software\Microsoft\Windows\CurrentVersion\Run",
                        0,
                        winreg.KEY_ALL_ACCESS
                    )
                    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{exec_path}"')
                    winreg.CloseKey(key)
                except Exception:
                    pass
                return True
            else:
                if is_admin():
                    cls.remove_windows_task_scheduler_job()
                if startup_dir:
                    shortcut_path = os.path.join(startup_dir, f"{APP_NAME}.lnk")
                    if os.path.exists(shortcut_path):
                        try:
                            os.remove(shortcut_path)
                        except Exception:
                            pass
                try:
                    import winreg
                    key = winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER,
                        r"Software\Microsoft\Windows\CurrentVersion\Run",
                        0,
                        winreg.KEY_ALL_ACCESS
                    )
                    winreg.DeleteValue(key, APP_NAME)
                    winreg.CloseKey(key)
                except Exception:
                    pass
                return True
        else:
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
                    return True
                except Exception:
                    return False
            else:
                if os.path.exists(desktop_path):
                    try:
                        os.remove(desktop_path)
                        return True
                    except Exception:
                        return False
                return True
