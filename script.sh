#!/usr/bin/env bash
set -euo pipefail

echo "=== 1. RUN BACKEND UNIT & INTEGRATION TESTS (15 STARTER CARDS) ==="
cd /Users/dochung/Desktop/card_g/be-card-g
npm test

echo "=== 2. RUN GODOT HEADLESS VERIFICATION FOR LOGIN SCREEN & 15 STARTER CARDS ==="
GODOT_BIN="/Applications/Godot.app/Contents/MacOS/Godot"
"$GODOT_BIN" --headless --path /Users/dochung/Desktop/card_g/src_game -s res://scripts/tools/verify_login_and_15_starter.gd

echo "=== 3. RE-EXPORT WEB, ANDROID APK & IOS XCODE PROJECT ==="
mkdir -p /Users/dochung/Desktop/card_g/build/web
mkdir -p /Users/dochung/Desktop/card_g/build/android
mkdir -p /Users/dochung/Desktop/card_g/build/ios

"$GODOT_BIN" --headless --path /Users/dochung/Desktop/card_g/src_game --export-release "Web" /Users/dochung/Desktop/card_g/build/web/index.html
"$GODOT_BIN" --headless --path /Users/dochung/Desktop/card_g/src_game --export-debug "Android" /Users/dochung/Desktop/card_g/build/android/ArcanaFive.apk
"$GODOT_BIN" --headless --path /Users/dochung/Desktop/card_g/src_game --export-debug "iOS" /Users/dochung/Desktop/card_g/build/ios/ArcanaFive.xcodeproj

ls -lh /Users/dochung/Desktop/card_g/build/web/index.html \
       /Users/dochung/Desktop/card_g/build/android/ArcanaFive.apk \
       /Users/dochung/Desktop/card_g/build/ios/ArcanaFive.pck

echo "=== 4. DEPLOY UPDATED WEB BUILD TO FIREBASE HOSTING ==="
cd /Users/dochung/Desktop/card_g
firebase deploy --only hosting --project arcana-five-card-g --non-interactive

echo "=== 5. COMMIT & PUSH SUBMODULE (be-card-g) AND MAIN REPO (card_g) ==="
cd /Users/dochung/Desktop/card_g/be-card-g
if [[ -n "$(git status --porcelain)" ]]; then
  git add -A
  git commit -m "feat(auth): gift 15 default starter cards on first Google login"
  git push origin main
fi

cd /Users/dochung/Desktop/card_g
if [[ -n "$(git status --porcelain)" ]]; then
  git add -A
  git commit -m "feat(login): add Google Login first screen and 15 default starter cards gift on first login"
  git push origin main
fi

echo "=== ALL DONE SUCCESSFULLY! ==="
