#!/usr/bin/env python3
"""
Extracts 4 lightweight, soft-opacity translucent VFX PNGs from c001_vfx_light_2x2_raw.png
using exact magenta (#FF00FF) alpha unmixing so the PNGs have smooth translucent opacity
(zero dark outlines, zero magenta spill, and edge_clip = 0px).
"""
import os
import numpy as np
from PIL import Image, ImageFilter

HERO_DIR = "/Users/dochung/Desktop/card_g/assets/heroes/c001_hac_kiem_tan_binh"
RAW_VFX_PATH = os.path.join(HERO_DIR, "vfx/c001_vfx_light_2x2_raw.png")
PARTS_DIR = os.path.join(HERO_DIR, "godot/parts")

raw_im = Image.open(RAW_VFX_PATH).convert("RGB")
W, H = raw_im.size
cw, ch = W // 2, H // 2


def unmix_magenta_soft_rgba(cell_rgb, max_alpha_scale=0.80, noise_floor=0.06, tint_rgb=None):
    """
    Unmixes foreground RGB and continuous soft Alpha from a #FF00FF (255, 0, 255) background.
    """
    arr = np.asarray(cell_rgb, dtype=np.float32)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

    # How close is each pixel to pure #FF00FF?
    # Pure magenta has R~255, G~0, B~255 => (min(R,B) - G) / 255 is 1.0
    mag_purity = np.clip((np.minimum(r, b) - g) / 255.0, 0.0, 1.0)
    alpha_raw = 1.0 - mag_purity

    # Remove faint JPEG/WebP background compression noise
    alpha_clean = np.clip((alpha_raw - noise_floor) / (1.0 - noise_floor), 0.0, 1.0)

    # Feather near cell boundaries (within 28px of cell border) so wisps never clip
    h, w = alpha_clean.shape
    yy, xx = np.mgrid[0:h, 0:w]
    dist_edge = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy))
    edge_fade = np.clip(dist_edge / 28.0, 0.0, 1.0)
    alpha_clean = alpha_clean * edge_fade

    # Smooth alpha slightly for silky soft opacity gradient
    alpha_pil = Image.fromarray((alpha_clean * 255.0).astype(np.uint8), mode="L")
    alpha_pil = alpha_pil.filter(ImageFilter.GaussianBlur(radius=1.0))
    alpha_smooth = np.asarray(alpha_pil, dtype=np.float32) / 255.0

    # Un-premultiply foreground color from (255, 0, 255) background
    denom = np.maximum(alpha_raw, 0.08)
    fg_r = np.clip((r - 255.0 * (1.0 - alpha_raw)) / denom, 0.0, 255.0)
    fg_g = np.clip(g / denom, 0.0, 255.0)
    fg_b = np.clip((b - 255.0 * (1.0 - alpha_raw)) / denom, 0.0, 255.0)

    # Suppress any residual pink/magenta saturation in semi-transparent fringes
    excess_rb = np.maximum(0.0, np.minimum(fg_r, fg_b) - fg_g)
    fg_r = np.clip(fg_r - excess_rb * 0.85, 0.0, 255.0)
    fg_b = np.clip(fg_b - excess_rb * 0.75, 0.0, 255.0)

    if tint_rgb is not None:
        # Blend foreground softly toward clean target palette (e.g. cool silver-white for air slash)
        tr, tg, tb, blend_w = tint_rgb
        lum = (0.299 * fg_r + 0.587 * fg_g + 0.114 * fg_b) / 255.0
        fg_r = fg_r * (1.0 - blend_w) + np.clip(tr * (0.65 + 0.45 * lum), 0, 255) * blend_w
        fg_g = fg_g * (1.0 - blend_w) + np.clip(tg * (0.65 + 0.45 * lum), 0, 255) * blend_w
        fg_b = fg_b * (1.0 - blend_w) + np.clip(tb * (0.65 + 0.45 * lum), 0, 255) * blend_w

    # Apply soft opacity cap so the PNG itself is lightweight and semi-transparent
    final_alpha = np.clip(alpha_smooth * max_alpha_scale * 255.0, 0.0, 255.0).astype(np.uint8)
    final_alpha[final_alpha < 4] = 0

    rgba = np.stack([
        fg_r.astype(np.uint8),
        fg_g.astype(np.uint8),
        fg_b.astype(np.uint8),
        final_alpha,
    ], axis=-1)

    ys, xs = np.where(final_alpha > 4)
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    cropped = Image.fromarray(rgba[y0:y1, x0:x1], mode="RGBA")
    return cropped


# 1. fx_slash (Top-Left cell): flip vertically so the crescent follows the downward-right sword swing (top-left -> bottom-right)
c1 = raw_im.crop((0, 0, cw, ch)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
fx_slash = unmix_magenta_soft_rgba(c1, max_alpha_scale=0.72, noise_floor=0.06, tint_rgb=(235, 245, 255, 0.65))
fx_slash.thumbnail((176, 160), Image.Resampling.LANCZOS)
canvas_slash = Image.new("RGBA", (fx_slash.width + 16, fx_slash.height + 16), (0, 0, 0, 0))
canvas_slash.alpha_composite(fx_slash, (8, 8))
canvas_slash.save(os.path.join(PARTS_DIR, "fx_slash.png"))

# 2. fx_slash_heavy (Top-Right cell): double thin wind-cut curves (flipped horizontally so the arc bows right!)
c2 = raw_im.crop((cw, 0, W, ch)).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
fx_heavy = unmix_magenta_soft_rgba(c2, max_alpha_scale=0.78, noise_floor=0.06, tint_rgb=(230, 242, 255, 0.65))
fx_heavy.thumbnail((184, 168), Image.Resampling.LANCZOS)
canvas_heavy = Image.new("RGBA", (fx_heavy.width + 16, fx_heavy.height + 16), (0, 0, 0, 0))
canvas_heavy.alpha_composite(fx_heavy, (8, 8))
canvas_heavy.save(os.path.join(PARTS_DIR, "fx_slash_heavy.png"))

# 3. fx_spark (Bottom-Left cell): subtle steel glint & warm golden-white sparks (clean warm gold tint to remove any pink halo)
c3 = raw_im.crop((0, ch, cw, H))
fx_spark = unmix_magenta_soft_rgba(c3, max_alpha_scale=0.82, noise_floor=0.08, tint_rgb=(255, 224, 150, 0.70))
fx_spark.thumbnail((140, 140), Image.Resampling.LANCZOS)
canvas_spark = Image.new("RGBA", (fx_spark.width + 16, fx_spark.height + 16), (0, 0, 0, 0))
canvas_spark.alpha_composite(fx_spark, (8, 8))
canvas_spark.save(os.path.join(PARTS_DIR, "fx_spark.png"))

# 4. fx_dust (Bottom-Right cell): soft translucent ground dust wisp
c4 = raw_im.crop((cw, ch, W, H))
fx_dust = unmix_magenta_soft_rgba(c4, max_alpha_scale=0.62, noise_floor=0.08, tint_rgb=(195, 188, 176, 0.60))
fx_dust.thumbnail((168, 114), Image.Resampling.LANCZOS)
canvas_dust = Image.new("RGBA", (fx_dust.width + 16, fx_dust.height + 16), (0, 0, 0, 0))
canvas_dust.alpha_composite(fx_dust, (8, 8))
canvas_dust.save(os.path.join(PARTS_DIR, "fx_dust.png"))

for name in ["fx_slash", "fx_slash_heavy", "fx_spark", "fx_dust"]:
    im = Image.open(os.path.join(PARTS_DIR, f"{name}.png")).convert("RGBA")
    a = np.array(im)[:, :, 3]
    nonzero = a[a > 0]
    edge_clip = int(a[0, :].sum() + a[-1, :].sum() + a[:, 0].sum() + a[:, -1].sum())
    print(f"Saved {name}.png ({im.width}x{im.height}) | mean_alpha={nonzero.mean():.1f}/255 ({nonzero.mean()/2.55:.0f}%), max_alpha={nonzero.max()}/255 ({nonzero.max()/2.55:.0f}%), edge_clip={edge_clip}px")
