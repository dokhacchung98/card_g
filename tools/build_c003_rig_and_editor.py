#!/usr/bin/env python3
"""
18-Bone Spine-Style Rig & Interactive Single-Action-Preview HTML Editor Builder
for Hero 003 (C03): Đao Phủ Đồi Thi (c003_dao_phu_doi_thi — Rarity N, Physical Melee AoE Bruiser)

Follows the Mandatory Front-Hand Weapon Grip Rule:
- Front Right Arm (UpperArm_L -> Forearm_L -> Hand_L -> Sword) holds the heavy iron executioner great-cleaver in the foreground!
- Back Left Arm (UpperArm_R -> Forearm_R -> Hand_R) is the secondary off-hand extended forward-right!
"""
import os
import json
import math
import glob
import base64
import shutil
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERO_DIR = "/Users/dochung/Desktop/card_g/assets/heroes/c003_dao_phu_doi_thi"
PARTS_DIR = os.path.join(HERO_DIR, "godot/parts")
GODOT_DIR = os.path.join(HERO_DIR, "godot")
QC_DIR = os.path.join(HERO_DIR, "qc_previews")
TSCN_PATH = os.path.join(GODOT_DIR, "c003_dao_phu_doi_thi.tscn")
GD_PATH = os.path.join(GODOT_DIR, "c003_dao_phu_doi_thi.gd")
RIG_STATE_PATH = os.path.join(GODOT_DIR, "c003_rig_state.json")
HTML_EDITOR_PATH = os.path.join(HERO_DIR, "c003_editor.html")
ARTIFACT_DIR = "/Users/dochung/.gemini/antigravity-cli/brain/e8f2a241-a2ff-47d9-a161-5cdae075b6ce"

os.makedirs(GODOT_DIR, exist_ok=True)
os.makedirs(QC_DIR, exist_ok=True)
os.makedirs(ARTIFACT_DIR, exist_ok=True)

# 0. Run extraction of all 18 body parts + 4 soft-opacity VFX PNGs
subprocess.run(["python3", "/Users/dochung/Desktop/card_g/tools/extract_c003_all_18_parts_and_vfx.py"], check=True)

# 1. Define the 18-Bone Hierarchy (Skeleton2D -> Bone2D -> Sprite2D)
# Note: Sword is a child of Hand_L (hand_front — closer foreground right hand!)
BONES = [
    {
        "name": "Hip",
        "parent": None,
        "part": "hip_kilt",
        "rest_x": 244.0, "rest_y": 248.0, "rest_rot": 0.0,
        "pivot_x": 92.0, "pivot_y": 24.0,
        "z_index": 7,
        "tip_child": "Chest",
    },
    {
        "name": "Thigh_L",
        "parent": "Hip",
        "part": "leg_thigh_back",
        "rest_x": 30.0, "rest_y": 22.0, "rest_rot": -16.0,
        "pivot_x": 40.0, "pivot_y": 22.0,
        "z_index": 1,
        "tip_child": "Shin_L",
    },
    {
        "name": "Shin_L",
        "parent": "Thigh_L",
        "part": "leg_shin_back",
        "rest_x": 6.0, "rest_y": 54.0, "rest_rot": 14.0,
        "pivot_x": 38.0, "pivot_y": 20.0,
        "z_index": 2,
        "tip_child": "Foot_L",
    },
    {
        "name": "Foot_L",
        "parent": "Shin_L",
        "part": "foot_back",
        "rest_x": 2.0, "rest_y": 82.0, "rest_rot": 2.0,
        "pivot_x": 28.0, "pivot_y": 20.0,
        "z_index": 3,
        "tip_offset": (42.0, 22.0),
    },
    {
        "name": "Thigh_R",
        "parent": "Hip",
        "part": "leg_thigh_front",
        "rest_x": -26.0, "rest_y": 22.0, "rest_rot": 14.0,
        "pivot_x": 44.0, "pivot_y": 22.0,
        "z_index": 4,
        "tip_child": "Shin_R",
    },
    {
        "name": "Shin_R",
        "parent": "Thigh_R",
        "part": "leg_shin_front",
        "rest_x": -4.0, "rest_y": 56.0, "rest_rot": -4.0,
        "pivot_x": 46.0, "pivot_y": 20.0,
        "z_index": 5,
        "tip_child": "Foot_R",
    },
    {
        "name": "Foot_R",
        "parent": "Shin_R",
        "part": "foot_front",
        "rest_x": -6.0, "rest_y": 80.0, "rest_rot": 0.0,
        "pivot_x": 32.0, "pivot_y": 18.0,
        "z_index": 6,
        "tip_offset": (-4.0, 36.0),
    },
    {
        "name": "Chest",
        "parent": "Hip",
        "part": "chest",
        "rest_x": 0.0, "rest_y": 4.0, "rest_rot": 0.0,
        "pivot_x": 58.0, "pivot_y": 124.0,
        "z_index": 8,
        "tip_offset": (2.0, -96.0),
    },
    {
        "name": "Cloak",
        "parent": "Chest",
        "part": "cloak",
        "rest_x": -34.0, "rest_y": -82.0, "rest_rot": 0.0,
        "pivot_x": 124.0, "pivot_y": 28.0,
        "z_index": 0,
        "tip_offset": (-72.0, 56.0),
    },
    {
        "name": "UpperArm_R",
        "parent": "Chest",
        "part": "arm_upper_back",
        "rest_x": 32.0, "rest_y": -84.0, "rest_rot": -38.0,
        "pivot_x": 32.0, "pivot_y": 22.0,
        "z_index": 6,
        "tip_child": "Forearm_R",
    },
    {
        "name": "Forearm_R",
        "parent": "UpperArm_R",
        "part": "arm_lower_back",
        "rest_x": 8.0, "rest_y": 44.0, "rest_rot": 34.0,
        "pivot_x": 20.0, "pivot_y": 24.0,
        "z_index": 9,
        "tip_child": "Hand_R",
    },
    {
        "name": "Hand_R",
        "parent": "Forearm_R",
        "part": "hand_back",
        "rest_x": 52.0, "rest_y": 20.0, "rest_rot": 4.0,
        "pivot_x": 20.0, "pivot_y": 22.0,
        "z_index": 10,
        "tip_offset": (26.0, 8.0),
    },
    {
        "name": "Head",
        "parent": "Chest",
        "part": "head",
        "rest_x": 4.0, "rest_y": -102.0, "rest_rot": 0.0,
        "pivot_x": 54.0, "pivot_y": 88.0,
        "z_index": 11,
        "tip_offset": (2.0, -64.0),
    },
    {
        "name": "UpperArm_L",
        "parent": "Chest",
        "part": "arm_upper_front",
        "rest_x": -38.0, "rest_y": -80.0, "rest_rot": 16.0,
        "pivot_x": 34.0, "pivot_y": 22.0,
        "z_index": 12,
        "tip_child": "Forearm_L",
    },
    {
        "name": "Forearm_L",
        "parent": "UpperArm_L",
        "part": "arm_lower_front",
        "rest_x": -4.0, "rest_y": 44.0, "rest_rot": -14.0,
        "pivot_x": 32.0, "pivot_y": 20.0,
        "z_index": 15,
        "tip_child": "Hand_L",
    },
    {
        "name": "Hand_L",
        "parent": "Forearm_L",
        "part": "hand_front",
        "rest_x": -4.0, "rest_y": 46.0, "rest_rot": -2.0,
        "pivot_x": 34.0, "pivot_y": 20.0,
        "z_index": 14,
        "tip_child": "Sword",
    },
    {
        "name": "Sword",
        "parent": "Hand_L",
        "part": "sword",
        "rest_x": -2.0, "rest_y": 8.0, "rest_rot": 0.0,
        "pivot_x": 38.0, "pivot_y": 34.0,
        "z_index": 13,
        "tip_offset": (132.0, 98.0),
    },
    {
        "name": "Pauldron",
        "parent": "Chest",
        "part": "pauldron",
        "rest_x": -38.0, "rest_y": -88.0, "rest_rot": 0.0,
        "pivot_x": 58.0, "pivot_y": 46.0,
        "z_index": 16,
        "tip_offset": (-22.0, 18.0),
    },
]

VFX_LIST = ["fx_slash", "fx_slash_heavy", "fx_spark", "fx_dust"]

PART_IMAGES = {}
for b in BONES:
    p = os.path.join(PARTS_DIR, f"{b['part']}.png")
    im = Image.open(p).convert("RGBA")
    PART_IMAGES[b["part"]] = im
    w, h = im.size
    b["width"] = w
    b["height"] = h
    b["offset_x"] = round(w / 2.0 - b["pivot_x"], 2)
    b["offset_y"] = round(h / 2.0 - b["pivot_y"], 2)

for fx in VFX_LIST:
    p = os.path.join(PARTS_DIR, f"{fx}.png")
    PART_IMAGES[fx] = Image.open(p).convert("RGBA")

# 2. Define the 6 Actions with Full 18-Bone Support for C003 (Đao Phủ Đồi Thi — Front-Hand Great-Cleaver)
ACTIONS = {
    "idle": {
        "grid": (2, 2),
        "length": 1.2,
        "loop": True,
        "frames": [
            {"t": 0.0, "Hip": (0, 0, 0), "Chest": (0, 0, 0), "Head": (0, 0, 0), "Cloak": (0, 0, 0), "UpperArm_R": (0, 0, 0), "Forearm_R": (0, 0, 0), "Hand_R": (0, 0, 0), "UpperArm_L": (0, 0, 0), "Forearm_L": (0, 0, 0), "Hand_L": (0, 0, 0), "Sword": (0, 0, 0), "Thigh_R": (0, 0, 0), "Shin_R": (0, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (0, 0, 0), "Shin_L": (0, 0, 0), "Foot_L": (0, 0, 0)},
            {"t": 0.3, "Hip": (0, 3, 0), "Chest": (2, 0, 0), "Head": (-2, 0, 0), "Cloak": (-4, 0, 0), "UpperArm_R": (3, 0, 0), "Forearm_R": (2, 0, 0), "Hand_R": (-2, 0, 0), "UpperArm_L": (-3, 0, 0), "Forearm_L": (-2, 0, 0), "Hand_L": (-2, 0, 0), "Sword": (-2, 0, 0), "Thigh_R": (-3, 0, 0), "Shin_R": (3, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (-2, 0, 0), "Shin_L": (2, 0, 0), "Foot_L": (0, 0, 0)},
            {"t": 0.6, "Hip": (0, 6, 0), "Chest": (4, 0, 0), "Head": (-3, 0, 0), "Cloak": (-8, 0, 0), "UpperArm_R": (5, 0, 0), "Forearm_R": (4, 0, 0), "Hand_R": (-3, 0, 0), "UpperArm_L": (-6, 0, 0), "Forearm_L": (-4, 0, 0), "Hand_L": (-3, 0, 0), "Sword": (-4, 0, 0), "Thigh_R": (-5, 0, 0), "Shin_R": (5, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (-4, 0, 0), "Shin_L": (4, 0, 0), "Foot_L": (0, 0, 0)},
            {"t": 0.9, "Hip": (0, 2, 0), "Chest": (1, 0, 0), "Head": (-1, 0, 0), "Cloak": (-3, 0, 0), "UpperArm_R": (2, 0, 0), "Forearm_R": (1, 0, 0), "Hand_R": (-1, 0, 0), "UpperArm_L": (-2, 0, 0), "Forearm_L": (-1, 0, 0), "Hand_L": (-1, 0, 0), "Sword": (-1, 0, 0), "Thigh_R": (-2, 0, 0), "Shin_R": (2, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (-1, 0, 0), "Shin_L": (1, 0, 0), "Foot_L": (0, 0, 0)},
        ],
    },
    "walk": {
        "grid": (2, 3),
        "length": 0.9,
        "loop": True,
        "frames": [
            {"t": 0.00, "Hip": (-4, 4, 2), "Chest": (4, 0, 0), "Head": (-3, 0, 0), "Cloak": (-10, 0, 0), "UpperArm_R": (12, 0, 0), "Forearm_R": (4, 0, 0), "Hand_R": (0, 0, 0), "UpperArm_L": (-14, 0, 0), "Forearm_L": (-8, 0, 0), "Hand_L": (-4, 0, 0), "Sword": (-4, 0, 0), "Thigh_R": (-20, 12, -4), "Shin_R": (8, 0, 0), "Foot_R": (6, 0, 0), "Thigh_L": (16, -10, 0), "Shin_L": (12, 0, 0), "Foot_L": (10, 0, 0)},
            {"t": 0.15, "Hip": (-2, 6, 2), "Chest": (5, 0, 0), "Head": (-4, 0, 0), "Cloak": (-14, 0, 0), "UpperArm_R": (6, 0, 0), "Forearm_R": (2, 0, 0), "Hand_R": (0, 0, 0), "UpperArm_L": (-8, 0, 0), "Forearm_L": (-4, 0, 0), "Hand_L": (-2, 0, 0), "Sword": (-2, 0, 0), "Thigh_R": (-10, 8, -2), "Shin_R": (10, 0, 0), "Foot_R": (2, 0, 0), "Thigh_L": (6, -6, 0), "Shin_L": (18, 0, 0), "Foot_L": (12, 0, 0)},
            {"t": 0.30, "Hip": (0, -2, 0), "Chest": (3, 0, 0), "Head": (-2, 0, 0), "Cloak": (-8, 0, 0), "UpperArm_R": (-6, 0, 0), "Forearm_R": (-4, 0, 0), "Hand_R": (0, 0, 0), "UpperArm_L": (6, 0, 0), "Forearm_L": (-2, 0, 0), "Hand_L": (0, 0, 0), "Sword": (2, 0, 0), "Thigh_R": (2, 4, 0), "Shin_R": (6, 0, 0), "Foot_R": (-4, 0, 0), "Thigh_L": (-10, 6, -4), "Shin_L": (16, 0, 0), "Foot_L": (6, 0, 0)},
            {"t": 0.45, "Hip": (4, 4, 2), "Chest": (5, 0, 0), "Head": (-3, 0, 0), "Cloak": (-12, 0, 0), "UpperArm_R": (-12, 0, 0), "Forearm_R": (-6, 0, 0), "Hand_R": (-2, 0, 0), "UpperArm_L": (12, 0, 0), "Forearm_L": (-4, 0, 0), "Hand_L": (2, 0, 0), "Sword": (4, 0, 0), "Thigh_R": (14, -10, 0), "Shin_R": (12, 0, 0), "Foot_R": (8, 0, 0), "Thigh_L": (-20, 14, -4), "Shin_L": (6, 0, 0), "Foot_L": (-4, 0, 0)},
            {"t": 0.60, "Hip": (2, 6, 2), "Chest": (6, 0, 0), "Head": (-4, 0, 0), "Cloak": (-15, 0, 0), "UpperArm_R": (-6, 0, 0), "Forearm_R": (-4, 0, 0), "Hand_R": (0, 0, 0), "UpperArm_L": (6, 0, 0), "Forearm_L": (-4, 0, 0), "Hand_L": (0, 0, 0), "Sword": (2, 0, 0), "Thigh_R": (6, -6, 0), "Shin_R": (18, 0, 0), "Foot_R": (10, 0, 0), "Thigh_L": (-8, 8, -2), "Shin_L": (10, 0, 0), "Foot_L": (0, 0, 0)},
            {"t": 0.75, "Hip": (-2, -2, 0), "Chest": (3, 0, 0), "Head": (-2, 0, 0), "Cloak": (-8, 0, 0), "UpperArm_R": (4, 0, 0), "Forearm_R": (0, 0, 0), "Hand_R": (0, 0, 0), "UpperArm_L": (-6, 0, 0), "Forearm_L": (-4, 0, 0), "Hand_L": (-2, 0, 0), "Sword": (-2, 0, 0), "Thigh_R": (-8, 6, -2), "Shin_R": (12, 0, 0), "Foot_R": (4, 0, 0), "Thigh_L": (4, -4, 0), "Shin_L": (8, 0, 0), "Foot_L": (4, 0, 0)},
        ],
    },
    "attack": {
        "grid": (2, 2),
        "length": 0.65,
        "loop": False,
        "frames": [
            {"t": 0.00, "Hip": (-8, 4, -4), "Chest": (-8, 0, 0), "Head": (6, 0, 0), "Cloak": (8, 0, 0), "UpperArm_R": (16, 0, 0), "Forearm_R": (10, 0, 0), "Hand_R": (6, 0, 0), "UpperArm_L": (-54, 0, -6), "Forearm_L": (-28, 0, 0), "Hand_L": (-18, 0, 0), "Sword": (-24, 0, 0), "Thigh_R": (10, -6, 0), "Shin_R": (10, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (-10, 6, 0), "Shin_L": (8, 0, 0), "Foot_L": (0, 0, 0)},
            {"t": 0.18, "Hip": (10, 6, 6), "Chest": (10, 0, 0), "Head": (-6, 0, 0), "Cloak": (-18, 0, 0), "UpperArm_R": (-18, 0, 0), "Forearm_R": (-12, 0, 0), "Hand_R": (-6, 0, 0), "UpperArm_L": (-18, 8, 0), "Forearm_L": (-8, 0, 0), "Hand_L": (-6, 0, 0), "Sword": (-12, 0, 0), "Thigh_R": (-16, 10, -2), "Shin_R": (10, 0, 0), "Foot_R": (4, 0, 0), "Thigh_L": (14, -8, 0), "Shin_L": (12, 0, 0), "Foot_L": (4, 0, 0),
             "vfx": {"fx_slash": {"pos": (346, 258), "rot": 18, "scale": 0.88, "alpha": 0.94}}},
            {"t": 0.36, "Hip": (12, 10, 8), "Chest": (12, 0, 0), "Head": (-8, 0, 0), "Cloak": (-22, 0, 0), "UpperArm_R": (-24, 0, 0), "Forearm_R": (-14, 0, 0), "Hand_R": (-8, 0, 0), "UpperArm_L": (6, 6, 0), "Forearm_L": (4, 0, 0), "Hand_L": (4, 0, 0), "Sword": (6, 0, 0), "Thigh_R": (-20, 12, -4), "Shin_R": (12, 0, 0), "Foot_R": (6, 0, 0), "Thigh_L": (18, -10, 0), "Shin_L": (14, 0, 0), "Foot_L": (6, 0, 0),
             "vfx": {"fx_spark": {"pos": (376, 344), "rot": 0, "scale": 0.82, "alpha": 0.92}}},
            {"t": 0.52, "Hip": (2, 2, 1), "Chest": (2, 0, 0), "Head": (-1, 0, 0), "Cloak": (-4, 0, 0), "UpperArm_R": (-4, 0, 0), "Forearm_R": (-2, 0, 0), "Hand_R": (0, 0, 0), "UpperArm_L": (-2, 0, 0), "Forearm_L": (0, 0, 0), "Hand_L": (0, 0, 0), "Sword": (0, 0, 0), "Thigh_R": (-4, 2, 0), "Shin_R": (4, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (4, -2, 0), "Shin_L": (4, 0, 0), "Foot_L": (0, 0, 0)},
        ],
    },
    "cast": {
        "grid": (2, 3),
        "length": 0.95,
        "loop": False,
        "frames": [
            {"t": 0.00, "Hip": (-10, 8, -4), "Chest": (-8, 0, 0), "Head": (6, 0, 0), "Cloak": (10, 0, 0), "UpperArm_R": (18, 0, 0), "Forearm_R": (12, 0, 0), "Hand_R": (6, 0, 0), "UpperArm_L": (-48, 0, -4), "Forearm_L": (-24, 0, 0), "Hand_L": (-16, 0, 0), "Sword": (-20, 0, 0), "Thigh_R": (8, -4, 0), "Shin_R": (12, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (-10, 6, 0), "Shin_L": (10, 0, 0), "Foot_L": (0, 0, 0),
             "vfx": {"fx_dust": {"pos": (224, 434), "rot": 0, "scale": 0.68, "alpha": 0.76}}},
            {"t": 0.16, "Hip": (-14, 12, -6), "Chest": (-12, 0, 0), "Head": (10, 0, 0), "Cloak": (14, 0, 0), "UpperArm_R": (24, 0, 0), "Forearm_R": (16, 0, 0), "Hand_R": (8, 0, 0), "UpperArm_L": (-64, 0, -8), "Forearm_L": (-32, 0, 0), "Hand_L": (-22, 0, 0), "Sword": (-28, 0, 0), "Thigh_R": (12, -6, 0), "Shin_R": (16, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (-14, 8, 0), "Shin_L": (14, 0, 0), "Foot_L": (0, 0, 0),
             "vfx": {"fx_dust": {"pos": (218, 432), "rot": 0, "scale": 0.82, "alpha": 0.86}}},
            {"t": 0.34, "Hip": (12, 4, 6), "Chest": (10, 0, 0), "Head": (-8, 0, 0), "Cloak": (-20, 0, 0), "UpperArm_R": (-20, 0, 0), "Forearm_R": (-12, 0, 0), "Hand_R": (-6, 0, 0), "UpperArm_L": (-24, 10, 0), "Forearm_L": (-12, 0, 0), "Hand_L": (-10, 0, 0), "Sword": (-18, 0, 0), "Thigh_R": (-18, 12, -4), "Shin_R": (12, 0, 0), "Foot_R": (4, 0, 0), "Thigh_L": (16, -10, 0), "Shin_L": (14, 0, 0), "Foot_L": (6, 0, 0),
             "vfx": {
                 "fx_slash_heavy": {"pos": (286, 268), "rot": 0, "scale": 0.94, "alpha": 0.95},
                 "fx_dust": {"pos": (196, 432), "rot": 0, "scale": 0.85, "alpha": 0.85},
             }},
            {"t": 0.52, "Hip": (16, 8, 8), "Chest": (14, 0, 0), "Head": (-10, 0, 0), "Cloak": (-24, 0, 0), "UpperArm_R": (-28, 0, 0), "Forearm_R": (-16, 0, 0), "Hand_R": (-8, 0, 0), "UpperArm_L": (4, 8, 0), "Forearm_L": (0, 0, 0), "Hand_L": (-2, 0, 0), "Sword": (-4, 0, 0), "Thigh_R": (-22, 14, -4), "Shin_R": (14, 0, 0), "Foot_R": (6, 0, 0), "Thigh_L": (20, -12, 0), "Shin_L": (16, 0, 0), "Foot_L": (8, 0, 0),
             "vfx": {
                 "fx_slash_heavy": {"pos": (306, 276), "rot": 45, "scale": 0.88, "alpha": 0.82},
                 "fx_spark": {"pos": (378, 336), "rot": 12, "scale": 0.84, "alpha": 0.94},
             }},
            {"t": 0.70, "Hip": (8, 4, 4), "Chest": (6, 0, 0), "Head": (-4, 0, 0), "Cloak": (-12, 0, 0), "UpperArm_R": (-12, 0, 0), "Forearm_R": (-6, 0, 0), "Hand_R": (-2, 0, 0), "UpperArm_L": (2, 4, 0), "Forearm_L": (0, 0, 0), "Hand_L": (0, 0, 0), "Sword": (0, 0, 0), "Thigh_R": (-10, 6, -2), "Shin_R": (8, 0, 0), "Foot_R": (2, 0, 0), "Thigh_L": (8, -4, 0), "Shin_L": (8, 0, 0), "Foot_L": (4, 0, 0),
             "vfx": {"fx_spark": {"pos": (384, 342), "rot": 25, "scale": 0.58, "alpha": 0.56}}},
            {"t": 0.86, "Hip": (0, 0, 0), "Chest": (0, 0, 0), "Head": (0, 0, 0), "Cloak": (0, 0, 0), "UpperArm_R": (0, 0, 0), "Forearm_R": (0, 0, 0), "Hand_R": (0, 0, 0), "UpperArm_L": (0, 0, 0), "Forearm_L": (0, 0, 0), "Hand_L": (0, 0, 0), "Sword": (0, 0, 0), "Thigh_R": (0, 0, 0), "Shin_R": (0, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (0, 0, 0), "Shin_L": (0, 0, 0), "Foot_L": (0, 0, 0)},
        ],
    },
    "hurt": {
        "grid": (2, 2),
        "length": 0.55,
        "loop": False,
        "frames": [
            {"t": 0.00, "Hip": (-10, 4, -6), "Chest": (-12, 0, 0), "Head": (-14, 0, 0), "Cloak": (12, 0, 0), "UpperArm_R": (10, 0, 0), "Forearm_R": (8, 0, 0), "Hand_R": (6, 0, 0), "UpperArm_L": (14, 0, 0), "Forearm_L": (-8, 0, 0), "Hand_L": (-6, 0, 0), "Sword": (-8, 0, 0), "Thigh_R": (8, 0, 0), "Shin_R": (6, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (-6, 0, 0), "Shin_L": (8, 0, 0), "Foot_L": (0, 0, 0),
             "vfx": {"fx_spark": {"pos": (254, 214), "rot": -15, "scale": 0.68, "alpha": 0.90}}},
            {"t": 0.15, "Hip": (-16, 8, -8), "Chest": (-14, 0, 0), "Head": (-18, 0, 0), "Cloak": (18, 0, 0), "UpperArm_R": (16, 0, 0), "Forearm_R": (12, 0, 0), "Hand_R": (8, 0, 0), "UpperArm_L": (20, 0, 0), "Forearm_L": (-12, 0, 0), "Hand_L": (-10, 0, 0), "Sword": (-12, 0, 0), "Thigh_R": (12, 0, 0), "Shin_R": (10, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (-10, 0, 0), "Shin_L": (12, 0, 0), "Foot_L": (0, 0, 0)},
            {"t": 0.32, "Hip": (-8, 4, -4), "Chest": (-6, 0, 0), "Head": (-8, 0, 0), "Cloak": (8, 0, 0), "UpperArm_R": (6, 0, 0), "Forearm_R": (4, 0, 0), "Hand_R": (4, 0, 0), "UpperArm_L": (8, 0, 0), "Forearm_L": (-4, 0, 0), "Hand_L": (-4, 0, 0), "Sword": (-4, 0, 0), "Thigh_R": (6, 0, 0), "Shin_R": (4, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (-4, 0, 0), "Shin_L": (6, 0, 0), "Foot_L": (0, 0, 0)},
            {"t": 0.48, "Hip": (0, 0, 0), "Chest": (0, 0, 0), "Head": (0, 0, 0), "Cloak": (0, 0, 0), "UpperArm_R": (0, 0, 0), "Forearm_R": (0, 0, 0), "Hand_R": (0, 0, 0), "UpperArm_L": (0, 0, 0), "Forearm_L": (0, 0, 0), "Hand_L": (0, 0, 0), "Sword": (0, 0, 0), "Thigh_R": (0, 0, 0), "Shin_R": (0, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (0, 0, 0), "Shin_L": (0, 0, 0), "Foot_L": (0, 0, 0)},
        ],
    },
    "death": {
        "grid": (2, 3),
        "length": 1.10,
        "loop": False,
        "frames": [
            {"t": 0.00, "Hip": (-12, 6, -8), "Chest": (-14, 0, 0), "Head": (-16, 0, 0), "Cloak": (12, 0, 0), "UpperArm_R": (-12, 0, 0), "Forearm_R": (-8, 0, 0), "Hand_R": (-6, 0, 0), "UpperArm_L": (16, 0, 0), "Forearm_L": (-8, 0, 0), "Hand_L": (-8, 0, 0), "Sword": (-10, 0, 0), "Thigh_R": (10, 0, 0), "Shin_R": (10, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (-8, 0, 0), "Shin_L": (12, 0, 0), "Foot_L": (0, 0, 0),
             "vfx": {"fx_spark": {"pos": (254, 212), "rot": 0, "scale": 0.72, "alpha": 0.92}}},
            {"t": 0.22, "Hip": (-10, 38, 14), "Chest": (16, 0, 0), "Head": (14, 0, 0), "Cloak": (-10, 0, 0), "UpperArm_R": (14, 0, 0), "Forearm_R": (-10, 0, 0), "Hand_R": (-10, 0, 0), "UpperArm_L": (-16, 0, 0), "Forearm_L": (-14, 0, 0), "Hand_L": (-18, 0, 0), "Sword": (-22, 0, 0), "Thigh_R": (-42, 0, 0), "Shin_R": (68, 0, 0), "Foot_R": (14, 0, 0), "Thigh_L": (-36, 0, 0), "Shin_L": (62, 0, 0), "Foot_L": (12, 0, 0)},
            {"t": 0.45, "Hip": (-8, 72, 34), "Chest": (28, 0, 0), "Head": (20, 0, 0), "Cloak": (-18, 0, 0), "UpperArm_R": (18, 0, 0), "Forearm_R": (-20, 0, 0), "Hand_R": (-16, 0, 0), "UpperArm_L": (-38, 0, 0), "Forearm_L": (-24, 0, 0), "Hand_L": (-28, 0, 0), "Sword": (-36, 0, 0), "Thigh_R": (-68, 0, 0), "Shin_R": (96, 0, 0), "Foot_R": (18, 0, 0), "Thigh_L": (-62, 0, 0), "Shin_L": (88, 0, 0), "Foot_L": (16, 0, 0),
             "vfx": {"fx_dust": {"pos": (256, 428), "rot": 0, "scale": 0.85, "alpha": 0.82}}},
            {"t": 0.68, "Hip": (-6, 84, 46), "Chest": (32, 0, 0), "Head": (24, 0, 0), "Cloak": (-22, 0, 0), "UpperArm_R": (14, 0, 0), "Forearm_R": (-26, 0, 0), "Hand_R": (-20, 0, 0), "UpperArm_L": (-48, 0, 0), "Forearm_L": (-28, 0, 0), "Hand_L": (-32, 0, 0), "Sword": (-42, 0, 0), "Thigh_R": (-78, 0, 0), "Shin_R": (108, 0, 0), "Foot_R": (20, 0, 0), "Thigh_L": (-72, 0, 0), "Shin_L": (102, 0, 0), "Foot_L": (18, 0, 0),
             "vfx": {"fx_dust": {"pos": (264, 430), "rot": 0, "scale": 0.90, "alpha": 0.65}}, "modulate_a": 0.88},
            {"t": 0.88, "Hip": (-4, 88, 50), "Chest": (34, 0, 0), "Head": (26, 0, 0), "Cloak": (-24, 0, 0), "UpperArm_R": (12, 0, 0), "Forearm_R": (-28, 0, 0), "Hand_R": (-22, 0, 0), "UpperArm_L": (-50, 0, 0), "Forearm_L": (-30, 0, 0), "Hand_L": (-34, 0, 0), "Sword": (-44, 0, 0), "Thigh_R": (-80, 0, 0), "Shin_R": (110, 0, 0), "Foot_R": (20, 0, 0), "Thigh_L": (-74, 0, 0), "Shin_L": (104, 0, 0), "Foot_L": (18, 0, 0),
             "vfx": {"fx_dust": {"pos": (266, 430), "rot": 0, "scale": 0.75, "alpha": 0.45}}, "modulate_a": 0.52},
            {"t": 1.05, "Hip": (-4, 90, 52), "Chest": (34, 0, 0), "Head": (26, 0, 0), "Cloak": (-24, 0, 0), "UpperArm_R": (12, 0, 0), "Forearm_R": (-28, 0, 0), "Hand_R": (-22, 0, 0), "UpperArm_L": (-50, 0, 0), "Forearm_L": (-30, 0, 0), "Hand_L": (-34, 0, 0), "Sword": (-44, 0, 0), "Thigh_R": (-80, 0, 0), "Shin_R": (110, 0, 0), "Foot_R": (20, 0, 0), "Thigh_L": (-74, 0, 0), "Shin_L": (104, 0, 0), "Foot_L": (18, 0, 0),
             "modulate_a": 0.22},
        ],
    },
}

BONE_MAP = {b["name"]: b for b in BONES}


def compute_world_transforms(frame_pose=None):
    if frame_pose is None:
        frame_pose = {}
    world = {}
    for b in BONES:
        name = b["name"]
        parent = b["parent"]
        if name == "Hip":
            dx, dy, drot = frame_pose.get("Hip", (0.0, 0.0, 0.0))
        else:
            drot, dx, dy = frame_pose.get(name, (0.0, 0.0, 0.0))
        lx = b["rest_x"] + dx
        ly = b["rest_y"] + dy
        lrot = b["rest_rot"] + drot
        if parent is None:
            wx, wy, wrot = lx, ly, lrot
        else:
            px, py, prot = world[parent][:3]
            rad = math.radians(prot)
            ca, sa = math.cos(rad), math.sin(rad)
            wx = px + lx * ca - ly * sa
            wy = py + lx * sa + ly * ca
            wrot = prot + lrot
        world[name] = [wx, wy, wrot, wx, wy]

    for b in BONES:
        name = b["name"]
        wx, wy, wrot = world[name][:3]
        if "tip_child" in b and b["tip_child"] in world:
            tx, ty = world[b["tip_child"]][:2]
        elif "tip_offset" in b:
            ox, oy = b["tip_offset"]
            rad = math.radians(wrot)
            ca, sa = math.cos(rad), math.sin(rad)
            tx = wx + ox * ca - oy * sa
            ty = wy + ox * sa + oy * ca
        else:
            tx, ty = wx, wy + 32.0
        world[name][3] = tx
        world[name][4] = ty
    return world


def draw_spine_bone(draw, x0, y0, x1, y1, color=(56, 189, 248, 235), joint_color=(245, 70, 70, 255)):
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy)
    if length > 2.0:
        ux, uy = dx / length, dy / length
        px, py = -uy, ux
        w = min(5.5, max(2.8, length * 0.10))
        mid_x = x0 + dx * 0.22
        mid_y = y0 + dy * 0.22
        poly = [
            (x0, y0),
            (mid_x + px * w, mid_y + py * w),
            (x1, y1),
            (mid_x - px * w, mid_y - py * w),
        ]
        draw.polygon(poly, fill=(color[0], color[1], color[2], 145), outline=color)
    draw.ellipse([x0 - 4, y0 - 4, x0 + 4, y0 + 4], fill=joint_color, outline=(255, 255, 255, 255))
    draw.ellipse([x1 - 2.5, y1 - 2.5, x1 + 2.5, y1 + 2.5], fill=color, outline=(255, 255, 255, 220))


def paste_rotated_part(canvas, part_im, wx, wy, wrot_deg, pivot_x, pivot_y, scale=1.0, alpha=1.0):
    if alpha <= 0.01:
        return
    im = part_im
    if abs(scale - 1.0) > 1e-3:
        nw = max(1, int(round(im.width * scale)))
        nh = max(1, int(round(im.height * scale)))
        im = im.resize((nw, nh), Image.Resampling.BICUBIC)
        pivot_x *= scale
        pivot_y *= scale
    if alpha < 0.999:
        arr = np.array(im).astype(np.float32)
        arr[:, :, 3] *= alpha
        im = Image.fromarray(arr.astype(np.uint8))

    max_r = int(math.ceil(math.hypot(max(pivot_x, im.width - pivot_x), max(pivot_y, im.height - pivot_y)))) + 4
    tmp_size = max_r * 2
    tmp = Image.new("RGBA", (tmp_size, tmp_size), (0, 0, 0, 0))
    paste_x = int(round(max_r - pivot_x))
    paste_y = int(round(max_r - pivot_y))
    tmp.paste(im, (paste_x, paste_y))
    rot_im = tmp.rotate(-wrot_deg, resample=Image.Resampling.BICUBIC, expand=False)
    dest_x = int(round(wx - max_r))
    dest_y = int(round(wy - max_r))
    canvas.alpha_composite(rot_im, (dest_x, dest_y))


def render_pose(frame_pose=None, canvas_size=512):
    if frame_pose is None:
        frame_pose = {}
    canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    world = compute_world_transforms(frame_pose)
    mod_a = frame_pose.get("modulate_a", 1.0)

    sorted_bones = sorted(BONES, key=lambda b: b["z_index"])
    for b in sorted_bones:
        wx, wy, wrot = world[b["name"]][:3]
        paste_rotated_part(
            canvas,
            PART_IMAGES[b["part"]],
            wx, wy, wrot,
            b["pivot_x"], b["pivot_y"],
            scale=1.0,
            alpha=mod_a,
        )

    vfx_dict = frame_pose.get("vfx", {})
    for fx_name, fx_cfg in vfx_dict.items():
        fx_im = PART_IMAGES[fx_name]
        fx_pos = fx_cfg["pos"]
        fx_rot = fx_cfg.get("rot", 0.0)
        fx_scale = fx_cfg.get("scale", 1.0)
        fx_alpha = fx_cfg.get("alpha", 1.0)
        paste_rotated_part(
            canvas,
            fx_im,
            fx_pos[0], fx_pos[1], fx_rot,
            fx_im.width / 2.0, fx_im.height / 2.0,
            scale=fx_scale,
            alpha=fx_alpha,
        )
    return canvas, world


try:
    font_title = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 15)
    font_sub = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 12)
except Exception:
    font_title = ImageFont.load_default()
    font_sub = ImageFont.load_default()

# 4A. Parts Catalog Audit
cat_cols, cat_rows = 6, 4
cell_w, cell_h = 280, 286
cat_im = Image.new("RGBA", (cat_cols * cell_w + 16, cat_rows * cell_h + 16), (22, 26, 34, 255))
cat_draw = ImageDraw.Draw(cat_im)

all_catalog_items = [(b["part"], b["pivot_x"], b["pivot_y"]) for b in [
    BONE_MAP["Head"], BONE_MAP["Chest"], BONE_MAP["Hip"], BONE_MAP["Cloak"], BONE_MAP["Pauldron"],
    BONE_MAP["UpperArm_L"], BONE_MAP["Forearm_L"], BONE_MAP["Hand_L"], BONE_MAP["Sword"],
    BONE_MAP["UpperArm_R"], BONE_MAP["Forearm_R"], BONE_MAP["Hand_R"],
    BONE_MAP["Thigh_R"], BONE_MAP["Shin_R"], BONE_MAP["Foot_R"],
    BONE_MAP["Thigh_L"], BONE_MAP["Shin_L"], BONE_MAP["Foot_L"],
]] + [(fx, PART_IMAGES[fx].width / 2.0, PART_IMAGES[fx].height / 2.0) for fx in VFX_LIST]

for idx, (pname, px, py) in enumerate(all_catalog_items):
    r_i, c_i = divmod(idx, cat_cols)
    ox = 8 + c_i * cell_w
    oy = 8 + r_i * cell_h
    cat_draw.rectangle([ox + 4, oy + 4, ox + cell_w - 4, oy + cell_h - 4], fill=(28, 33, 43, 255), outline=(65, 75, 95, 255), width=1)
    pim = PART_IMAGES[pname]
    pa = np.array(pim)[:, :, 3]
    edge_clip = int(pa[0, :].sum() + pa[-1, :].sum() + pa[:, 0].sum() + pa[:, -1].sum())
    px_x = ox + (cell_w - pim.width) // 2
    px_y = oy + 38 + (cell_h - 46 - pim.height) // 2
    cat_im.alpha_composite(pim, (px_x, px_y))
    cat_draw.rectangle([px_x, px_y, px_x + pim.width, px_y + pim.height], outline=(90, 220, 135, 180), width=1)
    dot_x, dot_y = px_x + px, px_y + py
    cat_draw.ellipse([dot_x - 4, dot_y - 4, dot_x + 4, dot_y + 4], fill=(240, 60, 60, 255), outline=(255, 255, 255, 255))
    cat_draw.text((ox + 12, oy + 8), f"{idx+1}. {pname} ({pim.width}x{pim.height})", fill=(230, 236, 245, 255), font=font_sub)
    cat_draw.text((ox + 12, oy + 23), f"edge_clip: {edge_clip}px | pivot red dot", fill=(100, 230, 140, 255), font=font_sub)

cat_path = os.path.join(QC_DIR, "c003_parts_catalog_audit.png")
cat_im.save(cat_path)

# 4B. Reassembly Verification Board
reassembled_im, rest_world = render_pose({}, 512)
ra_alpha = np.array(reassembled_im)[:, :, 3]
ra_edge = int(ra_alpha[0, :].sum() + ra_alpha[-1, :].sum() + ra_alpha[:, 0].sum() + ra_alpha[:, -1].sum())
ys_ra, xs_ra = np.where(ra_alpha > 15)
print(f"Reassembled 18-Bone Rest Pose bbox: x=[{xs_ra.min()}..{xs_ra.max()}], y=[{ys_ra.min()}..{ys_ra.max()}], edge_clip={ra_edge}px")

ref_im = Image.open(os.path.join(HERO_DIR, "reference/c003_reference_clean.png")).convert("RGBA")
ref_scaled = ref_im.resize((450, 450), Image.Resampling.LANCZOS)
ref_canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
ref_canvas.alpha_composite(ref_scaled, (31, 20))

ver_im = Image.new("RGBA", (3 * 532 + 16, 560), (18, 22, 30, 255))
ver_draw = ImageDraw.Draw(ver_im, "RGBA")
titles = [
    "1. ANH REFERENCE GOC (Muse AI — Cam Dai Dao Tay Front)",
    f"2. GHEP THU 18 MANH BO PHAN (edge_clip={ra_edge}px, Tay Front cam vu khi)",
    "3. CAY XUONG SPINE 18 BONE2D (UpperArm_L->Forearm_L->Hand_L->Sword)",
]
for i, (title, pane_im) in enumerate([(titles[0], ref_canvas), (titles[1], reassembled_im), (titles[2], reassembled_im.copy())]):
    ox = 12 + i * 532
    oy = 12
    ver_draw.rectangle([ox, oy, ox + 516, oy + 536], fill=(26, 31, 42, 255), outline=(70, 82, 105, 255), width=1)
    ver_im.alpha_composite(pane_im, (ox + 2, oy + 22))
    ver_draw.line([(ox + 36, oy + 22 + 440), (ox + 480, oy + 22 + 440)], fill=(110, 235, 150, 200), width=2)
    ver_draw.text((ox + 12, oy + 8), title, fill=(235, 240, 250, 255), font=font_sub)
    if i == 2:
        chest_tx, chest_ty = rest_world["Chest"][3], rest_world["Chest"][4]
        for child_name in ["Head", "UpperArm_L", "UpperArm_R", "Pauldron", "Cloak"]:
            cx, cy = rest_world[child_name][:2]
            ver_draw.line([(ox + 2 + chest_tx, oy + 22 + chest_ty), (ox + 2 + cx, oy + 22 + cy)], fill=(148, 163, 184, 160), width=1)
        hip_wx, hip_wy = rest_world["Hip"][:2]
        for leg_name in ["Thigh_L", "Thigh_R"]:
            lx, ly = rest_world[leg_name][:2]
            ver_draw.line([(ox + 2 + hip_wx, oy + 22 + hip_wy), (ox + 2 + lx, oy + 22 + ly)], fill=(148, 163, 184, 160), width=1)

        for b in BONES:
            wx, wy, _, tx, ty = rest_world[b["name"]]
            draw_spine_bone(ver_draw, ox + 2 + wx, oy + 22 + wy, ox + 2 + tx, oy + 22 + ty)

ver_path = os.path.join(QC_DIR, "c003_reassembly_verification.png")
ver_im.save(ver_path)

# 4C. All 6 Actions Overview Board
ov_w, ov_h = 3 * 560 + 24, 2 * 560 + 24
ov_im = Image.new("RGBA", (ov_w, ov_h), (16, 19, 26, 255))
ov_draw = ImageDraw.Draw(ov_im)
total_edge_clips = 0

action_order = ["idle", "walk", "attack", "cast", "hurt", "death"]
for a_idx, act_name in enumerate(action_order):
    act = ACTIONS[act_name]
    rows, cols = act["grid"]
    frames = act["frames"]
    ar, ac = divmod(a_idx, 3)
    bx = 12 + ac * 560
    by = 12 + ar * 560
    ov_draw.rectangle([bx, by, bx + 544, by + 544], fill=(24, 28, 38, 255), outline=(65, 75, 95, 255), width=1)

    thumb_size = 240 if cols == 2 else 166
    grid_w = cols * thumb_size
    grid_h = rows * thumb_size
    gx0 = bx + (544 - grid_w) // 2
    gy0 = by + 36 + (500 - grid_h) // 2

    sheet_im = Image.new("RGBA", (cols * 512, rows * 512), (0, 0, 0, 0))

    act_clips = 0
    for f_idx, f_pose in enumerate(frames):
        f_im, _ = render_pose(f_pose, 512)
        fa = np.array(f_im)[:, :, 3]
        f_clip = int(fa[0, :].sum() + fa[-1, :].sum() + fa[:, 0].sum() + fa[:, -1].sum())
        act_clips += f_clip
        total_edge_clips += f_clip

        fr, fc = divmod(f_idx, cols)
        sheet_im.alpha_composite(f_im, (fc * 512, fr * 512))

        tx = gx0 + fc * thumb_size
        ty = gy0 + fr * thumb_size
        ov_draw.rectangle([tx + 2, ty + 2, tx + thumb_size - 2, ty + thumb_size - 2], fill=(28, 33, 44, 255), outline=(50, 58, 74, 255), width=1)
        thumb = f_im.resize((thumb_size - 8, thumb_size - 8), Image.Resampling.LANCZOS)
        ov_im.alpha_composite(thumb, (tx + 4, ty + 4))
        base_y = ty + 4 + int(round(440.0 * (thumb_size - 8) / 512.0))
        ov_draw.line([(tx + 12, base_y), (tx + thumb_size - 12, base_y)], fill=(100, 220, 140, 170), width=1)

    sheet_path = os.path.join(QC_DIR, f"c003_{act_name}_{rows}x{cols}_sheet.png")
    sheet_im.save(sheet_path)

    ov_draw.text(
        (bx + 14, by + 10),
        f"Action {a_idx+1}: {act_name.upper()} ({rows}x{cols} | {len(frames)} frames | edge_clip={act_clips}px)",
        fill=(235, 240, 250, 255),
        font=font_title,
    )

assert total_edge_clips == 0, f"Found {total_edge_clips} edge-clipped pixels!"
ov_path = os.path.join(QC_DIR, "c003_all_6_actions_overview.png")
ov_im.save(ov_path)
print(f"Saved 6-action overview -> {ov_path} (total_edge_clips={total_edge_clips}px)")

for src, dst_name in [
    (cat_path, "c003_parts_catalog_audit.png"),
    (ver_path, "c003_reassembly_verification.png"),
    (ov_path, "c003_all_6_actions_overview.png"),
]:
    shutil.copyfile(src, os.path.join(ARTIFACT_DIR, dst_name))

# Update Mobile WebP parts
mob_parts_dir = "/Users/dochung/Desktop/card_g/assets/mobile/heroes/c003_dao_phu_doi_thi/parts"
os.makedirs(mob_parts_dir, exist_ok=True)
for png_file in sorted(glob.glob(os.path.join(PARTS_DIR, "*.png"))):
    bname = os.path.splitext(os.path.basename(png_file))[0]
    im = Image.open(png_file).convert("RGBA")
    im.save(os.path.join(mob_parts_dir, f"{bname}.webp"), "WEBP", quality=90, method=6)


# 5. Generate Native Godot 4 Scene (.tscn) & Script (.gd)
def generate_tscn_content(bones_data, actions_data):
    lines = []
    ext_count = 1 + len(bones_data) + len(VFX_LIST)
    sub_count = 1 + len(actions_data)
    lines.append(f'[gd_scene load_steps={ext_count + sub_count} format=3 uid="uid://c003daophudoithi"]')
    lines.append("")
    lines.append('[ext_resource type="Script" path="res://assets/heroes/c003_dao_phu_doi_thi/godot/c003_dao_phu_doi_thi.gd" id="1_script"]')

    part_ext_id = {}
    idx = 2
    for b in bones_data:
        p = b["part"]
        part_ext_id[p] = f"{idx}_{p}"
        lines.append(f'[ext_resource type="Texture2D" path="res://assets/heroes/c003_dao_phu_doi_thi/godot/parts/{p}.png" id="{part_ext_id[p]}"]')
        idx += 1
    for fx in VFX_LIST:
        part_ext_id[fx] = f"{idx}_{fx}"
        lines.append(f'[ext_resource type="Texture2D" path="res://assets/heroes/c003_dao_phu_doi_thi/godot/parts/{fx}.png" id="{part_ext_id[fx]}"]')
        idx += 1
    lines.append("")

    bone_paths = {}
    for b in bones_data:
        if b["parent"] is None:
            bone_paths[b["name"]] = f"Skeleton2D/{b['name']}"
        else:
            bone_paths[b["name"]] = f"{bone_paths[b['parent']]}/{b['name']}"

    for act_name, act in actions_data.items():
        frames = act["frames"]
        length = act["length"]
        loop_mode = 1 if act["loop"] else 0
        lines.append(f'[sub_resource type="Animation" id="Animation_{act_name}"]')
        lines.append(f'resource_name = "{act_name}"')
        lines.append(f'length = {length:.2f}')
        lines.append(f'loop_mode = {loop_mode}')

        t_idx = 0
        times_str = ", ".join(f"{f['t']:.2f}" for f in frames)
        trans_str = ", ".join("1" for _ in frames)

        for b in bones_data:
            bname = b["name"]
            bpath = bone_paths[bname]
            rots = []
            positions = []
            for f in frames:
                if bname == "Hip":
                    dx, dy, drot = f.get("Hip", (0.0, 0.0, 0.0))
                else:
                    drot, dx, dy = f.get(bname, (0.0, 0.0, 0.0))
                rad = math.radians(b["rest_rot"] + drot)
                px = b["rest_x"] + dx
                py = b["rest_y"] + dy
                rots.append(f"{rad:.4f}")
                positions.append(f"Vector2({px:.1f}, {py:.1f})")

            lines.append(f'tracks/{t_idx}/type = "value"')
            lines.append(f'tracks/{t_idx}/imported = false')
            lines.append(f'tracks/{t_idx}/enabled = true')
            lines.append(f'tracks/{t_idx}/path = NodePath("{bpath}:rotation")')
            lines.append(f'tracks/{t_idx}/interp = 1')
            lines.append(f'tracks/{t_idx}/loop_wrap = true')
            lines.append(f'tracks/{t_idx}/keys = {{')
            lines.append(f'"times": PackedFloat32Array({times_str}),')
            lines.append(f'"transitions": PackedFloat32Array({trans_str}),')
            lines.append(f'"update": 0,')
            lines.append(f'"values": [{", ".join(rots)}]')
            lines.append(f'}}')
            t_idx += 1

            lines.append(f'tracks/{t_idx}/type = "value"')
            lines.append(f'tracks/{t_idx}/imported = false')
            lines.append(f'tracks/{t_idx}/enabled = true')
            lines.append(f'tracks/{t_idx}/path = NodePath("{bpath}:position")')
            lines.append(f'tracks/{t_idx}/interp = 1')
            lines.append(f'tracks/{t_idx}/loop_wrap = true')
            lines.append(f'tracks/{t_idx}/keys = {{')
            lines.append(f'"times": PackedFloat32Array({times_str}),')
            lines.append(f'"transitions": PackedFloat32Array({trans_str}),')
            lines.append(f'"update": 0,')
            lines.append(f'"values": [{", ".join(positions)}]')
            lines.append(f'}}')
            t_idx += 1

        mod_vals = [f'Color(1, 1, 1, {f.get("modulate_a", 1.0):.2f})' for f in frames]
        lines.append(f'tracks/{t_idx}/type = "value"')
        lines.append(f'tracks/{t_idx}/imported = false')
        lines.append(f'tracks/{t_idx}/enabled = true')
        lines.append(f'tracks/{t_idx}/path = NodePath("Skeleton2D:modulate")')
        lines.append(f'tracks/{t_idx}/interp = 1')
        lines.append(f'tracks/{t_idx}/loop_wrap = true')
        lines.append(f'tracks/{t_idx}/keys = {{')
        lines.append(f'"times": PackedFloat32Array({times_str}),')
        lines.append(f'"transitions": PackedFloat32Array({trans_str}),')
        lines.append(f'"update": 0,')
        lines.append(f'"values": [{", ".join(mod_vals)}]')
        lines.append(f'}}')
        t_idx += 1

        for fx in VFX_LIST:
            vis_vals, pos_vals, rot_vals, scale_vals, col_vals = [], [], [], [], []
            for f in frames:
                vfx_d = f.get("vfx", {}).get(fx)
                if vfx_d:
                    vis_vals.append("true")
                    pos_vals.append(f"Vector2({vfx_d['pos'][0]:.1f}, {vfx_d['pos'][1]:.1f})")
                    rot_vals.append(f"{math.radians(vfx_d.get('rot', 0.0)):.4f}")
                    sc = vfx_d.get("scale", 1.0)
                    scale_vals.append(f"Vector2({sc:.2f}, {sc:.2f})")
                    col_vals.append(f"Color(1, 1, 1, {vfx_d.get('alpha', 1.0):.2f})")
                else:
                    vis_vals.append("false")
                    pos_vals.append("Vector2(256, 256)")
                    rot_vals.append("0.0")
                    scale_vals.append("Vector2(1, 1)")
                    col_vals.append("Color(1, 1, 1, 0)")

            for prop_name, update_mode, vals_list in [
                ("visible", 1, vis_vals),
                ("position", 0, pos_vals),
                ("rotation", 0, rot_vals),
                ("scale", 0, scale_vals),
                ("modulate", 0, col_vals),
            ]:
                lines.append(f'tracks/{t_idx}/type = "value"')
                lines.append(f'tracks/{t_idx}/imported = false')
                lines.append(f'tracks/{t_idx}/enabled = true')
                lines.append(f'tracks/{t_idx}/path = NodePath("VFXLayer/{fx}:{prop_name}")')
                lines.append(f'tracks/{t_idx}/interp = 1')
                lines.append(f'tracks/{t_idx}/loop_wrap = true')
                lines.append(f'tracks/{t_idx}/keys = {{')
                lines.append(f'"times": PackedFloat32Array({times_str}),')
                lines.append(f'"transitions": PackedFloat32Array({trans_str}),')
                lines.append(f'"update": {update_mode},')
                lines.append(f'"values": [{", ".join(vals_list)}]')
                lines.append(f'}}')
                t_idx += 1
        lines.append("")

    lines.append('[sub_resource type="AnimationLibrary" id="AnimationLibrary_c003"]')
    lines.append('_data = {')
    for act_name in actions_data.keys():
        lines.append(f'"{act_name}": SubResource("Animation_{act_name}"),')
    lines.append('}')
    lines.append("")

    lines.append('[node name="C003_DaoPhuDoiThi" type="Node2D"]')
    lines.append('script = ExtResource("1_script")')
    lines.append("")
    lines.append('[node name="Skeleton2D" type="Skeleton2D" parent="."]')
    lines.append("")

    for b in bones_data:
        bname = b["name"]
        parent_path = "Skeleton2D" if b["parent"] is None else bone_paths[b["parent"]]
        rad = math.radians(b["rest_rot"])
        ca, sa = math.cos(rad), math.sin(rad)
        rx, ry = b["rest_x"], b["rest_y"]
        if "tip_child" in b and b["tip_child"] in BONE_MAP:
            cb = BONE_MAP[b["tip_child"]]
            tx, ty = cb["rest_x"], cb["rest_y"]
        else:
            tx, ty = b.get("tip_offset", (0.0, 42.0))
        b_len = max(8.0, math.hypot(tx, ty))
        b_ang = math.atan2(ty, tx)

        lines.append(f'[node name="{bname}" type="Bone2D" parent="{parent_path}"]')
        lines.append(f'position = Vector2({rx:.1f}, {ry:.1f})')
        lines.append(f'rotation = {rad:.4f}')
        lines.append(f'rest = Transform2D({ca:.4f}, {sa:.4f}, {-sa:.4f}, {ca:.4f}, {rx:.1f}, {ry:.1f})')
        lines.append('auto_calculate_length_and_angle = false')
        lines.append(f'length = {b_len:.1f}')
        lines.append(f'bone_angle = {b_ang:.4f}')
        lines.append("")

        lines.append(f'[node name="Sprite" type="Sprite2D" parent="{bone_paths[bname]}"]')
        lines.append(f'z_index = {b["z_index"]}')
        lines.append('z_as_relative = false')
        lines.append(f'texture = ExtResource("{part_ext_id[b["part"]]}")')
        lines.append(f'offset = Vector2({b["offset_x"]:.2f}, {b["offset_y"]:.2f})')
        lines.append("")

    lines.append('[node name="VFXLayer" type="Node2D" parent="."]')
    lines.append('z_index = 20')
    lines.append('z_as_relative = false')
    lines.append("")
    for fx in VFX_LIST:
        lines.append(f'[node name="{fx}" type="Sprite2D" parent="VFXLayer"]')
        lines.append('visible = false')
        lines.append('position = Vector2(256, 256)')
        lines.append(f'texture = ExtResource("{part_ext_id[fx]}")')
        lines.append("")

    lines.append('[node name="AnimationPlayer" type="AnimationPlayer" parent="."]')
    lines.append('libraries = {')
    lines.append('"": SubResource("AnimationLibrary_c003")')
    lines.append('}')
    lines.append('autoplay = "idle"')
    lines.append("")
    return "\n".join(lines)


tscn_text = generate_tscn_content(BONES, ACTIONS)
with open(TSCN_PATH, "w", encoding="utf-8") as f:
    f.write(tscn_text)
print(f"Wrote 18-Bone Godot 4 .tscn -> {TSCN_PATH}")

gd_script_content = """extends Node2D
class_name HeroC003DaoPhuDoiThi

## Tướng 003 (C03): Đao Phủ Đồi Thi — Cấp độ hiếm N (Common)
## Hệ Vật Lý / Đấu Sĩ Cận Chiến (MeleeAoE) — 18 Bone2D Cutout Rig (Cầm Đại Đao Tay Front)
## Stats chuẩn GAME_DESIGN.md: HP 280 | Mana 65 | Khiên 20 | Dame 33 | ASPD 1.05/s | Range 1.3 (Gần) | Giáp 28 | K.Phép 18 | MSPD 120
## Kỹ năng [65 Mana]: Xoáy Trảm — Vung đại đao xoay tròn gây 115% Dame vật lý lên toàn bộ kẻ địch đứng xung quanh.

const HERO_ID: String = "c003_dao_phu_doi_thi"
const RARITY: String = "N"
const MAX_HP: int = 280
const MAX_MANA: int = 65
const INITIAL_SHIELD: int = 20
const BASE_DAMAGE: int = 33
const ATTACK_SPEED: float = 1.05
const ATTACK_RANGE: float = 1.3
const ARMOR: int = 28
const MAGIC_RESIST: int = 18
const MOVE_SPEED: int = 120

@onready var anim_player: AnimationPlayer = $AnimationPlayer
@onready var skeleton: Skeleton2D = $Skeleton2D

func _ready() -> void:
	play_action("idle")

func play_action(action_name: String) -> void:
	if anim_player and anim_player.has_animation(action_name):
		anim_player.play(action_name)
"""
with open(GD_PATH, "w", encoding="utf-8") as f:
    f.write(gd_script_content)
print(f"Wrote Godot 4 .gd script -> {GD_PATH}")

initial_state = {
    "hero_id": "c003_dao_phu_doi_thi",
    "tscn_path": TSCN_PATH,
    "bones": BONES,
    "vfx_list": VFX_LIST,
    "actions": ACTIONS,
}
with open(RIG_STATE_PATH, "w", encoding="utf-8") as f:
    json.dump(initial_state, f, ensure_ascii=False, indent=2)

b64_sprites = {}
for pname in [b["part"] for b in BONES] + VFX_LIST:
    p = os.path.join(PARTS_DIR, f"{pname}.png")
    with open(p, "rb") as fp:
        b64_sprites[pname] = "data:image/png;base64," + base64.b64encode(fp.read()).decode("ascii")

with open(os.path.join(HERO_DIR, "reference/c003_reference_clean.png"), "rb") as fp:
    ref_b64 = "data:image/png;base64," + base64.b64encode(fp.read()).decode("ascii")

with open("/Users/dochung/Desktop/card_g/tools/build_c001_rig_and_editor.py", "r", encoding="utf-8") as fp:
    c001_script = fp.read()

start_marker = 'html_content = f"""<!DOCTYPE html>'
end_marker = 'with open(HTML_EDITOR_PATH, "w", encoding="utf-8") as f:'
c001_editor_block = c001_script.split(start_marker)[1].split(end_marker)[0]

c003_html = "<!DOCTYPE html>" + c001_editor_block.strip()
if c003_html.endswith('"""'):
    c003_html = c003_html[:-3]

c003_html = c003_html.replace("{{", "{").replace("}}", "}")
c003_html = c003_html.replace("{json.dumps(b64_sprites)}", json.dumps(b64_sprites))
c003_html = c003_html.replace("{json.dumps(ref_b64)}", json.dumps(ref_b64))
c003_html = c003_html.replace("{json.dumps(initial_state, ensure_ascii=False)}", json.dumps(initial_state, ensure_ascii=False))
c003_html = c003_html.replace("C001 — Hắc Kiếm Tàn Binh", "C003 — Đao Phủ Đồi Thi")
c003_html = c003_html.replace("CẤP N — KIM", "CẤP N — ĐẤU SĨ ĐẠI ĐAO")
c003_html = c003_html.replace("c001_hac_kiem_tan_binh", "c003_dao_phu_doi_thi")
c003_html = c003_html.replace("C001_HacKiemTanBinh", "C003_DaoPhuDoiThi")
c003_html = c003_html.replace("AnimationLibrary_c001", "AnimationLibrary_c003")
c003_html = c003_html.replace("uid://c001hackiemtanbinh", "uid://c003daophudoithi")

with open(HTML_EDITOR_PATH, "w", encoding="utf-8") as f:
    f.write(c003_html)
print(f"Generated 18-Bone Interactive HTML Editor -> {HTML_EDITOR_PATH} ({os.path.getsize(HTML_EDITOR_PATH)/1024:.1f} KB)")
