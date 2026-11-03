#!/usr/bin/env python3
"""
Forge Pipeline for the Final 25 Cards (C076 - C100):
- C076 - C080: Final 5 Support Hero Cards (forged as W076-W080 Hero Weapons + linked into the 25-Card Item/Effect Registry)
- C081 - C100: All 20 Instant Item Cards (Nhóm 5: Thẻ Vật Phẩm Tức Thời)
  * Generates 2x2 Use/Activation Spritesheet on #FF00FF with layout_guide_2x2.png
  * Generates 884x632 RGB Card Preview (and 354x253 WebP) from the item reference
  * Generates & links 10 Shared 16x16 Status Effect Icons (grouped across items with the same status type)
  * Builds per-item QC boards, master 25-item overview board, Godot resources, and interactive HTML viewer.
"""
import argparse
import base64
import io
import json
import pathlib
import shutil
import sys
import urllib.request
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path("/Users/dochung/Desktop/card_g")
sys.path.insert(0, str(ROOT / "tools"))
from forge_weapon import (
    LAYOUT_1X1,
    LAYOUT_2X2,
    muse_post,
    unmix_magenta_rgba,
    keep_largest_component_and_crop,
    forge_single_weapon,
)

ITEMS_DIR = ROOT / "assets/items"
STATUS_DIR = ITEMS_DIR / "status_icons"
MOBILE_ITEMS_DIR = ROOT / "assets/mobile/items"
MOBILE_STATUS_DIR = ROOT / "assets/mobile/items/status_icons"

# ==============================================================================
# 1. 10 SHARED 16x16 STATUS EFFECT ICONS (GROUPED ACROSS C076 - C100)
# ==============================================================================
SHARED_STATUS_GROUPS = {
    "status_heal_cleanse": {
        "id": "status_heal_cleanse",
        "name": "Hồi Phục & Thanh Tẩy (Heal / Cleanse / Revive)",
        "shared_by": ["C077", "C079", "C081", "C097"],
        "sheet_group": 1,
        "cell_index": 0,
        "desc": "Hồi máu, Thanh tẩy Debuff hoặc Bảo hộ Phục sinh",
    },
    "status_shield_bastion": {
        "id": "status_shield_bastion",
        "name": "Khiên Chắn & Thạch Giáp (Shield / Stone Armor)",
        "shared_by": ["C078", "C085", "C092", "C094"],
        "sheet_group": 1,
        "cell_index": 1,
        "desc": "Tăng Khiên (Shield), Giáp/Kháng phép và Miễn nhiễm khống chế",
    },
    "status_haste_frenzy": {
        "id": "status_haste_frenzy",
        "name": "Gia Tốc & Cuồng Nộ (ASPD / MSPD / War Frenzy)",
        "shared_by": ["C083", "C084", "C087"],
        "sheet_group": 1,
        "cell_index": 2,
        "desc": "Tăng Tốc độ đánh (ASPD), Tốc độ di chuyển (MSPD) và Sát thương",
    },
    "status_vamp_bleed": {
        "id": "status_vamp_bleed",
        "name": "Huyết Nha & Chảy Máu (Lifesteal / Bleed)",
        "shared_by": ["C082", "C090"],
        "sheet_group": 1,
        "cell_index": 3,
        "desc": "Gây Chảy máu theo giây trên địch hoặc Hút máu (Vamp) cho đồng minh",
    },
    "status_stun_shackle": {
        "id": "status_stun_shackle",
        "name": "Choáng Sét & Trói Hồn (Stun / Root Shackles)",
        "shared_by": ["C086", "C089"],
        "sheet_group": 2,
        "cell_index": 0,
        "desc": "Khống chế cứng: Làm Choáng (Stun) hoặc Trói chân (Root) ngắt tích Mana",
    },
    "status_corrosion_curse": {
        "id": "status_corrosion_curse",
        "name": "Ăn Mòn Giáp & Chuyển Nguyền (Corrosion / Anti-Heal / Hex)",
        "shared_by": ["C076", "C088"],
        "sheet_group": 2,
        "cell_index": 1,
        "desc": "Giảm 50% nhận hồi máu, trừ Giáp/Kháng phép và phản/nhận Bùa Nguyền",
    },
    "status_silence_manalock": {
        "id": "status_silence_manalock",
        "name": "Câm Lặng & Khóa/Đổi Mana (Silence / Mana Lock & Swap)",
        "shared_by": ["C091", "C096"],
        "sheet_group": 2,
        "cell_index": 2,
        "desc": "Xóa/Hoán đổi Mana và Khóa không cho mục tiêu tích Mana",
    },
    "status_time_chrono": {
        "id": "status_time_chrono",
        "name": "Ngưng Đọng & Ngược Thời Gian (Time Slow / Rewind)",
        "shared_by": ["C080", "C093"],
        "sheet_group": 2,
        "cell_index": 3,
        "desc": "Làm chậm 45% ASPD & MSPD toàn đội địch hoặc Quay ngược thời gian",
    },
    "status_mirror_reflect": {
        "id": "status_mirror_reflect",
        "name": "Gương Hồn Phản Phệ & Sao Chép (Mirror Reflect / Copy)",
        "shared_by": ["C095", "C099"],
        "sheet_group": 3,
        "cell_index": 0,
        "desc": "Phản lại 40% sát thương nhận vào + nổ phản phệ hoặc Sao chép Item",
    },
    "status_shield_break": {
        "id": "status_shield_break",
        "name": "Phá Thuẫn & Khắc Hệ Ngũ Hành (Shield Break / Element Shift)",
        "shared_by": ["C098", "C100"],
        "sheet_group": 3,
        "cell_index": 1,
        "desc": "Phá hủy 100% Khiên (+150% sát thương lên Khiên) & Đổi Hệ Tương Khắc",
    },
}

STATUS_SHEET_PROMPTS = {
    1: (
        "Create a 2x2 grid sprite sheet of 4 distinct bold RPG status effect icons on a flat solid pure magenta (#FF00FF) background, "
        "strictly following the 4 cells of the attached layout_guide_2x2.png.\n"
        "- Top-Left Cell (Cell 1): A glowing emerald-green and golden-white Salvation Cross with a life droplet (Heal & Cleanse icon).\n"
        "- Top-Right Cell (Cell 2): A sturdy golden-cyan runic Aegis Bastion Shield emblem (Shield & Stone Armor buff icon).\n"
        "- Bottom-Left Cell (Cell 3): A blazing fiery-orange and golden winged sword-boot emblem (Attack Speed & War Frenzy Haste icon).\n"
        "- Bottom-Right Cell (Cell 4): Twin sharp crimson-red vampire fangs dripping a dark blood drop (Bleed & Lifesteal Vamp icon).\n"
        "RULES: Bold chunky readable silhouette suitable for downscaling to 16x16 pixel icon, thick dark outlines, centered inside each cell with generous margin, "
        "NO text, NO blue guide lines, 100% flat solid #FF00FF background."
    ),
    2: (
        "Create a 2x2 grid sprite sheet of 4 distinct bold RPG status effect icons on a flat solid pure magenta (#FF00FF) background, "
        "strictly following the 4 cells of the attached layout_guide_2x2.png.\n"
        "- Top-Left Cell (Cell 1): Electric yellow-cyan lightning bolt striking iron soul-shackle chains (Stun & Root Shackle debuff icon).\n"
        "- Top-Right Cell (Cell 2): A cracked bronze shield melting with toxic acid-green skull fumes (Armor Corrosion & Anti-Heal Hex icon).\n"
        "- Bottom-Left Cell (Cell 3): A dark void-indigo padlock sealing a glowing blue mana crystal with an X chains seal (Silence & Mana Lock icon).\n"
        "- Bottom-Right Cell (Cell 4): A glowing cyan-and-amber chronos hourglass encircled by a slow clock gear (Time Slow & Rewind icon).\n"
        "RULES: Bold chunky readable silhouette suitable for downscaling to 16x16 pixel icon, thick dark outlines, centered inside each cell with generous margin, "
        "NO text, NO blue guide lines, 100% flat solid #FF00FF background."
    ),
    3: (
        "Create a 2x2 grid sprite sheet of 4 bold RPG status effect icons on a flat solid pure magenta (#FF00FF) background, "
        "strictly following the 4 cells of the attached layout_guide_2x2.png.\n"
        "- Top-Left Cell (Cell 1): A spiked golden-violet octagonal mirror heart reflecting a fiery arrow (Mirror Damage Reflect & Copy icon).\n"
        "- Top-Right Cell (Cell 2): A golden spearhead shattering a cyan barrier shield in half with a five-element pentagram spark (Shield Break & Element Shift icon).\n"
        "- Bottom-Left Cell (Cell 3): A golden-emerald phoenix feather aura emblem.\n"
        "- Bottom-Right Cell (Cell 4): A crimson-gold battle banner emblem.\n"
        "RULES: Bold chunky readable silhouette suitable for downscaling to 16x16 pixel icon, thick dark outlines, centered inside each cell with generous margin, "
        "NO text, NO blue guide lines, 100% flat solid #FF00FF background."
    ),
}

# ==============================================================================
# 2. SPECIFICATIONS FOR ALL 25 FINAL CARDS (C076 - C100)
# ==============================================================================
FINAL_25_CARDS = [
    # --- Part A: Final 5 Support Heroes (C076 - C080) ---
    {
        "id": "c076",
        "weapon_id": "w076",
        "slug": "c076_chua_te_chuyen_nguyen",
        "weapon_slug": "w076_chua_te_chuyen_nguyen",
        "name": "C076 — Chúa Tể Chuyển Nguyền (Chuyển Họa Vi Phúc)",
        "tier": "S",
        "category": "Support Hero / Active Skill",
        "tag": "ReflectCurse",
        "status_id": "status_corrosion_curse",
        "effect_summary": "Hút toàn bộ hiệu ứng xấu trên người đồng minh, ném trả sang kẻ địch gần nhất và hồi 100 HP.",
    },
    {
        "id": "c077",
        "weapon_id": "w077",
        "slug": "c077_ke_trao_doi_menh",
        "weapon_slug": "w077_ke_trao_doi_menh",
        "name": "C077 — Kẻ Trao Đổi Mệnh (Cân Bằng Sinh Mệnh)",
        "tier": "S",
        "category": "Support Hero / Active Skill",
        "tag": "SpiritBalance",
        "status_id": "status_heal_cleanse",
        "effect_summary": "Cộng tổng %HP của mọi đồng minh còn sống rồi chia đều lại %HP cho tất cả, hồi thêm 75 HP mỗi người.",
    },
    {
        "id": "c078",
        "weapon_id": "w078",
        "slug": "c078_ke_cap_khien_co_dai",
        "weapon_slug": "w078_ke_cap_khien_co_dai",
        "name": "C078 — Kẻ Cắp Khiên Cổ Đại (Đoạt Thuẫn Hóa Linh)",
        "tier": "SSR",
        "category": "Support Hero / Active Skill",
        "tag": "ShieldSteal",
        "status_id": "status_shield_bastion",
        "effect_summary": "Đánh cắp toàn bộ Khiên của kẻ địch nhiều Khiên nhất chuyển cho đội mình, bơm +30 Mana cả đội.",
    },
    {
        "id": "c079",
        "weapon_id": "w079",
        "slug": "c079_thanh_nu_hoi_sinh",
        "weapon_slug": "w079_thanh_nu_hoi_sinh",
        "name": "C079 — Thánh Nữ Hồi Sinh (Khế Ước Phục Sinh)",
        "tier": "SSR",
        "category": "Support Hero / Active Skill",
        "tag": "Revive",
        "status_id": "status_heal_cleanse",
        "effect_summary": "Hồi 160 HP toàn đội; nếu có đồng minh vừa tử trận sẽ hồi sinh chiến đấu tiếp với 35% HP.",
    },
    {
        "id": "c080",
        "weapon_id": "w080",
        "slug": "c080_ke_giu_nga_re",
        "weapon_slug": "w080_ke_giu_nga_re",
        "name": "C080 — Kẻ Giữ Ngã Rẽ (Quay Lại Ngã Rẽ)",
        "tier": "SSR",
        "category": "Support Hero / Active Skill",
        "tag": "TimeRewind",
        "status_id": "status_time_chrono",
        "effect_summary": "Đưa HP và Mana của toàn bộ đồng minh còn sống quay ngược về đúng trạng thái của 4 giây trước.",
    },
    # --- Part B: 20 Instant Item Cards (C081 - C100) ---
    {
        "id": "c081",
        "slug": "c081_linh_duoc_hac_huyet",
        "name": "C081 — Linh Dược Hắc Huyết (Item Hồi Máu · InstantHeal)",
        "tier": "N",
        "category": "Instant Item",
        "tag": "InstantHeal",
        "status_id": "status_heal_cleanse",
        "effect_summary": "Đồng minh %HP thấp nhất: Hồi ngay 160 HP (+30% HP đã mất) và xóa 1 hiệu ứng làm chậm/thiêu đốt.",
        "prompt_use_2x2": (
            "Create a 2x2 sprite sheet (4 frames: row 1 left-to-right, row 2 left-to-right) on a flat solid pure magenta (#FF00FF) background, "
            "strictly following the attached layout_guide_2x2.png.\n"
            "SUBJECT: Dark-Fantasy Item C081 'Linh Dược Hắc Huyết' (Black-Blood Vitality Elixir Vial) activation animation:\n"
            "- Frame 1 (Top-Left): An ornate gothic silver-caged glass potion flask filled with glowing crimson-and-gold vitality elixir.\n"
            "- Frame 2 (Top-Right): The cork pops with a burst of golden-emerald and crimson healing runes swirling around the vial.\n"
            "- Frame 3 (Bottom-Left): The flask shatters into a radiant upward fountain of crimson-gold life essence and cleansing light.\n"
            "- Frame 4 (Bottom-Right): Expanding golden-emerald salvation cross aura and floating vitality droplets.\n"
            "RULES: Keep each frame centered inside its cell with generous margin, zero cell clipping, NO blue guide lines, NO pink/magenta on the item, 100% solid #FF00FF background."
        ),
        "prompt_card": (
            "Wide horizontal 16:11 dark-fantasy card illustration (884x632, 100% opaque RGB painting, NO magenta, NO card frame) featuring "
            "the exact same Gothic Silver-Caged Black-Blood Vitality Elixir Vial (Linh Dược Hắc Huyết - C081) from the attached reference image.\n"
            "Show the ornate crimson-and-gold potion flask in the foreground on a dark stone war-altar as golden-emerald cleansing light and vitality ribbons burst from it."
        ),
    },
    {
        "id": "c082",
        "slug": "c082_bom_gai_co_ngu",
        "name": "C082 — Bom Gai Cổ Ngữ (Item Sát Thương · BlastAoE)",
        "tier": "N",
        "category": "Instant Item",
        "tag": "BlastAoE",
        "status_id": "status_vamp_bleed",
        "effect_summary": "Cụm kẻ địch đông nhất: Phát nổ gây 125 sát thương ma pháp diện rộng và làm chảy máu 15 HP/s trong 3s.",
        "prompt_use_2x2": (
            "Create a 2x2 sprite sheet (4 frames: row 1 left-to-right, row 2 left-to-right) on a flat solid pure magenta (#FF00FF) background, "
            "strictly following the attached layout_guide_2x2.png.\n"
            "SUBJECT: Dark-Fantasy Item C082 'Bom Gai Cổ Ngữ' (Runic Spiked Shrapnel Bomb) activation animation:\n"
            "- Frame 1 (Top-Left): A heavy blackened-iron spiked sphere bomb etched with glowing fiery-orange and crimson blood runes and a burning fuse.\n"
            "- Frame 2 (Top-Right): The runic cracks blaze bright orange-red as the spiked iron shell bulges outward.\n"
            "- Frame 3 (Bottom-Left): Violent dark-fantasy explosion of fiery-orange blast waves and flying jagged iron spikes.\n"
            "- Frame 4 (Bottom-Right): Expanding ring of razor shrapnel spikes and crimson bleeding slash marks.\n"
            "RULES: Keep each frame centered inside its cell with generous margin, zero cell clipping, NO blue guide lines, NO pink/magenta on the item, 100% solid #FF00FF background."
        ),
        "prompt_card": (
            "Wide horizontal 16:11 dark-fantasy card illustration (884x632, 100% opaque RGB painting, NO magenta, NO card frame) featuring "
            "the exact same Runic Spiked Iron Bomb (Bom Gai Cổ Ngữ - C082) from the attached reference image.\n"
            "Show the spiked blackened-iron sphere glowing with fiery-orange and blood-red runes mid-detonation over a dark stone battlefield with flying iron spikes."
        ),
    },
    {
        "id": "c083",
        "slug": "c083_binh_linh_luc_vun",
        "name": "C083 — Bình Linh Lực Vụn (Item Bơm Mana · ManaPotion)",
        "tier": "N",
        "category": "Instant Item",
        "tag": "ManaPotion",
        "status_id": "status_haste_frenzy",
        "effect_summary": "Đồng minh %Mana thấp nhất: Bơm ngay +45 Mana và tăng +15% Tốc độ đánh trong 4 giây.",
        "prompt_use_2x2": (
            "Create a 2x2 sprite sheet (4 frames: row 1 left-to-right, row 2 left-to-right) on a flat solid pure magenta (#FF00FF) background, "
            "strictly following the attached layout_guide_2x2.png.\n"
            "SUBJECT: Dark-Fantasy Item C083 'Bình Linh Lực Vụn' (Shattered Aether-Shard Mana Flask) activation animation:\n"
            "- Frame 1 (Top-Left): A faceted crystal alchemy bottle brass-bound and filled with glowing sapphire-blue mana crystal shards.\n"
            "- Frame 2 (Top-Right): Brilliant cyan-blue arcane lightning and golden haste sparks erupt from the bottle neck.\n"
            "- Frame 3 (Bottom-Left): A swirling vortex of sapphire mana streams and golden attack-speed wind blades bursts outward.\n"
            "- Frame 4 (Bottom-Right): Radiant cyan mana halo and ascending aether crystals.\n"
            "RULES: Keep each frame centered inside its cell with generous margin, zero cell clipping, NO blue guide lines, NO pink/magenta on the item, 100% solid #FF00FF background."
        ),
        "prompt_card": (
            "Wide horizontal 16:11 dark-fantasy card illustration (884x632, 100% opaque RGB painting, NO magenta, NO card frame) featuring "
            "the exact same Brass-Bound Sapphire Mana Shard Flask (Bình Linh Lực Vụn - C083) from the attached reference image.\n"
            "Show the glowing blue crystal mana flask unleashing streams of sapphire aether energy and golden haste sparks in a dark arcane chamber."
        ),
    },
    {
        "id": "c084",
        "slug": "c084_bua_gia_toc_hac_phong",
        "name": "C084 — Bùa Gia Tốc Hắc Phong (Item Tăng Tốc · SpeedRune)",
        "tier": "N",
        "category": "Instant Item",
        "tag": "SpeedRune",
        "status_id": "status_haste_frenzy",
        "effect_summary": "Đồng minh MSPD thấp nhất: Tăng +40% Tốc độ di chuyển và +25% Tốc độ đánh trong 6 giây.",
        "prompt_use_2x2": (
            "Create a 2x2 sprite sheet (4 frames: row 1 left-to-right, row 2 left-to-right) on a flat solid pure magenta (#FF00FF) background, "
            "strictly following the attached layout_guide_2x2.png.\n"
            "SUBJECT: Dark-Fantasy Item C084 'Bùa Gia Tốc Hắc Phong' (Black-Gale Haste Talisman) activation animation:\n"
            "- Frame 1 (Top-Left): An obsidian-and-bronze winged wind talisman tablet carved with glowing turquoise-jade gale runes.\n"
            "- Frame 2 (Top-Right): The talisman ignites with swirling turquoise wind-blades and golden lightning streaks.\n"
            "- Frame 3 (Bottom-Left): A high-speed vortex of emerald-turquoise gale wings andsonic shockwaves expands outward.\n"
            "- Frame 4 (Bottom-Right): Twin glowing turquoise wind-wings and speed afterimage trails.\n"
            "RULES: Keep each frame centered inside its cell with generous margin, zero cell clipping, NO blue guide lines, NO pink/magenta on the item, 100% solid #FF00FF background."
        ),
        "prompt_card": (
            "Wide horizontal 16:11 dark-fantasy card illustration (884x632, 100% opaque RGB painting, NO magenta, NO card frame) featuring "
            "the exact same Obsidian Winged Black-Gale Talisman (Bùa Gia Tốc Hắc Phong - C084) from the attached reference image.\n"
            "Show the winged bronze-and-obsidian rune tablet surrounded by razor-sharp turquoise gale vortices and golden speed trails in a stormy dark-fantasy canyon."
        ),
    },
    {
        "id": "c085",
        "slug": "c085_binh_thach_thuan_nho",
        "name": "C085 — Bình Thạch Thuẫn Nhỏ (Item Tạo Khiên · MiniShield)",
        "tier": "N",
        "category": "Instant Item",
        "tag": "MiniShield",
        "status_id": "status_shield_bastion",
        "effect_summary": "Đồng minh %HP thấp nhất chưa có Khiên: Cấp ngay lớp 150 Khiên (Shield) tồn tại trong 6 giây.",
        "prompt_use_2x2": (
            "Create a 2x2 sprite sheet (4 frames: row 1 left-to-right, row 2 left-to-right) on a flat solid pure magenta (#FF00FF) background, "
            "strictly following the attached layout_guide_2x2.png.\n"
            "SUBJECT: Dark-Fantasy Item C085 'Bình Thạch Thuẫn Nhỏ' (Stone-Aegis Barrier Flask) activation animation:\n"
            "- Frame 1 (Top-Left): A heavy armoured granite-and-brass potion vessel shaped like a miniature shield filled with glowing amber-gold liquid stone.\n"
            "- Frame 2 (Top-Right): Golden-amber geometric runes erupt around the stone flask as it cracks open with power.\n"
            "- Frame 3 (Bottom-Left): A dome of interlocking golden-amber and stone hexagonal shield plates materializes outward.\n"
            "- Frame 4 (Bottom-Right): A complete glowing golden-stone bastard shield barrier emblem.\n"
            "RULES: Keep each frame centered inside its cell with generous margin, zero cell clipping, NO blue guide lines, NO pink/magenta on the item, 100% solid #FF00FF background."
        ),
        "prompt_card": (
            "Wide horizontal 16:11 dark-fantasy card illustration (884x632, 100% opaque RGB painting, NO magenta, NO card frame) featuring "
            "the exact same Granite-and-Brass Stone-Aegis Flask (Bình Thạch Thuẫn Nhỏ - C085) from the attached reference image.\n"
            "Show the shield-shaped stone alchemy vessel projecting a glowing golden-amber hexagonal barrier dome across a dark dungeon floor."
        ),
    },
    {
        "id": "c086",
        "slug": "c086_bua_set_te_liet",
        "name": "C086 — Bùa Sét Tê Liệt (Item Làm Choáng · ZapStun)",
        "tier": "N",
        "category": "Instant Item",
        "tag": "ZapStun",
        "status_id": "status_stun_shackle",
        "effect_summary": "Kẻ địch %Mana cao nhất: Giáng sét gây 95 sát thương phép và làm Choáng 1.2 giây (ngắt nhịp tích Mana).",
        "prompt_use_2x2": (
            "Create a 2x2 sprite sheet (4 frames: row 1 left-to-right, row 2 left-to-right) on a flat solid pure magenta (#FF00FF) background, "
            "strictly following the attached layout_guide_2x2.png.\n"
            "SUBJECT: Dark-Fantasy Item C086 'Bùa Sét Tê Liệt' (Paralyzing Thunder-Strike Talisman) activation animation:\n"
            "- Frame 1 (Top-Left): A jagged dark-iron and copper lightning rod talisman inscribed with crackling electric cyan-gold thunder runes.\n"
            "- Frame 2 (Top-Right): The talisman supercharges with blinding cyan-yellow lightning arcs.\n"
            "- Frame 3 (Bottom-Left): A massive vertical bolt of cyan-gold thunder strikes downward in a shattering electric impact.\n"
            "- Frame 4 (Bottom-Right): Crackling electric paralysis rings and dizzying golden stun stars.\n"
            "RULES: Keep each frame centered inside its cell with generous margin, zero cell clipping, NO blue guide lines, NO pink/magenta on the item, 100% solid #FF00FF background."
        ),
        "prompt_card": (
            "Wide horizontal 16:11 dark-fantasy card illustration (884x632, 100% opaque RGB painting, NO magenta, NO card frame) featuring "
            "the exact same Dark-Iron Thunder-Strike Talisman (Bùa Sét Tê Liệt - C086) from the attached reference image.\n"
            "Show the copper-and-iron thunder rune talisman calling down a violent pillar of cyan-and-gold lightning onto a dark battlefield."
        ),
    },
    {
        "id": "c087",
        "slug": "c087_chien_ky_cuong_no",
        "name": "C087 — Chiến Kỳ Cuồng Nộ (Item Buff Công · WarBanner)",
        "tier": "R",
        "category": "Instant Item",
        "tag": "WarBanner",
        "status_id": "status_haste_frenzy",
        "effect_summary": "Đồng minh Dame cao nhất (7s): Tăng +25% Dame, +25% Tốc độ đánh và +20% Hút máu.",
        "prompt_use_2x2": (
            "Create a 2x2 sprite sheet (4 frames: row 1 left-to-right, row 2 left-to-right) on a flat solid pure magenta (#FF00FF) background, "
            "strictly following the attached layout_guide_2x2.png.\n"
            "SUBJECT: Dark-Fantasy Item C087 'Chiến Kỳ Cuồng Nộ' (Blood-Rage War Banner) activation animation:\n"
            "- Frame 1 (Top-Left): A battle-scarred iron spear-standard bearing a tattered crimson-and-gold war banner with a roaring horned skull crest.\n"
            "- Frame 2 (Top-Right): The war banner slams into the ground, igniting with blazing fiery-orange and crimson berserker flames.\n"
            "- Frame 3 (Bottom-Left): A fierce shockwave of fiery golden-red battle runes and crossed-sword emblems erupts outward.\n"
            "- Frame 4 (Bottom-Right): Blazing crimson-gold war aura with rising flame pillars around the planted standard.\n"
            "RULES: Keep each frame centered inside its cell with generous margin, zero cell clipping, NO blue guide lines, NO pink/magenta on the item, 100% solid #FF00FF background."
        ),
        "prompt_card": (
            "Wide horizontal 16:11 dark-fantasy card illustration (884x632, 100% opaque RGB painting, NO magenta, NO card frame) featuring "
            "the exact same Crimson-and-Gold Horned Skull War Banner (Chiến Kỳ Cuồng Nộ - C087) from the attached reference image.\n"
            "Show the iron war standard planted heroically in a scorched battlefield as waves of fiery-orange and blood-red berserker energy radiate from the banner."
        ),
    },
    {
        "id": "c088",
        "slug": "c088_bua_doc_an_mon",
        "name": "C088 — Bùa Độc Ăn Mòn (Item Phá Giáp/Hồi · Corrosion)",
        "tier": "R",
        "category": "Instant Item",
        "tag": "Corrosion",
        "status_id": "status_corrosion_curse",
        "effect_summary": "Kẻ địch HP cao nhất: Gây 110 sát thương phép, giảm 50% nhận hồi máu và trừ 30 Giáp/Kháng phép trong 6s.",
        "prompt_use_2x2": (
            "Create a 2x2 sprite sheet (4 frames: row 1 left-to-right, row 2 left-to-right) on a flat solid pure magenta (#FF00FF) background, "
            "strictly following the attached layout_guide_2x2.png.\n"
            "SUBJECT: Dark-Fantasy Item C088 'Bùa Độc Ăn Mòn' (Venom-Acid Corrosion Hex Censer) activation animation:\n"
            "- Frame 1 (Top-Left): A bone-and-corroded-bronze skull censer talisman oozing glowing toxic emerald-green venom.\n"
            "- Frame 2 (Top-Right): The skull jaws open wide, spraying pressurized streams of neon-green acid and dark-indigo curse smoke.\n"
            "- Frame 3 (Bottom-Left): A corrosive acid explosion dissolving a spectral iron shield into bubbling green-purple fumes.\n"
            "- Frame 4 (Bottom-Right): Lingering toxic green skull-cloud and shattered armor runes.\n"
            "RULES: Keep each frame centered inside its cell with generous margin, zero cell clipping, NO blue guide lines, NO pink/magenta on the item, 100% solid #FF00FF background."
        ),
        "prompt_card": (
            "Wide horizontal 16:11 dark-fantasy card illustration (884x632, 100% opaque RGB painting, NO magenta, NO card frame) featuring "
            "the exact same Bone-and-Bronze Venom Corrosion Skull Talisman (Bùa Độc Ăn Mòn - C088) from the attached reference image.\n"
            "Show the cursed skull talisman unleashing a billowing cloud of glowing acid-green venom that melts knightly armor in a dark swamp ruin."
        ),
    },
    {
        "id": "c089",
        "slug": "c089_xieng_xich_hut_hon",
        "name": "C089 — Xiềng Xích Hút Hồn (Item Khống Chế · ManaSteal)",
        "tier": "R",
        "category": "Instant Item",
        "tag": "ManaSteal",
        "status_id": "status_stun_shackle",
        "effect_summary": "Kẻ địch nhiều Mana nhất: Trói chân 3s, rút 40 Mana của mục tiêu và chuyển thành 130 Khiên cho đồng minh thấp máu nhất.",
        "prompt_use_2x2": (
            "Create a 2x2 sprite sheet (4 frames: row 1 left-to-right, row 2 left-to-right) on a flat solid pure magenta (#FF00FF) background, "
            "strictly following the attached layout_guide_2x2.png.\n"
            "SUBJECT: Dark-Fantasy Item C089 'Xiềng Xích Hút Hồn' (Soul-Siphon Iron Shackles) activation animation:\n"
            "- Frame 1 (Top-Left): Coiled blackened-iron dungeon manacles and spiked grapple hooks glowing with spectral cyan-teal soul runes.\n"
            "- Frame 2 (Top-Right): The spiked chains lash outward in a criss-cross binding snare.\n"
            "- Frame 3 (Bottom-Left): The iron shackles lock tight around a glowing blue mana orb, siphoning streams of cyan soul-mana along the chains.\n"
            "- Frame 4 (Bottom-Right): Locked spectral cyan-iron binding chains and a crystallized mana shield prism.\n"
            "RULES: Keep each frame centered inside its cell with generous margin, zero cell clipping, NO blue guide lines, NO pink/magenta on the item, 100% solid #FF00FF background."
        ),
        "prompt_card": (
            "Wide horizontal 16:11 dark-fantasy card illustration (884x632, 100% opaque RGB painting, NO magenta, NO card frame) featuring "
            "the exact same Soul-Siphon Spiked Iron Shackles (Xiềng Xích Hút Hồn - C089) from the attached reference image.\n"
            "Show the heavy runic iron chains erupting from dark dungeon flagstones, glowing with spectral cyan-blue mana energy as they bind and drain arcane power."
        ),
    },
    {
        "id": "c090",
        "slug": "c090_co_vat_huyet_nha",
        "name": "C090 — Cổ Vật Huyết Nha (Item Hút Máu · VampRelic)",
        "tier": "R",
        "category": "Instant Item",
        "tag": "VampRelic",
        "status_id": "status_vamp_bleed",
        "effect_summary": "Đồng minh cận chiến Dame cao nhất (8s): Đòn đánh thường và Skill được hút máu 35% và tăng +20 Giáp.",
        "prompt_use_2x2": (
            "Create a 2x2 sprite sheet (4 frames: row 1 left-to-right, row 2 left-to-right) on a flat solid pure magenta (#FF00FF) background, "
            "strictly following the attached layout_guide_2x2.png.\n"
            "SUBJECT: Dark-Fantasy Item C090 'Cổ Vật Huyết Nha' (Crimson Blood-Fang Vampire Relic) activation animation:\n"
            "- Frame 1 (Top-Left): An ancient gold-and-obsidian vampire dragon-fang amulet cradling a pulsing ruby blood-stone.\n"
            "- Frame 2 (Top-Right): The twin fangs awaken, surrounded by a spectral bat-winged crimson-gold blood sigil.\n"
            "- Frame 3 (Bottom-Left): Swirling ribbons of crimson blood-mist and golden armor runes spiral upward in a predatory vortex.\n"
            "- Frame 4 (Bottom-Right): Blazing crimson-gold vampire fang crest and blood-shield aura.\n"
            "RULES: Keep each frame centered inside its cell with generous margin, zero cell clipping, NO blue guide lines, NO pink/magenta on the item, 100% solid #FF00FF background."
        ),
        "prompt_card": (
            "Wide horizontal 16:11 dark-fantasy card illustration (884x632, 100% opaque RGB painting, NO magenta, NO card frame) featuring "
            "the exact same Gold-and-Obsidian Blood-Fang Vampire Relic (Cổ Vật Huyết Nha - C090) from the attached reference image.\n"
            "Show the ancient fanged ruby relic levitating above a gothic blood-chalice altar with swirling crimson-gold lifesteal energy."
        ),
    },
    {
        "id": "c091",
        "slug": "c091_an_cam_lang_hu_khong",
        "name": "C091 — Ấn Câm Lặng Hư Không (Item Khóa Mana · SilenceSeal)",
        "tier": "R",
        "category": "Instant Item",
        "tag": "SilenceSeal",
        "status_id": "status_silence_manalock",
        "effect_summary": "Kẻ địch %Mana cao nhất: Xóa 30 Mana, gây 100 sát thương phép và khóa không cho tích Mana trong 3.5 giây.",
        "prompt_use_2x2": (
            "Create a 2x2 sprite sheet (4 frames: row 1 left-to-right, row 2 left-to-right) on a flat solid pure magenta (#FF00FF) background, "
            "strictly following the attached layout_guide_2x2.png.\n"
            "SUBJECT: Dark-Fantasy Item C091 'Ấn Câm Lặng Hư Không' (Void Silence Seal Grimoire Lock) activation animation:\n"
            "- Frame 1 (Top-Left): A heavy dark-silver and obsidian octagonal seal stamp bearing a mouthless masked face locked by iron chains.\n"
            "- Frame 2 (Top-Right): Deep indigo-violet void runes and silver chains expand around the seal.\n"
            "- Frame 3 (Bottom-Left): The giant Void Silence Seal slams down, shattering blue mana crystals into dark-indigo anti-magic smoke.\n"
            "- Frame 4 (Bottom-Right): A glowing indigo-silver crossedchain X-seal locking mana completely.\n"
            "RULES: Keep each frame centered inside its cell with generous margin, zero cell clipping, NO blue guide lines, NO pink/magenta on the item, 100% solid #FF00FF background."
        ),
        "prompt_card": (
            "Wide horizontal 16:11 dark-fantasy card illustration (884x632, 100% opaque RGB painting, NO magenta, NO card frame) featuring "
            "the exact same Obsidian-and-Silver Void Silence Seal (Ấn Câm Lặng Hư Không - C091) from the attached reference image.\n"
            "Show the chained mouthless mask seal floating in a dark void rift as silver anti-magic chains crush and silence glowing mana orbs."
        ),
    },
    {
        "id": "c092",
        "slug": "c092_duoc_pham_hoa_thach",
        "name": "C092 — Dược Phẩm Hóa Thạch (Item Siêu Giáp · StoneBrew)",
        "tier": "R",
        "category": "Instant Item",
        "tag": "StoneBrew",
        "status_id": "status_shield_bastion",
        "effect_summary": "Tanker đồng minh HP cao nhất (7s): Tăng +50 Giáp, +50 Kháng phép và hồi 120 HP (giảm 15% MSPD).",
        "prompt_use_2x2": (
            "Create a 2x2 sprite sheet (4 frames: row 1 left-to-right, row 2 left-to-right) on a flat solid pure magenta (#FF00FF) background, "
            "strictly following the attached layout_guide_2x2.png.\n"
            "SUBJECT: Dark-Fantasy Item C092 'Dược Phẩm Hóa Thạch' (Gargoyle Petrification Stone-Skin Brew) activation animation:\n"
            "- Frame 1 (Top-Left): A heavy dwarven basalt-stone flagon carved like a gargoyle head, brimming with glowing amber-emerald mineral elixir.\n"
            "- Frame 2 (Top-Right): Molten amber-gold earth runes and emerald healing vapor overflow from the stone flagon.\n"
            "- Frame 3 (Bottom-Left): Massive interlocking plates of runic granite and diamond-hard crystal armor erupt upward.\n"
            "- Frame 4 (Bottom-Right): A fortress-like golden-stone colossus armor emblem glowing with emerald vitality.\n"
            "RULES: Keep each frame centered inside its cell with generous margin, zero cell clipping, NO blue guide lines, NO pink/magenta on the item, 100% solid #FF00FF background."
        ),
        "prompt_card": (
            "Wide horizontal 16:11 dark-fantasy card illustration (884x632, 100% opaque RGB painting, NO magenta, NO card frame) featuring "
            "the exact same Gargoyle Basalt-Stone Brew Flagon (Dược Phẩm Hóa Thạch - C092) from the attached reference image.\n"
            "Show the runic stone flagon on an ancient dwarven anvil surrounded by erupting granite armor plates and glowing amber-emerald earth energy."
        ),
    },
    {
        "id": "c093",
        "slug": "c093_dong_ho_tro_tan",
        "name": "C093 — Đồng Hồ Tro Tàn (Item Làm Chậm Đội · TimeSlow)",
        "tier": "S",
        "category": "Instant Item",
        "tag": "TimeSlow",
        "status_id": "status_time_chrono",
        "effect_summary": "Ngưng đọng thời gian 4s: Toàn bộ địch bị giảm 45% ASPD & MSPD, còn toàn đội mình được cộng +25 Mana.",
        "prompt_use_2x2": (
            "Create a 2x2 sprite sheet (4 frames: row 1 left-to-right, row 2 left-to-right) on a flat solid pure magenta (#FF00FF) background, "
            "strictly following the attached layout_guide_2x2.png.\n"
            "SUBJECT: Epic Dark-Fantasy Item C093 'Đồng Hồ Tro Tàn' (Ashen Chronos Pocket-Hourglass) activation animation:\n"
            "- Frame 1 (Top-Left): An ornate blackened-gold and bone hourglass pocket-watch filled with glowing cyan-and-amber temporal ash.\n"
            "- Frame 2 (Top-Right): Golden clockwork gears and Roman numerals expand outward as the hourglass flips.\n"
            "- Frame 3 (Bottom-Left): A massive shockwave of frozen cyan-blue time ripples and suspended golden ash halts motion.\n"
            "- Frame 4 (Bottom-Right): A grand glowing cyan-gold clockwork stasis dial suspended in mid-air.\n"
            "RULES: Keep each frame centered inside its cell with generous margin, zero cell clipping, NO blue guide lines, NO pink/magenta on the item, 100% solid #FF00FF background."
        ),
        "prompt_card": (
            "Wide horizontal 16:11 dark-fantasy card illustration (884x632, 100% opaque RGB painting, NO magenta, NO card frame) featuring "
            "the exact same Blackened-Gold Ashen Chronos Hourglass (Đồng Hồ Tro Tàn - C093) from the attached reference image.\n"
            "Show the ornate clockwork hourglass floating over a battlefield where arrows, sparks, and ash are frozen mid-air inside a cyan-gold temporal stasis wave."
        ),
    },
    {
        "id": "c094",
        "slug": "c094_an_ky_thach_thuan",
        "name": "C094 — Ấn Ký Thạch Thuẫn (Item Tạo Khiên · TwinBastion)",
        "tier": "S",
        "category": "Instant Item",
        "tag": "TwinBastion",
        "status_id": "status_shield_bastion",
        "effect_summary": "2 Đồng minh đứng gần địch nhất (5s): Cấp ngay 220 Khiên, +35 Giáp/Kháng phép và miễn nhiễm khống chế.",
        "prompt_use_2x2": (
            "Create a 2x2 sprite sheet (4 frames: row 1 left-to-right, row 2 left-to-right) on a flat solid pure magenta (#FF00FF) background, "
            "strictly following the attached layout_guide_2x2.png.\n"
            "SUBJECT: Epic Dark-Fantasy Item C094 'Ấn Ký Thạch Thuẫn' (Twin-Bastion Sovereign Seal) activation animation:\n"
            "- Frame 1 (Top-Left): A royal gold-and-granite twin-lion shield crest medallion glowing with golden-cyan citadel runes.\n"
            "- Frame 2 (Top-Right): The medallion splits into two synchronized blazing golden-cyan bastion sigils.\n"
            "- Frame 3 (Bottom-Left): Twin colossal hexagonal golden-stone fortress barriers erupt side-by-side with unstoppable immunity halos.\n"
            "- Frame 4 (Bottom-Right): Interlocking twin golden-cyan citadel shields radiating unbreakable light.\n"
            "RULES: Keep each frame centered inside its cell with generous margin, zero cell clipping, NO blue guide lines, NO pink/magenta on the item, 100% solid #FF00FF background."
        ),
        "prompt_card": (
            "Wide horizontal 16:11 dark-fantasy card illustration (884x632, 100% opaque RGB painting, NO magenta, NO card frame) featuring "
            "the exact same Gold-and-Granite Twin-Bastion Shield Seal (Ấn Ký Thạch Thuẫn - C094) from the attached reference image.\n"
            "Show the majestic twin-lion stone-and-gold seal projecting two towering golden-cyan hexagonal fortress barriers on a dark siege battlefield."
        ),
    },
    {
        "id": "c095",
        "slug": "c095_guong_sao_chep_co_ngu",
        "name": "C095 — Gương Sao Chép Cổ Ngữ (Item Sao Chép · MirrorItem)",
        "tier": "S",
        "category": "Instant Item",
        "tag": "MirrorItem",
        "status_id": "status_mirror_reflect",
        "effect_summary": "Sao chép và kích hoạt lại hiệu ứng của thẻ Item gần nhất mà đối thủ vừa lật trong trận (100% hiệu lực)!",
        "prompt_use_2x2": (
            "Create a 2x2 sprite sheet (4 frames: row 1 left-to-right, row 2 left-to-right) on a flat solid pure magenta (#FF00FF) background, "
            "strictly following the attached layout_guide_2x2.png.\n"
            "SUBJECT: Epic Dark-Fantasy Item C095 'Gương Sao Chép Cổ Ngữ' (Runic Doppelganger Looking-Glass) activation animation:\n"
            "- Frame 1 (Top-Left): An ornate antique silver-and-gold octagonal hand mirror with a shimmering quicksilver-cyan reflective glass encircled by arcane runes.\n"
            "- Frame 2 (Top-Right): The mirror surface ripples like liquid silver as golden-cyan copy sigils spin around the frame.\n"
            "- Frame 3 (Bottom-Left): A twin phantom projection of the mirror emerges out of the glass in a burst of prismatic cyan-gold light.\n"
            "- Frame 4 (Bottom-Right): Synchronized dual runic portals radiating mirrored spell energy.\n"
            "RULES: Keep each frame centered inside its cell with generous margin, zero cell clipping, NO blue guide lines, NO pink/magenta on the item, 100% solid #FF00FF background."
        ),
        "prompt_card": (
            "Wide horizontal 16:11 dark-fantasy card illustration (884x632, 100% opaque RGB painting, NO magenta, NO card frame) featuring "
            "the exact same Silver-and-Gold Runic Doppelganger Mirror (Gương Sao Chép Cổ Ngữ - C095) from the attached reference image.\n"
            "Show the ornate octagonal arcane mirror floating in a mystical sanctum, duplicating a glowing golden-cyan spell artifact out of its liquid-silver glass."
        ),
    },
    {
        "id": "c096",
        "slug": "c096_co_vat_hoan_doi_linh_luc",
        "name": "C096 — Cổ Vật Hoán Đổi Linh Lực (Item Đổi Mana · ManaSwap)",
        "tier": "S",
        "category": "Instant Item",
        "tag": "ManaSwap",
        "status_id": "status_silence_manalock",
        "effect_summary": "Hoán đổi toàn bộ thanh %Mana hiện tại giữa đồng minh ít Mana nhất của bạn và kẻ địch gần đầy Mana nhất!",
        "prompt_use_2x2": (
            "Create a 2x2 sprite sheet (4 frames: row 1 left-to-right, row 2 left-to-right) on a flat solid pure magenta (#FF00FF) background, "
            "strictly following the attached layout_guide_2x2.png.\n"
            "SUBJECT: Epic Dark-Fantasy Item C096 'Cổ Vật Hoán Đổi Linh Lực' (Twin-Vessel Aether-Swap Relic) activation animation:\n"
            "- Frame 1 (Top-Left): An S-curved golden infinity conduit linking two crystal globes: one empty dark glass and one overflowing with radiant sapphire-cyan mana.\n"
            "- Frame 2 (Top-Right): The golden infinity conduit spins as streams of sapphire mana and dark void energy rush through the tubes.\n"
            "- Frame 3 (Bottom-Left): A dramatic figure-eight vortex of cyan-and-gold lightning swaps the energy between the two poles.\n"
            "- Frame 4 (Bottom-Right): The reversed twin globes blazing with completed mana-transference runes.\n"
            "RULES: Keep each frame centered inside its cell with generous margin, zero cell clipping, NO blue guide lines, NO pink/magenta on the item, 100% solid #FF00FF background."
        ),
        "prompt_card": (
            "Wide horizontal 16:11 dark-fantasy card illustration (884x632, 100% opaque RGB painting, NO magenta, NO card frame) featuring "
            "the exact same Golden Infinity Twin-Globe Mana-Swap Relic (Cổ Vật Hoán Đổi Linh Lực - C096) from the attached reference image.\n"
            "Show the twin-vessel infinity relic in a dark astral chamber as a figure-eight vortex of brilliant sapphire-cyan mana and golden runes swaps energy between two vessels."
        ),
    },
    {
        "id": "c097",
        "slug": "c097_thanh_gia_thanh_tay_doi",
        "name": "C097 — Thánh Giá Thanh Tẩy Đội (Item Giải Trừ Đội · MassCleanse)",
        "tier": "S",
        "category": "Instant Item",
        "tag": "MassCleanse",
        "status_id": "status_heal_cleanse",
        "effect_summary": "Toàn đội đồng minh: Xóa sạch mọi hiệu ứng bất lợi (Debuff/Khống chế); mỗi hiệu ứng xóa chuyển thành +20 Mana & 60 HP.",
        "prompt_use_2x2": (
            "Create a 2x2 sprite sheet (4 frames: row 1 left-to-right, row 2 left-to-right) on a flat solid pure magenta (#FF00FF) background, "
            "strictly following the attached layout_guide_2x2.png.\n"
            "SUBJECT: Epic Dark-Fantasy Item C097 'Thánh Giá Thanh Tẩy Đội' (Grand Seraphic Purification Cross Relic) activation animation:\n"
            "- Frame 1 (Top-Left): A majestic platinum-and-gold winged cathedral cross set with a radiant emerald-cyan purification crystal.\n"
            "- Frame 2 (Top-Right): Dark chains and curse smoke around the cross shatter as golden-white and emerald-cyan light blazes forth.\n"
            "- Frame 3 (Bottom-Left): A sweeping sacred nova of golden-white light and emerald healing feathers expands in a circle.\n"
            "- Frame 4 (Bottom-Right): A luminous sanctuary halo of pure golden-emerald blessing runes.\n"
            "RULES: Keep each frame centered inside its cell with generous margin, zero cell clipping, NO blue guide lines, NO pink/magenta on the item, 100% solid #FF00FF background."
        ),
        "prompt_card": (
            "Wide horizontal 16:11 dark-fantasy card illustration (884x632, 100% opaque RGB painting, NO magenta, NO card frame) featuring "
            "the exact same Platinum-and-Gold Winged Purification Cross (Thánh Giá Thanh Tẩy Đội - C097) from the attached reference image.\n"
            "Show the radiant winged cross relic unleashing a sanctuary nova of golden-white and emerald-cyan light that shatters dark curse chains across a gothic battlefield."
        ),
    },
    {
        "id": "c098",
        "slug": "c098_di_vat_pha_thuan",
        "name": "C098 — Di Vật Phá Thuẫn (Item Khắc Khiên · ShieldBreak)",
        "tier": "SSR",
        "category": "Instant Item",
        "tag": "ShieldBreak",
        "status_id": "status_shield_break",
        "effect_summary": "Phá hủy 100% Khiên của địch nhiều Khiên nhất (choáng 1.5s) và ban ấn Phá Thuẫn (+150% sát thương lên Khiên 8s).",
        "prompt_use_2x2": (
            "Create a 2x2 sprite sheet (4 frames: row 1 left-to-right, row 2 left-to-right) on a flat solid pure magenta (#FF00FF) background, "
            "strictly following the attached layout_guide_2x2.png.\n"
            "SUBJECT: Mythic SSR Dark-Fantasy Item C098 'Di Vật Phá Thuẫn' (Aegis-Shatter Meteor Spearhead Relic) activation animation:\n"
            "- Frame 1 (Top-Left): A mythic jagged obsidian-and-gold drill-spearhead relic crackling with blazing crimson-gold armor-piercing runes.\n"
            "- Frame 2 (Top-Right): The relic spins like a meteor drill, surrounded by a sonic cone of golden-red lightning.\n"
            "- Frame 3 (Bottom-Left): The spearhead violently pierces and shatters a glowing cyan barrier shield into a hundred flying glass-like shards.\n"
            "- Frame 4 (Bottom-Right): Blazing crimson-gold Shield-Breaker crest surrounded by shattered barrier fragments.\n"
            "RULES: Keep each frame centered inside its cell with generous margin, zero cell clipping, NO blue guide lines, NO pink/magenta on the item, 100% solid #FF00FF background."
        ),
        "prompt_card": (
            "Wide horizontal 16:11 dark-fantasy card illustration (884x632, 100% opaque RGB painting, NO magenta, NO card frame) featuring "
            "the exact same Mythic Obsidian-and-Gold Aegis-Shatter Spearhead Relic (Di Vật Phá Thuẫn - C098) from the attached reference image.\n"
            "Show the blazing crimson-gold meteor relic smashing straight through a colossal glowing cyan magic shield, sending crystalline barrier shards flying across a dark battlefield."
        ),
    },
    {
        "id": "c099",
        "slug": "c099_tim_guong_phan_phe",
        "name": "C099 — Tim Gương Phản Phệ (Item Phản Dame · MirrorHeart)",
        "tier": "SSR",
        "category": "Instant Item",
        "tag": "MirrorHeart",
        "status_id": "status_mirror_reflect",
        "effect_summary": "Khoác Gương Hồn 6s (+150 Khiên): Phản lại 40% mọi sát thương nhận vào; hết 6s phát nổ gây 50% tổng lượng đã phản + 30 Mana toàn đội!",
        "prompt_use_2x2": (
            "Create a 2x2 sprite sheet (4 frames: row 1 left-to-right, row 2 left-to-right) on a flat solid pure magenta (#FF00FF) background, "
            "strictly following the attached layout_guide_2x2.png.\n"
            "SUBJECT: Mythic SSR Dark-Fantasy Item C099 'Tim Gương Phản Phệ' (Spiked Mirror-Heart of Retribution) activation animation:\n"
            "- Frame 1 (Top-Left): A mythic anatomical heart forged from faceted diamond-mirror glass and spiked royal gold cages, pulsing with fiery crimson-gold light.\n"
            "- Frame 2 (Top-Right): A spherical cage of razor-spiked mirror facets expands around the heart, deflecting incoming energy bolts.\n"
            "- Frame 3 (Bottom-Left): The Mirror-Heart overloads and detonates in a cataclysmic nova of razor mirror shards and golden-crimson retribution fire.\n"
            "- Frame 4 (Bottom-Right): Radiant golden-crimson Retribution Mirror crown and mana wave.\n"
            "RULES: Keep each frame centered inside its cell with generous margin, zero cell clipping, NO blue guide lines, NO pink/magenta on the item, 100% solid #FF00FF background."
        ),
        "prompt_card": (
            "Wide horizontal 16:11 dark-fantasy card illustration (884x632, 100% opaque RGB painting, NO magenta, NO card frame) featuring "
            "the exact same Mythic Spiked Diamond-Glass Mirror-Heart (Tim Gương Phản Phệ - C099) from the attached reference image.\n"
            "Show the golden-caged mirror heart levitating in a grand gothic hall, deflecting dark spells off its faceted glass surface in a blinding burst of crimson-gold retribution."
        ),
    },
    {
        "id": "c100",
        "slug": "c100_an_doi_he_ngu_hanh",
        "name": "C100 — Ấn Đổi Hệ Ngũ Hành (Item Đổi Hệ · ElementShift)",
        "tier": "SSR",
        "category": "Instant Item",
        "tag": "ElementShift",
        "status_id": "status_shield_break",
        "effect_summary": "Đổi Hệ Ngũ Hành của đồng minh mạnh nhất sang Hệ Tương Khắc trực tiếp với kẻ địch mạnh nhất, +25% Dame & +35 Mana đến hết trận!",
        "prompt_use_2x2": (
            "Create a 2x2 sprite sheet (4 frames: row 1 left-to-right, row 2 left-to-right) on a flat solid pure magenta (#FF00FF) background, "
            "strictly following the attached layout_guide_2x2.png.\n"
            "SUBJECT: Mythic SSR Dark-Fantasy Item C100 'Ấn Đổi Hệ Ngũ Hành' (Supreme Five-Elements Pentagram Wheel Seal) activation animation:\n"
            "- Frame 1 (Top-Left): A mythic celestial gold-and-jade five-pointed Wu-Xing astrolabe wheel set with 5 elemental gems: White-Gold Metal, Emerald Wood, Ice-Blue Water, Crimson Fire, and Amber Earth.\n"
            "- Frame 2 (Top-Right): The five elemental gems ignite and the golden pentagram wheel spins rapidly with elemental dragons.\n"
            "- Frame 3 (Bottom-Left): A grand five-colored elemental transmutation vortex erupts, locking onto the dominant counter-element in a blinding golden-crimson-cyan beam.\n"
            "- Frame 4 (Bottom-Right): The awakened Supreme Five-Elements Sovereign Crest blazing with eternal power.\n"
            "RULES: Keep each frame centered inside its cell with generous margin, zero cell clipping, NO blue guide lines, NO pink/magenta on the item, 100% solid #FF00FF background."
        ),
        "prompt_card": (
            "Wide horizontal 16:11 dark-fantasy card illustration (884x632, 100% opaque RGB painting, NO magenta, NO card frame) featuring "
            "the exact same Mythic Five-Elements Pentagram Wheel Seal (Ấn Đổi Hệ Ngũ Hành - C100) from the attached reference image.\n"
            "Show the grand golden Wu-Xing astrolabe seal suspended above an ancient five-altar sanctum as streams of Metal, Wood, Water, Fire, and Earth energy converge into its core."
        ),
    },
]


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


def b64_png_uri(path: pathlib.Path) -> str:
    if not path.exists():
        return ""
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{data}"


# ==============================================================================
# 3. STEP A: GENERATE & EXTRACT THE 10 SHARED 16x16 STATUS EFFECT ICONS
# ==============================================================================
def forge_shared_status_icons(force_gen: bool = False):
    STATUS_DIR.mkdir(parents=True, exist_ok=True)
    MOBILE_STATUS_DIR.mkdir(parents=True, exist_ok=True)
    raw_dir = STATUS_DIR / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Check if all 10 icons already exist
    all_exist = all((STATUS_DIR / f"{sid}_16x16.png").exists() for sid in SHARED_STATUS_GROUPS)
    if all_exist and not force_gen:
        print("[status_icons] All 10 shared 16x16 status icons already exist.")
        build_status_icons_catalog_sheet()
        return

    for sheet_idx, prompt in STATUS_SHEET_PROMPTS.items():
        raw_sheet = raw_dir / f"status_sheet_{sheet_idx}_2x2_raw.png"
        if force_gen or not raw_sheet.exists():
            for attempt in range(3):
                print(f"[status_icons] Generating Shared Status Icon 2x2 Sheet {sheet_idx}/3 via Muse (attempt {attempt + 1}/3)...")
                try:
                    muse_post("/v1/thread", {"new_thread": True})
                    muse_post("/generate-image", {
                        "prompt": prompt,
                        "reference_images": [str(LAYOUT_2X2)],
                        "save_path": str(raw_sheet),
                    })
                except Exception as exc:
                    print(f"[status_icons] Muse warning on sheet {sheet_idx}: {exc}")
                if raw_sheet.exists():
                    break

        sheet_im = Image.open(raw_sheet).convert("RGBA")
        sw, sh = sheet_im.size
        cw, ch = sw // 2, sh // 2

        for sid, sinfo in SHARED_STATUS_GROUPS.items():
            if sinfo["sheet_group"] != sheet_idx:
                continue
            cidx = sinfo["cell_index"]
            r_i, c_i = cidx // 2, cidx % 2
            cell = sheet_im.crop((c_i * cw, r_i * ch, (c_i + 1) * cw, (r_i + 1) * ch))
            unmixed = unmix_magenta_rgba(cell)
            cropped = keep_largest_component_and_crop(unmixed, pad=0)

            # Fit into a square canvas (64x64 HD & 16x16 exact status icon)
            for target_px in (64, 16):
                canvas = Image.new("RGBA", (target_px, target_px), (0, 0, 0, 0))
                scale = min(target_px / max(1, cropped.width), target_px / max(1, cropped.height))
                nw = max(1, int(round(cropped.width * scale)))
                nh = max(1, int(round(cropped.height * scale)))
                resized = cropped.resize((nw, nh), Image.Resampling.LANCZOS)
                canvas.paste(resized, ((target_px - nw) // 2, (target_px - nh) // 2), resized)
                out_png = STATUS_DIR / f"{sid}_{target_px}x{target_px}.png"
                canvas.save(out_png)
                canvas.save(MOBILE_STATUS_DIR / f"{sid}_{target_px}x{target_px}.webp", format="WEBP", quality=95)

    build_status_icons_catalog_sheet()
    print("[status_icons] All 10 shared 16x16 & 64x64 status icons generated and exported!")


def build_status_icons_catalog_sheet():
    f_title = load_font(20)
    f_sub = load_font(13)
    w, h = 1480, 720
    board = Image.new("RGB", (w, h), (13, 17, 23))
    draw = ImageDraw.Draw(board)
    draw.text((28, 20), "BẢNG TỔNG HỢP 10 ICON TRẠNG THÁI DÙNG CHUNG (16x16 PIXEL & 64x64 HD) — NHÓM C076..C100", fill=(245, 158, 11), font=f_title)
    draw.text((28, 48), "Các Item/Kỹ năng có cùng bản chất hiệu ứng trạng thái (Buff / Debuff / Khống chế) dùng chung bộ Icon 16x16 đồng nhất", fill=(139, 148, 158), font=f_sub)

    items_list = list(SHARED_STATUS_GROUPS.values())
    for idx, sinfo in enumerate(items_list):
        col = idx % 2
        row = idx // 2
        bx = 28 + col * 720
        by = 84 + row * 122
        draw.rectangle([bx, by, bx + 696, by + 110], fill=(22, 27, 34), outline=(48, 54, 61), width=2)

        sid = sinfo["id"]
        ic16_path = STATUS_DIR / f"{sid}_16x16.png"
        ic64_path = STATUS_DIR / f"{sid}_64x64.png"
        if ic64_path.exists():
            ic64 = Image.open(ic64_path).convert("RGBA")
            board.paste(ic64, (bx + 18, by + 23), ic64)
            draw.rectangle([bx + 16, by + 21, bx + 84, by + 89], outline=(88, 166, 255), width=1)
        if ic16_path.exists():
            ic16 = Image.open(ic16_path).convert("RGBA")
            # True 16x16 size
            board.paste(ic16, (bx + 102, by + 26), ic16)
            draw.rectangle([bx + 100, by + 24, bx + 120, by + 44], outline=(245, 158, 11), width=1)
            # 3x Nearest-Neighbor zoom of 16x16 to show pixel clarity
            ic16_zoom = ic16.resize((48, 48), Image.Resampling.NEAREST)
            board.paste(ic16_zoom, (bx + 132, by + 26), ic16_zoom)
            draw.rectangle([bx + 130, by + 24, bx + 182, by + 76], outline=(63, 185, 80), width=1)
            draw.text((bx + 98, by + 80), "16x16 thật & Zoom 3x", fill=(139, 148, 158), font=f_sub)

        draw.text((bx + 200, by + 16), f"{idx + 1}. {sinfo['name']}", fill=(230, 237, 243), font=f_sub)
        draw.text((bx + 200, by + 42), f"Mã Icon: {sid}_16x16.png | Dùng chung bởi: {', '.join(sinfo['shared_by'])}", fill=(88, 166, 255), font=f_sub)
        draw.text((bx + 200, by + 68), f"Trạng thái: {sinfo['desc']}", fill=(139, 148, 158), font=f_sub)

    board.save(STATUS_DIR / "status_icons_catalog_sheet.png")


# ==============================================================================
# 4. STEP B: FORGE ALL 25 CARDS (C076 - C100) + QC BOARDS
# ==============================================================================
def build_item_qc_board(card_cfg: dict, item_dir: pathlib.Path):
    cid = card_cfg["id"].upper()
    slug = card_cfg["slug"]
    pdir = item_dir / "parts"
    cdir = item_dir / "card"
    qdir = item_dir / "qc_previews"
    qdir.mkdir(parents=True, exist_ok=True)

    f_title = load_font(18)
    f_sub = load_font(13)
    w, h = 1520, 620
    board = Image.new("RGB", (w, h), (13, 17, 23))
    draw = ImageDraw.Draw(board)

    status_id = card_cfg["status_id"]
    sinfo = SHARED_STATUS_GROUPS[status_id]

    draw.text((24, 16), f"{card_cfg['name']}  |  Tier: {card_cfg['tier']}  |  Tag: {card_cfg['tag']}", fill=(245, 158, 11), font=f_title)
    draw.text((24, 42), f"Hiệu ứng: {card_cfg['effect_summary']}", fill=(201, 209, 217), font=f_sub)

    # Panel 1: Card Illustration (884x632 scaled to 530x379)
    draw.rectangle([24, 72, 574, 596], fill=(22, 27, 34), outline=(245, 158, 11), width=2)
    draw.text((38, 84), f"1. ẢNH TRONG THẺ BÀI ({cid}_card_preview.png — 884x632 RGB Opaque)", fill=(245, 158, 11), font=f_sub)
    card_path = cdir / f"{card_cfg['id']}_card_preview.png"
    if card_path.exists():
        cim = Image.open(card_path).convert("RGB").resize((520, 372), Image.Resampling.LANCZOS)
        board.paste(cim, (39, 114))
        draw.rectangle([39, 114, 559, 486], outline=(88, 166, 255), width=1)
    draw.text((39, 502), "Định dạng: 884x632 RGB PNG & 354x253 Mobile WebP (100% Opaque)", fill=(63, 185, 80), font=f_sub)
    draw.text((39, 526), f"Phân loại: {card_cfg['category']} ({card_cfg['tag']})", fill=(139, 148, 158), font=f_sub)

    # Panel 2: 2x2 Use Spritesheet (4 frames)
    draw.rectangle([594, 72, 1134, 596], fill=(22, 27, 34), outline=(88, 166, 255), width=2)
    draw.text((608, 84), "2. SPRITE SHEET SỬ DỤNG 2x2 (use_frame_0..3.png & use_spritesheet_2x2.png)", fill=(88, 166, 255), font=f_sub)
    for idx in range(4):
        r_i, c_i = idx // 2, idx % 2
        fx = 618 + c_i * 250
        fy = 116 + r_i * 228
        draw.rectangle([fx, fy, fx + 232, fy + 212], fill=(16, 20, 26), outline=(48, 54, 61), width=1)
        fp = pdir / f"use_frame_{idx}.png"
        if fp.exists():
            fim = Image.open(fp).convert("RGBA")
            sc = min(180 / max(1, fim.width), 170 / max(1, fim.height))
            nw, nh = max(1, int(fim.width * sc)), max(1, int(fim.height * sc))
            f_res = fim.resize((nw, nh), Image.Resampling.LANCZOS)
            board.paste(f_res, (fx + (232 - nw) // 2, fy + 28 + (176 - nh) // 2), f_res)
        draw.text((fx + 10, fy + 8), f"Frame {idx + 1} (use_frame_{idx}.png)", fill=(139, 148, 158), font=f_sub)

    # Panel 3: Shared 16x16 Status Icon
    draw.rectangle([1154, 72, 1496, 596], fill=(22, 27, 34), outline=(63, 185, 80), width=2)
    draw.text((1168, 84), "3. ICON TRẠNG THÁI 16x16 (DÙNG CHUNG)", fill=(63, 185, 80), font=f_sub)

    ic16_p = pdir / "status_icon_16x16.png"
    ic64_p = pdir / "status_icon_64x64.png"
    if ic16_p.exists():
        ic16 = Image.open(ic16_p).convert("RGBA")
        # Actual 16x16
        draw.rectangle([1180, 128, 1236, 184], fill=(13, 17, 23), outline=(245, 158, 11), width=1)
        board.paste(ic16, (1200, 148), ic16)
        draw.text((1248, 140), "Kích thước gốc: 16x16 px", fill=(245, 158, 11), font=f_sub)
        draw.text((1248, 162), f"({status_id}_16x16.png)", fill=(139, 148, 158), font=f_sub)

        # Nearest-neighbor 6x zoom (96x96)
        ic_zoom = ic16.resize((96, 96), Image.Resampling.NEAREST)
        draw.rectangle([1180, 206, 1296, 322], fill=(13, 17, 23), outline=(63, 185, 80), width=1)
        board.paste(ic_zoom, (1190, 216), ic_zoom)
        draw.text((1308, 240), "Phóng to 6x", fill=(63, 185, 80), font=f_sub)
        draw.text((1308, 262), "(Pixel 16x16)", fill=(139, 148, 158), font=f_sub)

    if ic64_p.exists():
        ic64 = Image.open(ic64_p).convert("RGBA")
        draw.rectangle([1180, 340, 1264, 424], fill=(13, 17, 23), outline=(88, 166, 255), width=1)
        board.paste(ic64, (1190, 350), ic64)
        draw.text((1276, 368), "Bản HD 64x64 px", fill=(88, 166, 255), font=f_sub)
        draw.text((1276, 390), "(status_icon_64x64.png)", fill=(139, 148, 158), font=f_sub)

    draw.text((1168, 450), f"Nhóm Icon: {sinfo['name']}", fill=(230, 237, 243), font=f_sub)
    draw.text((1168, 476), f"Gộp dùng chung bởi: {', '.join(sinfo['shared_by'])}", fill=(88, 166, 255), font=f_sub)
    draw.text((1168, 502), f"Ý nghĩa: {sinfo['desc']}", fill=(139, 148, 158), font=f_sub)

    out_qc = qdir / f"{card_cfg['id']}_item_audit.png"
    board.save(out_qc)
    return out_qc


def forge_single_card_76_100(card_cfg: dict, force_gen: bool = False):
    cid = card_cfg["id"]
    slug = card_cfg["slug"]
    status_id = card_cfg["status_id"]

    idir = ITEMS_DIR / slug
    rdir = idir / "raw"
    pdir = idir / "parts"
    cdir = idir / "card"
    mdir_parts = MOBILE_ITEMS_DIR / slug / "parts"
    mdir_card = MOBILE_ITEMS_DIR / slug / "card"
    for d in (rdir, pdir, cdir, mdir_parts, mdir_card):
        d.mkdir(parents=True, exist_ok=True)

    # Copy shared 16x16 and 64x64 status icons into this card's parts folder
    shutil.copyfile(STATUS_DIR / f"{status_id}_16x16.png", pdir / "status_icon_16x16.png")
    shutil.copyfile(STATUS_DIR / f"{status_id}_64x64.png", pdir / "status_icon_64x64.png")

    # Case 1: Support Hero Cards C076-C080 (also forged as Hero Weapons W076-W080)
    if "weapon_id" in card_cfg:
        wid = card_cfg["weapon_id"]
        w_cfg_path = ROOT / "assets/weapons/configs" / f"{wid}.json"
        w_dir = ROOT / "assets/weapons" / card_cfg["weapon_slug"]
        if force_gen or not (w_dir / "card" / f"{wid}_card_preview.png").exists():
            forge_single_weapon(w_cfg_path, force_gen=force_gen)

        # Copy card preview & 4-frame 2x2 weapon/skill animation into assets/items/<slug>
        shutil.copyfile(w_dir / "card" / f"{wid}_card_preview.png", cdir / f"{cid}_card_preview.png")
        shutil.copyfile(w_dir / "parts/weapon_main.png", pdir / "item_main.png")
        for idx in range(4):
            src_f = w_dir / "parts" / f"weapon_anim_{idx}.png"
            if not src_f.exists():
                src_f = w_dir / "parts/weapon_main.png"
            shutil.copyfile(src_f, pdir / f"use_frame_{idx}.png")
    else:
        # Case 2: Instant Item Cards C081-C100
        use_raw = rdir / f"{cid}_use_2x2_raw.png"
        if force_gen or not use_raw.exists():
            for attempt in range(3):
                print(f"[{cid}] Generating 2x2 Item Use Spritesheet via Muse (attempt {attempt + 1}/3)...")
                try:
                    muse_post("/v1/thread", {"new_thread": True})
                    muse_post("/generate-image", {
                        "prompt": card_cfg["prompt_use_2x2"],
                        "reference_images": [str(LAYOUT_2X2)],
                        "save_path": str(use_raw),
                    })
                except Exception as exc:
                    print(f"[{cid}] Muse 2x2 warning: {exc}")
                if use_raw.exists():
                    break

        if force_gen or not (pdir / "use_frame_3.png").exists():
            sheet_im = Image.open(use_raw).convert("RGBA")
            sw, sh = sheet_im.size
            cw, ch = sw // 2, sh // 2
            for idx in range(4):
                r_i, c_i = idx // 2, idx % 2
                cell = sheet_im.crop((c_i * cw, r_i * ch, (c_i + 1) * cw, (r_i + 1) * ch))
                unmixed = unmix_magenta_rgba(cell)
                cropped = keep_largest_component_and_crop(unmixed, pad=0)
                # Fit into 220x220 inside 256x256 cell
                frame_canvas = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
                sc = min(220 / max(1, cropped.width), 220 / max(1, cropped.height))
                nw = max(1, int(round(cropped.width * sc)))
                nh = max(1, int(round(cropped.height * sc)))
                resized = cropped.resize((nw, nh), Image.Resampling.LANCZOS)
                frame_canvas.paste(resized, ((256 - nw) // 2, (256 - nh) // 2), resized)
                frame_canvas.save(pdir / f"use_frame_{idx}.png")
                if idx == 0:
                    resized.save(pdir / "item_main.png")

        # Generate Card Illustration (884x632 RGB) from the 2x2 sheet reference
        card_png = cdir / f"{cid}_card_preview.png"
        if force_gen or not card_png.exists():
            card_raw = rdir / f"{cid}_card_preview_raw.png"
            if force_gen or not card_raw.exists():
                for attempt in range(3):
                    print(f"[{cid}] Generating Card Illustration via Muse (attempt {attempt + 1}/3)...")
                    try:
                        muse_post("/generate-image", {
                            "prompt": card_cfg["prompt_card"],
                            "reference_images": [str(use_raw)],
                            "save_path": str(card_raw),
                        })
                    except Exception as exc:
                        print(f"[{cid}] Muse card warning: {exc}")
                    if card_raw.exists():
                        break
            if card_raw.exists():
                cim = Image.open(card_raw).convert("RGB").resize((884, 632), Image.Resampling.LANCZOS)
                cim.save(card_png, format="PNG")

    # Assemble clean 2x2 Use Spritesheet (512x512) & 4x1 Strip (1024x256)
    sheet_2x2 = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    strip_4x1 = Image.new("RGBA", (1024, 256), (0, 0, 0, 0))
    for idx in range(4):
        fim = Image.open(pdir / f"use_frame_{idx}.png").convert("RGBA")
        if fim.size != (256, 256):
            canvas = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
            sc = min(224 / max(1, fim.width), 224 / max(1, fim.height))
            nw, nh = max(1, int(fim.width * sc)), max(1, int(fim.height * sc))
            fr = fim.resize((nw, nh), Image.Resampling.LANCZOS)
            canvas.paste(fr, ((256 - nw) // 2, (256 - nh) // 2), fr)
            fim = canvas
        r_i, c_i = idx // 2, idx % 2
        sheet_2x2.paste(fim, (c_i * 256, r_i * 256), fim)
        strip_4x1.paste(fim, (idx * 256, 0), fim)

    sheet_2x2.save(pdir / "use_spritesheet_2x2.png")
    strip_4x1.save(pdir / "use_strip_4x1.png")

    # Export WebP for mobile
    card_png = cdir / f"{cid}_card_preview.png"
    if card_png.exists():
        Image.open(card_png).convert("RGB").resize((354, 253), Image.Resampling.LANCZOS).save(
            mdir_card / f"{cid}_card_preview.webp", format="WEBP", quality=90
        )
    for png_p in pdir.glob("*.png"):
        Image.open(png_p).convert("RGBA").save(mdir_parts / f"{png_p.stem}.webp", format="WEBP", quality=90)

    build_item_qc_board(card_cfg, idir)
    print(f"[{cid}] ITEM & EFFECT FORGE COMPLETE -> Card + 2x2 Use Sheet + 16x16 Shared Status Icon ({status_id})!")


def build_master_overview_and_html_viewer():
    f_title = load_font(22)
    f_sub = load_font(12)
    cols = 5
    rows = 5
    cell_w, cell_h = 340, 260
    w = 32 + cols * cell_w
    h = 90 + rows * cell_h
    board = Image.new("RGB", (w, h), (13, 17, 23))
    draw = ImageDraw.Draw(board)
    draw.text((24, 18), "TỔNG HỢP 25 THẺ CUỐI (C076 – C100): ẢNH THẺ BÀI + SPRITESHEET SỬ DỤNG 2x2 + ICON TRẠNG THÁI 16x16 DÙNG CHUNG", fill=(245, 158, 11), font=f_title)
    draw.text((24, 48), "Bao gồm 5 Thẻ Hỗ Trợ Cuối (C076–C080) & 20 Thẻ Vật Phẩm Tức Thời (C081–C100) kèm 10 Nhóm Icon Trạng Thái 16x16", fill=(139, 148, 158), font=f_sub)

    items_js_registry = {}
    for idx, cfg in enumerate(FINAL_25_CARDS):
        r_i, c_i = idx // cols, idx % cols
        bx = 16 + c_i * cell_w
        by = 76 + r_i * cell_h
        draw.rectangle([bx, by, bx + cell_w - 12, by + cell_h - 12], fill=(22, 27, 34), outline=(48, 54, 61), width=2)

        cid = cfg["id"]
        slug = cfg["slug"]
        idir = ITEMS_DIR / slug
        c_path = idir / "card" / f"{cid}_card_preview.png"
        s_path = idir / "parts/use_spritesheet_2x2.png"
        ic16_path = idir / "parts/status_icon_16x16.png"
        ic64_path = idir / "parts/status_icon_64x64.png"

        if c_path.exists():
            cim = Image.open(c_path).convert("RGB").resize((196, 140), Image.Resampling.LANCZOS)
            board.paste(cim, (bx + 10, by + 34))
            draw.rectangle([bx + 10, by + 34, bx + 206, by + 174], outline=(245, 158, 11), width=1)
        if s_path.exists():
            sim = Image.open(s_path).convert("RGBA").resize((108, 108), Image.Resampling.LANCZOS)
            board.paste(sim, (bx + 214, by + 34), sim)
            draw.rectangle([bx + 214, by + 34, bx + 322, by + 142], outline=(88, 166, 255), width=1)
        if ic16_path.exists():
            ic16 = Image.open(ic16_path).convert("RGBA")
            board.paste(ic16, (bx + 218, by + 154), ic16)
            ic_zoom = ic16.resize((32, 32), Image.Resampling.NEAREST)
            board.paste(ic_zoom, (bx + 244, by + 146), ic_zoom)
            draw.text((bx + 282, by + 154), "16x16", fill=(63, 185, 80), font=f_sub)

        short_title = cfg["name"].split("(")[0].strip()
        draw.text((bx + 10, by + 10), f"{short_title} [{cfg['tier']}]", fill=(230, 237, 243), font=f_sub)
        draw.text((bx + 10, by + 186), f"Tag: {cfg['tag']} | Icon: {cfg['status_id']}", fill=(88, 166, 255), font=f_sub)
        draw.text((bx + 10, by + 206), cfg["effect_summary"][:48] + "...", fill=(139, 148, 158), font=f_sub)

        items_js_registry[cid] = {
            "id": cid,
            "slug": slug,
            "name": cfg["name"],
            "tier": cfg["tier"],
            "tag": cfg["tag"],
            "category": cfg["category"],
            "status_id": cfg["status_id"],
            "status_name": SHARED_STATUS_GROUPS[cfg["status_id"]]["name"],
            "status_shared_by": SHARED_STATUS_GROUPS[cfg["status_id"]]["shared_by"],
            "effect_summary": cfg["effect_summary"],
            "card_b64": b64_png_uri(c_path),
            "frames_b64": [b64_png_uri(idir / "parts" / f"use_frame_{i}.png") for i in range(4)],
            "icon16_b64": b64_png_uri(ic16_path),
            "icon64_b64": b64_png_uri(ic64_path),
        }

    out_master = ITEMS_DIR / "qc_all_25_items_overview.png"
    board.save(out_master)

    # Save external JS data & lightweight HTML viewer for the 25 items
    items_data_js = ROOT / "assets/items_data.js"
    items_data_js.write_text(
        "// Auto-generated by tools/forge_items_76_100.py — DO NOT READ IN AI CONTEXT\n"
        f"window.SHARED_STATUS_GROUPS = {json.dumps(SHARED_STATUS_GROUPS, ensure_ascii=True)};\n"
        f"window.ITEMS_76_100 = {json.dumps(items_js_registry, ensure_ascii=True)};\n",
        encoding="utf-8",
    )

    viewer_html = ROOT / "assets/items_viewer.html"
    viewer_html.write_text('''<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8" />
<title>Card_G — Bộ 25 Item & Kỹ Năng Cuối (C076–C100) + Icon Trạng Thái 16x16 Dùng Chung</title>
<style>
  body { margin: 0; background: #0d1117; color: #e6edf3; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
  header { padding: 14px 24px; background: #161b22; border-bottom: 1px solid #30363d; display: flex; justify-content: space-between; align-items: center; }
  h1 { margin: 0; font-size: 18px; color: #f59e0b; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: 16px; padding: 20px; }
  .card { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 14px; display: flex; flex-direction: column; gap: 10px; }
  .card-head { display: flex; justify-content: space-between; align-items: center; font-weight: 700; font-size: 14px; color: #58a6ff; }
  .tier { background: #238636; color: #fff; padding: 2px 8px; border-radius: 99px; font-size: 11px; }
  .media-row { display: flex; gap: 12px; align-items: center; }
  .card-art { width: 190px; height: 136px; object-fit: cover; border-radius: 6px; border: 1px solid #f59e0b; }
  .anim-box { width: 136px; height: 136px; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; display: flex; align-items: center; justify-content: center; }
  .anim-box img { max-width: 124px; max-height: 124px; }
  .status-bar { display: flex; align-items: center; gap: 10px; background: #0d1117; padding: 8px 10px; border-radius: 6px; border: 1px solid #2ea043; font-size: 12px; }
  .ic16 { width: 16px; height: 16px; image-rendering: pixelated; border: 1px solid #f59e0b; }
  .ic48 { width: 48px; height: 48px; image-rendering: pixelated; border: 1px solid #2ea043; }
  .desc { font-size: 12px; color: #8b949e; line-height: 1.4; }
</style>
</head>
<body>
<header>
  <h1>Card_G — 25 Thẻ Cuối (C076–C100): Ảnh Bìa Thẻ + Spritesheet Sử Dụng 2x2 + Icon Trạng Thái 16x16 Dùng Chung</h1>
  <span style="font-size:12px;color:#8b949e">Animation 4-Frame chạy trực tiếp | Icon 16x16 Pixel-Crisp</span>
</header>
<div class="grid" id="grid"></div>
<script src="items_data.js"></script>
<script>
  const grid = document.getElementById("grid");
  const animImgs = [];
  Object.values(window.ITEMS_76_100).forEach(item => {
    const el = document.createElement("div");
    el.className = "card";
    el.innerHTML = `
      <div class="card-head">
        <span>${item.name}</span>
        <span class="tier">${item.tier}</span>
      </div>
      <div class="media-row">
        <img class="card-art" src="${item.card_b64}" alt="${item.id}" />
        <div class="anim-box"><img id="anim_${item.id}" src="${item.frames_b64[0]}" /></div>
      </div>
      <div class="status-bar">
        <img class="ic16" src="${item.icon16_b64}" title="16x16 gốc" />
        <img class="ic48" src="${item.icon16_b64}" title="16x16 Zoom 3x" />
        <div>
          <div style="color:#3fb950;font-weight:700">${item.status_name}</div>
          <div style="color:#8b949e">Dùng chung: ${item.status_shared_by.join(", ")}</div>
        </div>
      </div>
      <div class="desc">${item.effect_summary}</div>
    `;
    grid.appendChild(el);
    animImgs.push({ el: el.querySelector(`#anim_${item.id}`), frames: item.frames_b64 });
  });
  let f = 0;
  setInterval(() => {
    f = (f + 1) % 4;
    animImgs.forEach(a => { if (a.frames[f]) a.el.src = a.frames[f]; });
  }, 220);
</script>
</body>
</html>
''', encoding="utf-8")
    print(f"[master] Master 25-item overview ({out_master}) & assets/items_viewer.html updated!")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", type=str, help="Forge a specific card id (e.g. c081) or 'all'")
    parser.add_argument("--force-gen", action="store_true")
    args = parser.parse_args()

    forge_shared_status_icons(force_gen=args.force_gen)

    target_id = (args.id or "all").lower()
    for card_cfg in FINAL_25_CARDS:
        if target_id in ("all", card_cfg["id"]):
            forge_single_card_76_100(card_cfg, force_gen=args.force_gen)

    if target_id == "all":
        build_master_overview_and_html_viewer()


if __name__ == "__main__":
    main()
