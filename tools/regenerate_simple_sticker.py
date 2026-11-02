#!/usr/bin/env python3
"""
Regenerates the Minimalist Geometric Stickman (Tướng Sticker Đơn Giản) via Muse Local API in a new thread:
- Faceless circular head (đầu tròn không cần mặt)
- Neck joint capsule (cổ có khớp cổ)
- Uniform stadium/capsule segments rounded at both ends for torso & limbs (mỗi khung là 1 khung dài đều nhau tròn 2 đầu)
- Circular palm hand with a short wrist connector stem (lòng bàn tay hình tròn + 1 đoạn ngắn để gắn vào khớp cánh tay)
- Simple shoe foot with a short ankle connector stem (bàn chân dạng đôi giày + 1 đoạn ngắn để gắn vào khớp chân)
"""
import os
import json
import urllib.request

MUSE_BASE = "http://127.0.0.1:3456"
LAYOUT_1X1 = "/Users/dochung/Desktop/card_g/layout_guide/layout_guide_1x1.png"

STICKER_DIR = "/Users/dochung/Desktop/card_g/assets/sticker_hero"
os.makedirs(f"{STICKER_DIR}/reference", exist_ok=True)
os.makedirs(f"{STICKER_DIR}/raw", exist_ok=True)


def post_json(url, payload, timeout=420):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


print("=== 1. Creating New Thread on Muse Local Server ===")
res_thread = post_json(f"{MUSE_BASE}/v1/thread", {"new_thread": True})
print("New Thread Response:", json.dumps(res_thread, ensure_ascii=False))

# Step 2: Generate Minimalist Stickman Reference Sheet
ref_path = f"{STICKER_DIR}/reference/sticker_reference_raw.png"
prompt_ref = (
    "Single 2D game character sprite of a minimalist geometric stickman figure (nhân vật người que đơn giản) "
    "standing in a side-3/4 view facing right, centered on a pure solid flat magenta background (#FF00FF). "
    "Strict geometric construction: "
    "(1) HEAD: a completely smooth faceless royal-blue circle (#2563EB) with a clean black outline and subtle 2D cel-shading — NO eyes, NO mouth, NO face, NO helmet, NO headband. "
    "(2) NECK: a short vertical rounded-end capsule joint connecting the head to the torso. "
    "(3) TORSO & LIMBS: every body segment (torso, upper arm, forearm, thigh, shin) is a simple uniform-width straight capsule/pill bar rounded semi-circular at both ends (khung dài đều nhau tròn 2 đầu), royal-blue fill (#2563EB) with bold black outline. "
    "(4) HANDS: each hand is a simple circular palm with a short narrow rounded wrist stem attaching it to the forearm. "
    "(5) FEET: each foot is a simple smooth stylized shoe shape facing right with a short ankle stem attaching it to the shin. "
    "Zero text, zero labels, zero borders, zero square frames, pure flat #FF00FF background."
)
print("=== 2. Generating Minimalist Faceless Stickman Reference ===")
res_ref = post_json(
    f"{MUSE_BASE}/generate-image",
    {
        "prompt": prompt_ref,
        "reference_images": [LAYOUT_1X1],
        "save_path": ref_path,
    },
)
print("Saved Stickman Reference ->", res_ref.get("saved_path"))

# Step 3: Generate Separated Geometric Stickman Parts Sheet on pure #FF00FF (NO internal grid lines!)
parts_raw_path = f"{STICKER_DIR}/raw/sticker_parts_simple_raw.png"
prompt_parts = (
    "2D game skeletal cutout body-part kit of a minimalist royal-blue geometric stickman (#2563EB fill, bold black outline, subtle 2D cel-shading) "
    "arranged as 6 completely separated individual parts floating on a pure solid flat magenta background (#FF00FF) with wide #FF00FF empty space between every part. "
    "DO NOT draw any grid lines, dividing lines, boxes, or text labels. "
    "Arrange into 2 clean columns on pure #FF00FF: "
    "- LEFT COLUMN (top to bottom, 3 separated shapes): "
    "  (1) Top-left: HEAD — a single smooth faceless royal-blue circle (NO eyes, NO face, completely blank smooth sphere with black outline). "
    "  (2) Middle-left: NECK — a short vertical royal-blue pill/capsule shape rounded at both ends (khớp cổ ngắn tròn 2 đầu). "
    "  (3) Bottom-left: TORSO — a vertical royal-blue stadium/capsule bar of uniform width rounded semi-circular at both top and bottom ends. "
    "- RIGHT COLUMN (top to bottom, 3 separated shapes): "
    "  (4) Top-right: LIMB SEGMENT — a straight vertical royal-blue capsule/pill bar of strictly uniform width from top to bottom with smooth semi-circular rounded ends at both top and bottom (1 khung dài đều nhau tròn 2 đầu). "
    "  (5) Middle-right: HAND — a simple royal-blue circular palm with a short narrow rounded wrist connector stem protruding straight up from the top of the circle (lòng bàn tay hình tròn có thêm 1 đoạn ngắn ở cổ tay để gắn vào khớp cánh tay). "
    "  (6) Bottom-right: FOOT — a simple stylized royal-blue shoe profile facing right with a short vertical rounded ankle connector stem protruding straight up from the top of the shoe (bàn chân dạng đôi giày có thêm 1 đoạn ngắn ở cổ chân để gắn vào khớp chân). "
    "Every single shape must be 100% separated by wide flat #FF00FF magenta gaps, zero touching, zero grid lines, zero text."
)
print("=== 3. Generating Separated Geometric Stickman Parts Sheet ===")
res_parts = post_json(
    f"{MUSE_BASE}/generate-image",
    {
        "prompt": prompt_parts,
        "reference_images": [LAYOUT_1X1, ref_path],
        "save_path": parts_raw_path,
    },
)
print("Saved Stickman Parts Sheet ->", res_parts.get("saved_path"))
