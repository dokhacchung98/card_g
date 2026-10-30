#!/usr/bin/env python3
"""
Generates a lightweight, subtle, wispy 2x2 VFX sheet for C001 (Rarity N) via Muse Local API
and extracts 4 soft-opacity translucent PNGs (fx_slash, fx_slash_heavy, fx_spark, fx_dust).
"""
import os
import json
import urllib.request
import numpy as np
from PIL import Image, ImageFilter

HERO_DIR = "/Users/dochung/Desktop/card_g/assets/heroes/c001_hac_kiem_tan_binh"
VFX_DIR = os.path.join(HERO_DIR, "vfx")
PARTS_DIR = os.path.join(HERO_DIR, "godot/parts")
LAYOUT_2X2 = "/Users/dochung/Desktop/card_g/layout_guide/layout_guide_2x2.png"
RAW_VFX_PATH = os.path.join(VFX_DIR, "c001_vfx_light_2x2_raw.png")

os.makedirs(VFX_DIR, exist_ok=True)

prompt = (
    "A 2x2 grid of 4 minimal, subtle, lightweight 2D game combat effect elements on a pure solid flat magenta #FF00FF background. "
    "Use the attached 2x2 layout guide ONLY for invisible cell positions and safe margins; do not draw any grid lines or boxes. "
    "These effects are for a basic Rarity-N foot soldier, so they must be VERY SIMPLE, THIN, AIRY, WISPY, and UNDERSTATED — "
    "NO thick 3D metal blades, NO dark black outlines, NO heavy explosions. "
    "Top-left cell (cell 1 - fx_slash): a single thin, delicate, semi-transparent silver-white air-cut arc (a slender crescent wind line showing a quick sword swing, facing right, occupying 50% of the cell). "
    "Top-right cell (cell 2 - fx_slash_heavy): two thin, airy, parallel silver-white wind-cut curves (lightweight double air-slash trail facing right, sleek and delicate, no dark metal body, occupying 55% of the cell). "
    "Bottom-left cell (cell 3 - fx_spark): a small, subtle steel-on-steel parry glint with 5-6 tiny pale warm-amber and white pinpoint sparks radiating softly, compact and minimal, occupying 40% of the cell. "
    "Bottom-right cell (cell 4 - fx_dust): a small, soft, wispy puff of pale gray-brown ground dust at foot level, gentle and airy without hard outlines, occupying 45% of the cell. "
    "Every element must stay well inside the central 60% safe area of its cell on a completely flat #FF00FF background."
)

payload = {
    "prompt": prompt,
    "reference_images": [LAYOUT_2X2],
    "save_path": RAW_VFX_PATH,
}

print("Calling Muse Local API /generate-image for lightweight C001 VFX...")
req = urllib.request.Request(
    "http://127.0.0.1:3456/generate-image",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(req, timeout=180) as resp:
    res = json.loads(resp.read().decode("utf-8"))
    print("Muse response:", res.get("saved_path", res))

