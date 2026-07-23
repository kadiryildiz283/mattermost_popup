import os
import subprocess
import sys
import shutil

def build_appimage():
    print("Building Linux AppImage...")

    # 1. Ensure PyInstaller binary exists
    if not os.path.exists("dist/MattermostEmergencyClient"):
        print("PyInstaller binary not found. Running build_exe.py first...")
        from build_exe import build
        build()

    appdir = "AppDir"
    if os.path.exists(appdir):
        shutil.rmtree(appdir)
    
    os.makedirs(appdir, exist_ok=True)

    # Copy binary into AppDir
    bin_target = os.path.join(appdir, "MattermostEmergencyClient")
    shutil.copy2("dist/MattermostEmergencyClient", bin_target)
    os.chmod(bin_target, 0o755)

    # Copy logo
    logo_src = "albay-logo.png"
    if not os.path.exists(logo_src):
        from create_logo_assets import generate_assets
        generate_assets()

    shutil.copy2(logo_src, os.path.join(appdir, "albay-logo.png"))
    shutil.copy2(logo_src, os.path.join(appdir, ".DirIcon"))

    # Create Desktop Entry file
    desktop_content = """[Desktop Entry]
Name=Mattermost Emergency Client
Exec=MattermostEmergencyClient %U
Icon=albay-logo
Type=Application
Categories=Utility;Network;
Comment=Mattermost Emergency Alert Client
"""
    with open(os.path.join(appdir, "MattermostEmergencyClient.desktop"), "w", encoding="utf-8") as f:
        f.write(desktop_content)

    # Create AppRun script
    apprun_content = """#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
exec "${HERE}/MattermostEmergencyClient" "$@"
"""
    apprun_path = os.path.join(appdir, "AppRun")
    with open(apprun_path, "w", encoding="utf-8") as f:
        f.write(apprun_content)
    os.chmod(apprun_path, 0o755)

    # Download appimagetool if not present
    appimagetool = "./appimagetool-x86_64.AppImage"
    if not os.path.exists(appimagetool):
        print("Downloading appimagetool...")
        url = "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage"
        subprocess.check_call(["curl", "-sL", url, "-o", appimagetool])
        os.chmod(appimagetool, 0o755)

    output_appimage = "dist/MattermostEmergencyClient-x86_64.AppImage"
    env = os.environ.copy()
    env["ARCH"] = "x86_64"

    cmd = [appimagetool, "--appimage-extract-and-run", appdir, output_appimage]
    print(f"Running command: {' '.join(cmd)}")
    subprocess.check_call(cmd, env=env)

    print(f"\n[OK] AppImage build complete! Output at: '{output_appimage}'")

if __name__ == "__main__":
    build_appimage()
