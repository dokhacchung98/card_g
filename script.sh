#!/usr/bin/env bash
set -euo pipefail

cd /Users/dochung/Desktop/card_g

git status -s
git add -A
git commit -m "feat(branding): add official ARCANA FIVE dark-fantasy app icon and game logo"
git push origin main
git log -n 2 --oneline
