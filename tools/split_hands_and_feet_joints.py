#!/usr/bin/env python3
"""
Splits the forearm+hand and shin+boot textures at the anatomical Wrist and Ankle joints
with a rounded overlapping joint cap so that:
- UpperArm (Shoulder -> Elbow)
- Forearm  (Elbow -> Wrist)
- Hand     (Wrist -> Fingers / Grip)
- Thigh    (Hip -> Knee)
- Shin     (Knee -> Ankle)
- Foot     (Ankle -> Boot Toe)
are all independent Bone2D nodes with full Spine bone segments!
"""
import os
import numpy as np
from PIL import Image

PARTS_DIR = "/Users/dochung/Desktop/card_g/assets/heroes/c001_hac_kiem_tan_binh/godot/parts"
RAW_FIX_PATH = "/Users/dochung/Desktop/card_g/assets/heroes/c001_hac_kiem_tan_binh/parts/c001_parts_hands_feet_fix_2x2_raw.png"
REF_CLEAN_PATH = "/Users/dochung/Desktop/card_g/assets/heroes/c001_hac_kiem_tan_binh/reference/c001_reference_clean.png"

raw_im = Image.open(RAW_FIX_PATH).convert("RGBA")
W, H = raw_im.size
cw, ch = W // 2, H // 2

def clean_cell(cell_rgba, border_margin=18):
    arr = np.array(cell_rgba).astype(np.float32)
    h, w, _ = arr.shape
    arr[:border_margin, :, 3] = 0
    arr[h-border_margin:, :, 3] = 0
    arr[:, :border_margin, 3] = 0
    arr[:, w-border_margin:, 3] = 0

    r, g, b, a = arr[:,:,0], arr[:,:,1], arr[:,:,2], arr[:,:,3]
    mag_dist = np.sqrt((r - 255.0)**2 + (g - 0.0)**2 + (b - 255.0)**2)
    mag_dom = (r + b) / 2.0 - g
    is_bg = (mag_dist < 115.0) | ((mag_dom > 85.0) & (r > 130) & (b > 130))
    a[is_bg] = 0.0

    edge_fringe = (a > 0) & (mag_dom > 35.0)
    r[edge_fringe] = np.minimum(r[edge_fringe], g[edge_fringe] + 25.0)
    b[edge_fringe] = np.minimum(b[edge_fringe], g[edge_fringe] + 25.0)
    a[edge_fringe] *= np.clip(1.0 - (mag_dom[edge_fringe] - 35.0) / 60.0, 0.0, 1.0)
    arr[:,:,0], arr[:,:,1], arr[:,:,2], arr[:,:,3] = r, g, b, a
    return arr.astype(np.uint8)

def pad_and_save(rgba_arr, out_name, pad=16):
    ys, xs = np.where(rgba_arr[:, :, 3] > 15)
    crop = Image.fromarray(rgba_arr).crop((int(xs.min()), int(ys.min()), int(xs.max())+1, int(ys.max())+1))
    out = Image.new("RGBA", (crop.width + 2*pad, crop.height + 2*pad), (0, 0, 0, 0))
    out.paste(crop, (pad, pad))
    out_path = os.path.join(PARTS_DIR, out_name)
    out.save(out_path)
    print(f"  Saved {out_name:22s}: {out.size}")
    return out

# 1. Cell 00: Right Forearm (arm_lower_front) + Right Hand (hand_front)
c00 = clean_cell(raw_im.crop((0, 0, cw, ch)))
ys, xs = np.where(c00[:, :, 3] > 20)
c00_crop = c00[ys.min():ys.max()+1, xs.min():xs.max()+1].copy()
c00_im = Image.fromarray(c00_crop)
sc00 = 96.0 / c00_im.height
c00_im = c00_im.resize((int(round(c00_im.width * sc00)), 96), Image.Resampling.LANCZOS)
arr00 = np.array(c00_im)
h0, w0, _ = arr00.shape
yy, xx = np.mgrid[0:h0, 0:w0]
proj00 = (xx / w0) * 0.72 + (1.0 - yy / h0) * 0.69
arr00[proj00 > 0.95, 3] = 0

wrist_line_00 = (yy / h0) - (xx / w0) * 0.25
forearm_front_arr = arr00.copy()
forearm_front_arr[wrist_line_00 > 0.56, 3] = 0

hand_front_arr = arr00.copy()
hand_front_arr[wrist_line_00 < 0.46, 3] = 0

pad_and_save(forearm_front_arr, "arm_lower_front.png")
pad_and_save(hand_front_arr, "hand_front.png")

# 2. Cell 01: Left Forearm (arm_lower_back) + Left Gripping Hand (hand_back)
c01 = clean_cell(raw_im.crop((cw, 0, W, ch)))
ys, xs = np.where(c01[:, :, 3] > 20)
c01_crop = c01[ys.min():ys.max()+1, xs.min():xs.max()+1].copy()
c01_im = Image.fromarray(c01_crop)
sc01 = 92.0 / c01_im.height
c01_im = c01_im.resize((int(round(c01_im.width * sc01)), 92), Image.Resampling.LANCZOS)
arr01 = np.array(c01_im)
h1, w1, _ = arr01.shape
yy, xx = np.mgrid[0:h1, 0:w1]
proj01 = (1.0 - xx / w1) * 0.72 + (1.0 - yy / h1) * 0.69
arr01[proj01 > 0.96, 3] = 0

wrist_line_01 = (yy / h1) + (xx / w1) * 0.28
forearm_back_arr = arr01.copy()
forearm_back_arr[wrist_line_01 > 0.86, 3] = 0

hand_back_arr = arr01.copy()
hand_back_arr[wrist_line_01 < 0.74, 3] = 0

pad_and_save(forearm_back_arr, "arm_lower_back.png")
pad_and_save(hand_back_arr, "hand_back.png")

# 3. Right Lower Leg:
# Use cell_10's clean, unclipped iron knee-cap + shin greave for leg_shin_front.png (Knee -> Ankle),
# and the 3/4 front-angled laced leather boot from c001_reference_clean.png for foot_front.png (Ankle -> Toe)!
c10 = clean_cell(raw_im.crop((0, ch, cw, H)))
ys10, xs10 = np.where(c10[:,:,3] > 20)
sf_tight = Image.fromarray(c10).crop((int(xs10.min()), int(ys10.min()), int(xs10.max())+1, int(ys10.max())+1))
scale_sf = 138.0 / sf_tight.height
sf_resized = np.array(sf_tight.resize((int(round(sf_tight.width * scale_sf)), 138), Image.Resampling.LANCZOS))
shin_only_front = sf_resized.copy()
shin_only_front[102:, :, 3] = 0
pad_and_save(shin_only_front, "leg_shin_front.png")

ref_clean = Image.open(REF_CLEAN_PATH).convert("RGBA")
ref_arr = np.array(ref_clean)
# In c001_reference_clean.png, the 3/4 front-angled right boot is at x=[120..190], y=[418..496]
boot_front = ref_arr[416:496, 122:188].copy()
# Scale slightly so height is 48px
bf_im = Image.fromarray(boot_front)
bf_im = bf_im.resize((int(round(bf_im.width * 0.86)), int(round(bf_im.height * 0.86))), Image.Resampling.LANCZOS)
pad_and_save(np.array(bf_im), "foot_front.png")

# 4. Left Lower Leg (leg_shin_back = Greave Knee->Ankle, foot_back = Boot Ankle->Toe)
c11 = clean_cell(raw_im.crop((cw, ch, W, H)))
ys11, xs11 = np.where(c11[:,:,3] > 20)
sb_tight = Image.fromarray(c11).crop((int(xs11.min()), int(ys11.min()), int(xs11.max())+1, int(ys11.max())+1))
scale_sb = 134.0 / sb_tight.height
sb_resized = np.array(sb_tight.resize((int(round(sb_tight.width * scale_sb)), 134), Image.Resampling.LANCZOS))

shin_only_back = sb_resized.copy()
shin_only_back[100:, :, 3] = 0
foot_only_back = sb_resized.copy()
foot_only_back[:88, :, 3] = 0

pad_and_save(shin_only_back, "leg_shin_back.png")
pad_and_save(foot_only_back, "foot_back.png")
