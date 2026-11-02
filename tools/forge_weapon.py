#!/usr/bin/env python3
"""
Unified One-Shot Weapon & Spine Rig Builder (`forge_weapon.py`)
===============================================================
Token-Optimized Pipeline for `card_g` (Saves ~85-90% tokens per weapon):
- Input: A compact ~25-line JSON config (`assets/weapons/configs/wXXX.json`)
- Automatically handles:
  1. Muse Local API thread reset (`POST /v1/thread`) & raw weapon ref generation (`#FF00FF` + `layout_guide_1x1.png`).
  2. Chroma-key background removal, largest-component isolation (no stray ammo), handle orientation, 0px tight crop (`weapon_main.png` / `weapon_anim_0.png` / `weapon_offhand.png`).
  3. (Only for S / SSR tier; skipped for N / R tier) 2x2 Animated Weapon Spritesheet (`weapon_anim_0..3.png` + `weapon_aura.png`).
  4. Card Preview generation (`884x632` Opaque RGB PNG & `354x253` Opaque RGB WebP) — guaranteed `mode="RGB"`.
  5. 17-Bone2D Stickman Anatomical Rig (`0px` joint separation) + 6-Action Archetype Animations (`idle`, `walk`, `attack`, `cast`, `hurt`, `death`).
  6. QC Audit Boards (`wXXX_weapon_and_aura_audit.png` & `wXXX_sticker_all_6_actions_overview.png`).
  7. Godot 4 Scene & Script (`godot/cXXX_<slug>.tscn` & `.gd`).
  8. Updates `assets/weapons_data.js` and lightweight (~25 KB) `assets/sticker_weapon_editor.html` + `wXXX_editor.html`.
"""

import argparse
import base64
import json
import math
import pathlib
import shutil
import urllib.request
from collections import deque
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

ROOT = pathlib.Path("/Users/dochung/Desktop/card_g")
MUSE_BASE = "http://127.0.0.1:3456"
LAYOUT_1X1 = ROOT / "layout_guide/layout_guide_1x1.png"
LAYOUT_2X2 = ROOT / "layout_guide/layout_guide_2x2.png"
STICKER_DIR = ROOT / "assets/sticker_hero/godot/parts"
WEAPONS_DATA_JS = ROOT / "assets/weapons_data.js"
MAIN_EDITOR_HTML = ROOT / "assets/sticker_weapon_editor.html"

TEAMS = ["team_blue", "team_red", "team_green", "team_amber"]
VFX_NAMES = ["fx_slash", "fx_slash_heavy", "fx_spark", "fx_dust"]


# ==============================================================================
# 1. ARCHETYPE 6-ACTION POSES (0px Joint Separation on all Child Bones)
# ==============================================================================
ARCHETYPE_ACTIONS = {
    "melee_cleaver": {
        "idle": {
            "grid": [2, 2], "length": 1.2, "loop": True,
            "frames": [
                {"t": 0.0, "Hip": [0, 0, 0], "Chest": [0, 0, 0], "Neck": [0, 0, 0], "Head": [0, 0, 0], "UpperArm_R": [0, 0, 0], "Forearm_R": [0, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [0, 0, 0], "Forearm_L": [0, 0, 0], "Hand_L": [0, 0, 0], "Weapon_Front": [0, 0, 0], "Thigh_R": [0, 0, 0], "Shin_R": [0, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [0, 0, 0], "Shin_L": [0, 0, 0], "Foot_L": [0, 0, 0]},
                {"t": 0.3, "Hip": [0, 3, 0], "Chest": [2, 0, 0], "Neck": [0, 0, 0], "Head": [-2, 0, 0], "UpperArm_R": [3, 0, 0], "Forearm_R": [2, 0, 0], "Hand_R": [-2, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-3, 0, 0], "Forearm_L": [-2, 0, 0], "Hand_L": [-1, 0, 0], "Weapon_Front": [-2, 0, 0], "Thigh_R": [-3, 0, 0], "Shin_R": [3, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-2, 0, 0], "Shin_L": [2, 0, 0], "Foot_L": [0, 0, 0]},
                {"t": 0.6, "Hip": [0, 5, 0], "Chest": [4, 0, 0], "Neck": [0, 0, 0], "Head": [-3, 0, 0], "UpperArm_R": [5, 0, 0], "Forearm_R": [4, 0, 0], "Hand_R": [-3, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-5, 0, 0], "Forearm_L": [-4, 0, 0], "Hand_L": [-2, 0, 0], "Weapon_Front": [-4, 0, 0], "Thigh_R": [-5, 0, 0], "Shin_R": [5, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-4, 0, 0], "Shin_L": [4, 0, 0], "Foot_L": [0, 0, 0]},
                {"t": 0.9, "Hip": [0, 2, 0], "Chest": [1, 0, 0], "Neck": [0, 0, 0], "Head": [-1, 0, 0], "UpperArm_R": [2, 0, 0], "Forearm_R": [1, 0, 0], "Hand_R": [-1, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-2, 0, 0], "Forearm_L": [-1, 0, 0], "Hand_L": [-1, 0, 0], "Weapon_Front": [-1, 0, 0], "Thigh_R": [-2, 0, 0], "Shin_R": [2, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-1, 0, 0], "Shin_L": [1, 0, 0], "Foot_L": [0, 0, 0]},
            ],
        },
        "walk": {
            "grid": [2, 3], "length": 0.9, "loop": True,
            "frames": [
                {"t": 0.0, "Hip": [-2, 3, 2], "Chest": [4, 0, 0], "Neck": [0, 0, 0], "Head": [-3, 0, 0], "UpperArm_R": [14, 0, 0], "Forearm_R": [6, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-14, 0, 0], "Forearm_L": [-6, 0, 0], "Hand_L": [-2, 0, 0], "Weapon_Front": [-4, 0, 0], "Thigh_R": [-22, 0, 0], "Shin_R": [12, 0, 0], "Foot_R": [6, 0, 0], "Thigh_L": [18, 0, 0], "Shin_L": [14, 0, 0], "Foot_L": [8, 0, 0]},
                {"t": 0.15, "Hip": [-1, 5, 2], "Chest": [5, 0, 0], "Neck": [0, 0, 0], "Head": [-4, 0, 0], "UpperArm_R": [8, 0, 0], "Forearm_R": [4, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-8, 0, 0], "Forearm_L": [-4, 0, 0], "Hand_L": [-2, 0, 0], "Weapon_Front": [-2, 0, 0], "Thigh_R": [-10, 0, 0], "Shin_R": [14, 0, 0], "Foot_R": [2, 0, 0], "Thigh_L": [8, 0, 0], "Shin_L": [18, 0, 0], "Foot_L": [10, 0, 0]},
                {"t": 0.3, "Hip": [0, -1, 0], "Chest": [3, 0, 0], "Neck": [0, 0, 0], "Head": [-2, 0, 0], "UpperArm_R": [-8, 0, 0], "Forearm_R": [-4, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [8, 0, 0], "Forearm_L": [2, 0, 0], "Hand_L": [0, 0, 0], "Weapon_Front": [2, 0, 0], "Thigh_R": [4, 0, 0], "Shin_R": [8, 0, 0], "Foot_R": [-4, 0, 0], "Thigh_L": [-10, 0, 0], "Shin_L": [16, 0, 0], "Foot_L": [6, 0, 0]},
                {"t": 0.45, "Hip": [2, 3, 2], "Chest": [5, 0, 0], "Neck": [0, 0, 0], "Head": [-3, 0, 0], "UpperArm_R": [-14, 0, 0], "Forearm_R": [-6, 0, 0], "Hand_R": [-2, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [14, 0, 0], "Forearm_L": [4, 0, 0], "Hand_L": [2, 0, 0], "Weapon_Front": [4, 0, 0], "Thigh_R": [16, 0, 0], "Shin_R": [14, 0, 0], "Foot_R": [6, 0, 0], "Thigh_L": [-22, 0, 0], "Shin_L": [10, 0, 0], "Foot_L": [-4, 0, 0]},
                {"t": 0.6, "Hip": [1, 5, 2], "Chest": [6, 0, 0], "Neck": [0, 0, 0], "Head": [-4, 0, 0], "UpperArm_R": [-8, 0, 0], "Forearm_R": [-4, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [8, 0, 0], "Forearm_L": [2, 0, 0], "Hand_L": [0, 0, 0], "Weapon_Front": [2, 0, 0], "Thigh_R": [8, 0, 0], "Shin_R": [18, 0, 0], "Foot_R": [8, 0, 0], "Thigh_L": [-10, 0, 0], "Shin_L": [12, 0, 0], "Foot_L": [0, 0, 0]},
                {"t": 0.75, "Hip": [-1, -1, 0], "Chest": [3, 0, 0], "Neck": [0, 0, 0], "Head": [-2, 0, 0], "UpperArm_R": [6, 0, 0], "Forearm_R": [2, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-6, 0, 0], "Forearm_L": [-2, 0, 0], "Hand_L": [-1, 0, 0], "Weapon_Front": [-1, 0, 0], "Thigh_R": [-8, 0, 0], "Shin_R": [10, 0, 0], "Foot_R": [4, 0, 0], "Thigh_L": [4, 0, 0], "Shin_L": [10, 0, 0], "Foot_L": [4, 0, 0]},
            ],
        },
        "attack": {
            "grid": [2, 2], "length": 0.65, "loop": False,
            "frames": [
                {"t": 0.0, "Hip": [-8, 3, -4], "Chest": [-8, 0, 0], "Neck": [0, 0, 0], "Head": [6, 0, 0], "UpperArm_R": [18, 0, 0], "Forearm_R": [12, 0, 0], "Hand_R": [6, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-46, 0, 0], "Forearm_L": [-20, 0, 0], "Hand_L": [-14, 0, 0], "Weapon_Front": [-18, 0, 0], "Thigh_R": [10, 0, 0], "Shin_R": [10, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-10, 0, 0], "Shin_L": [10, 0, 0], "Foot_L": [0, 0, 0]},
                {"t": 0.18, "Hip": [10, 5, 6], "Chest": [10, 0, 0], "Neck": [0, 0, 0], "Head": [-6, 0, 0], "UpperArm_R": [-16, 0, 0], "Forearm_R": [-10, 0, 0], "Hand_R": [-6, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-8, 0, 0], "Forearm_L": [14, 0, 0], "Hand_L": [18, 0, 0], "Weapon_Front": [28, 0, 0], "Thigh_R": [-16, 0, 0], "Shin_R": [12, 0, 0], "Foot_R": [4, 0, 0], "Thigh_L": [14, 0, 0], "Shin_L": [12, 0, 0], "Foot_L": [4, 0, 0], "vfx": {"fx_slash": {"pos": [298, 248], "rot": 18, "scale": 0.72, "alpha": 0.94}}},
                {"t": 0.36, "Hip": [12, 7, 8], "Chest": [12, 0, 0], "Neck": [0, 0, 0], "Head": [-8, 0, 0], "UpperArm_R": [-22, 0, 0], "Forearm_R": [-14, 0, 0], "Hand_R": [-8, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [12, 0, 0], "Forearm_L": [22, 0, 0], "Hand_L": [24, 0, 0], "Weapon_Front": [44, 0, 0], "Thigh_R": [-20, 0, 0], "Shin_R": [14, 0, 0], "Foot_R": [6, 0, 0], "Thigh_L": [18, 0, 0], "Shin_L": [14, 0, 0], "Foot_L": [6, 0, 0], "vfx": {"fx_spark": {"pos": [336, 318], "rot": 0, "scale": 0.68, "alpha": 0.92}}},
                {"t": 0.52, "Hip": [2, 2, 1], "Chest": [2, 0, 0], "Neck": [0, 0, 0], "Head": [-1, 0, 0], "UpperArm_R": [-4, 0, 0], "Forearm_R": [-2, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-2, 0, 0], "Forearm_L": [0, 0, 0], "Hand_L": [0, 0, 0], "Weapon_Front": [0, 0, 0], "Thigh_R": [-4, 0, 0], "Shin_R": [4, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [4, 0, 0], "Shin_L": [4, 0, 0], "Foot_L": [0, 0, 0]},
            ],
        },
        "cast": {
            "grid": [2, 3], "length": 0.95, "loop": False,
            "frames": [
                {"t": 0.0, "Hip": [-10, 5, -4], "Chest": [-8, 0, 0], "Neck": [0, 0, 0], "Head": [6, 0, 0], "UpperArm_R": [20, 0, 0], "Forearm_R": [14, 0, 0], "Hand_R": [6, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-40, 0, 0], "Forearm_L": [-18, 0, 0], "Hand_L": [-14, 0, 0], "Weapon_Front": [-16, 0, 0], "Thigh_R": [8, 0, 0], "Shin_R": [10, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-10, 0, 0], "Shin_L": [10, 0, 0], "Foot_L": [0, 0, 0], "vfx": {"fx_dust": {"pos": [214, 384], "rot": 0, "scale": 0.62, "alpha": 0.76}}},
                {"t": 0.16, "Hip": [-14, 8, -6], "Chest": [-12, 0, 0], "Neck": [0, 0, 0], "Head": [10, 0, 0], "UpperArm_R": [26, 0, 0], "Forearm_R": [18, 0, 0], "Hand_R": [8, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-52, 0, 0], "Forearm_L": [-22, 0, 0], "Hand_L": [-18, 0, 0], "Weapon_Front": [-22, 0, 0], "Thigh_R": [12, 0, 0], "Shin_R": [14, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-14, 0, 0], "Shin_L": [14, 0, 0], "Foot_L": [0, 0, 0], "vfx": {"fx_dust": {"pos": [208, 384], "rot": 0, "scale": 0.72, "alpha": 0.86}}},
                {"t": 0.34, "Hip": [12, 4, 6], "Chest": [10, 0, 0], "Neck": [0, 0, 0], "Head": [-8, 0, 0], "UpperArm_R": [-18, 0, 0], "Forearm_R": [-12, 0, 0], "Hand_R": [-6, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-10, 0, 0], "Forearm_L": [12, 0, 0], "Hand_L": [16, 0, 0], "Weapon_Front": [26, 0, 0], "Thigh_R": [-18, 0, 0], "Shin_R": [12, 0, 0], "Foot_R": [4, 0, 0], "Thigh_L": [16, 0, 0], "Shin_L": [14, 0, 0], "Foot_L": [6, 0, 0], "vfx": {"fx_slash_heavy": {"pos": [294, 254], "rot": 12, "scale": 0.68, "alpha": 0.95}, "fx_dust": {"pos": [196, 384], "rot": 0, "scale": 0.74, "alpha": 0.85}}},
                {"t": 0.52, "Hip": [16, 7, 8], "Chest": [14, 0, 0], "Neck": [0, 0, 0], "Head": [-10, 0, 0], "UpperArm_R": [-24, 0, 0], "Forearm_R": [-16, 0, 0], "Hand_R": [-8, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [12, 0, 0], "Forearm_L": [22, 0, 0], "Hand_L": [24, 0, 0], "Weapon_Front": [46, 0, 0], "Thigh_R": [-22, 0, 0], "Shin_R": [14, 0, 0], "Foot_R": [6, 0, 0], "Thigh_L": [20, 0, 0], "Shin_L": [16, 0, 0], "Foot_L": [8, 0, 0], "vfx": {"fx_slash_heavy": {"pos": [304, 268], "rot": 28, "scale": 0.66, "alpha": 0.82}, "fx_spark": {"pos": [342, 320], "rot": 12, "scale": 0.7, "alpha": 0.94}}},
                {"t": 0.7, "Hip": [8, 3, 4], "Chest": [6, 0, 0], "Neck": [0, 0, 0], "Head": [-4, 0, 0], "UpperArm_R": [-10, 0, 0], "Forearm_R": [-6, 0, 0], "Hand_R": [-2, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [4, 0, 0], "Forearm_L": [8, 0, 0], "Hand_L": [8, 0, 0], "Weapon_Front": [14, 0, 0], "Thigh_R": [-10, 0, 0], "Shin_R": [8, 0, 0], "Foot_R": [2, 0, 0], "Thigh_L": [8, 0, 0], "Shin_L": [8, 0, 0], "Foot_L": [4, 0, 0], "vfx": {"fx_spark": {"pos": [346, 326], "rot": 25, "scale": 0.54, "alpha": 0.56}}},
                {"t": 0.86, "Hip": [0, 0, 0], "Chest": [0, 0, 0], "Neck": [0, 0, 0], "Head": [0, 0, 0], "UpperArm_R": [0, 0, 0], "Forearm_R": [0, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [0, 0, 0], "Forearm_L": [0, 0, 0], "Hand_L": [0, 0, 0], "Weapon_Front": [0, 0, 0], "Thigh_R": [0, 0, 0], "Shin_R": [0, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [0, 0, 0], "Shin_L": [0, 0, 0], "Foot_L": [0, 0, 0]},
            ],
        },
        "hurt": {
            "grid": [2, 2], "length": 0.55, "loop": False,
            "frames": [
                {"t": 0.0, "Hip": [-10, 4, -6], "Chest": [-12, 0, 0], "Neck": [0, 0, 0], "Head": [-14, 0, 0], "UpperArm_R": [14, 0, 0], "Forearm_R": [10, 0, 0], "Hand_R": [6, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [14, 0, 0], "Forearm_L": [-8, 0, 0], "Hand_L": [-6, 0, 0], "Weapon_Front": [-8, 0, 0], "Thigh_R": [8, 0, 0], "Shin_R": [6, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-6, 0, 0], "Shin_L": [8, 0, 0], "Foot_L": [0, 0, 0], "vfx": {"fx_spark": {"pos": [254, 214], "rot": -15, "scale": 0.68, "alpha": 0.9}}},
                {"t": 0.15, "Hip": [-16, 8, -8], "Chest": [-14, 0, 0], "Neck": [0, 0, 0], "Head": [-18, 0, 0], "UpperArm_R": [20, 0, 0], "Forearm_R": [14, 0, 0], "Hand_R": [8, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [20, 0, 0], "Forearm_L": [-12, 0, 0], "Hand_L": [-10, 0, 0], "Weapon_Front": [-12, 0, 0], "Thigh_R": [12, 0, 0], "Shin_R": [10, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-10, 0, 0], "Shin_L": [12, 0, 0], "Foot_L": [0, 0, 0]},
                {"t": 0.32, "Hip": [-8, 4, -4], "Chest": [-6, 0, 0], "Neck": [0, 0, 0], "Head": [-8, 0, 0], "UpperArm_R": [8, 0, 0], "Forearm_R": [6, 0, 0], "Hand_R": [4, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [8, 0, 0], "Forearm_L": [-4, 0, 0], "Hand_L": [-4, 0, 0], "Weapon_Front": [-4, 0, 0], "Thigh_R": [6, 0, 0], "Shin_R": [4, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-4, 0, 0], "Shin_L": [6, 0, 0], "Foot_L": [0, 0, 0]},
                {"t": 0.48, "Hip": [0, 0, 0], "Chest": [0, 0, 0], "Neck": [0, 0, 0], "Head": [0, 0, 0], "UpperArm_R": [0, 0, 0], "Forearm_R": [0, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [0, 0, 0], "Forearm_L": [0, 0, 0], "Hand_L": [0, 0, 0], "Weapon_Front": [0, 0, 0], "Thigh_R": [0, 0, 0], "Shin_R": [0, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [0, 0, 0], "Shin_L": [0, 0, 0], "Foot_L": [0, 0, 0]},
            ],
        },
        "death": {
            "grid": [2, 3], "length": 1.1, "loop": False,
            "frames": [
                {"t": 0.0, "Hip": [-10, 6, -6], "Chest": [-12, 0, 0], "Neck": [0, 0, 0], "Head": [-14, 0, 0], "UpperArm_R": [14, 0, 0], "Forearm_R": [8, 0, 0], "Hand_R": [6, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [14, 0, 0], "Forearm_L": [-8, 0, 0], "Hand_L": [-6, 0, 0], "Weapon_Front": [-8, 0, 0], "Thigh_R": [10, 0, 0], "Shin_R": [8, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-8, 0, 0], "Shin_L": [10, 0, 0], "Foot_L": [0, 0, 0], "vfx": {"fx_spark": {"pos": [254, 212], "rot": 0, "scale": 0.72, "alpha": 0.92}}},
                {"t": 0.22, "Hip": [-6, 26, 14], "Chest": [16, 0, 0], "Neck": [0, 0, 0], "Head": [12, 0, 0], "UpperArm_R": [24, 0, 0], "Forearm_R": [12, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-16, 0, 0], "Forearm_L": [-10, 0, 0], "Hand_L": [-12, 0, 0], "Weapon_Front": [-16, 0, 0], "Thigh_R": [-42, 0, 0], "Shin_R": [64, 0, 0], "Foot_R": [12, 0, 0], "Thigh_L": [-36, 0, 0], "Shin_L": [58, 0, 0], "Foot_L": [10, 0, 0]},
                {"t": 0.45, "Hip": [-4, 52, 30], "Chest": [24, 0, 0], "Neck": [0, 0, 0], "Head": [18, 0, 0], "UpperArm_R": [36, 0, 0], "Forearm_R": [18, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-32, 0, 0], "Forearm_L": [-16, 0, 0], "Hand_L": [-20, 0, 0], "Weapon_Front": [-26, 0, 0], "Thigh_R": [-66, 0, 0], "Shin_R": [90, 0, 0], "Foot_R": [16, 0, 0], "Thigh_L": [-60, 0, 0], "Shin_L": [84, 0, 0], "Foot_L": [14, 0, 0], "vfx": {"fx_dust": {"pos": [256, 388], "rot": 0, "scale": 0.85, "alpha": 0.82}}},
                {"t": 0.68, "Hip": [-2, 64, 40], "Chest": [28, 0, 0], "Neck": [0, 0, 0], "Head": [22, 0, 0], "UpperArm_R": [42, 0, 0], "Forearm_R": [20, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-40, 0, 0], "Forearm_L": [-20, 0, 0], "Hand_L": [-24, 0, 0], "Weapon_Front": [-32, 0, 0], "Thigh_R": [-76, 0, 0], "Shin_R": [100, 0, 0], "Foot_R": [18, 0, 0], "Thigh_L": [-70, 0, 0], "Shin_L": [94, 0, 0], "Foot_L": [16, 0, 0], "vfx": {"fx_dust": {"pos": [264, 390], "rot": 0, "scale": 0.9, "alpha": 0.65}}, "modulate_a": 0.88},
                {"t": 0.88, "Hip": [0, 68, 44], "Chest": [30, 0, 0], "Neck": [0, 0, 0], "Head": [24, 0, 0], "UpperArm_R": [44, 0, 0], "Forearm_R": [22, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-42, 0, 0], "Forearm_L": [-22, 0, 0], "Hand_L": [-26, 0, 0], "Weapon_Front": [-34, 0, 0], "Thigh_R": [-78, 0, 0], "Shin_R": [102, 0, 0], "Foot_R": [18, 0, 0], "Thigh_L": [-72, 0, 0], "Shin_L": [96, 0, 0], "Foot_L": [16, 0, 0], "vfx": {"fx_dust": {"pos": [266, 390], "rot": 0, "scale": 0.75, "alpha": 0.45}}, "modulate_a": 0.52},
                {"t": 1.05, "Hip": [0, 70, 46], "Chest": [30, 0, 0], "Neck": [0, 0, 0], "Head": [24, 0, 0], "UpperArm_R": [44, 0, 0], "Forearm_R": [22, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-42, 0, 0], "Forearm_L": [-22, 0, 0], "Hand_L": [-26, 0, 0], "Weapon_Front": [-34, 0, 0], "Thigh_R": [-78, 0, 0], "Shin_R": [102, 0, 0], "Foot_R": [18, 0, 0], "Thigh_L": [-72, 0, 0], "Shin_L": [96, 0, 0], "Foot_L": [16, 0, 0], "modulate_a": 0.22},
            ],
        },
    }
}
# Alias other archetypes to melee_cleaver or customized variants
for arch in ["melee_sword", "melee_spear", "ranged_crossbow", "magic_staff", "dual_blades"]:
    ARCHETYPE_ACTIONS[arch] = json.loads(json.dumps(ARCHETYPE_ACTIONS["melee_cleaver"]))


# ==============================================================================
# 2. MUSE API & IMAGE PROCESSING HELPERS
# ==============================================================================
def muse_post(endpoint: str, payload: dict, timeout: int = 240) -> dict:
    url = f"{MUSE_BASE}{endpoint}"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def unmix_magenta_rgba(raw_img: Image.Image) -> Image.Image:
    rgba = raw_img.convert("RGBA")
    w, h = rgba.size
    px = rgba.load()
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    opx = out.load()
    margin_x = max(8, int(w * 0.025))
    margin_y = max(8, int(h * 0.025))
    for y in range(margin_y, h - margin_y):
        for x in range(margin_x, w - margin_x):
            r, g, b, a = px[x, y]
            if a < 16:
                continue
            # Distance from pure #FF00FF
            mr = 255 - r
            mg = g
            mb = 255 - b
            dist = math.sqrt(mr * mr + mg * mg + mb * mb)
            mag_excess = (r + b) / 2.0 - g
            if dist < 58 or (mag_excess > 95 and g < 85):
                continue
            alpha = 255
            if dist < 95:
                alpha = int(max(0, min(255, (dist - 58) / 37.0 * 255)))
            # Despill magenta fringe on semi-transparent border pixels
            if mag_excess > 45 and alpha < 245:
                r = int(max(0, min(255, r - mag_excess * 0.35)))
                b = int(max(0, min(255, b - mag_excess * 0.35)))
            opx[x, y] = (r, g, b, alpha)
    return out


def keep_largest_component_and_crop(img: Image.Image, pad: int = 0) -> Image.Image:
    w, h = img.size
    px = img.load()
    visited = [[False] * w for _ in range(h)]
    comps = []
    for y in range(h):
        for x in range(w):
            if px[x, y][3] > 20 and not visited[y][x]:
                q = deque([(x, y)])
                visited[y][x] = True
                pts = []
                while q:
                    cx, cy = q.popleft()
                    pts.append((cx, cy))
                    for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                        if 0 <= nx < w and 0 <= ny < h and not visited[ny][nx] and px[nx, ny][3] > 20:
                            visited[ny][nx] = True
                            q.append((nx, ny))
                comps.append(pts)
    if not comps:
        return img
    comps.sort(key=len, reverse=True)
    keep = set(comps[0])
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    opx = out.load()
    min_x, min_y, max_x, max_y = w, h, 0, 0
    for cx, cy in keep:
        opx[cx, cy] = px[cx, cy]
        if cx < min_x: min_x = cx
        if cy < min_y: min_y = cy
        if cx > max_x: max_x = cx
        if cy > max_y: max_y = cy
    cropped = out.crop((min_x, min_y, max_x + 1, max_y + 1))
    if pad > 0:
        padded = Image.new("RGBA", (cropped.width + pad * 2, cropped.height + pad * 2), (0, 0, 0, 0))
        padded.paste(cropped, (pad, pad))
        return padded
    return cropped


def b64_uri(path: pathlib.Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


# ==============================================================================
# 3. ANATOMICAL 17-BONE STICKMAN RIG & RENDERER
# ==============================================================================
def build_anatomical_bones(w_main: Image.Image, w_offhand: Image.Image, cfg: dict) -> list:
    part_dims = {}
    for p in ["hip_kilt", "leg_thigh_back", "leg_shin_back", "foot_back", "leg_thigh_front", "leg_shin_front", "foot_front", "chest", "neck", "head", "arm_upper_back", "arm_lower_back", "hand_back", "arm_upper_front", "arm_lower_front", "hand_front"]:
        with Image.open(STICKER_DIR / "team_blue" / f"{p}.png") as im:
            part_dims[p] = im.size
    part_dims["weapon_main"] = w_main.size
    part_dims["weapon_offhand"] = w_offhand.size

    def mb(name, parent, part, rx, ry, rrot, px, py, z, tip_child=None, tip_offset=None, is_weapon=False, vis=True, g1=None, g2=None):
        w, h = part_dims[part]
        d = {
            "name": name, "parent": parent, "part": part, "is_weapon": is_weapon, "visible_default": vis,
            "rest_x": round(float(rx), 2), "rest_y": round(float(ry), 2), "rest_rot": round(float(rrot), 2),
            "pivot_x": round(float(px), 2), "pivot_y": round(float(py), 2), "z_index": z,
            "width": w, "height": h, "offset_x": round(w / 2.0 - px, 2), "offset_y": round(h / 2.0 - py, 2),
        }
        if tip_child: d["tip_child"] = tip_child
        if tip_offset: d["tip_offset"] = [round(float(tip_offset[0]), 2), round(float(tip_offset[1]), 2)]
        if g1: d["grip1_x"], d["grip1_y"] = round(float(g1[0]), 2), round(float(g1[1]), 2)
        if g2: d["grip2_x"], d["grip2_y"] = round(float(g2[0]), 2), round(float(g2[1]), 2)
        return d

    g1 = cfg.get("grip1", [round(w_main.width * 0.35, 1), round(w_main.height * 0.72, 1)])
    g2 = cfg.get("grip2", [round(w_main.width * 0.14, 1), round(w_main.height * 0.86, 1)])
    og1 = cfg.get("offhand_grip1", [round(w_offhand.width * 0.22, 1), round(w_offhand.height * 0.55, 1)])
    og2 = cfg.get("offhand_grip2", [round(w_offhand.width * 0.12, 1), round(w_offhand.height * 0.65, 1)])
    w_rot = cfg.get("rest_rot", 14.0)

    return [
        mb("Hip", None, "hip_kilt", 198, 258, 0, part_dims["hip_kilt"][0]/2, part_dims["hip_kilt"][1]*0.35, 7, tip_child="Chest"),
        mb("Thigh_L", "Hip", "leg_thigh_back", 8, 14, -22, part_dims["leg_thigh_back"][0]/2, 11, 1, tip_child="Shin_L"),
        mb("Shin_L", "Thigh_L", "leg_shin_back", 0, part_dims["leg_thigh_back"][1]-22, 16, part_dims["leg_shin_back"][0]/2, 10.5, 2, tip_child="Foot_L"),
        mb("Foot_L", "Shin_L", "foot_back", 0, part_dims["leg_shin_back"][1]-21, 6, part_dims["foot_back"][0]*0.29, 9, 3, tip_offset=[36, 18]),
        mb("Thigh_R", "Hip", "leg_thigh_front", -8, 14, 22, part_dims["leg_thigh_front"][0]/2, 11.5, 4, tip_child="Shin_R"),
        mb("Shin_R", "Thigh_R", "leg_shin_front", 0, part_dims["leg_thigh_front"][1]-23, -14, part_dims["leg_shin_front"][0]/2, 11, 5, tip_child="Foot_R"),
        mb("Foot_R", "Shin_R", "foot_front", 0, part_dims["leg_shin_front"][1]-22, -8, part_dims["foot_front"][0]*0.29, 9, 6, tip_offset=[38, 18]),
        mb("Chest", "Hip", "chest", 0, -4, 3, part_dims["chest"][0]/2, part_dims["chest"][1]-10, 8, tip_child="Neck"),
        mb("Neck", "Chest", "neck", 0, -(part_dims["chest"][1]-22), 0, part_dims["neck"][0]/2, part_dims["neck"][1]-7, 7, tip_child="Head"),
        mb("Head", "Neck", "head", 0, -(part_dims["neck"][1]-14), -3, part_dims["head"][0]/2, part_dims["head"][1]-10, 11, tip_offset=[0, -76]),
        mb("UpperArm_R", "Chest", "arm_upper_back", 10, -(part_dims["chest"][1]-26), -26, part_dims["arm_upper_back"][0]/2, 10.5, 6, tip_child="Forearm_R"),
        mb("Forearm_R", "UpperArm_R", "arm_lower_back", 0, part_dims["arm_upper_back"][1]-21, -38, part_dims["arm_lower_back"][0]/2, 10, 9, tip_child="Hand_R"),
        mb("Hand_R", "Forearm_R", "hand_back", 0, part_dims["arm_lower_back"][1]-20, 0, part_dims["hand_back"][0]*0.48, 5, 10, tip_child="Weapon_Back"),
        mb("Weapon_Back", "Hand_R", "weapon_offhand", 0, part_dims["hand_back"][1]*0.58, 22, og1[0], og1[1], 9, tip_offset=[115, 0], is_weapon=True, vis=False, g1=og1, g2=og2),
        mb("UpperArm_L", "Chest", "arm_upper_front", -8, -(part_dims["chest"][1]-26), 14, part_dims["arm_upper_front"][0]/2, 11, 12, tip_child="Forearm_L"),
        mb("Forearm_L", "UpperArm_L", "arm_lower_front", 0, part_dims["arm_upper_front"][1]-22, -52, part_dims["arm_lower_front"][0]/2, 10, 13, tip_child="Hand_L"),
        mb("Hand_L", "Forearm_L", "hand_front", 0, part_dims["arm_lower_front"][1]-20, 0, part_dims["hand_front"][0]*0.48, 5, 15, tip_child="Weapon_Front"),
        mb("Weapon_Front", "Hand_L", "weapon_main", 0, part_dims["hand_front"][1]*0.58, w_rot, g1[0], g1[1], 14, tip_offset=[135, -95], is_weapon=True, vis=True, g1=g1, g2=g2),
    ]


def compute_world_transforms(bones: list, frame_pose: dict) -> dict:
    world = {}
    for b in bones:
        name = b["name"]
        parent = b["parent"]
        val = frame_pose.get(name, [0.0, 0.0, 0.0])
        if name == "Hip":
            dx, dy, drot = val[0], val[1], val[2]
        else:
            drot, dx, dy = val[0], val[1], val[2]
        lx = b["rest_x"] + dx
        ly = b["rest_y"] + dy
        lrot = b["rest_rot"] + drot
        if parent is None:
            wx, wy, wrot = lx, ly, lrot
        else:
            p = world[parent]
            rad = math.radians(p["wrot"])
            ca, sa = math.cos(rad), math.sin(rad)
            wx = p["wx"] + lx * ca - ly * sa
            wy = p["wy"] + lx * sa + ly * ca
            wrot = p["wrot"] + lrot
        world[name] = {"wx": wx, "wy": wy, "wrot": wrot}
    return world


def paste_rotated_rgba(canvas: Image.Image, part_img: Image.Image, wx: float, wy: float, pivot_x: float, pivot_y: float, angle_deg: float, alpha_mult: float = 1.0):
    if alpha_mult <= 0.01:
        return
    src = part_img.convert("RGBA")
    if alpha_mult < 0.999:
        r, g, b, a = src.split()
        a = a.point(lambda p: int(p * alpha_mult))
        src = Image.merge("RGBA", (r, g, b, a))
    w, h = src.size
    diag = int(math.ceil(math.hypot(w, h) * 2.2)) + 8
    if diag % 2 == 1:
        diag += 1
    half = diag // 2
    pad_im = Image.new("RGBA", (diag, diag), (0, 0, 0, 0))
    pad_im.paste(src, (int(round(half - pivot_x)), int(round(half - pivot_y))))
    rot_im = pad_im.rotate(-angle_deg, resample=Image.Resampling.BICUBIC, expand=False)
    canvas.alpha_composite(rot_im, (int(round(wx - half)), int(round(wy - half))))


def render_pose_cell(bones: list, frame_pose: dict, team_key: str, weapon_parts: dict, dual_wield: bool = False, anim_frame_idx: int = 0) -> Image.Image:
    canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    world = compute_world_transforms(bones, frame_pose)
    mod_a = float(frame_pose.get("modulate_a", 1.0))
    sorted_bones = sorted(bones, key=lambda b: b["z_index"])
    for b in sorted_bones:
        bname = b["name"]
        if bname == "Weapon_Back" and not dual_wield:
            continue
        tr = world[bname]
        if b["is_weapon"]:
            if bname == "Weapon_Front":
                anim_key = f"weapon_anim_{anim_frame_idx % 4}"
                p_img = weapon_parts.get(anim_key, weapon_parts["weapon_main"])
            else:
                p_img = weapon_parts["weapon_offhand"]
        else:
            p_img = Image.open(STICKER_DIR / team_key / f"{b['part']}.png").convert("RGBA")
        paste_rotated_rgba(canvas, p_img, tr["wx"], tr["wy"], b["pivot_x"], b["pivot_y"], tr["wrot"], mod_a)

    for vname, vcfg in frame_pose.get("vfx", {}).items():
        if vname in weapon_parts:
            vimg = weapon_parts[vname]
            sc = float(vcfg.get("scale", 1.0))
            if abs(sc - 1.0) > 0.01:
                vimg = vimg.resize((max(1, int(vimg.width * sc)), max(1, int(vimg.height * sc))), Image.Resampling.LANCZOS)
            paste_rotated_rgba(canvas, vimg, vcfg["pos"][0], vcfg["pos"][1], vimg.width / 2.0, vimg.height / 2.0, float(vcfg.get("rot", 0.0)), float(vcfg.get("alpha", 1.0)))
    return canvas


def build_qc_boards(cfg: dict, bones: list, actions: dict, weapon_dir: pathlib.Path, weapon_parts: dict, card_img: Image.Image):
    qc_dir = weapon_dir / "qc_previews"
    qc_dir.mkdir(parents=True, exist_ok=True)
    wid = cfg["id"].upper()
    tier = cfg.get("tier", "N").upper()
    is_animated = tier in ("S", "SSR") and "weapon_anim_1" in weapon_parts

    # 1. Weapon & Team Audit Board
    audit = Image.new("RGBA", (1920, 1020), (13, 17, 23, 255))
    ad = ImageDraw.Draw(audit)
    team_meta = [
        ("team_blue", f"ĐỘI 1: XANH + {wid}", (59, 130, 246), False),
        ("team_red", f"ĐỘI 2: ĐỎ + SONG VŨ KHÍ {wid}", (239, 68, 68), True),
        ("team_green", f"ĐỘI 3: XANH LÁ + {wid}", (34, 197, 94), False),
        ("team_amber", f"ĐỘI 4: VÀNG CAM + {wid}", (245, 158, 11), False),
    ]
    for idx, (tkey, title, col, dw) in enumerate(team_meta):
        x0, y0 = 16 + idx * 356, 16
        ad.rectangle([x0, y0, x0 + 344, y0 + 476], fill=(22, 27, 36, 255), outline=col, width=2)
        ad.text((x0 + 14, y0 + 10), title, fill=col)
        ad.text((x0 + 14, y0 + 28), f"Cấp {tier} — {'Animated 2x2' if is_animated else '1 Ảnh Tĩnh (weapon_anim_0)'} | edge_clip=0px", fill=(180, 190, 205))
        cell = render_pose_cell(bones, actions["idle"]["frames"][0], tkey, weapon_parts, dual_wield=dw, anim_frame_idx=idx)
        cell_sm = cell.resize((330, 330), Image.Resampling.LANCZOS)
        audit.alpha_composite(cell_sm, (x0 + 7, y0 + 96))

    # Card Preview Box
    cx0, cy0 = 1440, 16
    ad.rectangle([cx0, cy0, cx0 + 464, cy0 + 476], fill=(22, 27, 36, 255), outline=(245, 158, 11), width=2)
    ad.text((cx0 + 14, cy0 + 12), "ẢNH BÌA CARD (884x632 RGB — 100% Opaque)", fill=(245, 158, 11))
    card_sm = card_img.resize((444, 318), Image.Resampling.LANCZOS).convert("RGBA")
    audit.alpha_composite(card_sm, (cx0 + 10, cy0 + 50))
    ad.rectangle([cx0 + 10, cy0 + 50, cx0 + 454, cy0 + 368], outline=(245, 158, 11), width=1)
    wf = next(b for b in bones if b["name"] == "Weapon_Front")
    ad.text((cx0 + 14, cy0 + 382), f"884x632 RGB PNG & 354x253 WebP (100% Opaque!)", fill=(250, 204, 21))
    ad.text((cx0 + 14, cy0 + 406), f"Grip 1: ({wf['grip1_x']}, {wf['grip1_y']}) | Grip 2: ({wf['grip2_x']}, {wf['grip2_y']})", fill=(200, 210, 225))
    ad.text((cx0 + 14, cy0 + 430), f"Tier {tier}: {'3-Step Animated Flow' if is_animated else '2-Step Static Weapon Flow'}", fill=(134, 239, 172))

    # Bottom row: Weapon + VFX
    bx0, by0 = 16, 508
    ad.rectangle([bx0, by0, bx0 + 450, by0 + 496], fill=(22, 27, 36, 255), outline=(245, 158, 11), width=2)
    w_main = weapon_parts["weapon_main"]
    w_off = weapon_parts["weapon_offhand"]
    ad.text((bx0 + 14, by0 + 12), f"VŨ KHÍ CẤP {tier} ({w_main.width}x{w_main.height} — 0px Pad)", fill=(245, 158, 11))
    ad.text((bx0 + 14, by0 + 32), f"{'4-Frame Animated (weapon_anim_0..3)' if is_animated else 'weapon_main.png = weapon_anim_0.png (Tĩnh)'}", fill=(134, 239, 172))
    wx, wy = bx0 + (450 - w_main.width) // 2, by0 + 84
    audit.alpha_composite(w_main, (wx, wy))
    ad.rectangle([wx, wy, wx + w_main.width, wy + w_main.height], outline=(134, 239, 172), width=1)
    g1x, g1y = wx + int(wf["grip1_x"]), wy + int(wf["grip1_y"])
    g2x, g2y = wx + int(wf["grip2_x"]), wy + int(wf["grip2_y"])
    ad.ellipse([g1x - 6, g1y - 6, g1x + 6, g1y + 6], fill=(239, 68, 68), outline=(255, 255, 255), width=2)
    ad.ellipse([g2x - 6, g2y - 6, g2x + 6, g2y + 6], fill=(56, 189, 248), outline=(255, 255, 255), width=2)
    ad.text((bx0 + 14, by0 + 305), f"Vũ khí phụ (weapon_offhand.png — {w_off.width}x{w_off.height}):", fill=(250, 204, 21))
    audit.alpha_composite(w_off, (bx0 + (450 - w_off.width) // 2, by0 + 340))

    for idx, fkey in enumerate(VFX_NAMES):
        fx0, fy0 = 484 + idx * 355, 508
        ad.rectangle([fx0, fy0, fx0 + 342, fy0 + 496], fill=(22, 27, 36, 255), outline=(56, 189, 248), width=1)
        fimg = weapon_parts[fkey]
        ad.text((fx0 + 14, fy0 + 12), f"VFX {idx+1}: {fkey}.png ({fimg.width}x{fimg.height})", fill=(250, 204, 21))
        audit.alpha_composite(fimg, (fx0 + (342 - fimg.width) // 2, fy0 + (496 - fimg.height) // 2 + 20))

    audit_path = qc_dir / f"{cfg['id']}_weapon_and_aura_audit.png"
    audit.save(audit_path)

    # 2. All 6 Actions Overview Board
    overview = Image.new("RGBA", (1920, 1300), (13, 17, 23, 255))
    od = ImageDraw.Draw(overview)
    act_order = [
        ("idle", "1: IDLE", "team_blue"),
        ("walk", "2: WALK", "team_red"),
        ("attack", "3: ATTACK", "team_green"),
        ("cast", "4: CAST", "team_amber"),
        ("hurt", "5: HURT", "team_blue"),
        ("death", "6: DEATH", "team_red"),
    ]
    for idx, (act_key, act_label, tkey) in enumerate(act_order):
        col_i, row_i = idx % 3, idx // 3
        bx, by = 16 + col_i * 632, 16 + row_i * 638
        od.rectangle([bx, by, bx + 616, by + 622], fill=(22, 27, 36, 255), outline=(245, 158, 11), width=1)
        act = actions[act_key]
        rows, cols = act["grid"]
        frames = act["frames"]
        od.text((bx + 14, by + 12), f"{wid} Action {act_label} ({tkey} | {len(frames)}f | Cấp {tier})", fill=(250, 204, 21))
        cell_draw_sz = 270 if cols == 2 else 188
        gx0 = bx + (616 - cols * cell_draw_sz) // 2
        gy0 = by + 48 + (560 - rows * cell_draw_sz) // 2
        for fi, fpose in enumerate(frames):
            r, c = fi // cols, fi % cols
            cell_im = render_pose_cell(bones, fpose, tkey, weapon_parts, dual_wield=False, anim_frame_idx=fi)
            cell_sm = cell_im.resize((cell_draw_sz, cell_draw_sz), Image.Resampling.LANCZOS)
            cx, cy = gx0 + c * cell_draw_sz, gy0 + r * cell_draw_sz
            od.rectangle([cx, cy, cx + cell_draw_sz, cy + cell_draw_sz], fill=(28, 34, 46, 255), outline=(75, 85, 99), width=1)
            overview.alpha_composite(cell_sm, (cx, cy))

    overview_path = qc_dir / f"{cfg['id']}_sticker_all_6_actions_overview.png"
    overview.save(overview_path)
    return audit_path, overview_path


# ==============================================================================
# 4. GODOT 4 (.TSCN & .GD) BUILDER
# ==============================================================================
def build_godot_files(cfg: dict, bones: list, actions: dict, weapon_dir: pathlib.Path):
    godot_dir = weapon_dir / "godot"
    godot_dir.mkdir(parents=True, exist_ok=True)
    slug = cfg["slug"]
    tscn_name = cfg["tscn_name"]
    gd_name = tscn_name.replace(".tscn", ".gd")
    node_name = cfg["node_name"]
    tier = cfg.get("tier", "N").upper()
    is_animated = tier in ("S", "SSR")
    bone_map = {b["name"]: b for b in bones}

    ext_list = [("1_script", "Script", f"res://assets/weapons/{slug}/godot/{gd_name}")]
    part_ext_id = {}
    idx = 2
    for b in bones:
        p = b["part"]
        if p not in part_ext_id:
            part_ext_id[p] = f"{idx}_{p}"
            if b["is_weapon"]:
                ext_list.append((part_ext_id[p], "Texture2D", f"res://assets/weapons/{slug}/parts/{p}.png"))
            else:
                ext_list.append((part_ext_id[p], "Texture2D", f"res://assets/sticker_hero/godot/parts/team_blue/{p}.png"))
            idx += 1
    for fx in VFX_NAMES:
        part_ext_id[fx] = f"{idx}_{fx}"
        ext_list.append((part_ext_id[fx], "Texture2D", f"res://assets/weapons/{slug}/parts/{fx}.png"))
        idx += 1

    bone_paths = {}
    for b in bones:
        bname = b["name"]
        bone_paths[bname] = f"Skeleton2D/{bname}" if b["parent"] is None else f"{bone_paths[b['parent']]}/{bname}"

    lines = [f'[gd_scene load_steps={len(ext_list) + 8} format=3]', ""]
    for eid, etype, epath in ext_list:
        lines.append(f'[ext_resource type="{etype}" path="{epath}" id="{eid}"]')
    lines.append("")

    for act_name, act in actions.items():
        lines.append(f'[sub_resource type="Animation" id="Animation_{act_name}"]')
        lines.append(f'resource_name = "{act_name}"')
        lines.append(f'length = {act["length"]}')
        lines.append(f'loop_mode = {1 if act["loop"] else 0}')
        frames = act["frames"]
        t_str = ", ".join(f'{f["t"]:.2f}' for f in frames)
        trans_str = ", ".join("1" for _ in frames)
        ti = 0
        for b in bones:
            bname = b["name"]
            bpath = bone_paths[bname]
            p_vals, r_vals = [], []
            for f in frames:
                val = f.get(bname, [0.0, 0.0, 0.0])
                if bname == "Hip":
                    dx, dy, drot = val[0], val[1], val[2]
                else:
                    drot, dx, dy = val[0], val[1], val[2]
                p_vals.append(f"Vector2({b['rest_x'] + dx:.1f}, {b['rest_y'] + dy:.1f})")
                r_vals.append(f"{math.radians(b['rest_rot'] + drot):.4f}")
            lines.append(f'tracks/{ti}/type = "value"')
            lines.append(f'tracks/{ti}/imported = false')
            lines.append(f'tracks/{ti}/enabled = true')
            lines.append(f'tracks/{ti}/path = NodePath("{bpath}:position")')
            lines.append(f'tracks/{ti}/interp = 1')
            lines.append(f'tracks/{ti}/loop_wrap = true')
            lines.append(f'tracks/{ti}/keys = {{"times": PackedFloat32Array({t_str}), "transitions": PackedFloat32Array({trans_str}), "update": 0, "values": [{", ".join(p_vals)}]}}')
            ti += 1
            lines.append(f'tracks/{ti}/type = "value"')
            lines.append(f'tracks/{ti}/imported = false')
            lines.append(f'tracks/{ti}/enabled = true')
            lines.append(f'tracks/{ti}/path = NodePath("{bpath}:rotation")')
            lines.append(f'tracks/{ti}/interp = 1')
            lines.append(f'tracks/{ti}/loop_wrap = true')
            lines.append(f'tracks/{ti}/keys = {{"times": PackedFloat32Array({t_str}), "transitions": PackedFloat32Array({trans_str}), "update": 0, "values": [{", ".join(r_vals)}]}}')
            ti += 1
        lines.append("")

    lines.append('[sub_resource type="AnimationLibrary" id="AnimationLibrary_main"]')
    lines.append('_data = {')
    for act_name in actions:
        lines.append(f'"{act_name}": SubResource("Animation_{act_name}"),')
    lines.append('}')
    lines.append("")

    lines.append(f'[node name="{node_name}" type="Node2D"]')
    lines.append('script = ExtResource("1_script")')
    lines.append("")
    lines.append('[node name="Skeleton2D" type="Skeleton2D" parent="."]')
    lines.append("")

    for b in bones:
        bname = b["name"]
        parent_path = "Skeleton2D" if b["parent"] is None else bone_paths[b["parent"]]
        rad = math.radians(b["rest_rot"])
        ca, sa = math.cos(rad), math.sin(rad)
        if "tip_child" in b and b["tip_child"] in bone_map:
            tx, ty = bone_map[b["tip_child"]]["rest_x"], bone_map[b["tip_child"]]["rest_y"]
        else:
            tx, ty = b.get("tip_offset", [0.0, 42.0])
        blen = max(8.0, math.hypot(tx, ty))
        bang = math.atan2(ty, tx)
        lines.append(f'[node name="{bname}" type="Bone2D" parent="{parent_path}"]')
        lines.append(f'position = Vector2({b["rest_x"]:.1f}, {b["rest_y"]:.1f})')
        lines.append(f'rotation = {rad:.4f}')
        lines.append(f'rest = Transform2D({ca:.4f}, {sa:.4f}, {-sa:.4f}, {ca:.4f}, {b["rest_x"]:.1f}, {b["rest_y"]:.1f})')
        lines.append('auto_calculate_length_and_angle = false')
        lines.append(f'length = {blen:.1f}')
        lines.append(f'bone_angle = {bang:.4f}')
        if b["is_weapon"]:
            lines.append(f'metadata/grip1 = Vector2({b["grip1_x"]:.1f}, {b["grip1_y"]:.1f})')
            lines.append(f'metadata/grip2 = Vector2({b["grip2_x"]:.1f}, {b["grip2_y"]:.1f})')
        lines.append("")
        lines.append(f'[node name="Sprite" type="Sprite2D" parent="{bone_paths[bname]}"]')
        if not b.get("visible_default", True):
            lines.append('visible = false')
        lines.append(f'z_index = {b["z_index"]}')
        lines.append('z_as_relative = false')
        lines.append(f'texture = ExtResource("{part_ext_id[b["part"]]}")')
        lines.append(f'offset = Vector2({b["offset_x"]:.2f}, {b["offset_y"]:.2f})')
        lines.append("")

    lines.append('[node name="VFXLayer" type="Node2D" parent="."]')
    lines.append('z_index = 20')
    lines.append('z_as_relative = false')
    lines.append("")
    for fx in VFX_NAMES:
        lines.append(f'[node name="{fx}" type="Sprite2D" parent="VFXLayer"]')
        lines.append('visible = false')
        lines.append('position = Vector2(256, 256)')
        lines.append(f'texture = ExtResource("{part_ext_id[fx]}")')
        lines.append("")

    lines.append('[node name="AnimationPlayer" type="AnimationPlayer" parent="."]')
    lines.append('libraries = {')
    lines.append('"": SubResource("AnimationLibrary_main")')
    lines.append('}')
    lines.append('autoplay = "idle"')
    lines.append("")

    tscn_path = godot_dir / tscn_name
    tscn_path.write_text("\n".join(lines), encoding="utf-8")

    gd_code = f'''extends Node2D
class_name {node_name}

@export_enum("team_blue", "team_red", "team_green", "team_amber") var team_color: String = "team_blue":
\tset(value):
\t\tteam_color = value
\t\tif is_node_ready():
\t\t\tapply_team_color(value)

@export_range(1, 2) var active_grip_slot: int = 1:
\tset(value):
\t\tactive_grip_slot = value
\t\tif is_node_ready():
\t\t\tapply_weapon_grip(value)

@export var dual_wield_enabled: bool = false:
\tset(value):
\t\tdual_wield_enabled = value
\t\tif is_node_ready() and has_node("Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Hand_R/Weapon_Back/Sprite"):
\t\t\t$"Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Hand_R/Weapon_Back/Sprite".visible = value

const STICKER_BONE_PARTS := {{
\t"Skeleton2D/Hip/Sprite": "hip_kilt",
\t"Skeleton2D/Hip/Thigh_L/Sprite": "leg_thigh_back",
\t"Skeleton2D/Hip/Thigh_L/Shin_L/Sprite": "leg_shin_back",
\t"Skeleton2D/Hip/Thigh_L/Shin_L/Foot_L/Sprite": "foot_back",
\t"Skeleton2D/Hip/Thigh_R/Sprite": "leg_thigh_front",
\t"Skeleton2D/Hip/Thigh_R/Shin_R/Sprite": "leg_shin_front",
\t"Skeleton2D/Hip/Thigh_R/Shin_R/Foot_R/Sprite": "foot_front",
\t"Skeleton2D/Hip/Chest/Sprite": "chest",
\t"Skeleton2D/Hip/Chest/Neck/Sprite": "neck",
\t"Skeleton2D/Hip/Chest/Neck/Head/Sprite": "head",
\t"Skeleton2D/Hip/Chest/UpperArm_R/Sprite": "arm_upper_back",
\t"Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Sprite": "arm_lower_back",
\t"Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Hand_R/Sprite": "hand_back",
\t"Skeleton2D/Hip/Chest/UpperArm_L/Sprite": "arm_upper_front",
\t"Skeleton2D/Hip/Chest/UpperArm_L/Forearm_L/Sprite": "arm_lower_front",
\t"Skeleton2D/Hip/Chest/UpperArm_L/Forearm_L/Hand_L/Sprite": "hand_front",
}}

func _ready() -> void:
\tapply_team_color(team_color)
\tapply_weapon_grip(active_grip_slot)
\tdual_wield_enabled = dual_wield_enabled

func apply_team_color(t_color: String) -> void:
\tfor node_path in STICKER_BONE_PARTS.keys():
\t\tif has_node(node_path):
\t\t\tvar spr: Sprite2D = get_node(node_path)
\t\t\tvar part_name: String = STICKER_BONE_PARTS[node_path]
\t\t\tvar tex_path := "res://assets/sticker_hero/godot/parts/%s/%s.png" % [t_color, part_name]
\t\t\tif ResourceLoader.exists(tex_path):
\t\t\t\tspr.texture = load(tex_path)

func apply_weapon_grip(slot: int) -> void:
\tvar w_bone_path := "Skeleton2D/Hip/Chest/UpperArm_L/Forearm_L/Hand_L/Weapon_Front"
\tif not has_node(w_bone_path):
\t\treturn
\tvar w_bone: Bone2D = get_node(w_bone_path)
\tvar w_spr: Sprite2D = w_bone.get_node("Sprite")
\tvar grip: Vector2 = w_bone.get_meta("grip1") if slot == 1 else w_bone.get_meta("grip2")
\tif w_spr.texture:
\t\tvar sz := w_spr.texture.get_size()
\t\tw_spr.offset = Vector2(sz.x / 2.0 - grip.x, sz.y / 2.0 - grip.y)
'''
    gd_path = godot_dir / gd_name
    gd_path.write_text(gd_code, encoding="utf-8")
    return tscn_path, gd_path


# ==============================================================================
# 5. EXTERNALIZED `weapons_data.js` & LIGHTWEIGHT (~22 KB) HTML EDITORS
# ==============================================================================
def build_team_part_b64() -> dict:
    part_names = [
        "hip_kilt", "leg_thigh_back", "leg_shin_back", "foot_back",
        "leg_thigh_front", "leg_shin_front", "foot_front", "chest",
        "neck", "head", "arm_upper_back", "arm_lower_back", "hand_back",
        "arm_upper_front", "arm_lower_front", "hand_front",
    ]
    out = {}
    for t in TEAMS:
        out[t] = {}
        for p in part_names:
            out[t][p] = b64_uri(STICKER_DIR / t / f"{p}.png")
    return out


def load_weapons_registry() -> tuple[dict, list]:
    if WEAPONS_DATA_JS.exists():
        txt = WEAPONS_DATA_JS.read_text(encoding="utf-8")
        reg_marker = "window.WEAPON_REGISTRY = "
        ord_marker = "window.WEAPON_ORDER = "
        if reg_marker in txt and ord_marker in txt:
            try:
                r_start = txt.index(reg_marker) + len(reg_marker)
                r_end = txt.index(";\nwindow.WEAPON_ORDER = ")
                reg = json.loads(txt[r_start:r_end])
                o_start = txt.index(ord_marker) + len(ord_marker)
                o_end = txt.rindex(";")
                order = json.loads(txt[o_start:o_end])
                return reg, order
            except Exception:
                pass
    return {}, []


def save_weapons_data_js(registry: dict, order: list):
    team_b64 = build_team_part_b64()
    js_lines = [
        "// Auto-generated by tools/forge_weapon.py — DO NOT READ OR EDIT MANUALLY IN AI CONTEXT",
        f"window.TEAM_PART_B64 = {json.dumps(team_b64, ensure_ascii=True)};",
        f"window.WEAPON_REGISTRY = {json.dumps(registry, ensure_ascii=True)};",
        f"window.WEAPON_ORDER = {json.dumps(order, ensure_ascii=True)};",
        "",
    ]
    WEAPONS_DATA_JS.write_text("\n".join(js_lines), encoding="utf-8")


def render_lightweight_editor_html(data_js_rel_path: str, default_weapon_id: str) -> str:
    return f'''<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Card_G — Stickman 4 Đội + Hệ Thống Vũ Khí Thẻ Bài (Token-Optimized Editor)</title>
<style>
  :root {{
    --bg: #0d1117;
    --panel: #161b22;
    --border: #30363d;
    --text: #e6edf3;
    --muted: #8b949e;
    --accent: #f59e0b;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    display: flex;
    flex-direction: column;
    height: 100vh;
    overflow: hidden;
  }}
  header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 16px;
    background: var(--panel);
    border-bottom: 1px solid var(--border);
    gap: 10px;
    flex-wrap: wrap;
  }}
  .brand {{ display: flex; align-items: center; gap: 10px; }}
  .badge {{
    background: rgba(245, 158, 11, 0.16);
    color: var(--accent);
    border: 1px solid var(--accent);
    font-size: 11px;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 999px;
  }}
  .team-bar, .action-bar, .tool-bar {{ display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }}
  button, select {{
    background: #21262d;
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 6px 11px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: 0.15s;
  }}
  button:hover, select:hover {{ border-color: #58a6ff; }}
  button.active {{ background: #1f6feb; border-color: #58a6ff; color: #fff; }}
  button.primary {{ background: #238636; border-color: #2ea043; color: #fff; }}
  .team-btn {{ display: inline-flex; align-items: center; gap: 6px; }}
  .dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; }}
  main {{
    flex: 1;
    display: grid;
    grid-template-columns: 330px 1fr 340px;
    overflow: hidden;
  }}
  .sidebar {{
    background: var(--panel);
    border-right: 1px solid var(--border);
    padding: 12px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }}
  .sidebar.right {{ border-right: none; border-left: 1px solid var(--border); }}
  h3 {{
    margin: 0;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: var(--accent);
  }}
  .card-box {{
    background: #0d1117;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }}
  .card-preview-img {{
    width: 100%;
    aspect-ratio: 884 / 632;
    object-fit: cover;
    border-radius: 6px;
    border: 1px solid var(--accent);
    background: #000;
  }}
  .bone-list {{
    display: flex;
    flex-direction: column;
    gap: 4px;
    max-height: 280px;
    overflow-y: auto;
  }}
  .bone-item {{
    padding: 6px 8px;
    border-radius: 6px;
    background: #0d1117;
    border: 1px solid transparent;
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    font-size: 12px;
  }}
  .bone-item.selected {{ border-color: var(--accent); background: rgba(245, 158, 11, 0.12); }}
  .viewport {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    position: relative;
    background: radial-gradient(circle at center, #1b2230 0%, #0d1117 75%);
    padding: 12px;
  }}
  canvas {{
    background: rgba(13, 17, 23, 0.72);
    border: 1px solid var(--border);
    border-radius: 10px;
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.5);
    max-width: 100%;
    max-height: calc(100vh - 180px);
  }}
  .timeline-bar {{
    width: 100%;
    max-width: 680px;
    margin-top: 10px;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 8px 12px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }}
  .timeline-controls {{ display: flex; align-items: center; justify-content: space-between; gap: 8px; }}
  .frame-pills {{ display: flex; gap: 6px; flex-wrap: wrap; }}
  .control-group {{
    background: #0d1117;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }}
  .slider-row {{
    display: grid;
    grid-template-columns: 78px 1fr 60px;
    align-items: center;
    gap: 6px;
    font-size: 12px;
  }}
  input[type="number"] {{
    background: #161b22;
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 4px;
    font-size: 11px;
    text-align: right;
  }}
  .hint {{ font-size: 11px; color: var(--muted); line-height: 1.45; }}
  .status-toast {{ font-size: 12px; color: #4ade80; min-height: 18px; }}
  .check-row {{ display: flex; align-items: center; gap: 8px; font-size: 12px; cursor: pointer; }}
</style>
</head>
<body>
<header>
  <div class="brand">
    <span class="badge">STICKMAN 4 TEAMS + WEAPON SYSTEM</span>
    <strong>Tướng Sticker Basic + Vũ Khí Thẻ Bài</strong>
  </div>
  <div class="team-bar" id="teamBar">
    <button class="team-btn active" onclick="setTeam('team_blue', this)"><span class="dot" style="background:#3b82f6"></span>Đội 1: Xanh</button>
    <button class="team-btn" onclick="setTeam('team_red', this)"><span class="dot" style="background:#ef4444"></span>Đội 2: Đỏ</button>
    <button class="team-btn" onclick="setTeam('team_green', this)"><span class="dot" style="background:#22c55e"></span>Đội 3: Lá</button>
    <button class="team-btn" onclick="setTeam('team_amber', this)"><span class="dot" style="background:#f59e0b"></span>Đội 4: Vàng</button>
  </div>
  <div class="action-bar" id="actionBar"></div>
  <div class="tool-bar">
    <button id="btnPlay" class="active" onclick="togglePlay()">⏸ Pause</button>
    <button id="btnBones" class="active" onclick="toggleBones()">🦴 Bones: ON</button>
    <button class="primary" onclick="saveToGodotTscn()">💾 Save to .tscn</button>
  </div>
</header>

<main>
  <aside class="sidebar">
    <div class="card-box">
      <h3>Thẻ Bài &amp; Vũ Khí Đang Trang Bị</h3>
      <select id="weaponSelect" onchange="onSelectWeapon()"></select>
      <img id="cardPreviewImg" class="card-preview-img" alt="Diagonal Weapon Card Preview" />
      <div class="hint">
        Ảnh Preview Thẻ Bài (<strong>884×632</strong> ngang RGB Opaque, đặt chéo vũ khí tối ưu khung hình).
      </div>
    </div>

    <div class="card-box">
      <h3>Thiết Lập 2 Vị Trí Cầm (Grip 1 &amp; Grip 2) + Đa Vũ Khí</h3>
      <div style="display:flex; gap:6px; flex-wrap:wrap;">
        <button id="btnGrip1" class="active" onclick="selectGripSlot(1)">🔴 Cầm ở Grip 1 (Chính)</button>
        <button id="btnGrip2" onclick="selectGripSlot(2)">🔵 Cầm ở Grip 2 (Phụ)</button>
      </div>
      <button onclick="applyTwoHandedGripPose()">🤝 Pose Cầm 2 Tay (Tay Phải bám Grip 2)</button>
      <label class="check-row">
        <input type="checkbox" id="chkDualWield" onchange="toggleDualWield(this.checked)" />
        <span>Bật Vũ Khí Phụ (<strong>Weapon_Back</strong> ở Tay Sau)</span>
      </label>
      <label class="check-row">
        <input type="checkbox" id="chkWeaponAura" onchange="toggleWeaponAura(this.checked)" />
        <span>Hiệu ứng <strong>Weapon Animation / Aura</strong> (Chỉ có ở cấp S &amp; SSR)</span>
      </label>
      <div class="slider-row">
        <span>Grip 1 X/Y</span>
        <input type="range" id="grip1X" min="0" max="240" step="1" value="54" oninput="updateGripPoints()" />
        <input type="number" id="grip1Y" min="0" max="180" step="1" value="118" oninput="updateGripPoints()" />
      </div>
      <div class="slider-row">
        <span>Grip 2 X/Y</span>
        <input type="range" id="grip2X" min="0" max="240" step="1" value="28" oninput="updateGripPoints()" />
        <input type="number" id="grip2Y" min="0" max="180" step="1" value="136" oninput="updateGripPoints()" />
      </div>
      <div class="hint">
        • Chấm <strong>Đỏ</strong> trên vũ khí = <code>Grip 1</code> | Chấm <strong>Xanh Cyan</strong> = <code>Grip 2</code>.
      </div>
    </div>

    <h3>Hệ Xương 17 Bone2D (Stickman + 2 Vũ Khí)</h3>
    <div class="bone-list" id="boneList"></div>
  </aside>

  <section class="viewport">
    <canvas id="rigCanvas" width="512" height="512"></canvas>
    <div class="timeline-bar">
      <div class="timeline-controls">
        <strong id="lblActionInfo">Action: IDLE</strong>
        <span id="lblTimeInfo" style="font-size:12px;color:var(--muted)">t = 0.00s</span>
      </div>
      <input type="range" id="timeScrubber" min="0" max="1.2" step="0.01" value="0" oninput="onScrubTime(this.value)" />
      <div class="frame-pills" id="framePills"></div>
    </div>
  </section>

  <aside class="sidebar right">
    <h3>Thông Số Khớp Xương Đang Chọn</h3>
    <div class="control-group">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <strong id="selectedBoneName" style="color:var(--accent)">Weapon_Front</strong>
        <button onclick="resetSelectedBone()">Reset Bone</button>
      </div>
      <div class="slider-row">
        <span>Rotate (°)</span>
        <input type="range" id="sldRot" min="-180" max="180" step="0.5" value="0" oninput="onBoneInput('rot', this.value)" />
        <input type="number" id="numRot" value="0" step="0.5" oninput="onBoneInput('rot', this.value)" />
      </div>
      <div class="slider-row">
        <span>Offset X</span>
        <input type="range" id="sldDx" min="-120" max="120" step="0.5" value="0" oninput="onBoneInput('dx', this.value)" />
        <input type="number" id="numDx" value="0" step="0.5" oninput="onBoneInput('dx', this.value)" />
      </div>
      <div class="slider-row">
        <span>Offset Y</span>
        <input type="range" id="sldDy" min="-120" max="120" step="0.5" value="0" oninput="onBoneInput('dy', this.value)" />
        <input type="number" id="numDy" value="0" step="0.5" oninput="onBoneInput('dy', this.value)" />
      </div>
    </div>

    <h3>Vị Trí Cốt (Rest Pose &amp; Pivot)</h3>
    <div class="control-group">
      <div class="slider-row">
        <span>Rest X</span>
        <input type="range" id="sldRestX" min="-160" max="360" step="0.5" value="0" oninput="onRestInput('rest_x', this.value)" />
        <input type="number" id="numRestX" value="0" step="0.5" oninput="onRestInput('rest_x', this.value)" />
      </div>
      <div class="slider-row">
        <span>Rest Y</span>
        <input type="range" id="sldRestY" min="-160" max="420" step="0.5" value="0" oninput="onRestInput('rest_y', this.value)" />
        <input type="number" id="numRestY" value="0" step="0.5" oninput="onRestInput('rest_y', this.value)" />
      </div>
      <div class="slider-row">
        <span>Pivot X</span>
        <input type="range" id="sldPivX" min="0" max="240" step="0.5" value="0" oninput="onRestInput('pivot_x', this.value)" />
        <input type="number" id="numPivX" value="0" step="0.5" oninput="onRestInput('pivot_x', this.value)" />
      </div>
      <div class="slider-row">
        <span>Pivot Y</span>
        <input type="range" id="sldPivY" min="0" max="240" step="0.5" value="0" oninput="onRestInput('pivot_y', this.value)" />
        <input type="number" id="numPivY" value="0" step="0.5" oninput="onRestInput('pivot_y', this.value)" />
      </div>
    </div>

    <div class="status-toast" id="statusToast">Sẵn sàng — Chọn màu đội, vũ khí, Grip 1/2 hoặc chỉnh pose!</div>

    <div class="hint">
      • <strong>Save to .tscn:</strong> Lưu trực tiếp toàn bộ cây xương <code>Skeleton2D</code> (17 <code>Bone2D</code>), tọa độ <code>Grip 1 / Grip 2</code> và <code>AnimationLibrary</code> 6 action thẳng vào file <code>.tscn</code> của tướng.<br/>
      • <strong>Kiến trúc Tối Ưu 90% Token:</strong> Toàn bộ dữ liệu ảnh Base64 được tách sang <code>weapons_data.js</code> và tự động đồng bộ qua <code>tools/forge_weapon.py</code>.
    </div>
  </aside>
</main>

<script>window.DEFAULT_WEAPON_ID = "{default_weapon_id}";</script>
<script src="{data_js_rel_path}"></script>
<script>
const VFX_LIST = ["fx_slash", "fx_slash_heavy", "fx_spark", "fx_dust"];
const BONES = [];
const BONE_MAP = {{}};
const ACTIONS = {{}};
const TEAM_IMAGES = {{}};
const WEAPON_PACK_IMAGES = {{}};
const WEAPON_IMAGES = {{}};

Object.keys(window.TEAM_PART_B64 || {{}}).forEach(tkey => {{
  TEAM_IMAGES[tkey] = {{}};
  Object.entries(window.TEAM_PART_B64[tkey]).forEach(([pname, b64]) => {{
    const img = new Image();
    img.src = b64;
    TEAM_IMAGES[tkey][pname] = img;
  }});
}});

Object.entries(window.WEAPON_REGISTRY || {{}}).forEach(([wid, pack]) => {{
  WEAPON_PACK_IMAGES[wid] = {{}};
  Object.entries(pack.images || {{}}).forEach(([k, src]) => {{
    const im = new Image();
    im.src = src;
    WEAPON_PACK_IMAGES[wid][k] = im;
  }});
}});

let currentWeaponId = window.DEFAULT_WEAPON_ID || (window.WEAPON_ORDER && window.WEAPON_ORDER[0]) || "w003";
let currentTeam = "team_blue";
let currentAction = "idle";
let currentFrameIdx = 0;
let currentTime = 0.0;
let isPlaying = true;
let showBones = true;
let showDualWield = false;
let showWeaponAura = false;
let activeGripSlot = 1;
let selectedBone = "Weapon_Front";
let lastTs = performance.now();

function rebuildBoneList() {{
  const boneList = document.getElementById("boneList");
  if (!boneList) return;
  boneList.innerHTML = "";
  BONES.forEach(b => {{
    const div = document.createElement("div");
    div.className = "bone-item" + (b.name === selectedBone ? " selected" : "");
    div.innerHTML = `<span>${{b.name}}</span><span style="color:var(--muted);font-size:11px">z:${{b.z_index}}</span>`;
    div.onclick = () => selectBone(b.name);
    boneList.appendChild(div);
  }});
}}

function applyWeaponPack(wid) {{
  const pack = window.WEAPON_REGISTRY[wid];
  if (!pack) return;
  currentWeaponId = wid;
  BONES.length = 0;
  JSON.parse(JSON.stringify(pack.bones)).forEach(b => BONES.push(b));
  Object.keys(BONE_MAP).forEach(k => delete BONE_MAP[k]);
  BONES.forEach(b => BONE_MAP[b.name] = b);
  Object.keys(ACTIONS).forEach(k => delete ACTIONS[k]);
  Object.entries(JSON.parse(JSON.stringify(pack.actions))).forEach(([k, v]) => ACTIONS[k] = v);
  Object.keys(WEAPON_IMAGES).forEach(k => delete WEAPON_IMAGES[k]);
  Object.entries(WEAPON_PACK_IMAGES[wid] || {{}}).forEach(([k, im]) => WEAPON_IMAGES[k] = im);
  showWeaponAura = Boolean(pack.aura_default && WEAPON_IMAGES["weapon_anim_1"]);
  const chkAura = document.getElementById("chkWeaponAura");
  if (chkAura) {{
    chkAura.checked = showWeaponAura;
    chkAura.disabled = !WEAPON_IMAGES["weapon_anim_1"];
  }}
  const cardImg = document.getElementById("cardPreviewImg");
  if (cardImg) cardImg.src = pack.card_b64;
  const wf = BONE_MAP["Weapon_Front"];
  if (wf) {{
    document.getElementById("grip1X").value = Math.round(wf.grip1_x);
    document.getElementById("grip1Y").value = Math.round(wf.grip1_y);
    document.getElementById("grip2X").value = Math.round(wf.grip2_x);
    document.getElementById("grip2Y").value = Math.round(wf.grip2_y);
  }}
  currentFrameIdx = 0;
  currentTime = 0.0;
  const sc = document.getElementById("timeScrubber");
  if (sc && ACTIONS[currentAction]) {{
    sc.max = ACTIONS[currentAction].length;
    sc.value = 0;
  }}
  rebuildBoneList();
  rebuildFramePills();
  syncInspector();
}}

function setTeam(teamKey, btnEl) {{
  currentTeam = teamKey;
  document.querySelectorAll("#teamBar .team-btn").forEach(b => b.classList.remove("active"));
  if (btnEl) btnEl.classList.add("active");
  document.getElementById("statusToast").textContent = "Đã chuyển màu đội sang: " + teamKey;
}}

function selectGripSlot(slot) {{
  activeGripSlot = slot;
  document.getElementById("btnGrip1").classList.toggle("active", slot === 1);
  document.getElementById("btnGrip2").classList.toggle("active", slot === 2);
  const wf = BONE_MAP["Weapon_Front"];
  if (slot === 1) {{
    wf.pivot_x = wf.grip1_x;
    wf.pivot_y = wf.grip1_y;
  }} else {{
    wf.pivot_x = wf.grip2_x;
    wf.pivot_y = wf.grip2_y;
  }}
  wf.offset_x = Number((wf.width / 2.0 - wf.pivot_x).toFixed(2));
  wf.offset_y = Number((wf.height / 2.0 - wf.pivot_y).toFixed(2));
  syncInspector();
  document.getElementById("statusToast").textContent = `Đang cầm vũ khí tại Grip ${{slot}} (${{wf.pivot_x}}, ${{wf.pivot_y}})`;
}}

function updateGripPoints() {{
  const wf = BONE_MAP["Weapon_Front"];
  wf.grip1_x = parseFloat(document.getElementById("grip1X").value) || 0;
  wf.grip1_y = parseFloat(document.getElementById("grip1Y").value) || 0;
  wf.grip2_x = parseFloat(document.getElementById("grip2X").value) || 0;
  wf.grip2_y = parseFloat(document.getElementById("grip2Y").value) || 0;
  selectGripSlot(activeGripSlot);
}}

function applyTwoHandedGripPose() {{
  const f = ACTIONS[currentAction].frames[currentFrameIdx];
  f["UpperArm_R"] = [-26, 0, 0];
  f["Forearm_R"] = [-22, 0, 0];
  f["Hand_R"] = [-8, 0, 0];
  syncInspector();
  document.getElementById("statusToast").textContent = "Đã áp dụng Pose Cầm 2 Tay (Tay Phải bám vào Grip 2)!";
}}

function toggleDualWield(checked) {{
  showDualWield = checked;
  document.getElementById("statusToast").textContent = checked
    ? "Đã bật Vũ Khí Phụ (Weapon_Back trên Hand_R)!"
    : "Đã tắt Vũ Khí Phụ (chỉ cầm Weapon_Front).";
}}

function toggleWeaponAura(checked) {{
  if (!WEAPON_IMAGES["weapon_anim_1"]) {{
    showWeaponAura = false;
    const chk = document.getElementById("chkWeaponAura");
    if (chk) chk.checked = false;
    document.getElementById("statusToast").textContent =
      "Vũ khí cấp N & R chỉ hiển thị 1 ảnh tĩnh (weapon_anim_0), không có hiệu ứng animation!";
    return;
  }}
  showWeaponAura = checked;
  document.getElementById("statusToast").textContent = checked
    ? "Đã bật hiệu ứng Weapon Animation 4-Frame (Cấp S / SSR)!"
    : "Đã tắt hiệu ứng Weapon Animation (hiển thị tĩnh weapon_anim_0).";
}}

function onSelectWeapon() {{
  const wid = document.getElementById("weaponSelect").value;
  applyWeaponPack(wid);
  const pack = window.WEAPON_REGISTRY[wid];
  if (pack) {{
    document.getElementById("statusToast").textContent = "Đang trang bị: " + pack.name;
  }}
}}

function initUI() {{
  const sel = document.getElementById("weaponSelect");
  sel.innerHTML = "";
  const order = window.WEAPON_ORDER || Object.keys(window.WEAPON_REGISTRY || {{}});
  order.forEach(wid => {{
    const pack = window.WEAPON_REGISTRY[wid];
    if (!pack) return;
    const opt = document.createElement("option");
    opt.value = wid;
    opt.textContent = pack.name;
    if (wid === currentWeaponId) opt.selected = true;
    sel.appendChild(opt);
  }});

  applyWeaponPack(currentWeaponId);

  const actionBar = document.getElementById("actionBar");
  actionBar.innerHTML = "";
  Object.keys(ACTIONS).forEach(act => {{
    const btn = document.createElement("button");
    btn.textContent = act.toUpperCase();
    btn.className = act === currentAction ? "active" : "";
    btn.onclick = () => selectAction(act);
    actionBar.appendChild(btn);
  }});
}}

function selectAction(act) {{
  currentAction = act;
  currentFrameIdx = 0;
  currentTime = 0.0;
  const sc = document.getElementById("timeScrubber");
  sc.max = ACTIONS[act].length;
  sc.value = 0;
  document.querySelectorAll("#actionBar button").forEach(b => {{
    b.classList.toggle("active", b.textContent === act.toUpperCase());
  }});
  rebuildFramePills();
  syncInspector();
}}

function rebuildFramePills() {{
  const pills = document.getElementById("framePills");
  if (!pills || !ACTIONS[currentAction]) return;
  pills.innerHTML = "";
  const frames = ACTIONS[currentAction].frames;
  frames.forEach((f, idx) => {{
    const b = document.createElement("button");
    b.textContent = `F${{idx + 1}} (${{f.t.toFixed(2)}}s)`;
    b.className = idx === currentFrameIdx ? "active" : "";
    b.onclick = () => {{
      isPlaying = false;
      updatePlayBtn();
      currentFrameIdx = idx;
      currentTime = f.t;
      document.getElementById("timeScrubber").value = currentTime;
      rebuildFramePills();
      syncInspector();
    }};
    pills.appendChild(b);
  }});
}}

function selectBone(bname) {{
  selectedBone = bname;
  document.querySelectorAll(".bone-item").forEach(el => {{
    el.classList.toggle("selected", el.firstChild.textContent === bname);
  }});
  syncInspector();
}}

function getFramePoseAtTime(actName, t) {{
  const act = ACTIONS[actName];
  const frames = act.frames;
  if (!isPlaying) return frames[currentFrameIdx];
  if (frames.length === 1) return frames[0];
  let i0 = 0;
  for (let i = 0; i < frames.length - 1; i++) {{
    if (t >= frames[i].t && t <= frames[i + 1].t) {{ i0 = i; break; }}
    if (t > frames[frames.length - 1].t) i0 = frames.length - 1;
  }}
  const i1 = (i0 + 1) % frames.length;
  const f0 = frames[i0], f1 = frames[i1];
  const t0 = f0.t, t1 = i1 === 0 ? act.length : f1.t;
  const alpha = t1 > t0 ? Math.max(0, Math.min(1, (t - t0) / (t1 - t0))) : 0;
  const interp = {{ t }};
  BONES.forEach(b => {{
    const name = b.name;
    const v0 = f0[name] || [0, 0, 0];
    const v1 = (i1 === 0 && !act.loop) ? v0 : (f1[name] || [0, 0, 0]);
    interp[name] = [
      v0[0] + (v1[0] - v0[0]) * alpha,
      v0[1] + (v1[1] - v0[1]) * alpha,
      v0[2] + (v1[2] - v0[2]) * alpha,
    ];
  }});
  const m0 = f0.modulate_a !== undefined ? f0.modulate_a : 1.0;
  const m1 = f1.modulate_a !== undefined ? f1.modulate_a : 1.0;
  interp.modulate_a = m0 + (m1 - m0) * alpha;
  interp.vfx = f0.vfx || {{}};
  return interp;
}}

function computeWorldTransforms(framePose) {{
  const world = {{}};
  BONES.forEach(b => {{
    const name = b.name, parent = b.parent;
    let dx = 0, dy = 0, drot = 0;
    const val = framePose[name] || [0, 0, 0];
    if (name === "Hip") {{ dx = val[0]; dy = val[1]; drot = val[2]; }}
    else {{ drot = val[0]; dx = val[1]; dy = val[2]; }}
    const lx = b.rest_x + dx, ly = b.rest_y + dy, lrot = b.rest_rot + drot;
    let wx, wy, wrot;
    if (!parent) {{ wx = lx; wy = ly; wrot = lrot; }}
    else {{
      const p = world[parent];
      const rad = p.wrot * Math.PI / 180.0;
      const ca = Math.cos(rad), sa = Math.sin(rad);
      wx = p.wx + lx * ca - ly * sa;
      wy = p.wy + lx * sa + ly * ca;
      wrot = p.wrot + lrot;
    }}
    world[name] = {{ wx, wy, wrot, tx: wx, ty: wy }};
  }});
  BONES.forEach(b => {{
    const w = world[b.name];
    if (b.tip_child && world[b.tip_child]) {{
      w.tx = world[b.tip_child].wx;
      w.ty = world[b.tip_child].wy;
    }} else if (b.tip_offset) {{
      const rad = w.wrot * Math.PI / 180.0;
      const ca = Math.cos(rad), sa = Math.sin(rad);
      w.tx = w.wx + b.tip_offset[0] * ca - b.tip_offset[1] * sa;
      w.ty = w.wy + b.tip_offset[0] * sa + b.tip_offset[1] * ca;
    }}
  }});
  return world;
}}

function syncInspector() {{
  const b = BONE_MAP[selectedBone];
  if (!b || !ACTIONS[currentAction]) return;
  const f = ACTIONS[currentAction].frames[currentFrameIdx];
  const val = f[selectedBone] || [0, 0, 0];
  let rot = 0, dx = 0, dy = 0;
  if (selectedBone === "Hip") {{ dx = val[0]; dy = val[1]; rot = val[2]; }}
  else {{ rot = val[0]; dx = val[1]; dy = val[2]; }}
  document.getElementById("selectedBoneName").textContent = selectedBone;
  document.getElementById("sldRot").value = rot;
  document.getElementById("numRot").value = rot;
  document.getElementById("sldDx").value = dx;
  document.getElementById("numDx").value = dx;
  document.getElementById("sldDy").value = dy;
  document.getElementById("numDy").value = dy;
  document.getElementById("sldRestX").value = b.rest_x;
  document.getElementById("numRestX").value = b.rest_x;
  document.getElementById("sldRestY").value = b.rest_y;
  document.getElementById("numRestY").value = b.rest_y;
  document.getElementById("sldPivX").value = b.pivot_x;
  document.getElementById("numPivX").value = b.pivot_x;
  document.getElementById("sldPivY").value = b.pivot_y;
  document.getElementById("numPivY").value = b.pivot_y;
  document.getElementById("lblActionInfo").textContent =
    `Action: ${{currentAction.toUpperCase()}} (Frame ${{currentFrameIdx + 1}}/${{ACTIONS[currentAction].frames.length}})`;
}}

function onBoneInput(field, rawVal) {{
  isPlaying = false;
  updatePlayBtn();
  const v = parseFloat(rawVal) || 0;
  const f = ACTIONS[currentAction].frames[currentFrameIdx];
  if (!f[selectedBone]) f[selectedBone] = [0, 0, 0];
  if (selectedBone === "Hip") {{
    if (field === "dx") f.Hip[0] = v;
    if (field === "dy") f.Hip[1] = v;
    if (field === "rot") f.Hip[2] = v;
  }} else {{
    if (field === "rot") f[selectedBone][0] = v;
    if (field === "dx") f[selectedBone][1] = v;
    if (field === "dy") f[selectedBone][2] = v;
  }}
  syncInspector();
}}

function onRestInput(field, rawVal) {{
  const v = parseFloat(rawVal) || 0;
  const b = BONE_MAP[selectedBone];
  b[field] = v;
  b.offset_x = Number((b.width / 2.0 - b.pivot_x).toFixed(2));
  b.offset_y = Number((b.height / 2.0 - b.pivot_y).toFixed(2));
  syncInspector();
}}

function resetSelectedBone() {{
  const f = ACTIONS[currentAction].frames[currentFrameIdx];
  f[selectedBone] = [0, 0, 0];
  syncInspector();
}}

function togglePlay() {{
  isPlaying = !isPlaying;
  updatePlayBtn();
}}

function updatePlayBtn() {{
  const btn = document.getElementById("btnPlay");
  btn.textContent = isPlaying ? "⏸ Pause" : "▶ Play";
  btn.classList.toggle("active", isPlaying);
}}

function toggleBones() {{
  showBones = !showBones;
  const btn = document.getElementById("btnBones");
  btn.textContent = showBones ? "🦴 Bones: ON" : "🦴 Bones: OFF";
  btn.classList.toggle("active", showBones);
}}

function onScrubTime(val) {{
  isPlaying = false;
  updatePlayBtn();
  currentTime = parseFloat(val) || 0;
  const frames = ACTIONS[currentAction].frames;
  let best = 0;
  for (let i = 0; i < frames.length; i++) {{
    if (Math.abs(frames[i].t - currentTime) < Math.abs(frames[best].t - currentTime)) best = i;
  }}
  currentFrameIdx = best;
  rebuildFramePills();
  syncInspector();
}}

const canvas = document.getElementById("rigCanvas");
const ctx = canvas.getContext("2d");
let dragging = false;

canvas.addEventListener("mousedown", e => {{
  const rect = canvas.getBoundingClientRect();
  const mx = (e.clientX - rect.left) * (canvas.width / rect.width);
  const my = (e.clientY - rect.top) * (canvas.height / rect.height);
  const pose = getFramePoseAtTime(currentAction, currentTime);
  const world = computeWorldTransforms(pose);
  let bestBone = null, bestDist = 22;
  BONES.forEach(b => {{
    if (b.name === "Weapon_Back" && !showDualWield) return;
    const w = world[b.name];
    const d = Math.hypot(mx - w.wx, my - w.wy);
    if (d < bestDist) {{ bestDist = d; bestBone = b.name; }}
  }});
  if (bestBone) {{
    selectBone(bestBone);
    dragging = true;
    isPlaying = false;
    updatePlayBtn();
  }}
}});

window.addEventListener("mousemove", e => {{
  if (!dragging) return;
  const rect = canvas.getBoundingClientRect();
  const mx = (e.clientX - rect.left) * (canvas.width / rect.width);
  const my = (e.clientY - rect.top) * (canvas.height / rect.height);
  const pose = getFramePoseAtTime(currentAction, currentTime);
  const world = computeWorldTransforms(pose);
  const w = world[selectedBone];
  const f = ACTIONS[currentAction].frames[currentFrameIdx];
  if (!f[selectedBone]) f[selectedBone] = [0, 0, 0];
  if (selectedBone === "Hip" && e.shiftKey) {{
    const b = BONE_MAP["Hip"];
    f.Hip[0] = Math.round((mx - b.rest_x) * 2) / 2;
    f.Hip[1] = Math.round((my - b.rest_y) * 2) / 2;
  }} else {{
    const targetAngle = Math.atan2(my - w.wy, mx - w.wx) * 180 / Math.PI - 90;
    const b = BONE_MAP[selectedBone];
    const pRot = b.parent ? world[b.parent].wrot : 0;
    let drot = targetAngle - pRot - b.rest_rot;
    while (drot > 180) drot -= 360;
    while (drot < -180) drot += 360;
    if (selectedBone === "Hip") f.Hip[2] = Math.round(drot * 2) / 2;
    else f[selectedBone][0] = Math.round(drot * 2) / 2;
  }}
  syncInspector();
}});

window.addEventListener("mouseup", () => {{ dragging = false; }});

function renderLoop(now) {{
  const dt = (now - lastTs) / 1000.0;
  lastTs = now;
  const act = ACTIONS[currentAction];
  if (isPlaying && act) {{
    currentTime += dt;
    if (currentTime >= act.length) {{
      currentTime = act.loop ? (currentTime % act.length) : 0.0;
    }}
    document.getElementById("timeScrubber").value = currentTime;
    let best = 0;
    for (let i = 0; i < act.frames.length; i++) {{
      if (currentTime >= act.frames[i].t) best = i;
    }}
    if (best !== currentFrameIdx) {{
      currentFrameIdx = best;
      rebuildFramePills();
      syncInspector();
    }}
  }}
  document.getElementById("lblTimeInfo").textContent = `t = ${{currentTime.toFixed(2)}}s`;

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = "rgba(255,255,255,0.08)";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(48, 396); ctx.lineTo(464, 396);
  ctx.stroke();

  if (act) {{
    const pose = getFramePoseAtTime(currentAction, currentTime);
    const world = computeWorldTransforms(pose);
    const sorted = [...BONES].sort((a, b) => a.z_index - b.z_index);
    const modA = pose.modulate_a !== undefined ? pose.modulate_a : 1.0;

    sorted.forEach(b => {{
      if (b.name === "Weapon_Back" && !showDualWield) return;
      const w = world[b.name];
      const img = b.is_weapon ? WEAPON_IMAGES[b.part] : (TEAM_IMAGES[currentTeam] && TEAM_IMAGES[currentTeam][b.part]);
      if (!img || !img.complete) return;
      ctx.save();
      ctx.globalAlpha = modA;
      ctx.translate(w.wx, w.wy);
      ctx.rotate(w.wrot * Math.PI / 180.0);
      let drawImg = img;
      if (b.name === "Weapon_Front" && showWeaponAura && WEAPON_IMAGES["weapon_anim_1"]) {{
        const animIdx = Math.floor(now / 150) % 4;
        const animCand = WEAPON_IMAGES["weapon_anim_" + animIdx];
        if (animCand && animCand.complete) drawImg = animCand;
      }} else if (b.name === "Weapon_Front" && WEAPON_IMAGES["weapon_anim_0"] && WEAPON_IMAGES["weapon_anim_0"].complete) {{
        drawImg = WEAPON_IMAGES["weapon_anim_0"];
      }}
      ctx.drawImage(drawImg, -b.pivot_x, -b.pivot_y);

      if (showBones && b.name === "Weapon_Front") {{
        ctx.fillStyle = "#ef4444";
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.arc(b.grip1_x - b.pivot_x, b.grip1_y - b.pivot_y, 4.5, 0, Math.PI * 2);
        ctx.fill(); ctx.stroke();

        ctx.fillStyle = "#38bdf8";
        ctx.beginPath();
        ctx.arc(b.grip2_x - b.pivot_x, b.grip2_y - b.pivot_y, 4.5, 0, Math.PI * 2);
        ctx.fill(); ctx.stroke();
      }}
      ctx.restore();
    }});

    if (pose.vfx) {{
      Object.entries(pose.vfx).forEach(([vname, vcfg]) => {{
        const vimg = WEAPON_IMAGES[vname];
        if (!vimg || !vimg.complete) return;
        ctx.save();
        ctx.globalAlpha = vcfg.alpha !== undefined ? vcfg.alpha : 1.0;
        ctx.translate(vcfg.pos[0], vcfg.pos[1]);
        ctx.rotate((vcfg.rot || 0) * Math.PI / 180.0);
        const sc = vcfg.scale || 1.0;
        ctx.scale(sc, sc);
        ctx.drawImage(vimg, -vimg.width / 2, -vimg.height / 2);
        ctx.restore();
      }});
    }}

    if (showBones) {{
      BONES.forEach(b => {{
        if (b.name === "Weapon_Back" && !showDualWield) return;
        const w = world[b.name];
        const isSel = b.name === selectedBone;
        ctx.strokeStyle = isSel ? "#f59e0b" : (b.is_weapon ? "#f43f5e" : "rgba(56, 189, 248, 0.78)");
        ctx.lineWidth = isSel ? 2.6 : 1.6;
        ctx.beginPath();
        ctx.moveTo(w.wx, w.wy);
        ctx.lineTo(w.tx, w.ty);
        ctx.stroke();

        ctx.fillStyle = isSel ? "#f59e0b" : "#38bdf8";
        ctx.beginPath();
        ctx.arc(w.wx, w.wy, isSel ? 4.5 : 3.0, 0, Math.PI * 2);
        ctx.fill();
      }});
    }}
  }}

  requestAnimationFrame(renderLoop);
}}

function buildGodotTscnString() {{
  const pack = window.WEAPON_REGISTRY[currentWeaponId];
  const slug = pack.slug || (currentWeaponId + "_weapon");
  const tscnName = pack.tscn_name || (currentWeaponId + ".tscn");
  const gdName = tscnName.replace(".tscn", ".gd");
  const nodeName = pack.node_name || currentWeaponId.toUpperCase();

  const extList = [["1_script", "Script", `res://assets/weapons/${{slug}}/godot/${{gdName}}`]];
  const partExtId = {{}};
  let idx = 2;
  BONES.forEach(b => {{
    if (!partExtId[b.part]) {{
      partExtId[b.part] = `${{idx}}_${{b.part}}`;
      if (b.is_weapon) {{
        extList.push([partExtId[b.part], "Texture2D", `res://assets/weapons/${{slug}}/parts/${{b.part}}.png`]);
      }} else {{
        extList.push([partExtId[b.part], "Texture2D", `res://assets/sticker_hero/godot/parts/${{currentTeam}}/${{b.part}}.png`]);
      }}
      idx++;
    }}
  }});
  VFX_LIST.forEach(fx => {{
    partExtId[fx] = `${{idx}}_${{fx}}`;
    extList.push([partExtId[fx], "Texture2D", `res://assets/weapons/${{slug}}/parts/${{fx}}.png`]);
    idx++;
  }});

  const bonePaths = {{}};
  BONES.forEach(b => {{
    bonePaths[b.name] = b.parent ? `${{bonePaths[b.parent]}}/${{b.name}}` : `Skeleton2D/${{b.name}}`;
  }});

  const lines = [];
  lines.push(`[gd_scene load_steps=${{extList.length + 8}} format=3]`);
  lines.push("");
  extList.forEach(([eid, etype, epath]) => {{
    lines.push(`[ext_resource type="${{etype}}" path="${{epath}}" id="${{eid}}"]`);
  }});
  lines.push("");

  Object.entries(ACTIONS).forEach(([actName, act]) => {{
    lines.push(`[sub_resource type="Animation" id="Animation_${{actName}}"]`);
    lines.push(`resource_name = "${{actName}}"`);
    lines.push(`length = ${{act.length}}`);
    lines.push(`loop_mode = ${{act.loop ? 1 : 0}}`);
    const frames = act.frames;
    const tStr = frames.map(f => f.t.toFixed(2)).join(", ");
    const transStr = frames.map(() => "1").join(", ");
    let ti = 0;
    BONES.forEach(b => {{
      const bname = b.name;
      const bpath = bonePaths[bname];
      const pVals = [], rVals = [];
      frames.forEach(f => {{
        const val = f[bname] || [0, 0, 0];
        let dx = 0, dy = 0, drot = 0;
        if (bname === "Hip") {{ dx = val[0]; dy = val[1]; drot = val[2]; }}
        else {{ drot = val[0]; dx = val[1]; dy = val[2]; }}
        pVals.push(`Vector2(${{(b.rest_x + dx).toFixed(1)}}, ${{(b.rest_y + dy).toFixed(1)}})`);
        rVals.push(((b.rest_rot + drot) * Math.PI / 180.0).toFixed(4));
      }});
      lines.push(`tracks/${{ti}}/type = "value"`);
      lines.push(`tracks/${{ti}}/imported = false`);
      lines.push(`tracks/${{ti}}/enabled = true`);
      lines.push(`tracks/${{ti}}/path = NodePath("${{bpath}}:position")`);
      lines.push(`tracks/${{ti}}/interp = 1`);
      lines.push(`tracks/${{ti}}/loop_wrap = true`);
      lines.push(`tracks/${{ti}}/keys = {{"times": PackedFloat32Array(${{tStr}}), "transitions": PackedFloat32Array(${{transStr}}), "update": 0, "values": [${{pVals.join(", ")}}]}}`);
      ti++;
      lines.push(`tracks/${{ti}}/type = "value"`);
      lines.push(`tracks/${{ti}}/imported = false`);
      lines.push(`tracks/${{ti}}/enabled = true`);
      lines.push(`tracks/${{ti}}/path = NodePath("${{bpath}}:rotation")`);
      lines.push(`tracks/${{ti}}/interp = 1`);
      lines.push(`tracks/${{ti}}/loop_wrap = true`);
      lines.push(`tracks/${{ti}}/keys = {{"times": PackedFloat32Array(${{tStr}}), "transitions": PackedFloat32Array(${{transStr}}), "update": 0, "values": [${{rVals.join(", ")}}]}}`);
      ti++;
    }});
    lines.push("");
  }});

  lines.push('[sub_resource type="AnimationLibrary" id="AnimationLibrary_main"]');
  lines.push('_data = {{');
  Object.keys(ACTIONS).forEach(actName => {{
    lines.push(`"${{actName}}": SubResource("Animation_${{actName}}"),`);
  }});
  lines.push('}}');
  lines.push("");

  lines.push(`[node name="${{nodeName}}" type="Node2D"]`);
  lines.push('script = ExtResource("1_script")');
  lines.push("");
  lines.push('[node name="Skeleton2D" type="Skeleton2D" parent="."]');
  lines.push("");

  BONES.forEach(b => {{
    const bname = b.name;
    const parentPath = b.parent ? bonePaths[b.parent] : "Skeleton2D";
    const rad = b.rest_rot * Math.PI / 180.0;
    const ca = Math.cos(rad), sa = Math.sin(rad);
    let tx = 0, ty = 42;
    if (b.tip_child && BONE_MAP[b.tip_child]) {{
      tx = BONE_MAP[b.tip_child].rest_x;
      ty = BONE_MAP[b.tip_child].rest_y;
    }} else if (b.tip_offset) {{
      tx = b.tip_offset[0];
      ty = b.tip_offset[1];
    }}
    const bLen = Math.max(8.0, Math.hypot(tx, ty));
    const bAng = Math.atan2(ty, tx);

    lines.push(`[node name="${{bname}}" type="Bone2D" parent="${{parentPath}}"]`);
    lines.push(`position = Vector2(${{b.rest_x.toFixed(1)}}, ${{b.rest_y.toFixed(1)}})`);
    lines.push(`rotation = ${{rad.toFixed(4)}}`);
    lines.push(`rest = Transform2D(${{ca.toFixed(4)}}, ${{sa.toFixed(4)}}, ${{-sa.toFixed(4)}}, ${{ca.toFixed(4)}}, ${{b.rest_x.toFixed(1)}}, ${{b.rest_y.toFixed(1)}})`);
    lines.push('auto_calculate_length_and_angle = false');
    lines.push(`length = ${{bLen.toFixed(1)}}`);
    lines.push(`bone_angle = ${{bAng.toFixed(4)}}`);
    if (b.is_weapon) {{
      lines.push(`metadata/grip1 = Vector2(${{b.grip1_x.toFixed(1)}}, ${{b.grip1_y.toFixed(1)}})`);
      lines.push(`metadata/grip2 = Vector2(${{b.grip2_x.toFixed(1)}}, ${{b.grip2_y.toFixed(1)}})`);
    }}
    lines.push("");
    lines.push(`[node name="Sprite" type="Sprite2D" parent="${{bonePaths[bname]}}"]`);
    if (b.name === "Weapon_Back" && !showDualWield) lines.push('visible = false');
    lines.push(`z_index = ${{b.z_index}}`);
    lines.push('z_as_relative = false');
    lines.push(`texture = ExtResource("${{partExtId[b.part]}}")`);
    lines.push(`offset = Vector2(${{b.offset_x.toFixed(2)}}, ${{b.offset_y.toFixed(2)}})`);
    lines.push("");
  }});

  lines.push('[node name="VFXLayer" type="Node2D" parent="."]');
  lines.push('z_index = 20');
  lines.push('z_as_relative = false');
  lines.push("");
  VFX_LIST.forEach(fx => {{
    lines.push(`[node name="${{fx}}" type="Sprite2D" parent="VFXLayer"]`);
    lines.push('visible = false');
    lines.push('position = Vector2(256, 256)');
    lines.push(`texture = ExtResource("${{partExtId[fx]}}")`);
    lines.push("");
  }});

  lines.push('[node name="AnimationPlayer" type="AnimationPlayer" parent="."]');
  lines.push('libraries = {{');
  lines.push('"": SubResource("AnimationLibrary_main")');
  lines.push('}}');
  lines.push('autoplay = "idle"');
  lines.push("");
  return lines.join("\\n");
}}

async function saveToGodotTscn() {{
  const tscnContent = buildGodotTscnString();
  const pack = window.WEAPON_REGISTRY[currentWeaponId] || {{}};
  const suggestedName = pack.tscn_name || `${{currentWeaponId}}.tscn`;
  const toast = document.getElementById("statusToast");
  try {{
    if (window.showSaveFilePicker) {{
      const handle = await window.showSaveFilePicker({{
        suggestedName,
        types: [{{ description: "Godot 4 Scene (.tscn)", accept: {{ "text/plain": [".tscn"] }} }}],
      }});
      const writable = await handle.createWritable();
      await writable.write(tscnContent);
      await writable.close();
      toast.textContent = "✅ Đã lưu trực tiếp vào file " + suggestedName + "!";
      return;
    }}
  }} catch (err) {{
    if (err && err.name === "AbortError") return;
  }}
  const blob = new Blob([tscnContent], {{ type: "text/plain;charset=utf-8" }});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = suggestedName;
  a.click();
  URL.revokeObjectURL(url);
  toast.textContent = "✅ Đã xuất file " + suggestedName + "!";
}}

initUI();
requestAnimationFrame(renderLoop);
</script>
</body>
</html>
'''


def build_pack_entry_from_config(cfg: dict) -> dict:
    slug = cfg["slug"]
    wdir = ROOT / "assets/weapons" / slug
    pdir = wdir / "parts"
    cdir = wdir / "card"
    wid = cfg["id"]
    tier = cfg.get("tier", "N").upper()
    is_animated = tier in ("S", "SSR") and (pdir / "weapon_anim_1.png").exists()

    w_main = Image.open(pdir / "weapon_main.png").convert("RGBA")
    w_off = Image.open(pdir / "weapon_offhand.png").convert("RGBA")
    bones = build_anatomical_bones(w_main, w_off, cfg)
    arch = cfg.get("archetype", "melee_cleaver")
    actions = cfg.get("custom_actions") or ARCHETYPE_ACTIONS.get(arch, ARCHETYPE_ACTIONS["melee_cleaver"])

    images = {
        "weapon_main": b64_uri(pdir / "weapon_main.png"),
        "weapon_offhand": b64_uri(pdir / "weapon_offhand.png"),
        "weapon_anim_0": b64_uri(pdir / "weapon_anim_0.png") if (pdir / "weapon_anim_0.png").exists() else b64_uri(pdir / "weapon_main.png"),
    }
    if is_animated:
        for i in range(1, 4):
            if (pdir / f"weapon_anim_{i}.png").exists():
                images[f"weapon_anim_{i}"] = b64_uri(pdir / f"weapon_anim_{i}.png")
    for fx in VFX_NAMES:
        if (pdir / f"{fx}.png").exists():
            images[fx] = b64_uri(pdir / f"{fx}.png")

    card_path = cdir / f"{wid}_card_preview.png"
    return {
        "id": wid,
        "slug": slug,
        "tier": tier,
        "name": cfg["name"],
        "tscn_name": cfg["tscn_name"],
        "node_name": cfg["node_name"],
        "aura_default": is_animated,
        "card_b64": b64_uri(card_path),
        "bones": bones,
        "actions": actions,
        "images": images,
    }


def forge_single_weapon(config_path: pathlib.Path, force_gen: bool = False):
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    wid = cfg["id"]
    slug = cfg["slug"]
    tier = cfg.get("tier", "N").upper()
    wdir = ROOT / "assets/weapons" / slug
    rdir = wdir / "raw"
    pdir = wdir / "parts"
    cdir = wdir / "card"
    mdir_parts = ROOT / "assets/mobile/weapons" / slug / "parts"
    mdir_cards = ROOT / "assets/mobile/weapons" / slug / "card"
    for d in [rdir, pdir, cdir, mdir_parts, mdir_cards]:
        d.mkdir(parents=True, exist_ok=True)

    ref_raw = rdir / f"{wid}_ref_raw.png"
    if force_gen or (not (pdir / "weapon_main.png").exists() and not ref_raw.exists()):
        print(f"[{wid}] Resetting Muse thread & generating Step 1 Ref Weapon...")
        muse_post("/v1/thread", {"new_thread": True})
        muse_post("/generate-image", {
            "prompt": cfg["prompt_ref"],
            "reference_images": [str(LAYOUT_1X1)],
            "save_path": str(ref_raw),
        })

    if force_gen or not (pdir / "weapon_main.png").exists():
        raw_im = Image.open(ref_raw).convert("RGBA")
        unmixed = unmix_magenta_rgba(raw_im)
        clean_im = keep_largest_component_and_crop(unmixed, pad=0)
        if cfg.get("flip_horizontal", False):
            clean_im = clean_im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        tsz = cfg.get("target_size", [216, 166])
        scale = min(tsz[0] / max(1, clean_im.width), tsz[1] / max(1, clean_im.height))
        w_main = clean_im.resize((max(1, int(round(clean_im.width * scale))), max(1, int(round(clean_im.height * scale)))), Image.Resampling.LANCZOS)
        w_main = keep_largest_component_and_crop(w_main, pad=0)
        w_main.save(pdir / "weapon_main.png")
        w_main.save(pdir / "weapon_anim_0.png")
        if not (pdir / "weapon_offhand.png").exists():
            w_off = w_main.resize((max(1, int(w_main.width * 0.75)), max(1, int(w_main.height * 0.75))), Image.Resampling.LANCZOS)
            w_off.save(pdir / "weapon_offhand.png")

    # Step 2 (Only for S and SSR tiers; skipped for N and R tiers): 2x2 Animated Weapon Spritesheet
    anim_raw = rdir / f"{wid}_weapon_anim_2x2_raw.png"
    if tier in ("S", "SSR"):
        if force_gen or not (pdir / "weapon_anim_1.png").exists():
            if (force_gen or not anim_raw.exists()) and "prompt_anim_2x2" in cfg:
                print(f"[{wid}] Generating Step 2 (S/SSR) 2x2 Weapon Animation Sheet via Muse...")
                muse_post("/generate-image", {
                    "prompt": cfg["prompt_anim_2x2"],
                    "reference_images": [str(ref_raw), str(LAYOUT_2X2)],
                    "save_path": str(anim_raw),
                })
            if anim_raw.exists():
                w_main_ref = Image.open(pdir / "weapon_main.png").convert("RGBA")
                sheet_im = Image.open(anim_raw).convert("RGBA")
                sw, sh = sheet_im.size
                cw, ch = sw // 2, sh // 2
                for idx in range(4):
                    r_i, c_i = idx // 2, idx % 2
                    cell = sheet_im.crop((c_i * cw, r_i * ch, (c_i + 1) * cw, (r_i + 1) * ch))
                    cell_unmixed = unmix_magenta_rgba(cell)
                    cell_clean = keep_largest_component_and_crop(cell_unmixed, pad=0)
                    if cfg.get("flip_horizontal", False):
                        cell_clean = cell_clean.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                    cell_fitted = cell_clean.resize(w_main_ref.size, Image.Resampling.LANCZOS)
                    cell_fitted.save(pdir / f"weapon_anim_{idx}.png")
                    if idx == 1 and not (pdir / "weapon_aura.png").exists():
                        cell_fitted.save(pdir / "weapon_aura.png")

    # Copy shared soft VFX if missing
    vfx_src_dir = ROOT / "assets/weapons/w001_hac_kiem_tan_binh/parts"
    for fx in VFX_NAMES:
        if not (pdir / f"{fx}.png").exists() and (vfx_src_dir / f"{fx}.png").exists():
            shutil.copyfile(vfx_src_dir / f"{fx}.png", pdir / f"{fx}.png")

    card_png = cdir / f"{wid}_card_preview.png"
    if force_gen or not card_png.exists():
        card_raw = rdir / f"{wid}_card_preview_raw.png"
        if not card_raw.exists() and "prompt_card" in cfg:
            print(f"[{wid}] Generating Card Preview via Muse...")
            card_refs = [str(ref_raw)]
            if tier in ("S", "SSR") and anim_raw.exists():
                card_refs.append(str(anim_raw))
            muse_post("/generate-image", {
                "prompt": cfg["prompt_card"],
                "reference_images": card_refs,
                "save_path": str(card_raw),
            })
        if card_raw.exists():
            cim = Image.open(card_raw).convert("RGB").resize((884, 632), Image.Resampling.LANCZOS)
            cim.save(card_png, format="PNG")

    # Export WebP mobile assets
    if card_png.exists():
        cim = Image.open(card_png).convert("RGB")
        cim.resize((354, 253), Image.Resampling.LANCZOS).save(mdir_cards / f"{wid}_card_preview.webp", format="WEBP", quality=90)
    for png_p in pdir.glob("*.png"):
        Image.open(png_p).convert("RGBA").save(mdir_parts / f"{png_p.stem}.webp", format="WEBP", quality=90)

    # Load parts & build rig + QC + Godot
    weapon_parts = {p.stem: Image.open(p).convert("RGBA") for p in pdir.glob("*.png")}
    card_img = Image.open(card_png).convert("RGB")
    pack = build_pack_entry_from_config(cfg)
    build_qc_boards(cfg, pack["bones"], pack["actions"], wdir, weapon_parts, card_img)
    build_godot_files(cfg, pack["bones"], pack["actions"], wdir)

    # Update registry & lightweight HTML editors
    reg, order = load_weapons_registry()
    reg[wid] = pack
    if wid not in order:
        order.insert(0, wid)
    save_weapons_data_js(reg, order)

    MAIN_EDITOR_HTML.write_text(render_lightweight_editor_html("weapons_data.js", order[0]), encoding="utf-8")
    for w_key, w_pack in reg.items():
        w_slug = w_pack["slug"]
        ed_path = ROOT / "assets/weapons" / w_slug / f"{w_key}_editor.html"
        if ed_path.parent.exists():
            ed_path.write_text(render_lightweight_editor_html("../../weapons_data.js", w_key), encoding="utf-8")

    print(f"[{wid}] FORGE COMPLETE -> QC, Godot (.tscn/.gd), weapons_data.js & lightweight HTML editors updated!")


def main():
    parser = argparse.ArgumentParser(description="One-Shot Token-Optimized Weapon & Spine Rig Builder")
    parser.add_argument("--config", type=str, help="Path to weapon JSON config (e.g. assets/weapons/configs/w004.json)")
    parser.add_argument("--sync-all", action="store_true", help="Rebuild all configs in assets/weapons/configs/*.json")
    parser.add_argument("--force-gen", action="store_true", help="Force regenerate raw images from Muse API")
    args = parser.parse_args()

    if args.sync_all:
        cfg_dir = ROOT / "assets/weapons/configs"
        for cp in sorted(cfg_dir.glob("*.json")):
            forge_single_weapon(cp, force_gen=args.force_gen)
    elif args.config:
        forge_single_weapon(pathlib.Path(args.config), force_gen=args.force_gen)
    else:
        parser.error("Provide --config <path.json> or --sync-all")


if __name__ == "__main__":
    main()
