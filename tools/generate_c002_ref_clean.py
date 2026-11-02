#!/usr/bin/env python3
"""
Generates C002 — Nỏ Thủ Câm Lặng (Rarity N) Master Reference (1x1 on pure #FF00FF)
with ZERO square frames, ZERO cyan boxes, ZERO crosshairs, and ZERO borders,
then runs generate2dsprite.py to produce c002_reference_clean.png.
"""
import os
import json
import subprocess
import urllib.request
from PIL import Image

HERO_DIR = "/Users/dochung/Desktop/card_g/assets/heroes/c002_no_thu_cam_lang"
REF_DIR = os.path.join(HERO_DIR, "reference")
LAYOUT_1X1 = "/Users/dochung/Desktop/card_g/layout_guide/layout_guide_1x1.png"
C001_REF_RAW = "/Users/dochung/Desktop/card_g/assets/heroes/c001_hac_kiem_tan_binh/reference/c001_reference_raw.png"

os.makedirs(REF_DIR, exist_ok=True)
raw_ref_path = os.path.join(REF_DIR, "c002_reference_raw.png")

prompt = (
    "A single full-body 2D dark-fantasy game character sprite on a 100% pure flat solid #FF00FF magenta background, "
    "matching the exact hand-painted dark-fantasy art style, proportions, and clean #FF00FF background of the second reference image. "
    "IMPORTANT: Use the first image (layout guide) ONLY for invisible sizing — DO NOT draw any cyan square box, DO NOT draw any blue frame, "
    "DO NOT draw any white dashed crosshair lines, and DO NOT draw any black border! The entire background must be 100% pure flat #FF00FF magenta. "
    "Character: 'Nỏ Thủ Câm Lặng' (Silent Crossbowman), Common Rarity N scout marksman. "
    "Appearance: weathered dark charcoal cloth hood with a simple dull riveted iron brow-band, dark cloth face mask covering nose and mouth, "
    "sharp watchful eyes, worn dark brown leather and riveted iron brigandine vest over a dark olive tunic, "
    "a single riveted iron pauldron on his closer right shoulder, a tattered dark scout cloak and leather quiver of bolts on his back, "
    "layered leather tasset belt kilt with bolt pouch, and dark leather knee-high boots with dull iron shin greaves. "
    "Zero magical glow, zero neon runes, grounded gritty mercenary equipment. "
    "Pose & Anatomy (3/4 view facing RIGHT, open limb separation so joints do not overlap, occupying 68% of canvas height with generous #FF00FF margin on all sides): "
    "- Closer RIGHT arm (viewer's left) hangs slightly angled out from the body, clearly showing the leather wrist bracer and the DORSAL BACK of the right hand "
    "with fingers naturally curved and palm facing inward toward his thigh (never an open palm facing the camera). "
    "- Farther LEFT arm (viewer's right) extends forward-right with the left hand gripping a heavy medieval wooden-and-iron crossbow pointed diagonally down-right. "
    "- Closer RIGHT leg (viewer's left) planted with boot angled in 3/4 front-right perspective; farther LEFT leg (viewer's right) stepping forward-right with boot in 3/4 profile."
)

payload = {
    "prompt": prompt,
    "reference_images": [LAYOUT_1X1, C001_REF_RAW],
    "save_path": raw_ref_path,
}

print("Calling Muse Local API /generate-image for clean C002 reference (no square frame)...")
req = urllib.request.Request(
    "http://127.0.0.1:3456/generate-image",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(req, timeout=300) as resp:
    data = json.loads(resp.read().decode("utf-8"))
print("Generated:", data.get("saved_path", raw_ref_path))

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

clean_ref_path = os.path.join(REF_DIR, "c002_reference_clean.png")
Image.open(os.path.join(proc_dir, "idle-1.png")).save(clean_ref_path)
print("Saved clean reference:", clean_ref_path)

# Remove any .gif files created by generate2dsprite.py
for root, _, files in os.walk(REF_DIR):
    for fn in files:
        if fn.endswith(".gif"):
            os.remove(os.path.join(root, fn))
