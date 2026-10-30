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

3. **Kiểm định chất lượng (QC) & Quy trình Tạo Tướng Xương 2D Godot 4 (`.tscn` — Cách 2A):**
   - **Kiểm tra giải phẫu Hướng Lòng Bàn Tay (Phải / Trái) & Chân (Phải / Trái):**
     - Khi vẽ ảnh Reference và tách các mảnh bộ phận (`arm_lower_front`, `arm_lower_back`, `leg_shin_front`, `leg_shin_back`) ở góc `3/4 hướng sang PHẢI`, bắt buộc kiểm tra kỹ:
       - **Hai bàn tay (`arm_lower_front` bên phải & `arm_lower_back` bên trái):** Tuyệt đối không vẽ ngược lòng bàn tay hoặc lật gương làm sai chiều ngón cái. Tay gần camera (`arm_lower_front`) phải thấy mu bàn tay / giáp cổ tay ngoài, các ngón tay khép/cong tự nhiên hướng lòng bàn tay vào trong thân người (không xòe ngửa lòng bàn tay ra ngoài camera). Tay cầm vũ khí (`arm_lower_back`) phải nắm chặt chuôi đúng chiều ngón cái và các đốt ngón tay.
       - **Hai bàn chân & ống chân (`leg_shin_front` chân phải & `leg_shin_back` chân trái):** Không nhân bản y hệt 1 chiếc ủng cho cả 2 chân. Chân trước (`leg_shin_front`) đặt trụ góc `3/4` hơi chếch mũi về phía người nhìn - bên phải; chân sau (`leg_shin_back`) bước về phía trước bên phải đúng phối cảnh `3/4`.
     - **Ghép thử 1:1 trước khi tạo animation:** Phải ghép toàn bộ mảnh rời thành 1 hình hoàn chỉnh để đối chiếu với ảnh Reference gốc, đảm bảo không thừa/trùng bộ phận (ví dụ `chest` không dính bắp tay), không thiếu khớp và không chạm viền (`edge_clip = 0px`).
   - **KHÔNG tạo file `.gif` — BẮT BUỘC tạo kèm 1 file HTML Editor (`<hero_id>_editor.html`) cho mỗi Tướng:**
     - Với mỗi tướng sau khi tạo xong `.tscn`, bắt buộc xuất kèm 1 file HTML tương tác (`/Users/dochung/Desktop/card_g/assets/heroes/<hero_dir>/<hero_id>_editor.html`) với thanh chọn 6 Action (`idle`, `walk`, `attack`, `cast`, `hurt`, `death`) ở trên: **chọn action nào thì mới preview trực tiếp action đó trên Canvas chính** (không hiển thị hàng loạt mini-canvas của các action khác trên thanh chọn).
     - File HTML cho phép người dùng tự kéo/chỉnh lại vị trí khớp xương (`position`, `rotation`, `offset`, `z_index`) trên hệ xương Spine 18 `Bone2D` đầy đủ (Vai $\rightarrow$ Khuỷu $\rightarrow$ Cổ tay $\rightarrow$ Bàn tay & Đùi $\rightarrow$ Gối $\rightarrow$ Cổ chân $\rightarrow$ Bàn chân) và từng keyframe của mỗi action, kèm nút **`Save to .tscn`** cập nhật trực tiếp vào file `<hero_id>.tscn` của Godot.
