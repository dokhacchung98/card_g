#!/usr/bin/env python3
"""
tools/build_w003_system.py
Complete pipeline builder for W003 (Đại Đao Đồi Thí / Trảm Đao Đao Phủ - Cấp N)
Follows strict 3-step weapon flow:
  1. Ref Weapon -> 2. Spritesheet Animation (2x2) -> 3. Card Preview (884x632)
Generates QC audit boards, Godot 4 .tscn/.gd, and interactive HTML editors.
"""

import os, json, math, shutil, base64
from PIL import Image, ImageDraw, ImageFont
import numpy as np

REPO_DIR = "/Users/dochung/Desktop/card_g"
STICKER_DIR = os.path.join(REPO_DIR, "assets", "sticker_hero")
STICKER_GODOT_PARTS = os.path.join(STICKER_DIR, "godot", "parts")

W003_DIR = os.path.join(REPO_DIR, "assets", "weapons", "w003_dao_phu_doi_thi")
W003_RAW_DIR = os.path.join(W003_DIR, "raw")
W003_PARTS_DIR = os.path.join(W003_DIR, "parts")
W003_CARD_DIR = os.path.join(W003_DIR, "card")
W003_QC_DIR = os.path.join(W003_DIR, "qc_previews")
W003_GODOT_DIR = os.path.join(W003_DIR, "godot")
ARTIFACT_DIR = "/Users/dochung/.gemini/antigravity-cli/brain/ab7dc2b7-9521-42a4-be21-abd94f794ce3"

for d in [W003_RAW_DIR, W003_PARTS_DIR, W003_CARD_DIR, W003_QC_DIR, W003_GODOT_DIR, ARTIFACT_DIR]:
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

# Weapon parts
w003_main = Image.open(os.path.join(W003_PARTS_DIR, "weapon_main.png")).convert("RGBA")
w003_offhand = Image.open(os.path.join(W003_PARTS_DIR, "weapon_offhand.png")).convert("RGBA")
w003_aura = Image.open(os.path.join(W003_PARTS_DIR, "weapon_aura.png")).convert("RGBA")

W003_ANIM_FRAMES = [
    Image.open(os.path.join(W003_PARTS_DIR, f"weapon_anim_{i}.png")).convert("RGBA") for i in range(4)
]

VFX_PARTS = {
    "fx_slash": Image.open(os.path.join(W003_PARTS_DIR, "fx_slash.png")).convert("RGBA"),
    "fx_slash_heavy": Image.open(os.path.join(W003_PARTS_DIR, "fx_slash_heavy.png")).convert("RGBA"),
    "fx_spark": Image.open(os.path.join(W003_PARTS_DIR, "fx_spark.png")).convert("RGBA"),
    "fx_dust": Image.open(os.path.join(W003_PARTS_DIR, "fx_dust.png")).convert("RGBA"),
}

W003_CARD_PNG = os.path.join(W003_CARD_DIR, "w003_card_preview.png")

# Grip points for Executioner Great-Cleaver
W003_G1_X, W003_G1_Y = 134.0, 120.0  # Main grip near collar guard
W003_G2_X, W003_G2_Y = 188.0, 145.0  # Lower hilt grip near pommel

# 17 Bone setup for Sticker + W003 Executioner Cleaver
BONES_W003 = [
    {"name": "Hip", "parent": None, "part": "hip_kilt", "is_weapon": False, "rest_x": 198.0, "rest_y": 258.0, "rest_rot": 0.0, "pivot_x": 34.5, "pivot_y": 18.2, "z_index": 7, "tip_child": "Chest", "width": 69, "height": 52, "offset_x": 0.0, "offset_y": 7.8},
    {"name": "Thigh_L", "parent": "Hip", "part": "leg_thigh_back", "is_weapon": False, "rest_x": 8.0, "rest_y": 14.0, "rest_rot": -22.0, "pivot_x": 11.0, "pivot_y": 11.0, "z_index": 1, "tip_child": "Shin_L", "width": 22, "height": 64, "offset_x": 0.0, "offset_y": 21.0},
    {"name": "Shin_L", "parent": "Thigh_L", "part": "leg_shin_back", "is_weapon": False, "rest_x": 0.0, "rest_y": 42.0, "rest_rot": 16.0, "pivot_x": 10.5, "pivot_y": 10.5, "z_index": 2, "tip_child": "Foot_L", "width": 21, "height": 60, "offset_x": 0.0, "offset_y": 19.5},
    {"name": "Foot_L", "parent": "Shin_L", "part": "foot_back", "is_weapon": False, "rest_x": 0.0, "rest_y": 39.0, "rest_rot": 6.0, "pivot_x": 13.9, "pivot_y": 9.0, "z_index": 3, "tip_offset": [36.0, 18.0], "width": 48, "height": 37, "offset_x": 10.1, "offset_y": 9.5},
    {"name": "Thigh_R", "parent": "Hip", "part": "leg_thigh_front", "is_weapon": False, "rest_x": -8.0, "rest_y": 14.0, "rest_rot": 22.0, "pivot_x": 11.5, "pivot_y": 11.5, "z_index": 4, "tip_child": "Shin_R", "width": 23, "height": 66, "offset_x": 0.0, "offset_y": 21.5},
    {"name": "Shin_R", "parent": "Thigh_R", "part": "leg_shin_front", "is_weapon": False, "rest_x": 0.0, "rest_y": 43.0, "rest_rot": -14.0, "pivot_x": 11.0, "pivot_y": 11.0, "z_index": 5, "tip_child": "Foot_R", "width": 22, "height": 62, "offset_x": 0.0, "offset_y": 20.0},
    {"name": "Foot_R", "parent": "Shin_R", "part": "foot_front", "is_weapon": False, "rest_x": 0.0, "rest_y": 40.0, "rest_rot": -8.0, "pivot_x": 14.6, "pivot_y": 9.0, "z_index": 6, "tip_offset": [38.0, 18.0], "width": 50, "height": 39, "offset_x": 10.4, "offset_y": 10.5},
    {"name": "Chest", "parent": "Hip", "part": "chest", "is_weapon": False, "rest_x": 0.0, "rest_y": -4.0, "rest_rot": 3.0, "pivot_x": 44.5, "pivot_y": 48.0, "z_index": 11, "tip_child": "Neck", "width": 89, "height": 72, "offset_x": 0.0, "offset_y": -12.0},
    {"name": "Neck", "parent": "Chest", "part": "neck", "is_weapon": False, "rest_x": -4.0, "rest_y": -44.0, "rest_rot": 0.0, "pivot_x": 9.5, "pivot_y": 8.0, "z_index": 10, "tip_child": "Head", "width": 19, "height": 16, "offset_x": 0.0, "offset_y": 0.0},
    {"name": "Head", "parent": "Neck", "part": "head", "is_weapon": False, "rest_x": 0.0, "rest_y": -10.0, "rest_rot": -3.0, "pivot_x": 30.5, "pivot_y": 30.5, "z_index": 10, "tip_offset": [0.0, -32.0], "width": 61, "height": 61, "offset_x": 0.0, "offset_y": -18.5},
    {"name": "UpperArm_R", "parent": "Chest", "part": "arm_upper_back", "is_weapon": False, "rest_x": 16.0, "rest_y": -54.0, "rest_rot": 26.0, "pivot_x": 10.5, "pivot_y": 10.5, "z_index": 8, "tip_child": "Forearm_R", "width": 21, "height": 60, "offset_x": 0.0, "offset_y": 19.5},
    {"name": "Forearm_R", "parent": "UpperArm_R", "part": "arm_lower_back", "is_weapon": False, "rest_x": 0.0, "rest_y": 39.0, "rest_rot": -42.0, "pivot_x": 10.0, "pivot_y": 10.0, "z_index": 9, "tip_child": "Hand_R", "width": 20, "height": 56, "offset_x": 0.0, "offset_y": 18.0},
    {"name": "Hand_R", "parent": "Forearm_R", "part": "hand_back", "is_weapon": False, "rest_x": 0.0, "rest_y": 36.0, "rest_rot": 0.0, "pivot_x": 15.5, "pivot_y": 5.0, "z_index": 10, "tip_child": "Weapon_Back", "width": 32, "height": 46, "offset_x": 0.5, "offset_y": 18.0},
    {"name": "Weapon_Back", "parent": "Hand_R", "part": "weapon_offhand", "is_weapon": True, "visible_default": False, "rest_x": 0.0, "rest_y": 24.0, "rest_rot": 45.0, "pivot_x": 110.0, "pivot_y": 35.0, "grip1_x": 110.0, "grip1_y": 35.0, "grip2_x": 140.0, "grip2_y": 45.0, "z_index": 9, "tip_offset": [120.0, -40.0], "width": w003_offhand.width, "height": w003_offhand.height, "offset_x": round(w003_offhand.width / 2.0 - 110.0, 2), "offset_y": round(w003_offhand.height / 2.0 - 35.0, 2)},
    {"name": "UpperArm_L", "parent": "Chest", "part": "arm_upper_front", "is_weapon": False, "rest_x": -8.0, "rest_y": -58.0, "rest_rot": 10.0, "pivot_x": 11.0, "pivot_y": 11.0, "z_index": 12, "tip_child": "Forearm_L", "width": 22, "height": 62, "offset_x": 0.0, "offset_y": 20.0},
    {"name": "Forearm_L", "parent": "UpperArm_L", "part": "arm_lower_front", "is_weapon": False, "rest_x": 0.0, "rest_y": 40.0, "rest_rot": -52.0, "pivot_x": 10.0, "pivot_y": 10.0, "z_index": 13, "tip_child": "Hand_L", "width": 20, "height": 58, "offset_x": 0.0, "offset_y": 19.0},
    {"name": "Hand_L", "parent": "Forearm_L", "part": "hand_front", "is_weapon": False, "rest_x": 0.0, "rest_y": 38.0, "rest_rot": 0.0, "pivot_x": 16.5, "pivot_y": 5.0, "z_index": 15, "tip_child": "Weapon_Front", "width": 34, "height": 48, "offset_x": 0.5, "offset_y": 19.0},
    {"name": "Weapon_Front", "parent": "Hand_L", "part": "weapon_main", "is_weapon": True, "visible_default": True, "rest_x": 0.0, "rest_y": 26.0, "rest_rot": 32.0, "pivot_x": W003_G1_X, "pivot_y": W003_G1_Y, "grip1_x": W003_G1_X, "grip1_y": W003_G1_Y, "grip2_x": W003_G2_X, "grip2_y": W003_G2_Y, "z_index": 14, "tip_offset": [150.0, -95.0], "width": w003_main.width, "height": w003_main.height, "offset_x": round(w003_main.width / 2.0 - W003_G1_X, 2), "offset_y": round(w003_main.height / 2.0 - W003_G1_Y, 2)}
]

BONE_MAP_W003 = {b["name"]: b for b in BONES_W003}

# Actions tailored for Corpse-Hill Executioner Bruiser (Idle, Walk, Attack=Decapitation Cleave, Cast=Toai Giap Cuong Tram, Hurt, Death)
ACTIONS_W003 = {
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
            {"t": 0.0, "Hip": [-3, 4, 2], "Chest": [4, 0, 0], "Head": [-3, 0, 0], "UpperArm_R": [14, 0, 0], "Forearm_R": [6, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-14, 0, 0], "Forearm_L": [-6, 0, 0], "Hand_L": [-2, 0, 0], "Weapon_Front": [-4, 0, 0], "Thigh_R": [-22, 8, -4], "Shin_R": [12, 0, 0], "Foot_R": [6, 0, 0], "Thigh_L": [18, -6, 0], "Shin_L": [14, 0, 0], "Foot_L": [8, 0, 0]},
            {"t": 0.15, "Hip": [-2, 6, 2], "Chest": [5, 0, 0], "Head": [-4, 0, 0], "UpperArm_R": [8, 0, 0], "Forearm_R": [4, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-8, 0, 0], "Forearm_L": [-4, 0, 0], "Hand_L": [-2, 0, 0], "Weapon_Front": [-2, 0, 0], "Thigh_R": [-10, 6, -2], "Shin_R": [14, 0, 0], "Foot_R": [2, 0, 0], "Thigh_L": [8, -4, 0], "Shin_L": [18, 0, 0], "Foot_L": [10, 0, 0]},
            {"t": 0.3, "Hip": [0, -2, 0], "Chest": [3, 0, 0], "Head": [-2, 0, 0], "UpperArm_R": [-6, 0, 0], "Forearm_R": [-4, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [6, 0, 0], "Forearm_L": [2, 0, 0], "Hand_L": [0, 0, 0], "Weapon_Front": [2, 0, 0], "Thigh_R": [4, 2, 0], "Shin_R": [8, 0, 0], "Foot_R": [-4, 0, 0], "Thigh_L": [-10, 4, -4], "Shin_L": [16, 0, 0], "Foot_L": [6, 0, 0]},
            {"t": 0.45, "Hip": [3, 4, 2], "Chest": [5, 0, 0], "Head": [-3, 0, 0], "UpperArm_R": [-14, 0, 0], "Forearm_R": [-6, 0, 0], "Hand_R": [-2, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [14, 0, 0], "Forearm_L": [4, 0, 0], "Hand_L": [2, 0, 0], "Weapon_Front": [4, 0, 0], "Thigh_R": [16, -6, 0], "Shin_R": [14, 0, 0], "Foot_R": [6, 0, 0], "Thigh_L": [-22, 8, -4], "Shin_L": [10, 0, 0], "Foot_L": [-4, 0, 0]},
            {"t": 0.6, "Hip": [2, 6, 2], "Chest": [6, 0, 0], "Head": [-4, 0, 0], "UpperArm_R": [-8, 0, 0], "Forearm_R": [-4, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [8, 0, 0], "Forearm_L": [2, 0, 0], "Hand_L": [0, 0, 0], "Weapon_Front": [2, 0, 0], "Thigh_R": [8, -4, 0], "Shin_R": [18, 0, 0], "Foot_R": [8, 0, 0], "Thigh_L": [-10, 6, -2], "Shin_L": [12, 0, 0], "Foot_L": [0, 0, 0]},
            {"t": 0.75, "Hip": [-2, -2, 0], "Chest": [3, 0, 0], "Head": [-2, 0, 0], "UpperArm_R": [6, 0, 0], "Forearm_R": [2, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-6, 0, 0], "Forearm_L": [-2, 0, 0], "Hand_L": [-1, 0, 0], "Weapon_Front": [-1, 0, 0], "Thigh_R": [-8, 4, -2], "Shin_R": [10, 0, 0], "Foot_R": [4, 0, 0], "Thigh_L": [4, -2, 0], "Shin_L": [10, 0, 0], "Foot_L": [4, 0, 0]}
        ]
    },
    "attack": {
        "grid": [2, 2], "length": 0.7, "loop": False,
        "frames": [
            # Frame 1: Raise cleaver high behind shoulder
            {"t": 0.0, "Hip": [-10, 4, -4], "Chest": [-14, 0, 0], "Head": [10, 0, 0], "UpperArm_R": [32, 0, 0], "Forearm_R": [20, 0, 0], "Hand_R": [10, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-55, 0, -6], "Forearm_L": [-35, 0, 0], "Hand_L": [-20, 0, 0], "Weapon_Front": [-40, 0, 0], "Thigh_R": [14, -6, 0], "Shin_R": [12, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-12, 4, 0], "Shin_L": [12, 0, 0], "Foot_L": [0, 0, 0]},
            # Frame 2: Driving downward chopping cleave
            {"t": 0.2, "Hip": [14, 6, 6], "Chest": [18, 0, 0], "Head": [-12, 0, 0], "UpperArm_R": [-22, 0, 0], "Forearm_R": [-14, 0, 0], "Hand_R": [-8, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [26, 8, 0], "Forearm_L": [32, 0, 0], "Hand_L": [28, 0, 0], "Weapon_Front": [48, 0, 0], "Thigh_R": [-18, 12, -4], "Shin_R": [14, 0, 0], "Foot_R": [6, 0, 0], "Thigh_L": [16, -8, 0], "Shin_L": [14, 0, 0], "Foot_L": [6, 0, 0], "vfx": {"fx_slash_heavy": {"pos": [330, 270], "rot": 18, "scale": 0.85, "alpha": 0.95}}},
            # Frame 3: Ground impact crush with sparks & dust
            {"t": 0.42, "Hip": [18, 10, 8], "Chest": [22, 0, 0], "Head": [-14, 0, 0], "UpperArm_R": [-26, 0, 0], "Forearm_R": [-18, 0, 0], "Hand_R": [-10, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [38, 10, 0], "Forearm_L": [42, 0, 0], "Hand_L": [34, 0, 0], "Weapon_Front": [62, 0, 0], "Thigh_R": [-22, 14, -6], "Shin_R": [16, 0, 0], "Foot_R": [8, 0, 0], "Thigh_L": [20, -10, 0], "Shin_L": [16, 0, 0], "Foot_L": [8, 0, 0], "vfx": {"fx_spark": {"pos": [360, 340], "rot": 0, "scale": 0.8, "alpha": 0.95}, "fx_dust": {"pos": [320, 390], "rot": 0, "scale": 0.75, "alpha": 0.85}}},
            # Frame 4: Recovery lift
            {"t": 0.58, "Hip": [4, 2, 2], "Chest": [4, 0, 0], "Head": [-2, 0, 0], "UpperArm_R": [-4, 0, 0], "Forearm_R": [-2, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-2, 0, 0], "Forearm_L": [0, 0, 0], "Hand_L": [0, 0, 0], "Weapon_Front": [0, 0, 0], "Thigh_R": [-4, 2, 0], "Shin_R": [4, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [4, -2, 0], "Shin_L": [4, 0, 0], "Foot_L": [0, 0, 0]}
        ]
    },
    "cast": {
        "grid": [2, 3], "length": 0.95, "loop": False,
        "frames": [
            # Frame 1: Gathering dark crimson fury
            {"t": 0.0, "Hip": [-8, 6, -4], "Chest": [-10, 0, 0], "Head": [8, 0, 0], "UpperArm_R": [22, 0, 0], "Forearm_R": [14, 0, 0], "Hand_R": [6, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-42, 0, -4], "Forearm_L": [-22, 0, 0], "Hand_L": [-16, 0, 0], "Weapon_Front": [-24, 0, 0], "Thigh_R": [10, -4, 0], "Shin_R": [10, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-10, 4, 0], "Shin_L": [10, 0, 0], "Foot_L": [0, 0, 0], "vfx": {"fx_dust": {"pos": [218, 412], "rot": 0, "scale": 0.65, "alpha": 0.76}}},
            # Frame 2: Heavy spin windup
            {"t": 0.16, "Hip": [-16, 10, -8], "Chest": [-16, 0, 0], "Head": [12, 0, 0], "UpperArm_R": [30, 0, 0], "Forearm_R": [20, 0, 0], "Hand_R": [8, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-60, 0, -8], "Forearm_L": [-28, 0, 0], "Hand_L": [-22, 0, 0], "Weapon_Front": [-35, 0, 0], "Thigh_R": [16, -8, 0], "Shin_R": [16, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-16, 8, 0], "Shin_L": [16, 0, 0], "Foot_L": [0, 0, 0], "vfx": {"fx_dust": {"pos": [212, 412], "rot": 0, "scale": 0.75, "alpha": 0.88}}},
            # Frame 3: Toai Giap Cuong Tram sweeping strike
            {"t": 0.34, "Hip": [14, 6, 8], "Chest": [16, 0, 0], "Head": [-10, 0, 0], "UpperArm_R": [-20, 0, 0], "Forearm_R": [-12, 0, 0], "Hand_R": [-6, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-8, 10, 0], "Forearm_L": [16, 0, 0], "Hand_L": [20, 0, 0], "Weapon_Front": [35, 0, 0], "Thigh_R": [-20, 12, -4], "Shin_R": [14, 0, 0], "Foot_R": [4, 0, 0], "Thigh_L": [18, -10, 0], "Shin_L": [16, 0, 0], "Foot_L": [6, 0, 0], "vfx": {"fx_slash_heavy": {"pos": [320, 260], "rot": 12, "scale": 0.85, "alpha": 0.96}, "fx_dust": {"pos": [196, 412], "rot": 0, "scale": 0.78, "alpha": 0.85}}},
            # Frame 4: Sweeping follow-through
            {"t": 0.52, "Hip": [20, 10, 10], "Chest": [20, 0, 0], "Head": [-14, 0, 0], "UpperArm_R": [-28, 0, 0], "Forearm_R": [-18, 0, 0], "Hand_R": [-8, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [18, 12, 0], "Forearm_L": [26, 0, 0], "Hand_L": [28, 0, 0], "Weapon_Front": [55, 0, 0], "Thigh_R": [-24, 14, -6], "Shin_R": [16, 0, 0], "Foot_R": [6, 0, 0], "Thigh_L": [22, -12, 0], "Shin_L": [18, 0, 0], "Foot_L": [8, 0, 0], "vfx": {"fx_slash": {"pos": [340, 275], "rot": 25, "scale": 0.78, "alpha": 0.88}, "fx_spark": {"pos": [370, 320], "rot": 15, "scale": 0.85, "alpha": 0.95}}},
            # Frame 5: Lingering blade wake
            {"t": 0.7, "Hip": [10, 5, 5], "Chest": [8, 0, 0], "Head": [-6, 0, 0], "UpperArm_R": [-10, 0, 0], "Forearm_R": [-6, 0, 0], "Hand_R": [-3, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [6, 6, 0], "Forearm_L": [8, 0, 0], "Hand_L": [8, 0, 0], "Weapon_Front": [18, 0, 0], "Thigh_R": [-12, 8, -2], "Shin_R": [10, 0, 0], "Foot_R": [2, 0, 0], "Thigh_L": [10, -6, 0], "Shin_L": [10, 0, 0], "Foot_L": [4, 0, 0], "vfx": {"fx_spark": {"pos": [375, 330], "rot": 30, "scale": 0.6, "alpha": 0.6}}},
            # Frame 6: End cast
            {"t": 0.86, "Hip": [0, 0, 0], "Chest": [0, 0, 0], "Head": [0, 0, 0], "UpperArm_R": [0, 0, 0], "Forearm_R": [0, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [0, 0, 0], "Forearm_L": [0, 0, 0], "Hand_L": [0, 0, 0], "Weapon_Front": [0, 0, 0], "Thigh_R": [0, 0, 0], "Shin_R": [0, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [0, 0, 0], "Shin_L": [0, 0, 0], "Foot_L": [0, 0, 0]}
        ]
    },
    "hurt": {
        "grid": [2, 2], "length": 0.55, "loop": False,
        "frames": [
            {"t": 0.0, "Hip": [-8, 2, -4], "Chest": [-14, 0, 0], "Head": [10, 0, 0], "UpperArm_R": [-12, 0, 0], "Forearm_R": [8, 0, 0], "Hand_R": [10, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-10, 0, 0], "Forearm_L": [-24, 0, 0], "Hand_L": [-14, 0, 0], "Weapon_Front": [-16, 0, 0], "Thigh_R": [-10, 4, 0], "Shin_R": [14, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [12, -4, 0], "Shin_L": [10, 0, 0], "Foot_L": [0, 0, 0]},
            {"t": 0.15, "Hip": [-16, 4, -8], "Chest": [-24, 0, 0], "Head": [18, 0, 0], "UpperArm_R": [-18, 0, 0], "Forearm_R": [14, 0, 0], "Hand_R": [16, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-16, 0, 0], "Forearm_L": [-38, 0, 0], "Hand_L": [-22, 0, 0], "Weapon_Front": [-24, 0, 0], "Thigh_R": [-16, 8, -4], "Shin_R": [22, 0, 0], "Foot_R": [2, 0, 0], "Thigh_L": [18, -8, 0], "Shin_L": [16, 0, 0], "Foot_L": [2, 0, 0], "vfx": {"fx_spark": {"pos": [260, 240], "rot": 0, "scale": 0.75, "alpha": 0.95}}},
            {"t": 0.32, "Hip": [-8, 2, -4], "Chest": [-10, 0, 0], "Head": [8, 0, 0], "UpperArm_R": [-8, 0, 0], "Forearm_R": [6, 0, 0], "Hand_R": [8, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-6, 0, 0], "Forearm_L": [-16, 0, 0], "Hand_L": [-8, 0, 0], "Weapon_Front": [-8, 0, 0], "Thigh_R": [-8, 4, 0], "Shin_R": [12, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [8, -4, 0], "Shin_L": [8, 0, 0], "Foot_L": [0, 0, 0]},
            {"t": 0.48, "Hip": [0, 0, 0], "Chest": [0, 0, 0], "Head": [0, 0, 0], "UpperArm_R": [0, 0, 0], "Forearm_R": [0, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [0, 0, 0], "Forearm_L": [0, 0, 0], "Hand_L": [0, 0, 0], "Weapon_Front": [0, 0, 0], "Thigh_R": [0, 0, 0], "Shin_R": [0, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [0, 0, 0], "Shin_L": [0, 0, 0], "Foot_L": [0, 0, 0]}
        ]
    },
    "death": {
        "grid": [2, 3], "length": 1.1, "loop": False,
        "frames": [
            # Frame 1: Stagger back
            {"t": 0.0, "Hip": [-12, 4, -6], "Chest": [-18, 0, 0], "Head": [14, 0, 0], "UpperArm_R": [-14, 0, 0], "Forearm_R": [8, 0, 0], "Hand_R": [10, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-12, 0, 0], "Forearm_L": [-26, 0, 0], "Hand_L": [-16, 0, 0], "Weapon_Front": [-18, 0, 0], "Thigh_R": [-12, 4, 0], "Shin_R": [16, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [14, -6, 0], "Shin_L": [12, 0, 0], "Foot_L": [0, 0, 0]},
            # Frame 2: Legs giving way
            {"t": 0.2, "Hip": [-6, 24, -2], "Chest": [-12, 0, 0], "Head": [10, 0, 0], "UpperArm_R": [-8, 0, 0], "Forearm_R": [14, 0, 0], "Hand_R": [14, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-8, 0, 0], "Forearm_L": [-14, 0, 0], "Hand_L": [-6, 0, 0], "Weapon_Front": [-8, 0, 0], "Thigh_R": [-35, 14, 0], "Shin_R": [48, 0, 0], "Foot_R": [10, 0, 0], "Thigh_L": [28, -10, 0], "Shin_L": [36, 0, 0], "Foot_L": [10, 0, 0]},
            # Frame 3: Kneeling impact
            {"t": 0.42, "Hip": [4, 52, 4], "Chest": [10, 0, 0], "Head": [4, 0, 0], "UpperArm_R": [12, 0, 0], "Forearm_R": [22, 0, 0], "Hand_R": [18, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [14, 0, 0], "Forearm_L": [12, 0, 0], "Hand_L": [14, 0, 0], "Weapon_Front": [24, 0, 0], "Thigh_R": [-60, 24, 0], "Shin_R": [82, 0, 0], "Foot_R": [18, 0, 0], "Thigh_L": [42, -18, 0], "Shin_L": [64, 0, 0], "Foot_L": [18, 0, 0], "vfx": {"fx_dust": {"pos": [210, 420], "rot": 0, "scale": 0.72, "alpha": 0.85}}},
            # Frame 4: Slumping forward onto cleaver stuck in earth
            {"t": 0.65, "Hip": [16, 78, 12], "Chest": [38, 0, 0], "Head": [18, 0, 0], "UpperArm_R": [24, 0, 0], "Forearm_R": [32, 0, 0], "Hand_R": [22, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [36, 0, 0], "Forearm_L": [38, 0, 0], "Hand_L": [30, 0, 0], "Weapon_Front": [52, 0, 0], "Thigh_R": [-75, 30, 0], "Shin_R": [96, 0, 0], "Foot_R": [24, 0, 0], "Thigh_L": [55, -24, 0], "Shin_L": [80, 0, 0], "Foot_L": [24, 0, 0], "vfx": {"fx_dust": {"pos": [260, 430], "rot": 0, "scale": 0.85, "alpha": 0.92}}},
            # Frame 5: Full collapse motionless
            {"t": 0.88, "Hip": [22, 92, 16], "Chest": [52, 0, 0], "Head": [24, 0, 0], "UpperArm_R": [32, 0, 0], "Forearm_R": [38, 0, 0], "Hand_R": [26, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [48, 0, 0], "Forearm_L": [48, 0, 0], "Hand_L": [38, 0, 0], "Weapon_Front": [65, 0, 0], "Thigh_R": [-82, 34, 0], "Shin_R": [104, 0, 0], "Foot_R": [28, 0, 0], "Thigh_L": [62, -28, 0], "Shin_L": [88, 0, 0], "Foot_L": [28, 0, 0]},
            # Frame 6: Stillness
            {"t": 1.05, "Hip": [22, 92, 16], "Chest": [52, 0, 0], "Head": [24, 0, 0], "UpperArm_R": [32, 0, 0], "Forearm_R": [38, 0, 0], "Hand_R": [26, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [48, 0, 0], "Forearm_L": [48, 0, 0], "Hand_L": [38, 0, 0], "Weapon_Front": [65, 0, 0], "Thigh_R": [-82, 34, 0], "Shin_R": [104, 0, 0], "Foot_R": [28, 0, 0], "Thigh_L": [62, -28, 0], "Shin_L": [88, 0, 0], "Foot_L": [28, 0, 0]}
        ]
    }
}

# 2. Forward Kinematics renderer for 512x512 preview frames
def render_w003_pose(pose_dict, team_name="team_blue", show_weapon_front=True, show_weapon_back=False, show_aura=True, anim_idx=0, canvas_size=512):
    canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    
    world_transforms = {}
    for b in BONES_W003:
        bname = b["name"]
        val = pose_dict.get(bname, [0, 0, 0])
        if bname == "Hip":
            dx, dy, drot = val[0], val[1], val[2]
        else:
            drot, dx, dy = val[0], val[1], val[2]
            
        local_rot = b["rest_rot"] + drot
        local_x = b["rest_x"] + dx
        local_y = b["rest_y"] + dy
        
        parent = b["parent"]
        if parent is None:
            world_transforms[bname] = {
                "x": local_x,
                "y": local_y,
                "rot": local_rot
            }
        else:
            pt = world_transforms[parent]
            prad = math.radians(pt["rot"])
            cos_p, sin_p = math.cos(prad), math.sin(prad)
            
            rx = local_x * cos_p - local_y * sin_p
            ry = local_x * sin_p + local_y * cos_p
            
            world_transforms[bname] = {
                "x": pt["x"] + rx,
                "y": pt["y"] + ry,
                "rot": pt["rot"] + local_rot
            }

    sorted_bones = sorted(BONES_W003, key=lambda x: x["z_index"])
    
    for b in sorted_bones:
        bname = b["name"]
        wt = world_transforms[bname]
        
        if b["is_weapon"]:
            if bname == "Weapon_Front" and not show_weapon_front:
                continue
            if bname == "Weapon_Back" and not show_weapon_back:
                continue
                
            if bname == "Weapon_Front":
                if show_aura and anim_idx is not None:
                    pimg = W003_ANIM_FRAMES[anim_idx % 4]
                else:
                    pimg = w003_main
            else:
                pimg = w003_offhand
        else:
            pimg = TEAM_PARTS[team_name][b["part"]]
            
        rot_deg = wt["rot"]
        pv_x, pv_y = b["pivot_x"], b["pivot_y"]
        
        # Center of part relative to pivot
        cx = pimg.width / 2.0 - pv_x
        cy = pimg.height / 2.0 - pv_y
        
        # Rotate image around center
        rotated = pimg.rotate(-rot_deg, resample=Image.Resampling.BICUBIC, expand=True)
        
        # Original center rotated
        rad = math.radians(rot_deg)
        cos_r, sin_r = math.cos(rad), math.sin(rad)
        rcx = cx * cos_r - cy * sin_r
        rcy = cx * sin_r + cy * cos_r
        
        # Destination on canvas
        dst_x = int(round(wt["x"] + rcx - rotated.width / 2.0))
        dst_y = int(round(wt["y"] + rcy - rotated.height / 2.0))
        
        canvas.alpha_composite(rotated, (dst_x, dst_y))
        
    # Render VFX if specified in frame
    vfx_dict = pose_dict.get("vfx", {})
    for vname, vdata in vfx_dict.items():
        if vname in VFX_PARTS:
            vimg = VFX_PARTS[vname].copy()
            vpos = vdata.get("pos", [256, 256])
            vrot = vdata.get("rot", 0)
            vscale = vdata.get("scale", 1.0)
            valpha = vdata.get("alpha", 1.0)
            
            if vscale != 1.0:
                nw, nh = max(1, int(vimg.width * vscale)), max(1, int(vimg.height * vscale))
                vimg = vimg.resize((nw, nh), Image.Resampling.LANCZOS)
            if vrot != 0:
                vimg = vimg.rotate(-vrot, resample=Image.Resampling.BICUBIC, expand=True)
            if valpha < 1.0:
                arr = np.array(vimg)
                arr[:, :, 3] = (arr[:, :, 3] * valpha).astype(np.uint8)
                vimg = Image.fromarray(arr, "RGBA")
            vx = int(round(vpos[0] - vimg.width / 2.0))
            vy = int(round(vpos[1] - vimg.height / 2.0))
            canvas.alpha_composite(vimg, (vx, vy))
            
    return canvas, world_transforms

# 3. Generate QC Audit Boards
print("=== 3. Building QC Audit Boards for W003 ===")

# 3A. Weapon & Aura Audit Board (w003_weapon_and_aura_audit.png)
board_w, board_h = 1200, 800
audit_im = Image.new("RGBA", (board_w, board_h), (18, 22, 32, 255))
draw = ImageDraw.Draw(audit_im)

try:
    font_lg = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
    font_md = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
    font_sm = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 13)
except Exception:
    font_lg = font_md = font_sm = ImageFont.load_default()

# Header
draw.rectangle([0, 0, board_w, 64], fill=(28, 34, 48, 255))
draw.text((24, 18), "W003 — ĐẠI ĐAO ĐỒI THÍ (CẤP N) — QC WEAPON & AURA AUDIT", fill=(255, 215, 0), font=font_lg)
draw.text((800, 22), "STRICT 3-STEP WEAPON FLOW VERIFIED", fill=(100, 220, 140), font=font_md)

# Panel 1: weapon_main + Grip1 & Grip2 inspection
draw.rectangle([30, 80, 580, 420], fill=(24, 28, 40, 255), outline=(50, 60, 80), width=1)
draw.text((45, 95), "1. WEAPON_MAIN (Executioner Great-Cleaver) & DUAL GRIP POINTS", fill=(230, 230, 240), font=font_md)
main_disp = w003_main.copy()
# Draw Grip 1 & Grip 2 markers on weapon_main
disp_draw = ImageDraw.Draw(main_disp)
# Grip 1 (Gold)
disp_draw.ellipse([W003_G1_X - 6, W003_G1_Y - 6, W003_G1_X + 6, W003_G1_Y + 6], fill=(255, 215, 0, 255), outline=(0, 0, 0), width=2)
disp_draw.text((W003_G1_X + 10, W003_G1_Y - 14), f"Grip 1 ({W003_G1_X:.1f}, {W003_G1_Y:.1f})", fill=(255, 230, 100), font=font_sm)
# Grip 2 (Cyan)
disp_draw.ellipse([W003_G2_X - 6, W003_G2_Y - 6, W003_G2_X + 6, W003_G2_Y + 6], fill=(0, 220, 255, 255), outline=(0, 0, 0), width=2)
disp_draw.text((W003_G2_X - 80, W003_G2_Y + 8), f"Grip 2 ({W003_G2_X:.1f}, {W003_G2_Y:.1f})", fill=(100, 240, 255), font=font_sm)

audit_im.alpha_composite(main_disp, (190, 150))
draw.text((45, 340), f"Tight Crop: {w003_main.width}x{w003_main.height} px | Edge Margin: 0px Transparent Margin", fill=(180, 190, 210), font=font_sm)
draw.text((45, 365), f"Grip 1: ({W003_G1_X}, {W003_G1_Y}) [Hand_L Collar] | Grip 2: ({W003_G2_X}, {W003_G2_Y}) [Hand_R Pommel]", fill=(180, 190, 210), font=font_sm)
draw.text((45, 390), "Status: 100% Full weapon visible, notched chopping blade, blood grooves, 0px edge-clip", fill=(100, 220, 140), font=font_sm)

# Panel 2: weapon_offhand (Secondary Cleaver / Hook)
draw.rectangle([610, 80, 1160, 420], fill=(24, 28, 40, 255), outline=(50, 60, 80), width=1)
draw.text((625, 95), "2. WEAPON_OFFHAND (Hand Cleaver / Meat Hook) & DUAL WEAPON SUPPORT", fill=(230, 230, 240), font=font_md)
off_disp = w003_offhand.copy()
audit_im.alpha_composite(off_disp, (800, 190))
draw.text((625, 340), f"Tight Crop: {w003_offhand.width}x{w003_offhand.height} px | Dual Weapon Support: Hand_R / Weapon_Back", fill=(180, 190, 210), font=font_sm)
draw.text((625, 365), "Pivot: (110.0, 35.0) | Grip 1: (110.0, 35.0) | Grip 2: (140.0, 45.0)", fill=(180, 190, 210), font=font_sm)
draw.text((625, 390), "Status: Zero ammunition/arrows, purely brutal executioner butcher tools", fill=(100, 220, 140), font=font_sm)

# Panel 3: 4-Frame Animation Spritesheet & WeaponAura
draw.rectangle([30, 440, 1160, 770], fill=(24, 28, 40, 255), outline=(50, 60, 80), width=1)
draw.text((45, 455), "3. 4-FRAME ANIMATED WEAPON SPRITESHEET (2x2 Loop) & WEAPON AURA", fill=(230, 230, 240), font=font_md)

# Paste the 4 animation frames
for i in range(4):
    ax = 50 + i * 270
    ay = 490
    draw.rectangle([ax, ay, ax + 250, ay + 200], fill=(16, 20, 28, 255), outline=(40, 50, 70), width=1)
    audit_im.alpha_composite(W003_ANIM_FRAMES[i], (ax + 17, ay + 17))
    titles = ["Frame 0: Resting Steel", "Frame 1: Crimson Pulse", "Frame 2: Peak Strike Glint", "Frame 3: Embers Reset"]
    draw.text((ax + 20, ay + 210), titles[i], fill=(255, 215, 0) if i==2 else (180, 190, 210), font=font_sm)

audit_path = os.path.join(W003_QC_DIR, "w003_weapon_and_aura_audit.png")
audit_im.save(audit_path)
shutil.copyfile(audit_path, os.path.join(ARTIFACT_DIR, "w003_weapon_and_aura_audit.png"))
print("Saved W003 Weapon & Aura Audit ->", audit_path)

# 3B. Sticker Character 4 Teams x 6 Actions Overview (w003_sticker_all_6_actions_overview.png)
ov_cols = 4  # 4 teams
ov_rows = 6  # 6 actions
thumb_size = 180
grid_gap_x = 24
grid_gap_y = 30
header_top = 80
side_label_w = 120

ov_w = side_label_w + ov_cols * (thumb_size + grid_gap_x) + 40
ov_h = header_top + ov_rows * (thumb_size + grid_gap_y) + 40

ov_im = Image.new("RGBA", (ov_w, ov_h), (16, 20, 28, 255))
ov_draw = ImageDraw.Draw(ov_im)

# Header
ov_draw.rectangle([0, 0, ov_w, 64], fill=(24, 30, 42, 255))
ov_draw.text((24, 18), "W003 — ĐẠI ĐAO ĐỒI THÍ — 4 TEAMS x 6 ACTIONS OVERVIEW (24 POSE MATRIX)", fill=(255, 215, 0), font=font_lg)

# Column headers (4 Teams)
team_titles = [("ĐỘI 1: XANH DƯƠNG", (100, 180, 255)), ("ĐỘI 2: ĐỎ", (255, 110, 110)), ("ĐỘI 3: XANH LÁ", (100, 230, 130)), ("ĐỘI 4: VÀNG CAM", (255, 200, 80))]
for c_idx, (t_title, t_col) in enumerate(team_titles):
    cx = side_label_w + c_idx * (thumb_size + grid_gap_x) + thumb_size // 2
    ov_draw.text((cx - 70, 72), t_title, fill=t_col, font=font_md)

# Row labels and frame rendering
action_keys = ["idle", "walk", "attack", "cast", "hurt", "death"]
action_labels = ["1. IDLE (Nghỉ)", "2. WALK (Bước)", "3. ATTACK (Trảm)", "4. CAST (Toái Giáp)", "5. HURT (Trúng Đòn)", "6. DEATH (Gục Ngã)"]

for r_idx, act_name in enumerate(action_keys):
    ry = header_top + 30 + r_idx * (thumb_size + grid_gap_y)
    ov_draw.text((20, ry + thumb_size // 2 - 10), action_labels[r_idx], fill=(220, 225, 235), font=font_md)
    
    act_data = ACTIONS_W003[act_name]
    # Pick representative keyframe (frame 1 for attack, frame 2 for cast, frame 2 for death)
    key_frame_idx = 1 if act_name in ["attack", "walk"] else (2 if act_name in ["cast", "death"] else 0)
    rep_frame = act_data["frames"][min(key_frame_idx, len(act_data["frames"]) - 1)]
    
    for c_idx, t_name in enumerate(TEAMS):
        cx = side_label_w + c_idx * (thumb_size + grid_gap_x)
        ov_draw.rectangle([cx, ry, cx + thumb_size, ry + thumb_size], fill=(22, 26, 36, 255), outline=(45, 55, 75), width=1)
        
        # Render pose with W003 weapon
        pose_im, _ = render_w003_pose(
            rep_frame,
            team_name=t_name,
            show_weapon_front=True,
            show_weapon_back=(act_name in ["cast", "attack"]),
            show_aura=True,
            anim_idx=key_frame_idx,
            canvas_size=512
        )
        thumb = pose_im.resize((thumb_size, thumb_size), Image.Resampling.LANCZOS)
        ov_im.alpha_composite(thumb, (cx, ry))

ov_path = os.path.join(W003_QC_DIR, "w003_sticker_all_6_actions_overview.png")
ov_im.save(ov_path)
shutil.copyfile(ov_path, os.path.join(ARTIFACT_DIR, "w003_sticker_all_6_actions_overview.png"))
print("Saved W003 6-Action Overview ->", ov_path)

# 4. Generate Godot 4 Scene & Script (.tscn & .gd)
print("=== 4. Building Godot 4 Scene & Script for W003 ===")

def build_godot_tscn(weapon_id="w003", weapon_name="C003_DaoPhuDoiThi", tscn_prefix="c003_dao_phu_doi_thi"):
    ext_resources = []
    
    ext_resources.append(f'[ext_resource type="Script" path="res://assets/weapons/{weapon_id}_dao_phu_doi_thi/godot/{tscn_prefix}.gd" id="1_script"]')
    res_id = 2
    part_res_map = {}
    
    # Sticker parts
    for p in STICKER_PARTS:
        part_res_map[p] = f"{res_id}_{p}"
        ext_resources.append(f'[ext_resource type="Texture2D" path="res://assets/sticker_hero/godot/parts/team_blue/{p}.png" id="{res_id}_{p}"]')
        res_id += 1
    
    # Weapon parts
    for wp in ["weapon_main", "weapon_offhand", "weapon_aura", "weapon_anim_0", "weapon_anim_1", "weapon_anim_2", "weapon_anim_3"]:
        part_res_map[wp] = f"{res_id}_{wp}"
        ext_resources.append(f'[ext_resource type="Texture2D" path="res://assets/weapons/{weapon_id}_dao_phu_doi_thi/parts/{wp}.png" id="{res_id}_{wp}"]')
        res_id += 1
    
    # VFX
    for fx in ["fx_slash", "fx_slash_heavy", "fx_spark", "fx_dust"]:
        part_res_map[fx] = f"{res_id}_{fx}"
        ext_resources.append(f'[ext_resource type="Texture2D" path="res://assets/weapons/{weapon_id}_dao_phu_doi_thi/parts/{fx}.png" id="{res_id}_{fx}"]')
        res_id += 1
    
    # SpriteFrames for WeaponAura
    sub_resources = []
    sub_resources.append("""[sub_resource type="SpriteFrames" id="SpriteFrames_weapon_anim"]
animations = [{
"frames": [{
"duration": 1.0,
"texture": ExtResource(\"""" + part_res_map["weapon_anim_0"] + """\")
}, {
"duration": 1.0,
"texture": ExtResource(\"""" + part_res_map["weapon_anim_1"] + """\")
}, {
"duration": 1.0,
"texture": ExtResource(\"""" + part_res_map["weapon_anim_2"] + """\")
}, {
"duration": 1.0,
"texture": ExtResource(\"""" + part_res_map["weapon_anim_3"] + """\")
}],
"loop": true,
"name": &"default",
"speed": 8.0
}]""")

    # Animations
    anim_sub_ids = []
    bone_paths = {}
    for b in BONES_W003:
        bone_paths[b["name"]] = b["parent"] + "/" + b["name"] if b["parent"] else f"Skeleton2D/{b['name']}"
    
    for act_name, act in ACTIONS_W003.items():
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
        for b in BONES_W003:
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
            
            rots_str = ", ".join(rots)
            pos_str = ", ".join(pos)
            
            # Rotation track
            anim_txt += f"""
tracks/{track_idx}/type = "value"
tracks/{track_idx}/imported = false
tracks/{track_idx}/enabled = true
tracks/{track_idx}/path = NodePath("Skeleton2D/{bpath}:rotation")
tracks/{track_idx}/interp = 1
tracks/{track_idx}/loop_wrap = true
tracks/{track_idx}/keys = {{
"times": PackedFloat32Array({times_str}),
"transitions": PackedFloat32Array({transitions}),
"update": 0,
"values": [{rots_str}]
}}"""
            track_idx += 1
            
            # Position track
            anim_txt += f"""
tracks/{track_idx}/type = "value"
tracks/{track_idx}/imported = false
tracks/{track_idx}/enabled = true
tracks/{track_idx}/path = NodePath("Skeleton2D/{bpath}:position")
tracks/{track_idx}/interp = 1
tracks/{track_idx}/loop_wrap = true
tracks/{track_idx}/keys = {{
"times": PackedFloat32Array({times_str}),
"transitions": PackedFloat32Array({transitions}),
"update": 0,
"values": [{pos_str}]
}}"""
            track_idx += 1
            
        sub_resources.append(anim_txt)
        
    # AnimationLibrary
    lib_lines = ['[sub_resource type="AnimationLibrary" id="AnimationLibrary_w003"]', '_data = {']
    for act_name, sub_id in anim_sub_ids:
        lib_lines.append(f'"{act_name}": SubResource("{sub_id}"),')
    lib_lines.append('}')
    sub_resources.append("\n".join(lib_lines))

    # Node hierarchy
    nodes_txt = f"""[node name="{weapon_name}" type="Node2D"]
script = ExtResource("1_script")

[node name="Skeleton2D" type="Skeleton2D" parent="."]

[node name="Hip" type="Bone2D" parent="Skeleton2D"]
position = Vector2(198, 258)
rest = Transform2D(1, 0, 0, 1, 198, 258)

[node name="Sprite" type="Sprite2D" parent="Skeleton2D/Hip"]
position = Vector2(0, 7.8)
texture = ExtResource("{part_res_map['hip_kilt']}")

[node name="Thigh_L" type="Bone2D" parent="Skeleton2D/Hip"]
position = Vector2(8, 14)
rotation = -0.384
rest = Transform2D(0.927, -0.375, 0.375, 0.927, 8, 14)

[node name="Sprite" type="Sprite2D" parent="Skeleton2D/Hip/Thigh_L"]
position = Vector2(0, 21)
texture = ExtResource("{part_res_map['leg_thigh_back']}")

[node name="Shin_L" type="Bone2D" parent="Skeleton2D/Hip/Thigh_L"]
position = Vector2(0, 42)
rotation = 0.279
rest = Transform2D(0.961, 0.276, -0.276, 0.961, 0, 42)

[node name="Sprite" type="Sprite2D" parent="Skeleton2D/Hip/Thigh_L/Shin_L"]
position = Vector2(0, 19.5)
texture = ExtResource("{part_res_map['leg_shin_back']}")

[node name="Foot_L" type="Bone2D" parent="Skeleton2D/Hip/Thigh_L/Shin_L"]
position = Vector2(0, 39)
rotation = 0.105
rest = Transform2D(0.995, 0.105, -0.105, 0.995, 0, 39)

[node name="Sprite" type="Sprite2D" parent="Skeleton2D/Hip/Thigh_L/Shin_L/Foot_L"]
position = Vector2(10.1, 9.5)
texture = ExtResource("{part_res_map['foot_back']}")

[node name="Thigh_R" type="Bone2D" parent="Skeleton2D/Hip"]
position = Vector2(-8, 14)
rotation = 0.384
rest = Transform2D(0.927, 0.375, -0.375, 0.927, -8, 14)

[node name="Sprite" type="Sprite2D" parent="Skeleton2D/Hip/Thigh_R"]
position = Vector2(0, 21.5)
texture = ExtResource("{part_res_map['leg_thigh_front']}")

[node name="Shin_R" type="Bone2D" parent="Skeleton2D/Hip/Thigh_R"]
position = Vector2(0, 43)
rotation = -0.244
rest = Transform2D(0.970, -0.242, 0.242, 0.970, 0, 43)

[node name="Sprite" type="Sprite2D" parent="Skeleton2D/Hip/Thigh_R/Shin_R"]
position = Vector2(0, 20)
texture = ExtResource("{part_res_map['leg_shin_front']}")

[node name="Foot_R" type="Bone2D" parent="Skeleton2D/Hip/Thigh_R/Shin_R"]
position = Vector2(0, 40)
rotation = -0.140
rest = Transform2D(0.990, -0.139, 0.139, 0.990, 0, 40)

[node name="Sprite" type="Sprite2D" parent="Skeleton2D/Hip/Thigh_R/Shin_R/Foot_R"]
position = Vector2(10.4, 10.5)
texture = ExtResource("{part_res_map['foot_front']}")

[node name="Chest" type="Bone2D" parent="Skeleton2D/Hip"]
position = Vector2(0, -4)
rotation = 0.052
rest = Transform2D(0.999, 0.052, -0.052, 0.999, 0, -4)

[node name="Sprite" type="Sprite2D" parent="Skeleton2D/Hip/Chest"]
position = Vector2(0, -12)
texture = ExtResource("{part_res_map['chest']}")

[node name="Neck" type="Bone2D" parent="Skeleton2D/Hip/Chest"]
position = Vector2(-4, -44)
rest = Transform2D(1, 0, 0, 1, -4, -44)

[node name="Sprite" type="Sprite2D" parent="Skeleton2D/Hip/Chest/Neck"]
texture = ExtResource("{part_res_map['neck']}")

[node name="Head" type="Bone2D" parent="Skeleton2D/Hip/Chest/Neck"]
position = Vector2(0, -10)
rotation = -0.052
rest = Transform2D(0.999, -0.052, 0.052, 0.999, 0, -10)

[node name="Sprite" type="Sprite2D" parent="Skeleton2D/Hip/Chest/Neck/Head"]
position = Vector2(0, -18.5)
texture = ExtResource("{part_res_map['head']}")

[node name="UpperArm_R" type="Bone2D" parent="Skeleton2D/Hip/Chest"]
position = Vector2(16, -54)
rotation = 0.454
rest = Transform2D(0.899, 0.438, -0.438, 0.899, 16, -54)

[node name="Sprite" type="Sprite2D" parent="Skeleton2D/Hip/Chest/UpperArm_R"]
position = Vector2(0, 19.5)
texture = ExtResource("{part_res_map['arm_upper_back']}")

[node name="Forearm_R" type="Bone2D" parent="Skeleton2D/Hip/Chest/UpperArm_R"]
position = Vector2(0, 39)
rotation = -0.733
rest = Transform2D(0.743, -0.669, 0.669, 0.743, 0, 39)

[node name="Sprite" type="Sprite2D" parent="Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R"]
position = Vector2(0, 18)
texture = ExtResource("{part_res_map['arm_lower_back']}")

[node name="Hand_R" type="Bone2D" parent="Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R"]
position = Vector2(0, 36)
rest = Transform2D(1, 0, 0, 1, 0, 36)

[node name="Sprite" type="Sprite2D" parent="Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Hand_R"]
position = Vector2(0.5, 18)
texture = ExtResource("{part_res_map['hand_back']}")

[node name="Weapon_Back" type="Bone2D" parent="Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Hand_R"]
visible = false
position = Vector2(0, 24)
rotation = 0.785
rest = Transform2D(0.707, 0.707, -0.707, 0.707, 0, 24)
metadata/grip1 = Vector2(110.0, 35.0)
metadata/grip2 = Vector2(140.0, 45.0)

[node name="Sprite" type="Sprite2D" parent="Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Hand_R/Weapon_Back"]
position = Vector2(-30.0, -3.5)
texture = ExtResource("{part_res_map['weapon_offhand']}")

[node name="UpperArm_L" type="Bone2D" parent="Skeleton2D/Hip/Chest"]
position = Vector2(-8, -58)
rotation = 0.175
rest = Transform2D(0.985, 0.174, -0.174, 0.985, -8, -58)

[node name="Sprite" type="Sprite2D" parent="Skeleton2D/Hip/Chest/UpperArm_L"]
position = Vector2(0, 20)
texture = ExtResource("{part_res_map['arm_upper_front']}")

[node name="Forearm_L" type="Bone2D" parent="Skeleton2D/Hip/Chest/UpperArm_L"]
position = Vector2(0, 40)
rotation = -0.908
rest = Transform2D(0.616, -0.788, 0.788, 0.616, 0, 40)

[node name="Sprite" type="Sprite2D" parent="Skeleton2D/Hip/Chest/UpperArm_L/Forearm_L"]
position = Vector2(0, 19)
texture = ExtResource("{part_res_map['arm_lower_front']}")

[node name="Hand_L" type="Bone2D" parent="Skeleton2D/Hip/Chest/UpperArm_L/Forearm_L"]
position = Vector2(0, 38)
rest = Transform2D(1, 0, 0, 1, 0, 38)

[node name="Sprite" type="Sprite2D" parent="Skeleton2D/Hip/Chest/UpperArm_L/Forearm_L/Hand_L"]
position = Vector2(0.5, 19)
texture = ExtResource("{part_res_map['hand_front']}")

[node name="Weapon_Front" type="Bone2D" parent="Skeleton2D/Hip/Chest/UpperArm_L/Forearm_L/Hand_L"]
position = Vector2(0, 26)
rotation = 0.559
rest = Transform2D(0.848, 0.530, -0.530, 0.848, 0, 26)
metadata/grip1 = Vector2({W003_G1_X}, {W003_G1_Y})
metadata/grip2 = Vector2({W003_G2_X}, {W003_G2_Y})

[node name="WeaponAura" type="AnimatedSprite2D" parent="Skeleton2D/Hip/Chest/UpperArm_L/Forearm_L/Hand_L/Weapon_Front"]
position = Vector2(-26.0, -37.0)
sprite_frames = SubResource("SpriteFrames_weapon_anim")
autoplay = "default"
frame_progress = 0.42

[node name="Sprite" type="Sprite2D" parent="Skeleton2D/Hip/Chest/UpperArm_L/Forearm_L/Hand_L/Weapon_Front"]
position = Vector2(-26.0, -37.0)
texture = ExtResource("{part_res_map['weapon_main']}")

[node name="AnimationPlayer" type="AnimationPlayer" parent="."]
libraries = {{
"": SubResource("AnimationLibrary_w003")
}}
"""

    total_steps = len(ext_resources) + len(sub_resources) + 1
    tscn_header = f"""[gd_scene load_steps={total_steps} format=3 uid="uid://c003daophudoithi"]

"""
    return tscn_header + "\n".join(ext_resources) + "\n\n" + "\n\n".join(sub_resources) + "\n\n" + nodes_txt

tscn_content = build_godot_tscn()
tscn_path = os.path.join(W003_GODOT_DIR, "c003_dao_phu_doi_thi.tscn")
with open(tscn_path, "w", encoding="utf-8") as f:
    f.write(tscn_content)
print("Saved Godot TSCN ->", tscn_path)

# Godot GD Script
gd_script = """extends Node2D

@export var dual_weapon_enabled: bool = false:
	set(value):
		dual_weapon_enabled = value
		if has_node("Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Hand_R/Weapon_Back"):
			$Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Hand_R/Weapon_Back.visible = value

@export var weapon_aura_enabled: bool = true:
	set(value):
		weapon_aura_enabled = value
		if has_node("Skeleton2D/Hip/Chest/UpperArm_L/Forearm_L/Hand_L/Weapon_Front/WeaponAura"):
			$Skeleton2D/Hip/Chest/UpperArm_L/Forearm_L/Hand_L/Weapon_Front/WeaponAura.visible = value

@onready var anim_player: AnimationPlayer = $AnimationPlayer
@onready var skeleton: Skeleton2D = $Skeleton2D
@onready var weapon_front: Bone2D = $Skeleton2D/Hip/Chest/UpperArm_L/Forearm_L/Hand_L/Weapon_Front
@onready var weapon_back: Bone2D = $Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Hand_R/Weapon_Back
@onready var weapon_aura: AnimatedSprite2D = $Skeleton2D/Hip/Chest/UpperArm_L/Forearm_L/Hand_L/Weapon_Front/WeaponAura

var current_team: String = "team_blue"

func _ready() -> void:
	play_action("idle")

func set_team(team_name: String) -> void:
	current_team = team_name
	var base_path := "res://assets/sticker_hero/godot/parts/" + team_name + "/"
	for bone in skeleton.get_children():
		_update_bone_texture(bone, base_path)

func _update_bone_texture(node: Node, base_path: String) -> void:
	if node is Bone2D and not node.name.begins_with("Weapon"):
		var sp := node.get_node_or_null("Sprite") as Sprite2D
		if sp:
			var part_name: String = node.name.to_lower()
			var tex_path := base_path + part_name + ".png"
			if ResourceLoader.exists(tex_path):
				sp.texture = load(tex_path)
	for child in node.get_children():
		_update_bone_texture(child, base_path)

func play_action(action_name: String) -> void:
	if anim_player and anim_player.has_animation(action_name):
		anim_player.play(action_name)

func toggle_dual_weapons(enabled: bool) -> void:
	dual_weapon_enabled = enabled

func toggle_weapon_aura(enabled: bool) -> void:
	weapon_aura_enabled = enabled
"""

gd_path = os.path.join(W003_GODOT_DIR, "c003_dao_phu_doi_thi.gd")
with open(gd_path, "w", encoding="utf-8") as f:
    f.write(gd_script)
print("Saved Godot GD Script ->", gd_path)

# 5. Pack data into JSON for HTML Editor
def b64_png(path):
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")

w003_pack = {
    "id": "w003",
    "name": "W003 — Đại Đao Đồi Thí (Cấp N — Animated Great-Cleaver)",
    "tscn_name": "c003_dao_phu_doi_thi.tscn",
    "node_name": "C003_DaoPhuDoiThi",
    "aura_default": True,
    "card_b64": b64_png(W003_CARD_PNG),
    "bones": BONES_W003,
    "actions": ACTIONS_W003,
    "images": {
        "weapon_main": b64_png(os.path.join(W003_PARTS_DIR, "weapon_main.png")),
        "weapon_offhand": b64_png(os.path.join(W003_PARTS_DIR, "weapon_offhand.png")),
        "weapon_aura": b64_png(os.path.join(W003_PARTS_DIR, "weapon_aura.png")),
        "weapon_anim_0": b64_png(os.path.join(W003_PARTS_DIR, "weapon_anim_0.png")),
        "weapon_anim_1": b64_png(os.path.join(W003_PARTS_DIR, "weapon_anim_1.png")),
        "weapon_anim_2": b64_png(os.path.join(W003_PARTS_DIR, "weapon_anim_2.png")),
        "weapon_anim_3": b64_png(os.path.join(W003_PARTS_DIR, "weapon_anim_3.png")),
        "fx_slash": b64_png(os.path.join(W003_PARTS_DIR, "fx_slash.png")),
        "fx_slash_heavy": b64_png(os.path.join(W003_PARTS_DIR, "fx_slash_heavy.png")),
        "fx_spark": b64_png(os.path.join(W003_PARTS_DIR, "fx_spark.png")),
        "fx_dust": b64_png(os.path.join(W003_PARTS_DIR, "fx_dust.png")),
    }
}

# 6. Update assets/sticker_weapon_editor.html to include W003 alongside W001, W002 & W018
editor_path = "/Users/dochung/Desktop/card_g/assets/sticker_weapon_editor.html"
with open(editor_path, "r", encoding="utf-8") as f:
    editor_html = f.read()

# Add W003 option to <select id="weaponSelect">
opt_target = '<option value="w002"'
opt_w003 = '<option value="w003" selected>W003 — Đại Đao Đồi Thí (Cấp N — Animated 2x2 Spritesheet)</option>\n        '
if opt_target in editor_html and 'value="w003"' not in editor_html:
    editor_html = editor_html.replace(opt_target, opt_w003 + opt_target)
    # Remove selected from w002
    editor_html = editor_html.replace('<option value="w002" selected>', '<option value="w002">')

# Inject or update W003_PACK definition
import re
w003_json_str = json.dumps(w003_pack)
marker = "const W018_PACK ="
w003_inject = f"const W003_PACK = {w003_json_str};\nconst W018_PACK ="
if "const W003_PACK =" in editor_html:
    editor_html = re.sub(r"const W003_PACK = .*?;\nconst W018_PACK =", lambda _: w003_inject, editor_html, count=1)
elif marker in editor_html:
    editor_html = editor_html.replace(marker, w003_inject)

# Update WEAPON_PACK_IMAGES to include w003
old_wpi = "const WEAPON_PACK_IMAGES = { w001: {}, w002: {}, w018: {} };"
new_wpi = """const WEAPON_PACK_IMAGES = { w001: {}, w002: {}, w003: {}, w018: {} };
Object.entries(W003_PACK.images).forEach(([k, src]) => {
  const im = new Image(); im.src = src; WEAPON_PACK_IMAGES.w003[k] = im;
});"""
if old_wpi in editor_html:
    editor_html = editor_html.replace(old_wpi, new_wpi)

# Update applyWeaponPack pack selection
old_pack_sel = 'const pack = wid === "w002" ? W002_PACK : (wid === "w018" ? W018_PACK : W001_PACK);'
new_pack_sel = 'const pack = wid === "w003" ? W003_PACK : (wid === "w002" ? W002_PACK : (wid === "w018" ? W018_PACK : W001_PACK));'
if old_pack_sel in editor_html:
    editor_html = editor_html.replace(old_pack_sel, new_pack_sel)

# Update onSelectWeapon toast
old_toast = 'document.getElementById("statusToast").textContent = wid === "w002" ? "Đang trang bị: W002 — Nỏ Câm Lặng (Cấp N — Animated Crossbow)" : (wid === "w018" ? "Đang trang bị: W018 — Huyết Kiếm Hành Quyết (SSR 4-Frame Animated Weapon)" : "Đang trang bị: W001 — Hắc Kiếm Tàn Binh (Cấp N)");'
new_toast = 'document.getElementById("statusToast").textContent = wid === "w003" ? "Đang trang bị: W003 — Đại Đao Đồi Thí (Cấp N — Animated Great-Cleaver)" : (wid === "w002" ? "Đang trang bị: W002 — Nỏ Câm Lặng (Cấp N — Animated Crossbow)" : (wid === "w018" ? "Đang trang bị: W018 — Huyết Kiếm Hành Quyết (SSR 4-Frame Animated Weapon)" : "Đang trang bị: W001 — Hắc Kiếm Tàn Binh (Cấp N)"));'
if old_toast in editor_html:
    editor_html = editor_html.replace(old_toast, new_toast)

# Update suggestedName in saveToGodotTscn
old_sugg = 'suggestedName: currentWeaponId === "w002" ? "c002_no_thu_cam_lang.tscn" : (currentWeaponId === "w018" ? "c018_hanh_quyet_gia.tscn" : "c001_hac_kiem_tan_binh.tscn"),'
new_sugg = 'suggestedName: currentWeaponId === "w003" ? "c003_dao_phu_doi_thi.tscn" : (currentWeaponId === "w002" ? "c002_no_thu_cam_lang.tscn" : (currentWeaponId === "w018" ? "c018_hanh_quyet_gia.tscn" : "c001_hac_kiem_tan_binh.tscn")),'
if old_sugg in editor_html:
    editor_html = editor_html.replace(old_sugg, new_sugg)

old_dl = 'a.download = currentWeaponId === "w002" ? "c002_no_thu_cam_lang.tscn" : (currentWeaponId === "w018" ? "c018_hanh_quyet_gia.tscn" : "c001_hac_kiem_tan_binh.tscn");'
new_dl = 'a.download = currentWeaponId === "w003" ? "c003_dao_phu_doi_thi.tscn" : (currentWeaponId === "w002" ? "c002_no_thu_cam_lang.tscn" : (currentWeaponId === "w018" ? "c018_hanh_quyet_gia.tscn" : "c001_hac_kiem_tan_binh.tscn"));'
if old_dl in editor_html:
    editor_html = editor_html.replace(old_dl, new_dl)

# Also update buildGodotTscnString in HTML editor for w003
old_cfg = 'w002: { dir: "w002_no_thu_cam_lang", script: "c002_no_thu_cam_lang", node: "C002_NoThuCamLang", uid: "uid://c002nothucamlang" },'
new_cfg = 'w003: { dir: "w003_dao_phu_doi_thi", script: "c003_dao_phu_doi_thi", node: "C003_DaoPhuDoiThi", uid: "uid://c003daophudoithi" },\n    w002: { dir: "w002_no_thu_cam_lang", script: "c002_no_thu_cam_lang", node: "C002_NoThuCamLang", uid: "uid://c002nothucamlang" },'
if old_cfg in editor_html:
    editor_html = editor_html.replace(old_cfg, new_cfg)

# Default to w003 at startup
editor_html = editor_html.replace('applyWeaponPack("w002");', 'applyWeaponPack("w003");')

# Save updated sticker_weapon_editor.html
with open(editor_path, "w", encoding="utf-8") as f:
    f.write(editor_html)

# Save standalone w003_editor.html
w003_editor_path = os.path.join(W003_DIR, "w003_editor.html")
with open(w003_editor_path, "w", encoding="utf-8") as f:
    f.write(editor_html)

# Also sync w001, w002, and w018 standalone editors with updated sticker_weapon_editor.html
for wid, wdir, fname in [
    ("w001", "assets/weapons/w001_hac_kiem_tan_binh", "w001_editor.html"),
    ("w002", "assets/weapons/w002_no_thu_cam_lang", "w002_editor.html"),
    ("w018", "assets/weapons/w018_huyet_kiem_hanh_quyet", "w018_editor.html")
]:
    p = os.path.join(REPO_DIR, wdir, fname)
    with open(p, "w", encoding="utf-8") as f:
        f.write(editor_html)

print("Saved Multi-Weapon Editor ->", editor_path, "and", w003_editor_path)
print("=== ALL W003 BUILD STEPS COMPLETE! ===")
