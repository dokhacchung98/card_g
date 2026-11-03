#!/usr/bin/env python3
"""
Master Builder for All 4 Remaining Graphic Asset Categories of Arcana Five (card_g):
1. Category 1 — Poker Battle Table (1920x1080 RGB), 4 Card Slot States, Shared Chaos Deck & Freeze Props (`assets/board_map/`)
2. Category 2 — Ranged Physical Projectiles + 5-Element Spell Projectiles, Impacts & Field Synergy Auras (`assets/vfx_elements/`)
3. Category 3 — Summoned Battlefield Units (`C24` Shadow Hound, `C30` Runic Turret, `C36` Skeleton Warrior) (`assets/summons/`)
4. Category 4 — Combat HUD, Player Avatar States, Match Timers & 4-Frame Gacha Card Pack Opening (`assets/ui_hud/`)
Plus QC Audit Boards for each category & an Interactive HTML Game World Viewer (`assets/game_world_viewer.html`).
"""
import argparse
import base64
import json
import pathlib
import sys
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path("/Users/dochung/Desktop/card_g")
sys.path.insert(0, str(ROOT / "tools"))
from forge_weapon import (
    LAYOUT_1X1,
    LAYOUT_2X2,
    muse_post,
    unmix_magenta_rgba,
    keep_largest_component_and_crop,
)

BOARD_DIR = ROOT / "assets/board_map"
VFX_ELEM_DIR = ROOT / "assets/vfx_elements"
SUMMONS_DIR = ROOT / "assets/summons"
UI_HUD_DIR = ROOT / "assets/ui_hud"
MOBILE_DIR = ROOT / "assets/mobile"


def load_font(size: int):
    for p in [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]:
        if pathlib.Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def b64_uri(path: pathlib.Path) -> str:
    if not path.exists():
        return ""
    mime = "image/png" if path.suffix.lower() == ".png" else "image/webp"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def generate_with_retry(tag: str, prompt: str, refs: list[str], save_path: pathlib.Path, new_thread: bool = True):
    if save_path.exists():
        return
    save_path.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(3):
        print(f"[{tag}] Generating via Muse Local API (attempt {attempt + 1}/3) -> {save_path.name} ...")
        try:
            if new_thread:
                muse_post("/v1/thread", {"new_thread": True})
            muse_post("/generate-image", {
                "prompt": prompt,
                "reference_images": refs,
                "save_path": str(save_path),
            })
        except Exception as exc:
            print(f"[{tag}] Muse warning: {exc}")
        if save_path.exists():
            break


def split_2x2_sheet(raw_sheet_path: pathlib.Path, out_paths: list[pathlib.Path], cell_canvas_size=(256, 256), inner_fit=(224, 224), tight_crop_only=False):
    sheet_im = Image.open(raw_sheet_path).convert("RGBA")
    sw, sh = sheet_im.size
    cw, ch = sw // 2, sh // 2
    results = []
    for idx in range(4):
        r_i, c_i = idx // 2, idx % 2
        cell = sheet_im.crop((c_i * cw, r_i * ch, (c_i + 1) * cw, (r_i + 1) * ch))
        unmixed = unmix_magenta_rgba(cell)
        cropped = keep_largest_component_and_crop(unmixed, pad=0)
        if tight_crop_only:
            sc = min(inner_fit[0] / max(1, cropped.width), inner_fit[1] / max(1, cropped.height))
            nw = max(1, int(round(cropped.width * sc)))
            nh = max(1, int(round(cropped.height * sc)))
            final_im = keep_largest_component_and_crop(cropped.resize((nw, nh), Image.Resampling.LANCZOS), pad=0)
        else:
            final_im = Image.new("RGBA", cell_canvas_size, (0, 0, 0, 0))
            sc = min(inner_fit[0] / max(1, cropped.width), inner_fit[1] / max(1, cropped.height))
            nw = max(1, int(round(cropped.width * sc)))
            nh = max(1, int(round(cropped.height * sc)))
            resized = cropped.resize((nw, nh), Image.Resampling.LANCZOS)
            final_im.paste(resized, ((cell_canvas_size[0] - nw) // 2, (cell_canvas_size[1] - nh) // 2), resized)
        out_p = out_paths[idx]
        out_p.parent.mkdir(parents=True, exist_ok=True)
        final_im.save(out_p)
        results.append(final_im)
    return results


# ==============================================================================
# CATEGORY 1: POKER BATTLE TABLE (4-EDGE ARENA), 4 CARD SLOT STATES & PROPS
# ==============================================================================
def forge_category_1_board():
    rdir = BOARD_DIR / "raw"
    sdir = BOARD_DIR / "slots"
    pdir = BOARD_DIR / "props"
    qdir = BOARD_DIR / "qc_previews"
    mdir = MOBILE_DIR / "board_map"
    for d in (rdir, sdir, pdir, qdir, mdir):
        d.mkdir(parents=True, exist_ok=True)

    # 1.1 Main 4-Edge SQUARE Poker Battle Table Background (1024x1024 RGB 1:1 for 4 Players)
    bg_raw = rdir / "poker_battle_table_square_raw.png"
    bg_png = BOARD_DIR / "poker_battle_table_square_1024x1024.png"
    generate_with_retry(
        "board_bg_square",
        (
            "Create a 1:1 SQUARE top-down dark-fantasy 4-player tactical game board map illustration (100% opaque RGB painting, following the 1:1 square aspect ratio of the attached reference image, NO guide lines, NO characters, NO text, NO UI).\n"
            "DESIGN (4-Sided Symmetric Square Poker Table + Square Central Battle Arena for 4 Players):\n"
            "- A grand 1:1 SQUARE Dark-Fantasy Stone Poker Battle Table viewed from directly above (90-degree top-down tactical view) designed symmetrically for 4 players sitting on the 4 equal sides (Top, Bottom, Left, Right).\n"
            "- Each of the 4 equal outer sides features an ornate dark-iron and carved obsidian card-dealing ledge (where each player places 10 cards) lit by warm gothic corner braziers.\n"
            "- The large spacious square center of the table is a sunken ancient basalt-stone Battle Arena inlaid with a subtle golden-bronze Wu-Xing Five-Elements magic circle in the middle.\n"
            "- Rich dark-fantasy atmosphere matching Arcana Five aesthetic, high contrast so 2D heroes and cards stand out clearly on top."
        ),
        [str(LAYOUT_1X1)],
        bg_raw,
        new_thread=True,
    )
    if bg_raw.exists() and not bg_png.exists():
        bim = Image.open(bg_raw).convert("RGB").resize((1024, 1024), Image.Resampling.LANCZOS)
        bim.save(bg_png, format="PNG")
        bim.resize((512, 512), Image.Resampling.LANCZOS).save(mdir / "poker_battle_table_square_512x512.webp", format="WEBP", quality=90)

    # 1.2 4 Card Slot States (2x2 on #FF00FF)
    slots_raw = rdir / "card_slots_states_2x2_raw.png"
    slot_files = [
        sdir / "slot_1_empty.png",
        sdir / "slot_2_facedown.png",
        sdir / "slot_3_active_hero.png",
        sdir / "slot_4_trigger_break.png",
    ]
    generate_with_retry(
        "board_slots",
        (
            "Create a 2x2 sprite sheet of 4 vertical rectangular card-slot frames on a flat solid pure magenta (#FF00FF) background, "
            "strictly following the 4 cells of the attached layout_guide_2x2.png.\n"
            "- Top-Left Cell (State 1 - Empty Slot): A recessed dark obsidian stone rectangular card slot frame etched with dim dormant runes.\n"
            "- Top-Right Cell (State 2 - Face-Down Card in Slot): The same stone slot holding a mysterious face-down dark-fantasy card back glowing with golden-cyan arcane edge runes.\n"
            "- Bottom-Left Cell (State 3 - Active Hero Linked Slot): The stone slot blazing with an active golden-emerald soul-link sigil and energy pedestal.\n"
            "- Bottom-Right Cell (State 4 - Slot Trigger / Break Burst): The stone slot erupting with shattering golden-crimson arcane sparks and runic shockwaves.\n"
            "RULES: Centered inside each cell with generous margin, zero cell clipping, NO blue guide lines, 100% flat solid #FF00FF background."
        ),
        [str(LAYOUT_2X2)],
        slots_raw,
        new_thread=True,
    )
    if slots_raw.exists() and not slot_files[-1].exists():
        split_2x2_sheet(slots_raw, slot_files, cell_canvas_size=(192, 256), inner_fit=(172, 232))

    # 1.3 Board Center Props & Phase Overlays (2x2 on #FF00FF)
    props_raw = rdir / "board_props_2x2_raw.png"
    prop_files = [
        pdir / "prop_1_shared_chaos_deck.png",
        pdir / "prop_2_freeze_pause_crystal.png",
        pdir / "prop_3_sudden_death_brazier.png",
        pdir / "prop_4_wuxing_synergy_seal.png",
    ]
    generate_with_retry(
        "board_props",
        (
            "Create a 2x2 sprite sheet of 4 dark-fantasy board tabletop props on a flat solid pure magenta (#FF00FF) background, "
            "strictly following the 4 cells of the attached layout_guide_2x2.png.\n"
            "- Top-Left Cell: A tall stack of ancient dark-fantasy magic cards bound by swirling golden-violet chaos energy (Shared Chaos Draw Deck Pile).\n"
            "- Top-Right Cell: A crystalline frost-and-chronos stasis seal with icy chains and frozen clock hands (15s Board Freeze / Pause Emblem).\n"
            "- Bottom-Left Cell: A horned iron skull war-brazier roaring with crimson-gold hellfire (60s Sudden Death Showdown Emblem).\n"
            "- Bottom-Right Cell: A radiant golden five-pointed Wu-Xing elemental pentagram medallion with 5 glowing elemental gems (Five-Element Synergy Crest).\n"
            "RULES: Centered inside each cell with generous margin, zero cell clipping, NO blue guide lines, 100% flat solid #FF00FF background."
        ),
        [str(LAYOUT_2X2)],
        props_raw,
        new_thread=True,
    )
    if props_raw.exists() and not prop_files[-1].exists():
        split_2x2_sheet(props_raw, prop_files, cell_canvas_size=(256, 256), inner_fit=(224, 224))

    for p in list(sdir.glob("*.png")) + list(pdir.glob("*.png")):
        Image.open(p).convert("RGBA").save(mdir / f"{p.stem}.webp", format="WEBP", quality=90)

    # QC Board for Category 1
    f_title = load_font(20)
    f_sub = load_font(13)
    qc = Image.new("RGB", (1560, 740), (13, 17, 23))
    draw = ImageDraw.Draw(qc)
    draw.text((24, 16), "QC HẠNG MỤC 1: MẶT BÀN POKER HÌNH VUÔNG 4 NGƯỜI CHƠI (1024x1024) + 4 TRẠNG THÁI Ô BÀI + PROPS", fill=(245, 158, 11), font=f_title)
    if bg_png.exists():
        bim = Image.open(bg_png).convert("RGB").resize((600, 600), Image.Resampling.LANCZOS)
        qc.paste(bim, (124, 60))
        draw.rectangle([124, 60, 724, 660], outline=(245, 158, 11), width=2)
        draw.text((124, 672), "poker_battle_table_square_1024x1024.png (1:1 Square RGB — Bàn Vuông 4 Cạnh Đối Xứng)", fill=(63, 185, 80), font=f_sub)

    slot_labels = ["1. Ô Trống", "2. Đang Úp Bài", "3. Duy Trì Tướng", "4. Kích Hoạt / Vỡ Ô"]
    for i, sp in enumerate(slot_files):
        sx = 850 + i * 172
        sy = 60
        draw.rectangle([sx, sy, sx + 160, sy + 240], fill=(22, 27, 34), outline=(88, 166, 255), width=1)
        if sp.exists():
            sim = Image.open(sp).convert("RGBA").resize((140, 186), Image.Resampling.LANCZOS)
            qc.paste(sim, (sx + 10, sy + 36), sim)
        draw.text((sx + 10, sy + 10), slot_labels[i], fill=(230, 237, 243), font=f_sub)

    prop_labels = ["Bộ Bài Chung", "Ấn Đóng Băng 15s", "Đài Tử Chiến 60s", "Ấn Ngũ Hành"]
    for i, pp in enumerate(prop_files):
        px = 850 + i * 172
        py = 330
        draw.rectangle([px, py, px + 160, py + 220], fill=(22, 27, 34), outline=(63, 185, 80), width=1)
        if pp.exists():
            pim = Image.open(pp).convert("RGBA").resize((140, 140), Image.Resampling.LANCZOS)
            qc.paste(pim, (px + 10, py + 44), pim)
        draw.text((px + 10, py + 10), prop_labels[i], fill=(230, 237, 243), font=f_sub)

    qc.save(qdir / "qc_category1_board_and_slots.png")
    print("[Category 1] Poker Battle Table, 4 Slot States & Props complete!")


# ==============================================================================
# CATEGORY 2: PHYSICAL PROJECTILES & 5-ELEMENT PROJECTILES / IMPACTS / AURAS
# ==============================================================================
ELEMENTS_SPEC = [
    {
        "id": "kim_metal",
        "name": "⚔️ Hệ KIM (Metal)",
        "color_desc": "brilliant platinum-silver and imperial gold metallic sword-qi energy",
        "proj_desc": "a razor-sharp crescent blade-wave and golden spear-bolt of metallic sword-qi oriented horizontally pointing right",
        "impact_desc": "explosive metallic silver-gold sword-slash sparks and shattering steel shards",
        "aura_desc": "a circular ground ring of spinning silver-gold sword runes and metallic shields",
    },
    {
        "id": "moc_wood",
        "name": "🌿 Hệ MỘC (Wood)",
        "color_desc": "luminous emerald-green nature vitality and dark-violet venom thorns",
        "proj_desc": "a spiraling emerald-green thorn-vine javelin and toxic violet spore-orb oriented horizontally pointing right",
        "impact_desc": "erupting thorny briar roots, emerald healing leaves, and splashing violet venom droplets",
        "aura_desc": "a circular ground ring of living emerald-green roots, glowing leaves, and vitality runes",
    },
    {
        "id": "thuy_water",
        "name": "❄️ Hệ THỦY (Water)",
        "color_desc": "crystalline glacial ice-blue and deep abyssal cyan-sapphire mana",
        "proj_desc": "a jagged glacial ice-lance and swirling sapphire water-vortex bolt oriented horizontally pointing right",
        "impact_desc": "shattering frost crystals, freezing cyan shockwaves, and splashing abyssal waves",
        "aura_desc": "a circular ground ring of snowflake frost runes and swirling sapphire mana currents",
    },
    {
        "id": "hoa_fire",
        "name": "🔥 Hệ HỎA (Fire)",
        "color_desc": "blazing hellfire crimson-red, molten lava orange, and bright solar gold",
        "proj_desc": "a roaring hellfire meteor-fireball with a trailing molten flame tail oriented horizontally pointing right",
        "impact_desc": "a violent volcano detonation of crimson-orange flames, lava sparks, and ash rings",
        "aura_desc": "a circular ground ring of roaring hellfire flames and molten magma runes",
    },
    {
        "id": "tho_earth",
        "name": "🪨 Hệ THỔ (Earth)",
        "color_desc": "heavy obsidian-basalt rock, bronze granite, and glowing amber-gold gravity runes",
        "proj_desc": "a jagged obsidian-boulder comet wrapped in glowing amber-gold gravity rings oriented horizontally pointing right",
        "impact_desc": "crushing stone shockwaves, flying basalt rock spikes, and golden seismic cracks",
        "aura_desc": "a circular ground ring of floating granite shield stones and glowing amber earth runes",
    },
]


def forge_category_2_vfx():
    rdir = VFX_ELEM_DIR / "raw"
    phys_dir = VFX_ELEM_DIR / "physical_projectiles"
    qdir = VFX_ELEM_DIR / "qc_previews"
    mdir = MOBILE_DIR / "vfx_elements"
    for d in (rdir, phys_dir, qdir, mdir):
        d.mkdir(parents=True, exist_ok=True)

    # 2.1 Physical Ranged Projectiles (Arrow, Crossbow Bolt, Harpoon Javelin, Spinning Chakram)
    phys_raw = rdir / "physical_projectiles_2x2_raw.png"
    phys_files = [
        phys_dir / "proj_arrow.png",
        phys_dir / "proj_crossbow_bolt.png",
        phys_dir / "proj_harpoon_javelin.png",
        phys_dir / "proj_spinning_chakram.png",
    ]
    generate_with_retry(
        "vfx_phys_proj",
        (
            "Create a 2x2 sprite sheet of 4 standalone ranged weapon projectiles on a flat solid pure magenta (#FF00FF) background, "
            "strictly following the 4 cells of the attached layout_guide_2x2.png.\n"
            "- Top-Left Cell: A dark-iron war arrow with raven-feather fletching and a steel broadhead pointing horizontally to the RIGHT.\n"
            "- Top-Right Cell: A heavy armor-piercing steel crossbow bolt with brass fins and white wind-trails pointing horizontally to the RIGHT.\n"
            "- Bottom-Left Cell: A barbed bounty-hunter harpoon javelin trailing a short iron chain link pointing horizontally to the RIGHT.\n"
            "- Bottom-Right Cell: A spinning gilded-bronze ritual bladed chakram war-disc with turquoise wind-slash motion trails.\n"
            "RULES: Centered inside each cell with generous margin, zero cell clipping, NO bows/crossbows, NO hands, NO blue guide lines, 100% flat solid #FF00FF background."
        ),
        [str(LAYOUT_2X2)],
        phys_raw,
        new_thread=True,
    )
    if phys_raw.exists() and not phys_files[-1].exists():
        split_2x2_sheet(phys_raw, phys_files, inner_fit=(160, 96), tight_crop_only=True)

    # 2.2 Five Elements Projectiles (2x2 each) + Impacts & Field Synergy Aura (2x2 each)
    for elem in ELEMENTS_SPEC:
        eid = elem["id"]
        edir = VFX_ELEM_DIR / eid
        edir.mkdir(parents=True, exist_ok=True)

        proj_raw = rdir / f"{eid}_projectile_2x2_raw.png"
        proj_files = [edir / f"projectile_{i}.png" for i in range(4)]
        generate_with_retry(
            f"vfx_{eid}_proj",
            (
                f"Create a 2x2 animated spell projectile sprite sheet (4 frames of {elem['color_desc']}) on a flat solid pure magenta (#FF00FF) background, "
                f"strictly following the 4 cells of the attached layout_guide_2x2.png.\n"
                f"SUBJECT: 4-frame looping flight animation of {elem['proj_desc']}.\n"
                f"RULES: All 4 frames must fly horizontally pointing RIGHT at the same center line, centered inside each cell with generous margin, "
                f"zero cell clipping, NO pink/magenta on the spell, NO blue guide lines, 100% flat solid #FF00FF background."
            ),
            [str(LAYOUT_2X2)],
            proj_raw,
            new_thread=True,
        )
        if proj_raw.exists() and not proj_files[-1].exists():
            frames = split_2x2_sheet(proj_raw, proj_files, cell_canvas_size=(192, 128), inner_fit=(168, 104))
            sheet = Image.new("RGBA", (384, 256), (0, 0, 0, 0))
            for i, fim in enumerate(frames):
                sheet.paste(fim, ((i % 2) * 192, (i // 2) * 128), fim)
            sheet.save(edir / "projectile_2x2.png")

        imp_raw = rdir / f"{eid}_impact_aura_2x2_raw.png"
        imp_files = [
            edir / "impact_0.png",
            edir / "impact_1.png",
            edir / "impact_2.png",
            edir / "synergy_aura.png",
        ]
        generate_with_retry(
            f"vfx_{eid}_imp",
            (
                f"Create a 2x2 elemental VFX sprite sheet ({elem['color_desc']}) on a flat solid pure magenta (#FF00FF) background, "
                f"strictly following the 4 cells of the attached layout_guide_2x2.png.\n"
                f"- Top-Left Cell (Impact Frame 1): Initial concentrated hit flash of {elem['impact_desc']}.\n"
                f"- Top-Right Cell (Impact Frame 2): Peak expanding explosion burst of {elem['impact_desc']}.\n"
                f"- Bottom-Left Cell (Impact Frame 3): Dissolving shockwave ring and lingering elemental embers of {elem['impact_desc']}.\n"
                f"- Bottom-Right Cell (Field Synergy Foot Aura): Top-down 3/4 perspective {elem['aura_desc']} meant to glow beneath a hero's feet.\n"
                f"RULES: Centered inside each cell with generous margin, zero cell clipping, NO pink/magenta on the VFX, NO blue guide lines, 100% flat solid #FF00FF background."
            ),
            [str(LAYOUT_2X2)],
            imp_raw,
            new_thread=True,
        )
        if imp_raw.exists() and not imp_files[-1].exists():
            frames = split_2x2_sheet(imp_raw, imp_files, cell_canvas_size=(224, 224), inner_fit=(196, 196))
            sheet = Image.new("RGBA", (448, 448), (0, 0, 0, 0))
            for i, fim in enumerate(frames):
                sheet.paste(fim, ((i % 2) * 224, (i // 2) * 224), fim)
            sheet.save(edir / "impact_and_aura_2x2.png")

    # Build Category 2 QC Board
    f_title = load_font(20)
    f_sub = load_font(12)
    qc = Image.new("RGB", (1560, 860), (13, 17, 23))
    draw = ImageDraw.Draw(qc)
    draw.text((24, 16), "QC HẠNG MỤC 2: ĐẠN VẬT LÝ TẦM XA + ĐẠN PHÉP, NỔ IMPACT & HÀO QUANG TƯƠNG SINH 5 HỆ NGŨ HÀNH", fill=(245, 158, 11), font=f_title)

    phys_names = ["Mũi Tên (Arrow)", "Đạn Nỏ (Bolt)", "Lao Móc (Harpoon)", "Phiến Luân (Chakram)"]
    for i, pp in enumerate(phys_files):
        bx = 24 + i * 376
        by = 54
        draw.rectangle([bx, by, bx + 360, by + 110], fill=(22, 27, 34), outline=(88, 166, 255), width=1)
        if pp.exists():
            pim = Image.open(pp).convert("RGBA")
            qc.paste(pim, (bx + (360 - pim.width) // 2, by + 30 + (72 - pim.height) // 2), pim)
        draw.text((bx + 12, by + 8), f"Đạn Vật Lý {i + 1}: {phys_names[i]} ({pp.name})", fill=(230, 237, 243), font=f_sub)

    for r_idx, elem in enumerate(ELEMENTS_SPEC):
        eid = elem["id"]
        edir = VFX_ELEM_DIR / eid
        by = 180 + r_idx * 130
        draw.rectangle([24, by, 1536, by + 118], fill=(22, 27, 34), outline=(48, 54, 61), width=1)
        draw.text((38, by + 10), elem["name"], fill=(245, 158, 11), font=f_sub)
        draw.text((38, by + 32), f"Thư mục: assets/vfx_elements/{eid}/", fill=(139, 148, 158), font=f_sub)

        # Show 4 projectile frames + 3 impact frames + 1 synergy aura
        all_8 = [
            (edir / "projectile_0.png", "Đạn F1"),
            (edir / "projectile_1.png", "Đạn F2"),
            (edir / "projectile_2.png", "Đạn F3"),
            (edir / "projectile_3.png", "Đạn F4"),
            (edir / "impact_0.png", "Nổ F1"),
            (edir / "impact_1.png", "Nổ F2"),
            (edir / "impact_2.png", "Nổ F3"),
            (edir / "synergy_aura.png", "Hào Quang Hệ"),
        ]
        for c_i, (fp, lbl) in enumerate(all_8):
            cx = 260 + c_i * 156
            cy = by + 8
            draw.rectangle([cx, cy, cx + 144, cy + 102], fill=(13, 17, 23), outline=(48, 54, 61), width=1)
            if fp.exists():
                fim = Image.open(fp).convert("RGBA")
                sc = min(124 / max(1, fim.width), 74 / max(1, fim.height))
                fr = fim.resize((max(1, int(fim.width * sc)), max(1, int(fim.height * sc))), Image.Resampling.LANCZOS)
                qc.paste(fr, (cx + (144 - fr.width) // 2, cy + 22 + (76 - fr.height) // 2), fr)
            draw.text((cx + 8, cy + 4), lbl, fill=(88, 166, 255), font=f_sub)

    qc.save(qdir / "qc_category2_projectiles_and_5elements.png")
    print("[Category 2] Physical Projectiles & 5-Element Spell Projectiles/Impacts/Auras complete!")


# ==============================================================================
# CATEGORY 3: SUMMONED BATTLEFIELD UNITS (C24 HOUND, C30 TURRET, C36 SKELETON)
# ==============================================================================
SUMMON_SPECS = [
    {
        "id": "s01_linh_cau",
        "card_ref": "C024 Triệu Hồi Sư Tập Sự",
        "name": "Hắc Khuyển Linh Cẩu (Shadow Hellhound)",
        "prompt_ref": (
            "Create a single-cell 1x1 game sprite of a dark-fantasy summoned Shadow Hellhound ('Hắc Khuyển Linh Cẩu' from Card C024) "
            "on a flat solid pure magenta (#FF00FF) background, strictly following the attached layout_guide_1x1.png.\n"
            "DESIGN: Side-view 3/4 facing RIGHT, a fierce dark-armored spectral wolf-hound with spiked iron collar, dark slate fur, "
            "and glowing cyan-blue soul-fire eyes and claws. Centered with generous margin, zero border clipping, 100% flat solid #FF00FF background."
        ),
        "prompt_2x2": (
            "Create a 2x2 sprite sheet (4 frames: row 1 left-to-right, row 2 left-to-right) of the EXACT SAME Shadow Hellhound from the first attached reference image, "
            "following the 2x2 grid of the second attached reference image (layout_guide_2x2.png).\n"
            "- Frame 1 (Top-Left): Ready combat prowl stance facing right.\n"
            "- Frame 2 (Top-Right): Bounding forward run stride.\n"
            "- Frame 3 (Bottom-Left): Fierce leaping lunge with glowing cyan-blue jaws wide open.\n"
            "- Frame 4 (Bottom-Right): Savage bite slash impact with cyan soul-fangs.\n"
            "RULES: Consistent proportions, zero cell clipping, NO blue guide lines, 100% flat solid #FF00FF background."
        ),
    },
    {
        "id": "s02_phao_co_ngu",
        "card_ref": "C030 Thợ Máy Cổ Ngữ",
        "name": "Ụ Pháo Cổ Ngữ (Arcane Runic Turret)",
        "prompt_ref": (
            "Create a single-cell 1x1 game sprite of a dark-fantasy summoned Arcane Runic Auto-Turret ('Ụ Pháo Cổ Ngữ' from Card C030) "
            "on a flat solid pure magenta (#FF00FF) background, strictly following the attached layout_guide_1x1.png.\n"
            "DESIGN: 3/4 side-front view facing RIGHT, a heavy dwarven blackened-iron and antique-brass tripod mechanical cannon turret "
            "with spinning gear wheels and a glowing amber-cyan runic crystal barrel. Centered with generous margin, zero border clipping, 100% flat solid #FF00FF background."
        ),
        "prompt_2x2": (
            "Create a 2x2 sprite sheet (4 frames: row 1 left-to-right, row 2 left-to-right) of the EXACT SAME Arcane Runic Auto-Turret from the first attached reference image, "
            "following the 2x2 grid of the second attached reference image (layout_guide_2x2.png).\n"
            "- Frame 1 (Top-Left): Idle deployed turret aiming right.\n"
            "- Frame 2 (Top-Right): Barrel charging with bright cyan-amber runic energy and spinning brass gears.\n"
            "- Frame 3 (Bottom-Left): Cannon firing a blinding muzzle blast of arcane energy with barrel recoil.\n"
            "- Frame 4 (Bottom-Right): Cooling barrel venting golden-cyan arcane steam.\n"
            "RULES: Consistent proportions and tripod base anchor, zero cell clipping, NO blue guide lines, 100% flat solid #FF00FF background."
        ),
    },
    {
        "id": "s03_chien_binh_xuong",
        "card_ref": "C036 Gọi Hồn Sư",
        "name": "Chiến Binh Xương (Undead Skeleton Minion)",
        "prompt_ref": (
            "Create a single-cell 1x1 game sprite of a dark-fantasy summoned Undead Skeleton Warrior ('Chiến Binh Xương' from Card C036) "
            "on a flat solid pure magenta (#FF00FF) background, strictly following the attached layout_guide_1x1.png.\n"
            "DESIGN: 3/4 side-front view facing RIGHT, an undead skeletal soldier in rusted iron pauldrons wielding a notched bone-cleaver sword "
            "and a cracked round buckler, glowing with emerald-green necromantic soul-fire in its eye sockets. Centered with generous margin, zero border clipping, 100% flat solid #FF00FF background."
        ),
        "prompt_2x2": (
            "Create a 2x2 sprite sheet (4 frames: row 1 left-to-right, row 2 left-to-right) of the EXACT SAME Undead Skeleton Warrior from the first attached reference image, "
            "following the 2x2 grid of the second attached reference image (layout_guide_2x2.png).\n"
            "- Frame 1 (Top-Left): Combat guard stance facing right with bone cleaver and shield.\n"
            "- Frame 2 (Top-Right): Marching step forward with sword raised high.\n"
            "- Frame 3 (Bottom-Left): Heavy downward cleaver slash with a trail of necrotic green energy.\n"
            "- Frame 4 (Bottom-Right): Follow-through recovery stance.\n"
            "RULES: Consistent proportions and feet line, zero cell clipping, NO blue guide lines, 100% flat solid #FF00FF background."
        ),
    },
]


def forge_category_3_summons():
    qdir = SUMMONS_DIR / "qc_previews"
    qdir.mkdir(parents=True, exist_ok=True)

    for spec in SUMMON_SPECS:
        sid = spec["id"]
        sdir = SUMMONS_DIR / sid
        rdir = sdir / "raw"
        pdir = sdir / "parts"
        mdir = MOBILE_DIR / "summons" / sid
        for d in (rdir, pdir, mdir):
            d.mkdir(parents=True, exist_ok=True)

        ref_raw = rdir / f"{sid}_ref_1x1_raw.png"
        generate_with_retry(f"summon_{sid}_ref", spec["prompt_ref"], [str(LAYOUT_1X1)], ref_raw, new_thread=True)
        if ref_raw.exists() and not (pdir / "summon_main.png").exists():
            im = Image.open(ref_raw).convert("RGBA")
            clean = keep_largest_component_and_crop(unmix_magenta_rgba(im), pad=0)
            sc = min(180 / max(1, clean.width), 180 / max(1, clean.height))
            res = clean.resize((max(1, int(clean.width * sc)), max(1, int(clean.height * sc))), Image.Resampling.LANCZOS)
            res.save(pdir / "summon_main.png")

        anim_raw = rdir / f"{sid}_anim_2x2_raw.png"
        anim_files = [pdir / f"anim_{i}.png" for i in range(4)]
        generate_with_retry(
            f"summon_{sid}_2x2",
            spec["prompt_2x2"],
            [str(ref_raw), str(LAYOUT_2X2)],
            anim_raw,
            new_thread=False,
        )
        if anim_raw.exists() and not anim_files[-1].exists():
            frames = split_2x2_sheet(anim_raw, anim_files, cell_canvas_size=(224, 224), inner_fit=(192, 192))
            sheet = Image.new("RGBA", (448, 448), (0, 0, 0, 0))
            for i, fim in enumerate(frames):
                sheet.paste(fim, ((i % 2) * 224, (i // 2) * 224), fim)
            sheet.save(pdir / "spritesheet_2x2.png")

        for p in pdir.glob("*.png"):
            Image.open(p).convert("RGBA").save(mdir / f"{p.stem}.webp", format="WEBP", quality=90)

    # QC Board for Category 3
    f_title = load_font(20)
    f_sub = load_font(13)
    qc = Image.new("RGB", (1520, 680), (13, 17, 23))
    draw = ImageDraw.Draw(qc)
    draw.text((24, 16), "QC HẠNG MỤC 3: ĐƠN VỊ TRIỆU HỒI PHỤ TRÊN SÂN (C024 LINH CẨU · C030 Ụ PHÁO · C036 CHIẾN BINH XƯƠNG)", fill=(245, 158, 11), font=f_title)

    for idx, spec in enumerate(SUMMON_SPECS):
        sid = spec["id"]
        pdir = SUMMONS_DIR / sid / "parts"
        by = 60 + idx * 198
        draw.rectangle([24, by, 1496, by + 184], fill=(22, 27, 34), outline=(88, 166, 255), width=2)
        draw.text((40, by + 12), f"{idx + 1}. {spec['name']} — Triệu hồi bởi: {spec['card_ref']}", fill=(245, 158, 11), font=f_sub)
        draw.text((40, by + 36), f"Thư mục: assets/summons/{sid}/parts/ (summon_main.png & anim_0..3.png)", fill=(139, 148, 158), font=f_sub)

        cols_items = [("Ref Tĩnh (summon_main)", pdir / "summon_main.png")] + [(f"Frame {i + 1} (anim_{i})", pdir / f"anim_{i}.png") for i in range(4)]
        for c_i, (lbl, fp) in enumerate(cols_items):
            cx = 440 + c_i * 206
            cy = by + 14
            draw.rectangle([cx, cy, cx + 190, cy + 156], fill=(13, 17, 23), outline=(48, 54, 61), width=1)
            if fp.exists():
                fim = Image.open(fp).convert("RGBA")
                sc = min(130 / max(1, fim.width), 116 / max(1, fim.height))
                fr = fim.resize((max(1, int(fim.width * sc)), max(1, int(fim.height * sc))), Image.Resampling.LANCZOS)
                qc.paste(fr, (cx + (190 - fr.width) // 2, cy + 28 + (120 - fr.height) // 2), fr)
            draw.text((cx + 10, cy + 6), lbl, fill=(63, 185, 80) if c_i == 0 else (88, 166, 255), font=f_sub)

    qc.save(qdir / "qc_category3_summoned_units.png")
    print("[Category 3] All 3 Summoned Battlefield Units complete!")


# ==============================================================================
# CATEGORY 4: COMBAT HUD, PLAYER AVATAR FRAMES, TIMERS & GACHA CARD PACK
# ==============================================================================
def forge_category_4_ui_hud():
    rdir = UI_HUD_DIR / "raw"
    adir = UI_HUD_DIR / "avatars"
    bdir = UI_HUD_DIR / "hud_bars"
    gdir = UI_HUD_DIR / "gacha_pack"
    qdir = UI_HUD_DIR / "qc_previews"
    mdir = MOBILE_DIR / "ui_hud"
    for d in (rdir, adir, bdir, gdir, qdir, mdir):
        d.mkdir(parents=True, exist_ok=True)

    # 4.1 Player Avatar Frames & History Scroll Icon (2x2 on #FF00FF)
    av_raw = rdir / "player_avatars_2x2_raw.png"
    av_files = [
        adir / "avatar_1_active_100hp.png",
        adir / "avatar_2_direct_hit.png",
        adir / "avatar_3_eliminated_0hp.png",
        adir / "icon_played_history_scroll.png",
    ]
    generate_with_retry(
        "ui_avatars",
        (
            "Create a 2x2 sprite sheet of 4 dark-fantasy UI elements on a flat solid pure magenta (#FF00FF) background, "
            "strictly following the 4 cells of the attached layout_guide_2x2.png.\n"
            "- Top-Left Cell (Active Player Avatar Crest): An ornate octagonal dark-iron and royal-gold warlord portrait frame with a glowing crimson heart gem at the bottom.\n"
            "- Top-Right Cell (Player Taking Direct Damage Frame): The same octagonal portrait frame engulfed in cracking fiery-red slash shockwaves and blood sparks.\n"
            "- Bottom-Left Cell (Eliminated 0 HP Player Frame): A shattered petrified grey stone portrait frame bound in dark iron chains with an extinguished skull emblem.\n"
            "- Bottom-Right Cell (Revealed Card History Button Icon): An ancient rolled parchment scroll bound with a golden wax seal and glowing cyan eye rune.\n"
            "RULES: Centered inside each cell with generous margin, zero cell clipping, NO text, NO blue guide lines, 100% flat solid #FF00FF background."
        ),
        [str(LAYOUT_2X2)],
        av_raw,
        new_thread=True,
    )
    if av_raw.exists() and not av_files[-1].exists():
        split_2x2_sheet(av_raw, av_files, cell_canvas_size=(224, 224), inner_fit=(196, 196))

    # 4.2 Overhead Unit HP/Mana/Shield Bars & Match Phase Timers (2x2 on #FF00FF)
    hud_raw = rdir / "hud_bars_timers_2x2_raw.png"
    hud_files = [
        bdir / "unit_hp_mana_bar_frame.png",
        bdir / "unit_shield_overlay_frame.png",
        bdir / "timer_prep_15s_compass.png",
        bdir / "timer_combat_15s_crossed_swords.png",
    ]
    generate_with_retry(
        "ui_bars_timers",
        (
            "Create a 2x2 sprite sheet of 4 dark-fantasy combat HUD elements on a flat solid pure magenta (#FF00FF) background, "
            "strictly following the 4 cells of the attached layout_guide_2x2.png.\n"
            "- Top-Left Cell (Unit Overhead HP & Mana Bar): A horizontal dark-iron dual-bar gauge with a glowing ruby-red top HP bar and a sapphire-blue bottom Mana bar.\n"
            "- Top-Right Cell (Unit Shield Bar Overlay): A horizontal gilded-silver and cyan-crystal armor bracket frame that wraps around an HP bar to indicate active Shield.\n"
            "- Bottom-Left Cell (15s Prep Phase Timer Medallion): An ornate brass-and-sapphire sandglass compass dial glowing with calm cyan-gold preparation runes.\n"
            "- Bottom-Right Cell (15s Combat Phase Timer Medallion): An iron-and-gold war clock dial backed by two crossed blazing swords and fiery combat runes.\n"
            "RULES: Centered inside each cell with generous margin, zero cell clipping, NO text/numbers, NO blue guide lines, 100% flat solid #FF00FF background."
        ),
        [str(LAYOUT_2X2)],
        hud_raw,
        new_thread=True,
    )
    if hud_raw.exists() and not hud_files[-1].exists():
        split_2x2_sheet(hud_raw, hud_files, cell_canvas_size=(240, 200), inner_fit=(216, 176))

    # 4.3 Gacha Card Pack 4-Frame Opening Animation (2x2 on #FF00FF)
    pack_raw = rdir / "card_pack_gacha_2x2_raw.png"
    pack_files = [
        gdir / "pack_0_sealed.png",
        gdir / "pack_1_cracking.png",
        gdir / "pack_2_ripping.png",
        gdir / "pack_3_burst_open.png",
    ]
    generate_with_retry(
        "ui_gacha_pack",
        (
            "Create a 2x2 sprite sheet (4 frames: row 1 left-to-right, row 2 left-to-right) of a Dark-Fantasy Booster Card Pack opening animation "
            "on a flat solid pure magenta (#FF00FF) background, strictly following the attached layout_guide_2x2.png.\n"
            "- Frame 1 (Top-Left): A sealed vertical dark-leather and gilded-iron booster card pack embossed with a glowing five-element Wu-Xing crest.\n"
            "- Frame 2 (Top-Right): The pack trembles as golden-cyan SSR light cracks through the central elemental seal.\n"
            "- Frame 3 (Bottom-Left): A razor slash of golden light rips across the top edge of the card pack.\n"
            "- Frame 4 (Bottom-Right): The card pack bursts open in a radiant fountain of golden-crimson-cyan rays and floating card silhouettes.\n"
            "RULES: Centered inside each cell with generous margin, zero cell clipping, NO text, NO blue guide lines, 100% flat solid #FF00FF background."
        ),
        [str(LAYOUT_2X2)],
        pack_raw,
        new_thread=True,
    )
    if pack_raw.exists() and not pack_files[-1].exists():
        frames = split_2x2_sheet(pack_raw, pack_files, cell_canvas_size=(256, 256), inner_fit=(224, 224))
        sheet = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        for i, fim in enumerate(frames):
            sheet.paste(fim, ((i % 2) * 256, (i // 2) * 256), fim)
        sheet.save(gdir / "card_pack_opening_2x2.png")

    for p in list(adir.glob("*.png")) + list(bdir.glob("*.png")) + list(gdir.glob("*.png")):
        Image.open(p).convert("RGBA").save(mdir / f"{p.stem}.webp", format="WEBP", quality=90)

    # QC Board for Category 4
    f_title = load_font(20)
    f_sub = load_font(13)
    qc = Image.new("RGB", (1520, 720), (13, 17, 23))
    draw = ImageDraw.Draw(qc)
    draw.text((24, 16), "QC HẠNG MỤC 4: KHUNG AVATAR NGƯỜI CHƠI (100 HP) + THANH HP/MANA/KHIÊN + ĐỒNG HỒ + GÓI BÀI GACHA (2x2)", fill=(245, 158, 11), font=f_title)

    rows_data = [
        ("1. Khung Avatar Người Chơi & Lịch Sử Bài Mở", av_files, ["Avatar 100 HP", "Bị Đánh Trực Tiếp", "Bị Loại (0 HP)", "Nút Bài Đã Mở"]),
        ("2. Thanh Máu/Mana/Khiên Tướng & Đồng Hồ Trận Đấu", hud_files, ["Thanh HP & Mana", "Khung Bọc Khiên", "Đồng Hồ 15s Chuẩn Bị", "Đồng Hồ 15s Chiến Đấu"]),
        ("3. Animation Mở Gói Bài Gacha (10 Thẻ / Pack)", pack_files, ["F1: Gói Nguyên Seal", "F2: Nứt Ấn SSR", "F3: Xé Đỉnh Gói", "F4: Bung Nổ Hào Quang"]),
    ]
    for r_i, (rtitle, flist, lbls) in enumerate(rows_data):
        by = 56 + r_i * 214
        draw.rectangle([24, by, 1496, by + 200], fill=(22, 27, 34), outline=(48, 54, 61), width=2)
        draw.text((40, by + 12), rtitle, fill=(245, 158, 11), font=f_sub)
        for c_i, (fp, lbl) in enumerate(zip(flist, lbls)):
            cx = 420 + c_i * 262
            cy = by + 14
            draw.rectangle([cx, cy, cx + 244, cy + 172], fill=(13, 17, 23), outline=(88, 166, 255), width=1)
            if fp.exists():
                fim = Image.open(fp).convert("RGBA")
                sc = min(160 / max(1, fim.width), 130 / max(1, fim.height))
                fr = fim.resize((max(1, int(fim.width * sc)), max(1, int(fim.height * sc))), Image.Resampling.LANCZOS)
                qc.paste(fr, (cx + (244 - fr.width) // 2, cy + 32 + (132 - fr.height) // 2), fr)
            draw.text((cx + 10, cy + 8), lbl, fill=(230, 237, 243), font=f_sub)

    qc.save(qdir / "qc_category4_ui_hud_and_gacha_pack.png")
    print("[Category 4] UI HUD, Player Avatars, Timers & Gacha Pack complete!")


# ==============================================================================
# INTERACTIVE HTML GAME WORLD & BATTLE BOARD VIEWER
# ==============================================================================
def build_game_world_viewer():
    data = {
        "board_bg": b64_uri(BOARD_DIR / "poker_battle_table_square_1024x1024.png"),
        "slots": [b64_uri(BOARD_DIR / "slots" / f) for f in ("slot_1_empty.png", "slot_2_facedown.png", "slot_3_active_hero.png", "slot_4_trigger_break.png")],
        "props": [b64_uri(BOARD_DIR / "props" / f) for f in ("prop_1_shared_chaos_deck.png", "prop_2_freeze_pause_crystal.png", "prop_3_sudden_death_brazier.png", "prop_4_wuxing_synergy_seal.png")],
        "phys_proj": [b64_uri(VFX_ELEM_DIR / "physical_projectiles" / f) for f in ("proj_arrow.png", "proj_crossbow_bolt.png", "proj_harpoon_javelin.png", "proj_spinning_chakram.png")],
        "elements": {
            e["id"]: {
                "name": e["name"],
                "proj": [b64_uri(VFX_ELEM_DIR / e["id"] / f"projectile_{i}.png") for i in range(4)],
                "impact": [b64_uri(VFX_ELEM_DIR / e["id"] / f"impact_{i}.png") for i in range(3)],
                "aura": b64_uri(VFX_ELEM_DIR / e["id"] / "synergy_aura.png"),
            }
            for e in ELEMENTS_SPEC
        },
        "summons": {
            s["id"]: {
                "name": s["name"],
                "card_ref": s["card_ref"],
                "frames": [b64_uri(SUMMONS_DIR / s["id"] / "parts" / f"anim_{i}.png") for i in range(4)],
            }
            for s in SUMMON_SPECS
        },
        "avatars": [b64_uri(UI_HUD_DIR / "avatars" / f) for f in ("avatar_1_active_100hp.png", "avatar_2_direct_hit.png", "avatar_3_eliminated_0hp.png", "icon_played_history_scroll.png")],
        "hud_bars": [b64_uri(UI_HUD_DIR / "hud_bars" / f) for f in ("unit_hp_mana_bar_frame.png", "unit_shield_overlay_frame.png", "timer_prep_15s_compass.png", "timer_combat_15s_crossed_swords.png")],
        "gacha_pack": [b64_uri(UI_HUD_DIR / "gacha_pack" / f"pack_{i}_{s}.png") for i, s in enumerate(("sealed", "cracking", "ripping", "burst_open"))],
    }

    (ROOT / "assets/game_world_data.js").write_text(
        "// Auto-generated by tools/forge_remaining_game_assets.py — DO NOT READ IN AI CONTEXT\n"
        f"window.GAME_WORLD_ASSETS = {json.dumps(data, ensure_ascii=True)};\n",
        encoding="utf-8",
    )

    (ROOT / "assets/game_world_viewer.html").write_text('''<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8" />
<title>Arcana Five (Card_G) — Trình Xem Bàn Cờ Poker, Đạn 5 Hệ, Đệ Triệu Hồi & UI HUD</title>
<style>
  body { margin: 0; background: #0d1117; color: #e6edf3; font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding-bottom: 40px; }
  header { padding: 14px 24px; background: #161b22; border-bottom: 1px solid #30363d; display: flex; justify-content: space-between; align-items: center; }
  h1 { margin: 0; font-size: 18px; color: #f59e0b; }
  h2 { margin: 24px 24px 12px; font-size: 16px; color: #58a6ff; border-left: 4px solid #f59e0b; padding-left: 10px; }
  .row { display: flex; gap: 16px; flex-wrap: wrap; padding: 0 24px; }
  .box { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 12px; display: flex; flex-direction: column; align-items: center; gap: 8px; min-width: 180px; }
  .box img { max-width: 160px; max-height: 160px; object-fit: contain; }
  .board-preview { width: 640px; height: 640px; object-fit: cover; margin: 0 24px; border: 2px solid #f59e0b; border-radius: 12px; }
  .lbl { font-size: 12px; color: #8b949e; text-align: center; }
</style>
</head>
<body>
<header>
  <h1>Arcana Five — Tổng Hợp 4 Hạng Mục Đồ Họa Sân Đấu, Đạn Ngũ Hành, Đệ Triệu Hồi & UI/Gacha Pack</h1>
  <span style="font-size:12px;color:#3fb950">100% Assets Ready</span>
</header>
<h2>1. Mặt Bàn Poker Hình Vuông 4 Cạnh Đối Xứng (1024x1024 RGB) + 4 Trạng Thái Ô Bài + Props</h2>
<img id="board_bg" class="board-preview" />
<div class="row" id="board_items" style="margin-top:14px"></div>
<h2>2. Đạn Vật Lý Tầm Xa + Đạn Phép, Nổ Impact & Hào Quang Tương Sinh 5 Hệ Ngũ Hành</h2>
<div class="row" id="vfx_items"></div>
<h2>3. Đơn Vị Triệu Hồi Phụ Trên Sân (Animation 4-Frame)</h2>
<div class="row" id="summon_items"></div>
<h2>4. Giao Diện HUD Chiến Đấu, Khung Avatar 100 HP & Mở Gói Bài Gacha (Animation 4-Frame)</h2>
<div class="row" id="hud_items"></div>
<script src="game_world_data.js"></script>
<script>
  const D = window.GAME_WORLD_ASSETS;
  document.getElementById("board_bg").src = D.board_bg;
  const bRow = document.getElementById("board_items");
  ["Ô Trống", "Đang Úp Bài", "Duy Trì Tướng", "Kích Hoạt / Vỡ"].forEach((t, i) => {
    bRow.innerHTML += `<div class="box"><img src="${D.slots[i]}"/><div class="lbl">${t}</div></div>`;
  });
  ["Bộ Bài Chung", "Ấn Đóng Băng 15s", "Đài Tử Chiến 60s", "Ấn Ngũ Hành"].forEach((t, i) => {
    bRow.innerHTML += `<div class="box"><img src="${D.props[i]}"/><div class="lbl">${t}</div></div>`;
  });
  const vRow = document.getElementById("vfx_items");
  ["Mũi Tên", "Đạn Nỏ", "Lao Móc", "Phiến Luân"].forEach((t, i) => {
    vRow.innerHTML += `<div class="box"><img src="${D.phys_proj[i]}"/><div class="lbl">${t}</div></div>`;
  });
  const anims = [];
  Object.entries(D.elements).forEach(([k, v]) => {
    vRow.innerHTML += `
      <div class="box"><img id="ep_${k}" src="${v.proj[0]}"/><div class="lbl">${v.name} — Đạn (4F)</div></div>
      <div class="box"><img id="ei_${k}" src="${v.impact[0]}"/><div class="lbl">${v.name} — Nổ Impact</div></div>
      <div class="box"><img src="${v.aura}"/><div class="lbl">${v.name} — Hào Quang</div></div>
    `;
  });
  const sRow = document.getElementById("summon_items");
  Object.entries(D.summons).forEach(([k, v]) => {
    sRow.innerHTML += `<div class="box"><img id="sum_${k}" src="${v.frames[0]}"/><div class="lbl"><b>${v.name}</b><br/>(${v.card_ref})</div></div>`;
  });
  const hRow = document.getElementById("hud_items");
  ["Avatar 100 HP", "Avatar Bị Đánh", "Avatar Bị Loại", "Nút Bài Đã Mở"].forEach((t, i) => {
    hRow.innerHTML += `<div class="box"><img src="${D.avatars[i]}"/><div class="lbl">${t}</div></div>`;
  });
  ["Thanh HP/Mana", "Khung Bọc Khiên", "Đồng Hồ 15s Prep", "Đồng Hồ 15s Combat"].forEach((t, i) => {
    hRow.innerHTML += `<div class="box"><img src="${D.hud_bars[i]}"/><div class="lbl">${t}</div></div>`;
  });
  hRow.innerHTML += `<div class="box"><img id="gacha_anim" src="${D.gacha_pack[0]}"/><div class="lbl"><b>Mở Gói Bài Gacha (4F)</b></div></div>`;

  let tick = 0;
  setInterval(() => {
    tick++;
    Object.entries(D.elements).forEach(([k, v]) => {
      document.getElementById("ep_" + k).src = v.proj[tick % 4];
      document.getElementById("ei_" + k).src = v.impact[tick % 3];
    });
    Object.entries(D.summons).forEach(([k, v]) => {
      document.getElementById("sum_" + k).src = v.frames[tick % 4];
    });
    document.getElementById("gacha_anim").src = D.gacha_pack[tick % 4];
  }, 220);
</script>
</body>
</html>
''', encoding="utf-8")
    print("[Viewer] assets/game_world_viewer.html & assets/game_world_data.js generated!")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", type=str, default="all", help="1, 2, 3, 4, or all")
    args = parser.parse_args()
    cat = args.category.lower()
    if cat in ("1", "all"):
        forge_category_1_board()
    if cat in ("2", "all"):
        forge_category_2_vfx()
    if cat in ("3", "all"):
        forge_category_3_summons()
    if cat in ("4", "all"):
        forge_category_4_ui_hud()
    if cat in ("all", "1", "viewer"):
        build_game_world_viewer()


if __name__ == "__main__":
    main()
