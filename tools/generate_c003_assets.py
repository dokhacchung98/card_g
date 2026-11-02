#!/usr/bin/env python3
"""
Step 2, 3, 4 & 5 Generator for Hero 003 (C03: Đao Phủ Đồi Thi — Corpse-Hill Executioner, Rarity N):
- Generates 1x1 Master Reference on pure flat #FF00FF (zero square frame, holding heavy iron executioner great-cleaver in FRONT HAND).
- Generates Horizontal Portrait Preview (884x632 PNG + 354x253 WebP, no card frame).
- Generates 2x2 Core Cutout Parts, 2x3 Limbs Cutout Parts, 2x2 Hands/Feet Cutout Parts, and 2x2 Lightweight VFX sheet on #FF00FF.
"""
import json
import os
import subprocess
import time
import urllib.request
import numpy as np
from PIL import Image

API_URL = "http://127.0.0.1:3456/generate-image"
HERO_DIR = "/Users/dochung/Desktop/card_g/assets/heroes/c003_dao_phu_doi_thi"
REF_DIR = os.path.join(HERO_DIR, "reference")
CARD_DIR = os.path.join(HERO_DIR, "card")
MOB_CARD_DIR = "/Users/dochung/Desktop/card_g/assets/mobile/heroes/c003_dao_phu_doi_thi/card"
PARTS_RAW_DIR = os.path.join(HERO_DIR, "parts")
VFX_RAW_DIR = os.path.join(HERO_DIR, "vfx")

LAYOUT_1X1 = "/Users/dochung/Desktop/card_g/layout_guide/layout_guide_1x1.png"
LAYOUT_2X2 = "/Users/dochung/Desktop/card_g/layout_guide/layout_guide_2x2.png"
LAYOUT_2X3 = "/Users/dochung/Desktop/card_g/layout_guide/layout_guide_2x3.png"
C001_REF_RAW = "/Users/dochung/Desktop/card_g/assets/heroes/c001_hac_kiem_tan_binh/reference/c001_reference_raw.png"
C001_PARTS_3X3 = "/Users/dochung/Desktop/card_g/assets/heroes/c001_hac_kiem_tan_binh/parts/c001_parts_3x3_raw.png"
C001_VFX_RAW = "/Users/dochung/Desktop/card_g/assets/heroes/c001_hac_kiem_tan_binh/vfx/c001_vfx_light_2x2_raw.png"

for d in [REF_DIR, CARD_DIR, MOB_CARD_DIR, PARTS_RAW_DIR, VFX_RAW_DIR]:
    os.makedirs(d, exist_ok=True)


def call_muse_generate(prompt: str, ref_images: list, save_path: str):
    if os.path.exists(save_path) and os.path.getsize(save_path) > 1024:
        print(f"[Muse API] Already exists, skipping: {save_path}")
        return
    for attempt in range(1, 4):
        payload = {
            "prompt": prompt,
            "reference_images": ref_images,
            "save_path": save_path,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            API_URL,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        print(f"[Muse API] Attempt {attempt}/3 Generating -> {save_path} ...")
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                res = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"[Muse API] Attempt {attempt} exception: {e}")
            res = {"error": str(e)}

        if os.path.exists(save_path) and os.path.getsize(save_path) > 1024:
            print(f"[Muse API] Successfully saved: {save_path} ({os.path.getsize(save_path)} bytes)")
            return res
        print(f"[Muse API] Warning: file not created yet (response={str(res)[:300]}). Retrying in 3s...")
        time.sleep(3)
    raise RuntimeError(f"Failed to generate {save_path} after 3 attempts!")


# 1. Generate Master Reference (1x1, 3/4 facing RIGHT, Weapon held in FRONT RIGHT HAND!)
ref_raw_path = os.path.join(REF_DIR, "c003_reference_raw.png")
ref_clean_path = os.path.join(REF_DIR, "c003_reference_clean.png")

prompt_ref = (
    "A single full-body 2D dark-fantasy game character sprite on a 100% pure flat solid #FF00FF magenta background, "
    "matching the exact hand-painted dark-fantasy art style, proportions, and clean #FF00FF background of the second reference image. "
    "IMPORTANT: Use the first image (layout guide) ONLY for invisible sizing — DO NOT draw any cyan square box, DO NOT draw any blue frame, "
    "DO NOT draw any white dashed crosshair lines, and DO NOT draw any black border! The entire background must be 100% pure flat #FF00FF magenta. "
    "Character: 'Đao Phủ Đồi Thi' (Corpse-Hill Executioner), Common Rarity N physical melee bruiser. "
    "Appearance: muscular battle-scarred medieval executioner wearing a dark weathered charcoal cloth executioner hood with a riveted dull iron brow-band, "
    "dark cloth face mask covering nose and mouth, fierce cold eyes, heavy riveted dark brown leather-and-iron brigandine chest harness, "
    "a spiked dark iron pauldron on his closer right shoulder, a tattered dark charcoal-brown executioner cape on his back, "
    "a rugged layered leather butcher apron/tasset kilt with iron chain belt at the waist, and dark leather knee-high boots with dull iron shin greaves. "
    "Zero magical glow, zero neon runes, grounded gritty executioner equipment. "
    "Pose & Anatomy (3/4 view facing RIGHT, open limb separation so joints do not overlap, occupying 68% of canvas height with generous #FF00FF margin on all sides): "
    "- MANDATORY FRONT-HAND WEAPON GRIP: Closer RIGHT arm (viewer's left, foreground Front Arm) is angled forward-right in front of his torso, "
    "clearly showing his leather wrist bracer and the DORSAL BACK of his right hand (fingers/knuckles wrapped inward around the handle) "
    "gripping a massive, heavy battle-nicked IRON EXECUTIONER GREAT-CLEAVER / BROAD-BLADE (Đại Đao) held diagonally forward-right in the foreground! "
    "- Farther LEFT arm (viewer's right, Back Arm) is his secondary off-hand, extended slightly out to the right clear of his chest with a closed leather-gloved fist for balance (NO weapon in the back hand). "
    "- Closer RIGHT leg (viewer's left) planted with boot angled in 3/4 front-right perspective; farther LEFT leg (viewer's right) stepping forward-right with boot in 3/4 profile."
)
call_muse_generate(prompt_ref, [LAYOUT_1X1, C001_REF_RAW], ref_raw_path)

# Post-process reference with generate2dsprite.py + despill
proc_dir = os.path.join(REF_DIR, "processed")
os.makedirs(proc_dir, exist_ok=True)
cmd = [
    "python3",
    "/Users/dochung/.gemini/config/skills/generate2dsprite/scripts/generate2dsprite.py",
    "process",
    "--input", ref_raw_path,
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

idle1_path = os.path.join(proc_dir, "idle-1.png")
im_ref = Image.open(idle1_path).convert("RGBA")
arr_ref = np.array(im_ref).astype(np.float32)
rr, rg, rb, ra = arr_ref[:, :, 0], arr_ref[:, :, 1], arr_ref[:, :, 2], arr_ref[:, :, 3]
mdom = (rr + rb) / 2.0 - rg
spill = (ra > 0) & (mdom > 14.0)
if spill.any():
    rr[spill] = np.minimum(rr[spill], rg[spill] + 10.0)
    rb[spill] = np.minimum(rb[spill], rg[spill] + 8.0)
    arr_ref[:, :, 0], arr_ref[:, :, 2] = rr, rb
clean_ref_im = Image.fromarray(np.clip(arr_ref, 0, 255).astype(np.uint8), mode="RGBA")
clean_ref_im.save(idle1_path)
clean_ref_im.save(ref_clean_path)
for gif_f in os.listdir(proc_dir):
    if gif_f.endswith(".gif"):
        os.remove(os.path.join(proc_dir, gif_f))
print(f"Saved clean 512x512 Master Reference -> {ref_clean_path}")

# 2. Generate Horizontal Portrait Preview ONLY (884x632 PNG & 354x253 WebP)
portrait_raw_path = os.path.join(CARD_DIR, "c003_portrait_raw.png")
portrait_png_path = os.path.join(CARD_DIR, "c003_portrait_preview.png")
portrait_webp_path = os.path.join(MOB_CARD_DIR, "c003_portrait_preview.webp")

prompt_portrait = (
    "Horizontal 4:3 dark-fantasy painted illustration portrait (waist-up) of the exact character in the reference image: "
    "'Đao Phủ Đồi Thi' (Corpse-Hill Executioner, Common Rarity N). "
    "He wears a weathered dark charcoal executioner hood with a riveted dull iron brow-band and dark cloth face mask, "
    "fierce cold eyes gleaming in shadow, heavy riveted leather-and-iron brigandine chest harness, spiked iron pauldron on his right shoulder, "
    "swinging his massive battle-nicked iron executioner great-cleaver (Đại Đao) with his foreground right gauntlet. "
    "Background: misty dark-fantasy corpse-hill battlefield at dusk with broken weapons stuck in the mud and crows in the dead trees. "
    "Gritty dark-fantasy painted illustration matching the card art style, grounded physical tones, zero magical glow, "
    "NO card frame, NO square border, NO text, full bleed artwork."
)
call_muse_generate(prompt_portrait, [ref_clean_path], portrait_raw_path)

raw_p = Image.open(portrait_raw_path).convert("RGB")
w, h = raw_p.size
target_ratio = 884.0 / 632.0
cur_ratio = w / float(h)
if cur_ratio > target_ratio:
    new_w = int(round(h * target_ratio))
    x0 = (w - new_w) // 2
    crop_p = raw_p.crop((x0, 0, x0 + new_w, h))
else:
    new_h = int(round(w / target_ratio))
    y0 = max(0, int((h - new_h) * 0.28))
    crop_p = raw_p.crop((0, y0, w, y0 + new_h))

portrait_884 = crop_p.resize((884, 632), Image.Resampling.LANCZOS)
portrait_884.save(portrait_png_path, format="PNG")
portrait_354 = portrait_884.resize((354, 253), Image.Resampling.LANCZOS)
portrait_354.save(portrait_webp_path, format="WEBP", quality=92, method=6)
print(f"Saved Portrait Previews -> {portrait_png_path} (884x632) & {portrait_webp_path} (354x253)")

# 3. Generate 2x2 Core Cutout Parts Sheet (head, chest, heavy executioner great-cleaver, hip_kilt)
core_raw_path = os.path.join(PARTS_RAW_DIR, "c003_parts_core_2x2_raw.png")
prompt_core = (
    "A 2x2 grid of 4 isolated 2D game character body-part cutouts for the dark-fantasy executioner in the second reference image, "
    "floating on a 100% pure flat solid #FF00FF magenta background just like the third reference image. "
    "IMPORTANT: Use the first image (2x2 layout guide) ONLY for invisible quadrant placement — DO NOT draw any cyan boxes, "
    "DO NOT draw any black grid lines, DO NOT draw any dashed crosshairs, and DO NOT draw any outer border! "
    "Each quadrant contains ONE isolated cutout piece centered with wide #FF00FF magenta margin on all sides: "
    "- Top-Left quadrant: Isolated HEAD and hooded neck in 3/4 view facing right — dark charcoal executioner cloth hood, dull riveted iron brow-band, "
    "fierce eyes, and dark cloth face mask covering nose and mouth. "
    "- Top-Right quadrant: Strictly ARMLESS and SLEEVELESS torso chest vest in 3/4 view facing right — weathered dark brown riveted leather-and-iron brigandine harness "
    "with iron buckles, completely sleeveless with NO shoulders, NO arms, and NO head attached. "
    "- Bottom-Left quadrant: Isolated massive medieval IRON EXECUTIONER GREAT-CLEAVER / BROAD-BLADE (Đại Đao) angled diagonally down-right — "
    "thick notched single-edged heavy butcher cleaver iron blade, iron ring pommel, and leather-wrapped grip hilt, NO hands or arms attached. "
    "- Bottom-Right quadrant: Isolated hip leather executioner apron-tasset KILT (layered battle-worn brown leather apron strips and iron chain belt, no legs attached). "
    "Hand-painted gritty dark-fantasy 2D art style matching the character reference, crisp dark outlines, 100% flat #FF00FF magenta background with zero lines or boxes."
)
call_muse_generate(prompt_core, [LAYOUT_2X2, ref_clean_path, C001_PARTS_3X3], core_raw_path)

# 4. Generate 2x3 Limbs Cutout Parts Sheet (cloak, pauldron, arm_upper_front, arm_upper_back, leg_thigh_front, leg_thigh_back)
limbs_raw_path = os.path.join(PARTS_RAW_DIR, "c003_parts_limbs_2x3_raw.png")
prompt_limbs = (
    "A 2-row by 3-column (2x3) arrangement of 6 isolated 2D game character armor/limb cutouts for the dark-fantasy executioner in the second reference image, "
    "floating on a 100% pure flat solid #FF00FF magenta background just like the third reference image. "
    "IMPORTANT: Use the first image (2x3 layout guide) ONLY for invisible cell positions — DO NOT draw any cyan boxes, "
    "DO NOT draw any black grid lines, DO NOT draw any dashed crosshairs, and DO NOT draw any outer border! "
    "Row 1 Left: Isolated tattered dark charcoal-brown executioner back CAPE with heavy iron chain clasp at the top shoulder, viewed from 3/4 side. "
    "Row 1 Center: Isolated riveted dark iron spiked shoulder PAULDRON (layered metal shoulder dome, no long straps). "
    "Row 1 Right: Isolated closer RIGHT upper arm segment (shoulder to elbow, dark brown leather-strapped padded sleeve, vertical cylinder with rounded ends). "
    "Row 2 Left: Isolated farther LEFT upper arm segment (shoulder to elbow, dark charcoal padded cloth sleeve, vertical cylinder with rounded ends). "
    "Row 2 Center: Isolated closer RIGHT upper leg THIGH segment (hip to knee, dark brown-grey padded trousers, vertical thigh tube with rounded ends). "
    "Row 2 Right: Isolated farther LEFT upper leg THIGH segment (hip to knee, dark brown-grey padded trousers, vertical thigh tube with rounded ends). "
    "Hand-painted gritty dark-fantasy 2D art style matching the character reference, crisp dark outlines, 100% flat #FF00FF magenta background with zero lines or boxes."
)
call_muse_generate(limbs_prompt := prompt_limbs, [LAYOUT_2X3, ref_clean_path, C001_PARTS_3X3], limbs_raw_path)

# 5. Generate 2x2 Lightweight VFX Sheet for C003 (Iron Cleaver Slash, Heavy Spin Cleave Arc, Sparks, Ground Dust)
vfx_raw_path = os.path.join(VFX_RAW_DIR, "c003_vfx_light_2x2_raw.png")
prompt_vfx = (
    "A 2x2 arrangement of 4 minimal, delicate, lightweight physical iron-cleaver wind & steel combat effect elements on a 100% pure flat solid #FF00FF magenta background, "
    "matching the borderless, boxless, airy translucent style of the second reference image. "
    "IMPORTANT: Use the first image (2x2 layout guide) ONLY for invisible quadrant positions — DO NOT draw any cyan boxes, "
    "DO NOT draw any black grid lines, DO NOT draw any crosshairs, and DO NOT draw any borders! "
    "These effects are for a Rarity-N executioner bruiser, so they must be VERY SIMPLE, THIN, AIRY, WISPY, and SEMI-TRANSPARENT with NO dark outlines: "
    "Top-Left quadrant (fx_slash): A single thin, sharp, semi-transparent silver-white cleaver wind crescent arc curving to the right. "
    "Top-Right quadrant (fx_slash_heavy): A wide, sweeping circular steel whirlwind cleave arc (for spinning cleave skill Xoáy Trảm) with fine translucent silver-white wind streaks, airy with no solid core. "
    "Bottom-Left quadrant (fx_spark): A small, subtle metallic iron-impact glint with 5 tiny pale warm-orange and white pinpoint sparks radiating softly. "
    "Bottom-Right quadrant (fx_dust): A small, soft, wispy puff of pale gray-brown graveyard ground dust at foot level, gentle and airy. "
    "100% flat #FF00FF magenta background with zero lines or boxes."
)
call_muse_generate(prompt_vfx, [LAYOUT_2X2, C001_VFX_RAW], vfx_raw_path)
print("All C003 Muse API generations completed successfully!")
