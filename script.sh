#!/usr/bin/env bash
set -euo pipefail

cp /Users/dochung/Desktop/card_g/assets/weapons/w003_dao_phu_doi_thi/qc_previews/w003_weapon_and_aura_audit.png \
   /Users/dochung/.gemini/antigravity-cli/brain/ab7dc2b7-9521-42a4-be21-abd94f794ce3/w003_weapon_and_aura_audit.png

cd /Users/dochung/Desktop/card_g
git status -s
git add -A
git commit -m "fix(w003): replace transparent card preview with full opaque RGB dark-fantasy card illustration (884x632 PNG & 354x253 WebP)"
git push origin main
