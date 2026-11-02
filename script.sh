#!/usr/bin/env bash
set -euo pipefail

cd /Users/dochung/Desktop/card_g

python3 - << 'PY'
import os, glob

repo = "/Users/dochung/Desktop/card_g"

targets_to_delete = []

for p in ["assets/cards/icons/elements_sheet", "assets/cards/icons/types_sheet", "assets/cards/icons/stats_sheet"]:
    for f in glob.glob(os.path.join(repo, p, "*.png")):
        targets_to_delete.append(f)

for p in [
    "assets/cards/raw/*.png",
    "assets/cards/previews/*.png",
    "assets/cards/references/*.png",
    "assets/cards/frames/khoet_common/*.png",
    "assets/cards/frames/khoet_anh_kem_icon_chiso/*.png",
    "assets/cards/frames/khoet_anh/*.png",
    "assets/cards/frames/card_back.png",
]:
    for f in glob.glob(os.path.join(repo, p)):
        targets_to_delete.append(f)

for f in glob.glob(os.path.join(repo, "assets/heroes/*/qc_previews/*_sheet.png")):
    targets_to_delete.append(f)

for f in glob.glob(os.path.join(repo, "assets/heroes/*/reference/processed/*.png")):
    targets_to_delete.append(f)

for f in [
    "assets/heroes/c001_hac_kiem_tan_binh/parts/c001_parts_upper_2x3_raw.png",
    "assets/heroes/c001_hac_kiem_tan_binh/vfx/c001_vfx_2x2_raw.png",
    "assets/heroes/c001_hac_kiem_tan_binh/card/c001_card_art_raw.png",
]:
    full_p = os.path.join(repo, f)
    if os.path.exists(full_p):
        targets_to_delete.append(full_p)

for i in range(4):
    f = os.path.join(repo, f"assets/weapons/w018_huyet_kiem_hanh_quyet/parts/weapon_aura_{i}.png")
    if os.path.exists(f):
        targets_to_delete.append(f)

deleted_count = 0
deleted_bytes = 0
for f in targets_to_delete:
    if os.path.exists(f):
        sz = os.path.getsize(f)
        os.remove(f)
        deleted_count += 1
        deleted_bytes += sz

print(f"Deleted {deleted_count} unused files ({deleted_bytes / (1024*1024):.2f} MB freed).")

# Clean up empty directories in assets
for root, dirs, files in os.walk("assets", topdown=False):
    for d in dirs:
        full_d = os.path.join(root, d)
        if os.path.exists(full_d) and not os.listdir(full_d):
            os.rmdir(full_d)
            print("Removed empty dir:", full_d)
PY

echo "=== GIT STATUS AFTER DELETION ==="
git status -s

echo "=== GIT COMMIT AND PUSH ==="
git add -u
git commit -m "chore(assets): remove 112 unused raw sheets, intermediate mockups, and legacy test previews"
git push origin main
