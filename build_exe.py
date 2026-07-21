import os
import subprocess
import sys

def build():
    print("Building Mattermost Emergency Client Executable...")

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
        "--onedir",
        "--windowed",
        "--name=MattermostEmergencyClient",
        f"--add-data=sounds{sep}sounds",
        f"--add-data=config.json{sep}.",
        "main.py"
    ]

    print(f"Running command: {' '.join(cmd)}")
    subprocess.check_call(cmd)
    print("\n[OK] Build complete! Executable folder is generated at 'dist/MattermostEmergencyClient'")

if __name__ == "__main__":
    build()
