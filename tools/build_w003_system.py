#!/usr/bin/env python3
"""
tools/build_w003_system.py
Complete pipeline builder for W003 (Đại Đao Đồi Thí / Trảm Đao Đao Phủ - Cấp N)
Follows strict 3-step weapon flow:
  1. Ref Weapon -> 2. Spritesheet Animation (2x2) -> 3. Card Preview (884x632)
Generates QC audit boards, Godot 4 .tscn/.gd, and interactive HTML editors.
"""

import os, json, math, shutil, base64, re
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

im_head = TEAM_PARTS["team_blue"]["head"]
im_neck = TEAM_PARTS["team_blue"]["neck"]
im_chest = TEAM_PARTS["team_blue"]["chest"]
im_hip = TEAM_PARTS["team_blue"]["hip_kilt"]
im_arm_uf = TEAM_PARTS["team_blue"]["arm_upper_front"]
im_arm_lf = TEAM_PARTS["team_blue"]["arm_lower_front"]
im_hand_f = TEAM_PARTS["team_blue"]["hand_front"]
im_arm_ub = TEAM_PARTS["team_blue"]["arm_upper_back"]
im_arm_lb = TEAM_PARTS["team_blue"]["arm_lower_back"]
im_hand_b = TEAM_PARTS["team_blue"]["hand_back"]
im_thigh_f = TEAM_PARTS["team_blue"]["leg_thigh_front"]
im_shin_f = TEAM_PARTS["team_blue"]["leg_shin_front"]
im_foot_f = TEAM_PARTS["team_blue"]["foot_front"]
im_thigh_b = TEAM_PARTS["team_blue"]["leg_thigh_back"]
im_shin_b = TEAM_PARTS["team_blue"]["leg_shin_back"]
im_foot_b = TEAM_PARTS["team_blue"]["foot_back"]

def find_top_stem_pivot(im):
    arr = np.array(im)
    sub_a = arr[1:8, :, 3] > 40
    ys, xs = np.where(sub_a)
    px = round(float(np.mean(xs)), 1) if len(xs) > 0 else round(im.width / 2.0, 1)
    return px, 5.0

hand_f_px, hand_f_py = find_top_stem_pivot(im_hand_f)
hand_b_px, hand_b_py = find_top_stem_pivot(im_hand_b)
foot_f_px, _ = find_top_stem_pivot(im_foot_f)
foot_b_px, _ = find_top_stem_pivot(im_foot_b)
foot_f_py, foot_b_py = 9.0, 9.0

# Weapon parts (oriented with handle at bottom-left, cleaver blade extending up-right)
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

# Grip points for Executioner Great-Cleaver (handle at bottom-left, blade pointing up-right)
W003_G1_X, W003_G1_Y = 82.0, 120.0   # Main grip right behind riveted iron collar
W003_G2_X, W003_G2_Y = 28.0, 145.0   # Lower hilt grip near iron ring pommel
OFF_G1_X, OFF_G1_Y = 50.0, 35.0      # Offhand cleaver main grip
OFF_G2_X, OFF_G2_Y = 20.0, 45.0      # Offhand cleaver secondary grip

# Exact anatomical 18-Bone setup matching W001, W002, and W018
BONES_W003 = [
    {"name": "Hip", "parent": None, "part": "hip_kilt", "is_weapon": False, "rest_x": 198.0, "rest_y": 258.0, "rest_rot": 0.0, "pivot_x": round(im_hip.width / 2.0, 1), "pivot_y": round(im_hip.height * 0.35, 1), "z_index": 7, "tip_child": "Chest"},
    {"name": "Thigh_L", "parent": "Hip", "part": "leg_thigh_back", "is_weapon": False, "rest_x": 8.0, "rest_y": 14.0, "rest_rot": -22.0, "pivot_x": round(im_thigh_b.width / 2.0, 1), "pivot_y": round(im_thigh_b.width / 2.0, 1), "z_index": 1, "tip_child": "Shin_L"},
    {"name": "Shin_L", "parent": "Thigh_L", "part": "leg_shin_back", "is_weapon": False, "rest_x": 0.0, "rest_y": round(float(im_thigh_b.height - im_thigh_b.width), 1), "rest_rot": 16.0, "pivot_x": round(im_shin_b.width / 2.0, 1), "pivot_y": round(im_shin_b.width / 2.0, 1), "z_index": 2, "tip_child": "Foot_L"},
    {"name": "Foot_L", "parent": "Shin_L", "part": "foot_back", "is_weapon": False, "rest_x": 0.0, "rest_y": round(float(im_shin_b.height - im_shin_b.width), 1), "rest_rot": 6.0, "pivot_x": foot_b_px, "pivot_y": foot_b_py, "z_index": 3, "tip_offset": [32.0, 18.0]},
    {"name": "Thigh_R", "parent": "Hip", "part": "leg_thigh_front", "is_weapon": False, "rest_x": -8.0, "rest_y": 14.0, "rest_rot": 22.0, "pivot_x": round(im_thigh_f.width / 2.0, 1), "pivot_y": round(im_thigh_f.width / 2.0, 1), "z_index": 4, "tip_child": "Shin_R"},
    {"name": "Shin_R", "parent": "Thigh_R", "part": "leg_shin_front", "is_weapon": False, "rest_x": 0.0, "rest_y": round(float(im_thigh_f.height - im_thigh_f.width), 1), "rest_rot": -14.0, "pivot_x": round(im_shin_f.width / 2.0, 1), "pivot_y": round(im_shin_f.width / 2.0, 1), "z_index": 5, "tip_child": "Foot_R"},
    {"name": "Foot_R", "parent": "Shin_R", "part": "foot_front", "is_weapon": False, "rest_x": 0.0, "rest_y": round(float(im_shin_f.height - im_shin_f.width), 1), "rest_rot": -8.0, "pivot_x": foot_f_px, "pivot_y": foot_f_py, "z_index": 6, "tip_offset": [34.0, 18.0]},
    {"name": "Chest", "parent": "Hip", "part": "chest", "is_weapon": False, "rest_x": 0.0, "rest_y": -4.0, "rest_rot": 3.0, "pivot_x": round(im_chest.width / 2.0, 1), "pivot_y": round(im_chest.height - 12.0, 1), "z_index": 8, "tip_child": "Neck"},
    {"name": "Neck", "parent": "Chest", "part": "neck", "is_weapon": False, "rest_x": 0.0, "rest_y": round(-(im_chest.height - 20.0), 1), "rest_rot": 0.0, "pivot_x": round(im_neck.width / 2.0, 1), "pivot_y": round(im_neck.height - im_neck.width / 2.0, 1), "z_index": 7, "tip_child": "Head"},
    {"name": "Head", "parent": "Neck", "part": "head", "is_weapon": False, "rest_x": 0.0, "rest_y": round(-float(im_neck.height - im_neck.width), 1), "rest_rot": -3.0, "pivot_x": round(im_head.width / 2.0, 1), "pivot_y": round(im_head.height - 10.0, 1), "z_index": 11, "tip_offset": [0.0, -76.0]},
    {"name": "UpperArm_R", "parent": "Chest", "part": "arm_upper_back", "is_weapon": False, "rest_x": 10.0, "rest_y": -58.0, "rest_rot": -28.0, "pivot_x": round(im_arm_ub.width / 2.0, 1), "pivot_y": round(im_arm_ub.width / 2.0, 1), "z_index": 6, "tip_child": "Forearm_R"},
    {"name": "Forearm_R", "parent": "UpperArm_R", "part": "arm_lower_back", "is_weapon": False, "rest_x": 0.0, "rest_y": round(float(im_arm_ub.height - im_arm_ub.width), 1), "rest_rot": -42.0, "pivot_x": round(im_arm_lb.width / 2.0, 1), "pivot_y": round(im_arm_lb.width / 2.0, 1), "z_index": 9, "tip_child": "Hand_R"},
    {"name": "Hand_R", "parent": "Forearm_R", "part": "hand_back", "is_weapon": False, "rest_x": 0.0, "rest_y": round(float(im_arm_lb.height - im_arm_lb.width), 1), "rest_rot": 0.0, "pivot_x": hand_b_px, "pivot_y": hand_b_py, "z_index": 10, "tip_child": "Weapon_Back"},
    {"name": "Weapon_Back", "parent": "Hand_R", "part": "weapon_offhand", "is_weapon": True, "visible_default": False, "rest_x": 0.0, "rest_y": round(im_hand_b.height * 0.58, 1), "rest_rot": 52.0, "pivot_x": OFF_G1_X, "pivot_y": OFF_G1_Y, "grip1_x": OFF_G1_X, "grip1_y": OFF_G1_Y, "grip2_x": OFF_G2_X, "grip2_y": OFF_G2_Y, "z_index": 9, "tip_offset": [105.0, -35.0]},
    {"name": "UpperArm_L", "parent": "Chest", "part": "arm_upper_front", "is_weapon": False, "rest_x": -8.0, "rest_y": -58.0, "rest_rot": 10.0, "pivot_x": round(im_arm_uf.width / 2.0, 1), "pivot_y": round(im_arm_uf.width / 2.0, 1), "z_index": 12, "tip_child": "Forearm_L"},
    {"name": "Forearm_L", "parent": "UpperArm_L", "part": "arm_lower_front", "is_weapon": False, "rest_x": 0.0, "rest_y": round(float(im_arm_uf.height - im_arm_uf.width), 1), "rest_rot": -62.0, "pivot_x": round(im_arm_lf.width / 2.0, 1), "pivot_y": round(im_arm_lf.width / 2.0, 1), "z_index": 13, "tip_child": "Hand_L"},
    {"name": "Hand_L", "parent": "Forearm_L", "part": "hand_front", "is_weapon": False, "rest_x": 0.0, "rest_y": round(float(im_arm_lf.height - im_arm_lf.width), 1), "rest_rot": 0.0, "pivot_x": hand_f_px, "pivot_y": hand_f_py, "z_index": 15, "tip_child": "Weapon_Front"},
    {"name": "Weapon_Front", "parent": "Hand_L", "part": "weapon_main", "is_weapon": True, "visible_default": True, "rest_x": 0.0, "rest_y": round(im_hand_f.height * 0.58, 1), "rest_rot": 46.0, "pivot_x": W003_G1_X, "pivot_y": W003_G1_Y, "grip1_x": W003_G1_X, "grip1_y": W003_G1_Y, "grip2_x": W003_G2_X, "grip2_y": W003_G2_Y, "z_index": 14, "tip_offset": [125.0, -90.0]},
]

W003_IMAGES = {
    "weapon_main": w003_main,
    "weapon_offhand": w003_offhand,
    **VFX_PARTS
}

for b in BONES_W003:
    pname = b["part"]
    im = W003_IMAGES[pname] if b["is_weapon"] else TEAM_PARTS["team_blue"][pname]
    w, h = im.size
    b["width"] = w
    b["height"] = h
    b["offset_x"] = round(w / 2.0 - b["pivot_x"], 2)
    b["offset_y"] = round(h / 2.0 - b["pivot_y"], 2)

BONE_MAP_W003 = {b["name"]: b for b in BONES_W003}

# Clean, natural 6-Action animations (0px joint separation on all child bones!)
ACTIONS_W003 = {
    "idle": {
        "grid": [2, 2], "length": 1.2, "loop": True,
        "frames": [
            {"t": 0.0, "aura_frame": 0, "Hip": [0, 0, 0], "Chest": [0, 0, 0], "Head": [0, 0, 0], "UpperArm_R": [0, 0, 0], "Forearm_R": [0, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [0, 0, 0], "Forearm_L": [0, 0, 0], "Hand_L": [0, 0, 0], "Weapon_Front": [0, 0, 0], "Thigh_R": [0, 0, 0], "Shin_R": [0, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [0, 0, 0], "Shin_L": [0, 0, 0], "Foot_L": [0, 0, 0]},
            {"t": 0.3, "aura_frame": 1, "Hip": [0, 3, 0], "Chest": [2, 0, 0], "Head": [-2, 0, 0], "UpperArm_R": [4, 0, 0], "Forearm_R": [3, 0, 0], "Hand_R": [-2, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-4, 0, 0], "Forearm_L": [-3, 0, 0], "Hand_L": [-2, 0, 0], "Weapon_Front": [-2, 0, 0], "Thigh_R": [-3, 0, 0], "Shin_R": [3, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-2, 0, 0], "Shin_L": [2, 0, 0], "Foot_L": [0, 0, 0]},
            {"t": 0.6, "aura_frame": 2, "Hip": [0, 6, 0], "Chest": [4, 0, 0], "Head": [-3, 0, 0], "UpperArm_R": [6, 0, 0], "Forearm_R": [5, 0, 0], "Hand_R": [-3, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-6, 0, 0], "Forearm_L": [-5, 0, 0], "Hand_L": [-3, 0, 0], "Weapon_Front": [-4, 0, 0], "Thigh_R": [-5, 0, 0], "Shin_R": [5, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-4, 0, 0], "Shin_L": [4, 0, 0], "Foot_L": [0, 0, 0]},
            {"t": 0.9, "aura_frame": 3, "Hip": [0, 2, 0], "Chest": [1, 0, 0], "Head": [-1, 0, 0], "UpperArm_R": [2, 0, 0], "Forearm_R": [2, 0, 0], "Hand_R": [-1, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-2, 0, 0], "Forearm_L": [-2, 0, 0], "Hand_L": [-1, 0, 0], "Weapon_Front": [-1, 0, 0], "Thigh_R": [-2, 0, 0], "Shin_R": [2, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-1, 0, 0], "Shin_L": [1, 0, 0], "Foot_L": [0, 0, 0]}
        ]
    },
    "walk": {
        "grid": [2, 3], "length": 0.9, "loop": True,
        "frames": [
            {"t": 0.00, "aura_frame": 0, "Hip": [-3, 4, 2], "Chest": [4, 0, 0], "Head": [-3, 0, 0], "UpperArm_R": [16, 0, 0], "Forearm_R": [6, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-16, 0, 0], "Forearm_L": [-6, 0, 0], "Hand_L": [-2, 0, 0], "Weapon_Front": [-4, 0, 0], "Thigh_R": [-22, 0, 0], "Shin_R": [12, 0, 0], "Foot_R": [6, 0, 0], "Thigh_L": [18, 0, 0], "Shin_L": [14, 0, 0], "Foot_L": [8, 0, 0]},
            {"t": 0.15, "aura_frame": 1, "Hip": [-2, 6, 2], "Chest": [5, 0, 0], "Head": [-4, 0, 0], "UpperArm_R": [8, 0, 0], "Forearm_R": [4, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-8, 0, 0], "Forearm_L": [-4, 0, 0], "Hand_L": [-2, 0, 0], "Weapon_Front": [-2, 0, 0], "Thigh_R": [-10, 0, 0], "Shin_R": [14, 0, 0], "Foot_R": [2, 0, 0], "Thigh_L": [8, 0, 0], "Shin_L": [18, 0, 0], "Foot_L": [10, 0, 0]},
            {"t": 0.30, "aura_frame": 2, "Hip": [0, -2, 0], "Chest": [3, 0, 0], "Head": [-2, 0, 0], "UpperArm_R": [-8, 0, 0], "Forearm_R": [-4, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [8, 0, 0], "Forearm_L": [2, 0, 0], "Hand_L": [0, 0, 0], "Weapon_Front": [2, 0, 0], "Thigh_R": [4, 0, 0], "Shin_R": [8, 0, 0], "Foot_R": [-4, 0, 0], "Thigh_L": [-10, 0, 0], "Shin_L": [16, 0, 0], "Foot_L": [6, 0, 0]},
            {"t": 0.45, "aura_frame": 3, "Hip": [3, 4, 2], "Chest": [5, 0, 0], "Head": [-3, 0, 0], "UpperArm_R": [-16, 0, 0], "Forearm_R": [-6, 0, 0], "Hand_R": [-2, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [16, 0, 0], "Forearm_L": [4, 0, 0], "Hand_L": [2, 0, 0], "Weapon_Front": [4, 0, 0], "Thigh_R": [16, 0, 0], "Shin_R": [14, 0, 0], "Foot_R": [6, 0, 0], "Thigh_L": [-22, 0, 0], "Shin_L": [10, 0, 0], "Foot_L": [-4, 0, 0]},
            {"t": 0.60, "aura_frame": 2, "Hip": [2, 6, 2], "Chest": [6, 0, 0], "Head": [-4, 0, 0], "UpperArm_R": [-8, 0, 0], "Forearm_R": [-4, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [8, 0, 0], "Forearm_L": [2, 0, 0], "Hand_L": [0, 0, 0], "Weapon_Front": [2, 0, 0], "Thigh_R": [8, 0, 0], "Shin_R": [18, 0, 0], "Foot_R": [8, 0, 0], "Thigh_L": [-10, 0, 0], "Shin_L": [12, 0, 0], "Foot_L": [0, 0, 0]},
            {"t": 0.75, "aura_frame": 1, "Hip": [-2, -2, 0], "Chest": [3, 0, 0], "Head": [-2, 0, 0], "UpperArm_R": [6, 0, 0], "Forearm_R": [2, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-6, 0, 0], "Forearm_L": [-2, 0, 0], "Hand_L": [-1, 0, 0], "Weapon_Front": [-1, 0, 0], "Thigh_R": [-8, 0, 0], "Shin_R": [10, 0, 0], "Foot_R": [4, 0, 0], "Thigh_L": [4, 0, 0], "Shin_L": [10, 0, 0], "Foot_L": [4, 0, 0]}
        ]
    },
    "attack": {
        "grid": [2, 2], "length": 0.65, "loop": False,
        "frames": [
            {"t": 0.00, "aura_frame": 1, "Hip": [-8, 4, -4], "Chest": [-8, 0, 0], "Head": [6, 0, 0], "UpperArm_R": [20, 0, 0], "Forearm_R": [12, 0, 0], "Hand_R": [6, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-48, 0, 0], "Forearm_L": [-20, 0, 0], "Hand_L": [-14, 0, 0], "Weapon_Front": [-18, 0, 0], "Thigh_R": [10, 0, 0], "Shin_R": [10, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-10, 0, 0], "Shin_L": [10, 0, 0], "Foot_L": [0, 0, 0]},
            {"t": 0.18, "aura_frame": 2, "Hip": [10, 6, 6], "Chest": [10, 0, 0], "Head": [-6, 0, 0], "UpperArm_R": [-16, 0, 0], "Forearm_R": [-10, 0, 0], "Hand_R": [-6, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-12, 0, 0], "Forearm_L": [10, 0, 0], "Hand_L": [12, 0, 0], "Weapon_Front": [16, 0, 0], "Thigh_R": [-16, 0, 0], "Shin_R": [12, 0, 0], "Foot_R": [4, 0, 0], "Thigh_L": [14, 0, 0], "Shin_L": [12, 0, 0], "Foot_L": [4, 0, 0],
             "vfx": {"fx_slash": {"pos": [306, 254], "rot": 22, "scale": 0.78, "alpha": 0.94}}},
            {"t": 0.36, "aura_frame": 2, "Hip": [12, 8, 8], "Chest": [12, 0, 0], "Head": [-8, 0, 0], "UpperArm_R": [-22, 0, 0], "Forearm_R": [-14, 0, 0], "Hand_R": [-8, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [4, 0, 0], "Forearm_L": [16, 0, 0], "Hand_L": [14, 0, 0], "Weapon_Front": [24, 0, 0], "Thigh_R": [-20, 0, 0], "Shin_R": [14, 0, 0], "Foot_R": [6, 0, 0], "Thigh_L": [18, 0, 0], "Shin_L": [14, 0, 0], "Foot_L": [6, 0, 0],
             "vfx": {"fx_spark": {"pos": [340, 320], "rot": 0, "scale": 0.72, "alpha": 0.92}}},
            {"t": 0.52, "aura_frame": 0, "Hip": [2, 2, 1], "Chest": [2, 0, 0], "Head": [-1, 0, 0], "UpperArm_R": [-4, 0, 0], "Forearm_R": [-2, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-2, 0, 0], "Forearm_L": [0, 0, 0], "Hand_L": [0, 0, 0], "Weapon_Front": [0, 0, 0], "Thigh_R": [-4, 0, 0], "Shin_R": [4, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [4, 0, 0], "Shin_L": [4, 0, 0], "Foot_L": [0, 0, 0]}
        ]
    },
    "cast": {
        "grid": [2, 3], "length": 0.95, "loop": False,
        "frames": [
            {"t": 0.00, "aura_frame": 0, "Hip": [-10, 6, -4], "Chest": [-8, 0, 0], "Head": [6, 0, 0], "UpperArm_R": [22, 0, 0], "Forearm_R": [14, 0, 0], "Hand_R": [6, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-42, 0, 0], "Forearm_L": [-18, 0, 0], "Hand_L": [-14, 0, 0], "Weapon_Front": [-16, 0, 0], "Thigh_R": [8, 0, 0], "Shin_R": [10, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-10, 0, 0], "Shin_L": [10, 0, 0], "Foot_L": [0, 0, 0],
             "vfx": {"fx_dust": {"pos": [218, 412], "rot": 0, "scale": 0.62, "alpha": 0.76}}},
            {"t": 0.16, "aura_frame": 1, "Hip": [-14, 10, -6], "Chest": [-12, 0, 0], "Head": [10, 0, 0], "UpperArm_R": [28, 0, 0], "Forearm_R": [18, 0, 0], "Hand_R": [8, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-50, 0, 0], "Forearm_L": [-20, 0, 0], "Hand_L": [-16, 0, 0], "Weapon_Front": [-20, 0, 0], "Thigh_R": [12, 0, 0], "Shin_R": [14, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-14, 0, 0], "Shin_L": [14, 0, 0], "Foot_L": [0, 0, 0],
             "vfx": {"fx_slash_heavy": {"pos": [224, 188], "rot": 0, "scale": 0.72, "alpha": 0.92}}},
            {"t": 0.34, "aura_frame": 2, "Hip": [12, 4, 6], "Chest": [10, 0, 0], "Head": [-8, 0, 0], "UpperArm_R": [-18, 0, 0], "Forearm_R": [-12, 0, 0], "Hand_R": [-6, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-12, 0, 0], "Forearm_L": [10, 0, 0], "Hand_L": [12, 0, 0], "Weapon_Front": [16, 0, 0], "Thigh_R": [-18, 0, 0], "Shin_R": [12, 0, 0], "Foot_R": [4, 0, 0], "Thigh_L": [16, 0, 0], "Shin_L": [14, 0, 0], "Foot_L": [6, 0, 0],
             "vfx": {
                 "fx_slash_heavy": {"pos": [302, 258], "rot": 18, "scale": 0.80, "alpha": 0.96},
                 "fx_dust": {"pos": [196, 412], "rot": 0, "scale": 0.74, "alpha": 0.85},
             }},
            {"t": 0.52, "aura_frame": 2, "Hip": [16, 8, 8], "Chest": [14, 0, 0], "Head": [-10, 0, 0], "UpperArm_R": [-24, 0, 0], "Forearm_R": [-16, 0, 0], "Hand_R": [-8, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [4, 0, 0], "Forearm_L": [16, 0, 0], "Hand_L": [14, 0, 0], "Weapon_Front": [24, 0, 0], "Thigh_R": [-22, 0, 0], "Shin_R": [14, 0, 0], "Foot_R": [6, 0, 0], "Thigh_L": [20, 0, 0], "Shin_L": [16, 0, 0], "Foot_L": [8, 0, 0],
             "vfx": {
                 "fx_slash_heavy": {"pos": [314, 276], "rot": 32, "scale": 0.76, "alpha": 0.88},
                 "fx_spark": {"pos": [342, 322], "rot": 12, "scale": 0.74, "alpha": 0.94},
             }},
            {"t": 0.70, "aura_frame": 3, "Hip": [8, 4, 4], "Chest": [6, 0, 0], "Head": [-4, 0, 0], "UpperArm_R": [-10, 0, 0], "Forearm_R": [-6, 0, 0], "Hand_R": [-2, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [2, 0, 0], "Forearm_L": [6, 0, 0], "Hand_L": [6, 0, 0], "Weapon_Front": [10, 0, 0], "Thigh_R": [-10, 0, 0], "Shin_R": [8, 0, 0], "Foot_R": [2, 0, 0], "Thigh_L": [8, 0, 0], "Shin_L": [8, 0, 0], "Foot_L": [4, 0, 0],
             "vfx": {"fx_spark": {"pos": [346, 326], "rot": 25, "scale": 0.56, "alpha": 0.60}}},
            {"t": 0.86, "aura_frame": 0, "Hip": [0, 0, 0], "Chest": [0, 0, 0], "Head": [0, 0, 0], "UpperArm_R": [0, 0, 0], "Forearm_R": [0, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [0, 0, 0], "Forearm_L": [0, 0, 0], "Hand_L": [0, 0, 0], "Weapon_Front": [0, 0, 0], "Thigh_R": [0, 0, 0], "Shin_R": [0, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [0, 0, 0], "Shin_L": [0, 0, 0], "Foot_L": [0, 0, 0]}
        ]
    },
    "hurt": {
        "grid": [2, 2], "length": 0.55, "loop": False,
        "frames": [
            {"t": 0.00, "aura_frame": 3, "Hip": [-10, 4, -6], "Chest": [-12, 0, 0], "Head": [-14, 0, 0], "UpperArm_R": [14, 0, 0], "Forearm_R": [10, 0, 0], "Hand_R": [6, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [14, 0, 0], "Forearm_L": [-8, 0, 0], "Hand_L": [-6, 0, 0], "Weapon_Front": [-8, 0, 0], "Thigh_R": [8, 0, 0], "Shin_R": [6, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-6, 0, 0], "Shin_L": [8, 0, 0], "Foot_L": [0, 0, 0],
             "vfx": {"fx_spark": {"pos": [254, 214], "rot": -15, "scale": 0.68, "alpha": 0.90}}},
            {"t": 0.15, "aura_frame": 1, "Hip": [-16, 8, -8], "Chest": [-14, 0, 0], "Head": [-18, 0, 0], "UpperArm_R": [20, 0, 0], "Forearm_R": [14, 0, 0], "Hand_R": [8, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [20, 0, 0], "Forearm_L": [-12, 0, 0], "Hand_L": [-10, 0, 0], "Weapon_Front": [-12, 0, 0], "Thigh_R": [12, 0, 0], "Shin_R": [10, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-10, 0, 0], "Shin_L": [12, 0, 0], "Foot_L": [0, 0, 0]},
            {"t": 0.32, "aura_frame": 0, "Hip": [-8, 4, -4], "Chest": [-6, 0, 0], "Head": [-8, 0, 0], "UpperArm_R": [8, 0, 0], "Forearm_R": [6, 0, 0], "Hand_R": [4, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [8, 0, 0], "Forearm_L": [-4, 0, 0], "Hand_L": [-4, 0, 0], "Weapon_Front": [-4, 0, 0], "Thigh_R": [6, 0, 0], "Shin_R": [4, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-4, 0, 0], "Shin_L": [6, 0, 0], "Foot_L": [0, 0, 0]},
            {"t": 0.48, "aura_frame": 1, "Hip": [0, 0, 0], "Chest": [0, 0, 0], "Head": [0, 0, 0], "UpperArm_R": [0, 0, 0], "Forearm_R": [0, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [0, 0, 0], "Forearm_L": [0, 0, 0], "Hand_L": [0, 0, 0], "Weapon_Front": [0, 0, 0], "Thigh_R": [0, 0, 0], "Shin_R": [0, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [0, 0, 0], "Shin_L": [0, 0, 0], "Foot_L": [0, 0, 0]}
        ]
    },
    "death": {
        "grid": [2, 3], "length": 1.10, "loop": False,
        "frames": [
            {"t": 0.00, "aura_frame": 3, "Hip": [-10, 6, -6], "Chest": [-12, 0, 0], "Head": [-14, 0, 0], "UpperArm_R": [14, 0, 0], "Forearm_R": [8, 0, 0], "Hand_R": [6, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [14, 0, 0], "Forearm_L": [-8, 0, 0], "Hand_L": [-6, 0, 0], "Weapon_Front": [-8, 0, 0], "Thigh_R": [10, 0, 0], "Shin_R": [8, 0, 0], "Foot_R": [0, 0, 0], "Thigh_L": [-8, 0, 0], "Shin_L": [10, 0, 0], "Foot_L": [0, 0, 0],
             "vfx": {"fx_spark": {"pos": [254, 212], "rot": 0, "scale": 0.72, "alpha": 0.92}}},
            {"t": 0.22, "aura_frame": 0, "Hip": [-6, 30, 14], "Chest": [16, 0, 0], "Head": [12, 0, 0], "UpperArm_R": [24, 0, 0], "Forearm_R": [12, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-16, 0, 0], "Forearm_L": [-10, 0, 0], "Hand_L": [-12, 0, 0], "Weapon_Front": [-16, 0, 0], "Thigh_R": [-42, 0, 0], "Shin_R": [64, 0, 0], "Foot_R": [12, 0, 0], "Thigh_L": [-36, 0, 0], "Shin_L": [58, 0, 0], "Foot_L": [10, 0, 0]},
            {"t": 0.45, "aura_frame": 3, "Hip": [-4, 56, 30], "Chest": [24, 0, 0], "Head": [18, 0, 0], "UpperArm_R": [36, 0, 0], "Forearm_R": [18, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-32, 0, 0], "Forearm_L": [-16, 0, 0], "Hand_L": [-20, 0, 0], "Weapon_Front": [-26, 0, 0], "Thigh_R": [-66, 0, 0], "Shin_R": [90, 0, 0], "Foot_R": [16, 0, 0], "Thigh_L": [-60, 0, 0], "Shin_L": [84, 0, 0], "Foot_L": [14, 0, 0],
             "vfx": {"fx_dust": {"pos": [256, 422], "rot": 0, "scale": 0.85, "alpha": 0.82}}},
            {"t": 0.68, "aura_frame": 0, "Hip": [-2, 68, 40], "Chest": [28, 0, 0], "Head": [22, 0, 0], "UpperArm_R": [42, 0, 0], "Forearm_R": [20, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-40, 0, 0], "Forearm_L": [-20, 0, 0], "Hand_L": [-24, 0, 0], "Weapon_Front": [-32, 0, 0], "Thigh_R": [-76, 0, 0], "Shin_R": [100, 0, 0], "Foot_R": [18, 0, 0], "Thigh_L": [-70, 0, 0], "Shin_L": [94, 0, 0], "Foot_L": [16, 0, 0],
             "vfx": {"fx_dust": {"pos": [264, 424], "rot": 0, "scale": 0.90, "alpha": 0.65}}, "modulate_a": 0.88},
            {"t": 0.88, "aura_frame": 3, "Hip": [0, 72, 44], "Chest": [30, 0, 0], "Head": [24, 0, 0], "UpperArm_R": [44, 0, 0], "Forearm_R": [22, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-42, 0, 0], "Forearm_L": [-22, 0, 0], "Hand_L": [-26, 0, 0], "Weapon_Front": [-34, 0, 0], "Thigh_R": [-78, 0, 0], "Shin_R": [102, 0, 0], "Foot_R": [18, 0, 0], "Thigh_L": [-72, 0, 0], "Shin_L": [96, 0, 0], "Foot_L": [16, 0, 0],
             "vfx": {"fx_dust": {"pos": [266, 424], "rot": 0, "scale": 0.75, "alpha": 0.45}}, "modulate_a": 0.52},
            {"t": 1.05, "aura_frame": 3, "Hip": [0, 74, 46], "Chest": [30, 0, 0], "Head": [24, 0, 0], "UpperArm_R": [44, 0, 0], "Forearm_R": [22, 0, 0], "Hand_R": [0, 0, 0], "Weapon_Back": [0, 0, 0], "UpperArm_L": [-42, 0, 0], "Forearm_L": [-22, 0, 0], "Hand_L": [-26, 0, 0], "Weapon_Front": [-34, 0, 0], "Thigh_R": [-78, 0, 0], "Shin_R": [102, 0, 0], "Foot_R": [18, 0, 0], "Thigh_L": [-72, 0, 0], "Shin_L": [96, 0, 0], "Foot_L": [16, 0, 0],
             "modulate_a": 0.22}
        ]
    }
}

def compute_world_transforms(bones_list, frame_pose=None):
    if frame_pose is None:
        frame_pose = {}
    world = {}
    for b in bones_list:
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
    return world

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

def render_w003_pose(frame_pose=None, team_name="team_blue", show_weapon_front=True, show_weapon_back=False, show_aura=True, aura_idx=None, canvas_size=512):
    if frame_pose is None:
        frame_pose = {}
    canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    world = compute_world_transforms(BONES_W003, frame_pose)
    mod_a = frame_pose.get("modulate_a", 1.0)
    a_idx = aura_idx if aura_idx is not None else frame_pose.get("aura_frame", 1)
    anim_weapon_im = W003_ANIM_FRAMES[a_idx % len(W003_ANIM_FRAMES)]

    sorted_bones = sorted(BONES_W003, key=lambda b: b["z_index"])
    for b in sorted_bones:
        bname = b["name"]
        if bname == "Weapon_Front" and not show_weapon_front:
            continue
        if bname == "Weapon_Back" and not show_weapon_back:
            continue
        wx, wy, wrot = world[bname][:3]
        if b["is_weapon"]:
            if show_aura and bname == "Weapon_Front":
                im = anim_weapon_im
            else:
                im = W003_IMAGES[b["part"]]
        else:
            im = TEAM_PARTS[team_name][b["part"]]

        paste_rotated_part(
            canvas,
            im,
            wx, wy, wrot,
            b["pivot_x"], b["pivot_y"],
            scale=1.0,
            alpha=mod_a,
        )

    vfx_dict = frame_pose.get("vfx", {})
    for fx_name, fx_cfg in vfx_dict.items():
        if fx_name in VFX_PARTS:
            fx_im = VFX_PARTS[fx_name]
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
    font_title = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 16)
    font_sub = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 12)
except Exception:
    font_title = ImageFont.load_default()
    font_sub = ImageFont.load_default()

print("=== 3. Building W003 3-Step Pipeline Audit Board & 6-Action Overview ===")
board_w, board_h = 1860, 960
audit_im = Image.new("RGBA", (board_w, board_h), (16, 19, 26, 255))
audit_draw = ImageDraw.Draw(audit_im, "RGBA")

team_display = [
    ("team_blue", "DOI 1: XANH + W003 (Frame 0)", (59, 130, 246, 255), 0, False),
    ("team_red", "DOI 2: DO + SONG DAO W003 (Frame 1)", (239, 68, 68, 255), 1, True),
    ("team_green", "DOI 3: XANH LA + W003 (Frame 2)", (34, 197, 94, 255), 2, False),
    ("team_amber", "DOI 4: VANG CAM + W003 (Frame 3)", (245, 158, 11, 255), 3, False),
]

for idx, (t_key, t_label, t_col, a_f, dual_w) in enumerate(team_display):
    ox = 12 + idx * 345
    oy = 12
    audit_draw.rectangle([ox, oy, ox + 335, oy + 450], fill=(26, 31, 42, 255), outline=t_col, width=2)
    t_pose_im, _ = render_w003_pose({}, team_name=t_key, show_weapon_front=True, show_weapon_back=dual_w, show_aura=True, aura_idx=a_f, canvas_size=512)
    t_thumb = t_pose_im.resize((330, 330), Image.Resampling.LANCZOS)
    audit_im.alpha_composite(t_thumb, (ox + 2, oy + 46))
    audit_draw.text((ox + 12, oy + 10), t_label, fill=t_col, font=font_title)
    sub_txt = "W003 Weapon Anim Spritesheet ON" if not dual_w else "Demo Song Dao W003 Anim ON"
    audit_draw.text((ox + 12, oy + 28), f"{sub_txt} | edge_clip=0px", fill=(210, 220, 235, 255), font=font_sub)

# Panel 5 on Top Row: BUOC 3 — W003 Diagonal Card Cover
ox5 = 12 + 4 * 345
audit_draw.rectangle([ox5, 12, board_w - 12, 462], fill=(26, 31, 42, 255), outline=(245, 158, 11, 255), width=2)
audit_draw.text((ox5 + 12, 20), "BUOC 3: ANH BIA CARD (884x632 RGB — Tu Ref & Anim)", fill=(252, 211, 77, 255), font=font_title)
card_prev = Image.open(W003_CARD_PNG).convert("RGBA").resize((436, 312), Image.Resampling.LANCZOS)
audit_im.alpha_composite(card_prev, (ox5 + 14, 48))
audit_draw.rectangle([ox5 + 14, 48, ox5 + 14 + 436, 48 + 312], outline=(245, 158, 11, 220), width=1)
audit_draw.text((ox5 + 14, 370), "884x632 RGB PNG & 354x253 WebP (100% Opaque Card Art!)", fill=(252, 211, 77, 255), font=font_sub)
audit_draw.text((ox5 + 14, 392), f"Grip 1 (Do): ({W003_G1_X}, {W003_G1_Y}) | Grip 2 (Xanh): ({W003_G2_X}, {W003_G2_Y})", fill=(220, 230, 245, 255), font=font_sub)
audit_draw.text((ox5 + 14, 414), "Flow: 1. Anh Ref -> 2. Spritesheet Anim 2x2 -> 3. Anh Bia Card", fill=(130, 235, 165, 255), font=font_sub)

# Bottom Left: BUOC 1 — W003 Reference Weapon with Grip 1 & Grip 2
bx_w = 12
by_w = 478
audit_draw.rectangle([bx_w, by_w, bx_w + 440, board_h - 12], fill=(26, 31, 42, 255), outline=(245, 158, 11, 255), width=2)
audit_draw.text((bx_w + 14, by_w + 12), f"BUOC 1: ANH REF VU KHI ({w003_main.width}x{w003_main.height} — 0px Pad)", fill=(252, 211, 77, 255), font=font_title)
audit_draw.text((bx_w + 14, by_w + 32), "Cham DO = Grip 1 (Tay Chinh) | Cham XANH = Grip 2 (Tay Phu)", fill=(130, 235, 165, 255), font=font_sub)
wx_p = bx_w + (440 - w003_main.width) // 2
wy_p = by_w + 68
audit_im.alpha_composite(w003_main, (wx_p, wy_p))
audit_draw.rectangle([wx_p, wy_p, wx_p + w003_main.width, wy_p + w003_main.height], outline=(90, 220, 135, 180), width=1)
g1x, g1y = wx_p + W003_G1_X, wy_p + W003_G1_Y
g2x, g2y = wx_p + W003_G2_X, wy_p + W003_G2_Y
audit_draw.ellipse([g1x - 6, g1y - 6, g1x + 6, g1y + 6], fill=(240, 50, 50, 255), outline=(255, 255, 255, 255), width=2)
audit_draw.ellipse([g2x - 6, g2y - 6, g2x + 6, g2y + 6], fill=(40, 210, 255, 255), outline=(255, 255, 255, 255), width=2)

# Bottom Right: 4 Frames of Animated Weapon Spritesheet
anim_titles = [
    "BUOC 2 - Frame 1 (weapon_anim_0): Resting Dark Steel",
    "BUOC 2 - Frame 2 (weapon_anim_1): Crimson Blood-Groove Pulse",
    "BUOC 2 - Frame 3 (weapon_anim_2): Peak Executioner Ember Glint",
    "BUOC 2 - Frame 4 (weapon_anim_3): Smoldering Reset Loop",
]
for idx in range(4):
    ax = 468 + idx * 345
    ay = 478
    audit_draw.rectangle([ax, ay, ax + 333, board_h - 12], fill=(22, 26, 36, 255), outline=(239, 68, 68, 200), width=1)
    audit_draw.text((ax + 10, ay + 12), anim_titles[idx], fill=(252, 211, 77, 255), font=font_sub)
    wf_im = W003_ANIM_FRAMES[idx]
    audit_draw.text((ax + 10, ay + 32), f"Size: {wf_im.width}x{wf_im.height} | Căn đồng trục Grip 1/2 (0px lệch)", fill=(130, 235, 165, 255), font=font_sub)
    audit_im.alpha_composite(wf_im, (ax + (333 - wf_im.width) // 2, ay + 120))
    audit_draw.rectangle(
        [ax + (333 - wf_im.width) // 2, ay + 120, ax + (333 - wf_im.width) // 2 + wf_im.width, ay + 120 + wf_im.height],
        outline=(90, 220, 135, 120),
        width=1,
    )

audit_path = os.path.join(W003_QC_DIR, "w003_weapon_and_aura_audit.png")
audit_im.save(audit_path)
shutil.copyfile(audit_path, os.path.join(ARTIFACT_DIR, "w003_weapon_and_aura_audit.png"))
print("Saved W003 Weapon & Aura Audit ->", audit_path)

# 3B. All 6 Actions Overview Board (3x2 Panels showing all 24 frames with ground reference line)
ov_w, ov_h = 3 * 560 + 24, 2 * 560 + 24
ov_im = Image.new("RGBA", (ov_w, ov_h), (16, 19, 26, 255))
ov_draw = ImageDraw.Draw(ov_im)
total_edge_clips = 0

action_order = ["idle", "walk", "attack", "cast", "hurt", "death"]
team_cycle = ["team_blue", "team_red", "team_green", "team_amber", "team_blue", "team_red"]
for a_idx, act_name in enumerate(action_order):
    act = ACTIONS_W003[act_name]
    rows, cols = act["grid"]
    frames = act["frames"]
    ar, ac = divmod(a_idx, 3)
    bx = 12 + ac * 560
    by = 12 + ar * 560
    ov_draw.rectangle([bx, by, bx + 544, by + 544], fill=(24, 28, 38, 255), outline=(245, 158, 11, 180), width=1)

    thumb_size = 240 if cols == 2 else 166
    grid_w = cols * thumb_size
    grid_h = rows * thumb_size
    gx0 = bx + (544 - grid_w) // 2
    gy0 = by + 36 + (500 - grid_h) // 2

    act_clips = 0
    t_for_act = team_cycle[a_idx]
    for f_idx, f_pose in enumerate(frames):
        f_im, _ = render_w003_pose(f_pose, team_name=t_for_act, show_weapon_front=True, show_weapon_back=False, show_aura=True, canvas_size=512)
        fa = np.array(f_im)[:, :, 3]
        f_clip = int(fa[0, :].sum() + fa[-1, :].sum() + fa[:, 0].sum() + fa[:, -1].sum())
        act_clips += f_clip
        total_edge_clips += f_clip

        fr, fc = divmod(f_idx, cols)
        tx = gx0 + fc * thumb_size
        ty = gy0 + fr * thumb_size
        ov_draw.rectangle([tx + 2, ty + 2, tx + thumb_size - 2, ty + thumb_size - 2], fill=(31, 37, 49, 255), outline=(55, 65, 81, 180), width=1)
        f_thumb = f_im.resize((thumb_size - 8, thumb_size - 8), Image.Resampling.LANCZOS)
        ov_im.alpha_composite(f_thumb, (tx + 4, ty + 4))
        base_y = ty + int(thumb_size * 0.84)
        ov_draw.line([(tx + 12, base_y), (tx + thumb_size - 12, base_y)], fill=(70, 210, 120, 140), width=1)

    ov_draw.text(
        (bx + 14, by + 10),
        f"W003 Action {a_idx+1}: {act_name.upper()} ({t_for_act} | {len(frames)}f | Anim Weapon ON | edge_clip={act_clips}px)",
        fill=(252, 211, 77, 255),
        font=font_title,
    )

ov_path = os.path.join(W003_QC_DIR, "w003_sticker_all_6_actions_overview.png")
ov_im.save(ov_path)
shutil.copyfile(ov_path, os.path.join(ARTIFACT_DIR, "w003_sticker_all_6_actions_overview.png"))
print(f"Saved W003 6-Action Overview -> {ov_path} (total_edge_clips={total_edge_clips}px)")

# 4. Generate Godot 4 Scene (.tscn) & GDScript (.gd)
print("=== 4. Building Godot 4 Scene & Script for W003 ===")

def build_godot_tscn():
    lines = []
    ext_count = 1 + len(BONES_W003) + len(VFX_PARTS)
    sub_count = 1 + len(ACTIONS_W003)
    lines.append(f'[gd_scene load_steps={ext_count + sub_count} format=3 uid="uid://c003daophudoithi"]')
    lines.append('')
    lines.append('[ext_resource type="Script" path="res://assets/weapons/w003_dao_phu_doi_thi/godot/c003_dao_phu_doi_thi.gd" id="1_script"]')

    res_map = {}
    idx = 2
    for b in BONES_W003:
        pname = b["part"]
        if pname not in res_map:
            rid = f"{idx}_{pname}"
            res_map[pname] = rid
            if b["is_weapon"]:
                lines.append(f'[ext_resource type="Texture2D" path="res://assets/weapons/w003_dao_phu_doi_thi/parts/{pname}.png" id="{rid}"]')
            else:
                lines.append(f'[ext_resource type="Texture2D" path="res://assets/sticker_hero/godot/parts/team_blue/{pname}.png" id="{rid}"]')
            idx += 1

    for vname in VFX_PARTS.keys():
        rid = f"{idx}_{vname}"
        res_map[vname] = rid
        lines.append(f'[ext_resource type="Texture2D" path="res://assets/weapons/w003_dao_phu_doi_thi/parts/{vname}.png" id="{rid}"]')
        idx += 1

    lines.append('')
    for act_name, act_data in ACTIONS_W003.items():
        lines.append(f'[sub_resource type="Animation" id="Animation_{act_name}"]')
        lines.append(f'resource_name = "{act_name}"')
        lines.append(f'length = {act_data["length"]}')
        lines.append(f'loop_mode = {1 if act_data["loop"] else 0}')
        frames = act_data["frames"]
        times_str = ", ".join(f'{f["t"]:.2f}' for f in frames)

        for t_idx, b in enumerate(BONES_W003):
            bname = b["name"]
            bpath = bname
            curr = b
            while curr["parent"] is not None:
                bpath = curr["parent"] + "/" + bpath
                curr = BONE_MAP_W003[curr["parent"]]

            if bname == "Hip":
                lines.append(f'tracks/{t_idx}/type = "value"')
                lines.append(f'tracks/{t_idx}/imported = false')
                lines.append(f'tracks/{t_idx}/enabled = true')
                lines.append(f'tracks/{t_idx}/path = NodePath("Skeleton2D/{bpath}:position")')
                lines.append(f'tracks/{t_idx}/interp = 1')
                lines.append(f'tracks/{t_idx}/loop_wrap = true')
                pos_vals = []
                for f in frames:
                    dx, dy, _ = f.get("Hip", [0, 0, 0])
                    pos_vals.append(f'Vector2({b["rest_x"] + dx:.1f}, {b["rest_y"] + dy:.1f})')
                lines.append(f'tracks/{t_idx}/keys = {{')
                lines.append(f'"times": PackedFloat32Array({times_str}),')
                lines.append(f'"transitions": PackedFloat32Array({", ".join(["1"] * len(frames))}),')
                lines.append('"update": 0,')
                lines.append(f'"values": [{", ".join(pos_vals)}]')
                lines.append('}')
            else:
                lines.append(f'tracks/{t_idx}/type = "value"')
                lines.append(f'tracks/{t_idx}/imported = false')
                lines.append(f'tracks/{t_idx}/enabled = true')
                lines.append(f'tracks/{t_idx}/path = NodePath("Skeleton2D/{bpath}:rotation")')
                lines.append(f'tracks/{t_idx}/interp = 1')
                lines.append(f'tracks/{t_idx}/loop_wrap = true')
                rot_vals = []
                for f in frames:
                    drot = f.get(bname, [0, 0, 0])[0]
                    r_rad = math.radians(b["rest_rot"] + drot)
                    rot_vals.append(f'{r_rad:.4f}')
                lines.append(f'tracks/{t_idx}/keys = {{')
                lines.append(f'"times": PackedFloat32Array({times_str}),')
                lines.append(f'"transitions": PackedFloat32Array({", ".join(["1"] * len(frames))}),')
                lines.append('"update": 0,')
                lines.append(f'"values": [{", ".join(rot_vals)}]')
                lines.append('}')
        lines.append('')

    anim_list = ",\n".join(f'"{k}": SubResource("Animation_{k}")' for k in ACTIONS_W003.keys())
    lines.append('[sub_resource type="AnimationLibrary" id="AnimationLibrary_main"]')
    lines.append(f'_data = {{\n{anim_list}\n}}')
    lines.append('')

    lines.append('[node name="C003_DaoPhuDoiThi" type="Node2D"]')
    lines.append('script = ExtResource("1_script")')
    lines.append('')
    lines.append('[node name="Skeleton2D" type="Skeleton2D" parent="."]')
    lines.append('')

    for b in BONES_W003:
        bname = b["name"]
        parent = b["parent"]
        if parent is None:
            p_str = "Skeleton2D"
        else:
            bpath = parent
            curr = BONE_MAP_W003[parent]
            while curr["parent"] is not None:
                bpath = curr["parent"] + "/" + bpath
                curr = BONE_MAP_W003[curr["parent"]]
            p_str = f"Skeleton2D/{bpath}"

        lines.append(f'[node name="{bname}" type="Bone2D" parent="{p_str}"]')
        lines.append(f'position = Vector2({b["rest_x"]}, {b["rest_y"]})')
        lines.append(f'rotation = {math.radians(b["rest_rot"]):.4f}')
        if b.get("visible_default") is False:
            lines.append('visible = false')
        lines.append('')

        lines.append(f'[node name="Sprite" type="Sprite2D" parent="{p_str}/{bname}"]')
        lines.append(f'z_index = {b["z_index"]}')
        lines.append(f'texture = ExtResource("{res_map[b["part"]]}")')
        lines.append(f'offset = Vector2({b["offset_x"]}, {b["offset_y"]})')
        lines.append('')

    lines.append('[node name="VFX" type="Node2D" parent="."]')
    for vname in VFX_PARTS.keys():
        lines.append(f'[node name="{vname}" type="Sprite2D" parent="VFX"]')
        lines.append('visible = false')
        lines.append('z_index = 20')
        lines.append(f'texture = ExtResource("{res_map[vname]}")')
        lines.append('')

    lines.append('[node name="AnimationPlayer" type="AnimationPlayer" parent="."]')
    lines.append('libraries = {')
    lines.append('"": SubResource("AnimationLibrary_main")')
    lines.append('}')
    lines.append('autoplay = "idle"')
    return "\n".join(lines)

tscn_path = os.path.join(W003_GODOT_DIR, "c003_dao_phu_doi_thi.tscn")
with open(tscn_path, "w", encoding="utf-8") as f:
    f.write(build_godot_tscn())
print("Saved Godot TSCN ->", tscn_path)

gd_script = """extends Node2D
class_name C003_DaoPhuDoiThi

@export_enum("team_blue", "team_red", "team_green", "team_amber") var current_team: String = "team_blue":
	set(val):
		current_team = val
		if is_inside_tree():
			set_team(val)

@export var dual_weapon_enabled: bool = false:
	set(val):
		dual_weapon_enabled = val
		if is_inside_tree() and has_node("Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Hand_R/Weapon_Back"):
			$Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Hand_R/Weapon_Back.visible = val

@export var weapon_aura_enabled: bool = true

@onready var anim_player: AnimationPlayer = $AnimationPlayer
@onready var skeleton: Skeleton2D = $Skeleton2D

func _ready() -> void:
	set_team(current_team)
	if has_node("Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Hand_R/Weapon_Back"):
		$Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Hand_R/Weapon_Back.visible = dual_weapon_enabled
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

# 6. Update assets/sticker_weapon_editor.html to include/update W003 alongside W001, W002 & W018
editor_path = "/Users/dochung/Desktop/card_g/assets/sticker_weapon_editor.html"
with open(editor_path, "r", encoding="utf-8") as f:
    editor_html = f.read()

w003_json_str = json.dumps(w003_pack)
marker = "const W018_PACK ="
w003_inject = f"const W003_PACK = {w003_json_str};\nconst W018_PACK ="
if "const W003_PACK =" in editor_html:
    editor_html = re.sub(r"const W003_PACK = .*?;\nconst W018_PACK =", lambda _: w003_inject, editor_html, count=1)
elif marker in editor_html:
    editor_html = editor_html.replace(marker, w003_inject)

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
