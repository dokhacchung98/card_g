#!/usr/bin/env bash
set -euo pipefail

cd /Users/dochung/Desktop/card_g
if [ -n "$(git status -s)" ]; then
  git add -A
  git commit --amend --no-edit
  git push -f origin main
fi
git status -s
git log -n 3 --oneline
