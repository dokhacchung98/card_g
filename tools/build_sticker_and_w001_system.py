#!/usr/bin/env python3
"""
Builds the Complete Stickman 4-Team Base Hero + Per-Card Weapon System (Starting with W001: Hắc Kiếm Tàn Binh):
1. Extracts all Stickman Base Parts from sticker_parts_2x2_raw.png with 0px edge clipping.
2. Generates 4 Team Color sets (team_blue, team_red, team_green, team_amber) + neutral base set.
3. Extracts Weapon 001 (W001: Hắc Kiếm Tàn Binh) full sprite on #FF00FF with 2 Grip Points (Grip 1 & Grip 2), offhand weapon option, aura, and 4 soft-opacity VFX.
4. Builds QC Audit Boards (4 Teams + Parts + Grip 1/2 + All 6 Actions with 0px edge clipping).
5. Generates Godot 4 Scenes (.tscn & .gd) and the Interactive HTML Sticker+Weapon Editor (sticker_weapon_editor.html) with Save to .tscn!
"""
import os
import json
import math
import glob
import base64
import shutil
from collections import deque
import numpy as np
from PIL import Image, ImageDraw, ImageFont

STICKER_DIR = "/Users/dochung/Desktop/card_g/assets/sticker_hero"
STICKER_REF_RAW = os.path.join(STICKER_DIR, "reference/sticker_reference_raw.png")
STICKER_REF_CLEAN = os.path.join(STICKER_DIR, "reference/sticker_reference_clean.png")
STICKER_PARTS_RAW = os.path.join(STICKER_DIR, "raw/sticker_parts_simple_raw.png")
STICKER_TORSO_RAW = os.path.join(STICKER_DIR, "raw/sticker_torso_parts_raw.png")
STICKER_FEET_RAW = os.path.join(STICKER_DIR, "raw/sticker_feet_raw.png")
STICKER_GODOT_DIR = os.path.join(STICKER_DIR, "godot")
STICKER_PARTS_ROOT = os.path.join(STICKER_GODOT_DIR, "parts")
STICKER_QC_DIR = os.path.join(STICKER_DIR, "qc_previews")

W001_DIR = "/Users/dochung/Desktop/card_g/assets/weapons/w001_hac_kiem_tan_binh"
W001_RAW_PATH = os.path.join(W001_DIR, "raw/w001_weapon_raw.png")
W001_CARD_PNG = os.path.join(W001_DIR, "card/w001_card_preview.png")
W001_PARTS_DIR = os.path.join(W001_DIR, "parts")
W001_GODOT_DIR = os.path.join(W001_DIR, "godot")
W001_QC_DIR = os.path.join(W001_DIR, "qc_previews")

C001_VFX_RAW = "/Users/dochung/Desktop/card_g/assets/heroes/c001_hac_kiem_tan_binh/vfx/c001_vfx_light_2x2_raw.png"
ARTIFACT_DIR = "/Users/dochung/.gemini/antigravity-cli/brain/e8f2a241-a2ff-47d9-a161-5cdae075b6ce"

TEAMS = ["team_blue", "team_red", "team_green", "team_amber", "base"]
for d in [STICKER_GODOT_DIR, STICKER_QC_DIR, W001_PARTS_DIR, W001_GODOT_DIR, W001_QC_DIR, ARTIFACT_DIR]:
    os.makedirs(d, exist_ok=True)
for t in TEAMS:
    os.makedirs(os.path.join(STICKER_PARTS_ROOT, t), exist_ok=True)
    os.makedirs(f"/Users/dochung/Desktop/card_g/assets/mobile/sticker_hero/parts/{t}", exist_ok=True)
os.makedirs("/Users/dochung/Desktop/card_g/assets/mobile/weapons/w001_hac_kiem_tan_binh/parts", exist_ok=True)


def clean_magenta(im_in, border_margin=6):
    arr = np.array(im_in.convert("RGBA")).astype(np.float32)
    h, w, _ = arr.shape
    if border_margin > 0:
        arr[:border_margin, :, 3] = 0
        arr[h - border_margin :, :, 3] = 0
        arr[:, :border_margin, 3] = 0
        arr[:, w - border_margin :, 3] = 0
    r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
    mag_dist = np.sqrt((r - 255.0) ** 2 + (g - 0.0) ** 2 + (b - 255.0) ** 2)
    mag_dom = (r + b) / 2.0 - g
    is_bg = (mag_dist < 120.0) | ((mag_dom > 80.0) & (r > 125) & (b > 125))
    a[is_bg] = 0.0
    fringe = (a > 0) & (mag_dom > 18.0)
    r[fringe] = np.minimum(r[fringe], g[fringe] + 8.0)
    b[fringe] = np.minimum(b[fringe], np.maximum(g[fringe] + 12.0, b[fringe] * 0.75))
    a[fringe] *= np.clip(1.0 - (mag_dom[fringe] - 25.0) / 60.0, 0.2, 1.0)
    arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3] = r, g, b, a
    return arr.astype(np.uint8)


def keep_largest_component(rgba_arr):
    alpha = rgba_arr[:, :, 3] > 20
    h, w = alpha.shape
    visited = np.zeros_like(alpha, dtype=bool)
    best_coords = None
    best_count = 0
    for y in range(h):
        xs = np.where(alpha[y] & ~visited[y])[0]
        for x0 in xs:
            if visited[y, x0]:
                continue
            stack = [(y, int(x0))]
            visited[y, x0] = True
            coords = []
            while stack:
                cy, cx = stack.pop()
                coords.append((cy, cx))
                for ny in range(max(0, cy - 1), min(h, cy + 2)):
                    for nx in range(max(0, cx - 1), min(w, cx + 2)):
                        if alpha[ny, nx] and not visited[ny, nx]:
                            visited[ny, nx] = True
                            stack.append((ny, nx))
            if len(coords) > best_count:
                best_count = len(coords)
                best_coords = coords
    out = np.zeros_like(rgba_arr)
    if best_coords:
        ys, xs = zip(*best_coords)
        out[ys, xs] = rgba_arr[ys, xs]
    return out


def recolor_stickman_team(rgba_arr, team_name, darken=1.0):
    """
    Transforms the royal-blue body pixels of the Stickman into:
    - team_blue:  Royal Blue (#3B82F6)
    - team_red:   Crimson Red (#EF4444)
    - team_green: Emerald Green (#22C55E)
    - team_amber: Golden Amber (#F59E0B)
    - base:       Neutral Silver-White (#E2E8F0)
    Preserves black outlines, white eyes, and dark slate headband/belt!
    """
    out = rgba_arr.astype(np.float32).copy()
    r, g, b, a = out[:, :, 0], out[:, :, 1], out[:, :, 2], out[:, :, 3]

    # Blue body mask: blue channel dominates red & green, and not pure white eye or black outline
    blue_excess = b - np.maximum(r, g)
    is_body = (a > 10) & (blue_excess > 25.0) & (b > 65.0)

    # Normalized luminance / shading factor from the original cel-shaded blue (0.0 .. 1.25)
    lum = (0.20 * r + 0.45 * g + 0.35 * b) / 185.0
    lum = np.clip(lum, 0.25, 1.35) * darken

    if team_name == "team_blue":
        nr = np.clip(48.0 * lum + 12.0 * (lum ** 2), 0, 255)
        ng = np.clip(132.0 * lum + 22.0 * (lum ** 2), 0, 255)
        nb = np.clip(242.0 * lum + 18.0 * (lum ** 2), 0, 255)
    elif team_name == "team_red":
        nr = np.clip(235.0 * lum + 20.0 * (lum ** 2), 0, 255)
        ng = np.clip(58.0 * lum + 18.0 * (lum ** 2), 0, 255)
        nb = np.clip(62.0 * lum + 15.0 * (lum ** 2), 0, 255)
    elif team_name == "team_green":
        nr = np.clip(38.0 * lum + 15.0 * (lum ** 2), 0, 255)
        ng = np.clip(198.0 * lum + 25.0 * (lum ** 2), 0, 255)
        nb = np.clip(88.0 * lum + 18.0 * (lum ** 2), 0, 255)
    elif team_name == "team_amber":
        nr = np.clip(245.0 * lum + 18.0 * (lum ** 2), 0, 255)
        ng = np.clip(158.0 * lum + 24.0 * (lum ** 2), 0, 255)
        nb = np.clip(24.0 * lum + 12.0 * (lum ** 2), 0, 255)
    else:  # "base" neutral silver-white
        nr = np.clip(215.0 * lum, 0, 255)
        ng = np.clip(222.0 * lum, 0, 255)
        nb = np.clip(232.0 * lum, 0, 255)

    r[is_body] = nr[is_body]
    g[is_body] = ng[is_body]
    b[is_body] = nb[is_body]
    out[:, :, 0], out[:, :, 1], out[:, :, 2] = r, g, b
    return out.astype(np.uint8)


def close_capsule_outline(crop_rgba):
    """
    Ensures that if any part was touching the 2x2 grid divider line (leaving a flat uncapped top/bottom edge),
    we round the corners and seal the entire 360-degree perimeter with the Stickman's crisp dark outline (14, 18, 26).
    """
    arr = crop_rgba.copy()
    h, w, _ = arr.shape
    alpha = arr[:, :, 3] > 20

    # Round off sharp corners on the top 6 rows and bottom 6 rows if the row is wide
    for r in range(min(6, h)):
        xs = np.where(alpha[r])[0]
        if len(xs) > 12:
            trim = (6 - r) * 2
            alpha[r, xs[:trim]] = False
            alpha[r, xs[-trim:]] = False
    for r in range(max(0, h - 6), h):
        xs = np.where(alpha[r])[0]
        if len(xs) > 12:
            trim = (r - (h - 7)) * 2
            alpha[r, xs[:trim]] = False
            alpha[r, xs[-trim:]] = False

    arr[~alpha] = [0, 0, 0, 0]

    # Any pixel on the top 4 rows or bottom 4 rows of each column's opaque span gets sealed with dark outline
    for x in range(w):
        ys = np.where(alpha[:, x])[0]
        if len(ys) > 0:
            y_top = ys[0]
            y_bot = ys[-1]
            for y in range(y_top, min(h, y_top + 4)):
                if alpha[y, x]:
                    arr[y, x, :3] = [14, 18, 26]
            for y in range(max(0, y_bot - 3), y_bot + 1):
                if alpha[y, x]:
                    arr[y, x, :3] = [14, 18, 26]
    return arr


def save_part_all_teams(rgba_arr, part_name, target_w=None, target_h=None, rotate_deg=0.0, darken=1.0):
    """
    Extracts the largest connected component, resizes to target_w/target_h,
    and TIGHTLY TRIMS 100% of outer transparent pixels (0px transparent padding)
    so the image bounding box (0..W, 0..H) is the exact visible part!
    """
    rgba_arr = keep_largest_component(rgba_arr)
    ys, xs = np.where(rgba_arr[:, :, 3] > 20)
    crop = rgba_arr[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1].copy()
    im = Image.fromarray(crop, mode="RGBA")
    if abs(rotate_deg) > 0.1:
        im = im.rotate(rotate_deg, resample=Image.Resampling.BICUBIC, expand=True)
        arr_r = np.array(im)
        ys2, xs2 = np.where(arr_r[:, :, 3] > 20)
        im = Image.fromarray(arr_r[ys2.min() : ys2.max() + 1, xs2.min() : xs2.max() + 1], mode="RGBA")

    cw, ch = im.size
    if target_w and target_h:
        im = im.resize((target_w, target_h), Image.Resampling.LANCZOS)
    elif target_w:
        sc = target_w / float(cw)
        im = im.resize((target_w, max(1, int(round(ch * sc)))), Image.Resampling.LANCZOS)
    elif target_h:
        sc = target_h / float(ch)
        im = im.resize((max(1, int(round(cw * sc))), target_h), Image.Resampling.LANCZOS)

    # Tightly trim any transparent border introduced by resize interpolation (alpha > 20)
    arr_resized = np.array(im)
    ys_t, xs_t = np.where(arr_resized[:, :, 3] > 20)
    base_arr = arr_resized[ys_t.min() : ys_t.max() + 1, xs_t.min() : xs_t.max() + 1].copy()
    base_arr[base_arr[:, :, 3] <= 20] = [0, 0, 0, 0]

    for t in TEAMS:
        t_arr = recolor_stickman_team(base_arr, t, darken=darken)
        t_im = Image.fromarray(t_arr, mode="RGBA")
        out_p = os.path.join(STICKER_PARTS_ROOT, t, part_name)
        t_im.save(out_p)
        bname = os.path.splitext(part_name)[0]
        t_im.save(f"/Users/dochung/Desktop/card_g/assets/mobile/sticker_hero/parts/{t}/{bname}.webp", "WEBP", quality=92)

    th, tw, _ = base_arr.shape
    print(f"  [Sticker Part] {part_name:22s}: {tw:3d}x{th:3d} (tight-trimmed 0px pad | saved 4 teams + base)")
    return Image.open(os.path.join(STICKER_PARTS_ROOT, "team_blue", part_name)).convert("RGBA")


def find_top_stem_pivot(im):
    arr = np.array(im)
    # Since im is tightly trimmed (0px padding), the short connector stem starts at y=0!
    sub_a = arr[1:8, :, 3] > 40
    ys, xs = np.where(sub_a)
    px = round(float(np.mean(xs)), 1) if len(xs) > 0 else round(im.width / 2.0, 1)
    py = 5.0
    return px, py


print("=== 1. Cleaning Stickman Reference & Extracting 16 Tight-Trimmed Stickman Parts (4 Teams, Upper/Lower Torso, Neck & Stem Joints) ===")
ref_raw_im = Image.open(STICKER_REF_RAW).convert("RGBA")
ref_clean_arr = clean_magenta(ref_raw_im, border_margin=8)
ys_rc, xs_rc = np.where(ref_clean_arr[:, :, 3] > 20)
rc_crop = Image.fromarray(ref_clean_arr[ys_rc.min() : ys_rc.max() + 1, xs_rc.min() : xs_rc.max() + 1], mode="RGBA")
rc_sc = min(420.0 / rc_crop.width, 420.0 / rc_crop.height)
rc_resized = rc_crop.resize((int(round(rc_crop.width * rc_sc)), int(round(rc_crop.height * rc_sc))), Image.Resampling.LANCZOS)
ref_512 = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
ref_512.paste(rc_resized, ((512 - rc_resized.width) // 2, 445 - rc_resized.height))
ref_512.save(STICKER_REF_CLEAN)


def extract_top_n_components(rgba_arr, n_expected):
    alpha = rgba_arr[:, :, 3] > 20
    h, w = alpha.shape
    visited = np.zeros((h, w), dtype=bool)
    comps = []
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    for y in range(h):
        for x in range(w):
            if alpha[y, x] and not visited[y, x]:
                q = deque([(y, x)])
                visited[y, x] = True
                coords = []
                while q:
                    cy, cx = q.popleft()
                    coords.append((cy, cx))
                    for dy, dx in dirs:
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and alpha[ny, nx] and not visited[ny, nx]:
                            visited[ny, nx] = True
                            q.append((ny, nx))
                if len(coords) >= 120:
                    ys, xs = zip(*coords)
                    mean_y = float(np.mean(ys))
                    sub = np.zeros_like(rgba_arr)
                    sub[ys, xs] = rgba_arr[ys, xs]
                    comps.append((len(coords), mean_y, sub))
    comps.sort(key=lambda item: item[0], reverse=True)
    top_comps = comps[:n_expected]
    top_comps.sort(key=lambda item: item[1])
    return [item[2] for item in top_comps]


parts_raw_im = Image.open(STICKER_PARTS_RAW).convert("RGBA")
parts_arr = clean_magenta(parts_raw_im, border_margin=8)
ph, pw, _ = parts_arr.shape
mid_x = pw // 2

# Left column of sticker_parts_simple_raw.png: 3 components (1: head, 2: neck capsule, 3: capsule)
left_parts = extract_top_n_components(parts_arr[:, :mid_x], 3)
head_box, neck_box, _ = left_parts

# Right column of sticker_parts_simple_raw.png: 3 components (4: uniform limb capsule, 5: circular hand + wrist stem, 6: old foot)
right_parts = extract_top_n_components(parts_arr[:, mid_x:], 3)
limb_box, hand_box, _ = right_parts

# Upper Torso (chest) & Lower Torso (hip) from sticker_torso_parts_raw.png
torso_raw_im = Image.open(STICKER_TORSO_RAW).convert("RGBA")
torso_arr = clean_magenta(torso_raw_im, border_margin=8)
torso_comps = extract_top_n_components(torso_arr, 2)
chest_box, hip_box = torso_comps[0], torso_comps[1]

# Chibi Ankle-Boots (foot_front & foot_back) from sticker_feet_raw.png
feet_raw_im = Image.open(STICKER_FEET_RAW).convert("RGBA")
feet_arr = clean_magenta(feet_raw_im, border_margin=8)
feet_comps = extract_top_n_components(feet_arr, 2)
foot_f_box, foot_b_box = feet_comps[0], feet_comps[1]

im_head = save_part_all_teams(head_box, "head.png", target_h=92, darken=1.0)
im_neck = save_part_all_teams(neck_box, "neck.png", target_h=34, darken=0.92)
im_chest = save_part_all_teams(chest_box, "chest.png", target_h=86, darken=1.0)
im_hip = save_part_all_teams(hip_box, "hip_kilt.png", target_h=52, darken=0.95)

# Front & Back Arms (uniform rounded-end capsules + circular hand with short wrist connector stem)
im_arm_uf = save_part_all_teams(limb_box, "arm_upper_front.png", target_h=62, darken=1.0)
im_arm_lf = save_part_all_teams(limb_box, "arm_lower_front.png", target_h=58, darken=1.0)
im_hand_f = save_part_all_teams(hand_box, "hand_front.png", target_h=48, darken=1.0)

im_arm_ub = save_part_all_teams(limb_box, "arm_upper_back.png", target_h=60, darken=0.82)
im_arm_lb = save_part_all_teams(limb_box, "arm_lower_back.png", target_h=56, darken=0.82)
im_hand_b = save_part_all_teams(hand_box, "hand_back.png", target_h=46, darken=0.82)

# Front & Back Legs (uniform rounded-end capsules + one-piece chibi ankle-boots)
im_thigh_f = save_part_all_teams(limb_box, "leg_thigh_front.png", target_h=66, darken=1.0)
im_shin_f = save_part_all_teams(limb_box, "leg_shin_front.png", target_h=62, darken=1.0)
im_foot_f = save_part_all_teams(foot_f_box, "foot_front.png", target_w=50, darken=1.0)

im_thigh_b = save_part_all_teams(limb_box, "leg_thigh_back.png", target_h=64, darken=0.82)
im_shin_b = save_part_all_teams(limb_box, "leg_shin_back.png", target_h=60, darken=0.82)
im_foot_b = save_part_all_teams(foot_b_box, "foot_back.png", target_w=48, darken=0.82)

hand_f_px, hand_f_py = find_top_stem_pivot(im_hand_f)
hand_b_px, hand_b_py = find_top_stem_pivot(im_hand_b)
foot_f_px, _ = find_top_stem_pivot(im_foot_f)
foot_b_px, _ = find_top_stem_pivot(im_foot_b)
foot_f_py = 9.0
foot_b_py = 9.0

print("=== 2. Extracting Weapon 001 (W001: Hắc Kiếm Tàn Binh) with 2 Grip Points (Grip 1 & Grip 2) ===")
w001_raw_im = Image.open(W001_RAW_PATH).convert("RGBA")
w001_arr = keep_largest_component(clean_magenta(w001_raw_im, border_margin=6))
ys_w, xs_w = np.where(w001_arr[:, :, 3] > 20)
w001_crop = Image.fromarray(w001_arr[ys_w.min() : ys_w.max() + 1, xs_w.min() : xs_w.max() + 1], mode="RGBA")

# Keep natural diagonal up-right combat orientation (+8 deg) so hilt is at bottom-left and blade points up-right!
w001_oriented = w001_crop.rotate(8, resample=Image.Resampling.BICUBIC, expand=True)
arr_wo = np.array(w001_oriented)
ys_o, xs_o = np.where(arr_wo[:, :, 3] > 20)
w001_tight = Image.fromarray(arr_wo[ys_o.min() : ys_o.max() + 1, xs_o.min() : xs_o.max() + 1], mode="RGBA")
sc_w = 204.0 / float(w001_tight.width)
w001_resized = w001_tight.resize((204, max(1, int(round(w001_tight.height * sc_w)))), Image.Resampling.LANCZOS)

# Tightly trim weapon_main.png (0px transparent padding)
w001_res_arr = np.array(w001_resized)
ys_wt, xs_wt = np.where(w001_res_arr[:, :, 3] > 20)
w001_final_arr = w001_res_arr[ys_wt.min() : ys_wt.max() + 1, xs_wt.min() : xs_wt.max() + 1].copy()
w001_final_arr[w001_final_arr[:, :, 3] <= 20] = [0, 0, 0, 0]
w001_final = Image.fromarray(w001_final_arr, mode="RGBA")

weapon_main_path = os.path.join(W001_PARTS_DIR, "weapon_main.png")
w001_final.save(weapon_main_path)
w001_final.save("/Users/dochung/Desktop/card_g/assets/mobile/weapons/w001_hac_kiem_tan_binh/parts/weapon_main.webp", "WEBP", quality=92)

# Automatically compute exact Grip 1 (upper handle behind crossguard) & Grip 2 (lower handle near pommel) on tightly-trimmed weapon_main.png
w_alpha = w001_final_arr[:, :, 3] > 40
wys, wxs = np.where(w_alpha)
# Project along sword axis from bottom-left (min x - y) to top-right (max x - y)
diag_proj = wxs.astype(np.float32) - wys.astype(np.float32)
d_min, d_max = float(diag_proj.min()), float(diag_proj.max())
d_span = d_max - d_min

# Grip 1: 23% from pommel along diagonal axis (upper handle right behind crossguard)
d_g1 = d_min + 0.23 * d_span
mask_g1 = np.abs(diag_proj - d_g1) <= 4.0
G1_X = round(float(np.mean(wxs[mask_g1])), 1)
G1_Y = round(float(np.mean(wys[mask_g1])), 1)

# Grip 2: 10% from pommel along diagonal axis (lower handle for 2-handed grip / secondary grip)
d_g2 = d_min + 0.10 * d_span
mask_g2 = np.abs(diag_proj - d_g2) <= 4.0
G2_X = round(float(np.mean(wxs[mask_g2])), 1)
G2_Y = round(float(np.mean(wys[mask_g2])), 1)

# Create tightly-trimmed weapon_offhand.png (0.78x companion short-blade version of W001 for optional dual-wielding)
w001_off_raw = w001_final.resize((int(round(w001_final.width * 0.78)), int(round(w001_final.height * 0.78))), Image.Resampling.LANCZOS)
arr_off = np.array(w001_off_raw)
ys_of, xs_of = np.where(arr_off[:, :, 3] > 20)
arr_off_tight = arr_off[ys_of.min() : ys_of.max() + 1, xs_of.min() : xs_of.max() + 1].copy()
arr_off_tight[arr_off_tight[:, :, 3] <= 20] = [0, 0, 0, 0]
w001_off = Image.fromarray(arr_off_tight, mode="RGBA")
weapon_off_path = os.path.join(W001_PARTS_DIR, "weapon_offhand.png")
w001_off.save(weapon_off_path)
w001_off.save("/Users/dochung/Desktop/card_g/assets/mobile/weapons/w001_hac_kiem_tan_binh/parts/weapon_offhand.webp", "WEBP", quality=92)

# Copy/extract soft-opacity VFX for W001 (fx_slash, fx_slash_heavy, fx_spark, fx_dust) + weapon_aura.png
c001_parts_dir = "/Users/dochung/Desktop/card_g/assets/heroes/c001_hac_kiem_tan_binh/godot/parts"
for fx_name in ["fx_slash", "fx_slash_heavy", "fx_spark", "fx_dust"]:
    src_fx = os.path.join(c001_parts_dir, f"{fx_name}.png")
    dst_fx = os.path.join(W001_PARTS_DIR, f"{fx_name}.png")
    shutil.copyfile(src_fx, dst_fx)
    Image.open(dst_fx).save(f"/Users/dochung/Desktop/card_g/assets/mobile/weapons/w001_hac_kiem_tan_binh/parts/{fx_name}.webp", "WEBP", quality=90)

shutil.copyfile(os.path.join(W001_PARTS_DIR, "fx_slash.png"), os.path.join(W001_PARTS_DIR, "weapon_aura.png"))

print(f"  [Weapon W001] weapon_main.png: {w001_final.size[0]}x{w001_final.size[1]} (tight-trimmed 0px pad) | Grip1=({G1_X}, {G1_Y}), Grip2=({G2_X}, {G2_Y})")

# 3. Define Stickman + Dual-Weapon Rig Hierarchy (18 Bones: 16 Tight-Trimmed Stickman Bones + Weapon_Front + Weapon_Back)
# Because every capsule part is tightly trimmed (0px padding) with width W and height H:
#   - Top semi-circle joint center (pivot_x, pivot_y) = (W / 2.0, W / 2.0)
#   - Distance to bottom semi-circle joint center (child rest_y) = H - W
BONES = [
    {
        "name": "Hip",
        "parent": None,
        "part": "hip_kilt",
        "is_weapon": False,
        "rest_x": 198.0, "rest_y": 258.0, "rest_rot": 0.0,
        "pivot_x": round(im_hip.width / 2.0, 1), "pivot_y": round(im_hip.height * 0.35, 1),
        "z_index": 7,
        "tip_child": "Chest",
    },
    {
        "name": "Thigh_L",
        "parent": "Hip",
        "part": "leg_thigh_back",
        "is_weapon": False,
        "rest_x": 8.0, "rest_y": 14.0, "rest_rot": -22.0,
        "pivot_x": round(im_thigh_b.width / 2.0, 1), "pivot_y": round(im_thigh_b.width / 2.0, 1),
        "z_index": 1,
        "tip_child": "Shin_L",
    },
    {
        "name": "Shin_L",
        "parent": "Thigh_L",
        "part": "leg_shin_back",
        "is_weapon": False,
        "rest_x": 0.0, "rest_y": round(float(im_thigh_b.height - im_thigh_b.width), 1), "rest_rot": 16.0,
        "pivot_x": round(im_shin_b.width / 2.0, 1), "pivot_y": round(im_shin_b.width / 2.0, 1),
        "z_index": 2,
        "tip_child": "Foot_L",
    },
    {
        "name": "Foot_L",
        "parent": "Shin_L",
        "part": "foot_back",
        "is_weapon": False,
        "rest_x": 0.0, "rest_y": round(float(im_shin_b.height - im_shin_b.width), 1), "rest_rot": 6.0,
        "pivot_x": foot_b_px, "pivot_y": foot_b_py,
        "z_index": 3,
        "tip_offset": (36.0, 18.0),
    },
    {
        "name": "Thigh_R",
        "parent": "Hip",
        "part": "leg_thigh_front",
        "is_weapon": False,
        "rest_x": -8.0, "rest_y": 14.0, "rest_rot": 22.0,
        "pivot_x": round(im_thigh_f.width / 2.0, 1), "pivot_y": round(im_thigh_f.width / 2.0, 1),
        "z_index": 4,
        "tip_child": "Shin_R",
    },
    {
        "name": "Shin_R",
        "parent": "Thigh_R",
        "part": "leg_shin_front",
        "is_weapon": False,
        "rest_x": 0.0, "rest_y": round(float(im_thigh_f.height - im_thigh_f.width), 1), "rest_rot": -14.0,
        "pivot_x": round(im_shin_f.width / 2.0, 1), "pivot_y": round(im_shin_f.width / 2.0, 1),
        "z_index": 5,
        "tip_child": "Foot_R",
    },
    {
        "name": "Foot_R",
        "parent": "Shin_R",
        "part": "foot_front",
        "is_weapon": False,
        "rest_x": 0.0, "rest_y": round(float(im_shin_f.height - im_shin_f.width), 1), "rest_rot": -8.0,
        "pivot_x": foot_f_px, "pivot_y": foot_f_py,
        "z_index": 6,
        "tip_offset": (38.0, 18.0),
    },
    {
        "name": "Chest",
        "parent": "Hip",
        "part": "chest",
        "is_weapon": False,
        "rest_x": 0.0, "rest_y": -4.0, "rest_rot": 3.0,
        "pivot_x": round(im_chest.width / 2.0, 1), "pivot_y": round(im_chest.height - 12.0, 1),
        "z_index": 8,
        "tip_child": "Neck",
    },
    {
        "name": "Neck",
        "parent": "Chest",
        "part": "neck",
        "is_weapon": False,
        "rest_x": 0.0, "rest_y": round(-(im_chest.height - 20.0), 1), "rest_rot": 0.0,
        "pivot_x": round(im_neck.width / 2.0, 1), "pivot_y": round(im_neck.height - im_neck.width / 2.0, 1),
        "z_index": 7,
        "tip_child": "Head",
    },
    {
        "name": "Head",
        "parent": "Neck",
        "part": "head",
        "is_weapon": False,
        "rest_x": 0.0, "rest_y": round(-float(im_neck.height - im_neck.width), 1), "rest_rot": -3.0,
        "pivot_x": round(im_head.width / 2.0, 1), "pivot_y": round(im_head.height - 10.0, 1),
        "z_index": 11,
        "tip_offset": (0.0, -76.0),
    },
    {
        "name": "UpperArm_R",
        "parent": "Chest",
        "part": "arm_upper_back",
        "is_weapon": False,
        "rest_x": 10.0, "rest_y": -58.0, "rest_rot": -28.0,
        "pivot_x": round(im_arm_ub.width / 2.0, 1), "pivot_y": round(im_arm_ub.width / 2.0, 1),
        "z_index": 6,
        "tip_child": "Forearm_R",
    },
    {
        "name": "Forearm_R",
        "parent": "UpperArm_R",
        "part": "arm_lower_back",
        "is_weapon": False,
        "rest_x": 0.0, "rest_y": round(float(im_arm_ub.height - im_arm_ub.width), 1), "rest_rot": -42.0,
        "pivot_x": round(im_arm_lb.width / 2.0, 1), "pivot_y": round(im_arm_lb.width / 2.0, 1),
        "z_index": 9,
        "tip_child": "Hand_R",
    },
    {
        "name": "Hand_R",
        "parent": "Forearm_R",
        "part": "hand_back",
        "is_weapon": False,
        "rest_x": 0.0, "rest_y": round(float(im_arm_lb.height - im_arm_lb.width), 1), "rest_rot": 0.0,
        "pivot_x": hand_b_px, "pivot_y": hand_b_py,
        "z_index": 10,
        "tip_child": "Weapon_Back",
    },
    {
        "name": "Weapon_Back",
        "parent": "Hand_R",
        "part": "weapon_offhand",
        "is_weapon": True,
        "visible_default": False,
        "rest_x": 0.0, "rest_y": round(im_hand_b.height * 0.58, 1), "rest_rot": 58.0,
        "pivot_x": round(G1_X * 0.78, 1), "pivot_y": round(G1_Y * 0.78, 1),
        "grip1_x": round(G1_X * 0.78, 1), "grip1_y": round(G1_Y * 0.78, 1),
        "grip2_x": round(G2_X * 0.78, 1), "grip2_y": round(G2_Y * 0.78, 1),
        "z_index": 9,
        "tip_offset": (122.0, -74.0),
    },
    {
        "name": "UpperArm_L",
        "parent": "Chest",
        "part": "arm_upper_front",
        "is_weapon": False,
        "rest_x": -8.0, "rest_y": -58.0, "rest_rot": 10.0,
        "pivot_x": round(im_arm_uf.width / 2.0, 1), "pivot_y": round(im_arm_uf.width / 2.0, 1),
        "z_index": 12,
        "tip_child": "Forearm_L",
    },
    {
        "name": "Forearm_L",
        "parent": "UpperArm_L",
        "part": "arm_lower_front",
        "is_weapon": False,
        "rest_x": 0.0, "rest_y": round(float(im_arm_uf.height - im_arm_uf.width), 1), "rest_rot": -62.0,
        "pivot_x": round(im_arm_lf.width / 2.0, 1), "pivot_y": round(im_arm_lf.width / 2.0, 1),
        "z_index": 13,
        "tip_child": "Hand_L",
    },
    {
        "name": "Hand_L",
        "parent": "Forearm_L",
        "part": "hand_front",
        "is_weapon": False,
        "rest_x": 0.0, "rest_y": round(float(im_arm_lf.height - im_arm_lf.width), 1), "rest_rot": 0.0,
        "pivot_x": hand_f_px, "pivot_y": hand_f_py,
        "z_index": 15,
        "tip_child": "Weapon_Front",
    },
    {
        "name": "Weapon_Front",
        "parent": "Hand_L",
        "part": "weapon_main",
        "is_weapon": True,
        "visible_default": True,
        "rest_x": 0.0, "rest_y": round(im_hand_f.height * 0.58, 1), "rest_rot": 48.0,
        "pivot_x": G1_X, "pivot_y": G1_Y,
        "grip1_x": G1_X, "grip1_y": G1_Y,
        "grip2_x": G2_X, "grip2_y": G2_Y,
        "z_index": 14,
        "tip_offset": (146.0, -108.0),
    },
]

VFX_LIST = ["fx_slash", "fx_slash_heavy", "fx_spark", "fx_dust"]

# Load part images for team_blue + weapon parts
PART_IMAGES_BY_TEAM = {t: {} for t in TEAMS}
WEAPON_IMAGES = {}

for b in BONES:
    pname = b["part"]
    if b["is_weapon"]:
        p = os.path.join(W001_PARTS_DIR, f"{pname}.png")
        im = Image.open(p).convert("RGBA")
        WEAPON_IMAGES[pname] = im
    else:
        for t in TEAMS:
            tp = os.path.join(STICKER_PARTS_ROOT, t, f"{pname}.png")
            PART_IMAGES_BY_TEAM[t][pname] = Image.open(tp).convert("RGBA")
        im = PART_IMAGES_BY_TEAM["team_blue"][pname]
    w, h = im.size
    b["width"] = w
    b["height"] = h
    b["offset_x"] = round(w / 2.0 - b["pivot_x"], 2)
    b["offset_y"] = round(h / 2.0 - b["pivot_y"], 2)

for fx in VFX_LIST + ["weapon_aura"]:
    p = os.path.join(W001_PARTS_DIR, f"{fx}.png")
    WEAPON_IMAGES[fx] = Image.open(p).convert("RGBA")

# 4. Define the 6 Actions for Stickman + W001 (Hắc Kiếm Tàn Binh — Kỹ năng Trọng Trảm)
ACTIONS = {
    "idle": {
        "grid": (2, 2),
        "length": 1.2,
        "loop": True,
        "frames": [
            {"t": 0.0, "Hip": (0, 0, 0), "Chest": (0, 0, 0), "Head": (0, 0, 0), "UpperArm_R": (0, 0, 0), "Forearm_R": (0, 0, 0), "Hand_R": (0, 0, 0), "Weapon_Back": (0, 0, 0), "UpperArm_L": (0, 0, 0), "Forearm_L": (0, 0, 0), "Hand_L": (0, 0, 0), "Weapon_Front": (0, 0, 0), "Thigh_R": (0, 0, 0), "Shin_R": (0, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (0, 0, 0), "Shin_L": (0, 0, 0), "Foot_L": (0, 0, 0)},
            {"t": 0.3, "Hip": (0, 3, 0), "Chest": (2, 0, 0), "Head": (-2, 0, 0), "UpperArm_R": (4, 0, 0), "Forearm_R": (3, 0, 0), "Hand_R": (-2, 0, 0), "Weapon_Back": (0, 0, 0), "UpperArm_L": (-4, 0, 0), "Forearm_L": (-3, 0, 0), "Hand_L": (-2, 0, 0), "Weapon_Front": (-2, 0, 0), "Thigh_R": (-3, 0, 0), "Shin_R": (3, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (-2, 0, 0), "Shin_L": (2, 0, 0), "Foot_L": (0, 0, 0)},
            {"t": 0.6, "Hip": (0, 6, 0), "Chest": (4, 0, 0), "Head": (-3, 0, 0), "UpperArm_R": (6, 0, 0), "Forearm_R": (5, 0, 0), "Hand_R": (-3, 0, 0), "Weapon_Back": (0, 0, 0), "UpperArm_L": (-6, 0, 0), "Forearm_L": (-5, 0, 0), "Hand_L": (-3, 0, 0), "Weapon_Front": (-4, 0, 0), "Thigh_R": (-5, 0, 0), "Shin_R": (5, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (-4, 0, 0), "Shin_L": (4, 0, 0), "Foot_L": (0, 0, 0)},
            {"t": 0.9, "Hip": (0, 2, 0), "Chest": (1, 0, 0), "Head": (-1, 0, 0), "UpperArm_R": (2, 0, 0), "Forearm_R": (2, 0, 0), "Hand_R": (-1, 0, 0), "Weapon_Back": (0, 0, 0), "UpperArm_L": (-2, 0, 0), "Forearm_L": (-2, 0, 0), "Hand_L": (-1, 0, 0), "Weapon_Front": (-1, 0, 0), "Thigh_R": (-2, 0, 0), "Shin_R": (2, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (-1, 0, 0), "Shin_L": (1, 0, 0), "Foot_L": (0, 0, 0)},
        ],
    },
    "walk": {
        "grid": (2, 3),
        "length": 0.9,
        "loop": True,
        "frames": [
            {"t": 0.00, "Hip": (-3, 4, 2), "Chest": (4, 0, 0), "Head": (-3, 0, 0), "UpperArm_R": (16, 0, 0), "Forearm_R": (6, 0, 0), "Hand_R": (0, 0, 0), "Weapon_Back": (0, 0, 0), "UpperArm_L": (-16, 0, 0), "Forearm_L": (-6, 0, 0), "Hand_L": (-2, 0, 0), "Weapon_Front": (-4, 0, 0), "Thigh_R": (-22, 8, -4), "Shin_R": (12, 0, 0), "Foot_R": (6, 0, 0), "Thigh_L": (18, -6, 0), "Shin_L": (14, 0, 0), "Foot_L": (8, 0, 0)},
            {"t": 0.15, "Hip": (-2, 6, 2), "Chest": (5, 0, 0), "Head": (-4, 0, 0), "UpperArm_R": (8, 0, 0), "Forearm_R": (4, 0, 0), "Hand_R": (0, 0, 0), "Weapon_Back": (0, 0, 0), "UpperArm_L": (-8, 0, 0), "Forearm_L": (-4, 0, 0), "Hand_L": (-2, 0, 0), "Weapon_Front": (-2, 0, 0), "Thigh_R": (-10, 6, -2), "Shin_R": (14, 0, 0), "Foot_R": (2, 0, 0), "Thigh_L": (8, -4, 0), "Shin_L": (18, 0, 0), "Foot_L": (10, 0, 0)},
            {"t": 0.30, "Hip": (0, -2, 0), "Chest": (3, 0, 0), "Head": (-2, 0, 0), "UpperArm_R": (-8, 0, 0), "Forearm_R": (-4, 0, 0), "Hand_R": (0, 0, 0), "Weapon_Back": (0, 0, 0), "UpperArm_L": (8, 0, 0), "Forearm_L": (2, 0, 0), "Hand_L": (0, 0, 0), "Weapon_Front": (2, 0, 0), "Thigh_R": (4, 2, 0), "Shin_R": (8, 0, 0), "Foot_R": (-4, 0, 0), "Thigh_L": (-10, 4, -4), "Shin_L": (16, 0, 0), "Foot_L": (6, 0, 0)},
            {"t": 0.45, "Hip": (3, 4, 2), "Chest": (5, 0, 0), "Head": (-3, 0, 0), "UpperArm_R": (-16, 0, 0), "Forearm_R": (-6, 0, 0), "Hand_R": (-2, 0, 0), "Weapon_Back": (0, 0, 0), "UpperArm_L": (16, 0, 0), "Forearm_L": (4, 0, 0), "Hand_L": (2, 0, 0), "Weapon_Front": (4, 0, 0), "Thigh_R": (16, -6, 0), "Shin_R": (14, 0, 0), "Foot_R": (6, 0, 0), "Thigh_L": (-22, 8, -4), "Shin_L": (10, 0, 0), "Foot_L": (-4, 0, 0)},
            {"t": 0.60, "Hip": (2, 6, 2), "Chest": (6, 0, 0), "Head": (-4, 0, 0), "UpperArm_R": (-8, 0, 0), "Forearm_R": (-4, 0, 0), "Hand_R": (0, 0, 0), "Weapon_Back": (0, 0, 0), "UpperArm_L": (8, 0, 0), "Forearm_L": (2, 0, 0), "Hand_L": (0, 0, 0), "Weapon_Front": (2, 0, 0), "Thigh_R": (8, -4, 0), "Shin_R": (18, 0, 0), "Foot_R": (8, 0, 0), "Thigh_L": (-10, 6, -2), "Shin_L": (12, 0, 0), "Foot_L": (0, 0, 0)},
            {"t": 0.75, "Hip": (-2, -2, 0), "Chest": (3, 0, 0), "Head": (-2, 0, 0), "UpperArm_R": (6, 0, 0), "Forearm_R": (2, 0, 0), "Hand_R": (0, 0, 0), "Weapon_Back": (0, 0, 0), "UpperArm_L": (-6, 0, 0), "Forearm_L": (-2, 0, 0), "Hand_L": (-1, 0, 0), "Weapon_Front": (-1, 0, 0), "Thigh_R": (-8, 4, -2), "Shin_R": (10, 0, 0), "Foot_R": (4, 0, 0), "Thigh_L": (4, -2, 0), "Shin_L": (10, 0, 0), "Foot_L": (4, 0, 0)},
        ],
    },
    "attack": {
        "grid": (2, 2),
        "length": 0.65,
        "loop": False,
        "frames": [
            {"t": 0.00, "Hip": (-8, 4, -4), "Chest": (-8, 0, 0), "Head": (6, 0, 0), "UpperArm_R": (20, 0, 0), "Forearm_R": (12, 0, 0), "Hand_R": (6, 0, 0), "Weapon_Back": (0, 0, 0), "UpperArm_L": (-48, 0, -6), "Forearm_L": (-20, 0, 0), "Hand_L": (-14, 0, 0), "Weapon_Front": (-18, 0, 0), "Thigh_R": (10, -4, 0), "Shin_R": (10, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (-10, 4, 0), "Shin_L": (10, 0, 0), "Foot_L": (0, 0, 0)},
            {"t": 0.18, "Hip": (10, 6, 6), "Chest": (10, 0, 0), "Head": (-6, 0, 0), "UpperArm_R": (-16, 0, 0), "Forearm_R": (-10, 0, 0), "Hand_R": (-6, 0, 0), "Weapon_Back": (0, 0, 0), "UpperArm_L": (-10, 8, 0), "Forearm_L": (14, 0, 0), "Hand_L": (18, 0, 0), "Weapon_Front": (28, 0, 0), "Thigh_R": (-16, 8, -2), "Shin_R": (12, 0, 0), "Foot_R": (4, 0, 0), "Thigh_L": (14, -6, 0), "Shin_L": (12, 0, 0), "Foot_L": (4, 0, 0),
             "vfx": {"fx_slash": {"pos": (308, 254), "rot": 18, "scale": 0.72, "alpha": 0.94}}},
            {"t": 0.36, "Hip": (12, 8, 8), "Chest": (12, 0, 0), "Head": (-8, 0, 0), "UpperArm_R": (-22, 0, 0), "Forearm_R": (-14, 0, 0), "Hand_R": (-8, 0, 0), "Weapon_Back": (0, 0, 0), "UpperArm_L": (12, 6, 0), "Forearm_L": (22, 0, 0), "Hand_L": (24, 0, 0), "Weapon_Front": (46, 0, 0), "Thigh_R": (-20, 10, -4), "Shin_R": (14, 0, 0), "Foot_R": (6, 0, 0), "Thigh_L": (18, -8, 0), "Shin_L": (14, 0, 0), "Foot_L": (6, 0, 0),
             "vfx": {"fx_spark": {"pos": (346, 326), "rot": 0, "scale": 0.68, "alpha": 0.92}}},
            {"t": 0.52, "Hip": (2, 2, 1), "Chest": (2, 0, 0), "Head": (-1, 0, 0), "UpperArm_R": (-4, 0, 0), "Forearm_R": (-2, 0, 0), "Hand_R": (0, 0, 0), "Weapon_Back": (0, 0, 0), "UpperArm_L": (-2, 0, 0), "Forearm_L": (0, 0, 0), "Hand_L": (0, 0, 0), "Weapon_Front": (0, 0, 0), "Thigh_R": (-4, 2, 0), "Shin_R": (4, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (4, -2, 0), "Shin_L": (4, 0, 0), "Foot_L": (0, 0, 0)},
        ],
    },
    "cast": {
        "grid": (2, 3),
        "length": 0.95,
        "loop": False,
        "frames": [
            {"t": 0.00, "Hip": (-10, 6, -4), "Chest": (-8, 0, 0), "Head": (6, 0, 0), "UpperArm_R": (22, 0, 0), "Forearm_R": (14, 0, 0), "Hand_R": (6, 0, 0), "Weapon_Back": (0, 0, 0), "UpperArm_L": (-42, 0, -4), "Forearm_L": (-18, 0, 0), "Hand_L": (-14, 0, 0), "Weapon_Front": (-16, 0, 0), "Thigh_R": (8, -4, 0), "Shin_R": (10, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (-10, 4, 0), "Shin_L": (10, 0, 0), "Foot_L": (0, 0, 0),
             "vfx": {"fx_dust": {"pos": (218, 412), "rot": 0, "scale": 0.62, "alpha": 0.76}}},
            {"t": 0.16, "Hip": (-14, 10, -6), "Chest": (-12, 0, 0), "Head": (10, 0, 0), "UpperArm_R": (28, 0, 0), "Forearm_R": (18, 0, 0), "Hand_R": (8, 0, 0), "Weapon_Back": (0, 0, 0), "UpperArm_L": (-54, 0, -6), "Forearm_L": (-22, 0, 0), "Hand_L": (-18, 0, 0), "Weapon_Front": (-22, 0, 0), "Thigh_R": (12, -6, 0), "Shin_R": (14, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (-14, 6, 0), "Shin_L": (14, 0, 0), "Foot_L": (0, 0, 0),
             "vfx": {"fx_dust": {"pos": (212, 412), "rot": 0, "scale": 0.72, "alpha": 0.86}}},
            {"t": 0.34, "Hip": (12, 4, 6), "Chest": (10, 0, 0), "Head": (-8, 0, 0), "UpperArm_R": (-18, 0, 0), "Forearm_R": (-12, 0, 0), "Hand_R": (-6, 0, 0), "Weapon_Back": (0, 0, 0), "UpperArm_L": (-12, 10, 0), "Forearm_L": (12, 0, 0), "Hand_L": (16, 0, 0), "Weapon_Front": (26, 0, 0), "Thigh_R": (-18, 10, -4), "Shin_R": (12, 0, 0), "Foot_R": (4, 0, 0), "Thigh_L": (16, -8, 0), "Shin_L": (14, 0, 0), "Foot_L": (6, 0, 0),
             "vfx": {
                 "fx_slash_heavy": {"pos": (298, 258), "rot": 12, "scale": 0.68, "alpha": 0.95},
                 "fx_dust": {"pos": (196, 412), "rot": 0, "scale": 0.74, "alpha": 0.85},
             }},
            {"t": 0.52, "Hip": (16, 8, 8), "Chest": (14, 0, 0), "Head": (-10, 0, 0), "UpperArm_R": (-24, 0, 0), "Forearm_R": (-16, 0, 0), "Hand_R": (-8, 0, 0), "Weapon_Back": (0, 0, 0), "UpperArm_L": (12, 8, 0), "Forearm_L": (22, 0, 0), "Hand_L": (24, 0, 0), "Weapon_Front": (48, 0, 0), "Thigh_R": (-22, 12, -4), "Shin_R": (14, 0, 0), "Foot_R": (6, 0, 0), "Thigh_L": (20, -10, 0), "Shin_L": (16, 0, 0), "Foot_L": (8, 0, 0),
             "vfx": {
                 "fx_slash_heavy": {"pos": (306, 272), "rot": 28, "scale": 0.66, "alpha": 0.82},
                 "fx_spark": {"pos": (348, 326), "rot": 12, "scale": 0.70, "alpha": 0.94},
             }},
            {"t": 0.70, "Hip": (8, 4, 4), "Chest": (6, 0, 0), "Head": (-4, 0, 0), "UpperArm_R": (-10, 0, 0), "Forearm_R": (-6, 0, 0), "Hand_R": (-2, 0, 0), "Weapon_Back": (0, 0, 0), "UpperArm_L": (4, 4, 0), "Forearm_L": (8, 0, 0), "Hand_L": (8, 0, 0), "Weapon_Front": (14, 0, 0), "Thigh_R": (-10, 6, -2), "Shin_R": (8, 0, 0), "Foot_R": (2, 0, 0), "Thigh_L": (8, -4, 0), "Shin_L": (8, 0, 0), "Foot_L": (4, 0, 0),
             "vfx": {"fx_spark": {"pos": (352, 332), "rot": 25, "scale": 0.54, "alpha": 0.56}}},
            {"t": 0.86, "Hip": (0, 0, 0), "Chest": (0, 0, 0), "Head": (0, 0, 0), "UpperArm_R": (0, 0, 0), "Forearm_R": (0, 0, 0), "Hand_R": (0, 0, 0), "Weapon_Back": (0, 0, 0), "UpperArm_L": (0, 0, 0), "Forearm_L": (0, 0, 0), "Hand_L": (0, 0, 0), "Weapon_Front": (0, 0, 0), "Thigh_R": (0, 0, 0), "Shin_R": (0, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (0, 0, 0), "Shin_L": (0, 0, 0), "Foot_L": (0, 0, 0)},
        ],
    },
    "hurt": {
        "grid": (2, 2),
        "length": 0.55,
        "loop": False,
        "frames": [
            {"t": 0.00, "Hip": (-10, 4, -6), "Chest": (-12, 0, 0), "Head": (-14, 0, 0), "UpperArm_R": (14, 0, 0), "Forearm_R": (10, 0, 0), "Hand_R": (6, 0, 0), "Weapon_Back": (0, 0, 0), "UpperArm_L": (14, 0, 0), "Forearm_L": (-8, 0, 0), "Hand_L": (-6, 0, 0), "Weapon_Front": (-8, 0, 0), "Thigh_R": (8, 0, 0), "Shin_R": (6, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (-6, 0, 0), "Shin_L": (8, 0, 0), "Foot_L": (0, 0, 0),
             "vfx": {"fx_spark": {"pos": (254, 214), "rot": -15, "scale": 0.68, "alpha": 0.90}}},
            {"t": 0.15, "Hip": (-16, 8, -8), "Chest": (-14, 0, 0), "Head": (-18, 0, 0), "UpperArm_R": (20, 0, 0), "Forearm_R": (14, 0, 0), "Hand_R": (8, 0, 0), "Weapon_Back": (0, 0, 0), "UpperArm_L": (20, 0, 0), "Forearm_L": (-12, 0, 0), "Hand_L": (-10, 0, 0), "Weapon_Front": (-12, 0, 0), "Thigh_R": (12, 0, 0), "Shin_R": (10, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (-10, 0, 0), "Shin_L": (12, 0, 0), "Foot_L": (0, 0, 0)},
            {"t": 0.32, "Hip": (-8, 4, -4), "Chest": (-6, 0, 0), "Head": (-8, 0, 0), "UpperArm_R": (8, 0, 0), "Forearm_R": (6, 0, 0), "Hand_R": (4, 0, 0), "Weapon_Back": (0, 0, 0), "UpperArm_L": (8, 0, 0), "Forearm_L": (-4, 0, 0), "Hand_L": (-4, 0, 0), "Weapon_Front": (-4, 0, 0), "Thigh_R": (6, 0, 0), "Shin_R": (4, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (-4, 0, 0), "Shin_L": (6, 0, 0), "Foot_L": (0, 0, 0)},
            {"t": 0.48, "Hip": (0, 0, 0), "Chest": (0, 0, 0), "Head": (0, 0, 0), "UpperArm_R": (0, 0, 0), "Forearm_R": (0, 0, 0), "Hand_R": (0, 0, 0), "Weapon_Back": (0, 0, 0), "UpperArm_L": (0, 0, 0), "Forearm_L": (0, 0, 0), "Hand_L": (0, 0, 0), "Weapon_Front": (0, 0, 0), "Thigh_R": (0, 0, 0), "Shin_R": (0, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (0, 0, 0), "Shin_L": (0, 0, 0), "Foot_L": (0, 0, 0)},
        ],
    },
    "death": {
        "grid": (2, 3),
        "length": 1.10,
        "loop": False,
        "frames": [
            {"t": 0.00, "Hip": (-10, 6, -6), "Chest": (-12, 0, 0), "Head": (-14, 0, 0), "UpperArm_R": (14, 0, 0), "Forearm_R": (8, 0, 0), "Hand_R": (6, 0, 0), "Weapon_Back": (0, 0, 0), "UpperArm_L": (14, 0, 0), "Forearm_L": (-8, 0, 0), "Hand_L": (-6, 0, 0), "Weapon_Front": (-8, 0, 0), "Thigh_R": (10, 0, 0), "Shin_R": (8, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (-8, 0, 0), "Shin_L": (10, 0, 0), "Foot_L": (0, 0, 0),
             "vfx": {"fx_spark": {"pos": (254, 212), "rot": 0, "scale": 0.72, "alpha": 0.92}}},
            {"t": 0.22, "Hip": (-6, 30, 14), "Chest": (16, 0, 0), "Head": (12, 0, 0), "UpperArm_R": (24, 0, 0), "Forearm_R": (12, 0, 0), "Hand_R": (0, 0, 0), "Weapon_Back": (0, 0, 0), "UpperArm_L": (-16, 0, 0), "Forearm_L": (-10, 0, 0), "Hand_L": (-12, 0, 0), "Weapon_Front": (-16, 0, 0), "Thigh_R": (-42, 0, 0), "Shin_R": (64, 0, 0), "Foot_R": (12, 0, 0), "Thigh_L": (-36, 0, 0), "Shin_L": (58, 0, 0), "Foot_L": (10, 0, 0)},
            {"t": 0.45, "Hip": (-4, 56, 30), "Chest": (24, 0, 0), "Head": (18, 0, 0), "UpperArm_R": (36, 0, 0), "Forearm_R": (18, 0, 0), "Hand_R": (0, 0, 0), "Weapon_Back": (0, 0, 0), "UpperArm_L": (-32, 0, 0), "Forearm_L": (-16, 0, 0), "Hand_L": (-20, 0, 0), "Weapon_Front": (-26, 0, 0), "Thigh_R": (-66, 0, 0), "Shin_R": (90, 0, 0), "Foot_R": (16, 0, 0), "Thigh_L": (-60, 0, 0), "Shin_L": (84, 0, 0), "Foot_L": (14, 0, 0),
             "vfx": {"fx_dust": {"pos": (256, 422), "rot": 0, "scale": 0.85, "alpha": 0.82}}},
            {"t": 0.68, "Hip": (-2, 68, 40), "Chest": (28, 0, 0), "Head": (22, 0, 0), "UpperArm_R": (42, 0, 0), "Forearm_R": (20, 0, 0), "Hand_R": (0, 0, 0), "Weapon_Back": (0, 0, 0), "UpperArm_L": (-40, 0, 0), "Forearm_L": (-20, 0, 0), "Hand_L": (-24, 0, 0), "Weapon_Front": (-32, 0, 0), "Thigh_R": (-76, 0, 0), "Shin_R": (100, 0, 0), "Foot_R": (18, 0, 0), "Thigh_L": (-70, 0, 0), "Shin_L": (94, 0, 0), "Foot_L": (16, 0, 0),
             "vfx": {"fx_dust": {"pos": (264, 424), "rot": 0, "scale": 0.90, "alpha": 0.65}}, "modulate_a": 0.88},
            {"t": 0.88, "Hip": (0, 72, 44), "Chest": (30, 0, 0), "Head": (24, 0, 0), "UpperArm_R": (44, 0, 0), "Forearm_R": (22, 0, 0), "Hand_R": (0, 0, 0), "Weapon_Back": (0, 0, 0), "UpperArm_L": (-42, 0, 0), "Forearm_L": (-22, 0, 0), "Hand_L": (-26, 0, 0), "Weapon_Front": (-34, 0, 0), "Thigh_R": (-78, 0, 0), "Shin_R": (102, 0, 0), "Foot_R": (18, 0, 0), "Thigh_L": (-72, 0, 0), "Shin_L": (96, 0, 0), "Foot_L": (16, 0, 0),
             "vfx": {"fx_dust": {"pos": (266, 424), "rot": 0, "scale": 0.75, "alpha": 0.45}}, "modulate_a": 0.52},
            {"t": 1.05, "Hip": (0, 74, 46), "Chest": (30, 0, 0), "Head": (24, 0, 0), "UpperArm_R": (44, 0, 0), "Forearm_R": (22, 0, 0), "Hand_R": (0, 0, 0), "Weapon_Back": (0, 0, 0), "UpperArm_L": (-42, 0, 0), "Forearm_L": (-22, 0, 0), "Hand_L": (-26, 0, 0), "Weapon_Front": (-34, 0, 0), "Thigh_R": (-78, 0, 0), "Shin_R": (102, 0, 0), "Foot_R": (18, 0, 0), "Thigh_L": (-72, 0, 0), "Shin_L": (96, 0, 0), "Foot_L": (16, 0, 0),
             "modulate_a": 0.22},
        ],
    },
}

BONE_MAP = {b["name"]: b for b in BONES}


def compute_world_transforms(frame_pose=None):
    if frame_pose is None:
        frame_pose = {}
    world = {}
    for b in BONES:
        name = b["name"]
        parent = b["parent"]
        if name == "Hip":
            dx, dy, drot = frame_pose.get("Hip", (0.0, 0.0, 0.0))
        else:
            drot, dx, dy = frame_pose.get(name, (0.0, 0.0, 0.0))
        lx = b["rest_x"] + dx
        ly = b["rest_y"] + dy
        lrot = b["rest_rot"] + drot
        if parent is None:
            wx, wy, wrot = lx, ly, lrot
        else:
            px, py, prot = world[parent][:3]
            rad = math.radians(prot)
            ca, sa = math.cos(rad), math.sin(rad)
            wx = px + lx * ca - ly * sa
            wy = py + lx * sa + ly * ca
            wrot = prot + lrot
        world[name] = [wx, wy, wrot, wx, wy]

    for b in BONES:
        name = b["name"]
        wx, wy, wrot = world[name][:3]
        if "tip_child" in b and b["tip_child"] in world:
            tx, ty = world[b["tip_child"]][:2]
        elif "tip_offset" in b:
            ox, oy = b["tip_offset"]
            rad = math.radians(wrot)
            ca, sa = math.cos(rad), math.sin(rad)
            tx = wx + ox * ca - oy * sa
            ty = wy + ox * sa + oy * ca
        else:
            tx, ty = wx, wy + 32.0
        world[name][3] = tx
        world[name][4] = ty
    return world


def draw_spine_bone(draw, x0, y0, x1, y1, color=(56, 189, 248, 235), joint_color=(245, 70, 70, 255)):
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy)
    if length > 2.0:
        ux, uy = dx / length, dy / length
        px, py = -uy, ux
        w = min(5.5, max(2.8, length * 0.10))
        mid_x = x0 + dx * 0.22
        mid_y = y0 + dy * 0.22
        poly = [
            (x0, y0),
            (mid_x + px * w, mid_y + py * w),
            (x1, y1),
            (mid_x - px * w, mid_y - py * w),
        ]
        draw.polygon(poly, fill=(color[0], color[1], color[2], 145), outline=color)
    draw.ellipse([x0 - 4, y0 - 4, x0 + 4, y0 + 4], fill=joint_color, outline=(255, 255, 255, 255))
    draw.ellipse([x1 - 2.5, y1 - 2.5, x1 + 2.5, y1 + 2.5], fill=color, outline=(255, 255, 255, 220))


def paste_rotated_part(canvas, part_im, wx, wy, wrot_deg, pivot_x, pivot_y, scale=1.0, alpha=1.0):
    if alpha <= 0.01:
        return
    im = part_im
    if abs(scale - 1.0) > 1e-3:
        nw = max(1, int(round(im.width * scale)))
        nh = max(1, int(round(im.height * scale)))
        im = im.resize((nw, nh), Image.Resampling.BICUBIC)
        pivot_x *= scale
        pivot_y *= scale
    if alpha < 0.999:
        arr = np.array(im).astype(np.float32)
        arr[:, :, 3] *= alpha
        im = Image.fromarray(arr.astype(np.uint8))

    max_r = int(math.ceil(math.hypot(max(pivot_x, im.width - pivot_x), max(pivot_y, im.height - pivot_y)))) + 4
    tmp_size = max_r * 2
    tmp = Image.new("RGBA", (tmp_size, tmp_size), (0, 0, 0, 0))
    paste_x = int(round(max_r - pivot_x))
    paste_y = int(round(max_r - pivot_y))
    tmp.paste(im, (paste_x, paste_y))
    rot_im = tmp.rotate(-wrot_deg, resample=Image.Resampling.BICUBIC, expand=False)
    dest_x = int(round(wx - max_r))
    dest_y = int(round(wy - max_r))
    canvas.alpha_composite(rot_im, (dest_x, dest_y))


def render_pose(frame_pose=None, team_name="team_blue", show_weapon_front=True, show_weapon_back=False, canvas_size=512):
    if frame_pose is None:
        frame_pose = {}
    canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    world = compute_world_transforms(frame_pose)
    mod_a = frame_pose.get("modulate_a", 1.0)

    sorted_bones = sorted(BONES, key=lambda b: b["z_index"])
    for b in sorted_bones:
        bname = b["name"]
        if bname == "Weapon_Front" and not show_weapon_front:
            continue
        if bname == "Weapon_Back" and not show_weapon_back:
            continue
        wx, wy, wrot = world[bname][:3]
        im = WEAPON_IMAGES[b["part"]] if b["is_weapon"] else PART_IMAGES_BY_TEAM[team_name][b["part"]]
        paste_rotated_part(
            canvas,
            im,
            wx, wy, wrot,
            b["pivot_x"], b["pivot_y"],
            scale=1.0,
            alpha=mod_a,
        )

    vfx_dict = frame_pose.get("vfx", {})
    for fx_name, fx_cfg in vfx_dict.items():
        fx_im = WEAPON_IMAGES[fx_name]
        fx_pos = fx_cfg["pos"]
        fx_rot = fx_cfg.get("rot", 0.0)
        fx_scale = fx_cfg.get("scale", 1.0)
        fx_alpha = fx_cfg.get("alpha", 1.0)
        paste_rotated_part(
            canvas,
            fx_im,
            fx_pos[0], fx_pos[1], fx_rot,
            fx_im.width / 2.0, fx_im.height / 2.0,
            scale=fx_scale,
            alpha=fx_alpha,
        )
    return canvas, world


try:
    font_title = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 15)
    font_sub = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 12)
except Exception:
    font_title = ImageFont.load_default()
    font_sub = ImageFont.load_default()

print("=== 3. Building QC Audit Board: 4 Team Stickman Colors + W001 (Grip 1 & Grip 2) + Diagonal Card Preview ===")
board_w, board_h = 1860, 960
audit_im = Image.new("RGBA", (board_w, board_h), (18, 22, 30, 255))
audit_draw = ImageDraw.Draw(audit_im, "RGBA")

team_display = [
    ("team_blue", "DOI 1: XANH DUONG (Team Blue)", (59, 130, 246, 255)),
    ("team_red", "DOI 2: DO (Team Red)", (239, 68, 68, 255)),
    ("team_green", "DOI 3: XANH LA (Team Green)", (34, 197, 94, 255)),
    ("team_amber", "DOI 4: VANG CAM (Team Amber)", (245, 158, 11, 255)),
]

for idx, (t_key, t_label, t_col) in enumerate(team_display):
    ox = 12 + idx * 345
    oy = 12
    audit_draw.rectangle([ox, oy, ox + 335, oy + 450], fill=(26, 31, 42, 255), outline=t_col, width=2)
    t_pose_im, t_world = render_pose({}, team_name=t_key, show_weapon_front=True, show_weapon_back=(idx == 1), canvas_size=512)
    t_thumb = t_pose_im.resize((330, 330), Image.Resampling.LANCZOS)
    audit_im.alpha_composite(t_thumb, (ox + 2, oy + 46))
    audit_draw.text((ox + 12, oy + 10), t_label, fill=t_col, font=font_title)
    sub_txt = "Cam 1 Vu Khi (Tay Front)" if idx != 1 else "Demo Cam 2 Vu Khi (Front + Back)"
    audit_draw.text((ox + 12, oy + 28), f"{sub_txt} | edge_clip=0px", fill=(210, 220, 235, 255), font=font_sub)

# Panel 5 on Top Row: W001 Diagonal Card Preview + Weapon Grip 1 & Grip 2 Showcase
ox5 = 12 + 4 * 345
audit_draw.rectangle([ox5, 12, board_w - 12, 462], fill=(26, 31, 42, 255), outline=(148, 163, 184, 255), width=2)
audit_draw.text((ox5 + 12, 20), "W001: HAC KIEM TAN BINH (Preview Ngang Cheo)", fill=(245, 200, 90, 255), font=font_title)
card_prev = Image.open(W001_CARD_PNG).convert("RGBA").resize((436, 312), Image.Resampling.LANCZOS)
audit_im.alpha_composite(card_prev, (ox5 + 14, 48))
audit_draw.rectangle([ox5 + 14, 48, ox5 + 14 + 436, 48 + 312], outline=(90, 220, 135, 200), width=1)
audit_draw.text((ox5 + 14, 370), "884x632 PNG & 354x253 WebP (Dat cheo toi uu khung ngang)", fill=(130, 235, 165, 255), font=font_sub)
audit_draw.text((ox5 + 14, 392), "Grip 1 (Do): Tay Chinh (58, 38) | Grip 2 (Xanh): Tay Phu (30, 24)", fill=(220, 230, 245, 255), font=font_sub)

# Bottom Half: Isolated Stickman Parts (16 parts including Neck) + Weapon W001 with Grip 1 & Grip 2 Markers + Rig Skeleton
part_showcase = [
    ("head", "1. head (khong mat)"),
    ("neck", "2. neck (khop co)"),
    ("chest", "3. chest (than tren)"),
    ("hip_kilt", "4. hip (than duoi)"),
    ("arm_upper_front", "5. arm_upper_F"),
    ("arm_lower_front", "6. arm_lower_F"),
    ("hand_front", "7. hand_F (+co tay)"),
    ("arm_upper_back", "8. arm_upper_B"),
    ("arm_lower_back", "9. arm_lower_B"),
    ("hand_back", "10. hand_B (+co tay)"),
    ("leg_thigh_front", "11. thigh_F"),
    ("leg_shin_front", "12. shin_F"),
    ("foot_front", "13. foot_F (+co chan)"),
    ("leg_thigh_back", "14. thigh_B"),
    ("leg_shin_back", "15. shin_B"),
    ("foot_back", "16. foot_B (+co chan)"),
]
for idx, (pk, plabel) in enumerate(part_showcase):
    r_i, c_i = divmod(idx, 8)
    bx = 12 + c_i * 172
    by = 478 + r_i * 234
    audit_draw.rectangle([bx, by, bx + 164, by + 224], fill=(26, 31, 42, 255), outline=(65, 75, 95, 255), width=1)
    pim = PART_IMAGES_BY_TEAM["team_blue"][pk]
    px = bx + (164 - pim.width) // 2
    py = by + 36 + (180 - pim.height) // 2
    audit_im.alpha_composite(pim, (px, py))
    audit_draw.rectangle([px, py, px + pim.width, py + pim.height], outline=(90, 220, 135, 160), width=1)
    audit_draw.text((bx + 8, by + 8), f"{plabel} ({pim.width}x{pim.height})", fill=(230, 236, 245, 255), font=font_sub)
    audit_draw.text((bx + 8, by + 22), "tight-trimmed: 0px pad", fill=(100, 230, 140, 255), font=font_sub)

# Slot 17 (Row 2 Col 9): Weapon W001 Full Uncropped Sprite with Grip 1 (Red) & Grip 2 (Cyan)
bx_w = 12 + 8 * 172
by_w = 478 + 1 * 234
audit_draw.rectangle([bx_w, by_w, board_w - 12, by_w + 224], fill=(26, 31, 42, 255), outline=(245, 158, 11, 255), width=2)
wim = WEAPON_IMAGES["weapon_main"]
wx_p = bx_w + 24
wy_p = by_w + 28
audit_im.alpha_composite(wim, (wx_p, wy_p))
audit_draw.rectangle([wx_w := wx_p, wy_p, wx_p + wim.width, wy_p + wim.height], outline=(90, 220, 135, 180), width=1)
# Draw Grip 1 (Red) & Grip 2 (Cyan)
g1x, g1y = wx_p + G1_X, wy_p + G1_Y
g2x, g2y = wx_p + G2_X, wy_p + G2_Y
audit_draw.ellipse([g1x - 6, g1y - 6, g1x + 6, g1y + 6], fill=(240, 50, 50, 255), outline=(255, 255, 255, 255), width=2)
audit_draw.ellipse([g2x - 6, g2y - 6, g2x + 6, g2y + 6], fill=(40, 210, 255, 255), outline=(255, 255, 255, 255), width=2)
audit_draw.text((bx_w + 12, by_w + 8), f"17. W001 weapon_main ({wim.width}x{wim.height}) | edge_clip: 0px", fill=(245, 200, 90, 255), font=font_title)
audit_draw.text((bx_w + 12, by_w + 26), "Cham DO = Grip 1 (Tay Chinh) | Cham XANH = Grip 2 (Tay Phu)", fill=(130, 235, 165, 255), font=font_sub)

# Also draw 18-Bone Skeleton diagram in top-right of bottom section (Row 1 Col 9 area)
bx_sk = 12 + 8 * 172
by_sk = 478
audit_draw.rectangle([bx_sk, by_sk, board_w - 12, by_sk + 224], fill=(26, 31, 42, 255), outline=(56, 189, 248, 255), width=1)
sk_im, sk_world = render_pose({}, team_name="team_blue", show_weapon_front=True, show_weapon_back=False, canvas_size=512)
sk_draw = ImageDraw.Draw(sk_im, "RGBA")
for b in BONES:
    if b["name"] == "Weapon_Back":
        continue
    wx, wy, _, tx, ty = sk_world[b["name"]]
    draw_spine_bone(sk_draw, wx, wy, tx, ty)
sk_thumb = sk_im.resize((190, 190), Image.Resampling.LANCZOS)
audit_im.alpha_composite(sk_thumb, (bx_sk + (board_w - 12 - bx_sk - 190) // 2, by_sk + 30))
audit_draw.text((bx_sk + 12, by_sk + 8), "HE XUONG 18 BONE2D (CO KHOP CO + 2 VU KHI)", fill=(56, 189, 248, 255), font=font_title)

audit_path = os.path.join(STICKER_QC_DIR, "sticker_4teams_and_w001_audit.png")
audit_im.save(audit_path)
shutil.copyfile(audit_path, os.path.join(W001_QC_DIR, "sticker_4teams_and_w001_audit.png"))
shutil.copyfile(audit_path, os.path.join(ARTIFACT_DIR, "sticker_4teams_and_w001_audit.png"))
print(f"Saved 4-Team + W001 Audit Board -> {audit_path}")

# 4C. All 6 Actions Overview Board for Stickman + W001
ov_w, ov_h = 3 * 560 + 24, 2 * 560 + 24
ov_im = Image.new("RGBA", (ov_w, ov_h), (16, 19, 26, 255))
ov_draw = ImageDraw.Draw(ov_im)
total_edge_clips = 0

action_order = ["idle", "walk", "attack", "cast", "hurt", "death"]
team_cycle = ["team_blue", "team_red", "team_green", "team_amber", "team_blue", "team_red"]
for a_idx, act_name in enumerate(action_order):
    act = ACTIONS[act_name]
    rows, cols = act["grid"]
    frames = act["frames"]
    ar, ac = divmod(a_idx, 3)
    bx = 12 + ac * 560
    by = 12 + ar * 560
    ov_draw.rectangle([bx, by, bx + 544, by + 544], fill=(24, 28, 38, 255), outline=(65, 75, 95, 255), width=1)

    thumb_size = 240 if cols == 2 else 166
    grid_w = cols * thumb_size
    grid_h = rows * thumb_size
    gx0 = bx + (544 - grid_w) // 2
    gy0 = by + 36 + (500 - grid_h) // 2

    act_clips = 0
    t_for_act = team_cycle[a_idx]
    for f_idx, f_pose in enumerate(frames):
        f_im, _ = render_pose(f_pose, team_name=t_for_act, show_weapon_front=True, show_weapon_back=False, canvas_size=512)
        fa = np.array(f_im)[:, :, 3]
        f_clip = int(fa[0, :].sum() + fa[-1, :].sum() + fa[:, 0].sum() + fa[:, -1].sum())
        act_clips += f_clip
        total_edge_clips += f_clip

        fr, fc = divmod(f_idx, cols)
        tx = gx0 + fc * thumb_size
        ty = gy0 + fr * thumb_size
        ov_draw.rectangle([tx + 2, ty + 2, tx + thumb_size - 2, ty + thumb_size - 2], fill=(28, 33, 44, 255), outline=(50, 58, 74, 255), width=1)
        thumb = f_im.resize((thumb_size - 8, thumb_size - 8), Image.Resampling.LANCZOS)
        ov_im.alpha_composite(thumb, (tx + 4, ty + 4))
        base_y = ty + 4 + int(round(430.0 * (thumb_size - 8) / 512.0))
        ov_draw.line([(tx + 12, base_y), (tx + thumb_size - 12, base_y)], fill=(100, 220, 140, 170), width=1)

    ov_draw.text(
        (bx + 14, by + 10),
        f"Action {a_idx+1}: {act_name.upper()} ({t_for_act} | {len(frames)}f | edge_clip={act_clips}px)",
        fill=(235, 240, 250, 255),
        font=font_title,
    )

assert total_edge_clips == 0, f"Found {total_edge_clips} edge-clipped pixels!"
ov_path = os.path.join(W001_QC_DIR, "w001_sticker_all_6_actions_overview.png")
ov_im.save(ov_path)
shutil.copyfile(ov_path, os.path.join(ARTIFACT_DIR, "w001_sticker_all_6_actions_overview.png"))
print(f"Saved 6-Action Overview -> {ov_path} (total_edge_clips={total_edge_clips}px)")


# 5. Generate Godot 4 Scene (.tscn) & Script (.gd) for C001/W001 + Base Stickman
def generate_tscn_content(bones_data, actions_data):
    lines = []
    ext_count = 1 + len(bones_data) + len(VFX_LIST)
    sub_count = 1 + len(actions_data)
    lines.append(f'[gd_scene load_steps={ext_count + sub_count} format=3 uid="uid://c001stickerweapon"]')
    lines.append("")
    lines.append('[ext_resource type="Script" path="res://assets/weapons/w001_hac_kiem_tan_binh/godot/c001_hac_kiem_tan_binh.gd" id="1_script"]')

    part_ext_id = {}
    idx = 2
    for b in bones_data:
        p = b["part"]
        part_ext_id[p] = f"{idx}_{p}"
        if b["is_weapon"]:
            lines.append(f'[ext_resource type="Texture2D" path="res://assets/weapons/w001_hac_kiem_tan_binh/parts/{p}.png" id="{part_ext_id[p]}"]')
        else:
            lines.append(f'[ext_resource type="Texture2D" path="res://assets/sticker_hero/godot/parts/team_blue/{p}.png" id="{part_ext_id[p]}"]')
        idx += 1
    for fx in VFX_LIST:
        part_ext_id[fx] = f"{idx}_{fx}"
        lines.append(f'[ext_resource type="Texture2D" path="res://assets/weapons/w001_hac_kiem_tan_binh/parts/{fx}.png" id="{part_ext_id[fx]}"]')
        idx += 1
    lines.append("")

    bone_paths = {}
    for b in bones_data:
        if b["parent"] is None:
            bone_paths[b["name"]] = f"Skeleton2D/{b['name']}"
        else:
            bone_paths[b["name"]] = f"{bone_paths[b['parent']]}/{b['name']}"

    for act_name, act in actions_data.items():
        frames = act["frames"]
        length = act["length"]
        loop_mode = 1 if act["loop"] else 0
        lines.append(f'[sub_resource type="Animation" id="Animation_{act_name}"]')
        lines.append(f'resource_name = "{act_name}"')
        lines.append(f'length = {length:.2f}')
        lines.append(f'loop_mode = {loop_mode}')

        t_idx = 0
        times_str = ", ".join(f"{f['t']:.2f}" for f in frames)
        trans_str = ", ".join("1" for _ in frames)

        for b in bones_data:
            bname = b["name"]
            bpath = bone_paths[bname]
            rots = []
            positions = []
            for f in frames:
                if bname == "Hip":
                    dx, dy, drot = f.get("Hip", (0.0, 0.0, 0.0))
                else:
                    drot, dx, dy = f.get(bname, (0.0, 0.0, 0.0))
                rad = math.radians(b["rest_rot"] + drot)
                px = b["rest_x"] + dx
                py = b["rest_y"] + dy
                rots.append(f"{rad:.4f}")
                positions.append(f"Vector2({px:.1f}, {py:.1f})")

            lines.append(f'tracks/{t_idx}/type = "value"')
            lines.append(f'tracks/{t_idx}/imported = false')
            lines.append(f'tracks/{t_idx}/enabled = true')
            lines.append(f'tracks/{t_idx}/path = NodePath("{bpath}:rotation")')
            lines.append(f'tracks/{t_idx}/interp = 1')
            lines.append(f'tracks/{t_idx}/loop_wrap = true')
            lines.append(f'tracks/{t_idx}/keys = {{')
            lines.append(f'"times": PackedFloat32Array({times_str}),')
            lines.append(f'"transitions": PackedFloat32Array({trans_str}),')
            lines.append(f'"update": 0,')
            lines.append(f'"values": [{", ".join(rots)}]')
            lines.append(f'}}')
            t_idx += 1

            lines.append(f'tracks/{t_idx}/type = "value"')
            lines.append(f'tracks/{t_idx}/imported = false')
            lines.append(f'tracks/{t_idx}/enabled = true')
            lines.append(f'tracks/{t_idx}/path = NodePath("{bpath}:position")')
            lines.append(f'tracks/{t_idx}/interp = 1')
            lines.append(f'tracks/{t_idx}/loop_wrap = true')
            lines.append(f'tracks/{t_idx}/keys = {{')
            lines.append(f'"times": PackedFloat32Array({times_str}),')
            lines.append(f'"transitions": PackedFloat32Array({trans_str}),')
            lines.append(f'"update": 0,')
            lines.append(f'"values": [{", ".join(positions)}]')
            lines.append(f'}}')
            t_idx += 1

        lines.append("")

    lines.append('[sub_resource type="AnimationLibrary" id="AnimationLibrary_c001"]')
    lines.append('_data = {')
    for act_name in actions_data.keys():
        lines.append(f'"{act_name}": SubResource("Animation_{act_name}"),')
    lines.append('}')
    lines.append("")

    lines.append('[node name="C001_HacKiemTanBinh" type="Node2D"]')
    lines.append('script = ExtResource("1_script")')
    lines.append("")
    lines.append('[node name="Skeleton2D" type="Skeleton2D" parent="."]')
    lines.append("")

    for b in bones_data:
        bname = b["name"]
        parent_path = "Skeleton2D" if b["parent"] is None else bone_paths[b["parent"]]
        rad = math.radians(b["rest_rot"])
        ca, sa = math.cos(rad), math.sin(rad)
        rx, ry = b["rest_x"], b["rest_y"]
        if "tip_child" in b and b["tip_child"] in BONE_MAP:
            cb = BONE_MAP[b["tip_child"]]
            tx, ty = cb["rest_x"], cb["rest_y"]
        else:
            tx, ty = b.get("tip_offset", (0.0, 42.0))
        b_len = max(8.0, math.hypot(tx, ty))
        b_ang = math.atan2(ty, tx)

        lines.append(f'[node name="{bname}" type="Bone2D" parent="{parent_path}"]')
        lines.append(f'position = Vector2({rx:.1f}, {ry:.1f})')
        lines.append(f'rotation = {rad:.4f}')
        lines.append(f'rest = Transform2D({ca:.4f}, {sa:.4f}, {-sa:.4f}, {ca:.4f}, {rx:.1f}, {ry:.1f})')
        lines.append('auto_calculate_length_and_angle = false')
        lines.append(f'length = {b_len:.1f}')
        lines.append(f'bone_angle = {b_ang:.4f}')
        if b["is_weapon"]:
            lines.append(f'metadata/grip1 = Vector2({b["grip1_x"]:.1f}, {b["grip1_y"]:.1f})')
            lines.append(f'metadata/grip2 = Vector2({b["grip2_x"]:.1f}, {b["grip2_y"]:.1f})')
        lines.append("")

        lines.append(f'[node name="Sprite" type="Sprite2D" parent="{bone_paths[bname]}"]')
        if b["is_weapon"] and not b.get("visible_default", True):
            lines.append('visible = false')
        lines.append(f'z_index = {b["z_index"]}')
        lines.append('z_as_relative = false')
        lines.append(f'texture = ExtResource("{part_ext_id[b["part"]]}")')
        lines.append(f'offset = Vector2({b["offset_x"]:.2f}, {b["offset_y"]:.2f})')
        lines.append("")

    lines.append('[node name="VFXLayer" type="Node2D" parent="."]')
    lines.append('z_index = 20')
    lines.append('z_as_relative = false')
    lines.append("")
    for fx in VFX_LIST:
        lines.append(f'[node name="{fx}" type="Sprite2D" parent="VFXLayer"]')
        lines.append('visible = false')
        lines.append('position = Vector2(256, 256)')
        lines.append(f'texture = ExtResource("{part_ext_id[fx]}")')
        lines.append("")

    lines.append('[node name="AnimationPlayer" type="AnimationPlayer" parent="."]')
    lines.append('libraries = {')
    lines.append('"": SubResource("AnimationLibrary_c001")')
    lines.append('}')
    lines.append('autoplay = "idle"')
    lines.append("")
    return "\n".join(lines)


w001_tscn_path = os.path.join(W001_GODOT_DIR, "c001_hac_kiem_tan_binh.tscn")
base_tscn_path = os.path.join(STICKER_GODOT_DIR, "sticker_hero_base.tscn")
tscn_str = generate_tscn_content(BONES, ACTIONS)
with open(w001_tscn_path, "w", encoding="utf-8") as f:
    f.write(tscn_str)
with open(base_tscn_path, "w", encoding="utf-8") as f:
    f.write(tscn_str)

gd_content = """extends Node2D
class_name StickerHeroWithWeapon

## Tướng Stickman 4 Màu Đội (team_blue, team_red, team_green, team_amber) + Hệ Thống Vũ Khí Theo Thẻ Bài
## Hỗ trợ 2 vị trí cầm trên mỗi vũ khí (Grip 1 & Grip 2) và cầm nhiều vũ khí (Weapon_Front & Weapon_Back)

@export_enum("team_blue", "team_red", "team_green", "team_amber") var team_color: String = "team_blue":
	set(value):
		team_color = value
		_apply_team_textures()

@export var use_secondary_grip: bool = false:
	set(value):
		use_secondary_grip = value
		_apply_weapon_grip()

@export var dual_wield_enabled: bool = false:
	set(value):
		dual_wield_enabled = value
		if has_node("Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Hand_R/Weapon_Back/Sprite"):
			$Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Hand_R/Weapon_Back/Sprite.visible = dual_wield_enabled

@onready var anim_player: AnimationPlayer = $AnimationPlayer

func _ready() -> void:
	_apply_team_textures()
	_apply_weapon_grip()
	play_action("idle")

func play_action(action_name: String) -> void:
	if anim_player and anim_player.has_animation(action_name):
		anim_player.play(action_name)

func _apply_team_textures() -> void:
	if not is_inside_tree():
		return
	var bone_parts := {
		"Skeleton2D/Hip/Sprite": "hip_kilt",
		"Skeleton2D/Hip/Chest/Sprite": "chest",
		"Skeleton2D/Hip/Chest/Neck/Sprite": "neck",
		"Skeleton2D/Hip/Chest/Neck/Head/Sprite": "head",
		"Skeleton2D/Hip/Chest/UpperArm_L/Sprite": "arm_upper_front",
		"Skeleton2D/Hip/Chest/UpperArm_L/Forearm_L/Sprite": "arm_lower_front",
		"Skeleton2D/Hip/Chest/UpperArm_L/Forearm_L/Hand_L/Sprite": "hand_front",
		"Skeleton2D/Hip/Chest/UpperArm_R/Sprite": "arm_upper_back",
		"Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Sprite": "arm_lower_back",
		"Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Hand_R/Sprite": "hand_back",
		"Skeleton2D/Hip/Thigh_R/Sprite": "leg_thigh_front",
		"Skeleton2D/Hip/Thigh_R/Shin_R/Sprite": "leg_shin_front",
		"Skeleton2D/Hip/Thigh_R/Shin_R/Foot_R/Sprite": "foot_front",
		"Skeleton2D/Hip/Thigh_L/Sprite": "leg_thigh_back",
		"Skeleton2D/Hip/Thigh_L/Shin_L/Sprite": "leg_shin_back",
		"Skeleton2D/Hip/Thigh_L/Shin_L/Foot_L/Sprite": "foot_back",
	}
	for np in bone_parts.keys():
		if has_node(np):
			var tex_path := "res://assets/sticker_hero/godot/parts/%s/%s.png" % [team_color, bone_parts[np]]
			if ResourceLoader.exists(tex_path):
				get_node(np).texture = load(tex_path)

func _apply_weapon_grip() -> void:
	if not has_node("Skeleton2D/Hip/Chest/UpperArm_L/Forearm_L/Hand_L/Weapon_Front"):
		return
	var wf: Bone2D = $Skeleton2D/Hip/Chest/UpperArm_L/Forearm_L/Hand_L/Weapon_Front
	var sp: Sprite2D = wf.get_node("Sprite")
	var g: Vector2 = wf.get_meta("grip2", Vector2(30, 24)) if use_secondary_grip else wf.get_meta("grip1", Vector2(58, 38))
	if sp and sp.texture:
		sp.offset = Vector2(sp.texture.get_width() / 2.0 - g.x, sp.texture.get_height() / 2.0 - g.y)
"""
with open(os.path.join(W001_GODOT_DIR, "c001_hac_kiem_tan_binh.gd"), "w", encoding="utf-8") as f:
    f.write(gd_content)
with open(os.path.join(STICKER_GODOT_DIR, "sticker_hero_base.gd"), "w", encoding="utf-8") as f:
    f.write(gd_content)

print(f"Wrote Godot 4 .tscn & .gd -> {w001_tscn_path}")

# 6. Build Interactive HTML Sticker + Weapon Animation Editor (sticker_weapon_editor.html & w001_editor.html)
def file_to_b64(path):
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")


TEAM_PART_B64 = {}
for t in ["team_blue", "team_red", "team_green", "team_amber"]:
    TEAM_PART_B64[t] = {}
    for b in BONES:
        if not b["is_weapon"]:
            p = b["part"]
            TEAM_PART_B64[t][p] = file_to_b64(os.path.join(STICKER_PARTS_ROOT, t, f"{p}.png"))

WEAPON_PART_B64 = {}
for p in ["weapon_main", "weapon_offhand", "weapon_aura"] + VFX_LIST:
    WEAPON_PART_B64[p] = file_to_b64(os.path.join(W001_PARTS_DIR, f"{p}.png"))

CARD_PREVIEW_B64 = file_to_b64(W001_CARD_PNG)

html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Card_G — Sticker Hero (4 Màu Đội) + Weapon Rig Editor (W001: Hắc Kiếm Tàn Binh)</title>
<style>
  :root {{
    --bg: #0f131a;
    --panel: #171d28;
    --panel-alt: #1f2735;
    --border: #2e3a4e;
    --text: #e2e8f0;
    --muted: #94a3b8;
    --accent: #38bdf8;
    --gold: #f59e0b;
    --success: #22c55e;
    --danger: #ef4444;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    height: 100vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }}
  header {{
    background: var(--panel);
    border-bottom: 1px solid var(--border);
    padding: 8px 14px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    flex-wrap: wrap;
  }}
  .brand {{
    display: flex;
    align-items: center;
    gap: 10px;
  }}
  .badge {{
    background: rgba(245, 158, 11, 0.16);
    color: var(--gold);
    border: 1px solid rgba(245, 158, 11, 0.45);
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 700;
  }}
  .team-bar, .action-bar, .tool-bar {{
    display: flex;
    gap: 6px;
    align-items: center;
    flex-wrap: wrap;
  }}
  button, select {{
    background: var(--panel-alt);
    color: var(--text);
    border: 1px solid var(--border);
    padding: 6px 10px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: 0.15s;
  }}
  button:hover, select:hover {{ border-color: var(--accent); }}
  button.active {{
    background: rgba(56, 189, 248, 0.18);
    color: var(--accent);
    border-color: var(--accent);
  }}
  button.team-btn {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }}
  .dot {{
    width: 10px;
    height: 10px;
    border-radius: 50%;
    display: inline-block;
  }}
  button.primary {{
    background: rgba(34, 197, 94, 0.18);
    color: #4ade80;
    border-color: rgba(34, 197, 94, 0.55);
  }}
  button.primary:hover {{ background: rgba(34, 197, 94, 0.28); }}
  main {{
    flex: 1;
    display: grid;
    grid-template-columns: 310px 1fr 350px;
    overflow: hidden;
  }}
  .sidebar {{
    background: var(--panel);
    border-right: 1px solid var(--border);
    padding: 12px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }}
  .sidebar.right {{
    border-right: none;
    border-left: 1px solid var(--border);
  }}
  h3 {{
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--muted);
    margin-bottom: 4px;
  }}
  .card-box {{
    background: var(--panel-alt);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }}
  .card-preview-img {{
    width: 100%;
    aspect-ratio: 884 / 632;
    object-fit: cover;
    border-radius: 6px;
    border: 1px solid rgba(245, 158, 11, 0.45);
    background: #0d1117;
  }}
  .bone-list {{
    display: flex;
    flex-direction: column;
    gap: 4px;
  }}
  .bone-item {{
    padding: 6px 9px;
    border-radius: 6px;
    background: var(--panel-alt);
    border: 1px solid transparent;
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;
  }}
  .bone-item:hover {{ border-color: var(--border); }}
  .bone-item.selected {{
    border-color: var(--accent);
    background: rgba(56, 189, 248, 0.14);
    color: var(--accent);
    font-weight: 700;
  }}
  .viewport {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: radial-gradient(circle at center, #1e2636 0%, #0d1118 100%);
    position: relative;
    padding: 12px;
    gap: 10px;
  }}
  canvas {{
    background-image:
      linear-gradient(45deg, #161c26 25%, transparent 25%),
      linear-gradient(-45deg, #161c26 25%, transparent 25%),
      linear-gradient(45deg, transparent 75%, #161c26 75%),
      linear-gradient(-45deg, transparent 75%, #161c26 75%);
    background-size: 24px 24px;
    background-position: 0 0, 0 12px, 12px -12px, -12px 0;
    background-color: #11161f;
    border: 1px solid var(--border);
    border-radius: 10px;
    box-shadow: 0 14px 35px rgba(0, 0, 0, 0.5);
    cursor: grab;
  }}
  canvas:active {{ cursor: grabbing; }}
  .timeline-bar {{
    width: 512px;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 8px 12px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }}
  .timeline-controls {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }}
  .frame-pills {{
    display: flex;
    gap: 5px;
    flex-wrap: wrap;
  }}
  .control-group {{
    background: var(--panel-alt);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 9px;
    display: flex;
    flex-direction: column;
    gap: 7px;
  }}
  .slider-row {{
    display: grid;
    grid-template-columns: 74px 1fr 54px;
    align-items: center;
    gap: 6px;
    font-size: 12px;
  }}
  input[type="range"] {{ width: 100%; accent-color: var(--accent); }}
  input[type="number"] {{
    width: 100%;
    background: var(--bg);
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 3px 5px;
    font-size: 11px;
    text-align: right;
  }}
  .hint {{
    font-size: 11px;
    color: var(--muted);
    line-height: 1.45;
  }}
  .status-toast {{
    font-size: 12px;
    color: #4ade80;
    min-height: 18px;
  }}
  .check-row {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    cursor: pointer;
  }}
</style>
</head>
<body>
<header>
  <div class="brand">
    <span class="badge">STICKMAN 4 TEAMS + WEAPON SYSTEM</span>
    <strong>Tướng Sticker Basic + Vũ Khí Thẻ Bài</strong>
  </div>
  <div class="team-bar" id="teamBar">
    <button class="team-btn active" onclick="setTeam('team_blue', this)"><span class="dot" style="background:#3b82f6"></span>Đội 1: Xanh</button>
    <button class="team-btn" onclick="setTeam('team_red', this)"><span class="dot" style="background:#ef4444"></span>Đội 2: Đỏ</button>
    <button class="team-btn" onclick="setTeam('team_green', this)"><span class="dot" style="background:#22c55e"></span>Đội 3: Lá</button>
    <button class="team-btn" onclick="setTeam('team_amber', this)"><span class="dot" style="background:#f59e0b"></span>Đội 4: Vàng</button>
  </div>
  <div class="action-bar" id="actionBar"></div>
  <div class="tool-bar">
    <button id="btnPlay" class="active" onclick="togglePlay()">⏸ Pause</button>
    <button id="btnBones" class="active" onclick="toggleBones()">🦴 Bones: ON</button>
    <button class="primary" onclick="saveToGodotTscn()">💾 Save to .tscn</button>
  </div>
</header>

<main>
  <aside class="sidebar">
    <div class="card-box">
      <h3>Thẻ Bài & Vũ Khí Đang Trang Bị</h3>
      <select id="weaponSelect" onchange="onSelectWeapon()">
        <option value="w001">W001 — Hắc Kiếm Tàn Binh (Cấp N)</option>
      </select>
      <img id="cardPreviewImg" class="card-preview-img" alt="Diagonal Weapon Card Preview" />
      <div class="hint">
        Ảnh Preview Thẻ Bài (<strong>884×632</strong> ngang, đặt chéo vũ khí tối ưu khung hình).
      </div>
    </div>

    <div class="card-box">
      <h3>Thiết Lập 2 Vị Trí Cầm (Grip 1 & Grip 2) + Đa Vũ Khí</h3>
      <div style="display:flex; gap:6px; flex-wrap:wrap;">
        <button id="btnGrip1" class="active" onclick="selectGripSlot(1)">🔴 Cầm ở Grip 1 (Chính)</button>
        <button id="btnGrip2" onclick="selectGripSlot(2)">🔵 Cầm ở Grip 2 (Phụ)</button>
      </div>
      <button onclick="applyTwoHandedGripPose()">🤝 Pose Cầm 2 Tay (Tay Phải bám Grip 2)</button>
      <label class="check-row">
        <input type="checkbox" id="chkDualWield" onchange="toggleDualWield(this.checked)" />
        <span>Bật Vũ Khí Phụ (<strong>Weapon_Back</strong> ở Tay Sau)</span>
      </label>
      <label class="check-row">
        <input type="checkbox" id="chkWeaponAura" onchange="toggleWeaponAura(this.checked)" />
        <span>Hiệu ứng <strong>Weapon Aura</strong> (Demo thần binh cấp SSR)</span>
      </label>
      <div class="slider-row">
        <span>Grip 1 X/Y</span>
        <input type="range" id="grip1X" min="0" max="240" step="1" value="54" oninput="updateGripPoints()" />
        <input type="number" id="grip1Y" min="0" max="180" step="1" value="118" oninput="updateGripPoints()" />
      </div>
      <div class="slider-row">
        <span>Grip 2 X/Y</span>
        <input type="range" id="grip2X" min="0" max="240" step="1" value="28" oninput="updateGripPoints()" />
        <input type="number" id="grip2Y" min="0" max="180" step="1" value="136" oninput="updateGripPoints()" />
      </div>
      <div class="hint">
        • Chấm <strong>Đỏ</strong> trên kiếm = <code>Grip 1</code> | Chấm <strong>Xanh Cyan</strong> = <code>Grip 2</code>.
      </div>
    </div>

    <h3>Hệ Xương 17 Bone2D (Stickman + 2 Vũ Khí)</h3>
    <div class="bone-list" id="boneList"></div>
  </aside>

  <section class="viewport">
    <canvas id="rigCanvas" width="512" height="512"></canvas>
    <div class="timeline-bar">
      <div class="timeline-controls">
        <strong id="lblActionInfo">Action: IDLE</strong>
        <span id="lblTimeInfo" style="font-size:12px;color:var(--muted)">t = 0.00s</span>
      </div>
      <input type="range" id="timeScrubber" min="0" max="1.2" step="0.01" value="0" oninput="onScrubTime(this.value)" />
      <div class="frame-pills" id="framePills"></div>
    </div>
  </section>

  <aside class="sidebar right">
    <h3>Thông Số Khớp Xương Đang Chọn</h3>
    <div class="control-group">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <strong id="selectedBoneName" style="color:var(--accent)">Weapon_Front</strong>
        <button onclick="resetSelectedBone()">Reset Bone</button>
      </div>
      <div class="slider-row">
        <span>Rotate (°)</span>
        <input type="range" id="sldRot" min="-180" max="180" step="0.5" value="0" oninput="onBoneInput('rot', this.value)" />
        <input type="number" id="numRot" value="0" step="0.5" oninput="onBoneInput('rot', this.value)" />
      </div>
      <div class="slider-row">
        <span>Offset X</span>
        <input type="range" id="sldDx" min="-120" max="120" step="0.5" value="0" oninput="onBoneInput('dx', this.value)" />
        <input type="number" id="numDx" value="0" step="0.5" oninput="onBoneInput('dx', this.value)" />
      </div>
      <div class="slider-row">
        <span>Offset Y</span>
        <input type="range" id="sldDy" min="-120" max="120" step="0.5" value="0" oninput="onBoneInput('dy', this.value)" />
        <input type="number" id="numDy" value="0" step="0.5" oninput="onBoneInput('dy', this.value)" />
      </div>
    </div>

    <h3>Vị Trí Cốt (Rest Pose & Pivot)</h3>
    <div class="control-group">
      <div class="slider-row">
        <span>Rest X</span>
        <input type="range" id="sldRestX" min="-160" max="360" step="0.5" value="0" oninput="onRestInput('rest_x', this.value)" />
        <input type="number" id="numRestX" value="0" step="0.5" oninput="onRestInput('rest_x', this.value)" />
      </div>
      <div class="slider-row">
        <span>Rest Y</span>
        <input type="range" id="sldRestY" min="-160" max="420" step="0.5" value="0" oninput="onRestInput('rest_y', this.value)" />
        <input type="number" id="numRestY" value="0" step="0.5" oninput="onRestInput('rest_y', this.value)" />
      </div>
      <div class="slider-row">
        <span>Pivot X</span>
        <input type="range" id="sldPivX" min="0" max="240" step="0.5" value="0" oninput="onRestInput('pivot_x', this.value)" />
        <input type="number" id="numPivX" value="0" step="0.5" oninput="onRestInput('pivot_x', this.value)" />
      </div>
      <div class="slider-row">
        <span>Pivot Y</span>
        <input type="range" id="sldPivY" min="0" max="240" step="0.5" value="0" oninput="onRestInput('pivot_y', this.value)" />
        <input type="number" id="numPivY" value="0" step="0.5" oninput="onRestInput('pivot_y', this.value)" />
      </div>
    </div>

    <div class="status-toast" id="statusToast">Sẵn sàng — Chọn màu đội, vũ khí, Grip 1/2 hoặc chỉnh pose!</div>

    <div class="hint">
      • <strong>Save to .tscn:</strong> Lưu trực tiếp toàn bộ cây xương <code>Skeleton2D</code> (17 <code>Bone2D</code>), tọa độ <code>Grip 1 / Grip 2</code> và <code>AnimationLibrary</code> 6 action thẳng vào file <code>c001_hac_kiem_tan_binh.tscn</code>.<br/>
      • <strong>Kiến trúc Tối Ưu Token:</strong> 1 bộ Stickman 4 màu đội dùng chung cho cả 80 thẻ bài; mỗi thẻ bài chỉ cần vẽ bộ Vũ Khí + cấu hình animation tại đây.
    </div>
  </aside>
</main>

<script>
const BONES = {json.dumps(BONES, ensure_ascii=False)};
const ACTIONS = {json.dumps(ACTIONS, ensure_ascii=False)};
const VFX_LIST = {json.dumps(VFX_LIST, ensure_ascii=False)};
const TEAM_PART_B64 = {json.dumps(TEAM_PART_B64, ensure_ascii=False)};
const WEAPON_PART_B64 = {json.dumps(WEAPON_PART_B64, ensure_ascii=False)};
const CARD_PREVIEW_B64 = {json.dumps(CARD_PREVIEW_B64, ensure_ascii=False)};

document.getElementById("cardPreviewImg").src = CARD_PREVIEW_B64;

const TEAM_IMAGES = {{}};
for (const [team, dict] of Object.entries(TEAM_PART_B64)) {{
  TEAM_IMAGES[team] = {{}};
  for (const [part, b64] of Object.entries(dict)) {{
    const img = new Image();
    img.src = b64;
    TEAM_IMAGES[team][part] = img;
  }}
}}

const WEAPON_IMAGES = {{}};
for (const [part, b64] of Object.entries(WEAPON_PART_B64)) {{
  const img = new Image();
  img.src = b64;
  WEAPON_IMAGES[part] = img;
}}

let currentTeam = "team_blue";
let currentAction = "idle";
let currentFrameIdx = 0;
let currentTime = 0.0;
let isPlaying = true;
let showBones = true;
let showDualWield = false;
let showWeaponAura = false;
let activeGripSlot = 1;
let selectedBone = "Weapon_Front";
let lastTick = performance.now();

const BONE_MAP = {{}};
BONES.forEach(b => BONE_MAP[b.name] = b);

function setTeam(teamKey, btnEl) {{
  currentTeam = teamKey;
  document.querySelectorAll("#teamBar .team-btn").forEach(b => b.classList.remove("active"));
  if (btnEl) btnEl.classList.add("active");
  document.getElementById("statusToast").textContent = "Đã chuyển màu đội sang: " + teamKey;
}}

function selectGripSlot(slot) {{
  activeGripSlot = slot;
  document.getElementById("btnGrip1").classList.toggle("active", slot === 1);
  document.getElementById("btnGrip2").classList.toggle("active", slot === 2);
  const wf = BONE_MAP["Weapon_Front"];
  if (slot === 1) {{
    wf.pivot_x = wf.grip1_x;
    wf.pivot_y = wf.grip1_y;
  }} else {{
    wf.pivot_x = wf.grip2_x;
    wf.pivot_y = wf.grip2_y;
  }}
  wf.offset_x = Number((wf.width / 2.0 - wf.pivot_x).toFixed(2));
  wf.offset_y = Number((wf.height / 2.0 - wf.pivot_y).toFixed(2));
  syncInspector();
  document.getElementById("statusToast").textContent = "Đang cầm vũ khí tại Grip " + slot + " (" + wf.pivot_x + ", " + wf.pivot_y + ")";
}}

function updateGripPoints() {{
  const wf = BONE_MAP["Weapon_Front"];
  wf.grip1_x = parseFloat(document.getElementById("grip1X").value) || 0;
  wf.grip1_y = parseFloat(document.getElementById("grip1Y").value) || 0;
  wf.grip2_x = parseFloat(document.getElementById("grip2X").value) || 0;
  wf.grip2_y = parseFloat(document.getElementById("grip2Y").value) || 0;
  selectGripSlot(activeGripSlot);
}}

function applyTwoHandedGripPose() {{
  const f = ACTIONS[currentAction].frames[currentFrameIdx];
  f["UpperArm_R"] = [-26, 4, 2];
  f["Forearm_R"] = [-22, 0, 0];
  f["Hand_R"] = [-8, 0, 0];
  syncInspector();
  document.getElementById("statusToast").textContent = "Đã áp dụng Pose Cầm 2 Tay (Tay Phải bám vào Grip 2 trên cán kiếm)!";
}}

function toggleDualWield(checked) {{
  showDualWield = checked;
  document.getElementById("statusToast").textContent = checked
    ? "Đã bật Vũ Khí Phụ (Weapon_Back trên Hand_R)!"
    : "Đã tắt Vũ Khí Phụ (chỉ cầm Weapon_Front).";
}}

function toggleWeaponAura(checked) {{
  showWeaponAura = checked;
  document.getElementById("statusToast").textContent = checked
    ? "Đã bật hiệu ứng Weapon Aura bao quanh vũ khí (Demo cấp SSR)!"
    : "Đã tắt hiệu ứng Weapon Aura.";
}}

function onSelectWeapon() {{
  document.getElementById("statusToast").textContent = "Đang chọn: W001 — Hắc Kiếm Tàn Binh";
}}

function initUI() {{
  const actionBar = document.getElementById("actionBar");
  actionBar.innerHTML = "";
  Object.keys(ACTIONS).forEach(act => {{
    const btn = document.createElement("button");
    btn.textContent = act.toUpperCase();
    btn.className = act === currentAction ? "active" : "";
    btn.onclick = () => selectAction(act);
    actionBar.appendChild(btn);
  }});

  const boneList = document.getElementById("boneList");
  boneList.innerHTML = "";
  BONES.forEach(b => {{
    const div = document.createElement("div");
    div.className = "bone-item" + (b.name === selectedBone ? " selected" : "");
    div.innerHTML = `<span>${{b.name}}</span><span style="color:var(--muted);font-size:11px">z:${{b.z_index}}</span>`;
    div.onclick = () => selectBone(b.name);
    boneList.appendChild(div);
  }});

  rebuildFramePills();
  syncInspector();
}}

function selectAction(act) {{
  currentAction = act;
  currentFrameIdx = 0;
  currentTime = 0.0;
  const sc = document.getElementById("timeScrubber");
  sc.max = ACTIONS[act].length;
  sc.value = 0;
  document.querySelectorAll("#actionBar button").forEach(b => {{
    b.classList.toggle("active", b.textContent === act.toUpperCase());
  }});
  rebuildFramePills();
  syncInspector();
}}

function rebuildFramePills() {{
  const pills = document.getElementById("framePills");
  pills.innerHTML = "";
  const frames = ACTIONS[currentAction].frames;
  frames.forEach((f, idx) => {{
    const b = document.createElement("button");
    b.textContent = `F${{idx + 1}} (${{f.t.toFixed(2)}}s)`;
    b.className = idx === currentFrameIdx ? "active" : "";
    b.onclick = () => {{
      isPlaying = false;
      updatePlayBtn();
      currentFrameIdx = idx;
      currentTime = f.t;
      document.getElementById("timeScrubber").value = currentTime;
      rebuildFramePills();
      syncInspector();
    }};
    pills.appendChild(b);
  }});
}}

function selectBone(bname) {{
  selectedBone = bname;
  document.querySelectorAll(".bone-item").forEach(el => {{
    el.classList.toggle("selected", el.firstChild.textContent === bname);
  }});
  syncInspector();
}}

function getFramePoseAtTime(actName, t) {{
  const act = ACTIONS[actName];
  const frames = act.frames;
  if (!isPlaying) return frames[currentFrameIdx];
  if (frames.length === 1) return frames[0];

  let i0 = 0;
  for (let i = 0; i < frames.length - 1; i++) {{
    if (t >= frames[i].t && t <= frames[i + 1].t) {{
      i0 = i;
      break;
    }}
    if (t > frames[frames.length - 1].t) {{
      i0 = frames.length - 1;
    }}
  }}
  const i1 = (i0 + 1) % frames.length;
  const f0 = frames[i0];
  const f1 = frames[i1];
  const t0 = f0.t;
  const t1 = i1 === 0 ? act.length : f1.t;
  const alpha = t1 > t0 ? Math.max(0, Math.min(1, (t - t0) / (t1 - t0))) : 0;

  const interp = {{ t }};
  BONES.forEach(b => {{
    const name = b.name;
    const v0 = f0[name] || [0, 0, 0];
    const v1 = (i1 === 0 && !act.loop) ? v0 : (f1[name] || [0, 0, 0]);
    interp[name] = [
      v0[0] + (v1[0] - v0[0]) * alpha,
      v0[1] + (v1[1] - v0[1]) * alpha,
      v0[2] + (v1[2] - v0[2]) * alpha,
    ];
  }});
  const m0 = f0.modulate_a !== undefined ? f0.modulate_a : 1.0;
  const m1 = f1.modulate_a !== undefined ? f1.modulate_a : 1.0;
  interp.modulate_a = m0 + (m1 - m0) * alpha;
  interp.vfx = f0.vfx || {{}};
  return interp;
}}

function computeWorldTransforms(framePose) {{
  const world = {{}};
  BONES.forEach(b => {{
    const name = b.name;
    const parent = b.parent;
    let dx = 0, dy = 0, drot = 0;
    const val = framePose[name] || [0, 0, 0];
    if (name === "Hip") {{
      dx = val[0]; dy = val[1]; drot = val[2];
    }} else {{
      drot = val[0]; dx = val[1]; dy = val[2];
    }}
    const lx = b.rest_x + dx;
    const ly = b.rest_y + dy;
    const lrot = b.rest_rot + drot;
    let wx, wy, wrot;
    if (!parent) {{
      wx = lx; wy = ly; wrot = lrot;
    }} else {{
      const p = world[parent];
      const rad = p.wrot * Math.PI / 180.0;
      const ca = Math.cos(rad), sa = Math.sin(rad);
      wx = p.wx + lx * ca - ly * sa;
      wy = p.wy + lx * sa + ly * ca;
      wrot = p.wrot + lrot;
    }}
    world[name] = {{ wx, wy, wrot, tx: wx, ty: wy }};
  }});

  BONES.forEach(b => {{
    const w = world[b.name];
    if (b.tip_child && world[b.tip_child]) {{
      w.tx = world[b.tip_child].wx;
      w.ty = world[b.tip_child].wy;
    }} else if (b.tip_offset) {{
      const rad = w.wrot * Math.PI / 180.0;
      const ca = Math.cos(rad), sa = Math.sin(rad);
      w.tx = w.wx + b.tip_offset[0] * ca - b.tip_offset[1] * sa;
      w.ty = w.wy + b.tip_offset[0] * sa + b.tip_offset[1] * ca;
    }}
  }});
  return world;
}}

function syncInspector() {{
  const b = BONE_MAP[selectedBone];
  const f = ACTIONS[currentAction].frames[currentFrameIdx];
  const val = f[selectedBone] || [0, 0, 0];
  let rot = 0, dx = 0, dy = 0;
  if (selectedBone === "Hip") {{
    dx = val[0]; dy = val[1]; rot = val[2];
  }} else {{
    rot = val[0]; dx = val[1]; dy = val[2];
  }}
  document.getElementById("selectedBoneName").textContent = selectedBone;
  document.getElementById("sldRot").value = rot;
  document.getElementById("numRot").value = rot;
  document.getElementById("sldDx").value = dx;
  document.getElementById("numDx").value = dx;
  document.getElementById("sldDy").value = dy;
  document.getElementById("numDy").value = dy;

  document.getElementById("sldRestX").value = b.rest_x;
  document.getElementById("numRestX").value = b.rest_x;
  document.getElementById("sldRestY").value = b.rest_y;
  document.getElementById("numRestY").value = b.rest_y;
  document.getElementById("sldPivX").value = b.pivot_x;
  document.getElementById("numPivX").value = b.pivot_x;
  document.getElementById("sldPivY").value = b.pivot_y;
  document.getElementById("numPivY").value = b.pivot_y;

  document.getElementById("lblActionInfo").textContent =
    `Action: ${{currentAction.toUpperCase()}} (Frame ${{currentFrameIdx + 1}}/${{ACTIONS[currentAction].frames.length}})`;
}}

function onBoneInput(field, rawVal) {{
  isPlaying = false;
  updatePlayBtn();
  const v = parseFloat(rawVal) || 0;
  const f = ACTIONS[currentAction].frames[currentFrameIdx];
  if (!f[selectedBone]) f[selectedBone] = [0, 0, 0];
  if (selectedBone === "Hip") {{
    if (field === "dx") f.Hip[0] = v;
    if (field === "dy") f.Hip[1] = v;
    if (field === "rot") f.Hip[2] = v;
  }} else {{
    if (field === "rot") f[selectedBone][0] = v;
    if (field === "dx") f[selectedBone][1] = v;
    if (field === "dy") f[selectedBone][2] = v;
  }}
  syncInspector();
}}

function onRestInput(field, rawVal) {{
  const v = parseFloat(rawVal) || 0;
  const b = BONE_MAP[selectedBone];
  b[field] = v;
  b.offset_x = Number((b.width / 2.0 - b.pivot_x).toFixed(2));
  b.offset_y = Number((b.height / 2.0 - b.pivot_y).toFixed(2));
  syncInspector();
}}

function resetSelectedBone() {{
  const f = ACTIONS[currentAction].frames[currentFrameIdx];
  f[selectedBone] = [0, 0, 0];
  syncInspector();
}}

function togglePlay() {{
  isPlaying = !isPlaying;
  updatePlayBtn();
}}

function updatePlayBtn() {{
  const btn = document.getElementById("btnPlay");
  btn.textContent = isPlaying ? "⏸ Pause" : "▶ Play";
  btn.classList.toggle("active", isPlaying);
}}

function toggleBones() {{
  showBones = !showBones;
  const btn = document.getElementById("btnBones");
  btn.textContent = showBones ? "🦴 Bones: ON" : "🦴 Bones: OFF";
  btn.classList.toggle("active", showBones);
}}

function onScrubTime(val) {{
  isPlaying = false;
  updatePlayBtn();
  currentTime = parseFloat(val) || 0;
  const frames = ACTIONS[currentAction].frames;
  let best = 0;
  for (let i = 0; i < frames.length; i++) {{
    if (Math.abs(frames[i].t - currentTime) < Math.abs(frames[best].t - currentTime)) best = i;
  }}
  currentFrameIdx = best;
  rebuildFramePills();
  syncInspector();
}}

const canvas = document.getElementById("rigCanvas");
const ctx = canvas.getContext("2d");
let dragging = false;

canvas.addEventListener("mousedown", e => {{
  const rect = canvas.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;
  const pose = getFramePoseAtTime(currentAction, currentTime);
  const world = computeWorldTransforms(pose);

  let nearest = null;
  let bestDist = 26;
  BONES.forEach(b => {{
    if (b.name === "Weapon_Back" && !showDualWield) return;
    const w = world[b.name];
    const d = Math.hypot(w.wx - mx, w.wy - my);
    if (d < bestDist) {{
      bestDist = d;
      nearest = b.name;
    }}
  }});
  if (nearest) {{
    selectBone(nearest);
    dragging = true;
    isPlaying = false;
    updatePlayBtn();
  }}
}});

window.addEventListener("mousemove", e => {{
  if (!dragging) return;
  const rect = canvas.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;
  const f = ACTIONS[currentAction].frames[currentFrameIdx];
  const world = computeWorldTransforms(f);
  const w = world[selectedBone];
  if (selectedBone === "Hip") {{
    const b = BONE_MAP.Hip;
    f.Hip = [Number((mx - b.rest_x).toFixed(1)), Number((my - b.rest_y).toFixed(1)), f.Hip ? f.Hip[2] : 0];
  }} else {{
    const ang = Math.atan2(my - w.wy, mx - w.wx) * 180.0 / Math.PI - 90.0;
    const cur = f[selectedBone] || [0, 0, 0];
    f[selectedBone] = [Number(ang.toFixed(1)), cur[1], cur[2]];
  }}
  syncInspector();
}});

window.addEventListener("mouseup", () => {{ dragging = false; }});

function renderLoop(now) {{
  const dt = (now - lastTick) / 1000.0;
  lastTick = now;

  const act = ACTIONS[currentAction];
  if (isPlaying) {{
    currentTime += dt;
    if (currentTime > act.length) {{
      currentTime = act.loop ? (currentTime % act.length) : 0.0;
    }}
    document.getElementById("timeScrubber").value = currentTime;
    let best = 0;
    for (let i = 0; i < act.frames.length; i++) {{
      if (currentTime >= act.frames[i].t) best = i;
    }}
    if (best !== currentFrameIdx) {{
      currentFrameIdx = best;
      rebuildFramePills();
    }}
  }}
  document.getElementById("lblTimeInfo").textContent = `t = ${{currentTime.toFixed(2)}}s / ${{act.length.toFixed(2)}}s`;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Baseline ground reference line (y = 430)
  ctx.strokeStyle = "rgba(34, 197, 94, 0.35)";
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(48, 430);
  ctx.lineTo(464, 430);
  ctx.stroke();

  const pose = getFramePoseAtTime(currentAction, currentTime);
  const world = computeWorldTransforms(pose);
  const modA = pose.modulate_a !== undefined ? pose.modulate_a : 1.0;

  const sortedBones = [...BONES].sort((a, b) => a.z_index - b.z_index);
  sortedBones.forEach(b => {{
    if (b.name === "Weapon_Back" && !showDualWield) return;
    const img = b.is_weapon ? WEAPON_IMAGES[b.part] : TEAM_IMAGES[currentTeam][b.part];
    if (!img || !img.complete) return;
    const w = world[b.name];

    // Optional SSR Weapon Aura behind/around Weapon_Front
    if (b.name === "Weapon_Front" && showWeaponAura && WEAPON_IMAGES["weapon_aura"] && WEAPON_IMAGES["weapon_aura"].complete) {{
      const auraImg = WEAPON_IMAGES["weapon_aura"];
      const pulse = 0.96 + 0.08 * Math.sin(now * 0.008);
      ctx.save();
      ctx.globalAlpha = modA * (0.72 + 0.22 * Math.sin(now * 0.01));
      ctx.translate(w.wx, w.wy);
      ctx.rotate(w.wrot * Math.PI / 180.0);
      ctx.scale(pulse, pulse);
      ctx.drawImage(auraImg, -b.pivot_x - 24, -b.pivot_y - 24);
      ctx.restore();
    }}

    ctx.save();
    ctx.globalAlpha = modA;
    ctx.translate(w.wx, w.wy);
    ctx.rotate(w.wrot * Math.PI / 180.0);
    ctx.drawImage(img, -b.pivot_x, -b.pivot_y);

    // Draw Grip 1 & Grip 2 markers on Weapon_Front when Bones overlay is ON
    if (b.name === "Weapon_Front" && showBones) {{
      ctx.fillStyle = "#ef4444";
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.arc(b.grip1_x - b.pivot_x, b.grip1_y - b.pivot_y, 5, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = "#38bdf8";
      ctx.beginPath();
      ctx.arc(b.grip2_x - b.pivot_x, b.grip2_y - b.pivot_y, 5, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
    }}
    ctx.restore();
  }});

  if (pose.vfx) {{
    Object.entries(pose.vfx).forEach(([fxName, fxCfg]) => {{
      const img = WEAPON_IMAGES[fxName];
      if (!img || !img.complete) return;
      const sc = fxCfg.scale !== undefined ? fxCfg.scale : 1.0;
      const al = fxCfg.alpha !== undefined ? fxCfg.alpha : 1.0;
      const rot = fxCfg.rot || 0;
      ctx.save();
      ctx.globalAlpha = al;
      ctx.translate(fxCfg.pos[0], fxCfg.pos[1]);
      ctx.rotate(rot * Math.PI / 180.0);
      ctx.scale(sc, sc);
      ctx.drawImage(img, -img.width / 2.0, -img.height / 2.0);
      ctx.restore();
    }});
  }}

  if (showBones) {{
    BONES.forEach(b => {{
      if (b.name === "Weapon_Back" && !showDualWield) return;
      const w = world[b.name];
      const isSel = b.name === selectedBone;
      const dx = w.tx - w.wx, dy = w.ty - w.wy;
      const len = Math.hypot(dx, dy);
      if (len > 2) {{
        const ux = dx / len, uy = dy / len;
        const px = -uy, py = ux;
        const bw = Math.min(5.5, Math.max(2.5, len * 0.10));
        const mx = w.wx + dx * 0.22, my = w.wy + dy * 0.22;
        ctx.beginPath();
        ctx.moveTo(w.wx, w.wy);
        ctx.lineTo(mx + px * bw, my + py * bw);
        ctx.lineTo(w.tx, w.ty);
        ctx.lineTo(mx - px * bw, my - py * bw);
        ctx.closePath();
        ctx.fillStyle = isSel ? "rgba(245, 158, 11, 0.65)" : "rgba(56, 189, 248, 0.45)";
        ctx.strokeStyle = isSel ? "#f59e0b" : "#38bdf8";
        ctx.lineWidth = isSel ? 2 : 1.2;
        ctx.fill();
        ctx.stroke();
      }}
      ctx.beginPath();
      ctx.arc(w.wx, w.wy, isSel ? 5.5 : 4, 0, Math.PI * 2);
      ctx.fillStyle = isSel ? "#f59e0b" : "#ef4444";
      ctx.fill();
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }});
  }}

  requestAnimationFrame(renderLoop);
}}

function buildGodotTscnString() {{
  const lines = [];
  const extCount = 1 + BONES.length + VFX_LIST.length;
  const subCount = 1 + Object.keys(ACTIONS).length;
  lines.push(`[gd_scene load_steps=${{extCount + subCount}} format=3 uid="uid://c001stickerweapon"]`);
  lines.push("");
  lines.push('[ext_resource type="Script" path="res://assets/weapons/w001_hac_kiem_tan_binh/godot/c001_hac_kiem_tan_binh.gd" id="1_script"]');

  const partExtId = {{}};
  let idx = 2;
  BONES.forEach(b => {{
    partExtId[b.part] = `${{idx}}_${{b.part}}`;
    if (b.is_weapon) {{
      lines.push(`[ext_resource type="Texture2D" path="res://assets/weapons/w001_hac_kiem_tan_binh/parts/${{b.part}}.png" id="${{partExtId[b.part]}}"]`);
    }} else {{
      lines.push(`[ext_resource type="Texture2D" path="res://assets/sticker_hero/godot/parts/${{currentTeam}}/${{b.part}}.png" id="${{partExtId[b.part]}}"]`);
    }}
    idx++;
  }});
  VFX_LIST.forEach(fx => {{
    partExtId[fx] = `${{idx}}_${{fx}}`;
    lines.push(`[ext_resource type="Texture2D" path="res://assets/weapons/w001_hac_kiem_tan_binh/parts/${{fx}}.png" id="${{partExtId[fx]}}"]`);
    idx++;
  }});
  lines.push("");

  const bonePaths = {{}};
  BONES.forEach(b => {{
    bonePaths[b.name] = b.parent ? `${{bonePaths[b.parent]}}/${{b.name}}` : `Skeleton2D/${{b.name}}`;
  }});

  Object.entries(ACTIONS).forEach(([actName, act]) => {{
    const frames = act.frames;
    lines.push(`[sub_resource type="Animation" id="Animation_${{actName}}"]`);
    lines.push(`resource_name = "${{actName}}"`);
    lines.push(`length = ${{act.length.toFixed(2)}}`);
    lines.push(`loop_mode = ${{act.loop ? 1 : 0}}`);

    const timesStr = frames.map(f => f.t.toFixed(2)).join(", ");
    const transStr = frames.map(() => "1").join(", ");
    let tIdx = 0;

    BONES.forEach(b => {{
      const bname = b.name;
      const bpath = bonePaths[bname];
      const rots = [];
      const pos = [];
      frames.forEach(f => {{
        const val = f[bname] || [0, 0, 0];
        let dx = 0, dy = 0, drot = 0;
        if (bname === "Hip") {{
          dx = val[0]; dy = val[1]; drot = val[2];
        }} else {{
          drot = val[0]; dx = val[1]; dy = val[2];
        }}
        const rad = (b.rest_rot + drot) * Math.PI / 180.0;
        rots.push(rad.toFixed(4));
        pos.push(`Vector2(${{(b.rest_x + dx).toFixed(1)}}, ${{(b.rest_y + dy).toFixed(1)}})`);
      }});

      lines.push(`tracks/${{tIdx}}/type = "value"`);
      lines.push(`tracks/${{tIdx}}/imported = false`);
      lines.push(`tracks/${{tIdx}}/enabled = true`);
      lines.push(`tracks/${{tIdx}}/path = NodePath("${{bpath}}:rotation")`);
      lines.push(`tracks/${{tIdx}}/interp = 1`);
      lines.push(`tracks/${{tIdx}}/loop_wrap = true`);
      lines.push(`tracks/${{tIdx}}/keys = {{`);
      lines.push(`"times": PackedFloat32Array(${{timesStr}}),`);
      lines.push(`"transitions": PackedFloat32Array(${{transStr}}),`);
      lines.push(`"update": 0,`);
      lines.push(`"values": [${{rots.join(", ")}}]`);
      lines.push(`}}`);
      tIdx++;

      lines.push(`tracks/${{tIdx}}/type = "value"`);
      lines.push(`tracks/${{tIdx}}/imported = false`);
      lines.push(`tracks/${{tIdx}}/enabled = true`);
      lines.push(`tracks/${{tIdx}}/path = NodePath("${{bpath}}:position")`);
      lines.push(`tracks/${{tIdx}}/interp = 1`);
      lines.push(`tracks/${{tIdx}}/loop_wrap = true`);
      lines.push(`tracks/${{tIdx}}/keys = {{`);
      lines.push(`"times": PackedFloat32Array(${{timesStr}}),`);
      lines.push(`"transitions": PackedFloat32Array(${{transStr}}),`);
      lines.push(`"update": 0,`);
      lines.push(`"values": [${{pos.join(", ")}}]`);
      lines.push(`}}`);
      tIdx++;
    }});
    lines.push("");
  }});

  lines.push('[sub_resource type="AnimationLibrary" id="AnimationLibrary_c001"]');
  lines.push('_data = {{');
  Object.keys(ACTIONS).forEach(actName => {{
    lines.push(`"${{actName}}": SubResource("Animation_${{actName}}"),`);
  }});
  lines.push('}}');
  lines.push("");

  lines.push('[node name="C001_HacKiemTanBinh" type="Node2D"]');
  lines.push('script = ExtResource("1_script")');
  lines.push("");
  lines.push('[node name="Skeleton2D" type="Skeleton2D" parent="."]');
  lines.push("");

  BONES.forEach(b => {{
    const bname = b.name;
    const parentPath = b.parent ? bonePaths[b.parent] : "Skeleton2D";
    const rad = b.rest_rot * Math.PI / 180.0;
    const ca = Math.cos(rad), sa = Math.sin(rad);
    let tx = 0, ty = 42;
    if (b.tip_child && BONE_MAP[b.tip_child]) {{
      tx = BONE_MAP[b.tip_child].rest_x;
      ty = BONE_MAP[b.tip_child].rest_y;
    }} else if (b.tip_offset) {{
      tx = b.tip_offset[0];
      ty = b.tip_offset[1];
    }}
    const bLen = Math.max(8.0, Math.hypot(tx, ty));
    const bAng = Math.atan2(ty, tx);

    lines.push(`[node name="${{bname}}" type="Bone2D" parent="${{parentPath}}"]`);
    lines.push(`position = Vector2(${{b.rest_x.toFixed(1)}}, ${{b.rest_y.toFixed(1)}})`);
    lines.push(`rotation = ${{rad.toFixed(4)}}`);
    lines.push(`rest = Transform2D(${{ca.toFixed(4)}}, ${{sa.toFixed(4)}}, ${{-sa.toFixed(4)}}, ${{ca.toFixed(4)}}, ${{b.rest_x.toFixed(1)}}, ${{b.rest_y.toFixed(1)}})`);
    lines.push('auto_calculate_length_and_angle = false');
    lines.push(`length = ${{bLen.toFixed(1)}}`);
    lines.push(`bone_angle = ${{bAng.toFixed(4)}}`);
    if (b.is_weapon) {{
      lines.push(`metadata/grip1 = Vector2(${{b.grip1_x.toFixed(1)}}, ${{b.grip1_y.toFixed(1)}})`);
      lines.push(`metadata/grip2 = Vector2(${{b.grip2_x.toFixed(1)}}, ${{b.grip2_y.toFixed(1)}})`);
    }}
    lines.push("");

    lines.push(`[node name="Sprite" type="Sprite2D" parent="${{bonePaths[bname]}}"]`);
    if (b.name === "Weapon_Back" && !showDualWield) {{
      lines.push('visible = false');
    }}
    lines.push(`z_index = ${{b.z_index}}`);
    lines.push('z_as_relative = false');
    lines.push(`texture = ExtResource("${{partExtId[b.part]}}")`);
    lines.push(`offset = Vector2(${{b.offset_x.toFixed(2)}}, ${{b.offset_y.toFixed(2)}})`);
    lines.push("");
  }});

  lines.push('[node name="VFXLayer" type="Node2D" parent="."]');
  lines.push('z_index = 20');
  lines.push('z_as_relative = false');
  lines.push("");
  VFX_LIST.forEach(fx => {{
    lines.push(`[node name="${{fx}}" type="Sprite2D" parent="VFXLayer"]`);
    lines.push('visible = false');
    lines.push('position = Vector2(256, 256)');
    lines.push(`texture = ExtResource("${{partExtId[fx]}}")`);
    lines.push("");
  }});

  lines.push('[node name="AnimationPlayer" type="AnimationPlayer" parent="."]');
  lines.push('libraries = {{');
  lines.push('"": SubResource("AnimationLibrary_c001")');
  lines.push('}}');
  lines.push('autoplay = "idle"');
  lines.push("");
  return lines.join("\\n");
}}

async function saveToGodotTscn() {{
  const tscnContent = buildGodotTscnString();
  const toast = document.getElementById("statusToast");
  try {{
    if (window.showSaveFilePicker) {{
      const handle = await window.showSaveFilePicker({{
        suggestedName: "c001_hac_kiem_tan_binh.tscn",
        types: [{{ description: "Godot 4 Scene (.tscn)", accept: {{ "text/plain": [".tscn"] }} }}],
      }});
      const writable = await handle.createWritable();
      await writable.write(tscnContent);
      await writable.close();
      toast.textContent = "✅ Đã lưu trực tiếp vào file c001_hac_kiem_tan_binh.tscn!";
      return;
    }}
  }} catch (err) {{
    if (err && err.name === "AbortError") return;
  }}
  const blob = new Blob([tscnContent], {{ type: "text/plain;charset=utf-8" }});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "c001_hac_kiem_tan_binh.tscn";
  a.click();
  URL.revokeObjectURL(url);
  toast.textContent = "✅ Đã xuất file c001_hac_kiem_tan_binh.tscn!";
}}

initUI();
requestAnimationFrame(renderLoop);
</script>
</body>
</html>
"""

html_paths = [
    "/Users/dochung/Desktop/card_g/assets/sticker_weapon_editor.html",
    os.path.join(STICKER_DIR, "sticker_weapon_editor.html"),
    os.path.join(W001_DIR, "w001_editor.html"),
]
for hp in html_paths:
    with open(hp, "w", encoding="utf-8") as f:
        f.write(html_content)
print("Wrote interactive HTML editors ->", html_paths)
print("ALL STICKMAN 4-TEAM + W001 WEAPON ASSETS, GODOT .TSCN & HTML EDITORS COMPLETED SUCCESSFULLY!")

