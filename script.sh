#!/usr/bin/env bash
set -euo pipefail

cd /Users/dochung/Desktop/card_g

echo "=== 1. Deploying Web Build to Firebase Hosting ==="
firebase deploy --only hosting

echo "=== 2. Committing and Pushing Changes to GitHub ==="
git add -A
git status -s
if ! git diff --cached --quiet; then
  git commit -m "fix(battle): raise hand carousel arc higher inside bottom panel and verify via headless dogfood"
  git push origin main
fi
