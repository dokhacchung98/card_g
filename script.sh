#!/usr/bin/env bash
set -euo pipefail

cd /Users/dochung/Desktop/card_g

git add -A
git status -s
git commit -m "perf(pipeline): implement one-shot forge_weapon.py CLI & external weapons_data.js (~90% token reduction)"
git push origin main
