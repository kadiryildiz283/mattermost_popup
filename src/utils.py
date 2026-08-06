import os
import sys

def get_resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller bundle.
    Checks PyInstaller bundle temp folder (_MEIPASS) first, then executable/script directory, then fallback to relative CWD.
    """
    # 1. PyInstaller bundle temp folder (_MEIPASS)
    if hasattr(sys, '_MEIPASS'):
        bundle_path = os.path.join(sys._MEIPASS, relative_path)
        if os.path.exists(bundle_path):
            return bundle_path

    # 2. Path relative to executable / script location
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

    app_path = os.path.join(base_dir, relative_path)
    if os.path.exists(app_path):
        return app_path

    # 3. Local path relative to current working dir fallback
    local_path = os.path.join(os.path.abspath("."), relative_path)
    if os.path.exists(local_path):
        return local_path

    return app_path

def is_mattermost_app_open_and_focused():
    """
    Checks if Mattermost app window (desktop app or browser tab) is currently active/focused.
    Returns True if Mattermost window is focused on screen.
    Returns False if Mattermost is closed, minimized, running in background, or another window is active.
    """
    try:
        # 1. Windows platform
        if sys.platform.startswith("win"):
            import ctypes
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            if not hwnd:
                return False
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value.lower()
                if "mattermost" in title and "emergency" not in title and "popup" not in title:
                    return True
            return False

        # 2. Linux platform
        elif sys.platform.startswith("linux"):
            import subprocess
            try:
                res = subprocess.run(['xprop', '-root', '_NET_ACTIVE_WINDOW'], capture_output=True, text=True, timeout=1)
                if res.returncode == 0:
                    parts = res.stdout.strip().split()
                    win_id = parts[-1]
                    if win_id and win_id != '0x0':
                        res2 = subprocess.run(['xprop', '-id', win_id, '_NET_WM_NAME'], capture_output=True, text=True, timeout=1)
                        if res2.returncode == 0 and '"' in res2.stdout:
                            title = res2.stdout.split('"')[1].lower()
                            if "mattermost" in title and "emergency" not in title and "popup" not in title:
                                return True
            except Exception:
                pass

            try:
                res = subprocess.run(["xdotool", "getactivewindow", "getwindowname"], capture_output=True, text=True, timeout=1)
                if res.returncode == 0:
                    title = res.stdout.strip().lower()
                    if "mattermost" in title and "emergency" not in title and "popup" not in title:
                        return True
            except Exception:
                pass

            return False

        # 3. macOS platform
        elif sys.platform.startswith("darwin"):
            import subprocess
            try:
                cmd = 'tell application "System Events" to get name of first process whose frontmost is true'
                res = subprocess.run(['osascript', '-e', cmd], capture_output=True, text=True, timeout=1)
                if res.returncode == 0 and "mattermost" in res.stdout.lower():
                    return True
            except Exception:
                pass
            return False

    except Exception as e:
        print(f"[AppCheck Error] {e}")

    return False

def is_admin():
    """Check if current process has Administrator/root rights."""
    try:
        if os.name == 'nt':
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0
    except Exception:
        return False

def is_mattermost_process_running():
    """Check if Mattermost desktop client process is running on PC."""
    try:
        import psutil
        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                pname = (proc.info['name'] or '').lower()
                cmd = ' '.join(proc.info['cmdline'] or []).lower()
                # Exclude our emergency client popup app
                if 'mattermost_popup' in cmd or 'mattermostemergencyclient' in cmd:
                    continue
                if pname in ['mattermost.exe', 'mattermost-desktop', 'mattermost'] or ('mattermost' in cmd and 'python' not in pname):
                    return True
            except Exception:
                pass
    except Exception:
        pass
    return False

def is_mattermost_app_open(api_client=None, user_id=None):
    """
    Returns True if Mattermost application is OPEN / user is active on computer:
    - User status in Mattermost API is 'online', 'away', or 'dnd' (yeşil tık veya turuncu tık).
    - OR Mattermost desktop app process is running on system.
    - OR Mattermost active window is currently focused.
    Returns False if user is offline and Mattermost process is not running.
    """
    # 1. Check process running
    if is_mattermost_process_running():
        return True

    # 2. Check active window
    if is_mattermost_app_open_and_focused():
        return True

    # 3. Check API user status (online, away, dnd)
    if api_client and user_id:
        status = api_client.get_user_status(user_id)
        if status in ("online", "away", "dnd"):
            return True

    return False


