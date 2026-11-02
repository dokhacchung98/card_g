#!/usr/bin/env python3
"""
Extracts and audits all 18 isolated body parts + 4 soft-opacity VFX PNGs for C002 — Nỏ Thủ Câm Lặng:
Every single PNG is cleanly masked with rounded joint caps and padded with transparent margin so edge_clip = 0px.
"""
import os
import numpy as np
from PIL import Image, ImageFilter

HERO_DIR = "/Users/dochung/Desktop/card_g/assets/heroes/c002_no_thu_cam_lang"
REF_CLEAN_PATH = os.path.join(HERO_DIR, "reference/c002_reference_clean.png")
CORE_RAW_PATH = os.path.join(HERO_DIR, "parts/c002_parts_core_2x2_raw.png")
LIMBS_RAW_PATH = os.path.join(HERO_DIR, "parts/c002_parts_limbs_2x3_raw.png")
HF_RAW_PATH = os.path.join(HERO_DIR, "parts/c002_parts_hands_feet_2x2_raw.png")
VFX_RAW_PATH = os.path.join(HERO_DIR, "vfx/c002_vfx_light_2x2_raw.png")
PARTS_DIR = os.path.join(HERO_DIR, "godot/parts")
C001_HF_FIX_PATH = "/Users/dochung/Desktop/card_g/assets/heroes/c001_hac_kiem_tan_binh/parts/c001_parts_hands_feet_fix_2x2_raw.png"

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
                sub_a = alpha[y_min:y_max, x_min:x_max]
                sub_v = visited[y_min:y_max, x_min:x_max]
                ny_arr, nx_arr = np.where(sub_a & ~sub_v)
                for ny, nx in zip(ny_arr, nx_arr):
                    ry, rx = y_min + int(ny), x_min + int(nx)
                    visited[ry, rx] = True
                    stack.append((ry, rx))
            if len(coords) > best_count:
                best_count = len(coords)
                best_coords = coords
    out = np.zeros_like(rgba_arr)
    if best_coords:
        ys, xs = zip(*best_coords)
        out[ys, xs] = rgba_arr[ys, xs]
    return out


def round_top_cap(rgba_arr, cap_frac=0.18):
    """Softens flat horizontal top cuts into a natural rounded joint cap."""
    out = rgba_arr.copy()
    ys, xs = np.where(out[:, :, 3] > 15)
    if len(ys) == 0:
        return out
    y0, y1 = int(ys.min()), int(ys.max())
    x0, x1 = int(xs.min()), int(xs.max())
    h = max(1, y1 - y0 + 1)
    w = max(1, x1 - x0 + 1)
    cap_h = max(4, int(round(h * cap_frac)))
    cx = 0.5 * (x0 + x1)
    rx = 0.52 * w
    for y in range(y0, min(y1, y0 + cap_h)):
        dy = (y0 + cap_h - y) / float(cap_h)
        max_dx = rx * np.sqrt(max(0.0, 1.0 - dy * dy * 0.75))
        for x in range(x0, x1 + 1):
            dist = abs(x - cx)
            if dist > max_dx:
                fade = np.clip(1.0 - (dist - max_dx) / 4.0, 0.0, 1.0)
                out[y, x, 3] = int(out[y, x, 3] * fade)
    return out


def crop_resize_pad_save(rgba_arr, out_name, target_h=None, target_w=None, pad=14, keep_largest=True, round_top=False):
    if keep_largest:
        rgba_arr = keep_largest_component(rgba_arr)
    if round_top:
        rgba_arr = round_top_cap(rgba_arr, cap_frac=0.18)
    ys, xs = np.where(rgba_arr[:, :, 3] > 15)
    crop = Image.fromarray(rgba_arr, mode="RGBA").crop(
        (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    )
    if target_h is not None and target_w is not None:
        crop = crop.resize((target_w, target_h), Image.Resampling.LANCZOS)
    elif target_h is not None:
        sc = target_h / float(crop.height)
        crop = crop.resize((max(1, int(round(crop.width * sc))), target_h), Image.Resampling.LANCZOS)
    elif target_w is not None:
        sc = target_w / float(crop.width)
        crop = crop.resize((target_w, max(1, int(round(crop.height * sc)))), Image.Resampling.LANCZOS)

    out = Image.new("RGBA", (crop.width + 2 * pad, crop.height + 2 * pad), (0, 0, 0, 0))
    out.paste(crop, (pad, pad))
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


print("=== Extracting 18 Body Cutout Parts for C002 ===")
for ref_p in [REF_CLEAN_PATH, os.path.join(HERO_DIR, "reference/processed/idle-1.png"), os.path.join(HERO_DIR, "reference/processed/spritesheet.png")]:
    if os.path.exists(ref_p):
        r_im = Image.open(ref_p).convert("RGBA")
        r_arr = np.array(r_im).astype(np.float32)
        rr, rg, rb, ra = r_arr[:, :, 0], r_arr[:, :, 1], r_arr[:, :, 2], r_arr[:, :, 3]
        mdom = (rr + rb) / 2.0 - rg
        spill = (ra > 0) & (mdom > 14.0)
        if spill.any():
            rr[spill] = np.minimum(rr[spill], rg[spill] + 10.0)
            rb[spill] = np.minimum(rb[spill], rg[spill] + 8.0)
            r_arr[:, :, 0], r_arr[:, :, 2] = rr, rb
            Image.fromarray(np.clip(r_arr, 0, 255).astype(np.uint8), mode="RGBA").save(ref_p)

core_im = Image.open(CORE_RAW_PATH).convert("RGBA")
cw, ch = core_im.width // 2, core_im.height // 2

# 1. head.png (Top-Left of core_2x2)
head_arr = clean_magenta_cell(core_im.crop((0, 0, cw, ch)))
crop_resize_pad_save(head_arr, "head.png", target_h=96, pad=12)

# 2. chest.png (Top-Right of core_2x2 — strictly sleeveless brigandine vest)
chest_arr = clean_magenta_cell(core_im.crop((cw, 0, core_im.width, ch)))
crop_resize_pad_save(chest_arr, "chest.png", target_h=128, pad=12)

# 3. sword.png & crossbow.png (Bottom-Left of core_2x2 — isolated heavy wooden-and-iron crossbow)
xbow_arr = clean_magenta_cell(core_im.crop((0, ch, cw, core_im.height)))
xbow_im = crop_resize_pad_save(xbow_arr, "sword.png", target_w=192, pad=14)
xbow_im.save(os.path.join(PARTS_DIR, "crossbow.png"))

# 4. hip_kilt.png (Bottom-Right of core_2x2 — leather tasset belt kilt with bolt pouch)
kilt_arr = clean_magenta_cell(core_im.crop((cw, ch, core_im.width, core_im.height)))
crop_resize_pad_save(kilt_arr, "hip_kilt.png", target_w=142, pad=12)

# Load limbs_2x3
limbs_im = Image.open(LIMBS_RAW_PATH).convert("RGBA")
lw, lh = limbs_im.width // 3, limbs_im.height // 2

# 5. cloak.png (Row 1 Col 1 of limbs_2x3 — intact tattered dark scout cloak + quiver of bolts!)
cloak_arr = clean_magenta_cell(limbs_im.crop((0, 0, lw, lh)))
crop_resize_pad_save(cloak_arr, "cloak.png", target_h=214, pad=12, keep_largest=True)

# 6. pauldron.png (Row 1 Col 2 of limbs_2x3 — trim right strap so only shoulder armor dome remains)
paul_arr = clean_magenta_cell(limbs_im.crop((lw, 0, 2 * lw, lh)))
ys_p, xs_p = np.where(paul_arr[:, :, 3] > 20)
paul_crop = paul_arr[ys_p.min() : ys_p.max() + 1, xs_p.min() : xs_p.max() + 1].copy()
ph_c, pw_c, _ = paul_crop.shape
paul_crop[:, int(pw_c * 0.54) :, 3] = 0
crop_resize_pad_save(paul_crop, "pauldron.png", target_h=64, pad=12)

# 7 & 8. Upper arms (arm_upper_front.png & arm_upper_back.png)
ua_f_raw = clean_magenta_cell(limbs_im.crop((2 * lw, 0, 3 * lw, lh)))
ys_u, xs_u = np.where(ua_f_raw[:, :, 3] > 20)
ua_f_crop = ua_f_raw[ys_u.min() : ys_u.max() + 1, xs_u.min() : xs_u.max() + 1].copy()
crop_resize_pad_save(ua_f_crop[: int(ua_f_crop.shape[0] * 0.56), :, :], "arm_upper_front.png", target_h=68, pad=12, round_top=True)

ua_b_raw = clean_magenta_cell(limbs_im.crop((0, lh, lw, 2 * lh)))
ys_ub, xs_ub = np.where(ua_b_raw[:, :, 3] > 20)
ua_b_crop = ua_b_raw[ys_ub.min() : ys_ub.max() + 1, xs_ub.min() : xs_ub.max() + 1].copy()
crop_resize_pad_save(ua_b_crop[: int(ua_b_crop.shape[0] * 0.56), :, :], "arm_upper_back.png", target_h=66, pad=12, round_top=True)

# 9 & 10. Closer Right Forearm (arm_lower_front.png) & Right Hand (hand_front.png)
ref_im = Image.open(REF_CLEAN_PATH).convert("RGBA")
ref_arr = np.array(ref_im)
forearm_f_arr = ref_arr[234:296, 108:145].copy()
hand_f_arr = ref_arr[284:328, 108:142].copy()
crop_resize_pad_save(forearm_f_arr, "arm_lower_front.png", target_h=58, pad=12, round_top=True)
crop_resize_pad_save(hand_f_arr, "hand_front.png", target_h=44, pad=12, round_top=True)

# 11 & 12. Farther Left Forearm (arm_lower_back.png) & Left Gripping Fist (hand_back.png)
# Use the high-res 2x2 hands/feet sheet
c001_hf = Image.open(C001_HF_FIX_PATH).convert("RGBA")
chw, chh = c001_hf.width // 2, c001_hf.height // 2
c_arm_back = clean_magenta_cell(c001_hf.crop((chw, 0, c001_hf.width, chh)), border_margin=18)
ys_ab, xs_ab = np.where(c_arm_back[:, :, 3] > 20)
ab_crop = c_arm_back[ys_ab.min() : ys_ab.max() + 1, xs_ab.min() : xs_ab.max() + 1].copy()
ab_im = Image.fromarray(ab_crop).resize(
    (int(round(ab_crop.shape[1] * 86.0 / ab_crop.shape[0])), 86), Image.Resampling.LANCZOS
)
ab_scaled = np.array(ab_im)
hab, wab, _ = ab_scaled.shape
yy_ab, xx_ab = np.mgrid[0:hab, 0:wab]
proj01 = (1.0 - xx_ab / float(wab)) * 0.72 + (1.0 - yy_ab / float(hab)) * 0.69
ab_scaled[proj01 > 0.96, 3] = 0
wrist_split = (yy_ab / float(hab)) + (xx_ab / float(wab)) * 0.28

forearm_b_arr = ab_scaled.copy()
forearm_b_arr[wrist_split > 0.85, 3] = 0
hand_b_arr = ab_scaled.copy()
hand_b_arr[wrist_split < 0.73, 3] = 0

crop_resize_pad_save(forearm_b_arr, "arm_lower_back.png", pad=12)
crop_resize_pad_save(hand_b_arr, "hand_back.png", pad=12)

# 13 & 14. Thighs (leg_thigh_front.png & leg_thigh_back.png) from limbs_2x3 Row 2 Col 2 & Col 3
thigh_f_raw = clean_magenta_cell(limbs_im.crop((lw, lh, 2 * lw, 2 * lh)))
crop_resize_pad_save(thigh_f_raw, "leg_thigh_front.png", target_h=92, pad=12, round_top=True)

thigh_b_raw = clean_magenta_cell(limbs_im.crop((2 * lw, lh, 3 * lw, 2 * lh)))
crop_resize_pad_save(thigh_b_raw, "leg_thigh_back.png", target_h=90, pad=12, round_top=True)

# 15 & 16. Closer Right Shin (leg_shin_front.png) & Right 3/4 Front Boot (foot_front.png)
shin_f_arr = ref_arr[346:448, 126:196].copy()
foot_f_arr = ref_arr[438:496, 124:174].copy()
crop_resize_pad_save(shin_f_arr, "leg_shin_front.png", target_h=98, pad=12, round_top=True)
crop_resize_pad_save(foot_f_arr, "foot_front.png", target_h=54, pad=12, round_top=True)

# 17 & 18. Farther Left Shin (leg_shin_back.png) & Left 3/4 Profile Boot (foot_back.png)
c_leg_back = clean_magenta_cell(c001_hf.crop((chw, chh, c001_hf.width, c001_hf.height)), border_margin=18)
ys_lb, xs_lb = np.where(c_leg_back[:, :, 3] > 20)
lb_crop = c_leg_back[ys_lb.min() : ys_lb.max() + 1, xs_lb.min() : xs_lb.max() + 1].copy()
lb_im = Image.fromarray(lb_crop).resize(
    (int(round(lb_crop.shape[1] * 134.0 / lb_crop.shape[0])), 134), Image.Resampling.LANCZOS
)
lb_scaled = np.array(lb_im)
shin_b_arr = lb_scaled.copy()
shin_b_arr[100:, :, 3] = 0
foot_b_arr = lb_scaled.copy()
foot_b_arr[:88, :, 3] = 0

crop_resize_pad_save(shin_b_arr, "leg_shin_back.png", pad=12)
crop_resize_pad_save(foot_b_arr, "foot_back.png", pad=12)

# Rebuild c002_parts_hands_feet_2x2_raw.png cleanly on pure #FF00FF with rounded caps and zero grid lines
clean_hf_sheet = Image.new("RGB", (1024, 1024), (255, 0, 255))
def paste_rgba_on_mag(dst_rgb, rgba_slice, center_xy, target_h=340):
    ys, xs = np.where(rgba_slice[:, :, 3] > 20)
    im = Image.fromarray(rgba_slice[ys.min():ys.max()+1, xs.min():xs.max()+1], mode="RGBA")
    sc = target_h / float(im.height)
    im = im.resize((int(round(im.width * sc)), target_h), Image.Resampling.LANCZOS)
    bg = Image.new("RGBA", im.size, (255, 0, 255, 255))
    bg.alpha_composite(im)
    cx, cy = center_xy
    dst_rgb.paste(bg.convert("RGB"), (cx - im.width // 2, cy - im.height // 2))

paste_rgba_on_mag(clean_hf_sheet, round_top_cap(ref_arr[234:328, 108:145].copy(), 0.18), (256, 256), target_h=320)
paste_rgba_on_mag(clean_hf_sheet, ab_crop, (768, 256), target_h=320)
paste_rgba_on_mag(clean_hf_sheet, round_top_cap(ref_arr[346:496, 124:196].copy(), 0.16), (256, 768), target_h=360)
paste_rgba_on_mag(clean_hf_sheet, lb_crop, (768, 768), target_h=360)
clean_hf_sheet.save(HF_RAW_PATH)
print("Updated clean boxless c002_parts_hands_feet_2x2_raw.png")

# --- Extract 4 Soft-Opacity Translucent VFX PNGs ---
print("=== Extracting 4 Soft-Opacity VFX PNGs ===")
vfx_raw = Image.open(VFX_RAW_PATH).convert("RGB")
vw, vh = vfx_raw.width // 2, vfx_raw.height // 2


def unmix_magenta_soft_rgba(cell_rgb, max_alpha_scale=0.80, noise_floor=0.06, tint_rgb=None):
    arr = np.asarray(cell_rgb, dtype=np.float32)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    mag_purity = np.clip((np.minimum(r, b) - g) / 255.0, 0.0, 1.0)
    alpha_raw = 1.0 - mag_purity
    alpha_clean = np.clip((alpha_raw - noise_floor) / (1.0 - noise_floor), 0.0, 1.0)

    h, w = alpha_clean.shape
    yy, xx = np.mgrid[0:h, 0:w]
    dist_edge = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy))
    edge_fade = np.clip(dist_edge / 28.0, 0.0, 1.0)
    alpha_clean = alpha_clean * edge_fade

    alpha_pil = Image.fromarray((alpha_clean * 255.0).astype(np.uint8), mode="L")
    alpha_pil = alpha_pil.filter(ImageFilter.GaussianBlur(radius=1.0))
    alpha_smooth = np.asarray(alpha_pil, dtype=np.float32) / 255.0

    denom = np.maximum(alpha_raw, 0.08)
    fg_r = np.clip((r - 255.0 * (1.0 - alpha_raw)) / denom, 0.0, 255.0)
    fg_g = np.clip(g / denom, 0.0, 255.0)
    fg_b = np.clip((b - 255.0 * (1.0 - alpha_raw)) / denom, 0.0, 255.0)

    excess_rb = np.maximum(0.0, np.minimum(fg_r, fg_b) - fg_g)
    fg_r = np.clip(fg_r - excess_rb * 0.85, 0.0, 255.0)
    fg_b = np.clip(fg_b - excess_rb * 0.75, 0.0, 255.0)

    if tint_rgb is not None:
        tr, tg, tb, blend_w = tint_rgb
        lum = (0.299 * fg_r + 0.587 * fg_g + 0.114 * fg_b) / 255.0
        fg_r = fg_r * (1.0 - blend_w) + np.clip(tr * (0.65 + 0.45 * lum), 0, 255) * blend_w
        fg_g = fg_g * (1.0 - blend_w) + np.clip(tg * (0.65 + 0.45 * lum), 0, 255) * blend_w
        fg_b = fg_b * (1.0 - blend_w) + np.clip(tb * (0.65 + 0.45 * lum), 0, 255) * blend_w

    final_alpha = np.clip(alpha_smooth * max_alpha_scale * 255.0, 0.0, 255.0).astype(np.uint8)
    final_alpha[final_alpha < 4] = 0

    rgba = np.stack([fg_r.astype(np.uint8), fg_g.astype(np.uint8), fg_b.astype(np.uint8), final_alpha], axis=-1)
    ys, xs = np.where(final_alpha > 4)
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    return Image.fromarray(rgba[y0:y1, x0:x1], mode="RGBA")


c1 = vfx_raw.crop((0, 0, vw, vh)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
fx_slash = unmix_magenta_soft_rgba(c1, max_alpha_scale=0.72, noise_floor=0.06, tint_rgb=(235, 245, 255, 0.65))
fx_slash.thumbnail((172, 156), Image.Resampling.LANCZOS)
can_slash = Image.new("RGBA", (fx_slash.width + 16, fx_slash.height + 16), (0, 0, 0, 0))
can_slash.alpha_composite(fx_slash, (8, 8))
can_slash.save(os.path.join(PARTS_DIR, "fx_slash.png"))

c2 = vfx_raw.crop((vw, 0, vfx_raw.width, vh)).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
fx_heavy = unmix_magenta_soft_rgba(c2, max_alpha_scale=0.78, noise_floor=0.06, tint_rgb=(225, 242, 255, 0.65))
fx_heavy.thumbnail((188, 168), Image.Resampling.LANCZOS)
can_heavy = Image.new("RGBA", (fx_heavy.width + 16, fx_heavy.height + 16), (0, 0, 0, 0))
can_heavy.alpha_composite(fx_heavy, (8, 8))
can_heavy.save(os.path.join(PARTS_DIR, "fx_slash_heavy.png"))

c3 = vfx_raw.crop((0, vh, vw, vfx_raw.height))
fx_spark = unmix_magenta_soft_rgba(c3, max_alpha_scale=0.82, noise_floor=0.08, tint_rgb=(255, 224, 150, 0.70))
fx_spark.thumbnail((140, 140), Image.Resampling.LANCZOS)
can_spark = Image.new("RGBA", (fx_spark.width + 16, fx_spark.height + 16), (0, 0, 0, 0))
can_spark.alpha_composite(fx_spark, (8, 8))
can_spark.save(os.path.join(PARTS_DIR, "fx_spark.png"))

c4 = vfx_raw.crop((vw, vh, vfx_raw.width, vfx_raw.height))
fx_dust = unmix_magenta_soft_rgba(c4, max_alpha_scale=0.62, noise_floor=0.08, tint_rgb=(195, 188, 176, 0.60))
fx_dust.thumbnail((168, 114), Image.Resampling.LANCZOS)
can_dust = Image.new("RGBA", (fx_dust.width + 16, fx_dust.height + 16), (0, 0, 0, 0))
can_dust.alpha_composite(fx_dust, (8, 8))
can_dust.save(os.path.join(PARTS_DIR, "fx_dust.png"))

for name in ["fx_slash", "fx_slash_heavy", "fx_spark", "fx_dust"]:
    im = Image.open(os.path.join(PARTS_DIR, f"{name}.png")).convert("RGBA")
    a = np.array(im)[:, :, 3]
    nonzero = a[a > 0]
    edge_clip = int(a[0, :].sum() + a[-1, :].sum() + a[:, 0].sum() + a[:, -1].sum())
    print(
        f"  VFX {name:16s}: {im.width:3d}x{im.height:3d} | mean_alpha={nonzero.mean()/2.55:.0f}%, max_alpha={nonzero.max()/2.55:.0f}% | edge_clip={edge_clip}px"
    )
