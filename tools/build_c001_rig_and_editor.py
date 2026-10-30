#!/usr/bin/env python3
"""
Builds the anatomically verified C001 — Hắc Kiếm Tàn Binh (Rarity N) 2D Skeletal Cutout Rig
with a full 18-Bone Spine Hierarchy:
- Torso & Head: Hip -> Chest -> Head, Cloak, Pauldron
- Right Arm (Closer): UpperArm_L (Shoulder->Elbow) -> Forearm_L (Elbow->Wrist) -> Hand_L (Wrist->Fingers)
- Left Sword Arm (Farther): UpperArm_R (Shoulder->Elbow) -> Forearm_R (Elbow->Wrist) -> Hand_R (Wrist->Fist) -> Sword (Hilt->BladeTip)
- Right Leg (Closer): Thigh_R (Hip->Knee) -> Shin_R (Knee->Ankle) -> Foot_R (Ankle->Toe)
- Left Leg (Farther): Thigh_L (Hip->Knee) -> Shin_L (Knee->Ankle) -> Foot_L (Ankle->Toe)
"""
import os
import json
import math
import glob
import base64
import shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERO_DIR = "/Users/dochung/Desktop/card_g/assets/heroes/c001_hac_kiem_tan_binh"
PARTS_DIR = os.path.join(HERO_DIR, "godot/parts")
QC_DIR = os.path.join(HERO_DIR, "qc_previews")
GODOT_DIR = os.path.join(HERO_DIR, "godot")
TSCN_PATH = os.path.join(GODOT_DIR, "c001_hac_kiem_tan_binh.tscn")
HTML_EDITOR_PATH = os.path.join(HERO_DIR, "c001_editor.html")
ARTIFACT_DIR = "/Users/dochung/.gemini/antigravity/brain/e3bbf70e-78bc-4496-9ca6-743d5d0bbf43"

os.makedirs(QC_DIR, exist_ok=True)

# --- 1. Full 18-Bone Hierarchy (Shoulder -> Elbow -> Wrist -> Hand & Hip -> Knee -> Ankle -> Foot) ---
# Each bone specifies:
# - rest_x, rest_y, rest_rot: local transform relative to parent Bone2D
# - pivot_x, pivot_y: pixel coordinate inside the part PNG where the Bone2D joint sits
# - tip_child or tip_offset: where the bone segment ends (for Spine-style bone visualization & Godot Bone2D length/angle)
BONES = [
    {
        "name": "Hip",
        "parent": None,
        "part": "hip_kilt",
        "rest_x": 206.0, "rest_y": 248.0, "rest_rot": 0.0,
        "pivot_x": 72.0, "pivot_y": 36.5,
        "z_index": 6,
        "tip_child": "Chest",
    },
    {
        "name": "Thigh_L",
        "parent": "Hip",
        "part": "leg_thigh_back",
        "rest_x": 22.0, "rest_y": 14.0, "rest_rot": -12.0,
        "pivot_x": 41.8, "pivot_y": 24.4,
        "z_index": 1,
        "tip_child": "Shin_L",
    },
    {
        "name": "Shin_L",
        "parent": "Thigh_L",
        "part": "leg_shin_back",
        "rest_x": 4.0, "rest_y": 64.0, "rest_rot": 6.0,
        "pivot_x": 58.0, "pivot_y": 28.0,
        "z_index": 2,
        "tip_child": "Foot_L",
    },
    {
        "name": "Foot_L",
        "parent": "Shin_L",
        "part": "foot_back",
        "rest_x": -12.0, "rest_y": 76.0, "rest_rot": 0.0,
        "pivot_x": 38.0, "pivot_y": 26.0,
        "z_index": 3,
        "tip_offset": (34.0, 22.0),
    },
    {
        "name": "Thigh_R",
        "parent": "Hip",
        "part": "leg_thigh_front",
        "rest_x": -22.0, "rest_y": 16.0, "rest_rot": 10.0,
        "pivot_x": 46.3, "pivot_y": 24.8,
        "z_index": 4,
        "tip_child": "Shin_R",
    },
    {
        "name": "Shin_R",
        "parent": "Thigh_R",
        "part": "leg_shin_front",
        "rest_x": -4.0, "rest_y": 66.0, "rest_rot": -4.0,
        "pivot_x": 48.0, "pivot_y": 28.0,
        "z_index": 5,
        "tip_child": "Foot_R",
    },
    {
        "name": "Foot_R",
        "parent": "Shin_R",
        "part": "foot_front",
        "rest_x": -8.0, "rest_y": 78.0, "rest_rot": 0.0,
        "pivot_x": 32.0, "pivot_y": 22.0,
        "z_index": 6,
        "tip_offset": (2.0, 36.0),
    },
    {
        "name": "Chest",
        "parent": "Hip",
        "part": "chest",
        "rest_x": 0.0, "rest_y": -8.0, "rest_rot": 0.0,
        "pivot_x": 67.0, "pivot_y": 141.1,
        "z_index": 8,
        "tip_offset": (2.0, -92.0),
    },
    {
        "name": "Cloak",
        "parent": "Chest",
        "part": "cloak",
        "rest_x": -20.0, "rest_y": -88.0, "rest_rot": 6.0,
        "pivot_x": 68.6, "pivot_y": 29.4,
        "z_index": 0,
        "tip_offset": (-8.0, 128.0),
    },
    {
        "name": "UpperArm_R",
        "parent": "Chest",
        "part": "arm_upper_back",
        "rest_x": 34.0, "rest_y": -84.0, "rest_rot": -28.0,
        "pivot_x": 36.0, "pivot_y": 25.1,
        "z_index": 2,
        "tip_child": "Forearm_R",
    },
    {
        "name": "Forearm_R",
        "parent": "UpperArm_R",
        "part": "arm_lower_back",
        "rest_x": 4.0, "rest_y": 54.0, "rest_rot": 4.0,
        "pivot_x": 28.0, "pivot_y": 26.0,
        "z_index": 11,
        "tip_child": "Hand_R",
    },
    {
        "name": "Hand_R",
        "parent": "Forearm_R",
        "part": "hand_back",
        "rest_x": 26.0, "rest_y": 36.0, "rest_rot": 0.0,
        "pivot_x": 28.0, "pivot_y": 26.0,
        "z_index": 12,
        "tip_child": "Sword",
    },
    {
        "name": "Sword",
        "parent": "Hand_R",
        "part": "sword",
        "rest_x": 12.0, "rest_y": 16.0, "rest_rot": 18.0,
        "pivot_x": 54.8, "pivot_y": 41.2,
        "z_index": 10,
        "tip_offset": (146.0, 106.0),
    },
    {
        "name": "Head",
        "parent": "Chest",
        "part": "head",
        "rest_x": 4.0, "rest_y": -112.0, "rest_rot": 0.0,
        "pivot_x": 55.7, "pivot_y": 93.2,
        "z_index": 9,
        "tip_offset": (2.0, -64.0),
    },
    {
        "name": "UpperArm_L",
        "parent": "Chest",
        "part": "arm_upper_front",
        "rest_x": -38.0, "rest_y": -88.0, "rest_rot": 26.0,
        "pivot_x": 40.0, "pivot_y": 25.5,
        "z_index": 13,
        "tip_child": "Forearm_L",
    },
    {
        "name": "Forearm_L",
        "parent": "UpperArm_L",
        "part": "arm_lower_front",
        "rest_x": -4.0, "rest_y": 56.0, "rest_rot": -6.0,
        "pivot_x": 44.0, "pivot_y": 26.0,
        "z_index": 15,
        "tip_child": "Hand_L",
    },
    {
        "name": "Hand_L",
        "parent": "Forearm_L",
        "part": "hand_front",
        "rest_x": -16.0, "rest_y": 36.0, "rest_rot": 0.0,
        "pivot_x": 38.0, "pivot_y": 22.0,
        "z_index": 14,
        "tip_offset": (-8.0, 38.0),
    },
    {
        "name": "Pauldron",
        "parent": "Chest",
        "part": "pauldron",
        "rest_x": -24.0, "rest_y": -92.0, "rest_rot": 0.0,
        "pivot_x": 45.0, "pivot_y": 28.0,
        "z_index": 16,
        "tip_offset": (-20.0, 18.0),
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

# --- 2. Define the 6 Actions with Full 18-Bone Support (including Hand_L, Hand_R, Foot_R, Foot_L) ---
ACTIONS = {
    "idle": {
        "grid": (2, 2),
        "length": 1.2,
        "loop": True,
        "frames": [
            {"t": 0.0, "Hip": (0, 0, 0), "Chest": (0, 0, 0), "Head": (0, 0, 0), "Cloak": (0, 0, 0), "UpperArm_R": (0, 0, 0), "Forearm_R": (0, 0, 0), "Hand_R": (0, 0, 0), "Sword": (0, 0, 0), "UpperArm_L": (0, 0, 0), "Forearm_L": (0, 0, 0), "Hand_L": (0, 0, 0), "Thigh_R": (0, 0, 0), "Shin_R": (0, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (0, 0, 0), "Shin_L": (0, 0, 0), "Foot_L": (0, 0, 0)},
            {"t": 0.3, "Hip": (0, 3, 0), "Chest": (2, 0, 0), "Head": (-2, 0, 0), "Cloak": (4, 0, 0), "UpperArm_R": (3, 0, 0), "Forearm_R": (3, 0, 0), "Hand_R": (-2, 0, 0), "Sword": (0, 0, 0), "UpperArm_L": (-3, 0, 0), "Forearm_L": (-3, 0, 0), "Hand_L": (-2, 0, 0), "Thigh_R": (-3, 0, 0), "Shin_R": (3, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (-2, 0, 0), "Shin_L": (2, 0, 0), "Foot_L": (0, 0, 0)},
            {"t": 0.6, "Hip": (0, 6, 0), "Chest": (3, 0, 0), "Head": (-3, 0, 0), "Cloak": (7, 0, 0), "UpperArm_R": (5, 0, 0), "Forearm_R": (5, 0, 0), "Hand_R": (-3, 0, 0), "Sword": (0, 0, 0), "UpperArm_L": (-5, 0, 0), "Forearm_L": (-5, 0, 0), "Hand_L": (-4, 0, 0), "Thigh_R": (-5, 0, 0), "Shin_R": (5, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (-4, 0, 0), "Shin_L": (4, 0, 0), "Foot_L": (0, 0, 0)},
            {"t": 0.9, "Hip": (0, 2, 0), "Chest": (1, 0, 0), "Head": (-1, 0, 0), "Cloak": (3, 0, 0), "UpperArm_R": (2, 0, 0), "Forearm_R": (2, 0, 0), "Hand_R": (-1, 0, 0), "Sword": (0, 0, 0), "UpperArm_L": (-2, 0, 0), "Forearm_L": (-2, 0, 0), "Hand_L": (-2, 0, 0), "Thigh_R": (-2, 0, 0), "Shin_R": (2, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (-1, 0, 0), "Shin_L": (1, 0, 0), "Foot_L": (0, 0, 0)},
        ],
    },
    "walk": {
        "grid": (2, 3),
        "length": 0.9,
        "loop": True,
        "frames": [
            {"t": 0.00, "Hip": (-6, 4, 2), "Chest": (4, 0, 0), "Head": (-3, 0, 0), "Cloak": (12, 0, 0), "UpperArm_R": (6, 0, 0), "Forearm_R": (2, 0, 0), "Hand_R": (-4, 0, 0), "Sword": (0, 0, 0), "UpperArm_L": (-16, 0, 0), "Forearm_L": (-8, 0, 0), "Hand_L": (-4, 0, 0), "Thigh_R": (-22, 14, -4), "Shin_R": (8, 0, 0), "Foot_R": (8, 0, 0), "Thigh_L": (18, -12, 0), "Shin_L": (14, 0, 0), "Foot_L": (12, 0, 0)},
            {"t": 0.15, "Hip": (-4, 7, 2), "Chest": (5, 0, 0), "Head": (-4, 0, 0), "Cloak": (15, 0, 0), "UpperArm_R": (2, 0, 0), "Forearm_R": (0, 0, 0), "Hand_R": (-2, 0, 0), "Sword": (0, 0, 0), "UpperArm_L": (-10, 0, 0), "Forearm_L": (-6, 0, 0), "Hand_L": (-2, 0, 0), "Thigh_R": (-12, 10, -2), "Shin_R": (10, 0, 0), "Foot_R": (2, 0, 0), "Thigh_L": (6, -8, 0), "Shin_L": (22, 0, 0), "Foot_L": (14, 0, 0)},
            {"t": 0.30, "Hip": (0, -2, 0), "Chest": (3, 0, 0), "Head": (-2, 0, 0), "Cloak": (9, 0, 0), "UpperArm_R": (-4, 0, 0), "Forearm_R": (-4, 0, 0), "Hand_R": (-2, 0, 0), "Sword": (0, 0, 0), "UpperArm_L": (6, 0, 0), "Forearm_L": (-6, 0, 0), "Hand_L": (0, 0, 0), "Thigh_R": (2, 4, 0), "Shin_R": (6, 0, 0), "Foot_R": (-4, 0, 0), "Thigh_L": (-12, 6, -4), "Shin_L": (18, 0, 0), "Foot_L": (8, 0, 0)},
            {"t": 0.45, "Hip": (4, 4, 2), "Chest": (5, 0, 0), "Head": (-3, 0, 0), "Cloak": (13, 0, 0), "UpperArm_R": (-2, 0, 0), "Forearm_R": (0, 0, 0), "Hand_R": (0, 0, 0), "Sword": (0, 0, 0), "UpperArm_L": (16, 0, 0), "Forearm_L": (-6, 0, 0), "Hand_L": (4, 0, 0), "Thigh_R": (16, -12, 0), "Shin_R": (14, 0, 0), "Foot_R": (10, 0, 0), "Thigh_L": (-22, 16, -4), "Shin_L": (6, 0, 0), "Foot_L": (-6, 0, 0)},
            {"t": 0.60, "Hip": (2, 7, 2), "Chest": (6, 0, 0), "Head": (-4, 0, 0), "Cloak": (16, 0, 0), "UpperArm_R": (-4, 0, 0), "Forearm_R": (-2, 0, 0), "Hand_R": (-2, 0, 0), "Sword": (0, 0, 0), "UpperArm_L": (10, 0, 0), "Forearm_L": (-8, 0, 0), "Hand_L": (2, 0, 0), "Thigh_R": (6, -8, 0), "Shin_R": (20, 0, 0), "Foot_R": (12, 0, 0), "Thigh_L": (-10, 10, -2), "Shin_L": (10, 0, 0), "Foot_L": (0, 0, 0)},
            {"t": 0.75, "Hip": (-2, -2, 0), "Chest": (3, 0, 0), "Head": (-2, 0, 0), "Cloak": (10, 0, 0), "UpperArm_R": (2, 0, 0), "Forearm_R": (0, 0, 0), "Hand_R": (-2, 0, 0), "Sword": (0, 0, 0), "UpperArm_L": (-6, 0, 0), "Forearm_L": (-8, 0, 0), "Hand_L": (-2, 0, 0), "Thigh_R": (-10, 6, -2), "Shin_R": (14, 0, 0), "Foot_R": (4, 0, 0), "Thigh_L": (4, -4, 0), "Shin_L": (8, 0, 0), "Foot_L": (4, 0, 0)},
        ],
    },
    "attack": {
        "grid": (2, 2),
        "length": 0.65,
        "loop": False,
        "frames": [
            {"t": 0.00, "Hip": (-8, 4, -4), "Chest": (-6, 0, 0), "Head": (6, 0, 0), "Cloak": (-8, 0, 0), "UpperArm_R": (-24, 0, 0), "Forearm_R": (-16, 0, 0), "Hand_R": (-14, 0, 0), "Sword": (-10, 0, 0), "UpperArm_L": (14, 0, 0), "Forearm_L": (-14, 0, 0), "Hand_L": (-6, 0, 0), "Thigh_R": (10, -6, 0), "Shin_R": (10, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (-12, 8, 0), "Shin_L": (8, 0, 0), "Foot_L": (0, 0, 0)},
            {"t": 0.18, "Hip": (12, 6, 5), "Chest": (8, 0, 0), "Head": (-6, 0, 0), "Cloak": (18, 0, 0), "UpperArm_R": (4, 0, 0), "Forearm_R": (4, 0, 0), "Hand_R": (2, 0, 0), "Sword": (4, 0, 0), "UpperArm_L": (-20, 0, 0), "Forearm_L": (-10, 0, 0), "Hand_L": (-4, 0, 0), "Thigh_R": (-18, 12, -2), "Shin_R": (10, 0, 0), "Foot_R": (4, 0, 0), "Thigh_L": (16, -10, 0), "Shin_L": (14, 0, 0), "Foot_L": (6, 0, 0),
             "vfx": {"fx_slash": {"pos": (356, 242), "rot": 12, "scale": 0.90, "alpha": 0.95}}},
            {"t": 0.36, "Hip": (16, 10, 6), "Chest": (10, 0, 0), "Head": (-8, 0, 0), "Cloak": (22, 0, 0), "UpperArm_R": (12, 0, 0), "Forearm_R": (8, 0, 0), "Hand_R": (6, 0, 0), "Sword": (6, 0, 0), "UpperArm_L": (-26, 0, 0), "Forearm_L": (-8, 0, 0), "Hand_L": (-4, 0, 0), "Thigh_R": (-22, 14, -4), "Shin_R": (12, 0, 0), "Foot_R": (6, 0, 0), "Thigh_L": (20, -12, 0), "Shin_L": (16, 0, 0), "Foot_L": (8, 0, 0),
             "vfx": {"fx_spark": {"pos": (388, 336), "rot": 0, "scale": 0.80, "alpha": 0.94}}},
            {"t": 0.52, "Hip": (4, 2, 2), "Chest": (3, 0, 0), "Head": (-2, 0, 0), "Cloak": (6, 0, 0), "UpperArm_R": (2, 0, 0), "Forearm_R": (2, 0, 0), "Hand_R": (0, 0, 0), "Sword": (0, 0, 0), "UpperArm_L": (-6, 0, 0), "Forearm_L": (-6, 0, 0), "Hand_L": (0, 0, 0), "Thigh_R": (-4, 2, 0), "Shin_R": (4, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (4, -2, 0), "Shin_L": (4, 0, 0), "Foot_L": (0, 0, 0)},
        ],
    },
    "cast": {
        "grid": (2, 3),
        "length": 0.95,
        "loop": False,
        "frames": [
            {"t": 0.00, "Hip": (-10, 8, -4), "Chest": (-6, 0, 0), "Head": (4, 0, 0), "Cloak": (-6, 0, 0), "UpperArm_R": (-22, 0, 0), "Forearm_R": (-14, 0, 0), "Hand_R": (-12, 0, 0), "Sword": (-10, 0, 0), "UpperArm_L": (12, 0, 0), "Forearm_L": (-14, 0, 0), "Hand_L": (-6, 0, 0), "Thigh_R": (8, -4, 0), "Shin_R": (12, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (-10, 6, 0), "Shin_L": (10, 0, 0), "Foot_L": (0, 0, 0),
             "vfx": {"fx_dust": {"pos": (214, 428), "rot": 0, "scale": 0.65, "alpha": 0.75}}},
            {"t": 0.16, "Hip": (-14, 12, -5), "Chest": (-8, 0, 0), "Head": (8, 0, 0), "Cloak": (-12, 0, 0), "UpperArm_R": (-24, 0, 0), "Forearm_R": (-15, 0, 0), "Hand_R": (-12, 0, 0), "Sword": (-10, 0, 0), "UpperArm_L": (20, 0, 0), "Forearm_L": (-18, 0, 0), "Hand_L": (-8, 0, 0), "Thigh_R": (12, -6, 0), "Shin_R": (16, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (-14, 8, 0), "Shin_L": (14, 0, 0), "Foot_L": (0, 0, 0),
             "vfx": {"fx_dust": {"pos": (208, 426), "rot": 0, "scale": 0.82, "alpha": 0.88}}},
            {"t": 0.34, "Hip": (16, 4, 6), "Chest": (10, 0, 0), "Head": (-8, 0, 0), "Cloak": (22, 0, 0), "UpperArm_R": (4, 0, 0), "Forearm_R": (4, 0, 0), "Hand_R": (2, 0, 0), "Sword": (4, 0, 0), "UpperArm_L": (-24, 0, 0), "Forearm_L": (-10, 0, 0), "Hand_L": (-4, 0, 0), "Thigh_R": (-20, 14, -4), "Shin_R": (12, 0, 0), "Foot_R": (4, 0, 0), "Thigh_L": (18, -12, 0), "Shin_L": (16, 0, 0), "Foot_L": (6, 0, 0),
             "vfx": {
                 "fx_slash_heavy": {"pos": (356, 248), "rot": 8, "scale": 0.88, "alpha": 0.98},
                 "fx_dust": {"pos": (176, 426), "rot": 0, "scale": 0.85, "alpha": 0.85},
             }},
            {"t": 0.52, "Hip": (20, 10, 8), "Chest": (12, 0, 0), "Head": (-10, 0, 0), "Cloak": (26, 0, 0), "UpperArm_R": (12, 0, 0), "Forearm_R": (8, 0, 0), "Hand_R": (6, 0, 0), "Sword": (6, 0, 0), "UpperArm_L": (-30, 0, 0), "Forearm_L": (-10, 0, 0), "Hand_L": (-4, 0, 0), "Thigh_R": (-24, 16, -4), "Shin_R": (14, 0, 0), "Foot_R": (6, 0, 0), "Thigh_L": (22, -14, 0), "Shin_L": (18, 0, 0), "Foot_L": (8, 0, 0),
             "vfx": {
                 "fx_slash_heavy": {"pos": (362, 282), "rot": 22, "scale": 0.82, "alpha": 0.80},
                 "fx_spark": {"pos": (392, 342), "rot": 10, "scale": 0.88, "alpha": 0.96},
             }},
            {"t": 0.70, "Hip": (10, 6, 4), "Chest": (6, 0, 0), "Head": (-4, 0, 0), "Cloak": (12, 0, 0), "UpperArm_R": (6, 0, 0), "Forearm_R": (4, 0, 0), "Hand_R": (2, 0, 0), "Sword": (0, 0, 0), "UpperArm_L": (-14, 0, 0), "Forearm_L": (-8, 0, 0), "Hand_L": (0, 0, 0), "Thigh_R": (-10, 8, -2), "Shin_R": (8, 0, 0), "Foot_R": (2, 0, 0), "Thigh_L": (10, -6, 0), "Shin_L": (10, 0, 0), "Foot_L": (4, 0, 0),
             "vfx": {"fx_spark": {"pos": (394, 348), "rot": 25, "scale": 0.56, "alpha": 0.55}}},
            {"t": 0.86, "Hip": (0, 0, 0), "Chest": (0, 0, 0), "Head": (0, 0, 0), "Cloak": (0, 0, 0), "UpperArm_R": (0, 0, 0), "Forearm_R": (0, 0, 0), "Hand_R": (0, 0, 0), "Sword": (0, 0, 0), "UpperArm_L": (0, 0, 0), "Forearm_L": (0, 0, 0), "Hand_L": (0, 0, 0), "Thigh_R": (0, 0, 0), "Shin_R": (0, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (0, 0, 0), "Shin_L": (0, 0, 0), "Foot_L": (0, 0, 0)},
        ],
    },
    "hurt": {
        "grid": (2, 2),
        "length": 0.55,
        "loop": False,
        "frames": [
            {"t": 0.00, "Hip": (-10, 4, -6), "Chest": (-12, 0, 0), "Head": (-14, 0, 0), "Cloak": (-14, 0, 0), "UpperArm_R": (6, 0, 0), "Forearm_R": (6, 0, 0), "Hand_R": (8, 0, 0), "Sword": (6, 0, 0), "UpperArm_L": (18, 0, 0), "Forearm_L": (-10, 0, 0), "Hand_L": (-4, 0, 0), "Thigh_R": (8, 0, 0), "Shin_R": (6, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (-6, 0, 0), "Shin_L": (8, 0, 0), "Foot_L": (0, 0, 0),
             "vfx": {"fx_spark": {"pos": (262, 214), "rot": -15, "scale": 0.65, "alpha": 0.90}}},
            {"t": 0.15, "Hip": (-18, 10, -8), "Chest": (-14, 0, 0), "Head": (-18, 0, 0), "Cloak": (-20, 0, 0), "UpperArm_R": (10, 0, 0), "Forearm_R": (8, 0, 0), "Hand_R": (10, 0, 0), "Sword": (8, 0, 0), "UpperArm_L": (28, 0, 0), "Forearm_L": (-14, 0, 0), "Hand_L": (-6, 0, 0), "Thigh_R": (14, 0, 0), "Shin_R": (12, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (-10, 0, 0), "Shin_L": (14, 0, 0), "Foot_L": (0, 0, 0)},
            {"t": 0.32, "Hip": (-10, 6, -4), "Chest": (-8, 0, 0), "Head": (-8, 0, 0), "Cloak": (-10, 0, 0), "UpperArm_R": (4, 0, 0), "Forearm_R": (4, 0, 0), "Hand_R": (6, 0, 0), "Sword": (4, 0, 0), "UpperArm_L": (12, 0, 0), "Forearm_L": (-8, 0, 0), "Hand_L": (-2, 0, 0), "Thigh_R": (6, 0, 0), "Shin_R": (6, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (-4, 0, 0), "Shin_L": (6, 0, 0), "Foot_L": (0, 0, 0)},
            {"t": 0.48, "Hip": (0, 0, 0), "Chest": (0, 0, 0), "Head": (0, 0, 0), "Cloak": (0, 0, 0), "UpperArm_R": (0, 0, 0), "Forearm_R": (0, 0, 0), "Hand_R": (0, 0, 0), "Sword": (0, 0, 0), "UpperArm_L": (0, 0, 0), "Forearm_L": (0, 0, 0), "Hand_L": (0, 0, 0), "Thigh_R": (0, 0, 0), "Shin_R": (0, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (0, 0, 0), "Shin_L": (0, 0, 0), "Foot_L": (0, 0, 0)},
        ],
    },
    "death": {
        "grid": (2, 3),
        "length": 1.10,
        "loop": False,
        "frames": [
            {"t": 0.00, "Hip": (-14, 6, -8), "Chest": (-16, 0, 0), "Head": (-18, 0, 0), "Cloak": (-16, 0, 0), "UpperArm_R": (-18, 0, 0), "Forearm_R": (-12, 0, 0), "Hand_R": (-16, 0, 0), "Sword": (0, 0, 0), "UpperArm_L": (22, 0, 0), "Forearm_L": (-10, 0, 0), "Hand_L": (-4, 0, 0), "Thigh_R": (10, 0, 0), "Shin_R": (10, 0, 0), "Foot_R": (0, 0, 0), "Thigh_L": (-8, 0, 0), "Shin_L": (12, 0, 0), "Foot_L": (0, 0, 0),
             "vfx": {"fx_spark": {"pos": (258, 212), "rot": 0, "scale": 0.72, "alpha": 0.92}}},
            {"t": 0.22, "Hip": (-6, 42, 14), "Chest": (18, 0, 0), "Head": (16, 0, 0), "Cloak": (12, 0, 0), "UpperArm_R": (12, 0, 0), "Forearm_R": (10, 0, 0), "Hand_R": (-28, 0, 0), "Sword": (0, 0, 0), "UpperArm_L": (10, 0, 0), "Forearm_L": (-14, 0, 0), "Hand_L": (-6, 0, 0), "Thigh_R": (-42, 0, 0), "Shin_R": (68, 0, 0), "Foot_R": (14, 0, 0), "Thigh_L": (-36, 0, 0), "Shin_L": (62, 0, 0), "Foot_L": (12, 0, 0)},
            {"t": 0.45, "Hip": (4, 88, 38), "Chest": (32, 0, 0), "Head": (24, 0, 0), "Cloak": (22, 0, 0), "UpperArm_R": (16, 0, 0), "Forearm_R": (-18, 0, 0), "Hand_R": (-82, 0, 0), "Sword": (0, 0, 0), "UpperArm_L": (-28, 0, 0), "Forearm_L": (-20, 0, 0), "Hand_L": (-10, 0, 0), "Thigh_R": (-68, 0, 0), "Shin_R": (96, 0, 0), "Foot_R": (18, 0, 0), "Thigh_L": (-62, 0, 0), "Shin_L": (88, 0, 0), "Foot_L": (16, 0, 0),
             "vfx": {"fx_dust": {"pos": (266, 426), "rot": 0, "scale": 0.85, "alpha": 0.82}}},
            {"t": 0.68, "Hip": (10, 102, 52), "Chest": (36, 0, 0), "Head": (28, 0, 0), "Cloak": (26, 0, 0), "UpperArm_R": (10, 0, 0), "Forearm_R": (-28, 0, 0), "Hand_R": (-92, 0, 0), "Sword": (0, 0, 0), "UpperArm_L": (-38, 0, 0), "Forearm_L": (-24, 0, 0), "Hand_L": (-12, 0, 0), "Thigh_R": (-78, 0, 0), "Shin_R": (108, 0, 0), "Foot_R": (20, 0, 0), "Thigh_L": (-72, 0, 0), "Shin_L": (102, 0, 0), "Foot_L": (18, 0, 0),
             "vfx": {"fx_dust": {"pos": (274, 428), "rot": 0, "scale": 0.92, "alpha": 0.65}}, "modulate_a": 0.88},
            {"t": 0.88, "Hip": (12, 106, 56), "Chest": (38, 0, 0), "Head": (30, 0, 0), "Cloak": (28, 0, 0), "UpperArm_R": (8, 0, 0), "Forearm_R": (-30, 0, 0), "Hand_R": (-94, 0, 0), "Sword": (0, 0, 0), "UpperArm_L": (-40, 0, 0), "Forearm_L": (-26, 0, 0), "Hand_L": (-12, 0, 0), "Thigh_R": (-80, 0, 0), "Shin_R": (110, 0, 0), "Foot_R": (20, 0, 0), "Thigh_L": (-74, 0, 0), "Shin_L": (104, 0, 0), "Foot_L": (18, 0, 0),
             "vfx": {"fx_dust": {"pos": (276, 428), "rot": 0, "scale": 0.75, "alpha": 0.45}}, "modulate_a": 0.52},
            {"t": 1.05, "Hip": (12, 108, 58), "Chest": (38, 0, 0), "Head": (30, 0, 0), "Cloak": (28, 0, 0), "UpperArm_R": (8, 0, 0), "Forearm_R": (-30, 0, 0), "Hand_R": (-94, 0, 0), "Sword": (0, 0, 0), "UpperArm_L": (-40, 0, 0), "Forearm_L": (-26, 0, 0), "Hand_L": (-12, 0, 0), "Thigh_R": (-80, 0, 0), "Shin_R": (110, 0, 0), "Foot_R": (20, 0, 0), "Thigh_L": (-74, 0, 0), "Shin_L": (104, 0, 0), "Foot_L": (18, 0, 0),
             "modulate_a": 0.22},
        ],
    },
}

# --- 3. Forward Kinematics & Spine Bone Segment Computation ---
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

    # Compute the exact Tail Tip (tx, ty) for every bone segment!
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

# --- 4. Generate QC Boards ---
try:
    font_title = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 15)
    font_sub = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 12)
except Exception:
    font_title = ImageFont.load_default()
    font_sub = ImageFont.load_default()

# 4A. Parts Catalog Audit (4x6 grid = 22 parts: 18 body parts + 4 VFX)
cat_cols, cat_rows = 6, 4
cell_w, cell_h = 280, 235
cat_im = Image.new("RGBA", (cat_cols * cell_w + 16, cat_rows * cell_h + 16), (22, 26, 34, 255))
cat_draw = ImageDraw.Draw(cat_im)

all_catalog_items = [(b["part"], b["pivot_x"], b["pivot_y"]) for b in [
    BONE_MAP["Head"], BONE_MAP["Chest"], BONE_MAP["Hip"], BONE_MAP["Cloak"], BONE_MAP["Pauldron"],
    BONE_MAP["UpperArm_L"], BONE_MAP["Forearm_L"], BONE_MAP["Hand_L"],
    BONE_MAP["UpperArm_R"], BONE_MAP["Forearm_R"], BONE_MAP["Hand_R"], BONE_MAP["Sword"],
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

cat_path = os.path.join(QC_DIR, "c001_parts_catalog_audit.png")
cat_im.save(cat_path)

# 4B. Reassembly Verification Board (with Full Spine-style 18-Bone Skeleton!)
reassembled_im, rest_world = render_pose({}, 512)
ra_alpha = np.array(reassembled_im)[:, :, 3]
ra_edge = int(ra_alpha[0, :].sum() + ra_alpha[-1, :].sum() + ra_alpha[:, 0].sum() + ra_alpha[:, -1].sum())
ys_ra, xs_ra = np.where(ra_alpha > 15)
print(f"Reassembled 18-Bone Rest Pose bbox: x=[{xs_ra.min()}..{xs_ra.max()}], y=[{ys_ra.min()}..{ys_ra.max()}], edge_clip={ra_edge}px")

ref_im = Image.open(os.path.join(HERO_DIR, "reference/c001_reference_clean.png")).convert("RGBA")
ref_scaled = ref_im.resize((450, 450), Image.Resampling.LANCZOS)
ref_canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
ref_canvas.alpha_composite(ref_scaled, (31, 20))

ver_im = Image.new("RGBA", (3 * 532 + 16, 560), (18, 22, 30, 255))
ver_draw = ImageDraw.Draw(ver_im, "RGBA")
titles = [
    "1. ANH REFERENCE NHAN VAT GOC (Muse AI)",
    f"2. GHEP THU 18 MANH BO PHAN (edge_clip={ra_edge}px, du khop Co Tay & Co Chan)",
    "3. CAY XUONG SPINE 18 BONE2D (Vai->Khuyu->CoTay->BanTay & Goi->CoChan)",
]
for i, (title, pane_im) in enumerate([(titles[0], ref_canvas), (titles[1], reassembled_im), (titles[2], reassembled_im.copy())]):
    ox = 12 + i * 532
    oy = 12
    ver_draw.rectangle([ox, oy, ox + 516, oy + 536], fill=(26, 31, 42, 255), outline=(70, 82, 105, 255), width=1)
    ver_im.alpha_composite(pane_im, (ox + 2, oy + 22))
    ver_draw.line([(ox + 36, oy + 22 + 436), (ox + 480, oy + 22 + 436)], fill=(110, 235, 150, 200), width=2)
    ver_draw.text((ox + 12, oy + 8), title, fill=(235, 240, 250, 255), font=font_sub)
    if i == 2:
        # Draw clavicle / pelvis hierarchy connector lines in dashed/thin cyan from Chest tip to Shoulder/Neck joints
        chest_tx, chest_ty = rest_world["Chest"][3], rest_world["Chest"][4]
        for child_name in ["Head", "UpperArm_L", "UpperArm_R", "Pauldron", "Cloak"]:
            cx, cy = rest_world[child_name][:2]
            ver_draw.line([(ox + 2 + chest_tx, oy + 22 + chest_ty), (ox + 2 + cx, oy + 22 + cy)], fill=(148, 163, 184, 160), width=1)
        hip_wx, hip_wy = rest_world["Hip"][:2]
        for leg_name in ["Thigh_L", "Thigh_R"]:
            lx, ly = rest_world[leg_name][:2]
            ver_draw.line([(ox + 2 + hip_wx, oy + 22 + hip_wy), (ox + 2 + lx, oy + 22 + ly)], fill=(148, 163, 184, 160), width=1)

        # Draw each of the 18 Spine bone segments from its Head (wx, wy) to its Tail (tx, ty)!
        for b in BONES:
            wx, wy, _, tx, ty = rest_world[b["name"]]
            draw_spine_bone(ver_draw, ox + 2 + wx, oy + 22 + wy, ox + 2 + tx, oy + 22 + ty)

ver_path = os.path.join(QC_DIR, "c001_reassembly_verification.png")
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

    act_clips = 0
    for f_idx, f_pose in enumerate(frames):
        f_im, _ = render_pose(f_pose, 512)
        fa = np.array(f_im)[:, :, 3]
        f_clip = int(fa[0, :].sum() + fa[-1, :].sum() + fa[:, 0].sum() + fa[:, -1].sum())
        ys_f, xs_f = np.where(fa > 15)
        print(f"  [{act_name:6s} F{f_idx}] bbox=({xs_f.min():3d},{ys_f.min():3d})->({xs_f.max():3d},{ys_f.max():3d}) | edge_clip={f_clip}px")
        act_clips += f_clip
        total_edge_clips += f_clip

        fr, fc = divmod(f_idx, cols)
        tx = gx0 + fc * thumb_size
        ty = gy0 + fr * thumb_size
        ov_draw.rectangle([tx + 2, ty + 2, tx + thumb_size - 2, ty + thumb_size - 2], fill=(28, 33, 44, 255), outline=(50, 58, 74, 255), width=1)
        thumb = f_im.resize((thumb_size - 8, thumb_size - 8), Image.Resampling.LANCZOS)
        ov_im.alpha_composite(thumb, (tx + 4, ty + 4))
        base_y = ty + 4 + int(round(436.0 * (thumb_size - 8) / 512.0))
        ov_draw.line([(tx + 12, base_y), (tx + thumb_size - 12, base_y)], fill=(100, 220, 140, 170), width=1)

    ov_draw.text(
        (bx + 14, by + 10),
        f"Action {a_idx+1}: {act_name.upper()} ({rows}x{cols} | {len(frames)} frames | edge_clip={act_clips}px)",
        fill=(235, 240, 250, 255),
        font=font_title,
    )

assert total_edge_clips == 0, f"Found {total_edge_clips} edge-clipped pixels!"
ov_path = os.path.join(QC_DIR, "c001_all_6_actions_overview.png")
ov_im.save(ov_path)
print(f"Saved 6-action overview -> {ov_path} (total_edge_clips={total_edge_clips}px)")

# --- 5. Generate Native Godot 4 Scene (.tscn) with Accurate Bone2D length & bone_angle ---
def generate_tscn_content(bones_data, actions_data):
    lines = []
    ext_count = 1 + len(bones_data) + len(VFX_LIST)
    sub_count = 1 + len(actions_data)
    lines.append(f'[gd_scene load_steps={ext_count + sub_count} format=3 uid="uid://c001hackiemtanbinh"]')
    lines.append("")
    lines.append('[ext_resource type="Script" path="res://assets/heroes/c001_hac_kiem_tan_binh/godot/c001_hac_kiem_tan_binh.gd" id="1_script"]')

    part_ext_id = {}
    idx = 2
    for b in bones_data:
        p = b["part"]
        part_ext_id[p] = f"{idx}_{p}"
        lines.append(f'[ext_resource type="Texture2D" path="res://assets/heroes/c001_hac_kiem_tan_binh/godot/parts/{p}.png" id="{part_ext_id[p]}"]')
        idx += 1
    for fx in VFX_LIST:
        part_ext_id[fx] = f"{idx}_{fx}"
        lines.append(f'[ext_resource type="Texture2D" path="res://assets/heroes/c001_hac_kiem_tan_binh/godot/parts/{fx}.png" id="{part_ext_id[fx]}"]')
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

    lines.append('[sub_resource type="AnimationLibrary" id="AnimationLibrary_c001"]')
    lines.append('_data = {')
    for act_name in actions_data.keys():
        lines.append(f'"{act_name}": SubResource("Animation_{act_name}"),')
    lines.append('}')
    lines.append("")

    lines.append('[node name="C001_HacKiemTanBinh" type="Node2D"]')
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
        # Calculate exact Bone2D length and bone_angle from tip_child or tip_offset
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
    lines.append('"": SubResource("AnimationLibrary_c001")')
    lines.append('}')
    lines.append('autoplay = "idle"')
    lines.append("")
    return "\n".join(lines)

tscn_text = generate_tscn_content(BONES, ACTIONS)
with open(TSCN_PATH, "w", encoding="utf-8") as f:
    f.write(tscn_text)
print(f"Wrote 18-Bone Godot 4 .tscn -> {TSCN_PATH}")

# Update Mobile WebP parts
mob_parts_dir = "/Users/dochung/Desktop/card_g/assets/mobile/heroes/c001_hac_kiem_tan_binh/parts"
os.makedirs(mob_parts_dir, exist_ok=True)
for png_file in sorted(glob.glob(os.path.join(PARTS_DIR, "*.png"))):
    bname = os.path.splitext(os.path.basename(png_file))[0]
    im = Image.open(png_file).convert("RGBA")
    im.save(os.path.join(mob_parts_dir, f"{bname}.webp"), "WEBP", quality=90, method=6)

for src, dst_name in [
    (cat_path, "c001_parts_catalog_audit.png"),
    (ver_path, "c001_reassembly_verification.png"),
    (ov_path, "c001_all_6_actions_overview.png"),
]:
    shutil.copyfile(src, os.path.join(ARTIFACT_DIR, dst_name))

# --- 6. Generate Interactive HTML Editor (c001_editor.html) with Full 18-Bone Spine Display ---
b64_sprites = {}
for pname in [b["part"] for b in BONES] + VFX_LIST:
    p = os.path.join(PARTS_DIR, f"{pname}.png")
    with open(p, "rb") as fp:
        b64_sprites[pname] = "data:image/png;base64," + base64.b64encode(fp.read()).decode("ascii")

with open(os.path.join(HERO_DIR, "reference/c001_reference_clean.png"), "rb") as fp:
    ref_b64 = "data:image/png;base64," + base64.b64encode(fp.read()).decode("ascii")

initial_state = {
    "hero_id": "c001_hac_kiem_tan_binh",
    "tscn_path": TSCN_PATH,
    "bones": BONES,
    "vfx_list": VFX_LIST,
    "actions": ACTIONS,
}

html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<title>C001 — Hắc Kiếm Tàn Binh | Godot 4 (.tscn) 18-Bone Spine Rig & 6-Action Editor</title>
<style>
  :root {{
    --bg: #0f131a;
    --panel: #171d28;
    --panel2: #1f2736;
    --border: #2e3a50;
    --accent: #38bdf8;
    --accent2: #22c55e;
    --warn: #f59e0b;
    --danger: #ef4444;
    --text: #e2e8f0;
    --muted: #94a3b8;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 13px;
    height: 100vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }}
  header {{
    background: var(--panel);
    border-bottom: 1px solid var(--border);
    padding: 8px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }}
  .title-wrap {{ display: flex; align-items: center; gap: 12px; }}
  .badge {{
    background: #334155;
    color: #f8fafc;
    padding: 3px 8px;
    border-radius: 6px;
    font-weight: 700;
    font-size: 11px;
  }}
  .btn {{
    background: var(--panel2);
    color: var(--text);
    border: 1px solid var(--border);
    padding: 6px 12px;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 600;
    font-size: 12px;
    transition: 0.15s;
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }}
  .btn:hover {{ border-color: var(--accent); color: #fff; }}
  .btn-primary {{
    background: linear-gradient(135deg, #16a34a, #15803d);
    border-color: #22c55e;
    color: #fff;
    font-size: 13px;
    padding: 7px 16px;
  }}
  .btn-primary:hover {{ filter: brightness(1.12); }}
  .btn.active {{ background: #0284c7; border-color: #38bdf8; color: #fff; }}
  #saveStatus {{
    font-size: 12px;
    color: var(--accent2);
    font-weight: 600;
  }}
  .preview-strip {{
    background: #121721;
    border-bottom: 1px solid var(--border);
    padding: 8px 16px;
    display: flex;
    align-items: center;
    gap: 10px;
    flex-shrink: 0;
  }}
  .action-tab {{
    background: var(--panel);
    border: 1.5px solid var(--border);
    border-radius: 8px;
    padding: 7px 16px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    font-weight: 700;
    color: var(--text);
    transition: 0.15s;
  }}
  .action-tab:hover {{ border-color: #64748b; background: var(--panel2); }}
  .action-tab.selected {{
    background: rgba(56, 189, 248, 0.16);
    border-color: var(--accent);
    color: var(--accent);
    box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2);
  }}
  .action-tab small {{
    font-weight: 500;
    font-size: 11px;
    color: var(--muted);
  }}
  .workspace {{
    flex: 1;
    display: grid;
    grid-template-columns: 320px 1fr 380px;
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
  .sidebar-right {{
    background: var(--panel);
    border-left: 1px solid var(--border);
    padding: 12px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }}
  .center-stage {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: space-between;
    padding: 12px;
    background: radial-gradient(circle at center, #1b2232 0%, #0f131a 100%);
    overflow: hidden;
  }}
  .canvas-toolbar {{
    display: flex;
    gap: 8px;
    align-items: center;
    flex-wrap: wrap;
    background: var(--panel);
    padding: 6px 12px;
    border-radius: 8px;
    border: 1px solid var(--border);
  }}
  #mainCanvas {{
    background: #181f2c;
    border: 2px solid var(--border);
    border-radius: 10px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    cursor: grab;
  }}
  #mainCanvas:active {{ cursor: grabbing; }}
  .timeline-bar {{
    width: 100%;
    max-width: 760px;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 8px 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }}
  .frame-pills {{
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
  }}
  .frame-pill {{
    padding: 5px 12px;
    border-radius: 6px;
    background: var(--panel2);
    border: 1px solid var(--border);
    color: var(--text);
    cursor: pointer;
    font-weight: 600;
    font-size: 12px;
  }}
  .frame-pill.active {{
    background: var(--accent);
    color: #0f172a;
    border-color: #fff;
  }}
  .section-title {{
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--muted);
    font-weight: 700;
    border-bottom: 1px solid var(--border);
    padding-bottom: 4px;
    margin-bottom: 6px;
  }}
  .bone-list {{
    display: flex;
    flex-direction: column;
    gap: 4px;
  }}
  .bone-item {{
    padding: 5px 10px;
    border-radius: 6px;
    background: var(--panel2);
    border: 1px solid transparent;
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .bone-item:hover {{ border-color: #475569; }}
  .bone-item.active {{
    background: rgba(56, 189, 248, 0.16);
    border-color: var(--accent);
    color: #fff;
    font-weight: 700;
  }}
  .control-group {{
    background: var(--panel2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }}
  .field-row {{
    display: grid;
    grid-template-columns: 92px 1fr 58px;
    align-items: center;
    gap: 8px;
  }}
  .field-row label {{
    font-size: 12px;
    color: var(--muted);
  }}
  input[type="range"] {{ width: 100%; accent-color: var(--accent); }}
  input[type="number"] {{
    width: 100%;
    background: #0f131a;
    border: 1px solid var(--border);
    color: var(--text);
    padding: 4px 6px;
    border-radius: 4px;
    font-size: 12px;
  }}
  .hint {{
    font-size: 11px;
    color: var(--muted);
    line-height: 1.4;
  }}
</style>
</head>
<body>

<header>
  <div class="title-wrap">
    <span class="badge">CẤP N — KIM</span>
    <h2>C001 — Hắc Kiếm Tàn Binh (18-Bone Spine Rig: Vai → Khuỷu → Cổ Tay → Bàn Tay & Đùi → Gối → Cổ Chân → Bàn Chân)</h2>
  </div>
  <div style="display:flex; align-items:center; gap:10px;">
    <span id="saveStatus">Sẵn sàng — Chỉnh sửa & bấm Save để cập nhật thẳng vào .tscn</span>
    <button class="btn" onclick="resetCurrentFrame()">↺ Reset Frame</button>
    <button class="btn" onclick="copyFramePose()">📋 Copy Pose</button>
    <button class="btn" onclick="pasteFramePose()">📥 Paste Pose</button>
    <button class="btn btn-primary" onclick="saveToTscn()">💾 Save to .tscn</button>
  </div>
</header>

<div class="preview-strip" id="previewStrip"></div>

<div class="workspace">
  <div class="sidebar">
    <div>
      <div class="section-title">1. Chọn Khớp Xương (18 Bone2D Đầy Đủ)</div>
      <div class="bone-list" id="boneList"></div>
    </div>
    <div>
      <div class="section-title">2. Chọn Hiệu Ứng (VFXLayer)</div>
      <div class="bone-list" id="vfxList"></div>
    </div>
    <div class="control-group">
      <div class="section-title">Hướng Dẫn Chuột Trên Canvas</div>
      <div class="hint">
        • <b>Click vào khớp xương</b> (chấm tròn đỏ) trên Canvas để chọn.<br>
        • <b>Kéo chuột trái:</b> Xoay góc của xương đó ở frame hiện tại.<br>
        • <b>Shift + Kéo chuột:</b> Dịch vị trí <code>(dx, dy)</code>.<br>
        • <b>Alt + Kéo chuột:</b> Chỉnh lệch mảnh ảnh <code>Sprite Offset</code>.<br>
        • Bấm <b>💾 Save to .tscn</b> để ghi đè trực tiếp vào file <code>c001_hac_kiem_tan_binh.tscn</code>!
      </div>
    </div>
  </div>

  <div class="center-stage">
    <div class="canvas-toolbar">
      <button class="btn active" id="btnPlayPause" onclick="togglePlay()">⏸ Pause</button>
      <button class="btn active" id="btnInterp" onclick="toggleInterp()">🌊 Nội suy mượt (Godot)</button>
      <span style="color:var(--border)">|</span>
      <button class="btn active" id="toolRotate" onclick="setDragTool('rotate')">🔄 Kéo để Xoay</button>
      <button class="btn" id="toolMove" onclick="setDragTool('move')">✥ Kéo dịch chuyển</button>
      <button class="btn" id="toolRest" onclick="setDragTool('rest')">🦴 Kéo vị trí Khớp Gốc</button>
      <button class="btn" id="toolOffset" onclick="setDragTool('offset')">🖼 Kéo lệch Mảnh Ảnh</button>
      <span style="color:var(--border)">|</span>
      <label style="display:flex;align-items:center;gap:4px;cursor:pointer;">
        <input type="checkbox" id="chkShowBones" checked onchange="renderMain()"> Hiện Xương Spine
      </label>
      <label style="display:flex;align-items:center;gap:4px;cursor:pointer;">
        <input type="checkbox" id="chkShowRef" onchange="renderMain()"> Hiện Ảnh Ref Gốc
      </label>
      <input type="range" id="refOpacity" min="0" max="1" step="0.05" value="0.45" style="width:70px;" title="Độ mờ ảnh Reference" oninput="renderMain()">
    </div>

    <canvas id="mainCanvas" width="512" height="512"></canvas>

    <div class="timeline-bar">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
          <strong id="timelineActionLabel" style="color:var(--accent);font-size:14px;">ACTION: IDLE</strong>
          <span id="timelineTimeLabel" style="color:var(--muted);margin-left:10px;">Frame 0 (t = 0.00s)</span>
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
          <label>Tốc độ:</label>
          <input type="range" id="speedSlider" min="0.2" max="2.0" step="0.1" value="1.0" style="width:80px;" oninput="document.getElementById('speedVal').textContent=this.value+'x'">
          <span id="speedVal">1.0x</span>
          <button class="btn" onclick="addKeyframe()">+ Thêm Frame</button>
          <button class="btn" onclick="deleteKeyframe()">🗑 Xóa Frame</button>
        </div>
      </div>
      <div class="frame-pills" id="framePills"></div>
    </div>
  </div>

  <div class="sidebar-right">
    <div class="control-group" id="keyframeInspector">
      <div class="section-title" id="kfInspectorTitle">Thông Số Keyframe (Frame Hiện Tại)</div>
      <div class="field-row">
        <label>Góc xoay (°)</label>
        <input type="range" id="kfRotRange" min="-140" max="140" step="0.5" oninput="onKfInput('rot', this.value)">
        <input type="number" id="kfRotNum" step="0.5" oninput="onKfInput('rot', this.value)">
      </div>
      <div class="field-row">
        <label>Dịch ngang ΔX</label>
        <input type="range" id="kfDxRange" min="-120" max="120" step="0.5" oninput="onKfInput('dx', this.value)">
        <input type="number" id="kfDxNum" step="0.5" oninput="onKfInput('dx', this.value)">
      </div>
      <div class="field-row">
        <label>Dịch dọc ΔY</label>
        <input type="range" id="kfDyRange" min="-120" max="140" step="0.5" oninput="onKfInput('dy', this.value)">
        <input type="number" id="kfDyNum" step="0.5" oninput="onKfInput('dy', this.value)">
      </div>
      <div class="field-row">
        <label>Độ rõ Nhân vật</label>
        <input type="range" id="kfAlphaRange" min="0" max="1" step="0.02" oninput="onKfAlpha(this.value)">
        <input type="number" id="kfAlphaNum" min="0" max="1" step="0.02" oninput="onKfAlpha(this.value)">
      </div>
      <div class="field-row">
        <label>Thời điểm (s)</label>
        <input type="range" id="kfTimeRange" min="0" max="2.5" step="0.01" oninput="onKfTime(this.value)">
        <input type="number" id="kfTimeNum" min="0" max="5.0" step="0.01" oninput="onKfTime(this.value)">
      </div>
    </div>

    <div class="control-group" id="vfxInspector" style="display:none;">
      <div class="section-title" id="vfxInspectorTitle">Chỉnh Hiệu Ứng VFX (Frame Hiện Tại)</div>
      <div class="field-row">
        <label>Hiển thị VFX</label>
        <input type="checkbox" id="vfxVisibleChk" onchange="onVfxChange()">
        <span>Bật/Tắt</span>
      </div>
      <div class="field-row">
        <label>Vị trí X</label>
        <input type="range" id="vfxXRange" min="0" max="512" step="1" oninput="onVfxInput('x', this.value)">
        <input type="number" id="vfxXNum" step="1" oninput="onVfxInput('x', this.value)">
      </div>
      <div class="field-row">
        <label>Vị trí Y</label>
        <input type="range" id="vfxYRange" min="0" max="512" step="1" oninput="onVfxInput('y', this.value)">
        <input type="number" id="vfxYNum" step="1" oninput="onVfxInput('y', this.value)">
      </div>
      <div class="field-row">
        <label>Góc xoay (°)</label>
        <input type="range" id="vfxRotRange" min="-180" max="180" step="1" oninput="onVfxInput('rot', this.value)">
        <input type="number" id="vfxRotNum" step="1" oninput="onVfxInput('rot', this.value)">
      </div>
      <div class="field-row">
        <label>Tỉ lệ Scale</label>
        <input type="range" id="vfxScaleRange" min="0.2" max="2.0" step="0.02" oninput="onVfxInput('scale', this.value)">
        <input type="number" id="vfxScaleNum" step="0.02" oninput="onVfxInput('scale', this.value)">
      </div>
      <div class="field-row">
        <label>Độ rõ Alpha</label>
        <input type="range" id="vfxAlphaRange" min="0" max="1" step="0.02" oninput="onVfxInput('alpha', this.value)">
        <input type="number" id="vfxAlphaNum" step="0.02" oninput="onVfxInput('alpha', this.value)">
      </div>
    </div>

    <div class="control-group">
      <div class="section-title" id="restInspectorTitle">Cấu Hình Khớp Gốc & Mảnh Ảnh (Rest Pose)</div>
      <div class="field-row">
        <label>Khớp Gốc X</label>
        <input type="range" id="restXRange" min="-180" max="360" step="0.5" oninput="onRestInput('rest_x', this.value)">
        <input type="number" id="restXNum" step="0.5" oninput="onRestInput('rest_x', this.value)">
      </div>
      <div class="field-row">
        <label>Khớp Gốc Y</label>
        <input type="range" id="restYRange" min="-180" max="360" step="0.5" oninput="onRestInput('rest_y', this.value)">
        <input type="number" id="restYNum" step="0.5" oninput="onRestInput('rest_y', this.value)">
      </div>
      <div class="field-row">
        <label>Góc Gốc (°)</label>
        <input type="range" id="restRotRange" min="-180" max="180" step="0.5" oninput="onRestInput('rest_rot', this.value)">
        <input type="number" id="restRotNum" step="0.5" oninput="onRestInput('rest_rot', this.value)">
      </div>
      <div class="field-row">
        <label>Lệch Ảnh X</label>
        <input type="range" id="offXRange" min="-120" max="120" step="0.5" oninput="onOffsetInput('offset_x', this.value)">
        <input type="number" id="offXNum" step="0.5" oninput="onOffsetInput('offset_x', this.value)">
      </div>
      <div class="field-row">
        <label>Lệch Ảnh Y</label>
        <input type="range" id="offYRange" min="-120" max="120" step="0.5" oninput="onOffsetInput('offset_y', this.value)">
        <input type="number" id="offYNum" step="0.5" oninput="onOffsetInput('offset_y', this.value)">
      </div>
      <div class="field-row">
        <label>Thứ tự lớp (Z)</label>
        <input type="range" id="zIdxRange" min="0" max="18" step="1" oninput="onRestInput('z_index', this.value)">
        <input type="number" id="zIdxNum" step="1" oninput="onRestInput('z_index', this.value)">
      </div>
    </div>
  </div>
</div>

<script>
const SPRITE_B64 = {json.dumps(b64_sprites)};
const REF_B64 = {json.dumps(ref_b64)};
const STATE = {json.dumps(initial_state, ensure_ascii=False)};

const IMAGES = {{}};
let refImage = new Image();
refImage.src = REF_B64;
for (const [k, src] of Object.entries(SPRITE_B64)) {{
  const img = new Image();
  img.src = src;
  IMAGES[k] = img;
}}

let currentAction = "idle";
let currentFrameIdx = 0;
let selectedBone = "Forearm_L";
let selectedVfx = null;
let isPlaying = true;
let smoothInterp = true;
let dragTool = "rotate";
let clipboardPose = null;
let tscnFileHandle = null;

const previewStrip = document.getElementById("previewStrip");
const actionNames = ["idle", "walk", "attack", "cast", "hurt", "death"];

const stripLabel = document.createElement("span");
stripLabel.style.cssText = "font-size:12px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:0.05em;margin-right:4px;";
stripLabel.textContent = "Chọn Action để Preview:";
previewStrip.appendChild(stripLabel);

actionNames.forEach(act => {{
  const btn = document.createElement("button");
  btn.className = "action-tab" + (act === currentAction ? " selected" : "");
  btn.id = "miniCard_" + act;
  btn.onclick = () => selectAction(act);
  btn.innerHTML = `
    <span>▶ ${{act.toUpperCase()}}</span>
    <small>(${{STATE.actions[act].frames.length}}f | ${{STATE.actions[act].length}}s)</small>
  `;
  previewStrip.appendChild(btn);
}});

function buildSidebarLists() {{
  const bList = document.getElementById("boneList");
  bList.innerHTML = "";
  STATE.bones.forEach(b => {{
    const el = document.createElement("div");
    el.className = "bone-item" + (selectedBone === b.name && !selectedVfx ? " active" : "");
    el.innerHTML = `<span>🦴 ${{b.name}} <small style="color:var(--muted)">(${{b.part}})</small></span><span class="badge">z=${{b.z_index}}</span>`;
    el.onclick = () => {{
      selectedVfx = null;
      selectedBone = b.name;
      buildSidebarLists();
      syncInspectorUI();
      renderMain();
    }};
    bList.appendChild(el);
  }});

  const vList = document.getElementById("vfxList");
  vList.innerHTML = "";
  STATE.vfx_list.forEach(fx => {{
    const el = document.createElement("div");
    el.className = "bone-item" + (selectedVfx === fx ? " active" : "");
    el.innerHTML = `<span>✨ ${{fx}}</span><span class="badge">VFX</span>`;
    el.onclick = () => {{
      selectedVfx = fx;
      buildSidebarLists();
      syncInspectorUI();
      renderMain();
    }};
    vList.appendChild(el);
  }});
}}

function selectAction(act) {{
  currentAction = act;
  currentFrameIdx = 0;
  startTime = performance.now();
  if (!isPlaying) togglePlay();
  actionNames.forEach(a => {{
    document.getElementById("miniCard_" + a).classList.toggle("selected", a === act);
  }});
  document.getElementById("timelineActionLabel").textContent = `ACTION: ${{act.toUpperCase()}} (${{STATE.actions[act].length}}s)`;
  buildFramePills();
  syncInspectorUI();
  renderMain();
}}

function buildFramePills() {{
  const wrap = document.getElementById("framePills");
  wrap.innerHTML = "";
  const frames = STATE.actions[currentAction].frames;
  frames.forEach((f, idx) => {{
    const pill = document.createElement("button");
    pill.className = "frame-pill" + (idx === currentFrameIdx ? " active" : "");
    pill.textContent = `F${{idx}} (${{f.t.toFixed(2)}}s)`;
    pill.onclick = () => {{
      currentFrameIdx = idx;
      if (isPlaying) togglePlay();
      buildFramePills();
      syncInspectorUI();
      renderMain();
    }};
    wrap.appendChild(pill);
  }});
}}

function getBoneObj(name) {{
  return STATE.bones.find(b => b.name === name);
}}

function getPoseTuple(frameObj, bname) {{
  const raw = frameObj[bname] || [0, 0, 0];
  if (bname === "Hip") {{
    return {{ dx: raw[0], dy: raw[1], rot: raw[2] }};
  }}
  return {{ rot: raw[0], dx: raw[1], dy: raw[2] }};
}}

function setPoseTuple(frameObj, bname, rot, dx, dy) {{
  if (bname === "Hip") {{
    frameObj["Hip"] = [Number(dx), Number(dy), Number(rot)];
  }} else {{
    frameObj[bname] = [Number(rot), Number(dx), Number(dy)];
  }}
}}

function interpolateActionPose(actName, timeSec) {{
  const act = STATE.actions[actName];
  const frames = act.frames;
  if (frames.length === 1) return frames[0];
  let i = 0;
  while (i < frames.length - 1 && frames[i + 1].t <= timeSec) i++;
  if (i >= frames.length - 1) {{
    if (act.loop) {{
      const fA = frames[frames.length - 1];
      const fB = frames[0];
      const span = Math.max(0.001, act.length - fA.t);
      const u = Math.min(1, Math.max(0, (timeSec - fA.t) / span));
      return blendFrames(fA, fB, u);
    }}
    return frames[frames.length - 1];
  }}
  const fA = frames[i];
  const fB = frames[i + 1];
  const span = Math.max(0.001, fB.t - fA.t);
  const u = Math.min(1, Math.max(0, (timeSec - fA.t) / span));
  return blendFrames(fA, fB, u);
}}

function blendFrames(fA, fB, u) {{
  const out = {{ t: fA.t + (fB.t - fA.t) * u }};
  STATE.bones.forEach(b => {{
    const pA = getPoseTuple(fA, b.name);
    const pB = getPoseTuple(fB, b.name);
    const rot = pA.rot + (pB.rot - pA.rot) * u;
    const dx = pA.dx + (pB.dx - pA.dx) * u;
    const dy = pA.dy + (pB.dy - pA.dy) * u;
    setPoseTuple(out, b.name, rot, dx, dy);
  }});
  const aA = fA.modulate_a !== undefined ? fA.modulate_a : 1.0;
  const aB = fB.modulate_a !== undefined ? fB.modulate_a : 1.0;
  out.modulate_a = aA + (aB - aA) * u;
  out.vfx = u < 0.5 ? (fA.vfx || {{}}) : (fB.vfx || {{}});
  return out;
}}

function computeWorldTransforms(framePose) {{
  const world = {{}};
  STATE.bones.forEach(b => {{
    const p = getPoseTuple(framePose, b.name);
    const lx = b.rest_x + p.dx;
    const ly = b.rest_y + p.dy;
    const lrot = b.rest_rot + p.rot;
    if (!b.parent) {{
      world[b.name] = {{ wx: lx, wy: ly, wrot: lrot, tx: lx, ty: ly }};
    }} else {{
      const pw = world[b.parent];
      const rad = pw.wrot * Math.PI / 180;
      const ca = Math.cos(rad), sa = Math.sin(rad);
      world[b.name] = {{
        wx: pw.wx + lx * ca - ly * sa,
        wy: pw.wy + lx * sa + ly * ca,
        wrot: pw.wrot + lrot,
        tx: 0, ty: 0
      }};
    }}
  }});
  STATE.bones.forEach(b => {{
    const w = world[b.name];
    if (b.tip_child && world[b.tip_child]) {{
      w.tx = world[b.tip_child].wx;
      w.ty = world[b.tip_child].wy;
    }} else if (b.tip_offset) {{
      const rad = w.wrot * Math.PI / 180;
      const ca = Math.cos(rad), sa = Math.sin(rad);
      w.tx = w.wx + b.tip_offset[0] * ca - b.tip_offset[1] * sa;
      w.ty = w.wy + b.tip_offset[0] * sa + b.tip_offset[1] * ca;
    }} else {{
      w.tx = w.wx;
      w.ty = w.wy + 32;
    }}
  }});
  return world;
}}

function drawSpineBoneJS(ctx, x0, y0, x1, y1, isSelected) {{
  const dx = x1 - x0, dy = y1 - y0;
  const len = Math.hypot(dx, dy);
  if (len > 2.0) {{
    const ux = dx / len, uy = dy / len;
    const px = -uy, py = ux;
    const w = Math.min(5.5, Math.max(2.8, len * 0.10));
    const mx = x0 + dx * 0.22, my = y0 + dy * 0.22;
    ctx.beginPath();
    ctx.moveTo(x0, y0);
    ctx.lineTo(mx + px * w, my + py * w);
    ctx.lineTo(x1, y1);
    ctx.lineTo(mx - px * w, my - py * w);
    ctx.closePath();
    ctx.fillStyle = isSelected ? "rgba(34, 197, 94, 0.55)" : "rgba(56, 189, 248, 0.42)";
    ctx.strokeStyle = isSelected ? "#22c55e" : "#38bdf8";
    ctx.lineWidth = isSelected ? 2 : 1.3;
    ctx.fill();
    ctx.stroke();
  }}
  ctx.fillStyle = isSelected ? "#22c55e" : "#ef4444";
  ctx.strokeStyle = "#ffffff";
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.arc(x0, y0, isSelected ? 5.5 : 4, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();
}}

function drawCharacterToCtx(ctx, framePose, canvasW, canvasH, showOverlays = false) {{
  ctx.clearRect(0, 0, canvasW, canvasH);
  const scale = canvasW / 512.0;
  ctx.save();
  ctx.scale(scale, scale);

  ctx.strokeStyle = "rgba(100, 116, 139, 0.22)";
  ctx.lineWidth = 1;
  ctx.strokeRect(16, 16, 480, 480);

  ctx.strokeStyle = "rgba(34, 197, 94, 0.55)";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(40, 436);
  ctx.lineTo(472, 436);
  ctx.stroke();

  if (showOverlays && document.getElementById("chkShowRef").checked && refImage.complete) {{
    ctx.save();
    ctx.globalAlpha = parseFloat(document.getElementById("refOpacity").value || 0.45);
    ctx.drawImage(refImage, 31, 20, 450, 450);
    ctx.restore();
  }}

  const world = computeWorldTransforms(framePose);
  const modA = framePose.modulate_a !== undefined ? framePose.modulate_a : 1.0;

  const sortedBones = [...STATE.bones].sort((a, b) => a.z_index - b.z_index);
  sortedBones.forEach(b => {{
    const img = IMAGES[b.part];
    if (!img || !img.complete) return;
    const w = world[b.name];
    ctx.save();
    ctx.translate(w.wx, w.wy);
    ctx.rotate(w.wrot * Math.PI / 180);
    ctx.globalAlpha = modA;
    const drawX = b.offset_x - b.width / 2.0;
    const drawY = b.offset_y - b.height / 2.0;
    ctx.drawImage(img, drawX, drawY);
    if (showOverlays && selectedBone === b.name && !selectedVfx) {{
      ctx.strokeStyle = "#38bdf8";
      ctx.lineWidth = 1.5;
      ctx.strokeRect(drawX, drawY, b.width, b.height);
    }}
    ctx.restore();
  }});

  const vfxMap = framePose.vfx || {{}};
  for (const [fxName, cfg] of Object.entries(vfxMap)) {{
    const img = IMAGES[fxName];
    if (!img || !img.complete) continue;
    ctx.save();
    ctx.translate(cfg.pos[0], cfg.pos[1]);
    ctx.rotate((cfg.rot || 0) * Math.PI / 180);
    const sc = cfg.scale !== undefined ? cfg.scale : 1.0;
    ctx.scale(sc, sc);
    ctx.globalAlpha = cfg.alpha !== undefined ? cfg.alpha : 1.0;
    ctx.drawImage(img, -img.width / 2, -img.height / 2);
    if (showOverlays && selectedVfx === fxName) {{
      ctx.strokeStyle = "#f59e0b";
      ctx.lineWidth = 2;
      ctx.strokeRect(-img.width / 2, -img.height / 2, img.width, img.height);
    }}
    ctx.restore();
  }}

  if (showOverlays && document.getElementById("chkShowBones").checked) {{
    // Draw subtle clavicle/pelvis hub connectors
    const cw = world["Chest"];
    ["Head", "UpperArm_L", "UpperArm_R", "Pauldron", "Cloak"].forEach(cn => {{
      const ch = world[cn];
      ctx.strokeStyle = "rgba(148, 163, 184, 0.45)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(cw.tx, cw.ty);
      ctx.lineTo(ch.wx, ch.wy);
      ctx.stroke();
    }});
    const hw = world["Hip"];
    ["Thigh_L", "Thigh_R"].forEach(ln => {{
      const lh = world[ln];
      ctx.strokeStyle = "rgba(148, 163, 184, 0.45)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(hw.wx, hw.wy);
      ctx.lineTo(lh.wx, lh.wy);
      ctx.stroke();
    }});

    // Draw all 18 full Spine bones from Head -> Tail!
    STATE.bones.forEach(b => {{
      const w = world[b.name];
      const isSel = (selectedBone === b.name && !selectedVfx);
      drawSpineBoneJS(ctx, w.wx, w.wy, w.tx, w.ty, isSel);
    }});
  }}

  ctx.restore();
  return world;
}}

function syncInspectorUI() {{
  const frameObj = STATE.actions[currentAction].frames[currentFrameIdx];
  const b = getBoneObj(selectedBone);
  document.getElementById("kfInspectorTitle").textContent = `Keyframe F${{currentFrameIdx}} — Khớp: ${{selectedBone}}`;
  document.getElementById("restInspectorTitle").textContent = `Cấu Hình Gốc — ${{selectedBone}} (${{b.part}}.png)`;

  const p = getPoseTuple(frameObj, selectedBone);
  document.getElementById("kfRotRange").value = p.rot;
  document.getElementById("kfRotNum").value = p.rot;
  document.getElementById("kfDxRange").value = p.dx;
  document.getElementById("kfDxNum").value = p.dx;
  document.getElementById("kfDyRange").value = p.dy;
  document.getElementById("kfDyNum").value = p.dy;

  const modA = frameObj.modulate_a !== undefined ? frameObj.modulate_a : 1.0;
  document.getElementById("kfAlphaRange").value = modA;
  document.getElementById("kfAlphaNum").value = modA;
  document.getElementById("kfTimeRange").value = frameObj.t;
  document.getElementById("kfTimeNum").value = frameObj.t;

  document.getElementById("restXRange").value = b.rest_x;
  document.getElementById("restXNum").value = b.rest_x;
  document.getElementById("restYRange").value = b.rest_y;
  document.getElementById("restYNum").value = b.rest_y;
  document.getElementById("restRotRange").value = b.rest_rot;
  document.getElementById("restRotNum").value = b.rest_rot;
  document.getElementById("offXRange").value = b.offset_x;
  document.getElementById("offXNum").value = b.offset_x;
  document.getElementById("offYRange").value = b.offset_y;
  document.getElementById("offYNum").value = b.offset_y;
  document.getElementById("zIdxRange").value = b.z_index;
  document.getElementById("zIdxNum").value = b.z_index;

  const vfxBox = document.getElementById("vfxInspector");
  if (selectedVfx) {{
    vfxBox.style.display = "flex";
    document.getElementById("vfxInspectorTitle").textContent = `Hiệu Ứng VFX: ${{selectedVfx}} (F${{currentFrameIdx}})`;
    const cfg = (frameObj.vfx && frameObj.vfx[selectedVfx]) || null;
    document.getElementById("vfxVisibleChk").checked = !!cfg;
    const vx = cfg ? cfg.pos[0] : 350;
    const vy = cfg ? cfg.pos[1] : 250;
    const vrot = cfg ? (cfg.rot || 0) : 0;
    const vsc = cfg ? (cfg.scale !== undefined ? cfg.scale : 1.0) : 1.0;
    const valpha = cfg ? (cfg.alpha !== undefined ? cfg.alpha : 1.0) : 1.0;
    document.getElementById("vfxXRange").value = vx; document.getElementById("vfxXNum").value = vx;
    document.getElementById("vfxYRange").value = vy; document.getElementById("vfxYNum").value = vy;
    document.getElementById("vfxRotRange").value = vrot; document.getElementById("vfxRotNum").value = vrot;
    document.getElementById("vfxScaleRange").value = vsc; document.getElementById("vfxScaleNum").value = vsc;
    document.getElementById("vfxAlphaRange").value = valpha; document.getElementById("vfxAlphaNum").value = valpha;
  }} else {{
    vfxBox.style.display = "none";
  }}
}}

function onKfInput(field, val) {{
  if (isPlaying) togglePlay();
  const num = parseFloat(val) || 0;
  const frameObj = STATE.actions[currentAction].frames[currentFrameIdx];
  const p = getPoseTuple(frameObj, selectedBone);
  p[field] = num;
  setPoseTuple(frameObj, selectedBone, p.rot, p.dx, p.dy);
  syncInspectorUI();
  renderMain();
}}

function onKfAlpha(val) {{
  if (isPlaying) togglePlay();
  const frameObj = STATE.actions[currentAction].frames[currentFrameIdx];
  frameObj.modulate_a = parseFloat(val) || 1.0;
  syncInspectorUI();
  renderMain();
}}

function onKfTime(val) {{
  if (isPlaying) togglePlay();
  const frameObj = STATE.actions[currentAction].frames[currentFrameIdx];
  frameObj.t = Math.max(0, parseFloat(val) || 0);
  buildFramePills();
  syncInspectorUI();
}}

function onRestInput(field, val) {{
  const b = getBoneObj(selectedBone);
  b[field] = parseFloat(val) || 0;
  buildSidebarLists();
  syncInspectorUI();
  renderMain();
}}

function onOffsetInput(field, val) {{
  const b = getBoneObj(selectedBone);
  b[field] = parseFloat(val) || 0;
  b.pivot_x = b.width / 2.0 - b.offset_x;
  b.pivot_y = b.height / 2.0 - b.offset_y;
  syncInspectorUI();
  renderMain();
}}

function onVfxChange() {{
  if (!selectedVfx) return;
  if (isPlaying) togglePlay();
  const frameObj = STATE.actions[currentAction].frames[currentFrameIdx];
  frameObj.vfx = frameObj.vfx || {{}};
  if (document.getElementById("vfxVisibleChk").checked) {{
    frameObj.vfx[selectedVfx] = {{
      pos: [parseFloat(document.getElementById("vfxXNum").value) || 350, parseFloat(document.getElementById("vfxYNum").value) || 250],
      rot: parseFloat(document.getElementById("vfxRotNum").value) || 0,
      scale: parseFloat(document.getElementById("vfxScaleNum").value) || 1.0,
      alpha: parseFloat(document.getElementById("vfxAlphaNum").value) || 1.0
    }};
  }} else {{
    delete frameObj.vfx[selectedVfx];
  }}
  syncInspectorUI();
  renderMain();
}}

function onVfxInput(field, val) {{
  if (!selectedVfx) return;
  document.getElementById("vfxVisibleChk").checked = true;
  if (field === 'x') document.getElementById("vfxXNum").value = val;
  if (field === 'y') document.getElementById("vfxYNum").value = val;
  if (field === 'rot') document.getElementById("vfxRotNum").value = val;
  if (field === 'scale') document.getElementById("vfxScaleNum").value = val;
  if (field === 'alpha') document.getElementById("vfxAlphaNum").value = val;
  onVfxChange();
}}

function setDragTool(tool) {{
  dragTool = tool;
  ["Rotate", "Move", "Rest", "Offset"].forEach(n => {{
    document.getElementById("tool" + n).classList.toggle("active", n.toLowerCase() === tool);
  }});
}}

function togglePlay() {{
  isPlaying = !isPlaying;
  const btn = document.getElementById("btnPlayPause");
  btn.textContent = isPlaying ? "⏸ Pause" : "▶ Play";
  btn.classList.toggle("active", isPlaying);
}}

function toggleInterp() {{
  smoothInterp = !smoothInterp;
  const btn = document.getElementById("btnInterp");
  btn.textContent = smoothInterp ? "🌊 Nội suy mượt (Godot)" : "🪜 Từng Frame Rời";
  btn.classList.toggle("active", smoothInterp);
}}

function resetCurrentFrame() {{
  if (isPlaying) togglePlay();
  const frameObj = STATE.actions[currentAction].frames[currentFrameIdx];
  STATE.bones.forEach(b => setPoseTuple(frameObj, b.name, 0, 0, 0));
  frameObj.modulate_a = 1.0;
  frameObj.vfx = {{}};
  syncInspectorUI();
  renderMain();
}}

function copyFramePose() {{
  const frameObj = STATE.actions[currentAction].frames[currentFrameIdx];
  clipboardPose = JSON.parse(JSON.stringify(frameObj));
  document.getElementById("saveStatus").textContent = `Đã copy pose Frame ${{currentFrameIdx}} của ${{currentAction}}!`;
}}

function pasteFramePose() {{
  if (!clipboardPose) return;
  if (isPlaying) togglePlay();
  const frameObj = STATE.actions[currentAction].frames[currentFrameIdx];
  const keepT = frameObj.t;
  Object.assign(frameObj, JSON.parse(JSON.stringify(clipboardPose)));
  frameObj.t = keepT;
  syncInspectorUI();
  renderMain();
}}

function addKeyframe() {{
  if (isPlaying) togglePlay();
  const act = STATE.actions[currentAction];
  const cur = act.frames[currentFrameIdx];
  const clone = JSON.parse(JSON.stringify(cur));
  clone.t = Number((cur.t + 0.12).toFixed(2));
  act.frames.splice(currentFrameIdx + 1, 0, clone);
  if (clone.t >= act.length) act.length = Number((clone.t + 0.15).toFixed(2));
  currentFrameIdx++;
  buildFramePills();
  syncInspectorUI();
  renderMain();
}}

function deleteKeyframe() {{
  const act = STATE.actions[currentAction];
  if (act.frames.length <= 1) return;
  if (isPlaying) togglePlay();
  act.frames.splice(currentFrameIdx, 1);
  currentFrameIdx = Math.max(0, currentFrameIdx - 1);
  buildFramePills();
  syncInspectorUI();
  renderMain();
}}

const mainCanvas = document.getElementById("mainCanvas");
const mainCtx = mainCanvas.getContext("2d");
let isDragging = false;
let dragStart = {{ x: 0, y: 0 }};
let dragInitial = null;
let lastRenderedWorld = {{}};

mainCanvas.addEventListener("mousedown", e => {{
  const rect = mainCanvas.getBoundingClientRect();
  const mx = (e.clientX - rect.left) * (512 / rect.width);
  const my = (e.clientY - rect.top) * (512 / rect.height);

  let closestBone = null;
  let bestDist = 24;
  for (const b of STATE.bones) {{
    const w = lastRenderedWorld[b.name];
    if (!w) continue;
    const d = Math.hypot(mx - w.wx, my - w.wy);
    if (d < bestDist) {{
      bestDist = d;
      closestBone = b.name;
    }}
  }}
  if (closestBone) {{
    selectedVfx = null;
    selectedBone = closestBone;
    buildSidebarLists();
    syncInspectorUI();
  }}

  if (isPlaying) togglePlay();
  isDragging = true;
  dragStart = {{ x: mx, y: my }};
  const frameObj = STATE.actions[currentAction].frames[currentFrameIdx];
  const b = getBoneObj(selectedBone);
  const p = getPoseTuple(frameObj, selectedBone);
  dragInitial = {{
    rot: p.rot, dx: p.dx, dy: p.dy,
    rest_x: b.rest_x, rest_y: b.rest_y,
    offset_x: b.offset_x, offset_y: b.offset_y,
    vfx_pos: (selectedVfx && frameObj.vfx && frameObj.vfx[selectedVfx]) ? [...frameObj.vfx[selectedVfx].pos] : [mx, my]
  }};
  renderMain();
}});

window.addEventListener("mousemove", e => {{
  if (!isDragging) return;
  const rect = mainCanvas.getBoundingClientRect();
  const mx = (e.clientX - rect.left) * (512 / rect.width);
  const my = (e.clientY - rect.top) * (512 / rect.height);
  const dx = mx - dragStart.x;
  const dy = my - dragStart.y;

  const frameObj = STATE.actions[currentAction].frames[currentFrameIdx];
  if (selectedVfx) {{
    frameObj.vfx = frameObj.vfx || {{}};
    frameObj.vfx[selectedVfx] = frameObj.vfx[selectedVfx] || {{ pos: [mx, my], rot: 0, scale: 1, alpha: 1 }};
    frameObj.vfx[selectedVfx].pos = [Math.round(dragInitial.vfx_pos[0] + dx), Math.round(dragInitial.vfx_pos[1] + dy)];
    syncInspectorUI();
    renderMain();
    return;
  }}

  const b = getBoneObj(selectedBone);
  const mode = e.altKey ? "offset" : (e.shiftKey ? "move" : dragTool);

  if (mode === "rotate") {{
    const newRot = Number((dragInitial.rot + dx * 0.65).toFixed(1));
    setPoseTuple(frameObj, selectedBone, newRot, dragInitial.dx, dragInitial.dy);
  }} else if (mode === "move") {{
    setPoseTuple(frameObj, selectedBone, dragInitial.rot, Number((dragInitial.dx + dx).toFixed(1)), Number((dragInitial.dy + dy).toFixed(1)));
  }} else if (mode === "rest") {{
    b.rest_x = Number((dragInitial.rest_x + dx).toFixed(1));
    b.rest_y = Number((dragInitial.rest_y + dy).toFixed(1));
  }} else if (mode === "offset") {{
    b.offset_x = Number((dragInitial.offset_x + dx).toFixed(1));
    b.offset_y = Number((dragInitial.offset_y + dy).toFixed(1));
    b.pivot_x = b.width / 2.0 - b.offset_x;
    b.pivot_y = b.height / 2.0 - b.offset_y;
  }}
  syncInspectorUI();
  renderMain();
}});

window.addEventListener("mouseup", () => {{ isDragging = false; }});

function renderMain(poseOverride = null) {{
  const frameObj = poseOverride || STATE.actions[currentAction].frames[currentFrameIdx];
  lastRenderedWorld = drawCharacterToCtx(mainCtx, frameObj, 512, 512, true);
}}

let startTime = performance.now();
function tick(now) {{
  const speed = parseFloat(document.getElementById("speedSlider").value || 1.0);
  const elapsed = ((now - startTime) / 1000.0) * speed;

  if (isPlaying) {{
    const act = STATE.actions[currentAction];
    const t = elapsed % act.length;
    let activeIdx = 0;
    for (let i = 0; i < act.frames.length; i++) {{
      if (act.frames[i].t <= t) activeIdx = i;
    }}
    if (activeIdx !== currentFrameIdx) {{
      currentFrameIdx = activeIdx;
      buildFramePills();
      syncInspectorUI();
    }}
    const pose = smoothInterp ? interpolateActionPose(currentAction, t) : act.frames[currentFrameIdx];
    document.getElementById("timelineTimeLabel").textContent = `Frame ${{currentFrameIdx}} (t = ${{t.toFixed(2)}}s / ${{act.length}}s)`;
    renderMain(pose);
  }} else {{
    const f = STATE.actions[currentAction].frames[currentFrameIdx];
    document.getElementById("timelineTimeLabel").textContent = `Frame ${{currentFrameIdx}} (t = ${{f.t.toFixed(2)}}s — Đang dừng để chỉnh sửa)`;
  }}
  requestAnimationFrame(tick);
}}

function buildGodotTscnText() {{
  const bones = STATE.bones;
  const actions = STATE.actions;
  const vfxList = STATE.vfx_list;
  const lines = [];
  const extCount = 1 + bones.length + vfxList.length;
  const subCount = 1 + Object.keys(actions).length;

  lines.push(`[gd_scene load_steps=${{extCount + subCount}} format=3 uid="uid://c001hackiemtanbinh"]`);
  lines.push("");
  lines.push(`[ext_resource type="Script" path="res://assets/heroes/c001_hac_kiem_tan_binh/godot/c001_hac_kiem_tan_binh.gd" id="1_script"]`);

  const partExtId = {{}};
  let idx = 2;
  bones.forEach(b => {{
    partExtId[b.part] = `${{idx}}_${{b.part}}`;
    lines.push(`[ext_resource type="Texture2D" path="res://assets/heroes/c001_hac_kiem_tan_binh/godot/parts/${{b.part}}.png" id="${{partExtId[b.part]}}"]`);
    idx++;
  }});
  vfxList.forEach(fx => {{
    partExtId[fx] = `${{idx}}_${{fx}}`;
    lines.push(`[ext_resource type="Texture2D" path="res://assets/heroes/c001_hac_kiem_tan_binh/godot/parts/${{fx}}.png" id="${{partExtId[fx]}}"]`);
    idx++;
  }});
  lines.push("");

  const bonePaths = {{}};
  bones.forEach(b => {{
    bonePaths[b.name] = !b.parent ? `Skeleton2D/${{b.name}}` : `${{bonePaths[b.parent]}}/${{b.name}}`;
  }});

  for (const [actName, act] of Object.entries(actions)) {{
    const frames = act.frames;
    const loopMode = act.loop ? 1 : 0;
    lines.push(`[sub_resource type="Animation" id="Animation_${{actName}}"]`);
    lines.push(`resource_name = "${{actName}}"`);
    lines.push(`length = ${{Number(act.length).toFixed(2)}}`);
    lines.push(`loop_mode = ${{loopMode}}`);

    let tIdx = 0;
    const timesStr = frames.map(f => Number(f.t).toFixed(2)).join(", ");
    const transStr = frames.map(() => "1").join(", ");

    bones.forEach(b => {{
      const bpath = bonePaths[b.name];
      const rots = [];
      const positions = [];
      frames.forEach(f => {{
        const p = getPoseTuple(f, b.name);
        const rad = ((b.rest_rot + p.rot) * Math.PI / 180).toFixed(4);
        const px = (b.rest_x + p.dx).toFixed(1);
        const py = (b.rest_y + p.dy).toFixed(1);
        rots.push(rad);
        positions.push(`Vector2(${{px}}, ${{py}})`);
      }});

      lines.push(`tracks/${{tIdx}}/type = "value"`);
      lines.push(`tracks/${{tIdx}}/imported = false`);
      lines.push(`tracks/${{tIdx}}/enabled = true`);
      lines.push(`tracks/${{tIdx}}/path = NodePath("${{bpath}}:rotation")`);
      lines.push(`tracks/${{tIdx}}/interp = 1`);
      lines.push(`tracks/${{tIdx}}/loop_wrap = true`);
      lines.push(`tracks/${{tIdx}}/keys = {{\\n"times": PackedFloat32Array(${{timesStr}}),\\n"transitions": PackedFloat32Array(${{transStr}}),\\n"update": 0,\\n"values": [${{rots.join(", ")}}]\\n}}`);
      tIdx++;

      lines.push(`tracks/${{tIdx}}/type = "value"`);
      lines.push(`tracks/${{tIdx}}/imported = false`);
      lines.push(`tracks/${{tIdx}}/enabled = true`);
      lines.push(`tracks/${{tIdx}}/path = NodePath("${{bpath}}:position")`);
      lines.push(`tracks/${{tIdx}}/interp = 1`);
      lines.push(`tracks/${{tIdx}}/loop_wrap = true`);
      lines.push(`tracks/${{tIdx}}/keys = {{\\n"times": PackedFloat32Array(${{timesStr}}),\\n"transitions": PackedFloat32Array(${{transStr}}),\\n"update": 0,\\n"values": [${{positions.join(", ")}}]\\n}}`);
      tIdx++;
    }});

    const modVals = frames.map(f => `Color(1, 1, 1, ${{Number(f.modulate_a !== undefined ? f.modulate_a : 1.0).toFixed(2)}})`).join(", ");
    lines.push(`tracks/${{tIdx}}/type = "value"`);
    lines.push(`tracks/${{tIdx}}/imported = false`);
    lines.push(`tracks/${{tIdx}}/enabled = true`);
    lines.push(`tracks/${{tIdx}}/path = NodePath("Skeleton2D:modulate")`);
    lines.push(`tracks/${{tIdx}}/interp = 1`);
    lines.push(`tracks/${{tIdx}}/loop_wrap = true`);
    lines.push(`tracks/${{tIdx}}/keys = {{\\n"times": PackedFloat32Array(${{timesStr}}),\\n"transitions": PackedFloat32Array(${{transStr}}),\\n"update": 0,\\n"values": [${{modVals}}]\\n}}`);
    tIdx++;

    vfxList.forEach(fx => {{
      const visVals = [], posVals = [], rotVals = [], scVals = [], colVals = [];
      frames.forEach(f => {{
        const d = f.vfx && f.vfx[fx];
        if (d) {{
          visVals.push("true");
          posVals.push(`Vector2(${{Number(d.pos[0]).toFixed(1)}}, ${{Number(d.pos[1]).toFixed(1)}})`);
          rotVals.push(((d.rot || 0) * Math.PI / 180).toFixed(4));
          const sc = Number(d.scale !== undefined ? d.scale : 1.0).toFixed(2);
          scVals.push(`Vector2(${{sc}}, ${{sc}})`);
          colVals.push(`Color(1, 1, 1, ${{Number(d.alpha !== undefined ? d.alpha : 1.0).toFixed(2)}})`);
        }} else {{
          visVals.push("false");
          posVals.push("Vector2(256, 256)");
          rotVals.push("0.0");
          scVals.push("Vector2(1, 1)");
          colVals.push("Color(1, 1, 1, 0)");
        }}
      }});
      [["visible", 1, visVals], ["position", 0, posVals], ["rotation", 0, rotVals], ["scale", 0, scVals], ["modulate", 0, colVals]].forEach(([prop, uMode, arr]) => {{
        lines.push(`tracks/${{tIdx}}/type = "value"`);
        lines.push(`tracks/${{tIdx}}/imported = false`);
        lines.push(`tracks/${{tIdx}}/enabled = true`);
        lines.push(`tracks/${{tIdx}}/path = NodePath("VFXLayer/${{fx}}:${{prop}}")`);
        lines.push(`tracks/${{tIdx}}/interp = 1`);
        lines.push(`tracks/${{tIdx}}/loop_wrap = true`);
        lines.push(`tracks/${{tIdx}}/keys = {{\\n"times": PackedFloat32Array(${{timesStr}}),\\n"transitions": PackedFloat32Array(${{transStr}}),\\n"update": ${{uMode}},\\n"values": [${{arr.join(", ")}}]\\n}}`);
        tIdx++;
      }});
    }});
    lines.push("");
  }}

  lines.push(`[sub_resource type="AnimationLibrary" id="AnimationLibrary_c001"]`);
  lines.push(`_data = {{`);
  Object.keys(actions).forEach(actName => {{
    lines.push(`"${{actName}}": SubResource("Animation_${{actName}}"),`);
  }});
  lines.push(`}}`);
  lines.push("");
  lines.push(`[node name="C001_HacKiemTanBinh" type="Node2D"]`);
  lines.push(`script = ExtResource("1_script")`);
  lines.push("");
  lines.push(`[node name="Skeleton2D" type="Skeleton2D" parent="."]`);
  lines.push("");

  bones.forEach(b => {{
    const parentPath = !b.parent ? "Skeleton2D" : bonePaths[b.parent];
    const rad = b.rest_rot * Math.PI / 180;
    const ca = Math.cos(rad).toFixed(4), sa = Math.sin(rad).toFixed(4), msa = (-Math.sin(rad)).toFixed(4);
    const rx = Number(b.rest_x).toFixed(1), ry = Number(b.rest_y).toFixed(1);
    let tx = 0, ty = 42;
    if (b.tip_child) {{
      const cb = getBoneObj(b.tip_child);
      if (cb) {{ tx = cb.rest_x; ty = cb.rest_y; }}
    }} else if (b.tip_offset) {{
      tx = b.tip_offset[0]; ty = b.tip_offset[1];
    }}
    const bLen = Math.max(8, Math.hypot(tx, ty)).toFixed(1);
    const bAng = Math.atan2(ty, tx).toFixed(4);

    lines.push(`[node name="${{b.name}}" type="Bone2D" parent="${{parentPath}}"]`);
    lines.push(`position = Vector2(${{rx}}, ${{ry}})`);
    lines.push(`rotation = ${{rad.toFixed(4)}}`);
    lines.push(`rest = Transform2D(${{ca}}, ${{sa}}, ${{msa}}, ${{ca}}, ${{rx}}, ${{ry}})`);
    lines.push(`auto_calculate_length_and_angle = false`);
    lines.push(`length = ${{bLen}}`);
    lines.push(`bone_angle = ${{bAng}}`);
    lines.push("");
    lines.push(`[node name="Sprite" type="Sprite2D" parent="${{bonePaths[b.name]}}"]`);
    lines.push(`z_index = ${{b.z_index}}`);
    lines.push(`z_as_relative = false`);
    lines.push(`texture = ExtResource("${{partExtId[b.part]}}")`);
    lines.push(`offset = Vector2(${{Number(b.offset_x).toFixed(2)}}, ${{Number(b.offset_y).toFixed(2)}})`);
    lines.push("");
  }});

  lines.push(`[node name="VFXLayer" type="Node2D" parent="."]`);
  lines.push(`z_index = 20`);
  lines.push(`z_as_relative = false`);
  lines.push("");
  vfxList.forEach(fx => {{
    lines.push(`[node name="${{fx}}" type="Sprite2D" parent="VFXLayer"]`);
    lines.push(`visible = false`);
    lines.push(`position = Vector2(256, 256)`);
    lines.push(`texture = ExtResource("${{partExtId[fx]}}")`);
    lines.push("");
  }});

  lines.push(`[node name="AnimationPlayer" type="AnimationPlayer" parent="."]`);
  lines.push(`libraries = {{\\n"": SubResource("AnimationLibrary_c001")\\n}}`);
  lines.push(`autoplay = "idle"`);
  lines.push("");
  return lines.join("\\n");
}}

async function saveToTscn() {{
  const tscnContent = buildGodotTscnText();
  const statusEl = document.getElementById("saveStatus");
  statusEl.textContent = "Đang lưu vào c001_hac_kiem_tan_binh.tscn...";

  try {{
    const resp = await fetch("http://127.0.0.1:3457/save-tscn", {{
      method: "POST",
      headers: {{ "Content-Type": "application/json" }},
      body: JSON.stringify({{
        tscn_path: STATE.tscn_path,
        tscn_content: tscnContent,
        state: STATE
      }})
    }});
    if (resp.ok) {{
      const data = await resp.json();
      statusEl.textContent = "✅ Đã lưu trực tiếp vào: " + data.saved_path + " (" + new Date().toLocaleTimeString() + ")";
      return;
    }}
  }} catch (err) {{}}

  if (window.showSaveFilePicker) {{
    try {{
      if (!tscnFileHandle) {{
        tscnFileHandle = await window.showSaveFilePicker({{
          suggestedName: "c001_hac_kiem_tan_binh.tscn",
          types: [{{ description: "Godot Scene (.tscn)", accept: {{ "text/plain": [".tscn"] }} }}]
        }});
      }}
      const writable = await tscnFileHandle.createWritable();
      await writable.write(tscnContent);
      await writable.close();
      statusEl.textContent = "✅ Đã ghi đè trực tiếp vào file c001_hac_kiem_tan_binh.tscn (" + new Date().toLocaleTimeString() + ")";
      return;
    }} catch (e) {{
      if (e.name === "AbortError") {{
        statusEl.textContent = "Đã hủy lưu file.";
        return;
      }}
    }}
  }}

  const blob = new Blob([tscnContent], {{ type: "text/plain;charset=utf-8" }});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "c001_hac_kiem_tan_binh.tscn";
  a.click();
  statusEl.textContent = "⬇️ Đã tải file c001_hac_kiem_tan_binh.tscn (Hãy chép đè vào thư mục godot/)";
}}

buildSidebarLists();
buildFramePills();
syncInspectorUI();
requestAnimationFrame(tick);
</script>
</body>
</html>
"""

with open(HTML_EDITOR_PATH, "w", encoding="utf-8") as f:
    f.write(html_content)
print(f"Generated 18-Bone Interactive HTML Editor -> {HTML_EDITOR_PATH} ({os.path.getsize(HTML_EDITOR_PATH)/1024:.1f} KB)")
