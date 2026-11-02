#!/usr/bin/env bash
set -euo pipefail

cd /Users/dochung/Desktop/card_g

git add -A
git commit -m "chore(weapons,rules): enforce static weapon_anim_0 for N/R tiers and 4-frame weapon animation only for S/SSR tiers"
git push origin main
git status -s
