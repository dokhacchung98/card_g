#!/usr/bin/env bash
set -euo pipefail

cd /Users/dochung/Desktop/card_g

git add -A
echo "Total staged files: $(git diff --cached --name-only | wc -l)"

git commit -m "feat(game): complete Godot 4 tactical card game, 500 fixed-element cards, dual currency shop, tutorial guide, and fantasy UI/HUD assets"
git push origin main
git status -s
git log -n 1 --oneline
