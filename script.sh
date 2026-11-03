#!/usr/bin/env bash
set -euo pipefail

cd /Users/dochung/Desktop/card_g/src_game

# 1. Headless audit of Battle mechanics & Curved Stack Carousel
/Applications/Godot.app/Contents/MacOS/Godot --headless --path . --script /Users/dochung/.gemini/antigravity-cli/brain/ab7dc2b7-9521-42a4-be21-abd94f794ce3/scratch/test_battle_mechanics.gd

# 2. Export Web, Android, and iOS builds
mkdir -p /Users/dochung/Desktop/card_g/build/web
mkdir -p /Users/dochung/Desktop/card_g/build/android
mkdir -p /Users/dochung/Desktop/card_g/build/ios

/Applications/Godot.app/Contents/MacOS/Godot --headless --path . --export-release "Web" /Users/dochung/Desktop/card_g/build/web/index.html
/Applications/Godot.app/Contents/MacOS/Godot --headless --path . --export-debug "Android" /Users/dochung/Desktop/card_g/build/android/arcana-five-card-g-debug.apk
/Applications/Godot.app/Contents/MacOS/Godot --headless --path . --export-debug "iOS" /Users/dochung/Desktop/card_g/build/ios/arcana-five-card-g.xcodeproj

# 3. Background Playwright dogfood
python3 /Users/dochung/.gemini/antigravity-cli/brain/ab7dc2b7-9521-42a4-be21-abd94f794ce3/scratch/run_bg_dogfood.py

# 4. Deploy Web to Firebase Hosting
cd /Users/dochung/Desktop/card_g
firebase deploy --only hosting --project arcana-five-card-g

# 5. Commit and push to GitHub
git add -A
if ! git diff --cached --quiet; then
  git commit -m "feat(ui,battle): 1-tap Google login, touch-scroll, large cards, curved stack hand carousel, +2 draw anim, instant item use & no player auto-bot"
  git push origin main
fi
