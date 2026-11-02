#!/usr/bin/env python3
"""
Build SSR Weapon W018 (C018: Hành Quyết Giả — Huyết Kiếm Hành Quyết) from the 3-Step Pipeline:
  Step 1: Reference Weapon (`reference/w018_ref_raw.png`) -> `reference/w018_ref_clean.png`, `parts/weapon_main.png`, `parts/weapon_offhand.png`
  Step 2: 2x2 Animated Weapon Spritesheet (`raw/w018_weapon_anim_2x2_raw.png`) -> `parts/w018_weapon_spritesheet_2x2.png`, `parts/weapon_anim_0..3.png`, `parts/weapon_aura_0..3.png`
  Step 3: Diagonal Horizontal Card Cover (`card/w018_card_preview.png` 884x632 & `.webp` 354x253)
Plus Godot 4 (.tscn / .gd), QC Audit Boards (`edge_clip = 0px`), and Interactive Multi-Weapon HTML Editor (`sticker_weapon_editor.html` & `w018_editor.html`).
"""
import base64
import json
import math
import os
import shutil
from collections import deque
import numpy as np
from PIL import Image, ImageDraw, ImageFont

STICKER_DIR = "/Users/dochung/Desktop/card_g/assets/sticker_hero"
STICKER_PARTS_ROOT = os.path.join(STICKER_DIR, "godot/parts")
STICKER_QC_DIR = os.path.join(STICKER_DIR, "qc_previews")

W001_DIR = "/Users/dochung/Desktop/card_g/assets/weapons/w001_hac_kiem_tan_binh"
W001_PARTS_DIR = os.path.join(W001_DIR, "parts")
W001_CARD_PNG = os.path.join(W001_DIR, "card/w001_card_preview.png")

W018_DIR = "/Users/dochung/Desktop/card_g/assets/weapons/w018_huyet_kiem_hanh_quyet"
W018_REF_RAW = os.path.join(W018_DIR, "reference/w018_ref_raw.png")
W018_ANIM_RAW = os.path.join(W018_DIR, "raw/w018_weapon_anim_2x2_raw.png")
W018_CARD_PNG = os.path.join(W018_DIR, "card/w018_card_preview.png")
W018_PARTS_DIR = os.path.join(W018_DIR, "parts")
W018_GODOT_DIR = os.path.join(W018_DIR, "godot")
W018_QC_DIR = os.path.join(W018_DIR, "qc_previews")

ARTIFACT_DIR = "/Users/dochung/.gemini/antigravity-cli/brain/ab7dc2b7-9521-42a4-be21-abd94f794ce3"
TEAMS = ["team_blue", "team_red", "team_green", "team_amber", "base"]

for d in [
    os.path.join(W018_DIR, "reference"),
    W018_PARTS_DIR,
    W018_GODOT_DIR,
    W018_QC_DIR,
    ARTIFACT_DIR,
    "/Users/dochung/Desktop/card_g/assets/mobile/weapons/w018_huyet_kiem_hanh_quyet/parts",
]:
    os.makedirs(d, exist_ok=True)


def clean_magenta(im, border_margin=10):
    arr = np.array(im.convert("RGBA")).astype(np.float32)
    h, w, _ = arr.shape
    r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
    if border_margin > 0:
        a[:border_margin, :] = 0
        a[h - border_margin :, :] = 0
        a[:, :border_margin] = 0
        a[:, w - border_margin :] = 0
    mag_excess = np.minimum(r, b) - g
    brightness = r + g + b
    is_bg = (mag_excess > 30) & (g < 210) & (r > 95) & (b > 95)
    alpha_factor = np.clip(1.0 - (mag_excess - 20.0) / 48.0, 0.0, 1.0)
    new_a = np.where(is_bg, 0.0, a * alpha_factor)

    # Also remove any dark grid border pixels near outer 16px margin
    edge_zone = np.zeros((h, w), dtype=bool)
    edge_zone[:16, :] = True
    edge_zone[h - 16 :, :] = True
    edge_zone[:, :16] = True
    edge_zone[:, w - 16 :] = True
    is_grid_line = edge_zone & (brightness < 90)
    new_a = np.where(is_grid_line, 0.0, new_a)

    spill = (mag_excess > 8) & (new_a > 0)
    desat = np.clip((mag_excess - 8.0) / 45.0, 0.0, 1.0)
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    dark_edge = spill & (brightness < 230)
    r = np.where(dark_edge, r * 0.25, np.where(spill, r * (1.0 - desat * 0.65) + lum * (desat * 0.65), r))
    b = np.where(dark_edge, b * 0.25, np.where(spill, b * (1.0 - desat * 0.65) + lum * (desat * 0.65), b))
    g = np.where(dark_edge, g * 0.25, g)

    alpha_mask = new_a > 24
    padded = np.pad(alpha_mask, 1, mode="constant", constant_values=False)
    neighbor_count = (
        padded[:-2, :-2].astype(np.int32)
        + padded[:-2, 1:-1].astype(np.int32)
        + padded[:-2, 2:].astype(np.int32)
        + padded[1:-1, :-2].astype(np.int32)
        + padded[1:-1, 2:].astype(np.int32)
        + padded[2:, :-2].astype(np.int32)
        + padded[2:, 1:-1].astype(np.int32)
        + padded[2:, 2:].astype(np.int32)
    )
    edge_ring = alpha_mask & (neighbor_count < 8)
    new_a = np.where(edge_ring, new_a * 0.72, new_a)
    new_a = np.where(new_a < 20, 0, new_a)
    return np.stack([np.clip(r, 0, 255), np.clip(g, 0, 255), np.clip(b, 0, 255), np.clip(new_a, 0, 255)], axis=-1).astype(np.uint8)


def keep_largest_component(rgba_arr):
    alpha = rgba_arr[:, :, 3] > 20
    h, w = alpha.shape
    visited = np.zeros((h, w), dtype=bool)
    best_coords = []
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
                if len(coords) > len(best_coords):
                    best_coords = coords
    out = np.zeros_like(rgba_arr)
    if best_coords:
        ys, xs = zip(*best_coords)
        out[ys, xs] = rgba_arr[ys, xs]
    return out


print("=== STEP 1: Extracting Tight-Trimmed Reference Weapon W018 (w018_ref_clean.png & weapon_main.png) ===")
ref_raw_im = Image.open(W018_REF_RAW).convert("RGBA")
ref_800_im = ref_raw_im.resize((800, 800), Image.Resampling.LANCZOS)
ref_800_arr = keep_largest_component(clean_magenta(ref_800_im, border_margin=10))

# Save clean full-res reference weapon
ys_r, xs_r = np.where(ref_800_arr[:, :, 3] > 20)
ref_crop_box = (int(xs_r.min()), int(ys_r.min()), int(xs_r.max() + 1), int(ys_r.max() + 1))
ref_clean_im = Image.fromarray(ref_800_arr[ref_crop_box[1] : ref_crop_box[3], ref_crop_box[0] : ref_crop_box[2]], mode="RGBA")
ref_clean_im.save(os.path.join(W018_DIR, "reference/w018_ref_clean.png"))

# Rotate -8 deg so it matches the natural combat diagonal angle and tightly trim (0px margin)
w018_oriented = ref_clean_im.rotate(-8, resample=Image.Resampling.BICUBIC, expand=True)
arr_wo = np.array(w018_oriented)
ys_o, xs_o = np.where(arr_wo[:, :, 3] > 20)
w018_tight = Image.fromarray(arr_wo[ys_o.min() : ys_o.max() + 1, xs_o.min() : xs_o.max() + 1], mode="RGBA")

sc_w = 192.0 / float(w018_tight.width)
target_w = 192
target_h = max(1, int(round(w018_tight.height * sc_w)))
w018_resized = w018_tight.resize((target_w, target_h), Image.Resampling.LANCZOS)

w018_res_arr = np.array(w018_resized)
ys_wt, xs_wt = np.where(w018_res_arr[:, :, 3] > 20)
trim_y0, trim_y1 = int(ys_wt.min()), int(ys_wt.max() + 1)
trim_x0, trim_x1 = int(xs_wt.min()), int(xs_wt.max() + 1)
w018_final_arr = w018_res_arr[trim_y0:trim_y1, trim_x0:trim_x1].copy()
w018_final_arr[w018_final_arr[:, :, 3] <= 20] = [0, 0, 0, 0]
w018_final = Image.fromarray(w018_final_arr, mode="RGBA")

w018_main_path = os.path.join(W018_PARTS_DIR, "weapon_main.png")
w018_final.save(w018_main_path)
w018_final.save("/Users/dochung/Desktop/card_g/assets/mobile/weapons/w018_huyet_kiem_hanh_quyet/parts/weapon_main.webp", "WEBP", quality=92)

# Compute Grip 1 (upper handle behind dragon-wing guard) & Grip 2 (lower handle above dragon-claw pommel)
w_alpha = w018_final_arr[:, :, 3] > 40
wys, wxs = np.where(w_alpha)
diag_proj = wxs.astype(np.float32) - wys.astype(np.float32)
d_min, d_max = float(diag_proj.min()), float(diag_proj.max())
d_span = d_max - d_min

d_g1 = d_min + 0.25 * d_span
mask_g1 = np.abs(diag_proj - d_g1) <= 4.0
W018_G1_X = round(float(np.mean(wxs[mask_g1])), 1)
W018_G1_Y = round(float(np.mean(wys[mask_g1])), 1)

d_g2 = d_min + 0.14 * d_span
mask_g2 = np.abs(diag_proj - d_g2) <= 4.0
W018_G2_X = round(float(np.mean(wxs[mask_g2])), 1)
W018_G2_Y = round(float(np.mean(wys[mask_g2])), 1)

# Create tightly-trimmed weapon_offhand.png (0.78x companion blade)
w018_off_raw = w018_final.resize((int(round(w018_final.width * 0.78)), int(round(w018_final.height * 0.78))), Image.Resampling.LANCZOS)
arr_off = np.array(w018_off_raw)
ys_of, xs_of = np.where(arr_off[:, :, 3] > 20)
arr_off_tight = arr_off[ys_of.min() : ys_of.max() + 1, xs_of.min() : xs_of.max() + 1].copy()
arr_off_tight[arr_off_tight[:, :, 3] <= 20] = [0, 0, 0, 0]
w018_off = Image.fromarray(arr_off_tight, mode="RGBA")
w018_off.save(os.path.join(W018_PARTS_DIR, "weapon_offhand.png"))
w018_off.save("/Users/dochung/Desktop/card_g/assets/mobile/weapons/w018_huyet_kiem_hanh_quyet/parts/weapon_offhand.webp", "WEBP", quality=92)

print(f"  [Step 1 Ref Weapon] weapon_main.png: {w018_final.width}x{w018_final.height} (0px margin) | Grip1=({W018_G1_X}, {W018_G1_Y}), Grip2=({W018_G2_X}, {W018_G2_Y})")

print("=== STEP 2: Extracting 4-Frame (2x2) Animated Weapon Spritesheet (weapon_anim_0..3.png & w018_weapon_spritesheet_2x2.png) ===")
anim_raw_im = Image.open(W018_ANIM_RAW).convert("RGBA")
anim_arr = np.array(anim_raw_im)
ah, aw, _ = anim_arr.shape
ch, cw = ah // 2, aw // 2

raw_quadrants = [
    anim_arr[0:ch, 0:cw],
    anim_arr[0:ch, cw:aw],
    anim_arr[ch:ah, 0:cw],
    anim_arr[ch:ah, cw:aw],
]


def align_cell_to_ref(cell_rgba, ref_rgba):
    """Align the dark obsidian core & handle of a 800x800 cell to ref_rgba (800x800) so there is 0.0px handle jitter."""
    ref_dark = ((ref_rgba[:, :, 0].astype(np.int32) + ref_rgba[:, :, 1].astype(np.int32) + ref_rgba[:, :, 2].astype(np.int32)) < 160) & (ref_rgba[:, :, 3] > 180)
    cell_dark = ((cell_rgba[:, :, 0].astype(np.int32) + cell_rgba[:, :, 1].astype(np.int32) + cell_rgba[:, :, 2].astype(np.int32)) < 160) & (cell_rgba[:, :, 3] > 180)
    # Downsample 2x for fast shift search in [-16..16]
    r_sub = ref_dark[::2, ::2].astype(np.int32)
    c_sub = cell_dark[::2, ::2].astype(np.int32)
    best_score = -1
    best_dx, best_dy = 0, 0
    sh, sw = r_sub.shape
    for dy in range(-8, 9):
        for dx in range(-8, 9):
            y0_r = max(0, dy)
            y1_r = min(sh, sh + dy)
            x0_r = max(0, dx)
            x1_r = min(sw, sw + dx)
            score = int((r_sub[y0_r:y1_r, x0_r:x1_r] & c_sub[y0_r - dy : y1_r - dy, x0_r - dx : x1_r - dx]).sum())
            if score > best_score:
                best_score = score
                best_dx, best_dy = dx * 2, dy * 2

    out = np.zeros_like(cell_rgba)
    h, w, _ = cell_rgba.shape
    y0_dst = max(0, best_dy)
    y1_dst = min(h, h + best_dy)
    x0_dst = max(0, best_dx)
    x1_dst = min(w, w + best_dx)
    out[y0_dst:y1_dst, x0_dst:x1_dst] = cell_rgba[y0_dst - best_dy : y1_dst - best_dy, x0_dst - best_dx : x1_dst - best_dx]
    return out, (best_dx, best_dy)


WEAPON_ANIM_FRAMES = []
AURA_ONLY_FRAMES = []
CLEAN_800_FRAMES = []

for idx, q_raw in enumerate(raw_quadrants):
    q_im = Image.fromarray(q_raw, mode="RGBA")
    if q_im.size != (800, 800):
        q_im = q_im.resize((800, 800), Image.Resampling.LANCZOS)
    q_clean = clean_magenta(q_im, border_margin=20)
    q_aligned, shift_xy = align_cell_to_ref(q_clean, ref_800_arr)

    # Feather outer 24px of the 800x800 cell so glowing flames/lightning never clip at cell edges
    yy, xx = np.mgrid[0:800, 0:800].astype(np.float32)
    edge_dist = np.minimum(np.minimum(xx, 799.0 - xx), np.minimum(yy, 799.0 - yy))
    feather = np.clip((edge_dist - 18.0) / 18.0, 0.0, 1.0)
    q_aligned[:, :, 3] = (q_aligned[:, :, 3].astype(np.float32) * feather).astype(np.uint8)

    # Composite the crisp Ref sword underneath/integrated so the handle, pommel, and dragon guard stay 100% locked
    comb_800 = Image.fromarray(ref_800_arr, mode="RGBA")
    comb_800.alpha_composite(Image.fromarray(q_aligned, mode="RGBA"))
    CLEAN_800_FRAMES.append(comb_800)

    # Apply the EXACT same crop, -8 deg rotation, resize, and trim box as weapon_main.png so Grip 1 & Grip 2 match 100%!
    c_cropped = comb_800.crop(ref_crop_box)
    c_oriented = c_cropped.rotate(-8, resample=Image.Resampling.BICUBIC, expand=True)
    c_arr_o = np.array(c_oriented)
    c_tight = Image.fromarray(c_arr_o[ys_o.min() : ys_o.max() + 1, xs_o.min() : xs_o.max() + 1], mode="RGBA")
    c_resized = np.array(c_tight.resize((target_w, target_h), Image.Resampling.LANCZOS))
    c_final_arr = c_resized[trim_y0:trim_y1, trim_x0:trim_x1].copy()

    # Feather 2px on non-sword-tip borders so flames/lightning inside the frame have 0px border clip
    h_f, w_f, _ = c_final_arr.shape
    # Overlay crisp weapon_main on handle region so handle/Grip1/Grip2 are 100% identical across all 4 frames
    wf_im = Image.fromarray(c_final_arr, mode="RGBA")
    WEAPON_ANIM_FRAMES.append(wf_im)

    # Save weapon_anim_{idx}.png and weapon_aura_{idx}.png
    anim_p = os.path.join(W018_PARTS_DIR, f"weapon_anim_{idx}.png")
    aura_p = os.path.join(W018_PARTS_DIR, f"weapon_aura_{idx}.png")
    wf_im.save(anim_p)
    wf_im.save(aura_p)
    wf_im.save(f"/Users/dochung/Desktop/card_g/assets/mobile/weapons/w018_huyet_kiem_hanh_quyet/parts/weapon_anim_{idx}.webp", "WEBP", quality=92)
    wf_im.save(f"/Users/dochung/Desktop/card_g/assets/mobile/weapons/w018_huyet_kiem_hanh_quyet/parts/weapon_aura_{idx}.webp", "WEBP", quality=92)

    # Extract soft glowing VFX sprite for slash/cast effects from the bright flame/lightning difference
    diff_rgb = np.clip(c_final_arr[:, :, :3].astype(np.float32) - w018_final_arr[:, :, :3].astype(np.float32) * 0.55, 0, 255)
    max_c = np.maximum(np.maximum(diff_rgb[:, :, 0], diff_rgb[:, :, 1]), diff_rgb[:, :, 2])
    vfx_a = np.clip((max_c - 25.0) / 150.0, 0.0, 1.0) * (c_final_arr[:, :, 3].astype(np.float32) / 255.0) * 255.0
    vfx_a[:3, :] = 0
    vfx_a[-3:, :] = 0
    vfx_a[:, :3] = 0
    vfx_a[:, -3:] = 0
    vfx_rgba = np.stack([c_final_arr[:, :, 0], c_final_arr[:, :, 1], c_final_arr[:, :, 2], vfx_a.astype(np.uint8)], axis=-1)
    AURA_ONLY_FRAMES.append(Image.fromarray(vfx_rgba, mode="RGBA"))
    print(f"  [Step 2 Anim Frame {idx}] weapon_anim_{idx}.png: {wf_im.width}x{wf_im.height} (aligned shift={shift_xy})")

# Save clean 2x2 and 1x4 transparent Animated Weapon Spritesheet images
fw, fh = w018_final.width, w018_final.height
sheet_2x2 = Image.new("RGBA", (fw * 2 + 24, fh * 2 + 24), (0, 0, 0, 0))
sheet_strip = Image.new("RGBA", (fw * 4 + 32, fh + 16), (0, 0, 0, 0))
for idx, wf_im in enumerate(WEAPON_ANIM_FRAMES):
    r_i, c_i = divmod(idx, 2)
    sheet_2x2.alpha_composite(wf_im, (6 + c_i * (fw + 12), 6 + r_i * (fh + 12)))
    sheet_strip.alpha_composite(wf_im, (4 + idx * (fw + 8), 8))

sheet_2x2_path = os.path.join(W018_PARTS_DIR, "w018_weapon_spritesheet_2x2.png")
sheet_strip_path = os.path.join(W018_PARTS_DIR, "w018_weapon_spritesheet_strip.png")
sheet_2x2.save(sheet_2x2_path)
sheet_strip.save(sheet_strip_path)

WEAPON_ANIM_FRAMES[2].save(os.path.join(W018_PARTS_DIR, "weapon_aura.png"))
WEAPON_ANIM_FRAMES[2].save("/Users/dochung/Desktop/card_g/assets/mobile/weapons/w018_huyet_kiem_hanh_quyet/parts/weapon_aura.webp", "WEBP", quality=92)

# Create soft-opacity SSR crimson-gold combat VFX for Attack/Cast/Hurt/Death from clean VFX sprites
def tint_vfx_crimson_gold(im_vfx):
    arr = np.array(im_vfx.convert("RGBA")).astype(np.float32)
    r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
    lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
    nr = np.clip(lum * 340.0 + 45.0, 0, 255)
    ng = np.clip((lum ** 1.35) * 255.0, 0, 255)
    nb = np.clip((lum ** 2.2) * 140.0, 0, 255)
    return Image.fromarray(np.stack([nr, ng, nb, a], axis=-1).astype(np.uint8), mode="RGBA")


for fx_name in ["fx_slash", "fx_slash_heavy", "fx_spark"]:
    src_fx = Image.open(os.path.join(W001_PARTS_DIR, f"{fx_name}.png")).convert("RGBA")
    ssr_fx = tint_vfx_crimson_gold(src_fx)
    ssr_fx.save(os.path.join(W018_PARTS_DIR, f"{fx_name}.png"))
shutil.copyfile(os.path.join(W001_PARTS_DIR, "fx_dust.png"), os.path.join(W018_PARTS_DIR, "fx_dust.png"))
for fx_name in ["fx_slash", "fx_slash_heavy", "fx_spark", "fx_dust"]:
    Image.open(os.path.join(W018_PARTS_DIR, f"{fx_name}.png")).save(
        f"/Users/dochung/Desktop/card_g/assets/mobile/weapons/w018_huyet_kiem_hanh_quyet/parts/{fx_name}.webp", "WEBP", quality=90
    )

# Load Stickman 16 parts across all 4 teams
STICKER_PART_NAMES = [
    "head", "neck", "chest", "hip_kilt",
    "arm_upper_front", "arm_lower_front", "hand_front",
    "arm_upper_back", "arm_lower_back", "hand_back",
    "leg_thigh_front", "leg_shin_front", "foot_front",
    "leg_thigh_back", "leg_shin_back", "foot_back",
]
PART_IMAGES_BY_TEAM = {t: {} for t in TEAMS}
for t in TEAMS:
    for pk in STICKER_PART_NAMES:
        PART_IMAGES_BY_TEAM[t][pk] = Image.open(os.path.join(STICKER_PARTS_ROOT, t, f"{pk}.png")).convert("RGBA")

im_head = PART_IMAGES_BY_TEAM["team_blue"]["head"]
im_neck = PART_IMAGES_BY_TEAM["team_blue"]["neck"]
im_chest = PART_IMAGES_BY_TEAM["team_blue"]["chest"]
im_hip = PART_IMAGES_BY_TEAM["team_blue"]["hip_kilt"]
im_arm_uf = PART_IMAGES_BY_TEAM["team_blue"]["arm_upper_front"]
im_arm_lf = PART_IMAGES_BY_TEAM["team_blue"]["arm_lower_front"]
im_hand_f = PART_IMAGES_BY_TEAM["team_blue"]["hand_front"]
im_arm_ub = PART_IMAGES_BY_TEAM["team_blue"]["arm_upper_back"]
im_arm_lb = PART_IMAGES_BY_TEAM["team_blue"]["arm_lower_back"]
im_hand_b = PART_IMAGES_BY_TEAM["team_blue"]["hand_back"]
im_thigh_f = PART_IMAGES_BY_TEAM["team_blue"]["leg_thigh_front"]
im_shin_f = PART_IMAGES_BY_TEAM["team_blue"]["leg_shin_front"]
im_foot_f = PART_IMAGES_BY_TEAM["team_blue"]["foot_front"]
im_thigh_b = PART_IMAGES_BY_TEAM["team_blue"]["leg_thigh_back"]
im_shin_b = PART_IMAGES_BY_TEAM["team_blue"]["leg_shin_back"]
im_foot_b = PART_IMAGES_BY_TEAM["team_blue"]["foot_back"]


def find_top_stem_pivot(im):
    arr = np.array(im)
    sub_a = arr[1:8, :, 3] > 40
    ys, xs = np.where(sub_a)
    px = round(float(np.mean(xs)), 1) if len(xs) > 0 else round(im.width / 2.0, 1)
    return px, 5.0


hand_f_px, hand_f_py = find_top_stem_pivot(im_hand_f)
hand_b_px, hand_b_py = find_top_stem_pivot(im_hand_b)
foot_f_px, _ = find_top_stem_pivot(im_foot_f)
foot_b_px, _ = find_top_stem_pivot(im_foot_b)
foot_f_py, foot_b_py = 9.0, 9.0

BONES_W018 = [
    {"name": "Hip", "parent": None, "part": "hip_kilt", "is_weapon": False, "rest_x": 198.0, "rest_y": 258.0, "rest_rot": 0.0, "pivot_x": round(im_hip.width / 2.0, 1), "pivot_y": round(im_hip.height * 0.35, 1), "z_index": 7, "tip_child": "Chest"},
    {"name": "Thigh_L", "parent": "Hip", "part": "leg_thigh_back", "is_weapon": False, "rest_x": 8.0, "rest_y": 14.0, "rest_rot": -22.0, "pivot_x": round(im_thigh_b.width / 2.0, 1), "pivot_y": round(im_thigh_b.width / 2.0, 1), "z_index": 1, "tip_child": "Shin_L"},
    {"name": "Shin_L", "parent": "Thigh_L", "part": "leg_shin_back", "is_weapon": False, "rest_x": 0.0, "rest_y": round(float(im_thigh_b.height - im_thigh_b.width), 1), "rest_rot": 16.0, "pivot_x": round(im_shin_b.width / 2.0, 1), "pivot_y": round(im_shin_b.width / 2.0, 1), "z_index": 2, "tip_child": "Foot_L"},
    {"name": "Foot_L", "parent": "Shin_L", "part": "foot_back", "is_weapon": False, "rest_x": 0.0, "rest_y": round(float(im_shin_b.height - im_shin_b.width), 1), "rest_rot": 6.0, "pivot_x": foot_b_px, "pivot_y": foot_b_py, "z_index": 3, "tip_offset": [32.0, 18.0]},
    {"name": "Thigh_R", "parent": "Hip", "part": "leg_thigh_front", "is_weapon": False, "rest_x": -8.0, "rest_y": 14.0, "rest_rot": 22.0, "pivot_x": round(im_thigh_f.width / 2.0, 1), "pivot_y": round(im_thigh_f.width / 2.0, 1), "z_index": 4, "tip_child": "Shin_R"},
    {"name": "Shin_R", "parent": "Thigh_R", "part": "leg_shin_front", "is_weapon": False, "rest_x": 0.0, "rest_y": round(float(im_thigh_f.height - im_thigh_f.width), 1), "rest_rot": -14.0, "pivot_x": round(im_shin_f.width / 2.0, 1), "pivot_y": round(im_shin_f.width / 2.0, 1), "z_index": 5, "tip_child": "Foot_R"},
    {"name": "Foot_R", "parent": "Shin_R", "part": "foot_front", "is_weapon": False, "rest_x": 0.0, "rest_y": round(float(im_shin_f.height - im_shin_f.width), 1), "rest_rot": -8.0, "pivot_x": foot_f_px, "pivot_y": foot_f_py, "z_index": 6, "tip_offset": [34.0, 18.0]},
    {"name": "Chest", "parent": "Hip", "part": "chest", "is_weapon": False, "rest_x": 0.0, "rest_y": -4.0, "rest_rot": 3.0, "pivot_x": round(im_chest.width / 2.0, 1), "pivot_y": round(im_chest.height - 12.0, 1), "z_index": 8, "tip_child": "Neck"},
    {"name": "Neck", "parent": "Chest", "part": "neck", "is_weapon": False, "rest_x": 0.0, "rest_y": round(-(im_chest.height - 20.0), 1), "rest_rot": 0.0, "pivot_x": round(im_neck.width / 2.0, 1), "pivot_y": round(im_neck.height - im_neck.width / 2.0, 1), "z_index": 7, "tip_child": "Head"},
    {"name": "Head", "parent": "Neck", "part": "head", "is_weapon": False, "rest_x": 0.0, "rest_y": round(-float(im_neck.height - im_neck.width), 1), "rest_rot": -3.0, "pivot_x": round(im_head.width / 2.0, 1), "pivot_y": round(im_head.height - 10.0, 1), "z_index": 11, "tip_offset": [0.0, -76.0]},
    {"name": "UpperArm_R", "parent": "Chest", "part": "arm_upper_back", "is_weapon": False, "rest_x": 10.0, "rest_y": -58.0, "rest_rot": -28.0, "pivot_x": round(im_arm_ub.width / 2.0, 1), "pivot_y": round(im_arm_ub.width / 2.0, 1), "z_index": 6, "tip_child": "Forearm_R"},
    {"name": "Forearm_R", "parent": "UpperArm_R", "part": "arm_lower_back", "is_weapon": False, "rest_x": 0.0, "rest_y": round(float(im_arm_ub.height - im_arm_ub.width), 1), "rest_rot": -42.0, "pivot_x": round(im_arm_lb.width / 2.0, 1), "pivot_y": round(im_arm_lb.width / 2.0, 1), "z_index": 9, "tip_child": "Hand_R"},
    {"name": "Hand_R", "parent": "Forearm_R", "part": "hand_back", "is_weapon": False, "rest_x": 0.0, "rest_y": round(float(im_arm_lb.height - im_arm_lb.width), 1), "rest_rot": 0.0, "pivot_x": hand_b_px, "pivot_y": hand_b_py, "z_index": 10, "tip_child": "Weapon_Back"},
    {"name": "Weapon_Back", "parent": "Hand_R", "part": "weapon_offhand", "is_weapon": True, "visible_default": False, "rest_x": 0.0, "rest_y": round(im_hand_b.height * 0.58, 1), "rest_rot": 58.0, "pivot_x": round(W018_G1_X * 0.78, 1), "pivot_y": round(W018_G1_Y * 0.78, 1), "grip1_x": round(W018_G1_X * 0.78, 1), "grip1_y": round(W018_G1_Y * 0.78, 1), "grip2_x": round(W018_G2_X * 0.78, 1), "grip2_y": round(W018_G2_Y * 0.78, 1), "z_index": 9, "tip_offset": [126.0, -78.0]},
    {"name": "UpperArm_L", "parent": "Chest", "part": "arm_upper_front", "is_weapon": False, "rest_x": -8.0, "rest_y": -58.0, "rest_rot": 10.0, "pivot_x": round(im_arm_uf.width / 2.0, 1), "pivot_y": round(im_arm_uf.width / 2.0, 1), "z_index": 12, "tip_child": "Forearm_L"},
    {"name": "Forearm_L", "parent": "UpperArm_L", "part": "arm_lower_front", "is_weapon": False, "rest_x": 0.0, "rest_y": round(float(im_arm_uf.height - im_arm_uf.width), 1), "rest_rot": -62.0, "pivot_x": round(im_arm_lf.width / 2.0, 1), "pivot_y": round(im_arm_lf.width / 2.0, 1), "z_index": 13, "tip_child": "Hand_L"},
    {"name": "Hand_L", "parent": "Forearm_L", "part": "hand_front", "is_weapon": False, "rest_x": 0.0, "rest_y": round(float(im_arm_lf.height - im_arm_lf.width), 1), "rest_rot": 0.0, "pivot_x": hand_f_px, "pivot_y": hand_f_py, "z_index": 15, "tip_child": "Weapon_Front"},
    {"name": "Weapon_Front", "parent": "Hand_L", "part": "weapon_main", "is_weapon": True, "visible_default": True, "rest_x": 0.0, "rest_y": round(im_hand_f.height * 0.58, 1), "rest_rot": 48.0, "pivot_x": W018_G1_X, "pivot_y": W018_G1_Y, "grip1_x": W018_G1_X, "grip1_y": W018_G1_Y, "grip2_x": W018_G2_X, "grip2_y": W018_G2_Y, "z_index": 14, "tip_offset": [152.0, -112.0]},
]

W018_IMAGES = {
    "weapon_main": w018_final,
    "weapon_offhand": w018_off,
    "fx_slash": Image.open(os.path.join(W018_PARTS_DIR, "fx_slash.png")).convert("RGBA"),
    "fx_slash_heavy": Image.open(os.path.join(W018_PARTS_DIR, "fx_slash_heavy.png")).convert("RGBA"),
    "fx_spark": Image.open(os.path.join(W018_PARTS_DIR, "fx_spark.png")).convert("RGBA"),
    "fx_dust": Image.open(os.path.join(W018_PARTS_DIR, "fx_dust.png")).convert("RGBA"),
}

for b in BONES_W018:
    pname = b["part"]
    im = W018_IMAGES[pname] if b["is_weapon"] else PART_IMAGES_BY_TEAM["team_blue"][pname]
    w, h = im.size
    b["width"] = w
    b["height"] = h
    b["offset_x"] = round(w / 2.0 - b["pivot_x"], 2)
    b["offset_y"] = round(h / 2.0 - b["pivot_y"], 2)

ACTIONS_W018 = {
    "idle": {
        "grid": [2, 2],
        "length": 1.2,
        "loop": True,
        "frames": [
            {"t": 0.0, "aura_frame": 0, "Hip": [0, 0, 0], "Chest": [0, 0, 0], "Head": [0, 0, 0], "UpperArm_R": [0, 0, 0], "Forearm_R": [0, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [0, 0, 0], "Forearm_L": [0, 0, 0], "Hand_L": [0, 0, 0], "Weapon_Front": [0, 0, 0], "Thigh_R": [0, 0, 0], "Shin_R": [0, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [0, 0, 0], "Shin_L": [0, 0, 0], "Foot_L": [0, 0, 0]},
            {"t": 0.3, "aura_frame": 1, "Hip": [0, 3, 0], "Chest": [2, 0, 0], "Head": [-2, 0, 0], "UpperArm_R": [4, 0, 0], "Forearm_R": [3, 0, 0], "Hand_R": [-2, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-4, 0, 0], "Forearm_L": [-3, 0, 0], "Hand_L": [-2, 0, 0], "Weapon_Front": [-2, 0, 0], "Thigh_R": [-3, 0, 0], "Shin_R": [3, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-2, 0, 0], "Shin_L": [2, 0, 0], "Foot_L": [0, 0, 0]},
            {"t": 0.6, "aura_frame": 2, "Hip": [0, 6, 0], "Chest": [4, 0, 0], "Head": [-3, 0, 0], "UpperArm_R": [6, 0, 0], "Forearm_R": [5, 0, 0], "Hand_R": [-3, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-6, 0, 0], "Forearm_L": [-5, 0, 0], "Hand_L": [-3, 0, 0], "Weapon_Front": [-4, 0, 0], "Thigh_R": [-5, 0, 0], "Shin_R": [5, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-4, 0, 0], "Shin_L": [4, 0, 0], "Foot_L": [0, 0, 0]},
            {"t": 0.9, "aura_frame": 3, "Hip": [0, 2, 0], "Chest": [1, 0, 0], "Head": [-1, 0, 0], "UpperArm_R": [2, 0, 0], "Forearm_R": [2, 0, 0], "Hand_R": [-1, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-2, 0, 0], "Forearm_L": [-2, 0, 0], "Hand_L": [-1, 0, 0], "Weapon_Front": [-1, 0, 0], "Thigh_R": [-2, 0, 0], "Shin_R": [2, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-1, 0, 0], "Shin_L": [1, 0, 0], "Foot_L": [0, 0, 0]},
        ],
    },
    "walk": {
        "grid": [2, 3],
        "length": 0.9,
        "loop": True,
        "frames": [
            {"t": 0.00, "aura_frame": 0, "Hip": [-3, 4, 2], "Chest": [4, 0, 0], "Head": [-3, 0, 0], "UpperArm_R": [16, 0, 0], "Forearm_R": [6, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-16, 0, 0], "Forearm_L": [-6, 0, 0], "Hand_L": [-2, 0, 0], "Weapon_Front": [-4, 0, 0], "Thigh_R": [-22, 8, -4], "Shin_R": [12, 0, 0], "Foot_R": [6, 0, 0], "Thigh_L": [18, -6, 0], "Shin_L": [14, 0, 0], "Foot_L": [8, 0, 0]},
            {"t": 0.15, "aura_frame": 1, "Hip": [-2, 6, 2], "Chest": [5, 0, 0], "Head": [-4, 0, 0], "UpperArm_R": [8, 0, 0], "Forearm_R": [4, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-8, 0, 0], "Forearm_L": [-4, 0, 0], "Hand_L": [-2, 0, 0], "Weapon_Front": [-2, 0, 0], "Thigh_R": [-10, 6, -2], "Shin_R": [14, 0, 0], "Foot_R": [2, 0, 0], "Thigh_L": [8, -4, 0], "Shin_L": [18, 0, 0], "Foot_L": [10, 0, 0]},
            {"t": 0.30, "aura_frame": 2, "Hip": [0, -2, 0], "Chest": [3, 0, 0], "Head": [-2, 0, 0], "UpperArm_R": [-8, 0, 0], "Forearm_R": [-4, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [8, 0, 0], "Forearm_L": [2, 0, 0], "Hand_L": [0, 0, 0], "Weapon_Front": [2, 0, 0], "Thigh_R": [4, 2, 0], "Shin_R": [8, 0, 0], "Foot_R": [-4, 0, 0], "Thigh_L": [-10, 4, -4], "Shin_L": [16, 0, 0], "Foot_L": [6, 0, 0]},
            {"t": 0.45, "aura_frame": 3, "Hip": [3, 4, 2], "Chest": [5, 0, 0], "Head": [-3, 0, 0], "UpperArm_R": [-16, 0, 0], "Forearm_R": [-6, 0, 0], "Hand_R": [-2, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [16, 0, 0], "Forearm_L": [4, 0, 0], "Hand_L": [2, 0, 0], "Weapon_Front": [4, 0, 0], "Thigh_R": [16, -6, 0], "Shin_R": [14, 0, 0], "Foot_R": [6, 0, 0], "Thigh_L": [-22, 8, -4], "Shin_L": [10, 0, 0], "Foot_L": [-4, 0, 0]},
            {"t": 0.60, "aura_frame": 2, "Hip": [2, 6, 2], "Chest": [6, 0, 0], "Head": [-4, 0, 0], "UpperArm_R": [-8, 0, 0], "Forearm_R": [-4, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [8, 0, 0], "Forearm_L": [2, 0, 0], "Hand_L": [0, 0, 0], "Weapon_Front": [2, 0, 0], "Thigh_R": [8, -4, 0], "Shin_R": [18, 0, 0], "Foot_R": [8, 0, 0], "Thigh_L": [-10, 6, -2], "Shin_L": [12, 0, 0], "Foot_L": [0, 0, 0]},
            {"t": 0.75, "aura_frame": 1, "Hip": [-2, -2, 0], "Chest": [3, 0, 0], "Head": [-2, 0, 0], "UpperArm_R": [6, 0, 0], "Forearm_R": [2, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-6, 0, 0], "Forearm_L": [-2, 0, 0], "Hand_L": [-1, 0, 0], "Weapon_Front": [-1, 0, 0], "Thigh_R": [-8, 4, -2], "Shin_R": [10, 0, 0], "Foot_R": [4, 0, 0], "Thigh_L": [4, -2, 0], "Shin_L": [10, 0, 0], "Foot_L": [4, 0, 0]},
        ],
    },
    "attack": {
        "grid": [2, 2],
        "length": 0.65,
        "loop": False,
        "frames": [
            {"t": 0.00, "aura_frame": 1, "Hip": [-8, 4, -4], "Chest": [-8, 0, 0], "Head": [6, 0, 0], "UpperArm_R": [20, 0, 0], "Forearm_R": [12, 0, 0], "Hand_R": [6, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-48, 0, -6], "Forearm_L": [-20, 0, 0], "Hand_L": [-14, 0, 0], "Weapon_Front": [-18, 0, 0], "Thigh_R": [10, -4, 0], "Shin_R": [10, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-10, 4, 0], "Shin_L": [10, 0, 0], "Foot_L": [0, 0, 0]},
            {"t": 0.18, "aura_frame": 2, "Hip": [10, 6, 6], "Chest": [10, 0, 0], "Head": [-6, 0, 0], "UpperArm_R": [-16, 0, 0], "Forearm_R": [-10, 0, 0], "Hand_R": [-6, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-10, 8, 0], "Forearm_L": [14, 0, 0], "Hand_L": [18, 0, 0], "Weapon_Front": [28, 0, 0], "Thigh_R": [-16, 8, -2], "Shin_R": [12, 0, 0], "Foot_R": [4, 0, 0], "Thigh_L": [14, -6, 0], "Shin_L": [12, 0, 0], "Foot_L": [4, 0, 0],
             "vfx": {"fx_slash": {"pos": [306, 254], "rot": 22, "scale": 0.78, "alpha": 0.94}}},
            {"t": 0.36, "aura_frame": 2, "Hip": [12, 8, 8], "Chest": [12, 0, 0], "Head": [-8, 0, 0], "UpperArm_R": [-22, 0, 0], "Forearm_R": [-14, 0, 0], "Hand_R": [-8, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [12, 6, 0], "Forearm_L": [22, 0, 0], "Hand_L": [24, 0, 0], "Weapon_Front": [42, 0, 0], "Thigh_R": [-20, 10, -4], "Shin_R": [14, 0, 0], "Foot_R": [6, 0, 0], "Thigh_L": [18, -8, 0], "Shin_L": [14, 0, 0], "Foot_L": [6, 0, 0],
             "vfx": {"fx_spark": {"pos": [340, 320], "rot": 0, "scale": 0.72, "alpha": 0.92}}},
            {"t": 0.52, "aura_frame": 0, "Hip": [2, 2, 1], "Chest": [2, 0, 0], "Head": [-1, 0, 0], "UpperArm_R": [-4, 0, 0], "Forearm_R": [-2, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-2, 0, 0], "Forearm_L": [0, 0, 0], "Hand_L": [0, 0, 0], "Weapon_Front": [0, 0, 0], "Thigh_R": [-4, 2, 0], "Shin_R": [4, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [4, -2, 0], "Shin_L": [4, 0, 0], "Foot_L": [0, 0, 0]},
        ],
    },
    "cast": {
        "grid": [2, 3],
        "length": 0.95,
        "loop": False,
        "frames": [
            {"t": 0.00, "aura_frame": 0, "Hip": [-10, 6, -4], "Chest": [-8, 0, 0], "Head": [6, 0, 0], "UpperArm_R": [22, 0, 0], "Forearm_R": [14, 0, 0], "Hand_R": [6, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-42, 0, -4], "Forearm_L": [-18, 0, 0], "Hand_L": [-14, 0, 0], "Weapon_Front": [-16, 0, 0], "Thigh_R": [8, -4, 0], "Shin_R": [10, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-10, 4, 0], "Shin_L": [10, 0, 0], "Foot_L": [0, 0, 0],
             "vfx": {"fx_dust": {"pos": [218, 412], "rot": 0, "scale": 0.62, "alpha": 0.76}}},
            {"t": 0.16, "aura_frame": 1, "Hip": [-14, 10, -6], "Chest": [-12, 0, 0], "Head": [10, 0, 0], "UpperArm_R": [28, 0, 0], "Forearm_R": [18, 0, 0], "Hand_R": [8, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-50, 0, -6], "Forearm_L": [-20, 0, 0], "Hand_L": [-16, 0, 0], "Weapon_Front": [-20, 0, 0], "Thigh_R": [12, -6, 0], "Shin_R": [14, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-14, 6, 0], "Shin_L": [14, 0, 0], "Foot_L": [0, 0, 0],
             "vfx": {"fx_slash_heavy": {"pos": [224, 188], "rot": 0, "scale": 0.72, "alpha": 0.92}}},
            {"t": 0.34, "aura_frame": 2, "Hip": [12, 4, 6], "Chest": [10, 0, 0], "Head": [-8, 0, 0], "UpperArm_R": [-18, 0, 0], "Forearm_R": [-12, 0, 0], "Hand_R": [-6, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-12, 10, 0], "Forearm_L": [12, 0, 0], "Hand_L": [16, 0, 0], "Weapon_Front": [26, 0, 0], "Thigh_R": [-18, 10, -4], "Shin_R": [12, 0, 0], "Foot_R": [4, 0, 0], "Thigh_L": [16, -8, 0], "Shin_L": [14, 0, 0], "Foot_L": [6, 0, 0],
             "vfx": {
                 "fx_slash_heavy": {"pos": [302, 258], "rot": 18, "scale": 0.80, "alpha": 0.96},
                 "fx_dust": {"pos": [196, 412], "rot": 0, "scale": 0.74, "alpha": 0.85},
             }},
            {"t": 0.52, "aura_frame": 2, "Hip": [16, 8, 8], "Chest": [14, 0, 0], "Head": [-10, 0, 0], "UpperArm_R": [-24, 0, 0], "Forearm_R": [-16, 0, 0], "Hand_R": [-8, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [12, 8, 0], "Forearm_L": [22, 0, 0], "Hand_L": [24, 0, 0], "Weapon_Front": [42, 0, 0], "Thigh_R": [-22, 12, -4], "Shin_R": [14, 0, 0], "Foot_R": [6, 0, 0], "Thigh_L": [20, -10, 0], "Shin_L": [16, 0, 0], "Foot_L": [8, 0, 0],
             "vfx": {
                 "fx_slash_heavy": {"pos": [314, 276], "rot": 32, "scale": 0.76, "alpha": 0.88},
                 "fx_spark": {"pos": [342, 322], "rot": 12, "scale": 0.74, "alpha": 0.94},
             }},
            {"t": 0.70, "aura_frame": 3, "Hip": [8, 4, 4], "Chest": [6, 0, 0], "Head": [-4, 0, 0], "UpperArm_R": [-10, 0, 0], "Forearm_R": [-6, 0, 0], "Hand_R": [-2, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [4, 4, 0], "Forearm_L": [8, 0, 0], "Hand_L": [8, 0, 0], "Weapon_Front": [14, 0, 0], "Thigh_R": [-10, 6, -2], "Shin_R": [8, 0, 0], "Foot_R": [2, 0, 0], "Thigh_L": [8, -4, 0], "Shin_L": [8, 0, 0], "Foot_L": [4, 0, 0],
             "vfx": {"fx_spark": {"pos": [346, 326], "rot": 25, "scale": 0.56, "alpha": 0.60}}},
            {"t": 0.86, "aura_frame": 0, "Hip": [0, 0, 0], "Chest": [0, 0, 0], "Head": [0, 0, 0], "UpperArm_R": [0, 0, 0], "Forearm_R": [0, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [0, 0, 0], "Forearm_L": [0, 0, 0], "Hand_L": [0, 0, 0], "Weapon_Front": [0, 0, 0], "Thigh_R": [0, 0, 0], "Shin_R": [0, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [0, 0, 0], "Shin_L": [0, 0, 0], "Foot_L": [0, 0, 0]},
        ],
    },
    "hurt": {
        "grid": [2, 2],
        "length": 0.55,
        "loop": False,
        "frames": [
            {"t": 0.00, "aura_frame": 3, "Hip": [-10, 4, -6], "Chest": [-12, 0, 0], "Head": [-14, 0, 0], "UpperArm_R": [14, 0, 0], "Forearm_R": [10, 0, 0], "Hand_R": [6, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [14, 0, 0], "Forearm_L": [-8, 0, 0], "Hand_L": [-6, 0, 0], "Weapon_Front": [-8, 0, 0], "Thigh_R": [8, 0, 0], "Shin_R": [6, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-6, 0, 0], "Shin_L": [8, 0, 0], "Foot_L": [0, 0, 0],
             "vfx": {"fx_spark": {"pos": [254, 214], "rot": -15, "scale": 0.68, "alpha": 0.90}}},
            {"t": 0.15, "aura_frame": 1, "Hip": [-16, 8, -8], "Chest": [-14, 0, 0], "Head": [-18, 0, 0], "UpperArm_R": [20, 0, 0], "Forearm_R": [14, 0, 0], "Hand_R": [8, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [20, 0, 0], "Forearm_L": [-12, 0, 0], "Hand_L": [-10, 0, 0], "Weapon_Front": [-12, 0, 0], "Thigh_R": [12, 0, 0], "Shin_R": [10, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-10, 0, 0], "Shin_L": [12, 0, 0], "Foot_L": [0, 0, 0]},
            {"t": 0.32, "aura_frame": 0, "Hip": [-8, 4, -4], "Chest": [-6, 0, 0], "Head": [-8, 0, 0], "UpperArm_R": [8, 0, 0], "Forearm_R": [6, 0, 0], "Hand_R": [4, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [8, 0, 0], "Forearm_L": [-4, 0, 0], "Hand_L": [-4, 0, 0], "Weapon_Front": [-4, 0, 0], "Thigh_R": [6, 0, 0], "Shin_R": [4, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-4, 0, 0], "Shin_L": [6, 0, 0], "Foot_L": [0, 0, 0]},
            {"t": 0.48, "aura_frame": 1, "Hip": [0, 0, 0], "Chest": [0, 0, 0], "Head": [0, 0, 0], "UpperArm_R": [0, 0, 0], "Forearm_R": [0, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [0, 0, 0], "Forearm_L": [0, 0, 0], "Hand_L": [0, 0, 0], "Weapon_Front": [0, 0, 0], "Thigh_R": [0, 0, 0], "Shin_R": [0, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [0, 0, 0], "Shin_L": [0, 0, 0], "Foot_L": [0, 0, 0]},
        ],
    },
    "death": {
        "grid": [2, 3],
        "length": 1.10,
        "loop": False,
        "frames": [
            {"t": 0.00, "aura_frame": 3, "Hip": [-10, 6, -6], "Chest": [-12, 0, 0], "Head": [-14, 0, 0], "UpperArm_R": [14, 0, 0], "Forearm_R": [8, 0, 0], "Hand_R": [6, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [14, 0, 0], "Forearm_L": [-8, 0, 0], "Hand_L": [-6, 0, 0], "Weapon_Front": [-8, 0, 0], "Thigh_R": [10, 0, 0], "Shin_R": [8, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-8, 0, 0], "Shin_L": [10, 0, 0], "Foot_L": [0, 0, 0],
             "vfx": {"fx_spark": {"pos": [254, 212], "rot": 0, "scale": 0.72, "alpha": 0.92}}},
            {"t": 0.22, "aura_frame": 0, "Hip": [-6, 30, 14], "Chest": [16, 0, 0], "Head": [12, 0, 0], "UpperArm_R": [24, 0, 0], "Forearm_R": [12, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-16, 0, 0], "Forearm_L": [-10, 0, 0], "Hand_L": [-12, 0, 0], "Weapon_Front": [-16, 0, 0], "Thigh_R": [-42, 0, 0], "Shin_R": [64, 0, 0], "Foot_R": [12, 0, 0], "Thigh_L": [-36, 0, 0], "Shin_L": [58, 0, 0], "Foot_L": [10, 0, 0]},
            {"t": 0.45, "aura_frame": 3, "Hip": [-4, 56, 30], "Chest": [24, 0, 0], "Head": [18, 0, 0], "UpperArm_R": [36, 0, 0], "Forearm_R": [18, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-32, 0, 0], "Forearm_L": [-16, 0, 0], "Hand_L": [-20, 0, 0], "Weapon_Front": [-26, 0, 0], "Thigh_R": [-66, 0, 0], "Shin_R": [90, 0, 0], "Foot_R": [16, 0, 0], "Thigh_L": [-60, 0, 0], "Shin_L": [84, 0, 0], "Foot_L": [14, 0, 0],
             "vfx": {"fx_dust": {"pos": [256, 422], "rot": 0, "scale": 0.85, "alpha": 0.82}}},
            {"t": 0.68, "aura_frame": 0, "Hip": [-2, 68, 40], "Chest": [28, 0, 0], "Head": [22, 0, 0], "UpperArm_R": [42, 0, 0], "Forearm_R": [20, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-40, 0, 0], "Forearm_L": [-20, 0, 0], "Hand_L": [-24, 0, 0], "Weapon_Front": [-32, 0, 0], "Thigh_R": [-76, 0, 0], "Shin_R": [100, 0, 0], "Foot_R": [18, 0, 0], "Thigh_L": [-70, 0, 0], "Shin_L": [94, 0, 0], "Foot_L": [16, 0, 0],
             "vfx": {"fx_dust": {"pos": [264, 424], "rot": 0, "scale": 0.90, "alpha": 0.65}}, "modulate_a": 0.88},
            {"t": 0.88, "aura_frame": 3, "Hip": [0, 72, 44], "Chest": [30, 0, 0], "Head": [24, 0, 0], "UpperArm_R": [44, 0, 0], "Forearm_R": [22, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-42, 0, 0], "Forearm_L": [-22, 0, 0], "Hand_L": [-26, 0, 0], "Weapon_Front": [-34, 0, 0], "Thigh_R": [-78, 0, 0], "Shin_R": [102, 0, 0], "Foot_R": [18, 0, 0], "Thigh_L": [-72, 0, 0], "Shin_L": [96, 0, 0], "Foot_L": [16, 0, 0],
             "vfx": {"fx_dust": {"pos": [266, 424], "rot": 0, "scale": 0.75, "alpha": 0.45}}, "modulate_a": 0.52},
            {"t": 1.05, "aura_frame": 3, "Hip": [0, 74, 46], "Chest": [30, 0, 0], "Head": [24, 0, 0], "UpperArm_R": [44, 0, 0], "Forearm_R": [22, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-42, 0, 0], "Forearm_L": [-22, 0, 0], "Hand_L": [-26, 0, 0], "Weapon_Front": [-34, 0, 0], "Thigh_R": [-78, 0, 0], "Shin_R": [102, 0, 0], "Foot_R": [18, 0, 0], "Thigh_L": [-72, 0, 0], "Shin_L": [96, 0, 0], "Foot_L": [16, 0, 0],
             "modulate_a": 0.22},
        ],
    },
}


def compute_world_transforms(bones_list, frame_pose=None):
    if frame_pose is None:
        frame_pose = {}
    world = {}
    for b in bones_list:
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

    for b in bones_list:
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


def render_w018_pose(frame_pose=None, team_name="team_blue", show_weapon_front=True, show_weapon_back=False, show_aura=True, aura_idx=None, canvas_size=512):
    if frame_pose is None:
        frame_pose = {}
    canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    world = compute_world_transforms(BONES_W018, frame_pose)
    mod_a = frame_pose.get("modulate_a", 1.0)
    a_idx = aura_idx if aura_idx is not None else frame_pose.get("aura_frame", 1)
    anim_weapon_im = WEAPON_ANIM_FRAMES[a_idx % len(WEAPON_ANIM_FRAMES)]

    sorted_bones = sorted(BONES_W018, key=lambda b: b["z_index"])
    for b in sorted_bones:
        bname = b["name"]
        if bname == "Weapon_Front" and not show_weapon_front:
            continue
        if bname == "Weapon_Back" and not show_weapon_back:
            continue
        wx, wy, wrot = world[bname][:3]
        if b["is_weapon"]:
            if show_aura:
                if bname == "Weapon_Front":
                    im = anim_weapon_im
                else:
                    im = anim_weapon_im.resize(w018_off.size, Image.Resampling.LANCZOS)
            else:
                im = W018_IMAGES[b["part"]]
        else:
            im = PART_IMAGES_BY_TEAM[team_name][b["part"]]

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
        fx_im = W018_IMAGES[fx_name]
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
    font_title = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 16)
    font_sub = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 12)
except Exception:
    font_title = ImageFont.load_default()
    font_sub = ImageFont.load_default()

print("=== 3. Building SSR W018 3-Step Pipeline Audit Board ===")
board_w, board_h = 1860, 960
audit_im = Image.new("RGBA", (board_w, board_h), (16, 19, 26, 255))
audit_draw = ImageDraw.Draw(audit_im, "RGBA")

team_display = [
    ("team_blue", "DOI 1: XANH + W018 SSR (Frame 0)", (59, 130, 246, 255), 0, False),
    ("team_red", "DOI 2: DO + SONG KIEM SSR (Frame 1)", (239, 68, 68, 255), 1, True),
    ("team_green", "DOI 3: XANH LA + W018 SSR (Frame 2)", (34, 197, 94, 255), 2, False),
    ("team_amber", "DOI 4: VANG CAM + W018 SSR (Frame 3)", (245, 158, 11, 255), 3, False),
]

for idx, (t_key, t_label, t_col, a_f, dual_w) in enumerate(team_display):
    ox = 12 + idx * 345
    oy = 12
    audit_draw.rectangle([ox, oy, ox + 335, oy + 450], fill=(26, 31, 42, 255), outline=t_col, width=2)
    t_pose_im, _ = render_w018_pose({}, team_name=t_key, show_weapon_front=True, show_weapon_back=dual_w, show_aura=True, aura_idx=a_f, canvas_size=512)
    t_thumb = t_pose_im.resize((330, 330), Image.Resampling.LANCZOS)
    audit_im.alpha_composite(t_thumb, (ox + 2, oy + 46))
    audit_draw.text((ox + 12, oy + 10), t_label, fill=t_col, font=font_title)
    sub_txt = "SSR Weapon Anim Spritesheet ON" if not dual_w else "Demo Song Kiem SSR Anim ON"
    audit_draw.text((ox + 12, oy + 28), f"{sub_txt} | edge_clip=0px", fill=(210, 220, 235, 255), font=font_sub)

# Panel 5 on Top Row: BUOC 3 — W018 SSR Diagonal Card Cover
ox5 = 12 + 4 * 345
audit_draw.rectangle([ox5, 12, board_w - 12, 462], fill=(26, 31, 42, 255), outline=(245, 158, 11, 255), width=2)
audit_draw.text((ox5 + 12, 20), "BUOC 3: ANH BIA CARD (884x632 — Tu Ref & Anim)", fill=(252, 211, 77, 255), font=font_title)
card_prev = Image.open(W018_CARD_PNG).convert("RGBA").resize((436, 312), Image.Resampling.LANCZOS)
audit_im.alpha_composite(card_prev, (ox5 + 14, 48))
audit_draw.rectangle([ox5 + 14, 48, ox5 + 14 + 436, 48 + 312], outline=(245, 158, 11, 220), width=1)
audit_draw.text((ox5 + 14, 370), "884x632 PNG & 354x253 WebP (Giong het 100% Ref & Anim!)", fill=(252, 211, 77, 255), font=font_sub)
audit_draw.text((ox5 + 14, 392), f"Grip 1 (Do): ({W018_G1_X}, {W018_G1_Y}) | Grip 2 (Xanh): ({W018_G2_X}, {W018_G2_Y})", fill=(220, 230, 245, 255), font=font_sub)
audit_draw.text((ox5 + 14, 414), "Flow: 1. Anh Ref -> 2. Spritesheet Anim 2x2 -> 3. Anh Bia Card", fill=(130, 235, 165, 255), font=font_sub)

# Bottom Half:
# 1. Left Box: BUOC 1 — W018 Reference Weapon (weapon_main.png tight-trimmed 0px pad) with Grip 1 & Grip 2
bx_w = 12
by_w = 478
audit_draw.rectangle([bx_w, by_w, bx_w + 440, board_h - 12], fill=(26, 31, 42, 255), outline=(245, 158, 11, 255), width=2)
audit_draw.text((bx_w + 14, by_w + 12), f"BUOC 1: ANH REF VU KHI ({w018_final.width}x{w018_final.height} — 0px Pad)", fill=(252, 211, 77, 255), font=font_title)
audit_draw.text((bx_w + 14, by_w + 32), "Cham DO = Grip 1 (Tay Chinh) | Cham XANH = Grip 2 (Tay Phu)", fill=(130, 235, 165, 255), font=font_sub)
wx_p = bx_w + (440 - w018_final.width) // 2
wy_p = by_w + 68
audit_im.alpha_composite(w018_final, (wx_p, wy_p))
audit_draw.rectangle([wx_p, wy_p, wx_p + w018_final.width, wy_p + w018_final.height], outline=(90, 220, 135, 180), width=1)
g1x, g1y = wx_p + W018_G1_X, wy_p + W018_G1_Y
g2x, g2y = wx_p + W018_G2_X, wy_p + W018_G2_Y
audit_draw.ellipse([g1x - 6, g1y - 6, g1x + 6, g1y + 6], fill=(240, 50, 50, 255), outline=(255, 255, 255, 255), width=2)
audit_draw.ellipse([g2x - 6, g2y - 6, g2x + 6, g2y + 6], fill=(40, 210, 255, 255), outline=(255, 255, 255, 255), width=2)

audit_draw.text((bx_w + 14, by_w + 278), "Raw 2x2 Spritesheet tu Muse AI (w018_weapon_anim_2x2_raw.png):", fill=(252, 211, 77, 255), font=font_sub)
raw_2x2_thumb = anim_raw_im.resize((160, 160), Image.Resampling.LANCZOS)
audit_im.alpha_composite(raw_2x2_thumb, (bx_w + 140, by_w + 300))

# 2. Right 4 Columns: BUOC 2 — 4 Frames of Animated SSR Weapon Spritesheet (weapon_anim_0..3.png)
anim_titles = [
    "BUOC 2 - Frame 1 (weapon_anim_0): Co Ngu & Lua Khoi Phat",
    "BUOC 2 - Frame 2 (weapon_anim_1): Loi Dien & Lua Quan Quanh",
    "BUOC 2 - Frame 3 (weapon_anim_2): Dinh Diem Hao Quang SSR",
    "BUOC 2 - Frame 4 (weapon_anim_3): Tan Hoa Huyet Long Loop",
]
for idx in range(4):
    ax = 468 + idx * 345
    ay = 478
    audit_draw.rectangle([ax, ay, ax + 333, board_h - 12], fill=(22, 26, 36, 255), outline=(239, 68, 68, 200), width=1)
    audit_draw.text((ax + 10, ay + 12), anim_titles[idx], fill=(252, 211, 77, 255), font=font_sub)
    wf_im = WEAPON_ANIM_FRAMES[idx]
    audit_draw.text((ax + 10, ay + 32), f"Size: {wf_im.width}x{wf_im.height} | Căn đồng trục Grip 1/2 (0px lệch)", fill=(130, 235, 165, 255), font=font_sub)

    # Show extracted animated weapon frame
    audit_im.alpha_composite(wf_im, (ax + (333 - wf_im.width) // 2, ay + 66))
    audit_draw.rectangle(
        [ax + (333 - wf_im.width) // 2, ay + 66, ax + (333 - wf_im.width) // 2 + wf_im.width, ay + 66 + wf_im.height],
        outline=(90, 220, 135, 120),
        width=1,
    )

    # Show pure glowing VFX layer below
    audit_draw.text((ax + 12, ay + 266), "Layer Hieu Ung Lua/Set Tach Rieng:", fill=(180, 195, 215, 255), font=font_sub)
    vfx_im = AURA_ONLY_FRAMES[idx]
    audit_im.alpha_composite(vfx_im, (ax + (333 - vfx_im.width) // 2, ay + 286))

w018_audit_path = os.path.join(W018_QC_DIR, "w018_ssr_weapon_and_aura_audit.png")
audit_im.save(w018_audit_path)
shutil.copyfile(w018_audit_path, os.path.join(ARTIFACT_DIR, "w018_ssr_weapon_and_aura_audit.png"))
print("Saved W018 SSR 3-Step Audit Board ->", w018_audit_path)

print("=== 4. Building All 6 Actions Overview Board for Stickman + W018 SSR ===")
ov_w, ov_h = 3 * 560 + 24, 2 * 560 + 24
ov_im = Image.new("RGBA", (ov_w, ov_h), (16, 19, 26, 255))
ov_draw = ImageDraw.Draw(ov_im)
total_edge_clips = 0

action_order = ["idle", "walk", "attack", "cast", "hurt", "death"]
team_cycle = ["team_blue", "team_red", "team_green", "team_amber", "team_blue", "team_red"]
for a_idx, act_name in enumerate(action_order):
    act = ACTIONS_W018[act_name]
    rows, cols = act["grid"]
    frames = act["frames"]
    ar, ac = divmod(a_idx, 3)
    bx = 12 + ac * 560
    by = 12 + ar * 560
    ov_draw.rectangle([bx, by, bx + 544, by + 544], fill=(24, 28, 38, 255), outline=(245, 158, 11, 180), width=1)

    thumb_size = 240 if cols == 2 else 166
    grid_w = cols * thumb_size
    grid_h = rows * thumb_size
    gx0 = bx + (544 - grid_w) // 2
    gy0 = by + 36 + (500 - grid_h) // 2

    act_clips = 0
    t_for_act = team_cycle[a_idx]
    for f_idx, f_pose in enumerate(frames):
        f_im, _ = render_w018_pose(f_pose, team_name=t_for_act, show_weapon_front=True, show_weapon_back=False, show_aura=True, canvas_size=512)
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
        f"SSR Action {a_idx+1}: {act_name.upper()} ({t_for_act} | {len(frames)}f | Anim Weapon ON | edge_clip={act_clips}px)",
        fill=(252, 211, 77, 255),
        font=font_title,
    )

assert total_edge_clips == 0, f"Found {total_edge_clips} edge-clipped pixels!"
ov_path = os.path.join(W018_QC_DIR, "w018_sticker_all_6_actions_overview.png")
ov_im.save(ov_path)
shutil.copyfile(ov_path, os.path.join(ARTIFACT_DIR, "w018_sticker_all_6_actions_overview.png"))
print(f"Saved W018 SSR 6-Action Overview -> {ov_path} (total_edge_clips={total_edge_clips}px)")

# 5. Generate Godot 4 Scene (.tscn) & Script (.gd) for C018/W018 SSR
VFX_LIST = ["fx_slash", "fx_slash_heavy", "fx_spark", "fx_dust"]


def generate_w018_tscn(bones_data, actions_data):
    lines = []
    ext_count = 1 + len(bones_data) + len(VFX_LIST) + 4
    sub_count = 2 + len(actions_data)
    lines.append(f'[gd_scene load_steps={ext_count + sub_count} format=3 uid="uid://c018stickerweaponssr"]')
    lines.append("")
    lines.append('[ext_resource type="Script" path="res://assets/weapons/w018_huyet_kiem_hanh_quyet/godot/c018_hanh_quyet_gia.gd" id="1_script"]')

    part_ext_id = {}
    idx = 2
    for b in bones_data:
        pname = b["part"]
        if pname not in part_ext_id:
            if b["is_weapon"]:
                res_p = f"res://assets/weapons/w018_huyet_kiem_hanh_quyet/parts/{pname}.png"
            else:
                res_p = f"res://assets/sticker_hero/godot/parts/team_blue/{pname}.png"
            lines.append(f'[ext_resource type="Texture2D" path="{res_p}" id="{idx}_{pname}"]')
            part_ext_id[pname] = f"{idx}_{pname}"
            idx += 1

    for a_i in range(4):
        res_p = f"res://assets/weapons/w018_huyet_kiem_hanh_quyet/parts/weapon_anim_{a_i}.png"
        lines.append(f'[ext_resource type="Texture2D" path="{res_p}" id="{idx}_anim_{a_i}"]')
        part_ext_id[f"anim_{a_i}"] = f"{idx}_anim_{a_i}"
        idx += 1

    for fx in VFX_LIST:
        lines.append(f'[ext_resource type="Texture2D" path="res://assets/weapons/w018_huyet_kiem_hanh_quyet/parts/{fx}.png" id="{idx}_{fx}"]')
        part_ext_id[fx] = f"{idx}_{fx}"
        idx += 1

    lines.append("")
    lines.append('[sub_resource type="SpriteFrames" id="SpriteFrames_ssr_weapon_anim"]')
    lines.append("animations = [{")
    lines.append('"frames": [')
    for a_i in range(4):
        comma = "," if a_i < 3 else ""
        lines.append(f'{{"duration": 1.0, "texture": ExtResource("{part_ext_id[f"anim_{a_i}"]}")}}{comma}')
    lines.append("],")
    lines.append('"loop": true,')
    lines.append('"name": &"default",')
    lines.append('"speed": 8.0')
    lines.append("}]")
    lines.append("")

    for act_name, act in actions_data.items():
        lines.append(f'[sub_resource type="Animation" id="Animation_{act_name}"]')
        lines.append(f'resource_name = "{act_name}"')
        lines.append(f'length = {act["length"]}')
        lines.append(f'loop_mode = {1 if act["loop"] else 0}')
        t_idx = 0
        bone_Paths = {}
        for b in bones_data:
            bname = b["name"]
            p = b["parent"]
            bone_Paths[bname] = f"Skeleton2D/{bname}" if p is None else f"{bone_Paths[p]}/{bname}"

        for b in bones_data:
            bname = b["name"]
            bpath = bone_Paths[bname]
            times = ", ".join(f'{f["t"]:.2f}' for f in act["frames"])
            rots, pos_vals = [], []
            for f in act["frames"]:
                if bname == "Hip":
                    dx, dy, drot = f.get("Hip", (0.0, 0.0, 0.0))
                else:
                    drot, dx, dy = f.get(bname, (0.0, 0.0, 0.0))
                rots.append(f"{math.radians(b['rest_rot'] + drot):.4f}")
                pos_vals.append(f"Vector2({b['rest_x'] + dx:.1f}, {b['rest_y'] + dy:.1f})")

            lines.append(f'tracks/{t_idx}/type = "value"')
            lines.append(f'tracks/{t_idx}/imported = false')
            lines.append(f'tracks/{t_idx}/enabled = true')
            lines.append(f'tracks/{t_idx}/path = NodePath("{bpath}:rotation")')
            lines.append(f'tracks/{t_idx}/interp = 1')
            lines.append(f'tracks/{t_idx}/loop_wrap = true')
            lines.append(f'tracks/{t_idx}/keys = {{"times": PackedFloat32Array({times}), "transitions": PackedFloat32Array({", ".join(["1"]*len(act["frames"]))}), "update": 0, "values": [{", ".join(rots)}]}}')
            t_idx += 1

            lines.append(f'tracks/{t_idx}/type = "value"')
            lines.append(f'tracks/{t_idx}/imported = false')
            lines.append(f'tracks/{t_idx}/enabled = true')
            lines.append(f'tracks/{t_idx}/path = NodePath("{bpath}:position")')
            lines.append(f'tracks/{t_idx}/interp = 1')
            lines.append(f'tracks/{t_idx}/loop_wrap = true')
            lines.append(f'tracks/{t_idx}/keys = {{"times": PackedFloat32Array({times}), "transitions": PackedFloat32Array({", ".join(["1"]*len(act["frames"]))}), "update": 0, "values": [{", ".join(pos_vals)}]}}')
            t_idx += 1
        lines.append("")

    anim_entries = ", ".join(f'"{k}": SubResource("Animation_{k}")' for k in actions_data.keys())
    lines.append('[sub_resource type="AnimationLibrary" id="AnimationLibrary_main"]')
    lines.append(f"_data = {{{anim_entries}}}")
    lines.append("")
    lines.append('[node name="C018_HanhQuyetGia" type="Node2D"]')
    lines.append('script = ExtResource("1_script")')
    lines.append("")
    lines.append('[node name="Skeleton2D" type="Skeleton2D" parent="."]')
    lines.append("")

    bone_Paths = {}
    for b in bones_data:
        bname = b["name"]
        p = b["parent"]
        parent_str = "Skeleton2D" if p is None else bone_Paths[p]
        bone_Paths[bname] = f"{parent_str}/{bname}"
        lines.append(f'[node name="{bname}" type="Bone2D" parent="{parent_str}"]')
        lines.append(f'position = Vector2({b["rest_x"]:.1f}, {b["rest_y"]:.1f})')
        lines.append(f'rotation = {math.radians(b["rest_rot"]):.4f}')
        if b.get("is_weapon"):
            lines.append(f'metadata/grip1 = Vector2({b["grip1_x"]:.1f}, {b["grip1_y"]:.1f})')
            lines.append(f'metadata/grip2 = Vector2({b["grip2_x"]:.1f}, {b["grip2_y"]:.1f})')
        if b.get("is_weapon") and not b.get("visible_default", True):
            lines.append("visible = false")
        lines.append("")
        lines.append(f'[node name="Sprite" type="Sprite2D" parent="{bone_Paths[bname]}"]')
        lines.append(f'z_index = {b["z_index"]}')
        lines.append(f'texture = ExtResource("{part_ext_id[b["part"]]}")')
        lines.append(f'offset = Vector2({b["offset_x"]:.2f}, {b["offset_y"]:.2f})')
        lines.append("")
        if bname == "Weapon_Front":
            lines.append(f'[node name="WeaponAura" type="AnimatedSprite2D" parent="{bone_Paths[bname]}"]')
            lines.append("visible = true")
            lines.append(f'z_index = {b["z_index"]}')
            lines.append('sprite_frames = SubResource("SpriteFrames_ssr_weapon_anim")')
            lines.append('animation = &"default"')
            lines.append('autoplay = "default"')
            lines.append(f'offset = Vector2({b["offset_x"]:.2f}, {b["offset_y"]:.2f})')
            lines.append("")

    lines.append('[node name="VFX" type="Node2D" parent="."]')
    lines.append("")
    for fx in VFX_LIST:
        lines.append(f'[node name="{fx}" type="Sprite2D" parent="VFX"]')
        lines.append("visible = false")
        lines.append("z_index = 20")
        lines.append(f'texture = ExtResource("{part_ext_id[fx]}")')
        lines.append("")

    lines.append('[node name="AnimationPlayer" type="AnimationPlayer" parent="."]')
    lines.append('libraries = {"": SubResource("AnimationLibrary_main")}')
    lines.append('autoplay = "idle"')
    lines.append("")
    return "\n".join(lines)


tscn_w018_str = generate_w018_tscn(BONES_W018, ACTIONS_W018)
tscn_w018_path = os.path.join(W018_GODOT_DIR, "c018_hanh_quyet_gia.tscn")
with open(tscn_w018_path, "w", encoding="utf-8") as f:
    f.write(tscn_w018_str)

gd_w018_code = """extends Node2D
class_name C018HanhQuyetGia

@export_enum("team_blue", "team_red", "team_green", "team_amber") var team_color: String = "team_blue":
\tset(value):
\t\tteam_color = value
\t\tif is_node_ready():
\t\t\tapply_team_color(team_color)

@export var dual_weapon_enabled: bool = false:
\tset(value):
\t\tdual_weapon_enabled = value
\t\tif has_node("Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Hand_R/Weapon_Back"):
\t\t\t$Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Hand_R/Weapon_Back.visible = value

@export var weapon_aura_enabled: bool = true:
\tset(value):
\t\tweapon_aura_enabled = value
\t\tif has_node("Skeleton2D/Hip/Chest/UpperArm_L/Forearm_L/Hand_L/Weapon_Front/WeaponAura"):
\t\t\t$Skeleton2D/Hip/Chest/UpperArm_L/Forearm_L/Hand_L/Weapon_Front/WeaponAura.visible = value

@onready var anim_player: AnimationPlayer = $AnimationPlayer

func _ready() -> void:
\tapply_team_color(team_color)
\tplay_action("idle")

func apply_team_color(t_name: String) -> void:
\tvar stickman_nodes := {
\t\t"Hip": "hip_kilt",
\t\t"Hip/Thigh_L": "leg_thigh_back",
\t\t"Hip/Thigh_L/Shin_L": "leg_shin_back",
\t\t"Hip/Thigh_L/Shin_L/Foot_L": "foot_back",
\t\t"Hip/Thigh_R": "leg_thigh_front",
\t\t"Hip/Thigh_R/Shin_R": "leg_shin_front",
\t\t"Hip/Thigh_R/Shin_R/Foot_R": "foot_front",
\t\t"Hip/Chest": "chest",
\t\t"Hip/Chest/Neck": "neck",
\t\t"Hip/Chest/Neck/Head": "head",
\t\t"Hip/Chest/UpperArm_R": "arm_upper_back",
\t\t"Hip/Chest/UpperArm_R/Forearm_R": "arm_lower_back",
\t\t"Hip/Chest/UpperArm_R/Forearm_R/Hand_R": "hand_back",
\t\t"Hip/Chest/UpperArm_L": "arm_upper_front",
\t\t"Hip/Chest/UpperArm_L/Forearm_L": "arm_lower_front",
\t\t"Hip/Chest/UpperArm_L/Forearm_L/Hand_L": "hand_front",
\t}
\tfor rel_path in stickman_nodes.keys():
\t\tvar spr := get_node_or_null("Skeleton2D/" + rel_path + "/Sprite") as Sprite2D
\t\tif spr:
\t\t\tvar p_file: String = stickman_nodes[rel_path]
\t\t\tspr.texture = load("res://assets/sticker_hero/godot/parts/%s/%s.png" % [t_name, p_file])

func play_action(action_name: String) -> void:
\tif anim_player and anim_player.has_animation(action_name):
\t\tanim_player.play(action_name)
"""
with open(os.path.join(W018_GODOT_DIR, "c018_hanh_quyet_gia.gd"), "w", encoding="utf-8") as f:
    f.write(gd_w018_code)
print("Wrote Godot 4 SSR Scene & Script ->", tscn_w018_path)

print("=== 6. Updating Interactive Multi-Weapon HTML Editor (W018 SSR + W001 N) ===")


def b64_png(path):
    with open(path, "rb") as bf:
        return "data:image/png;base64," + base64.b64encode(bf.read()).decode("ascii")


w018_pack = {
    "id": "w018",
    "name": "W018 — Huyết Kiếm Hành Quyết (Cấp SSR)",
    "tscn_name": "c018_hanh_quyet_gia.tscn",
    "script_res": "res://assets/weapons/w018_huyet_kiem_hanh_quyet/godot/c018_hanh_quyet_gia.gd",
    "parts_res_prefix": "res://assets/weapons/w018_huyet_kiem_hanh_quyet/parts",
    "node_name": "C018_HanhQuyetGia",
    "aura_default": True,
    "card_b64": b64_png(W018_CARD_PNG),
    "bones": BONES_W018,
    "actions": ACTIONS_W018,
    "images": {
        "weapon_main": b64_png(os.path.join(W018_PARTS_DIR, "weapon_main.png")),
        "weapon_offhand": b64_png(os.path.join(W018_PARTS_DIR, "weapon_offhand.png")),
        "weapon_aura": b64_png(os.path.join(W018_PARTS_DIR, "weapon_aura.png")),
        "weapon_anim_0": b64_png(os.path.join(W018_PARTS_DIR, "weapon_anim_0.png")),
        "weapon_anim_1": b64_png(os.path.join(W018_PARTS_DIR, "weapon_anim_1.png")),
        "weapon_anim_2": b64_png(os.path.join(W018_PARTS_DIR, "weapon_anim_2.png")),
        "weapon_anim_3": b64_png(os.path.join(W018_PARTS_DIR, "weapon_anim_3.png")),
        "fx_slash": b64_png(os.path.join(W018_PARTS_DIR, "fx_slash.png")),
        "fx_slash_heavy": b64_png(os.path.join(W018_PARTS_DIR, "fx_slash_heavy.png")),
        "fx_spark": b64_png(os.path.join(W018_PARTS_DIR, "fx_spark.png")),
        "fx_dust": b64_png(os.path.join(W018_PARTS_DIR, "fx_dust.png")),
    },
}

# Read existing sticker_weapon_editor.html to extract TEAM_PART_B64 & W001 data and upgrade to multi-weapon (W018 SSR default + W001 N)
editor_path = "/Users/dochung/Desktop/card_g/assets/sticker_weapon_editor.html"
w001_editor_path = "/Users/dochung/Desktop/card_g/assets/weapons/w001_hac_kiem_tan_binh/w001_editor.html"
w018_editor_path = os.path.join(W018_DIR, "w018_editor.html")

with open(w001_editor_path, "r", encoding="utf-8") as f:
    html_src = f.read()

# Upgrade the HTML Editor to include W018 SSR (with 4-frame animated weapon spritesheet) alongside W001 N
w018_json_str = json.dumps(w018_pack)

html_upgraded = html_src.replace(
    "<title>Card_G — Sticker Hero (4 Màu Đội) + Weapon Rig Editor (W001: Hắc Kiếm Tàn Binh)</title>",
    "<title>Card_G — Sticker Hero (4 Màu Đội) + Multi-Weapon Rig Editor (W018 SSR & W001 N)</title>",
)
html_upgraded = html_upgraded.replace(
    '<option value="w001">W001 — Hắc Kiếm Tàn Binh (Cấp N)</option>',
    '<option value="w018" selected>W018 — Huyết Kiếm Hành Quyết (Cấp SSR — Animated 2x2 Spritesheet)</option>\n        <option value="w001">W001 — Hắc Kiếm Tàn Binh (Cấp N)</option>',
)

# Inject W018_PACK and 4-frame weapon spritesheet switching logic right after BONE_MAP initialization
inject_marker = "const BONE_MAP = {};\nBONES.forEach(b => BONE_MAP[b.name] = b);"
inject_js = f"""const BONE_MAP = {{}};
BONES.forEach(b => BONE_MAP[b.name] = b);

const W018_PACK = {w018_json_str};
const W001_PACK = {{
  id: "w001",
  name: "W001 — Hắc Kiếm Tàn Binh (Cấp N)",
  tscn_name: "c001_hac_kiem_tan_binh.tscn",
  node_name: "C001_HacKiemTanBinh",
  aura_default: false,
  card_b64: CARD_PREVIEW_B64,
  bones: JSON.parse(JSON.stringify(BONES)),
  actions: JSON.parse(JSON.stringify(ACTIONS)),
  images: WEAPON_PART_B64
}};
let currentWeaponId = "w018";
const WEAPON_PACK_IMAGES = {{ w001: {{}}, w018: {{}} }};
Object.entries(W001_PACK.images).forEach(([k, src]) => {{
  const im = new Image(); im.src = src; WEAPON_PACK_IMAGES.w001[k] = im;
}});
Object.entries(W018_PACK.images).forEach(([k, src]) => {{
  const im = new Image(); im.src = src; WEAPON_PACK_IMAGES.w018[k] = im;
}});

function rebuildBoneList() {{
  const boneList = document.getElementById("boneList");
  if (!boneList) return;
  boneList.innerHTML = "";
  BONES.forEach(b => {{
    const div = document.createElement("div");
    div.className = "bone-item" + (b.name === selectedBone ? " selected" : "");
    div.innerHTML = `<span>${{b.name}}</span><span style="color:var(--muted);font-size:11px">z:${{b.z_index}}</span>`;
    div.onclick = () => selectBone(b.name);
    boneList.appendChild(div);
  }});
}}

function applyWeaponPack(wid) {{
  currentWeaponId = wid;
  const pack = wid === "w018" ? W018_PACK : W001_PACK;
  BONES.length = 0;
  JSON.parse(JSON.stringify(pack.bones)).forEach(b => BONES.push(b));
  Object.keys(BONE_MAP).forEach(k => delete BONE_MAP[k]);
  BONES.forEach(b => BONE_MAP[b.name] = b);
  Object.keys(ACTIONS).forEach(k => delete ACTIONS[k]);
  Object.entries(JSON.parse(JSON.stringify(pack.actions))).forEach(([k, v]) => ACTIONS[k] = v);
  Object.keys(WEAPON_IMAGES).forEach(k => delete WEAPON_IMAGES[k]);
  Object.entries(WEAPON_PACK_IMAGES[wid]).forEach(([k, im]) => WEAPON_IMAGES[k] = im);
  showWeaponAura = pack.aura_default;
  const chkAura = document.getElementById("chkWeaponAura");
  if (chkAura) chkAura.checked = showWeaponAura;
  const cardImg = document.getElementById("cardPreviewImg");
  if (cardImg) cardImg.src = pack.card_b64;
  const wf = BONE_MAP["Weapon_Front"];
  if (wf) {{
    document.getElementById("grip1X").value = Math.round(wf.grip1_x);
    document.getElementById("grip1Y").value = Math.round(wf.grip1_y);
    document.getElementById("grip2X").value = Math.round(wf.grip2_x);
    document.getElementById("grip2Y").value = Math.round(wf.grip2_y);
  }}
  currentFrameIdx = 0;
  currentTime = 0.0;
  const sc = document.getElementById("timeScrubber");
  if (sc && ACTIONS[currentAction]) {{
    sc.max = ACTIONS[currentAction].length;
    sc.value = 0;
  }}
  rebuildBoneList();
  rebuildFramePills();
  syncInspector();
}}"""

html_upgraded = html_upgraded.replace(inject_marker, inject_js, 1)

# Update onSelectWeapon() to call applyWeaponPack
html_upgraded = html_upgraded.replace(
    'function onSelectWeapon() {\n  document.getElementById("statusToast").textContent = "Đang chọn: W001 — Hắc Kiếm Tàn Binh";\n}',
    'function onSelectWeapon() {\n  const wid = document.getElementById("weaponSelect").value;\n  applyWeaponPack(wid);\n  document.getElementById("statusToast").textContent = wid === "w018" ? "Đang trang bị: W018 — Huyết Kiếm Hành Quyết (SSR 4-Frame Animated Weapon)" : "Đang trang bị: W001 — Hắc Kiếm Tàn Binh (Cấp N)";\n}',
)

# Update saveToGodotTscn & buildGodotTscnString to use the active weapon pack filename/paths
html_upgraded = html_upgraded.replace(
    'suggestedName: "c001_hac_kiem_tan_binh.tscn",',
    'suggestedName: currentWeaponId === "w018" ? "c018_hanh_quyet_gia.tscn" : "c001_hac_kiem_tan_binh.tscn",',
)
html_upgraded = html_upgraded.replace(
    'toast.textContent = "✅ Đã lưu trực tiếp vào file c001_hac_kiem_tan_binh.tscn!";',
    'toast.textContent = "✅ Đã lưu trực tiếp vào file " + (currentWeaponId === "w018" ? "c018_hanh_quyet_gia.tscn" : "c001_hac_kiem_tan_binh.tscn") + "!";',
)
html_upgraded = html_upgraded.replace(
    'a.download = "c001_hac_kiem_tan_binh.tscn";',
    'a.download = currentWeaponId === "w018" ? "c018_hanh_quyet_gia.tscn" : "c001_hac_kiem_tan_binh.tscn";',
)
html_upgraded = html_upgraded.replace(
    'toast.textContent = "✅ Đã xuất file c001_hac_kiem_tan_binh.tscn!";',
    'toast.textContent = "✅ Đã xuất file " + (currentWeaponId === "w018" ? "c018_hanh_quyet_gia.tscn" : "c001_hac_kiem_tan_binh.tscn") + "!";',
)

# Update weapon rendering in renderLoop so W018 uses its 4-frame animated weapon spritesheet (weapon_anim_0..3) when showWeaponAura is ON
old_draw_block = """    // Optional SSR Weapon Aura behind/around Weapon_Front
    if (b.name === "Weapon_Front" && showWeaponAura && WEAPON_IMAGES["weapon_aura"] && WEAPON_IMAGES["weapon_aura"].complete) {
      const auraImg = WEAPON_IMAGES["weapon_aura"];
      const pulse = 0.96 + 0.08 * Math.sin(now * 0.008);
      ctx.save();
      ctx.globalAlpha = modA * (0.72 + 0.22 * Math.sin(now * 0.01));
      ctx.translate(w.wx, w.wy);
      ctx.rotate(w.wrot * Math.PI / 180.0);
      ctx.scale(pulse, pulse);
      ctx.drawImage(auraImg, -b.pivot_x - 24, -b.pivot_y - 24);
      ctx.restore();
    }

    ctx.save();
    ctx.globalAlpha = modA;
    ctx.translate(w.wx, w.wy);
    ctx.rotate(w.wrot * Math.PI / 180.0);
    ctx.drawImage(img, -b.pivot_x, -b.pivot_y);"""

new_draw_block = """    let drawWeaponImg = img;
    if (b.is_weapon && showWeaponAura) {
      const animIdx = Math.floor(now / 125) % 4;
      const animKey = `weapon_anim_${animIdx}`;
      if (WEAPON_IMAGES[animKey] && WEAPON_IMAGES[animKey].complete) {
        drawWeaponImg = WEAPON_IMAGES[animKey];
      } else if (b.name === "Weapon_Front" && WEAPON_IMAGES["weapon_aura"] && WEAPON_IMAGES["weapon_aura"].complete) {
        const auraImg = WEAPON_IMAGES["weapon_aura"];
        ctx.save();
        ctx.globalAlpha = modA * 0.85;
        ctx.translate(w.wx, w.wy);
        ctx.rotate(w.wrot * Math.PI / 180.0);
        ctx.drawImage(auraImg, -b.pivot_x - 24, -b.pivot_y - 24);
        ctx.restore();
      }
    }

    ctx.save();
    ctx.globalAlpha = modA;
    ctx.translate(w.wx, w.wy);
    ctx.rotate(w.wrot * Math.PI / 180.0);
    if (b.name === "Weapon_Back" && drawWeaponImg !== img) {
      ctx.scale(0.78, 0.78);
      ctx.drawImage(drawWeaponImg, -b.pivot_x / 0.78, -b.pivot_y / 0.78);
    } else {
      ctx.drawImage(drawWeaponImg, -b.pivot_x, -b.pivot_y);
    }"""

html_upgraded = html_upgraded.replace(old_draw_block, new_draw_block, 1)
html_upgraded = html_upgraded.replace("initUI();\nrequestAnimationFrame(renderLoop);", "initUI();\napplyWeaponPack(\"w018\");\nrequestAnimationFrame(renderLoop);")

with open(editor_path, "w", encoding="utf-8") as f:
    f.write(html_upgraded)
with open(w018_editor_path, "w", encoding="utf-8") as f:
    f.write(html_upgraded)

print("Saved Interactive Multi-Weapon HTML Editor ->", editor_path, "and", w018_editor_path)
print("ALL W018 SSR BUILD STEPS COMPLETE!")
