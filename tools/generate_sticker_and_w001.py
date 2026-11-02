#!/usr/bin/env python3
"""
Generator for:
1. Base Stickman / Sticker Hero ('Tướng Sticker Basic' — Stick War / Supreme Duelist 2D style, 4 Team Colors: Blue, Red, Green, Amber)
2. Weapon 001 (W001: Hắc Kiếm Tàn Binh — Rarity N Black-Iron Broadsword):
   - Horizontal Card Preview (884x632 PNG & 354x253 WebP) with DIAGONAL weapon composition to optimize horizontal frame.
   - Full uncropped Weapon Sprite on pure #FF00FF magenta (zero square frame) with 2 Grip Points (Grip 1 & Grip 2).
"""
import json
import os
import subprocess
import time
import urllib.request
import numpy as np
from PIL import Image

BASE_URL = "http://127.0.0.1:3456"
API_URL = f"{BASE_URL}/generate-image"
THREAD_URL = f"{BASE_URL}/v1/thread"

STICKER_DIR = "/Users/dochung/Desktop/card_g/assets/sticker_hero"
STICKER_REF_DIR = os.path.join(STICKER_DIR, "reference")
STICKER_RAW_DIR = os.path.join(STICKER_DIR, "raw")

W001_DIR = "/Users/dochung/Desktop/card_g/assets/weapons/w001_hac_kiem_tan_binh"
W001_CARD_DIR = os.path.join(W001_DIR, "card")
W001_MOB_CARD_DIR = "/Users/dochung/Desktop/card_g/assets/mobile/weapons/w001_hac_kiem_tan_binh/card"
W001_RAW_DIR = os.path.join(W001_DIR, "raw")
W001_PARTS_DIR = os.path.join(W001_DIR, "parts")

LAYOUT_1X1 = "/Users/dochung/Desktop/card_g/layout_guide/layout_guide_1x1.png"
LAYOUT_2X2 = "/Users/dochung/Desktop/card_g/layout_guide/layout_guide_2x2.png"

for d in [STICKER_REF_DIR, STICKER_RAW_DIR, W001_CARD_DIR, W001_MOB_CARD_DIR, W001_RAW_DIR, W001_PARTS_DIR]:
    os.makedirs(d, exist_ok=True)


def create_new_muse_thread():
    data = json.dumps({"new_thread": True}).encode("utf-8")
    req = urllib.request.Request(
        THREAD_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    print("[Muse API] Creating brand-new thread (new_thread: true)...")
    with urllib.request.urlopen(req, timeout=60) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        print(f"[Muse API] New thread created: session_id={res.get('session_id')} | url={res.get('thread_url')}")
        return res


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


# 0. Start a brand-new thread on Muse Local Server
create_new_muse_thread()

# 1. Generate Master Reference of Base Stickman Warrior ('Tướng Sticker Basic' — Stick War / Supreme Duelist 2D style)
sticker_ref_raw = os.path.join(STICKER_REF_DIR, "sticker_reference_raw.png")
prompt_sticker_ref = (
    "A single full-body 2D stylized Stickman Warrior game character ('Tướng Sticker Basic' in the style of Stick War: Legacy and Supreme Duelist Stickman) "
    "standing in a dynamic 3/4 combat stance facing RIGHT on a 100% pure flat solid #FF00FF magenta background. "
    "CRITICAL: DO NOT draw any cyan box, DO NOT draw any square frame, DO NOT draw any grid lines, and DO NOT draw any weapon! "
    "The background everywhere around the character must be 100% pure flat #FF00FF magenta. "
    "Design & Anatomy of the Stickman Warrior (clean 2D vector-painted game art with bold dark outlines and smooth 2D cel-shaded royal-blue #3B82F6 body segments so joints are clearly articulated): "
    "- Head (`head`): a smooth spherical stickman head with fierce determined white warrior eyes and a sleek dark-slate headband/brow accent, facing 3/4 right. "
    "- Torso (`chest` + `hip`): an athletic tapered stickman upper torso capsule (`chest`) connected to a compact articulated pelvis/waist joint (`hip`) with a simple dark utility belt band. "
    "- Arms: clearly articulated capsule upper arms (`arm_upper`), capsule forearms (`arm_lower`), and rounded clenched stickman fists (`hand_front` and `hand_back`) with a thumb knuckle ready to hold any weapon, posed in an open combat stance with arms separated from the body so nothing overlaps. "
    "- Legs: clearly articulated capsule thighs (`leg_thigh`), capsule shins (`leg_shin`), and sleek rounded stickman feet (`foot_front` and `foot_back`) planted in a 3/4 combat stance."
)
call_muse_generate(prompt_sticker_ref, [LAYOUT_1X1], sticker_ref_raw)

# 2. Generate 2x2 Cutout Parts Sheet for Stickman Warrior on pure #FF00FF
sticker_parts_raw = os.path.join(STICKER_RAW_DIR, "sticker_parts_2x2_raw.png")
prompt_sticker_parts = (
    "2x2 grid of 4 isolated 2D game cutout body-part groups for the exact royal-blue #3B82F6 Stickman Warrior from the second reference image, "
    "on a 100% pure flat solid #FF00FF magenta background. "
    "CRITICAL: DO NOT draw any cyan boxes, grid lines, or borders! The entire background must be 100% pure flat #FF00FF magenta: "
    "- Top-Left (Row 1, Col 1): HEAD ONLY (`head`) — the smooth round royal-blue stickman warrior head with fierce white eyes and dark brow headband in 3/4 right view. "
    "- Top-Right (Row 1, Col 2): TORSO & PELVIS SEPARATED (`chest` above, `hip` below with space between them) — the armless, legless royal-blue tapered upper chest capsule and the compact waist/pelvis segment with dark belt band. "
    "- Bottom-Left (Row 2, Col 1): ARM SEGMENTS SEPARATED (`arm_upper`, `arm_lower`, and rounded gripping fist `hand` spaced apart with clear #FF00FF gap between each piece) — smooth royal-blue capsule limb segments with bold dark outlines and rounded joint ends. "
    "- Bottom-Right (Row 2, Col 2): LEG SEGMENTS SEPARATED (`leg_thigh`, `leg_shin`, and rounded stickman foot `foot` spaced apart with clear #FF00FF gap between each piece) — smooth royal-blue capsule leg segments and foot with bold dark outlines."
)
call_muse_generate(prompt_sticker_parts, [LAYOUT_2X2, sticker_ref_raw], sticker_parts_raw)

# 3. Generate Weapon 001 (W001: Hắc Kiếm Tàn Binh — Rarity N) FULL UNCROPPED SPRITE on pure #FF00FF
w001_raw_path = os.path.join(W001_RAW_DIR, "w001_weapon_raw.png")
prompt_w001_sprite = (
    "A single standalone 2D dark-fantasy game weapon sprite on a 100% pure flat solid #FF00FF magenta background. "
    "CRITICAL: DO NOT draw any cyan box, DO NOT draw any square border, DO NOT draw any character or hand! "
    "The entire weapon must fit 100% completely inside the canvas with generous #FF00FF margin on all 4 sides (zero cropped tips!). "
    "Weapon: 'Hắc Kiếm Tàn Binh' (Weapon 001 — Broken/Battle-Notched Black-Iron Greatsword / Broadsword, Common Rarity N). "
    "Design: a heavy, rugged medieval dark-fantasy broadsword with a long two-handed leather-wrapped hilt (clearly showing the primary upper grip section near the crossguard AND a secondary lower grip section above the heavy iron pommel so it can be held 1-handed or 2-handed), "
    "a dull notched dark-iron crossguard, and a wide, battle-scarred blackened iron blade with combat nicks, scratches, and slight rust patina (zero magical neon glow — grounded Common Rarity N iron weapon). "
    "Orientation: placed diagonally from bottom-left (pommel and hilt) to top-right (blade tip), sharp bold dark outlines, rich hand-painted metal and leather texture."
)
call_muse_generate(prompt_w001_sprite, [LAYOUT_1X1], w001_raw_path)

# 4. Generate Weapon 001 HORIZONTAL CARD PREVIEW (884x632 PNG + 354x253 WebP) — Diagonal weapon composition, NO card frame!
w001_card_raw = os.path.join(W001_CARD_DIR, "w001_card_preview_raw.png")
w001_card_png = os.path.join(W001_CARD_DIR, "w001_card_preview.png")
w001_card_webp = os.path.join(W001_MOB_CARD_DIR, "w001_card_preview.webp")

prompt_w001_card = (
    "Horizontal landscape 2D dark-fantasy weapon card illustration (aspect ratio 11:8 horizontal) showcasing the exact weapon 'Hắc Kiếm Tàn Binh' "
    "(battle-notched blackened iron broadsword with long two-handed leather-wrapped hilt and iron crossguard) from the reference image. "
    "COMPOSITION RULE: Because the sword is long, place the entire sword DIAGONALLY across the horizontal rectangular frame (from bottom-left hilt to top-right blade tip) "
    "so the weapon fills the diagonal of the image prominently and heroically without being cropped! "
    "Background: dramatic dark-fantasy stone battlefield ruin with drifting ash, cracked slate rocks, and subtle warm torchlight glinting off the notched black-iron blade. "
    "Pure illustration only — DO NOT draw any card frame, border, text, numbers, or UI icons."
)
call_muse_generate(prompt_w001_card, [w001_raw_path], w001_card_raw)

im_p = Image.open(w001_card_raw).convert("RGB")
pw, ph = im_p.size
target_ratio = 884.0 / 632.0
curr_ratio = pw / float(ph)
if curr_ratio > target_ratio:
    new_w = int(round(ph * target_ratio))
    x0 = (pw - new_w) // 2
    im_p = im_p.crop((x0, 0, x0 + new_w, ph))
elif curr_ratio < target_ratio:
    new_h = int(round(pw / target_ratio))
    y0 = (ph - new_h) // 2
    im_p = im_p.crop((0, y0, pw, y0 + new_h))

im_884 = im_p.resize((884, 632), Image.Resampling.LANCZOS)
im_884.save(w001_card_png, format="PNG")
im_354 = im_p.resize((354, 253), Image.Resampling.LANCZOS)
im_354.save(w001_card_webp, format="WEBP", quality=92)
print(f"[W001 Card Preview] Saved {w001_card_png} (884x632) & {w001_card_webp} (354x253)")
print("=== All Sticker Hero & W001 Muse Generations Complete! ===")
