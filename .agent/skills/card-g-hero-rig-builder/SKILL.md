---
name: card-g-hero-rig-builder
description: "End-to-end workflow for creating 2D Skeletal Cutout Heroes in the card_g project using Muse Local API, shared layout guides, 18-Bone Spine Skeleton2D hierarchy (Shoulder -> Elbow -> Wrist -> Hand & Hip -> Knee -> Ankle -> Foot), soft-opacity translucent VFX PNGs, native Godot 4 (.tscn) scene generation, and an interactive single-action-preview HTML Rig & Animation Editor (<hero_id>_editor.html) with direct Save to .tscn."
---

# Card G Hero Rig Builder (`card-g-hero-rig-builder`)

Use this skill whenever creating, rigging, or updating any Hero (`C001` through `C110`) in `/Users/dochung/Desktop/card_g`.

---

## Core Mandates

1. **Execute All Terminal Commands via `/Users/dochung/Desktop/card_g/script.sh`:**
   - Never run ad-hoc shell/python/curl/git commands directly in the terminal.
   - Always write the commands to `/Users/dochung/Desktop/card_g/script.sh` (keeping `#!/usr/bin/env bash` and `set -euo pipefail` at the top) and run `bash /Users/dochung/Desktop/card_g/script.sh`.
2. **Reuse Shared Layout Guides (`/Users/dochung/Desktop/card_g/layout_guide/`):**
   - Always pass existing layout guides (`layout_guide_1x1.png`, `layout_guide_2x2.png`, `layout_guide_2x3.png`, `layout_guide_3x2.png`, `layout_guide_3x3.png`, `layout_guide_3x4.png`, `layout_guide_4x4.png`) in `reference_images` when calling Muse Local API (`http://127.0.0.1:3456/generate-image` or `/edit-image`).
   - Only generate a new layout guide if a required grid dimension does not yet exist in `/Users/dochung/Desktop/card_g/layout_guide/`, and save it directly there.
3. **Zero `.gif` Files — Mandatory `<hero_id>_editor.html` with Single-Action Top Selector Bar:**
   - Never generate `.gif` files for heroes.
   - Every hero must include `/Users/dochung/Desktop/card_g/assets/heroes/<hero_dir>/<hero_id>_editor.html` featuring a clean top bar of 6 Action selector buttons (`IDLE`, `WALK`, `ATTACK`, `CAST`, `HURT`, `DEATH`): **whichever action is selected is previewed directly on the main Canvas** (do not render mini-canvases of unselected actions in the top bar).
   - Provide a **`Save to .tscn`** button that writes directly to `assets/heroes/<hero_dir>/godot/<hero_id>.tscn` via `tools/tscn_editor_server.py` (`http://127.0.0.1:3457/save-tscn`) or the browser's File System Access API.

---

## 8-Step Hero Creation & 18-Bone Rigging Pipeline

### Step 1: Lookup Hero Spec & Fixed Rarity Visual Tier in `GAME_DESIGN.md`

Each hero has ONE fixed rarity (`N`, `R`, `S`, or `SSR`), an Element (`Kim`, `Mộc`, `Thủy`, `Hỏa`, `Thổ`, `Ngũ Hành`), and a Combat Role (`Vật Lý`, `Phép`, `Chí Mạng`). Scale visual complexity strictly by the hero's fixed rarity:

- **Rarity `N` (Common):** Grounded foot soldier / recruit. Simple weathered iron/leather armor, plain steel weapon, tattered cloth, zero magical glow.
- **Rarity `R` (Rare):** Veteran knight / specialist. Well-crafted engraved armor, distinct silhouette, subtle elemental accent on weapon edge.
- **Rarity `S` (Epic):** Commander / archmage. Ornate layered armor with gold/obsidian trim, flowing cape, clear elemental energy radiating from weapon.
- **Rarity `SSR` (Legendary):** Mythic warlord / sovereign. Masterpiece multi-layered divine/demonic armor, floating elemental/runic aura, iconic legendary weapon.

### Step 2: Generate Master Reference Character (`1x1`, `3/4 Facing RIGHT`, `#FF00FF`)

1. Call `POST http://127.0.0.1:3456/generate-image` with `reference_images: ["/Users/dochung/Desktop/card_g/layout_guide/layout_guide_1x1.png"]`.
2. Require a full-body standing pose at `3/4 angle facing RIGHT`, solid flat `#FF00FF` magenta background, occupying 65%–70% of the canvas with open limb separation so all joints are clearly visible.
3. Post-process with `generate2dsprite.py process --rows 1 --cols 1 --align feet --scale-strategy preserve --strict-qc` to save `assets/heroes/<hero_dir>/reference/<hero_id>_reference_clean.png`.

### Step 3: Generate Horizontal Hero Portrait Preview Only (`<hero_id>_portrait_preview.png` & `.webp` — DO NOT Bake Card Frame)

- **DO NOT** generate a pre-assembled card image (`<hero_id>_card_complete_<rarity>.png`) with the card frame, text, or stats baked in — the card frame template, name, skill text, icons, and stats are assembled dynamically in game code.
- **ONLY** generate and save the horizontal hero portrait preview that fits the `art_window` slot in `assets/cards/card-template-layout.json`:
  - Master PNG (`884x632`): `assets/heroes/<hero_dir>/card/<hero_id>_portrait_preview.png`
  - Mobile WebP (`354x253`): `assets/mobile/heroes/<hero_dir>/card/<hero_id>_portrait_preview.webp`

### Step 4: Generate & Split 18 Isolated Body Cutout Parts (`godot/parts/*.png`)

Generate raw cutout part sheets on `#FF00FF` via Muse Local API (using `layout_guide_3x4.png` / `layout_guide_2x2.png` + `<hero_id>_reference_clean.png`) and split into **18 isolated body parts** for the **18-Bone Spine Hierarchy (`Skeleton2D`)**:

1. **Torso & Head (5 parts):**
   - `hip_kilt.png` (`Hip` root bone at pelvis center $\rightarrow$ waist)
   - `chest.png` (`Chest` spine bone from waist $\rightarrow$ upper-chest clavicle hub; **must be strictly armless/sleeveless** with zero overlap with upper arms)
   - `head.png` (`Head` bone from neck base $\rightarrow$ helmet/head top)
   - `cloak.png` (`Cloak` bone from collar $\rightarrow$ cloak hem)
   - `pauldron.png` (`Pauldron` bone at front shoulder joint)
2. **Front / Closer Right Arm (3 full bone segments: Shoulder $\rightarrow$ Elbow $\rightarrow$ Wrist $\rightarrow$ Fingers):**
   - `arm_upper_front.png` (`UpperArm_L`: Shoulder $\rightarrow$ Elbow)
   - `arm_lower_front.png` (`Forearm_L`: Elbow $\rightarrow$ Wrist bracer)
   - `hand_front.png` (`Hand_L`: Wrist $\rightarrow$ Fingers; **anatomical check:** must show the dorsal back of the hand / outer bracer with fingers naturally curved and palm facing inward toward the body — never an open palm facing the camera)
3. **Back / Farther Left Weapon Arm (4 full bone segments: Shoulder $\rightarrow$ Elbow $\rightarrow$ Wrist $\rightarrow$ Fist $\rightarrow$ Weapon Tip):**
   - `arm_upper_back.png` (`UpperArm_R`: Shoulder $\rightarrow$ Elbow)
   - `arm_lower_back.png` (`Forearm_R`: Elbow $\rightarrow$ Wrist bracer)
   - `hand_back.png` (`Hand_R`: Wrist $\rightarrow$ Closed weapon-gripping fist with accurate thumb/knuckle wrapping)
   - `sword.png` (or hero's weapon, `Sword`: Hilt grip $\rightarrow$ Blade tip)
4. **Front / Closer Right Leg (3 full bone segments: Hip $\rightarrow$ Knee $\rightarrow$ Ankle $\rightarrow$ Toe):**
   - `leg_thigh_front.png` (`Thigh_R`: Hip $\rightarrow$ Knee)
   - `leg_shin_front.png` (`Shin_R`: Knee cap + shin greave $\rightarrow$ Ankle)
   - `foot_front.png` (`Foot_R`: Ankle $\rightarrow$ Boot toe planted in `3/4` front-right perspective)
5. **Back / Farther Left Leg (3 full bone segments: Hip $\rightarrow$ Knee $\rightarrow$ Ankle $\rightarrow$ Toe):**
   - `leg_thigh_back.png` (`Thigh_L`: Hip $\rightarrow$ Knee)
   - `leg_shin_back.png` (`Shin_L`: Knee + shin greave $\rightarrow$ Ankle)
   - `foot_back.png` (`Foot_L`: Ankle $\rightarrow$ Boot toe stepping forward-right in `3/4` perspective; must be distinct from `foot_front.png`)

### Step 5: Generate 4 Lightweight Soft-Opacity VFX PNGs (`fx_slash`, `fx_slash_heavy`, `fx_spark`, `fx_dust`)

1. Generate a `2x2` VFX sheet on `#FF00FF` using `layout_guide_2x2.png` with delicate, wispy, airy motion lines appropriate for the hero's rarity.
2. **Mandatory Soft-Opacity Unmixing (see `tools/extract_soft_vfx.py`):**
   - Do **not** use opaque chroma-key thresholds that leave dark borders or heavy solid shapes.
   - Unmix continuous sub-pixel alpha from `#FF00FF` (`alpha_raw = 1.0 - clip((min(R,B) - G) / 255.0, 0, 1)`), un-premultiply foreground RGB, feather cell boundaries, and cap alpha (`max_alpha_scale ~ 0.62–0.84`) so each VFX PNG has smooth, lightweight translucent opacity (`mean_alpha ~ 17%–35%`, `edge_clip = 0px`).

### Step 6: Mandatory 1:1 Reassembly & 18-Bone Spine Skeleton Verification (`qc_previews/`)

Before creating animations, run the rig builder (modeled on `tools/build_c001_rig_and_editor.py`) to generate and visually inspect via `read_file`:

1. `qc_previews/<hero_id>_parts_catalog_audit.png`: Grid showing all 18 body parts + 4 VFX parts, their pixel dimensions, red pivot dots, and `edge_clip: 0px`.
2. `qc_previews/<hero_id>_reassembly_verification.png`: 3-panel side-by-side comparison:
   - Panel 1: Original Reference character.
   - Panel 2: 18-part Reassembled Rest Pose (`edge_clip = 0px`, seamless wrist/ankle/shoulder/hip joints).
   - Panel 3: Full 18-Bone Spine Skeleton diagram showing tapered diamond bones from joint head `(wx, wy)` to bone tail `(tx, ty)` for every upper arm, forearm, hand, weapon, thigh, shin, foot, chest, and head.
3. `qc_previews/<hero_id>_all_6_actions_overview.png`: All 6 actions (`idle`, `walk`, `attack`, `cast`, `hurt`, `death`) verified with `total_edge_clips = 0px`.

### Step 7: Generate Native Godot 4 Scene (`<hero_id>.tscn` & `<hero_id>.gd`) + Mobile `.webp`

1. Write `assets/heroes/<hero_dir>/godot/<hero_id>.tscn` with:
   - `Skeleton2D` containing all 18 `Bone2D` nodes (`auto_calculate_length_and_angle = false`, explicit `length` and `bone_angle` matching each bone's tip).
   - `VFXLayer` containing the 4 soft-opacity VFX `Sprite2D` nodes.
   - `AnimationPlayer` containing `idle` (loop), `walk` (loop), `attack` (one-shot), `cast` (one-shot), `hurt` (one-shot), and `death` (one-shot).
2. Export mobile-optimized `.webp` cutouts to `assets/mobile/heroes/<hero_dir>/parts/`.

### Step 8: Generate Interactive Single-Action-Preview HTML Editor (`<hero_id>_editor.html`)

Generate `assets/heroes/<hero_dir>/<hero_id>_editor.html` (modeled on `tools/build_c001_rig_and_editor.py`):

- **Top Action Selector Bar:** Clean horizontal buttons (`▶ IDLE`, `▶ WALK`, `▶ ATTACK`, `▶ CAST`, `▶ HURT`, `▶ DEATH`). Clicking an action button selects and previews **only that action** on the main `512x512` Canvas (no mini-canvas strip).
- **Full 18-Bone Interactive Editing:** Click any joint on the Canvas or in the left sidebar (`Hip`, `Chest`, `Head`, `Cloak`, `Pauldron`, `UpperArm_L`, `Forearm_L`, `Hand_L`, `UpperArm_R`, `Forearm_R`, `Hand_R`, `Sword`, `Thigh_R`, `Shin_R`, `Foot_R`, `Thigh_L`, `Shin_L`, `Foot_L`) to drag/adjust keyframe `rot`, `dx`, `dy`, `Rest Pose`, `Sprite Offset`, `z_index`, or `VFXLayer` placement.
- **Direct `.tscn` Save:** Clicking **`💾 Save to .tscn`** regenerates the complete Godot 4 `.tscn` file and saves it directly to `assets/heroes/<hero_dir>/godot/<hero_id>.tscn` via `http://127.0.0.1:3457/save-tscn` (`tools/tscn_editor_server.py`) or File System Access API.

---

## Reference Scripts in Project (`tools/`)

- [`tools/split_hands_and_feet_joints.py`](file:///Users/dochung/Desktop/card_g/tools/split_hands_and_feet_joints.py): Splits forearm/hand wrist joints and shin/foot ankle joints into 18 isolated cutout parts with `edge_clip = 0px`.
- [`tools/generate_light_vfx.py`](file:///Users/dochung/Desktop/card_g/tools/generate_light_vfx.py): Calls Muse Local API with `layout_guide_2x2.png` to generate lightweight Rarity-appropriate VFX sheets.
- [`tools/extract_soft_vfx.py`](file:///Users/dochung/Desktop/card_g/tools/extract_soft_vfx.py): Unmixes `#FF00FF` into smooth, semi-transparent soft-opacity VFX PNGs.
- [`tools/build_c001_rig_and_editor.py`](file:///Users/dochung/Desktop/card_g/tools/build_c001_rig_and_editor.py): Reference 18-bone forward-kinematics renderer, QC board generator, Godot 4 `.tscn` exporter, and `<hero_id>_editor.html` builder.
- [`tools/tscn_editor_server.py`](file:///Users/dochung/Desktop/card_g/tools/tscn_editor_server.py): Local HTTP server on `127.0.0.1:3457` that writes changes from `<hero_id>_editor.html` directly to `.tscn`.
