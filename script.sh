#!/usr/bin/env bash
set -euo pipefail

cd /Users/dochung/Desktop/card_g

echo "=== CLEANING UP .DS_Store ==="
find . -name ".DS_Store" -delete

echo "=== GIT STATUS BEFORE ADD ==="
git status -s

echo "=== GIT ADD ==="
git add .

echo "=== GIT STATUS STAGED ==="
git status -s

echo "=== COMMIT AND PUSH ==="
git commit -m "feat(system): add sticker hero 4 teams, C002-C004 heroes, W001 & W018 SSR weapon systems and editors" || echo "Nothing to commit"

echo "=== PUSHING TO ORIGIN MAIN ==="
git push origin main
