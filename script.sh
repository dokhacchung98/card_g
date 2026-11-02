#!/usr/bin/env bash
set -euo pipefail

python3 /Users/dochung/Desktop/card_g/tools/build_w003_system.py

cd /Users/dochung/Desktop/card_g
git status -s
git add -A
git commit -m "fix(w003): sync opaque RGB W003 card preview into all HTML editors"
git push origin main
