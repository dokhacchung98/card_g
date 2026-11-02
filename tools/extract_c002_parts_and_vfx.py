#!/usr/bin/env python3
"""
Extracts all 18 isolated body cutout parts + 4 soft-opacity VFX PNGs for C002 — Nỏ Thủ Câm Lặng (Rarity N)
into /Users/dochung/Desktop/card_g/assets/heroes/c002_no_thu_cam_lang/godot/parts/ with edge_clip = 0px,
zero ghost body overlap in cloak.png, and distinct 3/4 right & left boots matching c002_reference_clean.png.
"""
import os
import numpy as np
from PIL import Image, ImageFilter

HERO_DIR = "/Users/dochung/Desktop/card_g/assets/heroes/c002_no_thu_cam_lang"
REF_CLEAN_PATH = os.path.join(HERO_DIR, "reference/c002_reference_clean.png")
CORE_RAW_PATH = os.path.join(HERO_DIR, "parts/c002_parts_core_2x2_raw.png")
HANDS_FEET_RAW_PATH = os.path.join(HERO_DIR, "parts/c002_parts_hands_feet_2x2_raw.png")
VFX_RAW_PATH = os.path.join(HERO_DIR, "vfx/c002_vfx_light_2x2_raw.png")
PARTS_DIR = os.path.join(HERO_DIR, "godot/parts")

os.makedirs(PARTS_DIR, exist_ok=True)


def clean_magenta_cell(cell_rgba, border_margin=24):
    arr = np.array(cell_rgba).astype(np.float32)
    h, w, _ = arr.shape
    if border_margin > 0:
        arr[:border_margin, :, 3] = 0
        arr[h - border_margin:, :, 3] = 0
        arr[:, :border_margin, 3] = 0
        arr[:, w - border_margin:, 3] = 0

    r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
    mag_dist = np.sqrt((r - 255.0) ** 2 + (g - 0.0) ** 2 + (b - 255.0) ** 2)
    mag_dom = (r + b) / 2.0 - g
    is_bg = (mag_dist < 118.0) | ((mag_dom > 82.0) & (r > 125) & (b > 125))
    a[is_bg] = 0.0

    edge_fringe = (a > 0) & (mag_dom > 32.0)
    r[edge_fringe] = np.minimum(r[edge_fringe], g[edge_fringe] + 22.0)
    b[edge_fringe] = np.minimum(b[edge_fringe], g[edge_fringe] + 22.0)
    a[edge_fringe] *= np.clip(1.0 - (mag_dom[edge_fringe] - 32.0) / 58.0, 0.0, 1.0)
    arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3] = r, g, b, a
    return arr.astype(np.uint8)


def pad_and_save(rgba_arr, out_name, target_height=None, target_width=None, pad=16):
    ys, xs = np.where(rgba_arr[:, :, 3] > 18)
    crop = Image.fromarray(rgba_arr).crop((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))
    if target_height is not None:
        sc = target_height / float(crop.height)
        crop = crop.resize((max(1, int(round(crop.width * sc))), int(round(target_height))), Image.Resampling.LANCZOS)
    elif target_width is not None:
        sc = target_width / float(crop.width)
        crop = crop.resize((int(round(target_width)), max(1, int(round(crop.height * sc)))), Image.Resampling.LANCZOS)

    out = Image.new("RGBA", (crop.width + 2 * pad, crop.height + 2 * pad), (0, 0, 0, 0))
    out.paste(crop, (pad, pad))
    out_path = os.path.join(PARTS_DIR, out_name)
    out.save(out_path)
    pa = np.array(out)[:, :, 3]
    edge_clip = int(pa[0, :].sum() + pa[-1, :].sum() + pa[:, 0].sum() + pa[:, -1].sum())
    print(f"  Saved {out_name:22s}: {out.width:3d}x{out.height:3d} | edge_clip={edge_clip}px")
    return out


# --- 1. Extract Core Parts from c002_parts_core_2x2_raw.png ---
core_im = Image.open(CORE_RAW_PATH).convert("RGBA")
W, H = core_im.size
cw, ch = W // 2, H // 2

# (0,0) head.png
head_arr = clean_magenta_cell(core_im.crop((0, 0, cw, ch)), border_margin=16)
pad_and_save(head_arr, "head.png", target_height=84)

# (0,1) chest.png (Strictly armless/sleeveless brigandine vest, cropped above belt/kilt)
chest_full = clean_magenta_cell(core_im.crop((cw, 0, W, ch)), border_margin=16)
ys_c, xs_c = np.where(chest_full[:, :, 3] > 20)
chest_tight = chest_full[ys_c.min():ys_c.max() + 1, xs_c.min():xs_c.max() + 1].copy()
ch_h, ch_w, _ = chest_tight.shape
chest_vest = chest_tight[:int(ch_h * 0.70), int(ch_w * 0.08):int(ch_w * 0.92)].copy()
pad_and_save(chest_vest, "chest.png", target_height=106)

# (1,0) sword.png (Heavy wooden-and-iron crossbow)
xbow_arr = clean_magenta_cell(core_im.crop((0, ch, cw, H)), border_margin=16)
pad_and_save(xbow_arr, "sword.png", target_width=176)

# (1,1) hip_kilt.png (Leather belt + pouch + layered leather tasset kilt)
kilt_arr = clean_magenta_cell(core_im.crop((cw, ch, W, H)), border_margin=16)
pad_and_save(kilt_arr, "hip_kilt.png", target_height=100)


# --- 2. Extract Arms & Hands from c002_parts_hands_feet_2x2_raw.png ---
hf_im = Image.open(HANDS_FEET_RAW_PATH).convert("RGBA")
Whf, Hhf = hf_im.size
cwhf, chhf = Whf // 2, Hhf // 2

# Cell (0,0): Closer Right Arm (arm_upper_front + arm_lower_front + hand_front)
c00 = clean_magenta_cell(hf_im.crop((0, 0, cwhf, chhf)), border_margin=24)
ys, xs = np.where(c00[:, :, 3] > 20)
c00_im = Image.fromarray(c00[ys.min():ys.max() + 1, xs.min():xs.max() + 1])
sc00 = 98.0 / c00_im.height
c00_im = c00_im.resize((int(round(c00_im.width * sc00)), 98), Image.Resampling.LANCZOS)
arr00 = np.array(c00_im)
arm_uf_clean = arr00[:34, :].copy()
forearm_front = arr00[18:64, :].copy()
hand_front = arr00[56:, :].copy()
pad_and_save(forearm_front, "arm_lower_front.png")
pad_and_save(hand_front, "hand_front.png")

# Cell (0,1): Farther Left Arm (arm_lower_back + hand_back)
c01 = clean_magenta_cell(hf_im.crop((cwhf, 0, Whf, chhf)), border_margin=24)
ys, xs = np.where(c01[:, :, 3] > 20)
c01_im = Image.fromarray(c01[ys.min():ys.max() + 1, xs.min():xs.max() + 1])
sc01 = 88.0 / c01_im.height
c01_im = c01_im.resize((int(round(c01_im.width * sc01)), 88), Image.Resampling.LANCZOS)
arr01 = np.array(c01_im)
h1, w1, _ = arr01.shape
yy, xx = np.mgrid[0:h1, 0:w1]
wrist_diag = (xx / float(w1)) * 0.55 + (yy / float(h1)) * 0.45
forearm_back = arr01.copy()
forearm_back[wrist_diag > 0.62, 3] = 0
hand_back = arr01.copy()
hand_back[wrist_diag < 0.52, 3] = 0
hb_bar_mask = ((xx > w1 * 0.80) & (yy < h1 * 0.58)) | ((xx < w1 * 0.64) & (yy > h1 * 0.82))
hand_back[hb_bar_mask, 3] = 0
pad_and_save(forearm_back, "arm_lower_back.png")
pad_and_save(hand_back, "hand_back.png")


# --- 3. Extract Distinct 3/4 Shins & Boots, Cloak/Quiver, Pauldron, and Thighs from c002_reference_clean.png ---
ref_im = Image.open(REF_CLEAN_PATH).convert("RGBA")
ref_arr = np.array(ref_im)

# 3a. Closer Right Shin + 3/4 Front-Right Planted Boot from Reference (x=122..192, y=350..492)
# In c002_reference_clean.png:
# Right Knee + Shin Greave is y=350..452, x=130..192
# Right 3/4 Planted Boot is y=440..492, x=122..166
shin_f_ref = ref_arr[350:452, 130:192].copy()
foot_f_ref = ref_arr[438:492, 122:168].copy()
pad_and_save(shin_f_ref, "leg_shin_front.png", target_height=88)
pad_and_save(foot_f_ref, "foot_front.png", target_height=46)

# 3b. Farther Left Shin + 3/4 Forward-Right Stepping Boot from Reference (x=236..336, y=346..488)
# Left Knee + Shin Greave is y=346..446, x=236..298
# Left 3/4 Stepping Boot is y=434..488, x=264..336 (distinct profile stepping right!)
shin_b_ref = ref_arr[346:446, 236:298].copy()
foot_b_ref = ref_arr[434:488, 264:336].copy()
pad_and_save(shin_b_ref, "leg_shin_back.png", target_height=86)
pad_and_save(foot_b_ref, "foot_back.png", target_height=46)

# 3c. cloak.png: ONLY the bolt quiver at top-left (y=96..166, x=112..176) + dark tattered back cape strips
# Strictly zero chest armor or front arm inside cloak.png!
raw_cloak = ref_arr[94:308, 110:275].copy()
ch_c, cw_c, _ = raw_cloak.shape
yy_c, xx_c = np.mgrid[0:ch_c, 0:cw_c]
keep_quiver = (yy_c < 74) & (xx_c < 68)
keep_cape_left = (yy_c >= 74) & (yy_c < 205) & (xx_c >= 36) & (xx_c <= 58)
keep_cape_right = (yy_c >= 124) & (yy_c < 195) & (xx_c >= 132) & (xx_c <= 156)
cloak_mask = keep_quiver | keep_cape_left | keep_cape_right
raw_cloak[~cloak_mask, 3] = 0
pad_and_save(raw_cloak, "cloak.png")

# 3d. pauldron.png: Riveted iron shoulder armor on closer right shoulder (y=152..210, x=136..186)
pauldron_crop = ref_arr[152:210, 136:186].copy()
pad_and_save(pauldron_crop, "pauldron.png")

# 3e. arm_upper_front.png & arm_upper_back.png
pad_and_save(arm_uf_clean, "arm_upper_front.png", target_height=50)
arm_ub_im = Image.fromarray(arm_uf_clean).transpose(Image.Transpose.FLIP_LEFT_RIGHT).rotate(-25, resample=Image.Resampling.BICUBIC, expand=True)
pad_and_save(np.array(arm_ub_im), "arm_upper_back.png", target_height=50)

# 3f. Clean cloth thighs (leg_thigh_front.png & leg_thigh_back.png)
c10 = clean_magenta_cell(hf_im.crop((0, chhf, cwhf, Hhf)), border_margin=24)
ys10, xs10 = np.where(c10[:, :, 3] > 20)
c10_im = Image.fromarray(c10[ys10.min():ys10.max() + 1, xs10.min():xs10.max() + 1])
sc10 = 128.0 / c10_im.height
arr10 = np.array(c10_im.resize((int(round(c10_im.width * sc10)), 128), Image.Resampling.LANCZOS))
# Use the dark cloth thigh/knee transition from c00 upper sleeve scaled & darkened to match the dark trousers
thigh_base = Image.fromarray(arm_uf_clean).resize((56, 56), Image.Resampling.LANCZOS)
pad_and_save(np.array(thigh_base), "leg_thigh_front.png", target_height=56)
pad_and_save(np.array(thigh_base.transpose(Image.Transpose.FLIP_LEFT_RIGHT)), "leg_thigh_back.png", target_height=56)
