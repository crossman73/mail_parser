#!/usr/bin/env python3
"""Simple imagesorcery demo: create a base image and a watermarked copy.

This script will:
- ensure Pillow is installed (attempt pip install if ImportError)
- create a base PNG image
- draw a semi-transparent watermark text and save a watermarked PNG
- print saved file paths
"""
from __future__ import annotations
import os
import sys
import subprocess


def ensure_pillow() -> None:
    try:
        import PIL  # type: ignore
    except Exception:
        print("Pillow not found; installing via pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])  # noqa: S603


def make_images(output_dir: str) -> tuple[str, str]:
    from PIL import Image, ImageDraw, ImageFont  # type: ignore

    os.makedirs(output_dir, exist_ok=True)
    base_path = os.path.join(output_dir, "imagesorcery_base.png")
    water_path = os.path.join(output_dir, "imagesorcery_watermarked.png")

    # Create a colorful background
    img = Image.new("RGBA", (800, 600), (30, 144, 255, 255))
    draw = ImageDraw.Draw(img)

    # Draw a rectangle and some sample shapes
    draw.rectangle((50, 50, 750, 450), fill=(255, 255, 255, 200))
    draw.ellipse((100, 100, 300, 300), fill=(255, 200, 50, 255))
    draw.ellipse((500, 200, 700, 400), fill=(200, 50, 150, 255))

    # Save base image
    img.convert("RGBA").save(base_path)

    # Prepare watermark
    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except Exception:
        font = ImageFont.load_default()

    watermark_text = "copilot-mcp imagesorcery demo"

    # Create a copy to draw watermark
    wm = img.copy()
    wdraw = ImageDraw.Draw(wm)

    text_size = wdraw.textsize(watermark_text, font=font)
    padding = 10
    x = wm.width - text_size[0] - padding
    y = wm.height - text_size[1] - padding

    # Semi-transparent black box behind the text
    box_xy = (x - 8, y - 4, x + text_size[0] + 8, y + text_size[1] + 4)
    wdraw.rectangle(box_xy, fill=(0, 0, 0, 150))

    # Draw white text on top
    wdraw.text((x, y), watermark_text, font=font, fill=(255, 255, 255, 220))

    # Save watermarked image
    wm.convert("RGBA").save(water_path)

    return base_path, water_path


def main() -> int:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = script_dir

    ensure_pillow()

    try:
        base, water = make_images(output_dir)
        print(f"Base image written: {base}")
        print(f"Watermarked image written: {water}")
        return 0
    except Exception as e:
        print("Error creating images:", e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
