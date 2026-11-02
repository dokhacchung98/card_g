#!/usr/bin/env python3
"""
Step 2, 3, 4 & 5 Generator for Hero 004 (C04: Kỵ Binh Gỉ Sét — Rusted Cavalry Lancer, Rarity N):
- FIRST creates a brand-new thread on Muse Local Server (POST /v1/thread {"new_thread": true}) so zero old context bleeds over!
- Generates 1x1 Master Reference on pure flat #FF00FF (zero square frame, completely distinct open-faced grizzled bearded veteran face with rusted kettle-helm, holding heavy rusted iron cavalry shock-lance in FRONT HAND).
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

BASE_URL = "http://127.0.0.1:3456"
API_URL = f"{BASE_URL}/generate-image"
THREAD_URL = f"{BASE_URL}/v1/thread"

HERO_DIR = "/Users/dochung/Desktop/card_g/assets/heroes/c004_ky_binh_gi_set"
REF_DIR = os.path.join(HERO_DIR, "reference")
CARD_DIR = os.path.join(HERO_DIR, "card")
MOB_CARD_DIR = "/Users/dochung/Desktop/card_g/assets/mobile/heroes/c004_ky_binh_gi_set/card"
PARTS_RAW_DIR = os.path.join(HERO_DIR, "parts")
VFX_RAW_DIR = os.path.join(HERO_DIR, "vfx")

LAYOUT_1X1 = "/Users/dochung/Desktop/card_g/layout_guide/layout_guide_1x1.png"
LAYOUT_2X2 = "/Users/dochung/Desktop/card_g/layout_guide/layout_guide_2x2.png"
LAYOUT_2X3 = "/Users/dochung/Desktop/card_g/layout_guide/layout_guide_2x3.png"

for d in [REF_DIR, CARD_DIR, MOB_CARD_DIR, PARTS_RAW_DIR, VFX_RAW_DIR]:
    os.makedirs(d, exist_ok=True)


def create_new_muse_thread():
    data = json.dumps({"new_thread": True}).encode("utf-8")
    req = urllib.request.Request(
        THREAD_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    print("[Muse API] Creating brand-new thread (new_thread: true) to clear old context...")
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


# 0. Create a fresh Muse thread so zero previous hero context remains
create_new_muse_thread()

# 1. Generate Master Reference (1x1, 3/4 facing RIGHT, distinct open bearded veteran face, Weapon held in FRONT RIGHT HAND!)
ref_raw_path = os.path.join(REF_DIR, "c004_reference_raw.png")
ref_clean_path = os.path.join(REF_DIR, "c004_reference_clean.png")

prompt_ref = (
    "A single full-body 2D stylized dark-fantasy game character sprite on a 100% pure flat solid #FF00FF magenta background. "
    "IMPORTANT: Use the reference layout guide ONLY for invisible proportion sizing — DO NOT draw any cyan square box, DO NOT draw any blue frame, "
    "DO NOT draw any white dashed crosshair lines, and DO NOT draw any border! The entire background around the character must be 100% pure flat #FF00FF magenta. "
    "Art Style: stylized hand-painted 2D dark-fantasy RPG character sprite with bold clean dark outlines, rich painted metal/rust textures, game-ready readability, "
    "heroic 5.5-heads-tall proportions, occupying 68% of canvas height with generous #FF00FF margin on all sides. "
    "Character: 'Kỵ Binh Gỉ Sét' (Rusted Cavalry Shock Lancer), Common Rarity N physical charge/knockback warrior. "
    "DISTINCT FACE & HEAD (NO hood, NO cloth mask, NO closed visor!): "
    "An older, grizzled veteran human lancer with a completely UNCOVERED, expressive weathered face in 3/4 view facing RIGHT: "
    "rugged square jaw, a thick braided reddish-brown and grey handlebar mustache and short warrior beard, a prominent diagonal battle scar across his cheek, "
    "bushy furrowed brows, and fierce amber-brown human eyes. On the top of his head he wears an open-faced, dented rusted-iron kettle-helm / morion helmet "
    "with orange-brown rust patina and iron rivets, leaving his entire face 100% visible. "
    "Armor & Outfit (Common Rarity N — zero magical glow, grounded weathered metal): "
    "corroded rusted-iron cavalry breastplate with orange-brown rust streaks over a dusty ochre-tan quilted gambeson, "
    "a heavy riveted rusted-iron shoulder pauldron on his closer right shoulder, a tattered dusty rust-ochre half-cloak hanging behind his back, "
    "layered rusted iron tasset plates and worn brown leather belt at the waist, tan leather riding breeches, and rusted iron cavalry greaves with spurred iron boots. "
    "Pose & Anatomy (3/4 view facing RIGHT, open limb separation so joints do not overlap): "
    "- MANDATORY FRONT-HAND WEAPON GRIP: Closer RIGHT arm (viewer's left, foreground Front Arm) is angled forward-right in front of his torso, "
    "clearly showing his rusted iron vambrace and the DORSAL BACK of his right hand (fingers/knuckles wrapped inward around the shaft) "
    "gripping a heavy, battle-worn RUSTED IRON CAVALRY SHOCK-LANCE / BOAR-SPEAR with a flanged iron hand-guard and wide rusted steel spearhead pointed diagonally forward-right in the foreground! "
    "- Farther LEFT arm (viewer's right, Back Arm) is extended slightly forward-right clear of his chest, holding a small battered round rusted-iron buckler shield strapped to his left forearm/fist. "
    "- Closer RIGHT leg (viewer's left) planted in 3/4 front-right perspective; farther LEFT leg (viewer's right) stepping forward-right in 3/4 profile."
)
call_muse_generate(prompt_ref, [LAYOUT_1X1], ref_raw_path)

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
    ra[spill] *= np.clip(1.0 - (mdom[spill] - 25.0) / 55.0, 0.25, 1.0)
arr_ref[:, :, 0], arr_ref[:, :, 1], arr_ref[:, :, 2], arr_ref[:, :, 3] = rr, rg, rb, ra
Image.fromarray(arr_ref.astype(np.uint8), mode="RGBA").save(ref_clean_path)
print(f"[Clean Ref] Saved {ref_clean_path}")

# 2. Generate Horizontal Portrait Preview (884x632 PNG + 354x253 WebP, NO card frame)
portrait_raw_path = os.path.join(CARD_DIR, "c004_portrait_raw.png")
portrait_png_path = os.path.join(CARD_DIR, "c004_portrait_preview.png")
portrait_webp_path = os.path.join(MOB_CARD_DIR, "c004_portrait_preview.webp")

prompt_portrait = (
    "Horizontal landscape 2D dark-fantasy character portrait illustration (aspect ratio 11:8 horizontal) of the exact 'Kỵ Binh Gỉ Sét' (Rusted Cavalry Shock Lancer) "
    "from the reference image. Show a dramatic waist-up close-up of this grizzled, scarred veteran lancer with his thick reddish-brown braided mustache and beard, "
    "fierce amber eyes, and open-faced rusted iron kettle-helm, wearing his corroded rusted-iron breastplate and tattered ochre-rust cloak, "
    "charging forward through a dusty, mist-shrouded ancient battlefield strewn with rusted spears and broken war-wheels. "
    "He thrusts his heavy rusted iron cavalry shock-lance forward in his right hand while bracing his battered iron buckler on his left arm, kicking up sparks and dust. "
    "Pure illustration only — DO NOT draw any card frame, border, text, or UI icons."
)
call_muse_generate(prompt_portrait, [ref_raw_path], portrait_raw_path)

im_p = Image.open(portrait_raw_path).convert("RGB")
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
im_884.save(portrait_png_path, format="PNG")
im_354 = im_p.resize((354, 253), Image.Resampling.LANCZOS)
im_354.save(portrait_webp_path, format="WEBP", quality=92)
print(f"[Portrait] Saved {portrait_png_path} (884x632) & {portrait_webp_path} (354x253)")

# 3. Generate 2x2 Core Cutout Parts Sheet (head, chest, rusted cavalry lance, waist tasset kilt) on pure #FF00FF (NO boxes!)
core_raw_path = os.path.join(PARTS_RAW_DIR, "c004_parts_core_2x2_raw.png")
prompt_core = (
    "2x2 grid of 4 isolated 2D game character body-part cutout sprites for the exact 'Kỵ Binh Gỉ Sét' (Rusted Cavalry Lancer) from the second reference image, "
    "arranged in 2 rows by 2 columns on a 100% pure flat solid #FF00FF magenta background. "
    "CRITICAL: Use the first image (2x2 layout guide) ONLY for invisible cell placement — DO NOT draw any cyan boxes, DO NOT draw any grid lines, "
    "and DO NOT draw any borders! The background everywhere must be 100% pure flat #FF00FF magenta, and each part must sit cleanly inside the center 65% of its cell: "
    "- Top-Left (Row 1, Col 1): HEAD ONLY (`head`) — the grizzled scarred veteran head in 3/4 right view with thick reddish-brown mustache/beard, amber eyes, and open-faced rusted iron kettle-helm, rounded neck base. "
    "- Top-Right (Row 1, Col 2): TORSO / CHEST CUIRASS ONLY (`chest`) — armless, headless corroded rusted-iron cavalry breastplate with orange-brown rust patina over ochre gambeson, rounded shoulder/hip sockets. "
    "- Bottom-Left (Row 2, Col 1): RUSTED CAVALRY SHOCK-LANCE ONLY (`sword`) — the standalone heavy battle-worn rusted iron cavalry shock-lance / boar-spear with flanged iron guard and wide rusted spearhead, angled diagonally down-right, NO hand attached. "
    "- Bottom-Right (Row 2, Col 2): WAIST TASSET KILT & BELT ONLY (`hip_kilt`) — layered rusted iron tasset plates over worn brown leather cavalry belt and riding skirt, no legs attached."
)
call_muse_generate(prompt_core, [LAYOUT_2X2, ref_raw_path], core_raw_path)

# 4. Generate 2x3 Limbs Cutout Parts Sheet (cloak, pauldron, upper arms, thighs) on pure #FF00FF (NO boxes!)
limbs_raw_path = os.path.join(PARTS_RAW_DIR, "c004_parts_limbs_2x3_raw.png")
prompt_limbs = (
    "2x3 grid (2 rows, 3 columns) of 6 isolated 2D game character limb cutout sprites for the exact 'Kỵ Binh Gỉ Sét' from the second reference image, "
    "on a 100% pure flat solid #FF00FF magenta background. "
    "CRITICAL: DO NOT draw any cyan boxes, grid lines, or borders from the layout guide! Background must be 100% solid flat #FF00FF magenta: "
    "- Row 1, Col 1: BACK HALF-CLOAK ONLY (`cloak`) — tattered dusty rust-ochre cavalry half-cloak in 3/4 view. "
    "- Row 1, Col 2: SHOULDER PAULDRON ONLY (`pauldron`) — single riveted rusted-iron cavalry shoulder guard with rust patina. "
    "- Row 1, Col 3: FRONT RIGHT UPPER ARM ONLY (`arm_upper_front`) — ochre gambeson upper sleeve with rusted iron plate in 3/4 view, rounded shoulder and elbow caps. "
    "- Row 2, Col 1: BACK LEFT UPPER ARM ONLY (`arm_upper_back`) — darker shaded upper sleeve in 3/4 view, rounded shoulder and elbow caps. "
    "- Row 2, Col 2: FRONT RIGHT THIGH ONLY (`leg_thigh_front`) — tan-brown leather riding breech thigh with rusted iron thigh-guard, rounded hip and knee caps. "
    "- Row 2, Col 3: BACK LEFT THIGH ONLY (`leg_thigh_back`) — darker shaded leather riding breech thigh, rounded hip and knee caps."
)
call_muse_generate(prompt_limbs, [LAYOUT_2X3, ref_raw_path], limbs_raw_path)

# 5. Generate 2x2 Hands/Forearms & Greave-Boots Sheet on pure #FF00FF (NO boxes!)
hf_raw_path = os.path.join(PARTS_RAW_DIR, "c004_parts_hands_feet_2x2_raw.png")
prompt_hf = (
    "2x2 grid (2 rows, 2 columns) of 4 isolated 2D game character forearm and armored leg-boot cutout sprites for the exact 'Kỵ Binh Gỉ Sét' from the second reference image, "
    "on a 100% pure flat solid #FF00FF magenta background. "
    "CRITICAL: DO NOT draw any cyan boxes, grid lines, or borders! Background must be 100% solid flat #FF00FF magenta: "
    "- Top-Left (Row 1, Col 1): FRONT RIGHT FOREARM & GRIPPING HAND (`arm_lower_front` + `hand_front`) — rusted iron vambrace forearm and leather-gloved right hand showing DORSAL BACK of hand with fingers curled inward to grip a lance shaft (no weapon attached). "
    "- Top-Right (Row 1, Col 2): BACK LEFT FOREARM WITH SMALL BUCKLER (`arm_lower_back` + `hand_back`) — left forearm with a small battered round rusted-iron buckler shield and gloved fist in 3/4 right view. "
    "- Bottom-Left (Row 2, Col 1): FRONT RIGHT SHIN GREAVE & SPURRED BOOT (`leg_shin_front` + `foot_front`) — rusted iron cavalry shin greave and iron riding boot with spur planted in 3/4 front-right view. "
    "- Bottom-Right (Row 2, Col 2): BACK LEFT SHIN GREAVE & SPURRED BOOT (`leg_shin_back` + `foot_back`) — rusted iron cavalry shin greave and iron riding boot stepping forward-right in 3/4 profile."
)
call_muse_generate(prompt_hf, [LAYOUT_2X2, ref_raw_path], hf_raw_path)

# 6. Generate 2x2 Lightweight VFX Sheet for 'Lao Kích' (Charge Thrust Wave, Heavy Knockback Shockwave, Rust/Iron Sparks, Charge Dust) on pure #FF00FF
vfx_raw_path = os.path.join(VFX_RAW_DIR, "c004_vfx_light_2x2_raw.png")
prompt_vfx = (
    "2x2 grid (2 rows, 2 columns) of 4 isolated 2D game combat VFX sprites for a physical cavalry lance charge skill ('Lao Kích') on a 100% pure flat solid #FF00FF magenta background. "
    "CRITICAL: DO NOT draw any cyan boxes, grid lines, or borders! Background must be 100% pure flat #FF00FF magenta, and each VFX element must be centered inside its quadrant with generous margin: "
    "- Top-Left (Row 1, Col 1): `fx_slash` — a sharp silver-and-amber forward lance thrust wind-pierce streak pointing right. "
    "- Top-Right (Row 1, Col 2): `fx_slash_heavy` — an explosive golden-orange and steel-white conical shockwave ring + spear-charge impact cone ('Lao Kích' knockback wave) blasting right. "
    "- Bottom-Left (Row 2, Col 1): `fx_spark` — a bright burst of glowing orange-gold metal clash sparks and flying iron shards. "
    "- Bottom-Right (Row 2, Col 2): `fx_dust` — a dynamic puff of warm earthy brown-grey ground dust kick-up cloud."
)
call_muse_generate(prompt_vfx, [LAYOUT_2X2], vfx_raw_path)
print("=== All C004 Muse API Generations Complete! ===")
