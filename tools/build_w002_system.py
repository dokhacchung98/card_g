#!/usr/bin/env python3
"""
tools/build_w002_system.py
Complete pipeline builder for W002 (Nỏ Câm Lặng - Cấp N)
Follows strict 2-step weapon flow for N & R tier weapons:
  1. Static Ref Weapon (weapon_main.png / weapon_anim_0.png, no ammo drawn for ranged weapons, no weapon animation)
  2. Opaque RGB Card Preview (884x632 PNG & 354x253 WebP)
Generates QC audit boards, Godot 4 .tscn/.gd, and interactive HTML editors.
"""

import os, json, math, shutil, base64, re
from PIL import Image, ImageDraw, ImageFont
import numpy as np

REPO_DIR = "/Users/dochung/Desktop/card_g"
STICKER_DIR = os.path.join(REPO_DIR, "assets", "sticker_hero")
STICKER_GODOT_PARTS = os.path.join(STICKER_DIR, "godot", "parts")

W002_DIR = os.path.join(REPO_DIR, "assets", "weapons", "w002_no_thu_cam_lang")
W002_RAW_DIR = os.path.join(W002_DIR, "raw")
W002_PARTS_DIR = os.path.join(W002_DIR, "parts")
W002_CARD_DIR = os.path.join(W002_DIR, "card")
W002_QC_DIR = os.path.join(W002_DIR, "qc_previews")
W002_GODOT_DIR = os.path.join(W002_DIR, "godot")
ARTIFACT_DIR = "/Users/dochung/.gemini/antigravity-cli/brain/ab7dc2b7-9521-42a4-be21-abd94f794ce3"

for d in [W002_RAW_DIR, W002_PARTS_DIR, W002_CARD_DIR, W002_QC_DIR, W002_GODOT_DIR, ARTIFACT_DIR]:
    os.makedirs(d, exist_ok=True)

# 1. Base sticker parts for 4 teams
TEAMS = ["team_blue", "team_red", "team_green", "team_amber"]
STICKER_PARTS = [
    "head", "neck", "chest", "hip_kilt",
    "arm_upper_front", "arm_lower_front", "hand_front",
    "arm_upper_back", "arm_lower_back", "hand_back",
    "leg_thigh_front", "leg_shin_front", "foot_front",
    "leg_thigh_back", "leg_shin_back", "foot_back"
]

TEAM_PARTS = {t: {} for t in TEAMS}
for t in TEAMS:
    for p in STICKER_PARTS:
        fp = os.path.join(STICKER_GODOT_PARTS, t, f"{p}.png")
        TEAM_PARTS[t][p] = Image.open(fp).convert("RGBA")

# Weapon parts (Cấp N: 1 static weapon image weapon_main.png = weapon_anim_0.png, no weapon animation)
w002_main = Image.open(os.path.join(W002_PARTS_DIR, "weapon_main.png")).convert("RGBA")
w002_offhand = Image.open(os.path.join(W002_PARTS_DIR, "weapon_offhand.png")).convert("RGBA")
w002_anim_0 = Image.open(os.path.join(W002_PARTS_DIR, "weapon_anim_0.png")).convert("RGBA")

VFX_PARTS = {
    "fx_slash": Image.open(os.path.join(W002_PARTS_DIR, "fx_slash.png")).convert("RGBA"),
    "fx_slash_heavy": Image.open(os.path.join(W002_PARTS_DIR, "fx_slash_heavy.png")).convert("RGBA"),
    "fx_spark": Image.open(os.path.join(W002_PARTS_DIR, "fx_spark.png")).convert("RGBA"),
    "fx_dust": Image.open(os.path.join(W002_PARTS_DIR, "fx_dust.png")).convert("RGBA"),
}

W002_CARD_PNG = os.path.join(W002_CARD_DIR, "w002_card_preview.png")

# Grip points for Crossbow (210x115 tight-cropped static crossbow)
W002_G1_X, W002_G1_Y = 73.5, 58.0   # Main trigger grip
W002_G2_X, W002_G2_Y = 128.0, 52.0  # Front barrel grip

# 18-Bone setup for Sticker + W002 Crossbow
BONES_W002 = [
    {"name": "Hip", "parent": None, "part": "hip_kilt", "is_weapon": False, "rest_x": 198.0, "rest_y": 258.0, "rest_rot": 0.0, "pivot_x": 34.5, "pivot_y": 18.2, "z_index": 7, "tip_child": "Chest", "width": 69, "height": 52, "offset_x": 0.0, "offset_y": 7.8},
    {"name": "Thigh_L", "parent": "Hip", "part": "leg_thigh_back", "is_weapon": False, "rest_x": 8.0, "rest_y": 14.0, "rest_rot": -22.0, "pivot_x": 11.0, "pivot_y": 11.0, "z_index": 1, "tip_child": "Shin_L", "width": 22, "height": 64, "offset_x": 0.0, "offset_y": 21.0},
    {"name": "Shin_L", "parent": "Thigh_L", "part": "leg_shin_back", "is_weapon": False, "rest_x": 0.0, "rest_y": 42.0, "rest_rot": 16.0, "pivot_x": 10.5, "pivot_y": 10.5, "z_index": 2, "tip_child": "Foot_L", "width": 21, "height": 60, "offset_x": 0.0, "offset_y": 19.5},
    {"name": "Foot_L", "parent": "Shin_L", "part": "foot_back", "is_weapon": False, "rest_x": 0.0, "rest_y": 39.0, "rest_rot": 6.0, "pivot_x": 13.9, "pivot_y": 9.0, "z_index": 3, "tip_offset": [36.0, 18.0], "width": 48, "height": 37, "offset_x": 10.1, "offset_y": 9.5},
    {"name": "Thigh_R", "parent": "Hip", "part": "leg_thigh_front", "is_weapon": False, "rest_x": -8.0, "rest_y": 14.0, "rest_rot": 22.0, "pivot_x": 11.5, "pivot_y": 11.5, "z_index": 4, "tip_child": "Shin_R", "width": 23, "height": 66, "offset_x": 0.0, "offset_y": 21.5},
    {"name": "Shin_R", "parent": "Thigh_R", "part": "leg_shin_front", "is_weapon": False, "rest_x": 0.0, "rest_y": 43.0, "rest_rot": -14.0, "pivot_x": 11.0, "pivot_y": 11.0, "z_index": 5, "tip_child": "Foot_R", "width": 22, "height": 62, "offset_x": 0.0, "offset_y": 20.0},
    {"name": "Foot_R", "parent": "Shin_R", "part": "foot_front", "is_weapon": False, "rest_x": 0.0, "rest_y": 40.0, "rest_rot": -8.0, "pivot_x": 14.6, "pivot_y": 9.0, "z_index": 6, "tip_offset": [38.0, 18.0], "width": 50, "height": 39, "offset_x": 10.4, "offset_y": 10.5},
    {"name": "Chest", "parent": "Hip", "part": "chest", "is_weapon": False, "rest_x": 0.0, "rest_y": -4.0, "rest_rot": 3.0, "pivot_x": 44.5, "pivot_y": 74.0, "z_index": 8, "tip_child": "Neck", "width": 89, "height": 86, "offset_x": 0.0, "offset_y": -31.0},
    {"name": "Neck", "parent": "Chest", "part": "neck", "is_weapon": False, "rest_x": 0.0, "rest_y": -66.0, "rest_rot": 0.0, "pivot_x": 7.0, "pivot_y": 27.0, "z_index": 7, "tip_child": "Head", "width": 14, "height": 34, "offset_x": 0.0, "offset_y": -10.0},
    {"name": "Head", "parent": "Neck", "part": "head", "is_weapon": False, "rest_x": 0.0, "rest_y": -20.0, "rest_rot": -3.0, "pivot_x": 45.5, "pivot_y": 82.0, "z_index": 11, "tip_offset": [0.0, -76.0], "width": 91, "height": 92, "offset_x": 0.0, "offset_y": -36.0},
    {"name": "UpperArm_R", "parent": "Chest", "part": "arm_upper_back", "is_weapon": False, "rest_x": 10.0, "rest_y": -58.0, "rest_rot": -28.0, "pivot_x": 10.5, "pivot_y": 10.5, "z_index": 6, "tip_child": "Forearm_R", "width": 21, "height": 60, "offset_x": 0.0, "offset_y": 19.5},
    {"name": "Forearm_R", "parent": "UpperArm_R", "part": "arm_lower_back", "is_weapon": False, "rest_x": 0.0, "rest_y": 39.0, "rest_rot": -42.0, "pivot_x": 10.0, "pivot_y": 10.0, "z_index": 9, "tip_child": "Hand_R", "width": 20, "height": 56, "offset_x": 0.0, "offset_y": 18.0},
    {"name": "Hand_R", "parent": "Forearm_R", "part": "hand_back", "is_weapon": False, "rest_x": 0.0, "rest_y": 36.0, "rest_rot": 0.0, "pivot_x": 15.5, "pivot_y": 5.0, "z_index": 10, "tip_child": "Weapon_Back", "width": 32, "height": 46, "offset_x": 0.5, "offset_y": 18.0},
    {"name": "Weapon_Back", "parent": "Hand_R", "part": "weapon_offhand", "is_weapon": True, "visible_default": False, "rest_x": 0.0, "rest_y": 24.0, "rest_rot": 45.0, "pivot_x": 18.0, "pivot_y": 26.0, "grip1_x": 18.0, "grip1_y": 26.0, "grip2_x": 12.0, "grip2_y": 30.0, "z_index": 9, "tip_offset": [65.0, -25.0], "width": w002_offhand.width, "height": w002_offhand.height, "offset_x": round(w002_offhand.width / 2.0 - 18.0, 2), "offset_y": round(w002_offhand.height / 2.0 - 26.0, 2)},
    {"name": "UpperArm_L", "parent": "Chest", "part": "arm_upper_front", "is_weapon": False, "rest_x": -8.0, "rest_y": -58.0, "rest_rot": 10.0, "pivot_x": 11.0, "pivot_y": 11.0, "z_index": 12, "tip_child": "Forearm_L", "width": 22, "height": 62, "offset_x": 0.0, "offset_y": 20.0},
    {"name": "Forearm_L", "parent": "UpperArm_L", "part": "arm_lower_front", "is_weapon": False, "rest_x": 0.0, "rest_y": 40.0, "rest_rot": -62.0, "pivot_x": 10.0, "pivot_y": 10.0, "z_index": 13, "tip_child": "Hand_L", "width": 20, "height": 58, "offset_x": 0.0, "offset_y": 19.0},
    {"name": "Hand_L", "parent": "Forearm_L", "part": "hand_front", "is_weapon": False, "rest_x": 0.0, "rest_y": 38.0, "rest_rot": 0.0, "pivot_x": 16.5, "pivot_y": 5.0, "z_index": 15, "tip_child": "Weapon_Front", "width": 34, "height": 48, "offset_x": 0.5, "offset_y": 19.0},
    {"name": "Weapon_Front", "parent": "Hand_L", "part": "weapon_main", "is_weapon": True, "visible_default": True, "rest_x": 0.0, "rest_y": 26.0, "rest_rot": 38.0, "pivot_x": W002_G1_X, "pivot_y": W002_G1_Y, "grip1_x": W002_G1_X, "grip1_y": W002_G1_Y, "grip2_x": W002_G2_X, "grip2_y": W002_G2_Y, "z_index": 14, "tip_offset": [125.0, -45.0], "width": w002_main.width, "height": w002_main.height, "offset_x": round(w002_main.width / 2.0 - W002_G1_X, 2), "offset_y": round(w002_main.height / 2.0 - W002_G1_Y, 2)}
]

BONE_MAP_W002 = {b["name"]: b for b in BONES_W002}

# Clean 6-Action animations for Crossbow shooter (0px joint separation on all child bones)
ACTIONS_W002 = {
    "idle": {
        "grid": [2, 2], "length": 1.2, "loop": True,
        "frames": [
            {"t": 0.0, "Hip": [0, 0, 0], "Chest": [0, 0, 0], "Head": [0, 0, 0], "UpperArm_R": [0, 0, 0], "Forearm_R": [0, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [0, 0, 0], "Forearm_L": [0, 0, 0], "Hand_L": [0, 0, 0], "Weapon_Front": [0, 0, 0], "Thigh_R": [0, 0, 0], "Shin_R": [0, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [0, 0, 0], "Shin_L": [0, 0, 0], "Foot_L": [0, 0, 0]},
            {"t": 0.3, "Hip": [0, 3, 0], "Chest": [2, 0, 0], "Head": [-2, 0, 0], "UpperArm_R": [4, 0, 0], "Forearm_R": [3, 0, 0], "Hand_R": [-2, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-4, 0, 0], "Forearm_L": [-3, 0, 0], "Hand_L": [-2, 0, 0], "Weapon_Front": [-2, 0, 0], "Thigh_R": [-3, 0, 0], "Shin_R": [3, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-2, 0, 0], "Shin_L": [2, 0, 0], "Foot_L": [0, 0, 0]},
            {"t": 0.6, "Hip": [0, 5, 0], "Chest": [4, 0, 0], "Head": [-3, 0, 0], "UpperArm_R": [6, 0, 0], "Forearm_R": [5, 0, 0], "Hand_R": [-3, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-6, 0, 0], "Forearm_L": [-5, 0, 0], "Hand_L": [-3, 0, 0], "Weapon_Front": [-3, 0, 0], "Thigh_R": [-5, 0, 0], "Shin_R": [5, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-4, 0, 0], "Shin_L": [4, 0, 0], "Foot_L": [0, 0, 0]},
            {"t": 0.9, "Hip": [0, 2, 0], "Chest": [1, 0, 0], "Head": [-1, 0, 0], "UpperArm_R": [2, 0, 0], "Forearm_R": [2, 0, 0], "Hand_R": [-1, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-2, 0, 0], "Forearm_L": [-2, 0, 0], "Hand_L": [-1, 0, 0], "Weapon_Front": [-1, 0, 0], "Thigh_R": [-2, 0, 0], "Shin_R": [2, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-1, 0, 0], "Shin_L": [1, 0, 0], "Foot_L": [0, 0, 0]}
        ]
    },
    "walk": {
        "grid": [2, 3], "length": 0.9, "loop": True,
        "frames": [
            {"t": 0.0, "Hip": [-3, 4, 2], "Chest": [4, 0, 0], "Head": [-3, 0, 0], "UpperArm_R": [14, 0, 0], "Forearm_R": [6, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-14, 0, 0], "Forearm_L": [-6, 0, 0], "Hand_L": [-2, 0, 0], "Weapon_Front": [-4, 0, 0], "Thigh_R": [-22, 0, 0], "Shin_R": [12, 0, 0], "Foot_R": [6, 0, 0], "Thigh_L": [18, 0, 0], "Shin_L": [14, 0, 0], "Foot_L": [8, 0, 0]},
            {"t": 0.15, "Hip": [-2, 6, 2], "Chest": [5, 0, 0], "Head": [-4, 0, 0], "UpperArm_R": [8, 0, 0], "Forearm_R": [4, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-8, 0, 0], "Forearm_L": [-4, 0, 0], "Hand_L": [-2, 0, 0], "Weapon_Front": [-2, 0, 0], "Thigh_R": [-10, 0, 0], "Shin_R": [14, 0, 0], "Foot_R": [2, 0, 0], "Thigh_L": [8, 0, 0], "Shin_L": [18, 0, 0], "Foot_L": [10, 0, 0]},
            {"t": 0.3, "Hip": [0, -2, 0], "Chest": [3, 0, 0], "Head": [-2, 0, 0], "UpperArm_R": [-6, 0, 0], "Forearm_R": [-4, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [6, 0, 0], "Forearm_L": [2, 0, 0], "Hand_L": [0, 0, 0], "Weapon_Front": [2, 0, 0], "Thigh_R": [4, 0, 0], "Shin_R": [8, 0, 0], "Foot_R": [-4, 0, 0], "Thigh_L": [-10, 0, 0], "Shin_L": [16, 0, 0], "Foot_L": [6, 0, 0]},
            {"t": 0.45, "Hip": [3, 4, 2], "Chest": [5, 0, 0], "Head": [-3, 0, 0], "UpperArm_R": [-14, 0, 0], "Forearm_R": [-6, 0, 0], "Hand_R": [-2, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [14, 0, 0], "Forearm_L": [4, 0, 0], "Hand_L": [2, 0, 0], "Weapon_Front": [4, 0, 0], "Thigh_R": [16, 0, 0], "Shin_R": [14, 0, 0], "Foot_R": [6, 0, 0], "Thigh_L": [-22, 0, 0], "Shin_L": [10, 0, 0], "Foot_L": [-4, 0, 0]},
            {"t": 0.6, "Hip": [2, 6, 2], "Chest": [6, 0, 0], "Head": [-4, 0, 0], "UpperArm_R": [-8, 0, 0], "Forearm_R": [-4, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [8, 0, 0], "Forearm_L": [2, 0, 0], "Hand_L": [0, 0, 0], "Weapon_Front": [2, 0, 0], "Thigh_R": [8, 0, 0], "Shin_R": [18, 0, 0], "Foot_R": [8, 0, 0], "Thigh_L": [-10, 0, 0], "Shin_L": [12, 0, 0], "Foot_L": [0, 0, 0]},
            {"t": 0.75, "Hip": [-2, -2, 0], "Chest": [3, 0, 0], "Head": [-2, 0, 0], "UpperArm_R": [6, 0, 0], "Forearm_R": [2, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-6, 0, 0], "Forearm_L": [-2, 0, 0], "Hand_L": [-1, 0, 0], "Weapon_Front": [-1, 0, 0], "Thigh_R": [-8, 0, 0], "Shin_R": [10, 0, 0], "Foot_R": [4, 0, 0], "Thigh_L": [4, 0, 0], "Shin_L": [10, 0, 0], "Foot_L": [4, 0, 0]}
        ]
    },
    "attack": {
        "grid": [2, 2], "length": 0.65, "loop": False,
        "frames": [
            {"t": 0.0, "Hip": [-6, 4, -2], "Chest": [6, 0, 0], "Head": [-4, 0, 0], "UpperArm_R": [-22, 0, 0], "Forearm_R": [-18, 0, 0], "Hand_R": [-8, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-24, 0, 0], "Forearm_L": [-16, 0, 0], "Hand_L": [-12, 0, 0], "Weapon_Front": [-10, 0, 0], "Thigh_R": [12, 0, 0], "Shin_R": [10, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-12, 0, 0], "Shin_L": [10, 0, 0], "Foot_L": [0, 0, 0]},
            {"t": 0.18, "Hip": [8, 6, 4], "Chest": [8, 0, 0], "Head": [-6, 0, 0], "UpperArm_R": [-14, 0, 0], "Forearm_R": [-8, 0, 0], "Hand_R": [-4, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-10, 0, 0], "Forearm_L": [10, 0, 0], "Hand_L": [14, 0, 0], "Weapon_Front": [24, 0, 0], "Thigh_R": [-14, 0, 0], "Shin_R": [12, 0, 0], "Foot_R": [4, 0, 0], "Thigh_L": [12, 0, 0], "Shin_L": [12, 0, 0], "Foot_L": [4, 0, 0], "vfx": {"fx_spark": {"pos": [330, 260], "rot": 0, "scale": 0.75, "alpha": 0.95}}},
            {"t": 0.36, "Hip": [10, 8, 6], "Chest": [10, 0, 0], "Head": [-8, 0, 0], "UpperArm_R": [-18, 0, 0], "Forearm_R": [-12, 0, 0], "Hand_R": [-6, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [10, 0, 0], "Forearm_L": [18, 0, 0], "Hand_L": [20, 0, 0], "Weapon_Front": [38, 0, 0], "Thigh_R": [-18, 0, 0], "Shin_R": [14, 0, 0], "Foot_R": [6, 0, 0], "Thigh_L": [16, 0, 0], "Shin_L": [14, 0, 0], "Foot_L": [6, 0, 0], "vfx": {"fx_slash": {"pos": [360, 250], "rot": 12, "scale": 0.8, "alpha": 0.92}}},
            {"t": 0.52, "Hip": [2, 2, 1], "Chest": [2, 0, 0], "Head": [-1, 0, 0], "UpperArm_R": [-4, 0, 0], "Forearm_R": [-2, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-2, 0, 0], "Forearm_L": [0, 0, 0], "Hand_L": [0, 0, 0], "Weapon_Front": [0, 0, 0], "Thigh_R": [-4, 0, 0], "Shin_R": [4, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [4, 0, 0], "Shin_L": [4, 0, 0], "Foot_L": [0, 0, 0]}
        ]
    },
    "cast": {
        "grid": [2, 3], "length": 0.95, "loop": False,
        "frames": [
            {"t": 0.0, "Hip": [-10, 6, -4], "Chest": [-8, 0, 0], "Head": [6, 0, 0], "UpperArm_R": [18, 0, 0], "Forearm_R": [12, 0, 0], "Hand_R": [4, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-38, 0, 0], "Forearm_L": [-16, 0, 0], "Hand_L": [-12, 0, 0], "Weapon_Front": [-14, 0, 0], "Thigh_R": [8, 0, 0], "Shin_R": [10, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-10, 0, 0], "Shin_L": [10, 0, 0], "Foot_L": [0, 0, 0], "vfx": {"fx_dust": {"pos": [218, 412], "rot": 0, "scale": 0.62, "alpha": 0.76}}},
            {"t": 0.16, "Hip": [-14, 10, -6], "Chest": [-12, 0, 0], "Head": [10, 0, 0], "UpperArm_R": [24, 0, 0], "Forearm_R": [16, 0, 0], "Hand_R": [6, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-50, 0, 0], "Forearm_L": [-20, 0, 0], "Hand_L": [-16, 0, 0], "Weapon_Front": [-20, 0, 0], "Thigh_R": [12, 0, 0], "Shin_R": [14, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-14, 0, 0], "Shin_L": [14, 0, 0], "Foot_L": [0, 0, 0], "vfx": {"fx_dust": {"pos": [212, 412], "rot": 0, "scale": 0.72, "alpha": 0.86}}},
            {"t": 0.34, "Hip": [12, 4, 6], "Chest": [10, 0, 0], "Head": [-8, 0, 0], "UpperArm_R": [-16, 0, 0], "Forearm_R": [-10, 0, 0], "Hand_R": [-4, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-10, 0, 0], "Forearm_L": [10, 0, 0], "Hand_L": [14, 0, 0], "Weapon_Front": [24, 0, 0], "Thigh_R": [-18, 0, 0], "Shin_R": [12, 0, 0], "Foot_R": [4, 0, 0], "Thigh_L": [16, 0, 0], "Shin_L": [14, 0, 0], "Foot_L": [6, 0, 0], "vfx": {"fx_slash_heavy": {"pos": [310, 258], "rot": 10, "scale": 0.72, "alpha": 0.95}, "fx_dust": {"pos": [196, 412], "rot": 0, "scale": 0.74, "alpha": 0.85}}},
            {"t": 0.52, "Hip": [16, 8, 8], "Chest": [14, 0, 0], "Head": [-10, 0, 0], "UpperArm_R": [-22, 0, 0], "Forearm_R": [-14, 0, 0], "Hand_R": [-6, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [12, 0, 0], "Forearm_L": [20, 0, 0], "Hand_L": [22, 0, 0], "Weapon_Front": [44, 0, 0], "Thigh_R": [-22, 0, 0], "Shin_R": [14, 0, 0], "Foot_R": [6, 0, 0], "Thigh_L": [20, 0, 0], "Shin_L": [16, 0, 0], "Foot_L": [8, 0, 0], "vfx": {"fx_slash_heavy": {"pos": [330, 268], "rot": 20, "scale": 0.68, "alpha": 0.82}, "fx_spark": {"pos": [360, 310], "rot": 12, "scale": 0.75, "alpha": 0.94}}},
            {"t": 0.7, "Hip": [8, 4, 4], "Chest": [6, 0, 0], "Head": [-4, 0, 0], "UpperArm_R": [-8, 0, 0], "Forearm_R": [-4, 0, 0], "Hand_R": [-2, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [4, 0, 0], "Forearm_L": [6, 0, 0], "Hand_L": [6, 0, 0], "Weapon_Front": [12, 0, 0], "Thigh_R": [-10, 0, 0], "Shin_R": [8, 0, 0], "Foot_R": [2, 0, 0], "Thigh_L": [8, 0, 0], "Shin_L": [8, 0, 0], "Foot_L": [4, 0, 0], "vfx": {"fx_spark": {"pos": [365, 320], "rot": 25, "scale": 0.55, "alpha": 0.55}}},
            {"t": 0.86, "Hip": [0, 0, 0], "Chest": [0, 0, 0], "Head": [0, 0, 0], "UpperArm_R": [0, 0, 0], "Forearm_R": [0, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [0, 0, 0], "Forearm_L": [0, 0, 0], "Hand_L": [0, 0, 0], "Weapon_Front": [0, 0, 0], "Thigh_R": [0, 0, 0], "Shin_R": [0, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [0, 0, 0], "Shin_L": [0, 0, 0], "Foot_L": [0, 0, 0]}
        ]
    },
    "hurt": {
        "grid": [2, 2], "length": 0.55, "loop": False,
        "frames": [
            {"t": 0.0, "Hip": [-10, 4, -6], "Chest": [-12, 0, 0], "Head": [-14, 0, 0], "UpperArm_R": [14, 0, 0], "Forearm_R": [10, 0, 0], "Hand_R": [6, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [14, 0, 0], "Forearm_L": [-8, 0, 0], "Hand_L": [-6, 0, 0], "Weapon_Front": [-8, 0, 0], "Thigh_R": [8, 0, 0], "Shin_R": [6, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-6, 0, 0], "Shin_L": [8, 0, 0], "Foot_L": [0, 0, 0], "vfx": {"fx_spark": {"pos": [254, 214], "rot": -15, "scale": 0.68, "alpha": 0.9}}},
            {"t": 0.15, "Hip": [-16, 8, -8], "Chest": [-14, 0, 0], "Head": [-18, 0, 0], "UpperArm_R": [20, 0, 0], "Forearm_R": [14, 0, 0], "Hand_R": [8, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [20, 0, 0], "Forearm_L": [-12, 0, 0], "Hand_L": [-10, 0, 0], "Weapon_Front": [-12, 0, 0], "Thigh_R": [12, 0, 0], "Shin_R": [10, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-10, 0, 0], "Shin_L": [12, 0, 0], "Foot_L": [0, 0, 0]},
            {"t": 0.32, "Hip": [-8, 4, -4], "Chest": [-6, 0, 0], "Head": [-8, 0, 0], "UpperArm_R": [8, 0, 0], "Forearm_R": [6, 0, 0], "Hand_R": [4, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [8, 0, 0], "Forearm_L": [-4, 0, 0], "Hand_L": [-4, 0, 0], "Weapon_Front": [-4, 0, 0], "Thigh_R": [6, 0, 0], "Shin_R": [4, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-4, 0, 0], "Shin_L": [6, 0, 0], "Foot_L": [0, 0, 0]},
            {"t": 0.48, "Hip": [0, 0, 0], "Chest": [0, 0, 0], "Head": [0, 0, 0], "UpperArm_R": [0, 0, 0], "Forearm_R": [0, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [0, 0, 0], "Forearm_L": [0, 0, 0], "Hand_L": [0, 0, 0], "Weapon_Front": [0, 0, 0], "Thigh_R": [0, 0, 0], "Shin_R": [0, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [0, 0, 0], "Shin_L": [0, 0, 0], "Foot_L": [0, 0, 0]}
        ]
    },
    "death": {
        "grid": [2, 3], "length": 1.1, "loop": False,
        "frames": [
            {"t": 0.0, "Hip": [-10, 6, -6], "Chest": [-12, 0, 0], "Head": [-14, 0, 0], "UpperArm_R": [14, 0, 0], "Forearm_R": [8, 0, 0], "Hand_R": [6, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [14, 0, 0], "Forearm_L": [-8, 0, 0], "Hand_L": [-6, 0, 0], "Weapon_Front": [-8, 0, 0], "Thigh_R": [10, 0, 0], "Shin_R": [8, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-8, 0, 0], "Shin_L": [10, 0, 0], "Foot_L": [0, 0, 0], "vfx": {"fx_spark": {"pos": [254, 212], "rot": 0, "scale": 0.72, "alpha": 0.92}}},
            {"t": 0.22, "Hip": [-6, 30, 14], "Chest": [16, 0, 0], "Head": [12, 0, 0], "UpperArm_R": [24, 0, 0], "Forearm_R": [12, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-16, 0, 0], "Forearm_L": [-10, 0, 0], "Hand_L": [-12, 0, 0], "Weapon_Front": [-16, 0, 0], "Thigh_R": [-42, 0, 0], "Shin_R": [64, 0, 0], "Foot_R": [12, 0, 0], "Thigh_L": [-36, 0, 0], "Shin_L": [58, 0, 0], "Foot_L": [10, 0, 0]},
            {"t": 0.45, "Hip": [-4, 56, 30], "Chest": [24, 0, 0], "Head": [18, 0, 0], "UpperArm_R": [36, 0, 0], "Forearm_R": [18, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-32, 0, 0], "Forearm_L": [-16, 0, 0], "Hand_L": [-20, 0, 0], "Weapon_Front": [-26, 0, 0], "Thigh_R": [-66, 0, 0], "Shin_R": [90, 0, 0], "Foot_R": [16, 0, 0], "Thigh_L": [-60, 0, 0], "Shin_L": [84, 0, 0], "Foot_L": [14, 0, 0], "vfx": {"fx_dust": {"pos": [256, 422], "rot": 0, "scale": 0.85, "alpha": 0.82}}},
            {"t": 0.68, "Hip": [-2, 68, 40], "Chest": [28, 0, 0], "Head": [22, 0, 0], "UpperArm_R": [42, 0, 0], "Forearm_R": [20, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-40, 0, 0], "Forearm_L": [-20, 0, 0], "Hand_L": [-24, 0, 0], "Weapon_Front": [-32, 0, 0], "Thigh_R": [-76, 0, 0], "Shin_R": [100, 0, 0], "Foot_R": [18, 0, 0], "Thigh_L": [-70, 0, 0], "Shin_L": [94, 0, 0], "Foot_L": [16, 0, 0], "vfx": {"fx_dust": {"pos": [264, 424], "rot": 0, "scale": 0.9, "alpha": 0.65}}, "modulate_a": 0.88},
            {"t": 0.88, "Hip": [0, 72, 44], "Chest": [30, 0, 0], "Head": [24, 0, 0], "UpperArm_R": [44, 0, 0], "Forearm_R": [22, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-42, 0, 0], "Forearm_L": [-22, 0, 0], "Hand_L": [-26, 0, 0], "Weapon_Front": [-34, 0, 0], "Thigh_R": [-78, 0, 0], "Shin_R": [102, 0, 0], "Foot_R": [18, 0, 0], "Thigh_L": [-72, 0, 0], "Shin_L": [96, 0, 0], "Foot_L": [16, 0, 0], "vfx": {"fx_dust": {"pos": [266, 424], "rot": 0, "scale": 0.75, "alpha": 0.45}}, "modulate_a": 0.52},
            {"t": 1.05, "Hip": [0, 74, 46], "Chest": [30, 0, 0], "Head": [24, 0, 0], "UpperArm_R": [44, 0, 0], "Forearm_R": [22, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-42, 0, 0], "Forearm_L": [-22, 0, 0], "Hand_L": [-26, 0, 0], "Weapon_Front": [-34, 0, 0], "Thigh_R": [-78, 0, 0], "Shin_R": [102, 0, 0], "Foot_R": [18, 0, 0], "Thigh_L": [-72, 0, 0], "Shin_L": [96, 0, 0], "Foot_L": [16, 0, 0], "modulate_a": 0.22}
        ]
    }
}

def compute_world_transforms(frame_pose, bones):
    world = {}
    for b in bones:
        name = b["name"]
        parent = b["parent"]
        val = frame_pose.get(name, [0, 0, 0])
        if name == "Hip":
            dx, dy, drot = val[0], val[1], val[2]
        else:
            drot, dx, dy = val[0], val[1], val[2]
        lx = b["rest_x"] + dx
        ly = b["rest_y"] + dy
        lrot = b["rest_rot"] + drot
        if not parent:
            wx, wy, wrot = lx, ly, lrot
        else:
            p = world[parent]
            rad = math.radians(p["wrot"])
            ca, sa = math.cos(rad), math.sin(rad)
            wx = p["wx"] + lx * ca - ly * sa
            wy = p["wy"] + lx * sa + ly * ca
            wrot = p["wrot"] + lrot
        world[name] = {"wx": wx, "wy": wy, "wrot": wrot, "tx": wx, "ty": wy}
    return world

def paste_rotated_part(canvas, part_img, wx, wy, wrot, pivot_x, pivot_y, scale=1.0, alpha=1.0):
    if scale != 1.0:
        nw = max(1, int(round(part_img.width * scale)))
        nh = max(1, int(round(part_img.height * scale)))
        part_img = part_img.resize((nw, nh), Image.Resampling.LANCZOS)
        pivot_x *= scale
        pivot_y *= scale

    if alpha < 1.0:
        part_img = part_img.copy()
        pa = np.array(part_img)
        pa[:, :, 3] = (pa[:, :, 3].astype(np.float32) * alpha).astype(np.uint8)
        part_img = Image.fromarray(pa, "RGBA")

    rot_img = part_img.rotate(-wrot, expand=True, resample=Image.Resampling.BICUBIC)
    rad = math.radians(-wrot)
    ca, sa = math.cos(rad), math.sin(rad)
    cx, cy = part_img.width / 2.0, part_img.height / 2.0
    dx = pivot_x - cx
    dy = pivot_y - cy
    rx = dx * ca - dy * sa
    ry = dx * sa + dy * ca
    paste_x = int(round(wx - (rot_img.width / 2.0 + rx)))
    paste_y = int(round(wy - (rot_img.height / 2.0 + ry)))
    canvas.alpha_composite(rot_img, (paste_x, paste_y))

def render_w002_pose(frame_pose, team_name="team_blue", show_weapon_front=True, show_weapon_back=False, canvas_size=512):
    canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    world = compute_world_transforms(frame_pose, BONES_W002)
    mod_a = frame_pose.get("modulate_a", 1.0)
    sorted_bones = sorted(BONES_W002, key=lambda b: b["z_index"])

    for b in sorted_bones:
        bname = b["name"]
        if bname == "Weapon_Back" and not show_weapon_back:
            continue
        if bname == "Weapon_Front" and not show_weapon_front:
            continue

        w = world[bname]
        if b["is_weapon"]:
            part_img = w002_anim_0 if bname == "Weapon_Front" else w002_offhand
        else:
            part_img = TEAM_PARTS[team_name][b["part"]]

        paste_rotated_part(canvas, part_img, w["wx"], w["wy"], w["wrot"], b["pivot_x"], b["pivot_y"], scale=1.0, alpha=mod_a)

    # VFX
    vfx_dict = frame_pose.get("vfx", {})
    for fx_name, fx_cfg in vfx_dict.items():
        if fx_name not in VFX_PARTS:
            continue
        fx_im = VFX_PARTS[fx_name]
        pos = fx_cfg.get("pos", [256, 256])
        rot = fx_cfg.get("rot", 0)
        sc = fx_cfg.get("scale", 1.0)
        al = fx_cfg.get("alpha", 1.0)
        paste_rotated_part(canvas, fx_im, pos[0], pos[1], rot, fx_im.width / 2.0, fx_im.height / 2.0, scale=sc, alpha=al)

    return canvas, world

# 2. Build QC Audit Board
print("=== 2. Building W002 (Cấp N - Static Weapon) Audit Board ===")
board_w, board_h = 1860, 960
audit_im = Image.new("RGBA", (board_w, board_h), (16, 19, 26, 255))
audit_draw = ImageDraw.Draw(audit_im, "RGBA")

try:
    font_title = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 16)
    font_sub = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 12)
except Exception:
    font_title = ImageFont.load_default()
    font_sub = ImageFont.load_default()

team_display = [
    ("team_blue", "ĐỘI 1: XANH + W002 NỎ (Tĩnh)", (59, 130, 246, 255), False),
    ("team_red", "ĐỘI 2: ĐỎ + NỎ + ĐOẢN ĐAO", (239, 68, 68, 255), True),
    ("team_green", "ĐỘI 3: XANH LÁ + W002 NỎ (Tĩnh)", (34, 197, 94, 255), False),
    ("team_amber", "ĐỘI 4: VÀNG + W002 NỎ (Tĩnh)", (245, 158, 11, 255), False),
]

for idx, (t_key, t_label, t_col, dual_w) in enumerate(team_display):
    ox = 12 + idx * 345
    oy = 12
    audit_draw.rectangle([ox, oy, ox + 335, oy + 450], fill=(26, 31, 42, 255), outline=t_col, width=2)
    t_pose_im, _ = render_w002_pose({}, team_name=t_key, show_weapon_front=True, show_weapon_back=dual_w, canvas_size=512)
    t_thumb = t_pose_im.resize((330, 330), Image.Resampling.LANCZOS)
    audit_im.alpha_composite(t_thumb, (ox + 2, oy + 46))
    audit_draw.text((ox + 12, oy + 10), t_label, fill=t_col, font=font_title)
    sub_txt = "Cấp N — 1 Ảnh Tĩnh (weapon_anim_0)" if not dual_w else "Cấp N — Nỏ Tĩnh + Đoản Đao Phụ"
    audit_draw.text((ox + 12, oy + 28), f"{sub_txt} | edge_clip=0px", fill=(210, 220, 235, 255), font=font_sub)

# Panel 5 on Top Row: Card Cover (Step 2 for N/R weapons)
ox5 = 12 + 4 * 345
audit_draw.rectangle([ox5, 12, board_w - 12, 462], fill=(26, 31, 42, 255), outline=(245, 158, 11, 255), width=2)
audit_draw.text((ox5 + 12, 20), "BƯỚC 2: ẢNH BÌA CARD (884x632 RGB — Từ Ảnh Ref)", fill=(252, 211, 77, 255), font=font_title)
card_prev = Image.open(W002_CARD_PNG).convert("RGBA").resize((436, 312), Image.Resampling.LANCZOS)
audit_im.alpha_composite(card_prev, (ox5 + 14, 48))
audit_draw.rectangle([ox5 + 14, 48, ox5 + 14 + 436, 48 + 312], outline=(245, 158, 11, 220), width=1)
audit_draw.text((ox5 + 14, 370), "884x632 PNG & 354x253 WebP (Đồng nhất 100% với Ảnh Ref)", fill=(252, 211, 77, 255), font=font_sub)
audit_draw.text((ox5 + 14, 392), f"Grip 1 (Đỏ): ({W002_G1_X}, {W002_G1_Y}) | Grip 2 (Xanh): ({W002_G2_X}, {W002_G2_Y})", fill=(220, 230, 245, 255), font=font_sub)
audit_draw.text((ox5 + 14, 414), "Flow Cấp N/R: 1. Ảnh Vũ Khí Tĩnh (weapon_anim_0) -> 2. Ảnh Bìa Card", fill=(130, 235, 165, 255), font=font_sub)

# Bottom Row: Step 1 Static Weapon (weapon_anim_0 / weapon_main), Offhand Dagger, and Combat VFX
bx_w = 12
by_w = 478
audit_draw.rectangle([bx_w, by_w, bx_w + 440, board_h - 12], fill=(26, 31, 42, 255), outline=(245, 158, 11, 255), width=2)
audit_draw.text((bx_w + 14, by_w + 12), f"BƯỚC 1: VŨ KHÍ TĨNH CẤP N ({w002_main.width}x{w002_main.height} — 0px Pad)", fill=(252, 211, 77, 255), font=font_title)
audit_draw.text((bx_w + 14, by_w + 32), "weapon_main.png = weapon_anim_0.png (Không vẽ đạn, Không animation)", fill=(130, 235, 165, 255), font=font_sub)
wx_p = bx_w + (440 - w002_main.width) // 2
wy_p = by_w + 90
audit_im.alpha_composite(w002_main, (wx_p, wy_p))
audit_draw.rectangle([wx_p, wy_p, wx_p + w002_main.width, wy_p + w002_main.height], outline=(90, 220, 135, 180), width=1)
g1x, g1y = wx_p + int(W002_G1_X), wy_p + int(W002_G1_Y)
g2x, g2y = wx_p + int(W002_G2_X), wy_p + int(W002_G2_Y)
audit_draw.ellipse([g1x - 6, g1y - 6, g1x + 6, g1y + 6], fill=(240, 50, 50, 255), outline=(255, 255, 255, 255), width=2)
audit_draw.ellipse([g2x - 6, g2y - 6, g2x + 6, g2y + 6], fill=(40, 210, 255, 255), outline=(255, 255, 255, 255), width=2)
audit_draw.text((bx_w + 14, by_w + 260), f"Vũ khí phụ (weapon_offhand.png — {w002_offhand.width}x{w002_offhand.height}):", fill=(252, 211, 77, 255), font=font_sub)
audit_im.alpha_composite(w002_offhand, (bx_w + 160, by_w + 290))

vfx_display = [
    ("fx_slash", "VFX 1: fx_slash.png (Luồng Gió Bắn Nỏ)"),
    ("fx_slash_heavy", "VFX 2: fx_slash_heavy.png (Tiễn Xuyên Tâm)"),
    ("fx_spark", "VFX 3: fx_spark.png (Tia Lửa Nảy Cò)"),
    ("fx_dust", "VFX 4: fx_dust.png (Bụi Đất Khi Quỳ Bắn / Ngã)"),
]
for idx, (fx_k, fx_title) in enumerate(vfx_display):
    ax = 468 + idx * 345
    ay = 478
    audit_draw.rectangle([ax, ay, ax + 333, board_h - 12], fill=(22, 26, 36, 255), outline=(56, 189, 248, 200), width=1)
    audit_draw.text((ax + 10, ay + 12), fx_title, fill=(252, 211, 77, 255), font=font_sub)
    fx_im = VFX_PARTS[fx_k]
    audit_draw.text((ax + 10, ay + 32), f"Size: {fx_im.width}x{fx_im.height} | Cấp N: Vũ khí tĩnh weapon_anim_0", fill=(130, 235, 165, 255), font=font_sub)
    audit_im.alpha_composite(fx_im, (ax + (333 - fx_im.width) // 2, ay + 110))

w002_audit_path = os.path.join(W002_QC_DIR, "w002_weapon_and_aura_audit.png")
audit_im.save(w002_audit_path)
shutil.copyfile(w002_audit_path, os.path.join(ARTIFACT_DIR, "w002_weapon_and_aura_audit.png"))
print("Saved W002 Audit Board ->", w002_audit_path)

# 3. Overview Board for 6 Actions
print("=== 3. Building All 6 Actions Overview Board for W002 ===")
ov_w, ov_h = 3 * 560 + 24, 2 * 560 + 24
ov_im = Image.new("RGBA", (ov_w, ov_h), (16, 19, 26, 255))
ov_draw = ImageDraw.Draw(ov_im)

action_order = ["idle", "walk", "attack", "cast", "hurt", "death"]
team_cycle = ["team_blue", "team_red", "team_green", "team_amber", "team_blue", "team_red"]

for a_idx, act_name in enumerate(action_order):
    act = ACTIONS_W002[act_name]
    rows, cols = act["grid"]
    frames = act["frames"]
    ar, ac = divmod(a_idx, 3)
    bx = 12 + ac * 560
    by = 12 + ar * 560
    ov_draw.rectangle([bx, by, bx + 544, by + 544], fill=(24, 28, 38, 255), outline=(56, 189, 248, 180), width=1)

    thumb_size = 240 if cols == 2 else 166
    grid_w = cols * thumb_size
    grid_h = rows * thumb_size
    gx0 = bx + (544 - grid_w) // 2
    gy0 = by + 36 + (500 - grid_h) // 2

    t_name = team_cycle[a_idx]
    ov_draw.text((bx + 14, by + 12), f"W002 Action: {act_name.upper()} ({len(frames)}f | {t_name} | Cấp N Vũ Khí Tĩnh)", fill=(56, 189, 248, 255), font=font_title)

    for f_idx, f in enumerate(frames):
        fr, fc = divmod(f_idx, cols)
        px = gx0 + fc * thumb_size
        py = gy0 + fr * thumb_size
        f_im, _ = render_w002_pose(f, team_name=t_name, show_weapon_front=True, show_weapon_back=False, canvas_size=512)
        f_thumb = f_im.resize((thumb_size, thumb_size), Image.Resampling.LANCZOS)
        ov_im.alpha_composite(f_thumb, (px, py))
        ov_draw.rectangle([px, py, px + thumb_size, py + thumb_size], outline=(40, 50, 68, 180), width=1)

ov_path = os.path.join(W002_QC_DIR, "w002_sticker_all_6_actions_overview.png")
ov_im.save(ov_path)
shutil.copyfile(ov_path, os.path.join(ARTIFACT_DIR, "w002_sticker_all_6_actions_overview.png"))
print("Saved W002 6-Action Overview ->", ov_path)

# 4. Generate Godot 4 Scene & Script (.tscn & .gd)
print("=== 4. Building Godot 4 Scene & Script for W002 ===")

def build_godot_tscn(weapon_id="w002", weapon_name="C002_NoThuCamLang", tscn_prefix="c002_no_thu_cam_lang"):
    ext_resources = []
    sub_resources = []
    nodes = []

    ext_resources.append(f'[ext_resource type="Script" path="res://assets/weapons/{weapon_id}_no_thu_cam_lang/godot/{tscn_prefix}.gd" id="1_script"]')
    res_id = 2
    part_res_map = {}

    for p in STICKER_PARTS:
        part_res_map[p] = f"{res_id}_{p}"
        ext_resources.append(f'[ext_resource type="Texture2D" path="res://assets/sticker_hero/godot/parts/team_blue/{p}.png" id="{res_id}_{p}"]')
        res_id += 1

    for wp in ["weapon_main", "weapon_offhand", "weapon_anim_0"]:
        part_res_map[wp] = f"{res_id}_{wp}"
        ext_resources.append(f'[ext_resource type="Texture2D" path="res://assets/weapons/{weapon_id}_no_thu_cam_lang/parts/{wp}.png" id="{res_id}_{wp}"]')
        res_id += 1

    for fx in ["fx_slash", "fx_slash_heavy", "fx_spark", "fx_dust"]:
        part_res_map[fx] = f"{res_id}_{fx}"
        ext_resources.append(f'[ext_resource type="Texture2D" path="res://assets/weapons/{weapon_id}_no_thu_cam_lang/parts/{fx}.png" id="{res_id}_{fx}"]')
        res_id += 1

    anim_sub_ids = []
    bone_paths = {}
    for b in BONES_W002:
        bone_paths[b["name"]] = bone_paths[b["parent"]] + "/" + b["name"] if b["parent"] else f"Skeleton2D/{b['name']}"

    for act_name, act in ACTIONS_W002.items():
        frames = act["frames"]
        sub_id = f"Animation_{act_name}"
        anim_sub_ids.append((act_name, sub_id))

        times = [f"{f['t']:.2f}" for f in frames]
        times_str = ", ".join(times)
        transitions = ", ".join(["1"] * len(frames))

        anim_txt = f"""[sub_resource type="Animation" id="{sub_id}"]
resource_name = "{act_name}"
length = {act['length']:.2f}
loop_mode = {1 if act['loop'] else 0}"""

        track_idx = 0
        for b in BONES_W002:
            bname = b["name"]
            bpath = bone_paths[bname]

            rots = []
            pos = []
            for f in frames:
                val = f.get(bname, [0, 0, 0])
                if bname == "Hip":
                    dx, dy, drot = val[0], val[1], val[2]
                else:
                    drot, dx, dy = val[0], val[1], val[2]
                rad = math.radians(b["rest_rot"] + drot)
                rots.append(f"{rad:.4f}")
                pos.append(f"Vector2({b['rest_x'] + dx:.1f}, {b['rest_y'] + dy:.1f})")

            anim_txt += f"""
tracks/{track_idx}/type = "value"
tracks/{track_idx}/imported = false
tracks/{track_idx}/enabled = true
tracks/{track_idx}/path = NodePath("{bpath}:rotation")
tracks/{track_idx}/interp = 1
tracks/{track_idx}/loop_wrap = true
tracks/{track_idx}/keys = {{
"times": PackedFloat32Array({times_str}),
"transitions": PackedFloat32Array({transitions}),
"update": 0,
"values": [{', '.join(rots)}]
}}"""
            track_idx += 1

            anim_txt += f"""
tracks/{track_idx}/type = "value"
tracks/{track_idx}/imported = false
tracks/{track_idx}/enabled = true
tracks/{track_idx}/path = NodePath("{bpath}:position")
tracks/{track_idx}/interp = 1
tracks/{track_idx}/loop_wrap = true
tracks/{track_idx}/keys = {{
"times": PackedFloat32Array({times_str}),
"transitions": PackedFloat32Array({transitions}),
"update": 0,
"values": [{', '.join(pos)}]
}}"""
            track_idx += 1

        sub_resources.append(anim_txt)

    lib_data = ",\n".join([f'"{name}": SubResource("{sub_id}")' for name, sub_id in anim_sub_ids])
    sub_resources.append(f"""[sub_resource type="AnimationLibrary" id="AnimationLibrary_w002"]
_data = {{
{lib_data}
}}""")

    nodes.append(f'[node name="{weapon_name}" type="Node2D"]')
    nodes.append('script = ExtResource("1_script")')
    nodes.append("")
    nodes.append('[node name="Skeleton2D" type="Skeleton2D" parent="."]')
    nodes.append("")

    for b in BONES_W002:
        bname = b["name"]
        parent_path = bone_paths[b["parent"]] if b["parent"] else "Skeleton2D"
        rad = math.radians(b["rest_rot"])
        ca, sa = math.cos(rad), math.sin(rad)

        tx = 0.0
        ty = 42.0
        if b.get("tip_child") and b["tip_child"] in BONE_MAP_W002:
            tx = BONE_MAP_W002[b["tip_child"]]["rest_x"]
            ty = BONE_MAP_W002[b["tip_child"]]["rest_y"]
        elif b.get("tip_offset"):
            tx = b["tip_offset"][0]
            ty = b["tip_offset"][1]

        bLen = max(8.0, math.hypot(tx, ty))
        bAng = math.atan2(ty, tx)

        nodes.append(f'[node name="{bname}" type="Bone2D" parent="{parent_path}"]')
        nodes.append(f'position = Vector2({b["rest_x"]:.1f}, {b["rest_y"]:.1f})')
        nodes.append(f'rotation = {rad:.4f}')
        nodes.append(f'rest = Transform2D({ca:.4f}, {sa:.4f}, {-sa:.4f}, {ca:.4f}, {b["rest_x"]:.1f}, {b["rest_y"]:.1f})')
        nodes.append('auto_calculate_length_and_angle = false')
        nodes.append(f'length = {bLen:.1f}')
        nodes.append(f'bone_angle = {bAng:.4f}')
        if b["is_weapon"]:
            nodes.append(f'metadata/grip1 = Vector2({b["grip1_x"]:.1f}, {b["grip1_y"]:.1f})')
            nodes.append(f'metadata/grip2 = Vector2({b["grip2_x"]:.1f}, {b["grip2_y"]:.1f})')
        nodes.append("")

        nodes.append(f'[node name="Sprite" type="Sprite2D" parent="{bone_paths[bname]}"]')
        if bname == "Weapon_Back":
            nodes.append('visible = false')
        nodes.append(f'z_index = {b["z_index"]}')
        nodes.append('z_as_relative = false')
        nodes.append(f'texture = ExtResource("{part_res_map[b["part"]]}")')
        nodes.append(f'offset = Vector2({b["offset_x"]:.2f}, {b["offset_y"]:.2f})')
        nodes.append("")

    nodes.append('[node name="VFXLayer" type="Node2D" parent="."]')
    nodes.append('z_index = 20')
    nodes.append('z_as_relative = false')
    nodes.append("")
    for fx in ["fx_slash", "fx_slash_heavy", "fx_spark", "fx_dust"]:
        nodes.append(f'[node name="{fx}" type="Sprite2D" parent="VFXLayer"]')
        nodes.append('visible = false')
        nodes.append('position = Vector2(256, 256)')
        nodes.append(f'texture = ExtResource("{part_res_map[fx]}")')
        nodes.append("")

    nodes.append('[node name="AnimationPlayer" type="AnimationPlayer" parent="."]')
    nodes.append('libraries = {')
    nodes.append('"": SubResource("AnimationLibrary_w002")')
    nodes.append('}')
    nodes.append('autoplay = "idle"')

    total_steps = len(ext_resources) + len(sub_resources)
    header = f'[gd_scene load_steps={total_steps + 1} format=3 uid="uid://c002nothucamlang"]\n\n'
    return header + "\n".join(ext_resources) + "\n\n" + "\n\n".join(sub_resources) + "\n\n" + "\n".join(nodes)

tscn_content = build_godot_tscn()
tscn_path = os.path.join(W002_GODOT_DIR, "c002_no_thu_cam_lang.tscn")
with open(tscn_path, "w", encoding="utf-8") as f:
    f.write(tscn_content)
print("Saved Godot TSCN ->", tscn_path)

gd_script = """extends Node2D

@onready var anim_player: AnimationPlayer = $AnimationPlayer
@onready var skeleton: Skeleton2D = $Skeleton2D
@onready var weapon_front: Bone2D = $Skeleton2D/Hip/Chest/UpperArm_L/Forearm_L/Hand_L/Weapon_Front
@onready var weapon_back: Bone2D = $Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Hand_R/Weapon_Back

var current_team: String = "team_blue"

func _ready() -> void:
	play_action("idle")

func play_action(action_name: String) -> void:
	if anim_player.has_animation(action_name):
		anim_player.play(action_name)

func set_team_color(team_key: String) -> void:
	current_team = team_key
	var base_path := "res://assets/sticker_hero/godot/parts/" + team_key + "/"
	for bone in skeleton.get_children():
		_update_bone_textures_recursive(bone, base_path)

func _update_bone_textures_recursive(node: Node, base_path: String) -> void:
	if node is Bone2D and not node.name.begins_with("Weapon"):
		var sprite := node.get_node_or_null("Sprite") as Sprite2D
		if sprite:
			var part_name: String = node.name.to_snake_case()
			var tex_path := base_path + part_name + ".png"
			if ResourceLoader.exists(tex_path):
				sprite.texture = load(tex_path)
	for child in node.get_children():
		_update_bone_textures_recursive(child, base_path)

func toggle_dual_wield(enabled: bool) -> void:
	if weapon_back:
		var sp := weapon_back.get_node_or_null("Sprite") as Sprite2D
		if sp:
			sp.visible = enabled
"""

gd_path = os.path.join(W002_GODOT_DIR, "c002_no_thu_cam_lang.gd")
with open(gd_path, "w", encoding="utf-8") as f:
    f.write(gd_script)
print("Saved Godot GD Script ->", gd_path)

# 5. Pack data into JSON for HTML Editor (Cấp N: aura_default=False, only weapon_anim_0)
def b64_png(path):
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")

w002_pack = {
    "id": "w002",
    "name": "W002 — Nỏ Câm Lặng (Cấp N — Vũ Khí Tĩnh)",
    "tscn_name": "c002_no_thu_cam_lang.tscn",
    "node_name": "C002_NoThuCamLang",
    "aura_default": False,
    "card_b64": b64_png(W002_CARD_PNG),
    "bones": BONES_W002,
    "actions": ACTIONS_W002,
    "images": {
        "weapon_main": b64_png(os.path.join(W002_PARTS_DIR, "weapon_main.png")),
        "weapon_offhand": b64_png(os.path.join(W002_PARTS_DIR, "weapon_offhand.png")),
        "weapon_anim_0": b64_png(os.path.join(W002_PARTS_DIR, "weapon_anim_0.png")),
        "fx_slash": b64_png(os.path.join(W002_PARTS_DIR, "fx_slash.png")),
        "fx_slash_heavy": b64_png(os.path.join(W002_PARTS_DIR, "fx_slash_heavy.png")),
        "fx_spark": b64_png(os.path.join(W002_PARTS_DIR, "fx_spark.png")),
        "fx_dust": b64_png(os.path.join(W002_PARTS_DIR, "fx_dust.png")),
    }
}

# 6. Update assets/sticker_weapon_editor.html with updated W002_PACK
editor_path = "/Users/dochung/Desktop/card_g/assets/sticker_weapon_editor.html"
with open(editor_path, "r", encoding="utf-8") as f:
    editor_html = f.read()

w002_json_str = json.dumps(w002_pack)
w002_line = f"const W002_PACK = {w002_json_str};\n"
if "const W002_PACK =" in editor_html:
    editor_html = re.sub(r"const W002_PACK = .*?;\n", lambda _: w002_line, editor_html, count=1)

with open(editor_path, "w", encoding="utf-8") as f:
    f.write(editor_html)

w002_editor_path = os.path.join(W002_DIR, "w002_editor.html")
with open(w002_editor_path, "w", encoding="utf-8") as f:
    f.write(editor_html)

print("Saved Multi-Weapon Editor ->", editor_path, "and", w002_editor_path)
print("=== ALL W002 BUILD STEPS COMPLETE! ===")
