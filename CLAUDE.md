# Project Rules & Agent Instructions (`card_g`)

Mọi AI Agent (Antigravity, Gemini, Claude, Cursor, Codex, OpenCode...) khi làm việc trong dự án này **BẮT BUỘC** phải tuân thủ nghiêm ngặt 2 quy tắc cốt lõi dưới đây trong mọi bước thực thi:

---

## QUY TẮC 1: Thực thi lệnh Terminal thông qua `script.sh` (BẮT BUỘC 100%)

1. **KHÔNG BAO GIỜ** chạy trực tiếp các câu lệnh rời rạc trên terminal.
2. Khi cần thực thi bất kỳ lệnh terminal / shell / python / curl / build / test nào:
   - **Bước 1:** Dùng công cụ ghi/sửa file (`write_file` / `edit_file`) để cập nhật nội dung lệnh cần chạy vào file `/Users/dochung/Desktop/card_g/script.sh`.
   - **Bước 2:** Chạy duy nhất lệnh thực thi file script đó trên terminal:
     ```bash
     bash /Users/dochung/Desktop/card_g/script.sh
     ```
     (hoặc `bash script.sh` khi working directory đang ở `/Users/dochung/Desktop/card_g`).
3. Luôn giữ `#!/usr/bin/env bash` và `set -euo pipefail` ở đầu file `script.sh` để đảm bảo bắt lỗi chính xác.

---

## QUY TẮC 2: Tạo Ảnh, Sprites, Maps & Game Assets bằng Muse Local API + Skill `agent-sprite-forge`

Khi cần generate ảnh, spritesheet, nhân vật, hiệu ứng (FX/projectile/impact), props, tilemaps, 2D maps hoặc chuyển đổi video sang sprite:
- **TUYỆT ĐỐI KHÔNG** vẽ giả lập bằng code (không dùng PIL drawing, HTML5 Canvas, SVG, CSS hay hình khối placeholder để thay thế asset).
- **BẮT BUỘC** sử dụng **Muse AI Local Server** kết hợp với quy trình và bộ script hậu xử lý của skill **`agent-sprite-forge`** (`https://github.com/0x0funky/agent-sprite-forge`).

### 2.1. Kết nối và sử dụng Muse AI Local Server (`/Users/dochung/Desktop/muse-local-api`)

1. **Kiểm tra và khởi chạy server (nếu chưa chạy)** — đặt trong `script.sh` và chạy `bash script.sh`:
   ```bash
   bash /Users/dochung/Desktop/muse-local-api/start.sh --daemon
   ```
2. **Thông tin kết nối API:**
   - **Base URL:** `http://127.0.0.1:3456/v1`
   - **Health Check:** `GET http://127.0.0.1:3456/health`
   - **Model ID:** `"muse-spark"`
   - **API Key:** `"muse-local"` (không bắt buộc xác thực key ở local)
   - **Chat Completions Endpoint:** `POST http://127.0.0.1:3456/v1/chat/completions` (hỗ trợ chuẩn OpenAI `messages`, `stream: false` hoặc `stream: true` SSE)
   - **Simple Chat Endpoint:** `POST http://127.0.0.1:3456/chat` với body `{"prompt": "...", "system": "..."}` -> trả về `{"reply": "..."}`
   - **Image Generation Endpoint (thay thế `image_gen`):**
     `POST http://127.0.0.1:3456/generate-image` (hoặc `POST http://127.0.0.1:3456/v1/images/generations`)
     ```json
     {
       "prompt": "<prompt chi tiết theo chuẩn agent-sprite-forge>",
       "reference_images": ["/duong/dan/anh_ref_neu_co.png"],
       "save_path": "/duong/dan/luu/raw-sheet.png"
     }
     ```
     *(Hoặc truyền `"output_dir"` và `"filename_prefix"`)*
   - **Image Edit Endpoint (thay thế `image_edit`):**
     `POST http://127.0.0.1:3456/edit-image` (hoặc `POST http://127.0.0.1:3456/v1/images/edits`)
     ```json
     {
       "image": "/duong/dan/anh_goc.png",
       "reference_images": ["/duong/dan/anh_ref_phu.png"],
       "prompt": "<hướng dẫn chỉnh sửa / biến thể>",
       "strength": 0.7,
       "save_path": "/duong/dan/luu/edited.png"
     }
     ```
   - **Video Generation Endpoint (thay thế `image_to_video` cho `video2dsprite`):**
     `POST http://127.0.0.1:3456/generate-video` (hoặc `POST http://127.0.0.1:3456/v1/videos/generations`)
     ```json
     {
       "image": "/duong/dan/base-still-magenta.png",
       "prompt": "<prompt chuyển động tại chỗ trên nền #FF00FF, khoá camera>",
       "duration": 6,
       "save_path": "/duong/dan/luu/motion.mp4"
     }
     ```
   - **Lưu ý:** Nếu cần thêm thông tin chi tiết về server, hãy đọc file `/Users/dochung/Desktop/muse-local-api/README.md`.

### 2.2. Tuân thủ nghiêm ngặt quy trình Skill `agent-sprite-forge`

Trước khi tạo bất kỳ asset 2D nào, hãy đọc tài liệu skill tương ứng đã được cài đặt sẵn trên máy:
- **Skill chuyên biệt tạo Tướng Xương 2D (18 `Bone2D` + Soft-Opacity VFX + HTML Editor) của dự án `card_g`:** `/Users/dochung/Desktop/card_g/.agent/skills/card-g-hero-rig-builder/SKILL.md` (hoặc `/Users/dochung/.gemini/config/skills/card-g-hero-rig-builder/SKILL.md`)
- **Tổng quan:** `/Users/dochung/.gemini/config/skills/agent-sprite-forge/SKILL.md`
- **Tạo Sprite & Animation (`generate2dsprite`):** `/Users/dochung/.gemini/config/skills/generate2dsprite/SKILL.md`
  - Quy tắc viết prompt: `/Users/dochung/.gemini/config/skills/generate2dsprite/references/prompt-rules.md`
  - Chế độ & bố cục: `/Users/dochung/.gemini/config/skills/generate2dsprite/references/modes.md`
- **Tạo Bản đồ & Prop Pack (`generate2dmap`):** `/Users/dochung/.gemini/config/skills/generate2dmap/SKILL.md`
  - Chiến lược map: `/Users/dochung/.gemini/config/skills/generate2dmap/references/map-strategies.md`
  - Layered map contract: `/Users/dochung/.gemini/config/skills/generate2dmap/references/layered-map-contract.md`
  - Prop pack contract: `/Users/dochung/.gemini/config/skills/generate2dmap/references/prop-pack-contract.md`
- **Chuyển Video thành Sprite (`video2dsprite`):** `/Users/dochung/.gemini/config/skills/video2dsprite/SKILL.md`

#### Các nguyên tắc bắt buộc của `agent-sprite-forge`:
1. **Lập kế hoạch & Viết Prompt thủ công:**
   - Tự xác định `asset_type`, `action`, `view` (`topdown`, `side`, `3/4`), `sheet` (`2x2`, `2x3`, `3x3`, `4x4`), `anchor` (`feet`, `bottom`, `center`), `art_style` (`pixel_art`, `clean_hd`, `retro_pixel`, `project-native`).
   - **Không** dùng dải 1 hàng (`1x4`, `1x6`, `1xN`) khi generate raw sheet cho nhân vật/quái vật (vì dễ lệch tỉ lệ và trôi ngang). Luôn generate theo lưới nhiều hàng (`2x2` cho 4 frame, `2x3` cho 6 frame, `3x3` cho 9 frame, `4x4` cho 16 frame).
   - **Không** gộp nhiều hành động khác nhau (ví dụ idle + run + attack) vào chung 1 raw sheet. Hãy tạo từng raw sheet riêng cho mỗi hành động, dùng `reference_images` trong Muse Local API để giữ đồng nhất nhân vật.
   - Luôn yêu cầu nền đơn sắc độ tương phản cao: **solid magenta `#FF00FF`** (mặc định chuẩn của bộ xử lý `generate2dsprite.py`), nhân vật nằm gọn trong vùng an toàn 60%–70% chính giữa mỗi ô, giữ nguyên tỉ lệ cơ thể và đường chân (`feet`), **không chạm viền ô (no cell-edge clipping)**.
   - **Tái sử dụng Layout Guide dùng chung (`/Users/dochung/Desktop/card_g/layout_guide`):**
     - Các file Layout Guide chuẩn (`layout_guide_1x1.png`, `layout_guide_2x2.png`, `layout_guide_2x3.png`, `layout_guide_3x2.png`, `layout_guide_3x3.png`, `layout_guide_3x4.png`, `layout_guide_4x4.png`) **ĐÃ CÓ SẴN** trong thư mục `/Users/dochung/Desktop/card_g/layout_guide/`.
     - **BẮT BUỘC** dùng trực tiếp các file có sẵn trong `/Users/dochung/Desktop/card_g/layout_guide/` để truyền vào `reference_images` khi gọi Muse API nhằm tiết kiệm thời gian và token. Chỉ chạy `make_layout_guide.py` khi cần thêm một kích thước lưới mới chưa có sẵn, và phải lưu thẳng vào `/Users/dochung/Desktop/card_g/layout_guide/`.

2. **Hậu xử lý (Post-processing) bằng bộ script Python của `agent-sprite-forge` (chạy qua `script.sh`):**
   - **Tách nền Chroma-key, cắt frame, căn chỉnh anchor, kiểm tra QC và xuất PNG trong suốt + GIF:**
     ```bash
     python3 /Users/dochung/.gemini/config/skills/generate2dsprite/scripts/generate2dsprite.py process \
       --input <raw-sheet.png> \
       --target <player|npc|creature|spell|projectile|impact|prop> \
       --mode <idle|walk|run|attack|cast|...> \
       --rows <rows> --cols <cols> \
       --output-dir <out-dir> \
       --cell-size <size> \
       --align <feet|bottom|center> \
       --scale-strategy <preserve|fit> \
       --component-mode <largest|all> \
       --strict-qc
     ```
   - **Tạo Layout Guide / Anchor Sheet:**
     - `/Users/dochung/.gemini/config/skills/generate2dsprite/scripts/make_layout_guide.py`
     - `/Users/dochung/.gemini/config/skills/generate2dsprite/scripts/make_anchor_layout.py`
   - **Xử lý Prop Pack, Tileset & Map Preview (`generate2dmap`):**
     - `/Users/dochung/.gemini/config/skills/generate2dmap/scripts/extract_prop_pack.py`
     - `/Users/dochung/.gemini/config/skills/generate2dmap/scripts/extract_terrain_tiles.py`
     - `/Users/dochung/.gemini/config/skills/generate2dmap/scripts/compose_layered_preview.py`
   - **Xử lý Video sang Sprite (`video2dsprite`):**
     - `/Users/dochung/.gemini/config/skills/video2dsprite/scripts/video2dsprite.py`

3. **Kiểm định chất lượng (QC) & Quy trình Tạo Tướng Stickman 4 Màu + Vũ Khí Theo Thẻ Bài (`.tscn` — Kiến trúc Tối Ưu Token):**
   - **Kiến trúc Nhân Vật Chung (`Sticker / Stickman Base`) + Vũ Khí Riêng Cho Từng Thẻ Bài (`W001` – `W080`):**
     - Thay vì vẽ 80 nhân vật riêng lẻ, toàn bộ các thẻ tướng dùng chung **1 bộ Tướng Stickman / Chiến Binh Người Que 2D (`assets/sticker_hero/`)** gồm 16 bộ phận chuẩn:
       - Đầu tròn trơn không mặt (`head`), khớp cổ (`neck`), thân trên ngực-vai (`chest`), thân dưới bụng-hông (`hip_kilt`).
       - Các đốt tay chân (`arm_upper_front/back`, `arm_lower_front/back`, `leg_thigh_front/back`, `leg_shin_front/back`) mỗi đốt là **1 khung dài đều nhau tròn 2 đầu (capsule)**.
       - Bàn tay (`hand_front/back`) là **hình tròn có thêm 1 đoạn cổ tay ngắn** để gắn vào khớp cẳng tay; bàn chân (`foot_front/back`) vẽ **dạng đôi giày có thêm 1 đoạn cổ chân ngắn** để gắn vào khớp ống chân.
       - **BẮT BUỘC Trim Sát (`Tight Crop / 0px Transparent Margin`):** Tất cả các file ảnh part của Sticker và Vũ Khí phải được **trim sát 100% vào bounding box hiển thị (xóa toàn bộ phần transparent dư thừa xung quanh)** để việc tính toán tọa độ khớp xoay (`pivot`) và độ dài xương chính xác tuyệt đối.
     - **4 Màu Đội (4 Teams):** Hỗ trợ 4 màu tương ứng 4 người chơi trên bàn: **Đội 1 Xanh Dương (`blue`)**, **Đội 2 Đỏ (`red`)**, **Đội 3 Xanh Lá (`green`)**, **Đội 4 Vàng Cam (`amber`)** (xuất sẵn 4 bộ màu và hỗ trợ đổi màu trực tiếp trên HTML Editor & Godot).
     - **Mỗi Thẻ Bài tương ứng với 1 Bộ Vũ Khí riêng (`assets/weapons/wXXX_<slug>/`):**
       - **Quy tắc hiệu ứng Animation của Vũ Khí theo Cấp Độ Hiếm (`N` / `R` vs `S` / `SSR`):**
         - **Vũ khí cấp `N` và `R` (Common / Rare):** **KHÔNG có hiệu ứng animation của vũ khí** (không tạo/không chạy spritesheet 2x2 trên thân vũ khí; chỉ hiển thị **1 ảnh tĩnh duy nhất** là `weapon_main.png` / `weapon_anim_0.png`, `aura_default: false`). Nếu là vũ khí tầm xa (cung, nỏ, súng...) **không vẽ đạn/mũi tên** dính liền vào vũ khí.
         - **Vũ khí cấp `S` và `SSR` (Epic / Legendary):** **CÓ hiệu ứng animation 4-frame (`2x2`) của chính vũ khí đó** (`weapon_anim_0..3.png` / `weapon_aura`, `aura_default: true`, như `W018`).
       - **Thứ Tự Flow Bắt Buộc Khi Tạo Vũ Khí:**
         1. **Bước 1 — Vẽ Ảnh Ref của Vũ Khí Trước (`wXXX_ref_raw.png` trên nền `#FF00FF` với `layout_guide_1x1.png`):** Vẽ đầy đủ 100% nguyên cây vũ khí (nếu là vũ khí tầm xa không vẽ đạn), đặt chéo nếu là vũ khí dài, tách nền sạch và trim sát (`0px` margin) làm chuẩn thiết kế (`weapon_main.png` / `weapon_anim_0.png`).
         2. **Bước 2 — Tạo Ảnh Spritesheet Animation của Vũ Khí *(CHỈ ÁP DỤNG CHO CẤP `S` VÀ `SSR`, BỎ QUA Ở CẤP `N` VÀ `R`)* (`wXXX_weapon_anim_2x2_raw.png` trên nền `#FF00FF`):** Truyền **`reference_images: [wXXX_ref_raw.png, layout_guide_2x2.png]`** để tạo lưới `2x2` (4 frame loop `weapon_anim_0..3.png`) của chính thanh vũ khí đó kèm hiệu ứng năng lượng/hào quang chuyển động dọc theo thân vũ khí (giữ đồng nhất 100% hình dáng, tỉ lệ, góc nghiêng và vị trí cầm `Grip 1` / `Grip 2` với ảnh Ref).
         3. **Bước Cuối — Tạo Ảnh Bìa của Card (`wXXX_card_preview.png` `884x632` RGB & `.webp` `354x253` RGB):** Truyền `reference_images` (gồm `[wXXX_ref_raw.png]` đối với cấp `N`/`R`, hoặc `[wXXX_ref_raw.png, wXXX_weapon_anim_2x2_raw.png]` đối với cấp `S`/`SSR`) để vẽ ảnh bìa chữ nhật ngang đặt chéo của vũ khí **có nền bối cảnh dark-fantasy đầy đủ (`mode="RGB"`, 100% không trong suốt)**, đảm bảo vũ khí trên bìa thẻ bài giống hệt 100% với ảnh Ref.
       - **Ảnh Preview Thẻ Bài (`wXXX_card_preview.png` `884x632` RGB & `.webp` `354x253` RGB):** Bắt buộc là **ảnh minh họa đầy đủ nền (`RGB` opaque, không phải PNG tách nền trong suốt)** của chính Vũ Khí đó (không ghép sẵn khung thẻ). Nếu vũ khí dài (kiếm, đao, thương, trượng...), bắt buộc **vẽ đặt chéo (diagonal)** để tối ưu khung hình chữ nhật ngang.
       - **Ảnh Vũ Khí Thật (`weapon_main.png`, `weapon_offhand.png`, và `weapon_anim_0..3.png` cho cấp `S`/`SSR`):** Phải vẽ **đầy đủ 100% nguyên cây vũ khí** trên nền `#FF00FF`, tách nền sạch (`edge_clip = 0px`).
       - **Mỗi vũ khí có 2 Vị Trí Cầm (`Grip 1` & `Grip 2`) + Hỗ trợ Cầm Nhiều Vũ Khí (`Weapon_Front` & `Weapon_Back`):**
         - `Grip 1` là điểm cầm tay chính (`Hand_L` / Tay Front); `Grip 2` là điểm cầm thứ 2 trên cán/thân vũ khí (hỗ trợ cầm 2 tay hoặc đổi vị trí cầm).
         - Hỗ trợ gắn vũ khí ở cả **Tay Front (`Weapon_Front`)** lẫn **Tay Back (`Weapon_Back`)** cho các tướng cầm 2 vũ khí (Song Đao, Kiếm + Khiên...).
   - **Tạo Thread Mới trên Muse (`POST /v1/thread` với `{"new_thread": true}`):**
     - Trước khi bắt đầu tạo vũ khí mới, gọi `POST http://127.0.0.1:3456/v1/thread` với body `{"new_thread": true}` để khởi tạo phiên hội thoại mới trên Muse Local Server, tránh bị dính ngữ cảnh cũ.
   - **KHÔNG tạo file `.gif` — BẮT BUỘC tích hợp vào HTML Editor (`sticker_weapon_editor.html` / `<weapon_id>_editor.html`):**
     - File HTML cho phép chọn màu đội (4 màu), chọn thẻ bài/vũ khí, chỉnh 2 vị trí cầm (`Grip 1` & `Grip 2`), bật/tắt vũ khí phụ (`Weapon_Back`) và hiệu ứng bao quanh vũ khí (`WeaponAura`), chọn từng action trong 6 Action (`idle`, `walk`, `attack`, `cast`, `hurt`, `death`) để preview trực tiếp trên Canvas chính, kéo chỉnh khớp xương/keyframe và bấm **`Save to .tscn`** lưu thẳng vào file `.tscn` của từng tướng.
