#!/usr/bin/env bash
set -euo pipefail

cd /Users/dochung/Desktop/card_g

echo "=== 1. Check Vercel Backend Endpoint ==="
curl -s https://be-card-g.vercel.app/api/v1/health || true
echo ""

echo "=== 2. Check Firebase Web Hosting Live URL ==="
curl -I -s https://arcana-five-card-g.web.app | head -n 8 || true

echo "=== 3. Commit & Push Updated Export Configs and Submodule Reference to GitHub ==="
git add -A
git status -s
git commit -m "feat(deploy): configure Web, Android, and iOS exports, Firebase Hosting, and connect to https://be-card-g.vercel.app" || true
git push origin main
