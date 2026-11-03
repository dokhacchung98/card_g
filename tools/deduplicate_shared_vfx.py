#!/usr/bin/env python3
"""
Deduplicate Shared Combat VFX (`fx_slash`, `fx_slash_heavy`, `fx_spark`, `fx_dust`)
into a single shared directory `assets/vfx_shared/` & `assets/mobile/vfx_shared/`.
"""

import pathlib
import re
import shutil
import sys
from PIL import Image

ROOT = pathlib.Path("/Users/dochung/Desktop/card_g")
sys.path.insert(0, str(ROOT / "tools"))
import forge_weapon as fw  # noqa: E402

VFX_NAMES = ["fx_slash", "fx_slash_heavy", "fx_spark", "fx_dust"]
SHARED_DIR = ROOT / "assets/vfx_shared"
MOBILE_SHARED_DIR = ROOT / "assets/mobile/vfx_shared"


def main():
    SHARED_DIR.mkdir(parents=True, exist_ok=True)
    MOBILE_SHARED_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Copy canonical 4 VFX files into assets/vfx_shared/ and export .webp into assets/mobile/vfx_shared/
    for fx in VFX_NAMES:
        dest_png = SHARED_DIR / f"{fx}.png"
        if not dest_png.exists():
            candidates = list((ROOT / "assets/weapons").glob(f"*/parts/{fx}.png")) + list((ROOT / "assets/heroes").glob(f"*/vfx/{fx}.png"))
            if not candidates:
                raise FileNotFoundError(f"Could not find source for {fx}.png")
            shutil.copyfile(candidates[0], dest_png)
        im = Image.open(dest_png).convert("RGBA")
        im.save(MOBILE_SHARED_DIR / f"{fx}.webp", format="WEBP", quality=90)

    print(f"[1/5] Canonical shared VFX saved to {SHARED_DIR} (PNG) and {MOBILE_SHARED_DIR} (WebP).")

    # 2. Delete all duplicate fx_* files across all 80 weapons (PNG & WebP) and legacy heroes
    removed_png = 0
    removed_webp = 0
    for fx in VFX_NAMES:
        for p in (ROOT / "assets/weapons").glob(f"*/parts/{fx}.png"):
            p.unlink()
            removed_png += 1
        for p in (ROOT / "assets/mobile/weapons").glob(f"*/parts/{fx}.webp"):
            p.unlink()
            removed_webp += 1
        for p in (ROOT / "assets/heroes").glob(f"*/vfx/{fx}.png"):
            p.unlink()
            removed_png += 1

    print(f"[2/5] Removed {removed_png} duplicate PNGs and {removed_webp} duplicate WebPs from individual hero/weapon folders.")

    # 3. Update all Godot .tscn files to reference res://assets/vfx_shared/fx_*.png
    updated_tscn = 0
    for tscn_path in list((ROOT / "assets/weapons").glob("*/godot/*.tscn")) + list((ROOT / "assets/heroes").glob("*/godot/*.tscn")):
        txt = tscn_path.read_text(encoding="utf-8")
        new_txt = txt
        for fx in VFX_NAMES:
            new_txt = re.sub(
                rf'res://assets/(?:weapons/[^/]+/parts|heroes/[^/]+/vfx)/{fx}\.png',
                f'res://assets/vfx_shared/{fx}.png',
                new_txt,
            )
        if new_txt != txt:
            tscn_path.write_text(new_txt, encoding="utf-8")
            updated_tscn += 1

    print(f"[3/5] Updated {updated_tscn} Godot .tscn files to reference res://assets/vfx_shared/fx_*.png.")

    # 4. Deduplicate assets/weapons_data.js and refresh all HTML editors
    old_size_kb = (ROOT / "assets/weapons_data.js").stat().st_size / 1024.0 if (ROOT / "assets/weapons_data.js").exists() else 0
    reg, order = fw.load_weapons_registry()
    stripped_entries = 0
    for wid, pack in reg.items():
        imgs = pack.get("images", {})
        for fx in VFX_NAMES:
            if fx in imgs:
                del imgs[fx]
                stripped_entries += 1
    fw.save_weapons_data_js(reg, order)
    new_size_kb = (ROOT / "assets/weapons_data.js").stat().st_size / 1024.0

    default_wid = order[0] if order else "w001"
    fw.MAIN_EDITOR_HTML.write_text(fw.render_lightweight_editor_html("weapons_data.js", default_wid), encoding="utf-8")
    updated_editors = 1
    for w_key, w_pack in reg.items():
        w_slug = w_pack["slug"]
        ed_path = ROOT / "assets/weapons" / w_slug / f"{w_key}_editor.html"
        if ed_path.parent.exists():
            ed_path.write_text(fw.render_lightweight_editor_html("../../weapons_data.js", w_key), encoding="utf-8")
            updated_editors += 1

    print(
        f"[4/5] Deduplicated weapons_data.js (removed {stripped_entries} embedded fx_* Base64 strings; "
        f"{old_size_kb:.1f} KB -> {new_size_kb:.1f} KB) and updated {updated_editors} HTML editors."
    )

    # 5. Clean up old 16:9 rectangular board table if present so only the 1:1 Square table remains
    for old_board in [
        ROOT / "assets/board_map/poker_battle_table_1920x1080.png",
        ROOT / "assets/mobile/board_map/poker_battle_table_960x540.webp",
    ]:
        if old_board.exists():
            old_board.unlink()
            print(f"[5/5] Removed obsolete rectangular board file: {old_board.relative_to(ROOT)}")

    # Final verification check
    rem_dups = sum(len(list((ROOT / "assets/weapons").glob(f"*/parts/{fx}.*"))) for fx in VFX_NAMES)
    shared_files = sorted(p.name for p in SHARED_DIR.glob("*.png"))
    mobile_shared_files = sorted(p.name for p in MOBILE_SHARED_DIR.glob("*.webp"))
    print(f"VERIFY: remaining duplicates in weapons/*/parts/ = {rem_dups}")
    print(f"VERIFY: assets/vfx_shared/ = {shared_files}")
    print(f"VERIFY: assets/mobile/vfx_shared/ = {mobile_shared_files}")


if __name__ == "__main__":
    main()
