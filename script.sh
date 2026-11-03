#!/usr/bin/env bash
set -euo pipefail

cd /Users/dochung/Desktop/card_g

git add -A
git commit -m "feat(backend,firebase): add be-card-g submodule, Firebase Android/iOS/Web configs, Google Auth, and 10s matchmaking bot fallback"
git push origin main
git log -n 2 --oneline
git submodule status
