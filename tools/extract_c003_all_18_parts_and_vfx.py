#!/usr/bin/env python3
"""
Extracts and audits all 18 isolated body parts + 4 soft-opacity VFX PNGs for C003 — Đao Phủ Đồi Thi:
- Follows the Front-Hand Weapon Grip Rule:
  Front Arm (UpperArm_L -> Forearm_L -> Hand_L -> Sword) holds the heavy iron executioner great-cleaver in the foreground!
  Back Arm (UpperArm_R -> Forearm_R -> Hand_R) is the secondary off-hand extended forward-right!
- Every single PNG is cleanly masked with rounded joint caps and padded with transparent margin so edge_clip = 0px.
"""
import os
import numpy as np
from PIL import Image, ImageFilter

HERO_DIR = "/Users/dochung/Desktop/card_g/assets/heroes/c003_dao_phu_doi_thi"
REF_CLEAN_PATH = os.path.join(HERO_DIR, "reference/c003_reference_clean.png")
CORE_RAW_PATH = os.path.join(HERO_DIR, "parts/c003_parts_core_2x2_raw.png")
LIMBS_RAW_PATH = os.path.join(HERO_DIR, "parts/c003_parts_limbs_2x3_raw.png")
HF_RAW_PATH = os.path.join(HERO_DIR, "parts/c003_parts_hands_feet_2x2_raw.png")
VFX_RAW_PATH = os.path.join(HERO_DIR, "vfx/c003_vfx_light_2x2_raw.png")
PARTS_DIR = os.path.join(HERO_DIR, "godot/parts")

os.makedirs(PARTS_DIR, exist_ok=True)


def clean_magenta_cell(cell_im, border_margin=12):
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


print("=== Extracting 18 Body Cutout Parts for C003 (Front-Hand Weapon Grip) ===")
core_im = Image.open(CORE_RAW_PATH).convert("RGBA")
cw, ch = core_im.width // 2, core_im.height // 2

# 1. head.png (Top-Left of core_2x2)
head_arr = clean_magenta_cell(core_im.crop((0, 0, cw, ch)))
crop_resize_pad_save(head_arr, "head.png", target_h=98, pad=12)

# 2. chest.png (Top-Right of core_2x2 — trim bottom apron fringe so it doesn't duplicate hip_kilt)
chest_arr = clean_magenta_cell(core_im.crop((cw, 0, core_im.width, ch)))
ys_c, xs_c = np.where(chest_arr[:, :, 3] > 20)
chest_crop = chest_arr[ys_c.min() : ys_c.max() + 1, xs_c.min() : xs_c.max() + 1].copy()
ch_h, ch_w, _ = chest_crop.shape
chest_crop[int(ch_h * 0.80) :, :, 3] = 0
crop_resize_pad_save(chest_crop, "chest.png", target_h=126, pad=12, round_bottom=True)

# 3. sword.png (Bottom-Left of core_2x2 — massive iron executioner great-cleaver held in FRONT HAND)
cleaver_arr = clean_magenta_cell(core_im.crop((0, ch, cw, core_im.height)))
crop_resize_pad_save(cleaver_arr, "sword.png", target_w=178, pad=14)

# 4. hip_kilt.png (Bottom-Right of core_2x2 — leather executioner apron-kilt with iron chain belt & pouch)
kilt_arr = clean_magenta_cell(core_im.crop((cw, ch, core_im.width, core_im.height)))
crop_resize_pad_save(kilt_arr, "hip_kilt.png", target_w=156, pad=12)

# Load limbs_2x3 and c003_reference_clean.png
limbs_im = Image.open(LIMBS_RAW_PATH).convert("RGBA")
lw, lh = limbs_im.width // 3, limbs_im.height // 2
ref_im = Image.open(REF_CLEAN_PATH).convert("RGBA")
ref_arr = np.array(ref_im)

def poly_crop_ref(pts, box):
    from PIL import ImageDraw
    mask = Image.new("L", (512, 512), 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=1.2))
    m_arr = np.array(mask).astype(np.float32) / 255.0
    out = ref_arr.copy()
    out[:, :, 3] = (out[:, :, 3].astype(np.float32) * m_arr).astype(np.uint8)
    x0, y0, x1, y1 = box
    res = np.zeros_like(out)
    res[y0:y1, x0:x1] = out[y0:y1, x0:x1]
    return res

# 5. cloak.png — Extract ONLY the tattered dark executioner shoulder cape wing (excluding the front arm!)
cloak_ref = poly_crop_ref(
    [(72, 175), (178, 168), (154, 212), (140, 276), (72, 276)],
    (72, 168, 178, 276),
)
cloak_im = crop_resize_pad_save(cloak_ref, "cloak.png", target_w=128, pad=12, keep_largest=True)

# 6. pauldron.png (Row 1 Col 2 of limbs_2x3 — spiked dark iron shoulder pauldron, trim right strap)
paul_arr = clean_magenta_cell(limbs_im.crop((lw, 0, 2 * lw, lh)))
ys_p, xs_p = np.where(paul_arr[:, :, 3] > 20)
paul_crop = paul_arr[ys_p.min() : ys_p.max() + 1, xs_p.min() : xs_p.max() + 1].copy()
ph_c, pw_c, _ = paul_crop.shape
paul_crop[:, int(pw_c * 0.82) :, 3] = 0
crop_resize_pad_save(paul_crop, "pauldron.png", target_h=78, pad=12)

# 7. arm_upper_front.png (Row 1 Col 3 of limbs_2x3)
arm_uf_arr = clean_magenta_cell(limbs_im.crop((2 * lw, 0, limbs_im.width, lh)))
crop_resize_pad_save(arm_uf_arr, "arm_upper_front.png", target_h=68, pad=12, round_top=True, round_bottom=True)

# 8. arm_upper_back.png (Row 2 Col 1 of limbs_2x3)
arm_ub_arr = clean_magenta_cell(limbs_im.crop((0, lh, lw, limbs_im.height)))
crop_resize_pad_save(arm_ub_arr, "arm_upper_back.png", target_h=66, pad=12, round_top=True, round_bottom=True)

# 9 & 10. leg_thigh_front.png & leg_thigh_back.png (Row 2 Col 2 & Col 3 of limbs_2x3)
thigh_f_arr = clean_magenta_cell(limbs_im.crop((lw, lh, 2 * lw, limbs_im.height)))
crop_resize_pad_save(thigh_f_arr, "leg_thigh_front.png", target_h=88, pad=12, round_top=True, round_bottom=True)

thigh_b_arr = clean_magenta_cell(limbs_im.crop((2 * lw, lh, limbs_im.width, limbs_im.height)))
crop_resize_pad_save(thigh_b_arr, "leg_thigh_back.png", target_h=86, pad=12, round_top=True, round_bottom=True)

# 11 & 12. Front Forearm (arm_lower_front.png) & Front Weapon-Gripping Hand (hand_front.png) from c003_reference_clean.png
forearm_f_ref = poly_crop_ref(
    [(142, 218), (186, 218), (176, 286), (138, 286)],
    (138, 218, 186, 286),
)
crop_resize_pad_save(forearm_f_ref, "arm_lower_front.png", target_h=66, pad=12, round_top=True)

hand_f_ref = poly_crop_ref(
    [(136, 276), (176, 276), (178, 314), (136, 314)],
    (136, 276, 178, 314),
)
crop_resize_pad_save(hand_f_ref, "hand_front.png", target_h=44, pad=12, round_top=True)

# 13 & 14. Back Forearm (arm_lower_back.png) & Back Secondary Fist (hand_back.png) from c003_reference_clean.png
forearm_b_ref = poly_crop_ref(
    [(310, 200), (378, 224), (366, 256), (302, 232)],
    (302, 200, 378, 256),
)
crop_resize_pad_save(forearm_b_ref, "arm_lower_back.png", target_w=68, pad=12, round_top=True)

hand_b_ref = poly_crop_ref(
    [(362, 228), (398, 234), (398, 266), (358, 262)],
    (358, 228, 398, 266),
)
crop_resize_pad_save(hand_b_ref, "hand_back.png", target_w=42, pad=12, round_top=True)

# 15 & 16. Front Shin (leg_shin_front.png) & Front Foot (foot_front.png) from c003_reference_clean.png
shin_f_ref = poly_crop_ref(
    [(150, 358), (210, 358), (190, 456), (144, 456)],
    (144, 358, 210, 456),
)
crop_resize_pad_save(shin_f_ref, "leg_shin_front.png", target_h=96, pad=12, round_top=True)

foot_f_ref = poly_crop_ref(
    [(138, 446), (184, 446), (182, 498), (138, 498)],
    (138, 446, 184, 498),
)
crop_resize_pad_save(foot_f_ref, "foot_front.png", target_h=52, pad=12, round_top=True)

# 17 & 18. Back Shin (leg_shin_back.png) & Back Foot (foot_back.png) from c003_reference_clean.png
shin_b_ref = poly_crop_ref(
    [(298, 350), (354, 350), (352, 454), (298, 454)],
    (298, 350, 354, 454),
)
crop_resize_pad_save(shin_b_ref, "leg_shin_back.png", target_h=98, pad=12, round_top=True)

foot_b_ref = poly_crop_ref(
    [(306, 444), (376, 444), (376, 490), (306, 490)],
    (306, 444, 376, 490),
)
crop_resize_pad_save(foot_b_ref, "foot_back.png", target_w=72, pad=12, round_top=True)

# Save clean boxless c003_parts_hands_feet_2x2_raw.png on #FF00FF
clean_hf_sheet = Image.new("RGB", (1024, 1024), (255, 0, 255))
def paste_part_on_mag(dst_rgb, part_png_name, center_xy, scale=2.2):
    im = Image.open(os.path.join(PARTS_DIR, part_png_name)).convert("RGBA")
    im = im.resize((int(round(im.width * scale)), int(round(im.height * scale))), Image.Resampling.LANCZOS)
    bg = Image.new("RGBA", im.size, (255, 0, 255, 255))
    bg.alpha_composite(im)
    cx, cy = center_xy
    dst_rgb.paste(bg.convert("RGB"), (cx - im.width // 2, cy - im.height // 2))

paste_part_on_mag(clean_hf_sheet, "arm_lower_front.png", (210, 220))
paste_part_on_mag(clean_hf_sheet, "hand_front.png", (330, 310))
paste_part_on_mag(clean_hf_sheet, "arm_lower_back.png", (720, 220))
paste_part_on_mag(clean_hf_sheet, "hand_back.png", (850, 300))
paste_part_on_mag(clean_hf_sheet, "leg_shin_front.png", (220, 720))
paste_part_on_mag(clean_hf_sheet, "foot_front.png", (340, 820))
paste_part_on_mag(clean_hf_sheet, "leg_shin_back.png", (710, 720))
paste_part_on_mag(clean_hf_sheet, "foot_back.png", (850, 820))
clean_hf_sheet.save(HF_RAW_PATH)
print("Saved clean boxless c003_parts_hands_feet_2x2_raw.png")


# --- Extract 4 Soft-Opacity Translucent VFX PNGs ---
print("=== Extracting 4 Soft-Opacity VFX PNGs for C003 ===")
vfx_im = Image.open(VFX_RAW_PATH).convert("RGB")
vw, vh = vfx_im.width // 2, vfx_im.height // 2

vfx_cells = [
    ("fx_slash", (0, 0, vw, vh), 185, 0.72),
    ("fx_slash_heavy", (vw, 0, vfx_im.width, vh), 205, 0.78),
    ("fx_spark", (0, vh, vw, vfx_im.height), 145, 0.84),
    ("fx_dust", (vw, vh, vfx_im.width, vfx_im.height), 175, 0.62),
]

for fx_name, box, target_max_dim, max_alpha_scale in vfx_cells:
    cell_rgb = np.array(vfx_im.crop(box)).astype(np.float32)
    ch_i, cw_i, _ = cell_rgb.shape
    m = 16
    cell_rgb[:m, :] = [255, 0, 255]
    cell_rgb[-m:, :] = [255, 0, 255]
    cell_rgb[:, :m] = [255, 0, 255]
    cell_rgb[:, -m:] = [255, 0, 255]

    r, g, b = cell_rgb[:, :, 0], cell_rgb[:, :, 1], cell_rgb[:, :, 2]
    mag_ness = (np.minimum(r, b) - g) / 255.0
    alpha_raw = 1.0 - np.clip(mag_ness, 0.0, 1.0)
    dist_mag = np.sqrt((r - 255.0) ** 2 + (g - 0.0) ** 2 + (b - 255.0) ** 2) / 441.67
    alpha = np.maximum(alpha_raw, np.clip((dist_mag - 0.14) * 1.45, 0.0, 1.0))
    alpha = np.clip((alpha - 0.08) / 0.92, 0.0, 1.0)
    alpha = (alpha ** 1.15) * max_alpha_scale

    safe_a = np.maximum(alpha, 0.05)
    fg_r = np.clip((r - (1.0 - alpha) * 255.0) / safe_a, 0.0, 255.0)
    fg_g = np.clip(g / safe_a, 0.0, 255.0)
    fg_b = np.clip((b - (1.0 - alpha) * 255.0) / safe_a, 0.0, 255.0)

    if fx_name in ("fx_slash", "fx_slash_heavy"):
        lum = 0.299 * fg_r + 0.587 * fg_g + 0.114 * fg_b
        boost = np.maximum(lum, 205.0)
        fg_r = 0.35 * fg_r + 0.65 * boost
        fg_g = 0.35 * fg_g + 0.65 * boost
        fg_b = np.minimum(255.0, (0.35 * fg_b + 0.65 * boost) * 1.04)
    elif fx_name == "fx_dust":
        lum = 0.30 * fg_r + 0.50 * fg_g + 0.20 * fg_b
        fg_r = np.clip(lum * 1.06 + 18.0, 0.0, 255.0)
        fg_g = np.clip(lum * 0.98 + 12.0, 0.0, 255.0)
        fg_b = np.clip(lum * 0.90 + 8.0, 0.0, 255.0)

    a_u8 = np.clip(alpha * 255.0, 0, 255).astype(np.uint8)
    a_u8 = np.array(Image.fromarray(a_u8, mode="L").filter(ImageFilter.GaussianBlur(radius=1.0)))

    rgba = np.stack([fg_r.astype(np.uint8), fg_g.astype(np.uint8), fg_b.astype(np.uint8), a_u8], axis=-1)
    ys, xs = np.where(rgba[:, :, 3] > 8)
    crop = rgba[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]
    im = Image.fromarray(crop, mode="RGBA")
    sc = target_max_dim / float(max(im.width, im.height))
    im = im.resize((max(1, int(round(im.width * sc))), max(1, int(round(im.height * sc)))), Image.Resampling.LANCZOS)

    pad = 12
    out = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    out.paste(im, (pad, pad))
    out_arr = np.array(out)
    out_arr[:2, :, 3] = 0
    out_arr[-2:, :, 3] = 0
    out_arr[:, :2, 3] = 0
    out_arr[:, -2:, 3] = 0
    out = Image.fromarray(out_arr, mode="RGBA")
    out.save(os.path.join(PARTS_DIR, f"{fx_name}.png"))

    nz_a = out_arr[:, :, 3][out_arr[:, :, 3] > 0]
    mean_op = float(nz_a.mean() / 255.0) * 100.0 if len(nz_a) else 0.0
    max_op = float(nz_a.max() / 255.0) * 100.0 if len(nz_a) else 0.0
    ec = int(out_arr[0, :, 3].sum() + out_arr[-1, :, 3].sum() + out_arr[:, 0, 3].sum() + out_arr[:, -1, 3].sum())
    print(f"  VFX {fx_name:15s}: {out.width:3d}x{out.height:3d} | mean_alpha={mean_op:.0f}%, max_alpha={max_op:.0f}% | edge_clip={ec}px")
