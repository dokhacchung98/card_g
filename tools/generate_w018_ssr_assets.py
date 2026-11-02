#!/usr/bin/env python3
"""
Generate SSR Weapon W018 (C018: Hành Quyết Giả — Huyết Kiếm Hành Quyết) via Muse Local API
strictly following the 3-step SSR Weapon Flow:
1. New Muse Thread (`POST /v1/thread {"new_thread": true}`)
2. STEP 1 — Reference Image (`w018_ref_raw.png` on #FF00FF using `layout_guide_1x1.png`)
3. STEP 2 — 4-Frame (2x2) Animated Weapon Spritesheet (`w018_weapon_anim_2x2_raw.png` on #FF00FF
   using `[w018_ref_raw.png, layout_guide_2x2.png]` in `reference_images`)
4. STEP 3 — Horizontal Diagonal Card Cover (`w018_card_raw.png` -> `w018_card_preview.png` 884x632 & `.webp` 354x253
   using `[w018_ref_raw.png, w018_weapon_anim_2x2_raw.png]` in `reference_images`)
"""
import json
import os
import shutil
import urllib.request
from PIL import Image

API_BASE = "http://127.0.0.1:3456"
LAYOUT_1X1 = "/Users/dochung/Desktop/card_g/layout_guide/layout_guide_1x1.png"
LAYOUT_2X2 = "/Users/dochung/Desktop/card_g/layout_guide/layout_guide_2x2.png"

W018_DIR = "/Users/dochung/Desktop/card_g/assets/weapons/w018_huyet_kiem_hanh_quyet"
REF_DIR = os.path.join(W018_DIR, "reference")
RAW_DIR = os.path.join(W018_DIR, "raw")
CARD_DIR = os.path.join(W018_DIR, "card")
MOBILE_CARD_DIR = "/Users/dochung/Desktop/card_g/assets/mobile/cards"

for d in [REF_DIR, RAW_DIR, CARD_DIR, MOBILE_CARD_DIR]:
    os.makedirs(d, exist_ok=True)


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


print("=== [W018 SSR] 0. Creating new Muse conversation thread ===")
thread_res = post_json(f"{API_BASE}/v1/thread", {"new_thread": True})
print("   Thread response:", thread_res)

# ==============================================================================
# BƯỚC 1: VẼ ẢNH REF CỦA VŨ KHÍ SSR TRƯỚC (1x1 Base Reference Weapon on #FF00FF)
# ==============================================================================
ref_raw_path = os.path.join(REF_DIR, "w018_ref_raw.png")
weapon_raw_path = os.path.join(RAW_DIR, "w018_weapon_raw.png")

ref_prompt = (
    "Single isolated 2D game weapon reference sprite of 'Huyết Kiếm Hành Quyết' "
    "(SSR Legendary Crimson-Gold Executioner Greatsword) on a pure solid flat magenta (#FF00FF) background, "
    "following the 1x1 layout guide. "
    "Place the entire sword DIAGONALLY from bottom-left (pommel and hilt) to top-right (blade tip) "
    "inside the central 70% safe zone with generous solid #FF00FF margin on all 4 sides so 100% of the pommel and blade tip are completely visible and never clipped. "
    "Weapon reference design details: "
    "- Long two-handed royal crimson-and-black grip with gold wire wrapping and a golden dragon-claw pommel holding a glowing blood-ruby orb (providing 2 clear hand-grip positions: Grip 1 near the upper handle behind the guard, Grip 2 on the lower handle above the pommel). "
    "- Majestic golden dragon-wing crossguard with a central faceted crimson blood-gem. "
    "- Broad, imposing obsidian-black executioner greatsword blade with razor-sharp gleaming golden beveled edges and a glowing crimson runic blood-channel running down the center of the blade. "
    "- Clean, bold 2D fantasy game art style with crisp outlines and cel-shaded metallic gold and crimson highlights. "
    "- Pure solid flat #FF00FF magenta background, NO borders, NO boxes, NO text, NO characters."
)
print("=== [W018 SSR] BƯỚC 1: Vẽ Ảnh Ref Vũ Khí SSR (w018_ref_raw.png) ===")
post_json(
    f"{API_BASE}/generate-image",
    {
        "prompt": ref_prompt,
        "reference_images": [LAYOUT_1X1],
        "save_path": ref_raw_path,
    },
)
shutil.copyfile(ref_raw_path, weapon_raw_path)
print("   Saved SSR Weapon Ref Raw ->", ref_raw_path)

# ==============================================================================
# BƯỚC 2: TẠO ẢNH SPRITESHEET ANIMATION CỦA VŨ KHÍ TỪ ẢNH REF (2x2 4-Frame Loop)
# ==============================================================================
anim_raw_path = os.path.join(RAW_DIR, "w018_weapon_anim_2x2_raw.png")
aura_compat_path = os.path.join(RAW_DIR, "w018_aura_2x2_raw.png")

anim_prompt = (
    "2x2 4-frame animated 2D weapon spritesheet of the EXACT SSR Legendary Greatsword 'Huyết Kiếm Hành Quyết' "
    "from the attached weapon reference image, on a pure solid flat magenta (#FF00FF) background, "
    "strictly following the attached 2x2 layout guide. "
    "Each of the 4 quadrant cells (top-left, top-right, bottom-left, bottom-right) MUST show the FULL uncropped greatsword "
    "at the EXACT same diagonal angle (bottom-left pommel to top-right blade tip), exact same size, proportions, two-handed grip, golden dragon-wing crossguard, and obsidian-gold blade as the reference image, centered inside its cell with generous #FF00FF margin and zero cell-edge clipping. "
    "Across the 4 frames, animate the SSR crimson-gold magical energy aura and blood-fire wrapping directly around the sword blade in a seamless 4-frame loop: "
    "- Frame 1 (top-left): The crimson runes along the blade core ignite bright red while golden-crimson soul flames begin rising tightly along the blade edges. "
    "- Frame 2 (top-right): Blazing crimson-gold flames and crackling red-gold lightning arcs spiral up the obsidian-gold blade from the dragon crossguard to the tip. "
    "- Frame 3 (bottom-left): Peak SSR legendary power — intense golden-crimson dragon fire, glowing runic energy, and bright red-gold electric arcs surge around the entire sword blade. "
    "- Frame 4 (bottom-right): Pulsing crimson-gold flames and glowing embers settle smoothly along the blade edges to loop back to Frame 1. "
    "Pure solid flat #FF00FF magenta background in all 4 cells, NO grid lines, NO borders, NO boxes, NO text."
)
print("=== [W018 SSR] BƯỚC 2: Tạo Ảnh Spritesheet Animation 2x2 của Vũ Khí từ Ảnh Ref ===")
post_json(
    f"{API_BASE}/generate-image",
    {
        "prompt": anim_prompt,
        "reference_images": [ref_raw_path, LAYOUT_2X2],
        "save_path": anim_raw_path,
    },
)
shutil.copyfile(anim_raw_path, aura_compat_path)
print("   Saved SSR Weapon 2x2 Animation Spritesheet Raw ->", anim_raw_path)

# ==============================================================================
# BƯỚC 3: CUỐI CÙNG MỚI TẠO ẢNH BÌA CỦA CARD TỪ ẢNH REF & SPRITESHEET VŨ KHÍ
# ==============================================================================
card_raw_path = os.path.join(RAW_DIR, "w018_card_raw.png")
card_prompt = (
    "Horizontal rectangular 2D fantasy card game weapon cover illustration (landscape 4:3 aspect ratio) "
    "of the EXACT SSR Legendary Greatsword 'Huyết Kiếm Hành Quyết' shown in the attached weapon reference and animated weapon spritesheet. "
    "Keep 100% identical weapon design from the reference: the golden dragon-claw pommel holding a crimson ruby orb, the long two-handed crimson-and-black wire-wrapped handle, "
    "the ornate golden dragon-wing crossguard with its central blood-gem, and the broad obsidian-black blade with gleaming golden beveled edges and glowing red runic fuller. "
    "Because the sword is long, place the greatsword DIAGONALLY from bottom-left (hilt) to top-right (blade tip) filling the horizontal frame majestically, "
    "surrounded by its signature SSR blazing crimson-gold soul flames and crackling red-gold lightning arcs over a dark atmospheric ancient execution altar background. "
    "Masterpiece 2D digital card illustration, NO UI frame, NO borders, NO text, NO characters."
)
print("=== [W018 SSR] BƯỚC 3: Tạo Ảnh Bìa Card (884x632) từ Ảnh Ref & Spritesheet Vũ Khí ===")
post_json(
    f"{API_BASE}/generate-image",
    {
        "prompt": card_prompt,
        "reference_images": [ref_raw_path, anim_raw_path],
        "save_path": card_raw_path,
    },
)

im_card = Image.open(card_raw_path).convert("RGB")
w, h = im_card.size
target_ratio = 884.0 / 632.0
cur_ratio = w / float(h)
if cur_ratio > target_ratio:
    new_w = int(round(h * target_ratio))
    x0 = (w - new_w) // 2
    im_card = im_card.crop((x0, 0, x0 + new_w, h))
else:
    new_h = int(round(w / target_ratio))
    y0 = (h - new_h) // 2
    im_card = im_card.crop((0, y0, w, y0 + new_h))

card_png = os.path.join(CARD_DIR, "w018_card_preview.png")
card_webp = os.path.join(MOBILE_CARD_DIR, "c018_hanh_quyet_gia.webp")
card_w_webp = os.path.join(MOBILE_CARD_DIR, "w018_huyet_kiem_hanh_quyet.webp")
im_card.resize((884, 632), Image.Resampling.LANCZOS).save(card_png, "PNG")
im_card.resize((354, 253), Image.Resampling.LANCZOS).save(card_webp, "WEBP", quality=92)
im_card.resize((354, 253), Image.Resampling.LANCZOS).save(card_w_webp, "WEBP", quality=92)
print("   Saved SSR Card Preview ->", card_png)
print("ALL 3 STEPS (1. Ref -> 2. Weapon Animation Spritesheet -> 3. Card Cover) COMPLETE!")
