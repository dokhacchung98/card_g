#!/usr/bin/env python3
"""
Post-processes the Muse-generated 2x2 Overhead Unit HP & Mana Bar Kit
into high-luminance 3D crystal strips so HP & Mana bars are vivid and crisp at mobile scale.
"""

from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path("/Users/dochung/Desktop/card_g")
RAW_DIR = ROOT / "assets" / "ui_hud" / "raw"
BARS_DIR = ROOT / "assets" / "ui_hud" / "hud_bars"
MOBILE_DIR = ROOT / "assets" / "mobile" / "ui_hud"


def unmix_magenta_rgba(im: Image.Image) -> Image.Image:
    arr = np.array(im.convert("RGBA"), dtype=np.float32)
    r, g, b, a = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3]
    mag_dist = np.sqrt((r - 255.0) ** 2 + (g - 0.0) ** 2 + (b - 255.0) ** 2)
    is_bg = (mag_dist < 85.0) | ((r > 190) & (b > 190) & (g < 95) & ((r + b) - 2 * g > 240))
    alpha = np.where(is_bg, 0.0, np.clip((mag_dist - 65.0) / 45.0, 0.0, 1.0) * a)
    edge = (alpha > 0) & (alpha < 250)
    r = np.where(edge, np.minimum(r, (r + g) * 0.5), r)
    b = np.where(edge, np.minimum(b, (b + g) * 0.5), b)
    out = np.stack([np.clip(r, 0, 255), np.clip(g, 0, 255), np.clip(b, 0, 255), np.clip(alpha, 0, 255)], axis=-1).astype(np.uint8)
    return Image.fromarray(out, mode="RGBA")


def tight_crop(im: Image.Image) -> Image.Image:
    arr = np.array(im)
    alpha = arr[..., 3]
    ys, xs = np.where(alpha > 16)
    if len(xs) == 0 or len(ys) == 0:
        return im
    return im.crop((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))


def to_bright_luminance_strip(im: Image.Image) -> Image.Image:
    """Converts the green crystal strip into a high-luminance 3D grayscale-white strip so Godot modulation tints it vividly."""
    arr = np.array(im.convert("RGBA"), dtype=np.float32)
    r, g, b, a = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3]
    lum = np.maximum(np.maximum(r, g), b)
    # Boost midtones and specular highlights so tinted HP bars pop brightly
    norm = np.clip((lum / 255.0) ** 0.72 * 255.0 * 1.15, 0, 255)
    out = np.stack([norm, norm, norm, a], axis=-1).astype(np.uint8)
    return Image.fromarray(out, mode="RGBA")


def main():
    raw_path = RAW_DIR / "unit_overhead_bars_v2_2x2_raw.png"
    sheet = Image.open(raw_path).convert("RGBA")
    w, h = sheet.size
    cw, ch = w // 2, h // 2
    names = [
        "unit_bar_empty_frame.png",
        "unit_hp_fill_strip.png",
        "unit_mana_fill_strip.png",
        "unit_shield_fill_strip.png",
    ]
    coords = [
        (0, 0, cw, ch),
        (cw, 0, w, ch),
        (0, ch, cw, h),
        (cw, ch, w, h),
    ]
    for name, box in zip(names, coords):
        margin_x = int((box[2] - box[0]) * 0.05)
        margin_y = int((box[3] - box[1]) * 0.05)
        cell = sheet.crop((box[0] + margin_x, box[1] + margin_y, box[2] - margin_x, box[3] - margin_y))
        clean = tight_crop(unmix_magenta_rgba(cell))
        if name == "unit_hp_fill_strip.png":
            clean = to_bright_luminance_strip(clean)
        target_w = 180 if "frame" in name else 148
        target_h = 44 if "frame" in name else 18
        resized = clean.resize((target_w, target_h), Image.Resampling.LANCZOS)
        out_png = BARS_DIR / name
        resized.save(out_png)
        resized.save(MOBILE_DIR / f"{out_png.stem}.webp", format="WEBP", quality=92)
        print("   -> Updated", out_png, resized.size)


if __name__ == "__main__":
    main()
