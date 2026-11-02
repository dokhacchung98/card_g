#!/usr/bin/env python3
"""
Generates isolated Upper Torso (Thân Trên) & Lower Torso (Thân Dưới) on pure #FF00FF
matching the exact smooth rounded chest block and rounded pelvis bowl of sticker_reference_raw.png.
"""
import json
import urllib.request

MUSE_BASE = "http://127.0.0.1:3456"
LAYOUT_1X1 = "/Users/dochung/Desktop/card_g/layout_guide/layout_guide_1x1.png"
STICKER_DIR = "/Users/dochung/Desktop/card_g/assets/sticker_hero"
REF_PATH = f"{STICKER_DIR}/reference/sticker_reference_raw.png"
TORSO_PARTS_PATH = f"{STICKER_DIR}/raw/sticker_torso_parts_raw.png"


def post_json(url, payload, timeout=420):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


prompt_torso = (
    "2D game cutout body-part kit on a pure solid flat magenta background (#FF00FF), matching the EXACT torso shapes of the royal-blue stickman character in the reference image (#2563EB fill, bold black outline, subtle 2D cel-shading on the right edge). "
    "Draw ONLY 2 separated shapes arranged vertically in the center with a wide flat #FF00FF magenta gap between them: "
    "(1) TOP SHAPE — UPPER TORSO (THÂN TRÊN / CHEST): the exact smooth rounded-corner vertical chest block from the reference character (rounded dome shoulders at top, gently tapering sides, smooth rounded waist at bottom — NO protruding side flaps). "
    "(2) BOTTOM SHAPE — LOWER TORSO (THÂN DƯỚI / PELVIS-HIP): the exact smooth rounded bowl/pelvis block from the reference character (gently rounded horizontal waist top, smooth U-shaped rounded hip bottom — NO split lobes). "
    "Zero grid lines, zero arms, zero legs, zero head, zero text, pure flat #FF00FF background."
)
print("=== Generating Exact Upper Torso & Lower Torso from sticker_reference_raw.png ===")
res = post_json(
    f"{MUSE_BASE}/generate-image",
    {
        "prompt": prompt_torso,
        "reference_images": [LAYOUT_1X1, REF_PATH],
        "save_path": TORSO_PARTS_PATH,
    },
)
print("Saved ->", res.get("saved_path"))
