import os
import subprocess
import sys

def build():
    print("Building Mattermost Emergency Client Executable (One-File)...")

    # Generate logo assets if not present
    if not os.path.exists("app.ico") or not os.path.exists("albay-logo.png"):
        try:
            from create_logo_assets import generate_assets
            generate_assets()
        except Exception as e:
            print(f"Warning generating logo assets: {e}")

    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller is not installed. Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Separation char for add-data argument (; on Windows, : on Linux)
    sep = ";" if os.name == 'nt' else ":"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--icon=app.ico",
        "--name=MattermostEmergencyClient",
        f"--add-data=sounds{sep}sounds",
        f"--add-data=config.json{sep}.",
        f"--add-data=albay-logo.jpg{sep}.",
        f"--add-data=albay-logo.png{sep}.",
        f"--add-data=app.ico{sep}.",
        "main.py"
    ]

    print(f"Running command: {' '.join(cmd)}")
    subprocess.check_call(cmd)
    out_name = "dist/MattermostEmergencyClient.exe" if os.name == 'nt' else "dist/MattermostEmergencyClient"
    print(f"\n[OK] Build complete! Single Executable generated at '{out_name}'")

if __name__ == "__main__":
    build()
