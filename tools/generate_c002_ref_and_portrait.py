#!/usr/bin/env python3
"""
Step 2 & Step 3 for C002 — Nỏ Thủ Câm Lặng (Rarity N):
1. Generates the 1x1 Master Reference character on #FF00FF using layout_guide_1x1.png
   and processes it with generate2dsprite.py into c002_reference_clean.png.
2. Generates the horizontal Portrait Preview (c002_portrait_preview.png 884x632 & .webp 354x253)
   without any card frame baked in.
"""
import os
import subprocess
import urllib.request
import json
from PIL import Image

HERO_DIR = "/Users/dochung/Desktop/card_g/assets/heroes/c002_no_thu_cam_lang"
REF_DIR = os.path.join(HERO_DIR, "reference")
CARD_DIR = os.path.join(HERO_DIR, "card")
MOBILE_CARD_DIR = "/Users/dochung/Desktop/card_g/assets/mobile/heroes/c002_no_thu_cam_lang/card"
LAYOUT_1X1 = "/Users/dochung/Desktop/card_g/layout_guide/layout_guide_1x1.png"

os.makedirs(REF_DIR, exist_ok=True)
os.makedirs(CARD_DIR, exist_ok=True)
os.makedirs(MOBILE_CARD_DIR, exist_ok=True)

def call_muse_generate(prompt, ref_images, save_path):
    url = "http://127.0.0.1:3456/generate-image"
    payload = {
        "prompt": prompt,
        "reference_images": ref_images,
        "save_path": save_path,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    print(f"Generated: {save_path}")
    return data

# 1. Generate Master Reference (1x1 on #FF00FF)
raw_ref_path = os.path.join(REF_DIR, "c002_reference_raw.png")
ref_prompt = (
    "Single 2D game character full-body concept sprite centered inside the safe box of the 1x1 layout guide on a flat solid #FF00FF magenta background. "
    "Character: 'Nỏ Thủ Câm Lặng' (Silent Crossbowman), Common Rarity N dark-fantasy scout marksman. "
    "Visual appearance: grounded low-tier mercenary scout wearing a weathered dark charcoal-grey cloth hood with a simple dull iron brow-band, "
    "a dark cloth mask covering his lower face (nose and mouth), a worn dark brown leather and riveted iron brigandine vest over a dark tunic, "
    "a single riveted iron-and-leather shoulder pauldron on his closer right shoulder, a short tattered dark scout cloak/quiver at his back, "
    "a weathered leather belt with bolt pouch and tasset kilt, and rugged dark leather knee-high scout boots with iron shin guards. "
    "Strictly NO glowing magic, NO neon runes, NO gold trim. "
    "Pose & Anatomy: standing in 3/4 view facing RIGHT with clear space between limbs so joints do not overlap. "
    "His farther left arm (viewer's right) extends forward-right holding a rugged heavy wooden-and-iron medieval crossbow pointed diagonally down-right, "
    "with his left fist gripping the crossbow stock cleanly. "
    "His closer right arm (viewer's left) hangs naturally slightly bent at his side, clearly showing the leather wrist bracer and the DORSAL BACK of his right hand "
    "with fingers naturally curved and palm facing inward toward his hip (do NOT draw an open palm facing the camera). "
    "His two legs are in a clear 3/4 stance facing right: closer right boot planted in 3/4 front-right view, farther left boot stepping slightly forward-right. "
    "Clean hand-painted 2D dark-fantasy art style with crisp outlines, solid flat #FF00FF background, zero ground shadow, no text, no borders."
)
call_muse_generate(ref_prompt, [LAYOUT_1X1], raw_ref_path)

# Process with generate2dsprite.py
proc_dir = os.path.join(REF_DIR, "processed")
os.makedirs(proc_dir, exist_ok=True)
cmd = [
    "python3",
    "/Users/dochung/.gemini/config/skills/generate2dsprite/scripts/generate2dsprite.py",
    "process",
    "--input", raw_ref_path,
    "--target", "player",
    "--mode", "idle",
    "--rows", "1",
    "--cols", "1",
    "--output-dir", proc_dir,
    "--cell-size", "512",
    "--align", "feet",
    "--scale-strategy", "preserve",
    "--component-mode", "largest",
    "--strict-qc",
]
subprocess.run(cmd, check=True)

clean_frame = os.path.join(proc_dir, "frames", "frame_000.png")
clean_ref_path = os.path.join(REF_DIR, "c002_reference_clean.png")
if os.path.exists(clean_frame):
    Image.open(clean_frame).save(clean_ref_path)
    print(f"Saved clean reference: {clean_ref_path}")

# Remove any auto-generated .gif from generate2dsprite.py per zero-gif rule
for root, _, files in os.walk(REF_DIR):
    for fn in files:
        if fn.endswith(".gif"):
            os.remove(os.path.join(root, fn))

# 2. Generate Horizontal Portrait Preview (884x632 PNG & 354x253 WebP)
raw_portrait_path = os.path.join(CARD_DIR, "c002_portrait_raw.png")
portrait_prompt = (
    "Horizontal 4:3 dark-fantasy illustration portrait (waist-up) of the exact character in the reference image: "
    "'Nỏ Thủ Câm Lặng' (Silent Crossbowman, Common Rarity N). "
    "He wears a weathered dark charcoal hood with a dull iron brow-guard and a dark cloth mask over his lower face, "
    "intense watchful eyes in shadow, worn dark leather and riveted iron brigandine vest, "
    "holding his heavy wooden-and-iron crossbow ready across his chest. "
    "Background: atmospheric misty dark-fantasy ruined stone watchtower and dead pine forest at dusk with drifting ash and rain. "
    "Realistic gritty dark-fantasy painted illustration matching the card art style, grounded physical tones, no magical glow, "
    "NO card frame, NO text, NO borders, full bleed artwork."
)
call_muse_generate(portrait_prompt, [clean_ref_path], raw_portrait_path)

# Crop & resize to 884x632 (Master PNG) and 354x253 (Mobile WebP)
im = Image.open(raw_portrait_path).convert("RGB")
w, h = im.size
target_ratio = 884.0 / 632.0
cur_ratio = w / float(h)
if cur_ratio > target_ratio:
    new_w = int(round(h * target_ratio))
    left = (w - new_w) // 2
    im_cropped = im.crop((left, 0, left + new_w, h))
else:
    new_h = int(round(w / target_ratio))
    top = max(0, int((h - new_h) * 0.35))
    im_cropped = im.crop((0, top, w, top + new_h))

preview_png_path = os.path.join(CARD_DIR, "c002_portrait_preview.png")
preview_webp_path = os.path.join(MOBILE_CARD_DIR, "c002_portrait_preview.webp")

im_884 = im_cropped.resize((884, 632), Image.Resampling.LANCZOS)
im_884.save(preview_png_path, format="PNG")
im_354 = im_cropped.resize((354, 253), Image.Resampling.LANCZOS)
im_354.save(preview_webp_path, format="WEBP", quality=92)
print(f"Saved portrait previews: {preview_png_path} (884x632) and {preview_webp_path} (354x253)")

