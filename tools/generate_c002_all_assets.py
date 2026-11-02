#!/usr/bin/env python3
"""
Regenerates C002 — Nỏ Thủ Câm Lặng (Rarity N) Master Reference cleanly (without layout_guide_1x1.png
so no blue border, outer black frame, or dashed crosshairs are drawn by the image model),
processes it with generate2dsprite.py, and generates the Portrait Preview, Cutout Parts, and Soft-Opacity VFX.
"""
import os
import json
import subprocess
import urllib.request
from PIL import Image

HERO_DIR = "/Users/dochung/Desktop/card_g/assets/heroes/c002_no_thu_cam_lang"
REF_DIR = os.path.join(HERO_DIR, "reference")
CARD_DIR = os.path.join(HERO_DIR, "card")
PARTS_RAW_DIR = os.path.join(HERO_DIR, "parts")
VFX_RAW_DIR = os.path.join(HERO_DIR, "vfx")
GODOT_PARTS_DIR = os.path.join(HERO_DIR, "godot/parts")
MOBILE_CARD_DIR = "/Users/dochung/Desktop/card_g/assets/mobile/heroes/c002_no_thu_cam_lang/card"

LAYOUT_2X2 = "/Users/dochung/Desktop/card_g/layout_guide/layout_guide_2x2.png"

for d in [REF_DIR, CARD_DIR, PARTS_RAW_DIR, VFX_RAW_DIR, GODOT_PARTS_DIR, MOBILE_CARD_DIR]:
    os.makedirs(d, exist_ok=True)


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


# --- STEP 1: Regenerate 1x1 Master Reference WITHOUT layout_guide_1x1.png ---
raw_ref_path = os.path.join(REF_DIR, "c002_reference_raw.png")
ref_prompt = (
    "Single 2D game character full-body concept sprite centered on a 100% solid flat #FF00FF magenta background. "
    "Character fills about 65% of the canvas height with generous uniform #FF00FF magenta margin on all four sides. "
    "NO borders, NO frames, NO boxes, NO crosshairs, NO lines, NO text, NO ground shadow. "
    "Character: 'Nỏ Thủ Câm Lặng' (Silent Crossbowman), Common Rarity N dark-fantasy scout marksman. "
    "Visual appearance: grounded low-tier mercenary scout wearing a weathered dark charcoal-grey cloth hood with a simple dull riveted iron brow-band, "
    "a dark cloth mask covering his lower face (nose and mouth), a worn dark brown leather and riveted iron brigandine vest over a dark tunic, "
    "a single riveted iron-and-leather shoulder pauldron on his closer right shoulder, a short tattered dark scout cloak and bolt quiver at his back, "
    "a weathered leather belt with bolt pouch and layered leather tasset kilt, and rugged dark leather knee-high scout boots with iron shin greaves. "
    "Strictly NO glowing magic, NO neon runes, NO gold trim. "
    "Pose & Anatomy: standing in 3/4 view facing RIGHT with clear space between limbs so joints do not overlap. "
    "His farther left arm (viewer's right) extends forward-right holding a rugged heavy wooden-and-iron medieval crossbow pointed diagonally down-right, "
    "with his left fist gripping the crossbow stock cleanly. "
    "His closer right arm (viewer's left) hangs naturally slightly bent at his side, clearly showing the leather wrist bracer and the DORSAL BACK of his right hand "
    "with fingers naturally curved and palm facing inward toward his hip (do NOT draw an open palm facing the camera). "
    "His two legs are in a clear 3/4 stance facing right: closer right boot planted in 3/4 front-right view, farther left boot stepping slightly forward-right. "
    "Clean hand-painted gritty dark-fantasy 2D art style with crisp dark outlines on a pure flat #FF00FF magenta background."
)
call_muse_generate(ref_prompt, [], raw_ref_path)

proc_dir = os.path.join(REF_DIR, "processed")
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
print(f"Saved clean reference: {clean_ref_path}")

for root, _, files in os.walk(REF_DIR):
    for fn in files:
        if fn.endswith(".gif"):
            os.remove(os.path.join(root, fn))


# --- STEP 2: Generate Horizontal Portrait Preview (884x632 PNG & 354x253 WebP) ---
raw_portrait_path = os.path.join(CARD_DIR, "c002_portrait_raw.png")
portrait_prompt = (
    "Horizontal 4:3 dark-fantasy illustration portrait (waist-up) of the exact character in the reference image: "
    "'Nỏ Thủ Câm Lặng' (Silent Crossbowman, Common Rarity N). "
    "He wears a weathered dark charcoal hood with a dull riveted iron brow-band and a dark cloth mask covering his nose and mouth, "
    "sharp watchful eyes in shadow, worn dark brown leather and riveted iron brigandine vest with a leather shoulder strap, "
    "riveted iron pauldron on his right shoulder, quiver of bolts behind his back, holding his heavy wooden-and-iron crossbow ready across his chest. "
    "Background: atmospheric misty dark-fantasy ruined stone watchtower and dead pine forest at dusk with drifting ash and rain. "
    "Gritty dark-fantasy painted illustration matching the card art style, grounded physical tones, zero magical glow, "
    "NO card frame, NO text, NO borders, full bleed artwork."
)
call_muse_generate(portrait_prompt, [clean_ref_path], raw_portrait_path)

im_p = Image.open(raw_portrait_path).convert("RGB")
pw, ph = im_p.size
target_ratio = 884.0 / 632.0
cur_ratio = pw / float(ph)
if cur_ratio > target_ratio:
    new_w = int(round(ph * target_ratio))
    left = (pw - new_w) // 2
    im_cropped = im_p.crop((left, 0, left + new_w, ph))
else:
    new_h = int(round(pw / target_ratio))
    top = max(0, int((ph - new_h) * 0.28))
    im_cropped = im_p.crop((0, top, pw, top + new_h))

preview_png_path = os.path.join(CARD_DIR, "c002_portrait_preview.png")
preview_webp_path = os.path.join(MOBILE_CARD_DIR, "c002_portrait_preview.webp")
im_cropped.resize((884, 632), Image.Resampling.LANCZOS).save(preview_png_path, format="PNG")
im_cropped.resize((354, 253), Image.Resampling.LANCZOS).save(preview_webp_path, format="WEBP", quality=92)
print(f"Saved portrait previews: {preview_png_path} and {preview_webp_path}")


# --- STEP 3: Generate 2x2 High-Detail Forearms+Hands & Shins+Boots Cutout Sheet ---
hands_feet_raw_path = os.path.join(PARTS_RAW_DIR, "c002_parts_hands_feet_2x2_raw.png")
hands_feet_prompt = (
    "Use the layout guide image just shown as a layout-only reference. Use it only to understand the 2 rows, 2 columns, equal invisible frame slots, centering, spacing, and safe padding. "
    "Do not reproduce the guide: no visible boxes, no safe-area rectangles, no center marks, no dashed crosshairs, no labels, no borders, no guide background. "
    "Use the character image as the visual identity reference. "
    "Generate a 2x2 grid of 4 isolated 2D game character body-part cutouts on a 100% solid flat #FF00FF magenta background: "
    "Top-Left (Slot 1): Closer RIGHT forearm and hand in 3/4 view facing right — dark olive sleeve cuff, riveted dark brown leather wrist bracer, "
    "and the DORSAL BACK of the right hand with fingerless leather glove and naturally curved fingers facing inward (palm hidden facing body, thumb on right side). "
    "Top-Right (Slot 2): Farther LEFT forearm and closed gripping hand in 3/4 view facing right — dark olive sleeve, riveted leather bracer, "
    "and a closed fist wrapped around a short wooden grip (thumb and knuckles clearly visible). "
    "Bottom-Left (Slot 3): Closer RIGHT lower leg (shin greave + boot) in 3/4 front-right view — dull iron knee guard, dark metal shin greave with leather straps, "
    "and an armored leather-and-iron boot planted at a 3/4 front-right angle. "
    "Bottom-Right (Slot 4): Farther LEFT lower leg (shin greave + boot) in 3/4 side-right view — dull iron knee guard, strapped metal shin greave, "
    "and a leather-and-iron boot stepping forward-right in profile. "
    "Leave wide #FF00FF magenta margin around every piece. No borders, no boxes, no lines."
)
call_muse_generate(hands_feet_prompt, [LAYOUT_2X2, clean_ref_path], hands_feet_raw_path)


# --- STEP 4: Generate 2x2 Isolated Crossbow + Torso + Head + Kilt Sheet ---
core_parts_raw_path = os.path.join(PARTS_RAW_DIR, "c002_parts_core_2x2_raw.png")
core_parts_prompt = (
    "Use the layout guide image just shown as a layout-only reference. Use it only to understand the 2 rows, 2 columns, equal invisible frame slots, centering, spacing, and safe padding. "
    "Do not reproduce the guide: no visible boxes, no safe-area rectangles, no center marks, no dashed crosshairs, no labels, no borders, no guide background. "
    "Use the character image as the visual identity reference. "
    "Generate a 2x2 grid of 4 isolated 2D game character body-part cutouts on a 100% solid flat #FF00FF magenta background: "
    "Top-Left (Slot 1): Isolated HEAD and neck hood in 3/4 view facing right — dark charcoal cloth hood, dull riveted iron brow-band, "
    "sharp eyes, and dark cloth face mask covering nose and mouth. "
    "Top-Right (Slot 2): Strictly ARMLESS and SLEEVELESS torso chest vest in 3/4 view facing right — weathered dark brown riveted leather brigandine vest "
    "with diagonal leather strap and belt buckle, completely sleeveless with NO shoulders, NO arms, and NO head attached. "
    "Bottom-Left (Slot 3): Isolated heavy medieval WOODEN-AND-IRON CROSSBOW in 3/4 view pointed diagonally down-right — "
    "dark wooden stock, iron trigger mechanism, curved steel bow prod with taut bowstring, and an iron-tipped bolt loaded on the rail, NO hands attached. "
    "Bottom-Right (Slot 4): Isolated hip leather tasset KILT (layered riveted brown leather strips hanging from a belt, no legs attached). "
    "Leave wide #FF00FF magenta margin around every piece. No borders, no boxes, no lines."
)
call_muse_generate(core_parts_prompt, [LAYOUT_2X2, clean_ref_path], core_parts_raw_path)


# --- STEP 5: Generate 2x2 Lightweight Soft-Opacity Crossbow VFX Sheet ---
vfx_raw_path = os.path.join(VFX_RAW_DIR, "c002_vfx_light_2x2_raw.png")
vfx_prompt = (
    "Use the layout guide image just shown as a layout-only reference. Use it only to understand the 2 rows, 2 columns, equal invisible frame slots, centering, spacing, and safe padding. "
    "Do not reproduce the guide: no visible boxes, no safe-area rectangles, no center marks, no dashed crosshairs, no labels, no borders, no guide background. "
    "Generate a 2x2 sprite sheet of 4 minimal, delicate, lightweight physical crossbow air & wind effects on a 100% solid flat #FF00FF magenta background. "
    "Keep every effect small inside the center 55% of its quadrant: "
    "Top-Left: A single thin, airy silver-white bowstring release wind arc / crescent shockwave curving to the right, wispy and semi-transparent, no dark outline. "
    "Top-Right: A sleek, thin piercing wind-tunnel bolt streak pointing diagonally down-right with two delicate translucent air-ring ripples around a sharp white-silver core (for sniper skill Tiễn Xuyên Tâm), no dark outline. "
    "Bottom-Left: A subtle metallic steel impact glint burst with 4 tiny pale gold-and-white pinpoint sparks, airy and small, no dark outline. "
    "Bottom-Right: A small, soft, wispy grey-tan ground recoil dust puff, very light and airy, no dark outline. "
    "100% solid flat #FF00FF magenta background, no boxes, no lines."
)
call_muse_generate(vfx_prompt, [LAYOUT_2X2], vfx_raw_path)
print("All C002 raw assets regenerated cleanly!")
