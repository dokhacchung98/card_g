---
trigger: always_on
description: Quy tắc bắt buộc chạy lệnh terminal qua script.sh và tạo ảnh/assets bằng Muse Local API theo chuẩn skill agent-sprite-forge
---

# Project Rules & Agent Instructions (`card_g`)

1. **Thực thi Terminal qua `script.sh`:**
   - Mọi lệnh terminal cần chạy **BẮT BUỘC** phải được ghi/sửa vào file `/Users/dochung/Desktop/card_g/script.sh`, sau đó chỉ thực thi bằng lệnh `bash /Users/dochung/Desktop/card_g/script.sh` (hoặc `bash script.sh`). Không chạy lệnh lẻ trực tiếp.

2. **Tạo Ảnh & Game Assets bằng Muse Local API + `agent-sprite-forge`:**
   - Khởi động Muse Local Server (qua `script.sh`): `bash /Users/dochung/Desktop/muse-local-api/start.sh --daemon`
   - Base URL: `http://127.0.0.1:3456/v1` | Health: `GET http://127.0.0.1:3456/health` | Model: `"muse-spark"` | Key: `"muse-local"`
   - Tạo ảnh / raw spritesheet / map: `POST http://127.0.0.1:3456/generate-image`
   - Sửa ảnh / tạo biến thể từ reference: `POST http://127.0.0.1:3456/edit-image`
   - Tạo video cho `video2dsprite`: `POST http://127.0.0.1:3456/generate-video`
   - Tuân thủ toàn bộ quy trình lập kế hoạch, viết prompt nền `#FF00FF`, chia lưới nhiều hàng (`2x2`, `2x3`, `3x3`, `4x4`), hậu xử lý bằng Python scripts và QC nghiêm ngặt theo tài liệu trong `/Users/dochung/Desktop/card_g/AGENTS.md` và `/Users/dochung/.gemini/config/skills/agent-sprite-forge/SKILL.md`.
   - **Tái sử dụng Layout Guide (`/Users/dochung/Desktop/card_g/layout_guide/`):** Luôn dùng sẵn các file `layout_guide_<rows>x<cols>.png` trong `/Users/dochung/Desktop/card_g/layout_guide/` thay vì tạo lại mỗi lần chạy. Nếu cần thêm layout mới, lưu trực tiếp vào `/Users/dochung/Desktop/card_g/layout_guide/` để tối ưu thời gian và tiết kiệm token.
   - **Phân cấp ngoại hình Tướng theo Độ Hiếm (`N -> R -> S -> SSR`):** Mỗi tướng cố định ở 1 độ hiếm trong `GAME_DESIGN.md`. Khi thiết kế:
     - **Tướng cấp `N` (Common):** Ngoại hình lính bộ binh / tân binh cơ bản nhất, giáp sắt/da mộc mạc, vũ khí thô, không phát sáng hào quang.
     - **Tướng cấp `R` (Rare):** Chiến binh / kỵ sĩ tinh nhuệ, giáp chạm khắc chỉnh tề, vũ khí sắc bén có điểm nhấn nguyên tố nhẹ.
     - **Tướng cấp `S` (Epic):** Thống lĩnh / đại pháp sư, giáp chiến cầu kỳ viền vàng/hắc kim, vũ khí phát sáng năng lượng nguyên tố rõ rệt.
     - **Tướng cấp `SSR` (Legendary):** Thần tướng / bá chủ tối thượng, giáp thần thoại lộng lẫy nhiều tầng, hào quang cổ ngữ/nguyên tố rực rỡ và thần binh cực kỳ hoành tráng.
   - **Kiểm tra giải phẫu Hướng Lòng Bàn Tay (Phải / Trái) & Chân (Phải / Trái):**
     - Tay gần camera (`arm_lower_front`) phải thấy mu bàn tay / giáp cổ tay ngoài, lòng bàn tay hướng vào trong thân người (tuyệt đối không xòe ngửa lòng bàn tay ra ngoài camera hoặc gắn nhầm tay trái/phải); tay cầm vũ khí (`arm_lower_back`) nắm chặt chuôi đúng chiều ngón cái.
     - Chân phải (`leg_shin_front`) và chân trái (`leg_shin_back`) phải phân biệt rõ góc đứng `3/4` (không nhân bản y hệt 1 chiếc ủng cho cả 2 chân).
   - **Skill chuẩn tạo Tướng Xương 2D của dự án (`card-g-hero-rig-builder`):** Luôn đọc và tuân thủ quy trình 8 bước tại `/Users/dochung/Desktop/card_g/.agent/skills/card-g-hero-rig-builder/SKILL.md` (tách 18 mảnh cơ thể + 4 VFX có opacity mềm trong suốt, ghép thử 1:1 kiểm định giải phẫu 2 bàn tay/chân & 18 xương Spine, xuất `.tscn` và `<hero_id>_editor.html`).
   - **Chỉ tạo ảnh ngang Preview Chân Dung Tướng (`<hero_id>_portrait_preview.png` `884x632` & `.webp` `354x253`), KHÔNG tạo ảnh thẻ bài đã ghép sẵn khung:** Khung thẻ template, tên tướng, mô tả kỹ năng, icon hệ/loại và chỉ số sẽ được ghép động bằng code trong game.
   - **Không tạo file `.gif` — Bắt buộc tạo kèm 1 file HTML Editor (`<hero_id>_editor.html`) cho mỗi Tướng:**
     - Mỗi tướng phải có sẵn 1 file `<hero_id>_editor.html` với thanh chọn 6 Action (`idle`, `walk`, `attack`, `cast`, `hurt`, `death`) ở trên: **chọn action nào thì mới preview trực tiếp action đó trên Canvas chính** (không hiển thị mini-canvas của các action khác trên thanh chọn), cho phép người dùng tự chỉnh vị trí/góc xoay của từng bộ phận trên hệ xương Spine 18 `Bone2D` đầy đủ & từng keyframe, kèm nút **`Save to .tscn`** cập nhật trực tiếp vào file `.tscn`.
