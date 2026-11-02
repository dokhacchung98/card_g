#!/usr/bin/env python3
"""
Generate clean, well-proportioned Stickman Shoes (`foot_front` & `foot_back`)
matching the exact cute rounded shoe silhouette at the bottom of `sticker_reference_raw.png`,
with a smooth, continuous one-piece rounded ankle joint extension on the top-left.
"""
import json
import urllib.request

API_BASE = "http://127.0.0.1:3456"
LAYOUT_1X1 = "/Users/dochung/Desktop/card_g/layout_guide/layout_guide_1x1.png"
CHAR_REF = "/Users/dochung/Desktop/card_g/assets/sticker_hero/reference/sticker_reference_raw.png"
OUT_RAW = "/Users/dochung/Desktop/card_g/assets/sticker_hero/raw/sticker_feet_raw.png"


def post_json(url, payload, timeout=420):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Authorization": "Bearer muse-local"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


print("=== Regenerating Clean One-Piece Chibi Stickman Boots (foot_front & foot_back) via Muse Local API ===")
print("1. Creating new Muse thread...")
print("   Thread response:", post_json(f"{API_BASE}/v1/thread", {"new_thread": True}))

prompt = (
    "2D game character isolated foot/boot sprite asset on a pure solid magenta (#FF00FF) background. "
    "Look at the TWO SHOES at the bottom of the attached stickman character reference image: they are cute, compact, smooth rounded shoes with a flat horizontal bottom, a gently rounded heel on the left, a smooth curved toe on the right, royal blue (#2563EB) fill with a darker blue shadow rim on the right, and a bold black outline. "
    "Draw TWO isolated, separated shoes stacked vertically (TOP = foot_front, BOTTOM = foot_back) with a large gap of pure #FF00FF magenta between them. "
    "Each shoe MUST be a SINGLE, CONTINUOUS, ONE-PIECE L-shaped chibi ankle-boot silhouette pointing RIGHT: "
    "- The bottom is the exact cute compact rounded shoe from the reference image (flat horizontal sole, smooth rounded toe on the right, NO separate sole line, NO pointy tongue bump, NO internal black dividing lines). "
    "- Rising smoothly and continuously from the TOP-LEFT (ankle area) of the shoe is a short, wide, rounded-top ankle cuff/neck (about 40% as wide as the shoe, shaped like the rounded end of a capsule) so the lower leg bone can overlap and pivot cleanly on it. "
    "- IMPORTANT: The ankle cuff and the shoe body are ONE SINGLE UNIFIED SHAPE filled with royal blue (#2563EB) and surrounded by ONE single outer black outline (do NOT draw a black line separating the ankle cuff from the shoe, and do NOT draw a skinny thin antenna tab). "
    "- Pure solid flat #FF00FF magenta background everywhere outside the two boots. No grid lines, no boxes."
)

res = post_json(
    f"{API_BASE}/generate-image",
    {
        "prompt": prompt,
        "reference_images": [LAYOUT_1X1, CHAR_REF],
        "save_path": OUT_RAW,
    },
)
print("Saved feet raw ->", OUT_RAW, res)
