#!/usr/bin/env python3
"""
Step 3, Step 4 (raw sheets), and Step 5 (raw VFX sheet) for C002 — Nỏ Thủ Câm Lặng (Rarity N):
Generates:
1. Horizontal Portrait Preview (c002_portrait_preview.png 884x632 & .webp 354x253) — NO card frame!
2. c002_parts_core_2x2_raw.png (Head, Sleeveless Chest Vest, Isolated Crossbow, Hip Tasset Kilt) — NO grid lines/boxes!
3. c002_parts_limbs_2x3_raw.png (Cloak+Quiver, Pauldron, UpperArm Front, UpperArm Back, Thigh Front, Thigh Back) — NO grid lines/boxes!
4. c002_parts_hands_feet_2x2_raw.png (Forearm+Hand Front, Forearm+Hand Back, Shin+Boot Front, Shin+Boot Back) — NO grid lines/boxes!
5. c002_vfx_light_2x2_raw.png (4 lightweight crossbow air/wind/spark/dust VFX) — NO grid lines/boxes!
"""
import os
import json
import urllib.request
from PIL import Image

HERO_DIR = "/Users/dochung/Desktop/card_g/assets/heroes/c002_no_thu_cam_lang"
REF_CLEAN = os.path.join(HERO_DIR, "reference/c002_reference_clean.png")
CARD_DIR = os.path.join(HERO_DIR, "card")
PARTS_RAW_DIR = os.path.join(HERO_DIR, "parts")
VFX_RAW_DIR = os.path.join(HERO_DIR, "vfx")
MOBILE_CARD_DIR = "/Users/dochung/Desktop/card_g/assets/mobile/heroes/c002_no_thu_cam_lang/card"

LAYOUT_2X2 = "/Users/dochung/Desktop/card_g/layout_guide/layout_guide_2x2.png"
LAYOUT_2X3 = "/Users/dochung/Desktop/card_g/layout_guide/layout_guide_2x3.png"
C001_PARTS_3X3 = "/Users/dochung/Desktop/card_g/assets/heroes/c001_hac_kiem_tan_binh/parts/c001_parts_3x3_raw.png"
C001_VFX_RAW = "/Users/dochung/Desktop/card_g/assets/heroes/c001_hac_kiem_tan_binh/vfx/c001_vfx_light_2x2_raw.png"

for d in [CARD_DIR, PARTS_RAW_DIR, VFX_RAW_DIR, MOBILE_CARD_DIR]:
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


# --- 1. Horizontal Portrait Preview (884x632 PNG & 354x253 WebP) ---
raw_portrait_path = os.path.join(CARD_DIR, "c002_portrait_raw.png")
portrait_prompt = (
    "Horizontal 4:3 dark-fantasy painted illustration portrait (waist-up) of the exact character in the reference image: "
    "'Nỏ Thủ Câm Lặng' (Silent Crossbowman, Common Rarity N). "
    "He wears a weathered dark charcoal cloth hood with a dull riveted iron brow-band and a dark cloth mask covering his nose and mouth, "
    "sharp watchful eyes in shadow, worn dark brown leather and riveted iron brigandine vest with diagonal leather strap, "
    "riveted iron pauldron on his right shoulder, quiver of bolts behind his shoulder, holding his heavy wooden-and-iron crossbow ready across his chest. "
    "Background: atmospheric misty dark-fantasy ruined stone watchtower and dead pine forest at dusk with drifting ash and rain. "
    "Gritty dark-fantasy painted illustration matching the card art style, grounded physical tones, zero magical glow, "
    "NO card frame, NO square border, NO text, full bleed artwork."
)
call_muse_generate(portrait_prompt, [REF_CLEAN], raw_portrait_path)

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


# --- 2. 2x2 Core Cutout Parts (Head, Sleeveless Chest, Isolated Crossbow, Hip Kilt) ---
core_raw_path = os.path.join(PARTS_RAW_DIR, "c002_parts_core_2x2_raw.png")
core_prompt = (
    "A 2x2 grid of 4 isolated 2D game character body-part cutouts for the dark-fantasy crossbowman in the second reference image, "
    "floating on a 100% pure flat solid #FF00FF magenta background just like the third reference image. "
    "IMPORTANT: Use the first image (2x2 layout guide) ONLY for invisible quadrant placement — DO NOT draw any cyan boxes, "
    "DO NOT draw any black grid lines, DO NOT draw any dashed crosshairs, and DO NOT draw any outer border! "
    "Each quadrant contains ONE isolated cutout piece centered with wide #FF00FF magenta margin on all sides: "
    "- Top-Left quadrant: Isolated HEAD and hooded neck in 3/4 view facing right — dark charcoal cloth hood, dull riveted iron brow-band, "
    "watchful eyes, and dark cloth face mask covering nose and mouth. "
    "- Top-Right quadrant: Strictly ARMLESS and SLEEVELESS torso chest vest in 3/4 view facing right — weathered dark brown riveted leather brigandine vest "
    "with diagonal leather strap and belt buckle, completely sleeveless with NO shoulders, NO arms, and NO head attached. "
    "- Bottom-Left quadrant: Isolated heavy medieval WOODEN-AND-IRON CROSSBOW in 3/4 view pointed diagonally down-right — "
    "dark wooden stock, iron trigger lever, curved steel bow prod with taut bowstring and iron stirrup at the front, NO hands or arms attached. "
    "- Bottom-Right quadrant: Isolated hip leather tasset KILT (layered riveted brown leather strips and small bolt pouch hanging from a waist belt, no legs attached). "
    "Hand-painted gritty dark-fantasy 2D art style matching the character reference, crisp dark outlines, 100% flat #FF00FF magenta background with zero lines or boxes."
)
call_muse_generate(core_prompt, [LAYOUT_2X2, REF_CLEAN, C001_PARTS_3X3], core_raw_path)


# --- 3. 2x3 Upper Limbs, Thighs, Cloak & Pauldron Sheet ---
limbs_raw_path = os.path.join(PARTS_RAW_DIR, "c002_parts_limbs_2x3_raw.png")
limbs_prompt = (
    "A 2-row by 3-column (2x3) arrangement of 6 isolated 2D game character armor/limb cutouts for the dark-fantasy crossbowman in the second reference image, "
    "floating on a 100% pure flat solid #FF00FF magenta background just like the third reference image. "
    "IMPORTANT: Use the first image (2x3 layout guide) ONLY for invisible cell positions — DO NOT draw any cyan boxes, "
    "DO NOT draw any black grid lines, DO NOT draw any dashed crosshairs, and DO NOT draw any outer border! "
    "Row 1 Left: Isolated tattered dark charcoal-brown scout CLOAK with a leather quiver of bolts attached at the top shoulder, viewed from 3/4 side. "
    "Row 1 Center: Isolated riveted dark iron shoulder PAULDRON (layered metal shoulder guard with leather strap). "
    "Row 1 Right: Isolated closer RIGHT upper arm segment (shoulder to elbow, dark olive padded cloth sleeve, vertical cylinder with rounded ends). "
    "Row 2 Left: Isolated farther LEFT upper arm segment (shoulder to elbow, dark olive padded cloth sleeve, vertical cylinder with rounded ends). "
    "Row 2 Center: Isolated closer RIGHT upper leg THIGH segment (hip to knee, dark olive-brown cloth trousers, vertical thigh tube with rounded ends). "
    "Row 2 Right: Isolated farther LEFT upper leg THIGH segment (hip to knee, dark olive-brown cloth trousers, vertical thigh tube with rounded ends). "
    "Hand-painted gritty dark-fantasy 2D art style matching the character reference, crisp dark outlines, 100% flat #FF00FF magenta background with zero lines or boxes."
)
call_muse_generate(limbs_prompt, [LAYOUT_2X3, REF_CLEAN, C001_PARTS_3X3], limbs_raw_path)


# --- 4. 2x2 High-Detail Forearms+Hands & Shins+Boots Sheet ---
hands_feet_raw_path = os.path.join(PARTS_RAW_DIR, "c002_parts_hands_feet_2x2_raw.png")
hands_feet_prompt = (
    "A 2x2 arrangement of 4 isolated 2D game character limb cutouts for the dark-fantasy crossbowman in the second reference image, "
    "floating on a 100% pure flat solid #FF00FF magenta background just like the third reference image. "
    "IMPORTANT: Use the first image (2x2 layout guide) ONLY for invisible quadrant positions — DO NOT draw any cyan boxes, "
    "DO NOT draw any black grid lines, DO NOT draw any dashed crosshairs, and DO NOT draw any outer border! "
    "Top-Left quadrant: Closer RIGHT forearm and hand in 3/4 view facing right — dark iron-and-leather wrist bracer, fingerless dark leather glove, "
    "and the DORSAL BACK of the right hand with naturally curved fingers and palm facing inward (never an open palm facing the viewer). "
    "Top-Right quadrant: Farther LEFT forearm and closed gripping hand in 3/4 view facing right — dark leather wrist bracer "
    "and a closed fist gripping upward/forward (knuckles and thumb clearly defined, no weapon attached). "
    "Bottom-Left quadrant: Closer RIGHT lower leg (knee guard + iron shin greave + laced dark leather boot) planted in 3/4 front-right perspective. "
    "Bottom-Right quadrant: Farther LEFT lower leg (knee guard + iron shin greave + laced dark leather boot) stepping forward-right in 3/4 side profile. "
    "Hand-painted gritty dark-fantasy 2D art style matching the character reference, crisp dark outlines, 100% flat #FF00FF magenta background with zero lines or boxes."
)
call_muse_generate(hands_feet_prompt, [LAYOUT_2X2, REF_CLEAN, C001_PARTS_3X3], hands_feet_raw_path)


# --- 5. 2x2 Lightweight Soft-Opacity Crossbow VFX Sheet ---
vfx_raw_path = os.path.join(VFX_RAW_DIR, "c002_vfx_light_2x2_raw.png")
vfx_prompt = (
    "A 2x2 arrangement of 4 minimal, delicate, lightweight physical crossbow air & wind combat effect elements on a 100% pure flat solid #FF00FF magenta background, "
    "matching the borderless, boxless, airy translucent style of the second reference image. "
    "IMPORTANT: Use the first image (2x2 layout guide) ONLY for invisible quadrant positions — DO NOT draw any cyan boxes, "
    "DO NOT draw any black grid lines, DO NOT draw any crosshairs, and DO NOT draw any borders! "
    "These effects are for a Rarity-N marksman, so they must be VERY SIMPLE, THIN, AIRY, WISPY, and SEMI-TRANSPARENT with NO dark outlines: "
    "Top-Left quadrant (fx_slash): A single thin, delicate, semi-transparent silver-white bowstring release wind arc / crescent air wave curving to the right. "
    "Top-Right quadrant (fx_slash_heavy): A sleek, thin piercing wind-tunnel bolt streak pointing diagonally down-right with two delicate translucent air-ring ripples around a sharp silver-white core (for sniper skill Tiễn Xuyên Tâm). "
    "Bottom-Left quadrant (fx_spark): A small, subtle metallic steel bolt-impact glint with 5 tiny pale warm-gold and white pinpoint sparks radiating softly. "
    "Bottom-Right quadrant (fx_dust): A small, soft, wispy puff of pale gray-brown ground recoil dust at foot level, gentle and airy. "
    "100% flat #FF00FF magenta background with zero lines or boxes."
)
call_muse_generate(vfx_prompt, [LAYOUT_2X2, C001_VFX_RAW], vfx_raw_path)

print("All C002 raw sheets generated successfully!")
