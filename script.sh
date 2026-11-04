#!/usr/bin/env bash
set -euo pipefail

cd /Users/dochung/Desktop/card_g

echo "=== 1. Deploying Web Build to Firebase Hosting ==="
firebase deploy --only hosting

echo "=== 2. Committing and Pushing Changes to GitHub ==="
git add -A
git status -s
if ! git diff --cached --quiet; then
  git commit -m "feat(ui,battle): enlarge fonts, declutter UI/cards, fix hand tap pull-up animation, remove skip/speed header buttons"
  git push origin main
fi
