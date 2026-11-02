---
name: card-g-hero-rig-builder
description: Quy trình chuẩn tạo Tướng Stickman / Sticker Basic 4 màu đội (Xanh Dương, Đỏ, Xanh Lá, Vàng Cam) dùng chung cho toàn bộ thẻ bài kết hợp Hệ thống Vũ Khí riêng cho từng thẻ bài (có 2 vị trí cầm Grip 1 & Grip 2, hỗ trợ cầm nhiều vũ khí, hiệu ứng animation bao quanh vũ khí cho bậc cao, ảnh preview thẻ bài dạng ngang vẽ chéo cho vũ khí dài) và HTML Editor lưu thẳng ra Godot 4 (.tscn).
---

# Quy Trình Tạo Tướng Stickman 4 Màu Đội + Vũ Khí Theo Thẻ Bài (`card-g-hero-rig-builder`)

Skill này định nghĩa kiến trúc tối ưu hóa tài nguyên và token cho dự án **`card_g` (Arcana Five: Huyết Bài Ngũ Hành)**:
- **Giữ nguyên thư mục `/Users/dochung/Desktop/card_g/assets/heroes/` cũ tạm thời.**
- **1 Tướng Cơ Bản Duy Nhất (`assets/sticker_hero/`):** Toàn bộ 80 thẻ tướng dùng chung **1 bộ Tướng Stickman / Chiến Binh Người Que 2D cách điệu** (kiểu *Stick War / Supreme Duelist*: đầu tròn, thân ngực, hông, bắp tay, cẳng tay, bàn tay nắm, đùi, ống chân, bàn chân rõ khớp), xuất sẵn **4 màu ứng với 4 Đội**:
  1. **Đội 1 — Xanh Dương (`blue` / `#3B82F6`)**
  2. **Đội 2 — Đỏ (`red` / `#EF4444`)**
  3. **Đội 3 — Xanh Lá (`green` / `#22C55E`)**
  4. **Đội 4 — Vàng Cam (`amber` / `#F59E0B`)**
- **Mỗi Thẻ Bài (`C01` – `C80`) Tương Ứng Với 1 Bộ Vũ Khí Riêng (`assets/weapons/wXXX_<slug>/`):**
  - **Quy tắc hiệu ứng Animation của Vũ Khí theo Độ Hiếm (`N` / `R` vs `S` / `SSR`):**
    - **Cấp `N` (Common) & Cấp `R` (Rare):** **KHÔNG có hiệu ứng animation của vũ khí** (không tạo/không chạy spritesheet `2x2` cho vũ khí; chỉ hiển thị **1 ảnh tĩnh duy nhất** là `weapon_main.png` / `weapon_anim_0.png`, `aura_default: false`). Nếu là vũ khí tầm xa (cung, nỏ, súng...) **không vẽ đạn/mũi tên**.
    - **Cấp `S` (Epic) & Cấp `SSR` (Legendary):** **CÓ hiệu ứng spritesheet animation 4 frame (`2x2`) của chính vũ khí đó (`weapon_anim_0..3.png` / `weapon_aura`, `aura_default: true`, như `W018`)** kèm hiệu ứng kỹ năng hoành tráng.
  - **Thứ Tự Flow Bắt Buộc Khi Tạo Vũ Khí:**
    1. **Bước 1 — Vẽ Ảnh Ref của Vũ Khí Trước (`reference/wXXX_ref_raw.png`):** Dùng `layout_guide_1x1.png` vẽ nguyên cây vũ khí trên nền `#FF00FF` (đặt chéo nếu là vũ khí dài, không vẽ đạn nếu là vũ khí tầm xa), tách nền sạch và trim sát (`0px` margin) thành `weapon_main.png` (và `weapon_anim_0.png` tĩnh).
    2. **Bước 2 — Tạo Ảnh Spritesheet Animation của Vũ Khí *(CHỈ ÁP DỤNG CHO CẤP `S` VÀ `SSR`, BỎ QUA Ở CẤP `N` VÀ `R`)* (`raw/wXXX_weapon_anim_2x2_raw.png`):** Truyền `reference_images: [wXXX_ref_raw.png, layout_guide_2x2.png]` để vẽ lưới `2x2` (4 frame loop `weapon_anim_0..3.png`) của chính vũ khí trong ảnh Ref với hiệu ứng năng lượng/lửa/sét chuyển động dọc theo lưỡi vũ khí trên nền `#FF00FF`.
    3. **Bước Cuối — Tạo Ảnh Bìa của Card (`card/wXXX_card_preview.png` `884x632` RGB & `.webp` `354x253` RGB):** Truyền `reference_images` (`[wXXX_ref_raw.png]` cho cấp `N`/`R`, hoặc `[wXXX_ref_raw.png, wXXX_weapon_anim_2x2_raw.png]` cho cấp `S`/`SSR`) để tạo ảnh bìa ngang đặt chéo của vũ khí **có nền bối cảnh dark-fantasy đầy đủ (`mode="RGB"`, 100% không trong suốt)**, đồng nhất 100% thiết kế với ảnh Ref.
  - **Ảnh Preview Thẻ Bài (`wXXX_card_preview.png` `884x632` & `.webp` `354x253`):**
    - Đổi từ chân dung tướng sang **ảnh chữ nhật ngang của chính Vũ Khí đó** (không ghép sẵn khung thẻ).
    - **Nếu vũ khí dài (kiếm, đao, thương, trượng, cung...):** Bắt buộc **vẽ đặt chéo (diagonal composition)** trong khung ngang `884x632` để tối ưu diện tích hiển thị.
  - **Ảnh Vũ Khí Thật (`weapon_main.png`, `weapon_offhand.png` nếu có):**
    - Phải vẽ **đầy đủ 100% nguyên cây vũ khí** trên nền `#FF00FF`, tách nền sạch (`edge_clip = 0px`).
  - **2 Vị Trí Cầm (`Grip 1` & `Grip 2`) + Hỗ Trợ Nhiều Vũ Khí (`Weapon_Front` & `Weapon_Back`):**
    - Mỗi vũ khí có **2 điểm mốc cầm**:
      - **`Grip 1` (`grip1_x, grip1_y`):** Vị trí tay chính (`Hand_L` / Tay Front) nắm vũ khí (đồng thời là tâm xoay `pivot` của vũ khí).
      - **`Grip 2` (`grip2_x, grip2_y`):** Vị trí cầm thứ 2 trên cán/thân vũ khí (dùng cho vũ khí cầm 2 tay hoặc đổi vị trí nắm; trên HTML Editor có nút **Snap Tay Phụ vào Grip 2**).
    - Nhân vật Stickman hỗ trợ gắn vũ khí ở cả **Tay Front (`Weapon_Front` gắn vào `Hand_L`)** và **Tay Back (`Weapon_Back` gắn vào `Hand_R`)** để hỗ trợ tướng cầm 2 vũ khí (Song Đao, Kiếm + Khiên...).

---

## 1. Cấu Trúc Thư Mục Chuẩn

1. **Thư mục Tướng Stickman Cơ Bản (Dùng chung cho mọi thẻ tướng):**
   - `/Users/dochung/Desktop/card_g/assets/sticker_hero/`
     - `reference/` (`sticker_reference_raw.png`, `sticker_reference_clean.png`)
     - `godot/parts/base/` (14 part gốc: `head.png`, `chest.png`, `hip.png`, `arm_upper_front.png`, `arm_lower_front.png`, `hand_front.png`, `arm_upper_back.png`, `arm_lower_back.png`, `hand_back.png`, `leg_thigh_front.png`, `leg_shin_front.png`, `foot_front.png`, `leg_thigh_back.png`, `leg_shin_back.png`, `foot_back.png`)
     - `godot/parts/team_blue/`, `team_red/`, `team_green/`, `team_amber/` (4 bộ part đã nhuộm chuẩn 4 màu đội với shading bóng sáng 2D)
     - `godot/sticker_hero_base.tscn` & `sticker_hero_base.gd`
     - `qc_previews/sticker_parts_4teams_audit.png`
2. **Thư mục Vũ Khí Theo Từng Thẻ Bài (`w001` – `w080`):**
   - `/Users/dochung/Desktop/card_g/assets/weapons/<wXXX_slug>/`
     - `card/<wXXX>_card_preview.png` (`884x632` — ảnh ngang của vũ khí, vẽ đặt chéo nếu vũ khí dài)
     - `raw/` (ảnh raw nền `#FF00FF` từ Muse AI, không dính khung vuông)
     - `parts/` (`weapon_main.png`, `weapon_offhand.png` nếu có, `weapon_aura.png`, `fx_slash.png`, `fx_slash_heavy.png`, `fx_spark.png`, `fx_dust.png`)
     - `godot/<cXXX_slug>.tscn` & `<cXXX_slug>.gd` (Scene Godot 4 kết hợp Stickman 4 màu + Vũ khí của thẻ đó + 6 animation `idle`, `walk`, `attack`, `cast`, `hurt`, `death`)
     - `qc_previews/<wXXX>_weapon_and_actions_audit.png`
3. **File HTML Editor Tổng Hợp & Theo Từng Tướng:**
   - `/Users/dochung/Desktop/card_g/assets/sticker_weapon_editor.html` (và `/Users/dochung/Desktop/card_g/assets/weapons/<wXXX_slug>/<wXXX>_editor.html`):
     - Chọn **Màu Đội (Xanh Dương / Đỏ / Xanh Lá / Vàng Cam)**.
     - Chọn **Thẻ Bài / Vũ Khí**, chỉnh tọa độ **2 vị trí cầm (`Grip 1` & `Grip 2`)**, bật/tắt **Vũ khí phụ (`Weapon_Back`)** & **Hiệu ứng bao quanh vũ khí (`WeaponAura`)**.
     - Chọn từng action trong **6 Action (`idle`, `walk`, `attack`, `cast`, `hurt`, `death`)** trên thanh topbar để preview trực tiếp trên Canvas chính.
     - Kéo chỉnh khớp xương & bấm **`Save to .tscn`** lưu thẳng vào file `.tscn` của từng tướng!

---

## 2. Quy Trình One-Shot Tối Ưu 90% Token (`tools/forge_weapon.py` + `assets/weapons/configs/wXXX.json`)

Để giảm số lượt gọi (turns) từ **70–95 turns xuống còn 3–4 turns/vũ khí** (tiết kiệm ~85–90% token cho mỗi lần triển khai vũ khí và spine rig):

1. **TUYỆT ĐỐI KHÔNG viết lại script Python dài 500–650 dòng cho từng vũ khí (`build_wXXX_system.py`):**
   - Toàn bộ logic xử lý ảnh Muse, tách nền `#FF00FF`, lọc thành phần lớn nhất (không vẽ đạn rời), `0px` tight crop, lắp ráp bộ xương 17 `Bone2D` (`0px` joint gap), 6 action pose theo Archetype, xuất bảng QC, xuất Godot 4 `.tscn`/`.gd` và cập nhật HTML Editor đã được đóng gói vào CLI chuẩn: `/Users/dochung/Desktop/card_g/tools/forge_weapon.py`.
2. **Tách Dữ Liệu Base64 Ra `assets/weapons_data.js` (`~39 KB` cho mỗi HTML Editor):**
   - Toàn bộ dữ liệu Base64 của 4 đội Stickman (`window.TEAM_PART_B64`) và danh sách gói vũ khí (`window.WEAPON_REGISTRY`, `window.WEAPON_ORDER`) được lưu tự động tại `/Users/dochung/Desktop/card_g/assets/weapons_data.js` và nạp qua `<script src="weapons_data.js"></script>`.
   - **CẤM TUYỆT ĐỐI** dùng `read_file` đọc `assets/weapons_data.js` vào ngữ cảnh AI để tránh tràn context window.
3. **3 Bước Duy Nhất Khi Triển Khai Vũ Khí Mới (`W004` – `W080`):**
   - **Bước 1:** Tạo file cấu hình JSON nhỏ gọn (~25 dòng) tại `/Users/dochung/Desktop/card_g/assets/weapons/configs/wXXX.json`:
     ```json
     {
       "id": "w004",
       "slug": "w004_<slug>",
       "tier": "N",
       "name": "W004 — <Tên Vũ Khí> (C04 · <Hệ> · <Vai Trò> · Cấp N)",
       "tscn_name": "c004_<slug>.tscn",
       "node_name": "C004Hero",
       "archetype": "melee_cleaver",
       "target_size": [216, 166],
       "grip1_norm": [0.16, 0.80],
       "grip2_norm": [0.30, 0.66],
       "rest_rot": -10.0,
       "flip_horizontal": false,
       "prompt_ref": "<Prompt Bước 1 vẽ vũ khí trên nền #FF00FF với layout_guide_1x1.png>",
       "prompt_card": "<Prompt Bước Cuối vẽ ảnh bìa thẻ bài 884x632 Opaque RGB>"
     }
     ```
     *(Nếu `"tier"` là `"S"` hoặc `"SSR"`, thêm trường `"prompt_anim_2x2"` để tự động chạy Bước 2 tạo lưới `2x2` animation 4 frame cho vũ khí).*
   - **Bước 2:** Ghi lệnh vào `/Users/dochung/Desktop/card_g/script.sh` và chạy `bash /Users/dochung/Desktop/card_g/script.sh`:
     ```bash
     python3 /Users/dochung/Desktop/card_g/tools/forge_weapon.py --config /Users/dochung/Desktop/card_g/assets/weapons/configs/wXXX.json
     ```
   - **Bước 3:** Dùng `read_file` kiểm tra 2 bảng QC (`wXXX_weapon_and_aura_audit.png` & `wXXX_sticker_all_6_actions_overview.png`) và báo cáo kết quả cho người dùng.
