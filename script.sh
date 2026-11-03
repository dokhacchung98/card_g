#!/usr/bin/env bash
set -euo pipefail

GODOT_BIN="/Applications/Godot.app/Contents/MacOS/Godot"

echo "=== 1. HEADLESS UI BOUNDS AUDIT (VERIFY ZERO OVERFLOWS) ==="
"$GODOT_BIN" --headless --path /Users/dochung/Desktop/card_g/src_game -s res://scripts/tools/inspect_ui_bounds.gd

echo "=== 2. EXPORT WEB, ANDROID & IOS (HEADLESS) ==="
"$GODOT_BIN" --headless --path /Users/dochung/Desktop/card_g/src_game --export-release "Web" /Users/dochung/Desktop/card_g/build/web/index.html
"$GODOT_BIN" --headless --path /Users/dochung/Desktop/card_g/src_game --export-debug "Android" /Users/dochung/Desktop/card_g/build/android/ArcanaFive.apk
"$GODOT_BIN" --headless --path /Users/dochung/Desktop/card_g/src_game --export-debug "iOS" /Users/dochung/Desktop/card_g/build/ios/ArcanaFive.xcodeproj

echo "=== 3. RUN BACKGROUND HEADLESS BROWSER DOGFOOD (NO WINDOW POPUP) ==="
python3 /Users/dochung/.gemini/antigravity-cli/brain/ab7dc2b7-9521-42a4-be21-abd94f794ce3/scratch/run_bg_dogfood.py

echo "=== 4. DEPLOY UPDATED WEB BUILD TO FIREBASE HOSTING ==="
cd /Users/dochung/Desktop/card_g
firebase deploy --only hosting --project arcana-five-card-g --non-interactive

echo "=== 5. COMMIT & PUSH TO GITHUB ==="
cd /Users/dochung/Desktop/card_g
if [[ -n "$(git status --porcelain)" ]]; then
  git add -A
  git commit -m "fix(ui): fix HomeScreen horizontal overflow clipping and display 15-card loadout in 5x3 grid"
  git push origin main
fi

echo "=== ALL TASKS COMPLETED SUCCESSFULLY! ==="
