#!/usr/bin/env bash
set -euo pipefail

cd /Users/dochung/Desktop/card_g
git status -s
git add -A
git commit -m "fix(w003): fix stickman bone proportions, forward-facing cleaver orientation, grip points, and 6-action animations in w003_editor.html"
git push origin main
