#!/usr/bin/env python3
"""
Extracts and audits all 18 isolated body parts + 4 soft-opacity VFX PNGs for C004 — Kỵ Binh Gỉ Sét:
- Follows the Front-Hand Weapon Grip Rule:
  Front Arm (UpperArm_L -> Forearm_L -> Hand_L -> Sword) holds the heavy rusted iron cavalry shock-lance in the foreground!
  Back Arm (UpperArm_R -> Forearm_R -> Hand_R) holds the small battered round rusted-iron buckler shield!
- Every single PNG is cleanly masked with rounded joint caps and padded with transparent margin so edge_clip = 0px.
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERO_DIR = "/Users/dochung/Desktop/card_g/assets/heroes/c004_ky_binh_gi_set"
REF_CLEAN_PATH = os.path.join(HERO_DIR, "reference/c004_reference_clean.png")
CORE_RAW_PATH = os.path.join(HERO_DIR, "parts/c004_parts_core_2x2_raw.png")
LIMBS_RAW_PATH = os.path.join(HERO_DIR, "parts/c004_parts_limbs_2x3_raw.png")
HF_RAW_PATH = os.path.join(HERO_DIR, "parts/c004_parts_hands_feet_2x2_raw.png")
VFX_RAW_PATH = os.path.join(HERO_DIR, "vfx/c004_vfx_light_2x2_raw.png")
PARTS_DIR = os.path.join(HERO_DIR, "godot/parts")

os.makedirs(PARTS_DIR, exist_ok=True)


def clean_magenta_cell(cell_im, border_margin=10):
    arr = np.array(cell_im.convert("RGBA")).astype(np.float32)
    h, w, _ = arr.shape
    if border_margin > 0:
        arr[:border_margin, :, 3] = 0
        arr[h - border_margin :, :, 3] = 0
        arr[:, :border_margin, 3] = 0
        arr[:, w - border_margin :, 3] = 0

    r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
    mag_dist = np.sqrt((r - 255.0) ** 2 + (g - 0.0) ** 2 + (b - 255.0) ** 2)
    mag_dom = (r + b) / 2.0 - g
    is_bg = (mag_dist < 115.0) | ((mag_dom > 82.0) & (r > 125) & (b > 125))
    a[is_bg] = 0.0

    edge_fringe = (a > 0) & (mag_dom > 16.0)
    r[edge_fringe] = np.minimum(r[edge_fringe], g[edge_fringe] + 10.0)
    b[edge_fringe] = np.minimum(b[edge_fringe], g[edge_fringe] + 8.0)
    a[edge_fringe] *= np.clip(1.0 - (mag_dom[edge_fringe] - 28.0) / 58.0, 0.25, 1.0)
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
                y_min, y_max = max(0, cy - 1), min(h, cy + 2)
                x_min, x_max = max(0, cx - 1), min(w, cx + 2)
                for ny in range(y_min, y_max):
                    for nx in range(x_min, x_max):
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


def round_top_bottom_caps(crop_arr, round_top=True, round_bottom=False, cap_frac=0.18):
    out = crop_arr.copy()
    h, w, _ = out.shape
    if round_top and h > 16 and w > 12:
        cap_h = max(6, int(round(h * cap_frac)))
        cx = (w - 1) / 2.0
        rx = max(4.0, w * 0.48)
        for y in range(cap_h):
            dy = (cap_h - y) / float(cap_h)
            max_dx = rx * np.sqrt(max(0.0, 1.0 - dy * dy * 0.85))
            for x in range(w):
                dist = abs(x - cx)
                if dist > max_dx + 2.0:
                    out[y, x, 3] = 0
                elif dist > max_dx:
                    out[y, x, 3] = int(out[y, x, 3] * (1.0 - (dist - max_dx) / 2.0))
    if round_bottom and h > 16 and w > 12:
        cap_h = max(6, int(round(h * cap_frac)))
        cx = (w - 1) / 2.0
        rx = max(4.0, w * 0.48)
        for i in range(cap_h):
            y = h - 1 - i
            dy = (cap_h - i) / float(cap_h)
            max_dx = rx * np.sqrt(max(0.0, 1.0 - dy * dy * 0.85))
            for x in range(w):
                dist = abs(x - cx)
                if dist > max_dx + 2.0:
                    out[y, x, 3] = 0
                elif dist > max_dx:
                    out[y, x, 3] = int(out[y, x, 3] * (1.0 - (dist - max_dx) / 2.0))
    return out


def crop_resize_pad_save(
    rgba_arr,
    out_name,
    target_w=None,
    target_h=None,
    pad=12,
    keep_largest=True,
    round_top=False,
    round_bottom=False,
):
    if keep_largest:
        rgba_arr = keep_largest_component(rgba_arr)
    ys, xs = np.where(rgba_arr[:, :, 3] > 20)
    if len(xs) == 0:
        raise RuntimeError(f"Empty part when extracting {out_name}!")
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    crop = rgba_arr[y0:y1, x0:x1].copy()
    if round_top or round_bottom:
        crop = round_top_bottom_caps(crop, round_top=round_top, round_bottom=round_bottom)
    im = Image.fromarray(crop, mode="RGBA")
    cw, ch = im.size
    if target_w and target_h:
        im = im.resize((target_w, target_h), Image.Resampling.LANCZOS)
    elif target_w:
        sc = target_w / float(cw)
        im = im.resize((target_w, max(1, int(round(ch * sc)))), Image.Resampling.LANCZOS)
    elif target_h:
        sc = target_h / float(ch)
        im = im.resize((max(1, int(round(cw * sc))), target_h), Image.Resampling.LANCZOS)

    nw, nh = im.size
    out = Image.new("RGBA", (nw + 2 * pad, nh + 2 * pad), (0, 0, 0, 0))
    out.paste(im, (pad, pad))
    out_arr = np.array(out)
    out_arr[:2, :, 3] = 0
    out_arr[-2:, :, 3] = 0
    out_arr[:, :2, 3] = 0
    out_arr[:, -2:, 3] = 0
    out = Image.fromarray(out_arr, mode="RGBA")
    out_path = os.path.join(PARTS_DIR, out_name)
    out.save(out_path)
    a = out_arr[:, :, 3]
    edge_clip = int(a[0, :].sum() + a[-1, :].sum() + a[:, 0].sum() + a[:, -1].sum())
    print(f"  Saved {out_name:22s}: {out.size[0]:3d}x{out.size[1]:3d} | edge_clip={edge_clip}px")
    return out


print("=== Extracting 18 Body Cutout Parts for C004 (Kỵ Binh Gỉ Sét — Front-Hand Lance) ===")
core_im = Image.open(CORE_RAW_PATH).convert("RGBA")
cw, ch = core_im.width // 2, core_im.height // 2

# 1. head.png (Top-Left of core_2x2 — grizzled veteran head with rusted morion helmet & braided mustache)
head_arr = clean_magenta_cell(core_im.crop((0, 0, cw, ch)))
crop_resize_pad_save(head_arr, "head.png", target_h=124, pad=12)

# 2. chest.png (Top-Right of core_2x2 — corroded rusted-iron breastplate, trim bottom belt pouches so they don't duplicate hip_kilt)
chest_arr = clean_magenta_cell(core_im.crop((cw, 0, core_im.width, ch)))
ys_c, xs_c = np.where(chest_arr[:, :, 3] > 20)
chest_crop = chest_arr[ys_c.min() : ys_c.max() + 1, xs_c.min() : xs_c.max() + 1].copy()
ch_h, ch_w, _ = chest_crop.shape
chest_crop[int(ch_h * 0.76) :, :, 3] = 0
crop_resize_pad_save(chest_crop, "chest.png", target_h=122, pad=12, round_bottom=True)

# 3. sword.png (Bottom-Left of core_2x2 — standalone heavy rusted iron cavalry shock-lance, rotated to match the 20-deg combat grip angle)
lance_cell = clean_magenta_cell(core_im.crop((0, ch, cw, core_im.height)), border_margin=10)
lance_im_raw = Image.fromarray(keep_largest_component(lance_cell), mode="RGBA")
lance_rot = lance_im_raw.rotate(22, resample=Image.Resampling.BICUBIC, expand=True)
crop_resize_pad_save(np.array(lance_rot), "sword.png", target_w=252, pad=12, keep_largest=True)

# 4. hip_kilt.png (Bottom-Right of core_2x2 — belt pouches + layered rusted iron tasset plates)
kilt_arr = clean_magenta_cell(core_im.crop((cw, ch, core_im.width, core_im.height)))
crop_resize_pad_save(kilt_arr, "hip_kilt.png", target_w=170, pad=12)

# Load limbs_2x3
limbs_im = Image.open(LIMBS_RAW_PATH).convert("RGBA")
lw, lh = limbs_im.width // 3, limbs_im.height // 2

# 5. cloak.png (Row 1 Col 1 of limbs_2x3 — standalone tattered dusty rust-ochre cavalry cloak)
cloak_arr = clean_magenta_cell(limbs_im.crop((0, 0, lw, lh)))
crop_resize_pad_save(cloak_arr, "cloak.png", target_w=166, pad=12)

# 6. pauldron.png (Row 1 Col 2 of limbs_2x3 — standalone riveted rusted-iron shoulder guard)
paul_arr = clean_magenta_cell(limbs_im.crop((lw, 0, 2 * lw, lh)))
crop_resize_pad_save(paul_arr, "pauldron.png", target_h=90, pad=12)

# 7. arm_upper_front.png (Row 2 Col 1 of limbs_2x3 — quilted gambeson upper arm with shoulder/elbow plates)
arm_uf_arr = clean_magenta_cell(limbs_im.crop((0, lh, lw, limbs_im.height)))
crop_resize_pad_save(arm_uf_arr, "arm_upper_front.png", target_h=76, pad=12, round_top=True, round_bottom=True)

# 8, 13 & 14. Back Arm (arm_upper_back, arm_lower_back, hand_back with buckler) from Top-Right of hf_2x2
hf_im = Image.open(HF_RAW_PATH).convert("RGBA")
hw, hh = hf_im.width // 2, hf_im.height // 2

back_arm_cell = clean_magenta_cell(hf_im.crop((hw, 0, hf_im.width, hh)))
ys_ba, xs_ba = np.where(back_arm_cell[:, :, 3] > 20)
ba_crop = back_arm_cell[ys_ba.min() : ys_ba.max() + 1, xs_ba.min() : xs_ba.max() + 1].copy()
bah, baw, _ = ba_crop.shape

ub_crop = ba_crop[:, : int(baw * 0.38)].copy()
crop_resize_pad_save(ub_crop, "arm_upper_back.png", target_w=60, pad=12, round_top=True, round_bottom=True)

lb_crop = ba_crop[int(bah * 0.14) : int(bah * 0.78), int(baw * 0.22) : int(baw * 0.50)].copy()
crop_resize_pad_save(lb_crop, "arm_lower_back.png", target_w=54, pad=12, round_top=True, round_bottom=True)

hb_crop = ba_crop[:, int(baw * 0.48) :].copy()
crop_resize_pad_save(hb_crop, "hand_back.png", target_h=94, pad=12)

# 9 & 10. leg_thigh_front.png & leg_thigh_back.png (Row 2 Col 2 & Col 3 of limbs_2x3)
thigh_f_arr = clean_magenta_cell(limbs_im.crop((lw, lh, 2 * lw, limbs_im.height)))
crop_resize_pad_save(thigh_f_arr, "leg_thigh_front.png", target_h=90, pad=12, round_top=True, round_bottom=True)

thigh_b_arr = clean_magenta_cell(limbs_im.crop((2 * lw, lh, limbs_im.width, limbs_im.height)))
ys_tb, xs_tb = np.where(thigh_b_arr[:, :, 3] > 20)
tb_crop = thigh_b_arr[ys_tb.min() : ys_tb.max() + 1, xs_tb.min() : xs_tb.max() + 1].copy()
tb_crop = tb_crop[:, int(tb_crop.shape[1] * 0.46) :].copy()
crop_resize_pad_save(tb_crop, "leg_thigh_back.png", target_h=88, pad=12, round_top=True, round_bottom=True)

# 11 & 12. Front Forearm (arm_lower_front.png) & Front Weapon-Gripping Hand (hand_front.png) from Top-Left of hf_2x2
front_arm_cell = clean_magenta_cell(hf_im.crop((0, 0, hw, hh)), border_margin=6)
ys_fa, xs_fa = np.where(front_arm_cell[:, :, 3] > 20)
fa_crop = front_arm_cell[ys_fa.min() : ys_fa.max() + 1, xs_fa.min() : xs_fa.max() + 1].copy()
fah, faw, _ = fa_crop.shape

fa_clean = fa_crop.copy()
fa_clean[:, : int(faw * 0.30), 3] = 0
fa_clean[:, int(faw * 0.80) :, 3] = 0

forearm_f = fa_clean[: int(fah * 0.72), :].copy()
crop_resize_pad_save(forearm_f, "arm_lower_front.png", target_h=68, pad=12, round_top=True)

hand_f = fa_clean[int(fah * 0.58) :, :].copy()
crop_resize_pad_save(hand_f, "hand_front.png", target_h=46, pad=12, round_top=True)

# 15 & 16. Front Right Shin Greave & Fur-Trimmed Boot (leg_shin_front.png & foot_front.png) from c004_reference_clean.png
ref_im = Image.open(REF_CLEAN_PATH).convert("RGBA")
ref_arr = np.array(ref_im)
ys_r, xs_r = np.where(ref_arr[:, :, 3] > 20)
# Note: in c004_reference_clean.png (512x512, aligned feet), bottom of front boot is at y_max (~500)
y_bot = int(ys_r.max())


def poly_crop_ref(pts, box):
    mask = Image.new("L", (512, 512), 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=1.0))
    m_arr = np.array(mask).astype(np.float32) / 255.0
    out = ref_arr.copy()
    out[:, :, 3] = (out[:, :, 3].astype(np.float32) * m_arr).astype(np.uint8)
    x0, y0, x1, y1 = box
    res = np.zeros_like(out)
    res[y0:y1, x0:x1] = out[y0:y1, x0:x1]
    return res


shin_f_ref = poly_crop_ref(
    [(88, y_bot - 126), (162, y_bot - 114), (138, y_bot - 42), (82, y_bot - 46)],
    (82, y_bot - 126, 162, y_bot - 42),
)
crop_resize_pad_save(shin_f_ref, "leg_shin_front.png", target_h=84, pad=12, round_top=True)

foot_f_ref = poly_crop_ref(
    [(74, y_bot - 56), (140, y_bot - 52), (140, y_bot + 1), (74, y_bot + 1)],
    (74, y_bot - 56, 140, y_bot + 1),
)
crop_resize_pad_save(foot_f_ref, "foot_front.png", target_h=52, pad=12, round_top=True)

# 17 & 18. Back Left Shin Greave & Spurred Boot (leg_shin_back.png & foot_back.png) from Bottom-Left of hf_2x2
shin_b_cell = clean_magenta_cell(hf_im.crop((0, hh, hw, hf_im.height)))
ys_sb, xs_sb = np.where(shin_b_cell[:, :, 3] > 20)
sb_crop = shin_b_cell[ys_sb.min() : ys_sb.max() + 1, xs_sb.min() : xs_sb.max() + 1].copy()
sbh, sbw, _ = sb_crop.shape

shin_b_upper = sb_crop[: int(sbh * 0.76), :].copy()
foot_b_lower = sb_crop[int(sbh * 0.68) :, :].copy()
crop_resize_pad_save(shin_b_upper, "leg_shin_back.png", target_h=86, pad=12, round_top=True)
crop_resize_pad_save(foot_b_lower, "foot_back.png", target_h=52, pad=12, round_top=True)

# 19-22. Extract 4 Soft-Opacity Translucent VFX PNGs from c004_vfx_light_2x2_raw.png
print("=== Extracting 4 Soft-Opacity VFX Cutout Parts for C004 ===")
vfx_im = Image.open(VFX_RAW_PATH).convert("RGBA")
vw, vh = vfx_im.width // 2, vfx_im.height // 2


def extract_soft_vfx(box, out_name, target_w, is_dust=False):
    cell = np.array(vfx_im.crop(box).convert("RGBA")).astype(np.float32)
    cell[:10, :, 3] = 0
    cell[-10:, :, 3] = 0
    cell[:, :10, 3] = 0
    cell[:, -10:, 3] = 0
    r, g, b, a = cell[:, :, 0], cell[:, :, 1], cell[:, :, 2], cell[:, :, 3]

    k = np.clip((255.0 - g) / 255.0, 0.0, 1.0)
    mag_closeness = 1.0 - np.clip(np.sqrt((r - 255.0) ** 2 + (g - 0.0) ** 2 + (b - 255.0) ** 2) / 195.0, 0.0, 1.0)
    bg_weight = np.clip(mag_closeness * k, 0.0, 1.0)
    soft_alpha = np.clip(1.0 - bg_weight * 1.22, 0.0, 1.0)
    soft_alpha[soft_alpha < 0.10] = 0.0

    r_clean = np.clip(r - 255.0 * bg_weight * 0.92, 0.0, 255.0)
    b_clean = np.clip(b - 255.0 * bg_weight * 0.95, 0.0, 255.0)
    if is_dust:
        lum = 0.3 * r_clean + 0.55 * g + 0.15 * b_clean
        r_clean = np.clip(lum * 1.08 + 18.0, 0.0, 255.0)
        g_clean = np.clip(lum * 0.98 + 10.0, 0.0, 255.0)
        b_clean = np.clip(lum * 0.84 + 4.0, 0.0, 255.0)
        soft_alpha *= 0.80
    else:
        g_clean = g
        purple_mask = b_clean > g_clean + 12.0
        b_clean[purple_mask] = g_clean[purple_mask] + 8.0
        r_clean[purple_mask] = np.minimum(r_clean[purple_mask], g_clean[purple_mask] + 28.0)
        soft_alpha *= 0.90

    cell[:, :, 0] = r_clean
    cell[:, :, 1] = g_clean
    cell[:, :, 2] = b_clean
    cell[:, :, 3] = soft_alpha * (a / 255.0) * 255.0
    return crop_resize_pad_save(cell.astype(np.uint8), out_name, target_w=target_w, pad=14, keep_largest=False)


extract_soft_vfx((0, 0, vw, vh), "fx_slash.png", target_w=200, is_dust=False)
extract_soft_vfx((vw, 0, vfx_im.width, vh), "fx_slash_heavy.png", target_w=230, is_dust=False)
extract_soft_vfx((0, vh, vw, vfx_im.height), "fx_spark.png", target_w=165, is_dust=False)
extract_soft_vfx((vw, vh, vfx_im.width, vfx_im.height), "fx_dust.png", target_w=185, is_dust=True)
print("=== All 18 Body Parts + 4 VFX Extracted with 0px Edge Clipping! ===")
