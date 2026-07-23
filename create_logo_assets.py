import os
from PIL import Image, ImageDraw

def generate_assets():
    logo_jpg = "albay-logo.jpg"
    if not os.path.exists(logo_jpg):
        print(f"Error: {logo_jpg} not found!")
        return

    print("Generating app icons and UI assets from albay-logo.jpg...")
    img = Image.open(logo_jpg).convert("RGBA")

    # Save PNG version
    png_path = "albay-logo.png"
    img.save(png_path, format="PNG")
    print(f"Saved {png_path}")

    # Save ICO version with multiple resolutions for Windows
    ico_path = "app.ico"
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(ico_path, format="ICO", sizes=sizes)
    print(f"Saved {ico_path}")

if __name__ == "__main__":
    generate_assets()
