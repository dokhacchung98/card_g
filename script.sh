#!/usr/bin/env bash
set -euo pipefail

cd /Users/dochung/Desktop/card_g
git add -A
git commit -m "feat(c001): redraw 4 VFX as lightweight soft-opacity translucent PNGs"
git status -s
git log -n 2 --oneline
