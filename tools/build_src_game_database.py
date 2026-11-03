#!/usr/bin/env python3
"""
Parse all 100 Core Cards (C01 - C100) from GAME_DESIGN.md and link them
to their exact weapon/item assets, Godot .tscn scenes, and skill metadata.
Outputs: /Users/dochung/Desktop/card_g/src_game/data/cards_db.json
"""

import json
import pathlib
import re

ROOT = pathlib.Path("/Users/dochung/Desktop/card_g")
GDD_PATH = ROOT / "GAME_DESIGN.md"
OUT_DIR = ROOT / "src_game/data"


def parse_number(s: str, default=0.0):
    m = re.search(r"[-+]?\d+(?:\.\d+)?", s)
    return float(m.group(0)) if m else default


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    txt = GDD_PATH.read_text(encoding="utf-8")

    # Map w001..w080 folders
    weapon_dirs = {}
    for p in sorted((ROOT / "assets/weapons").glob("w*_*")):
        if p.is_dir():
            m = re.match(r"^w(\d{3})_(.+)$", p.name)
            if m:
                idx = int(m.group(1))
                weapon_dirs[idx] = p

    # Map c076..c100 item folders
    item_dirs = {}
    for p in sorted((ROOT / "assets/items").glob("c*_*")):
        if p.is_dir():
            m = re.match(r"^c(\d{3})_(.+)$", p.name)
            if m:
                idx = int(m.group(1))
                item_dirs[idx] = p

    # Load item status icons mapping if present
    status_map = {}
    for idx, idir in item_dirs.items():
        meta_f = idir / "item_meta.json"
        if meta_f.exists():
            meta = json.loads(meta_f.read_text(encoding="utf-8"))
            status_map[idx] = meta.get("status_id", "status_corrosion_curse")

    cards = []
    lines = txt.splitlines()

    for line in lines:
        line_s = line.strip()
        if not line_s.startswith("| `C"):
            continue
        parts = [c.strip() for c in line_s.strip("|").split("|")]
        if len(parts) < 6:
            continue

        code_raw = parts[0].strip("` ")
        m_code = re.match(r"^C(\d+)$", code_raw)
        if not m_code:
            continue
        c_num = int(m_code.group(1))
        cid = f"C{c_num:03d}"
        wid = f"w{c_num:03d}"
        name = parts[1].replace("**", "").strip()
        rarity = parts[2].replace("**", "").strip()
        sub_tag = parts[3].replace("`", "").strip()

        if c_num <= 20:
            role_group = "atk_phys"
            role_label = "Tấn Công Vật Lý"
            is_item = False
        elif c_num <= 40:
            role_group = "atk_mag"
            role_label = "Tấn Công Ma Pháp"
            is_item = False
        elif c_num <= 60:
            role_group = "tanker"
            role_label = "Tanker Đỡ Đòn"
            is_item = False
        elif c_num <= 80:
            role_group = "support"
            role_label = "Hỗ Trợ"
            is_item = False
        else:
            role_group = "item"
            role_label = "Vật Phẩm"
            is_item = True

        if not is_item and len(parts) >= 8:
            # Hero card row: | Mã | Tên | Hiếm | Phân Loại | HP·Mana·Khiên | Dame·ASPD·Range | Giáp·K.Phép·MSPD | Skill |
            ui_col = parts[4].replace("`", "")
            atk_col = parts[5].replace("`", "")
            def_col = parts[6].replace("`", "")
            skill_col = parts[7]

            hp = int(parse_number(re.search(r"HP:\s*(\d+)", ui_col).group(1), 250))
            mana = int(parse_number(re.search(r"Mana:\s*(\d+)", ui_col).group(1), 60))
            shield = int(parse_number(re.search(r"Khiên:\s*(\d+)", ui_col).group(1), 0))

            dame = int(parse_number(re.search(r"Dame:\s*(\d+)", atk_col).group(1), 30))
            aspd = float(parse_number(re.search(r"ASPD:\s*([\d.]+)", atk_col).group(1), 1.0))
            rng = float(parse_number(re.search(r"Range:\s*([\d.]+)", atk_col).group(1), 1.2))
            is_ranged = rng >= 2.5

            pdef = int(parse_number(re.search(r"Giáp:\s*(\d+)", def_col).group(1), 20))
            mdef = int(parse_number(re.search(r"K\.Phép:\s*(\d+)", def_col).group(1), 20))
            mspd = int(parse_number(re.search(r"MSPD:\s*(\d+)", def_col).group(1), 115))

            skill_clean = re.sub(r"\*\*([^*]+)\*\*", r"\1", skill_col).replace("`", "").strip()
            skill_name = skill_clean.split(":")[0].strip() if ":" in skill_clean else "Tuyệt Kỹ"
            skill_desc = skill_clean.split(":", 1)[1].strip() if ":" in skill_clean else skill_clean

            wdir = weapon_dirs.get(c_num)
            slug = wdir.name if wdir else f"{wid}_weapon"
            tscn_files = list((wdir / "godot").glob("*.tscn")) if wdir and (wdir / "godot").exists() else []
            tscn_res = f"res://assets/weapons/{slug}/godot/{tscn_files[0].name}" if tscn_files else ""
            card_art_res = f"res://assets/weapons/{slug}/card/{wid}_card_preview.png"
            weapon_main_res = f"res://assets/weapons/{slug}/parts/weapon_main.png"

            cards.append({
                "id": cid,
                "num": c_num,
                "name": name,
                "rarity": rarity,
                "role_group": role_group,
                "role_label": role_label,
                "sub_tag": sub_tag,
                "is_item": False,
                "hp": hp,
                "mana": mana,
                "shield": shield,
                "dame": dame,
                "aspd": aspd,
                "range": rng,
                "is_ranged": is_ranged,
                "def": pdef,
                "mdef": mdef,
                "mspd": mspd,
                "auto_target": "NearestEnemy",
                "skill_name": skill_name,
                "skill_desc": skill_desc,
                "card_art": card_art_res,
                "icon_art": weapon_main_res,
                "tscn_path": tscn_res,
                "status_icon": "",
            })
        else:
            # Item card row: | Mã | Tên | Hiếm | Phân Loại | Auto-Target | Hiệu Ứng |
            auto_target = parts[4].replace("`", "").strip()
            eff_col = parts[5]
            eff_clean = re.sub(r"\*\*([^*]+)\*\*", r"\1", eff_col).replace("`", "").strip()

            idir = item_dirs.get(c_num)
            slug = idir.name if idir else f"c{c_num:03d}_item"
            card_art_res = f"res://assets/items/{slug}/card/c{c_num:03d}_card_preview.png"
            item_main_res = f"res://assets/items/{slug}/parts/item_main.png"
            use_frames = [f"res://assets/items/{slug}/parts/use_frame_{i}.png" for i in range(4)]
            st_id = status_map.get(c_num, "status_corrosion_curse")
            status_icon_res = f"res://assets/items/status_icons/{st_id}_16x16.png"

            cards.append({
                "id": cid,
                "num": c_num,
                "name": name,
                "rarity": rarity,
                "role_group": role_group,
                "role_label": role_label,
                "sub_tag": sub_tag,
                "is_item": True,
                "hp": 0,
                "mana": 0,
                "shield": 0,
                "dame": 0,
                "aspd": 0.0,
                "range": 9.9,
                "is_ranged": True,
                "def": 0,
                "mdef": 0,
                "mspd": 0,
                "auto_target": auto_target,
                "skill_name": "Kích Hoạt Tức Thì",
                "skill_desc": eff_clean,
                "card_art": card_art_res,
                "icon_art": item_main_res,
                "use_frames": use_frames,
                "tscn_path": "",
                "status_icon": status_icon_res,
            })

    cards.sort(key=lambda x: x["num"])
    out_file = OUT_DIR / "cards_db.json"
    out_file.write_text(json.dumps(cards, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Successfully parsed {len(cards)} cards into {out_file}!")
    by_role = {}
    by_rarity = {}
    for c in cards:
        by_role[c["role_group"]] = by_role.get(c["role_group"], 0) + 1
        by_rarity[c["rarity"]] = by_rarity.get(c["rarity"], 0) + 1
    print("By role:", by_role)
    print("By rarity:", by_rarity)


if __name__ == "__main__":
    main()
