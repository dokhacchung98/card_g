#!/usr/bin/env bash
set -euo pipefail

cd /Users/dochung/Desktop/card_g
git add -A
git commit -m "refactor(card): replace pre-baked card image with horizontal portrait preview (884x632 & 354x253) and update skill"
git push origin main
git status -s
git log -n 2 --oneline
