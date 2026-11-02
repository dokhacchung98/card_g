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
   - **Kiến trúc Tướng Stickman 4 Màu (`assets/sticker_hero/`) + Vũ Khí Theo Thẻ Bài (`assets/weapons/wXXX_<slug>/`):**
     - Toàn bộ các thẻ tướng dùng chung **1 bộ Tướng Stickman / Chiến Binh Người Que 2D (`sticker_hero`)** với **4 màu đội**: **Đội 1 Xanh Dương (`blue`)**, **Đội 2 Đỏ (`red`)**, **Đội 3 Xanh Lá (`green`)**, **Đội 4 Vàng Cam (`amber`)** (tách rời đầy đủ 16 part: `head` tròn không mặt, `neck` khớp cổ, `chest` thân trên, `hip_kilt` thân dưới, `arm_upper_front/back`, `arm_lower_front/back` dạng khung dài đều tròn 2 đầu, `hand_front/back` tròn kèm đoạn cổ tay ngắn, `leg_thigh_front/back`, `leg_shin_front/back` dạng khung dài đều tròn 2 đầu, `foot_front/back` dạng giày kèm đoạn cổ chân ngắn).
     - **BẮT BUỘC Trim Sát (`Tight Crop / 0px Transparent Margin`):** Tất cả hình ảnh part của Sticker và Vũ Khí phải được **trim sát 100% vào vùng pixel hiển thị (xóa bỏ hoàn toàn vùng transparent dư thừa xung quanh)** để việc tính toán pivot và gắn khớp chính xác.
     - Mỗi thẻ bài (`C01`..`C80`) tương ứng với **1 Bộ Vũ Khí riêng** phân cấp theo độ hiếm (`N`: vũ khí gỉ sét/cơ bản $\rightarrow$ `R`: tinh luyện $\rightarrow$ `S`: phát sáng nguyên tố $\rightarrow$ `SSR`: thần binh xịn có spritesheet animation của vũ khí `weapon_anim_0..3.png`).
     - **Flow 3 Bước Bắt Buộc Khi Vẽ Vũ Khí (đặc biệt là `SSR`):**
       1. **Bước 1:** Vẽ **Ảnh Ref của Vũ Khí trước** (`wXXX_ref_raw.png` trên nền `#FF00FF` dùng `layout_guide_1x1.png`), đầy đủ 100% nguyên cây.
       2. **Bước 2:** Từ ảnh Ref (`reference_images: [wXXX_ref_raw.png, layout_guide_2x2.png]`), tạo **Ảnh Spritesheet Animation 2x2 của chính Vũ Khí đó** (`wXXX_weapon_anim_2x2_raw.png` trên nền `#FF00FF`), giữ nguyên hình dáng/góc nghiêng của vũ khí và diễn hoạt hiệu ứng năng lượng bao quanh lưỡi vũ khí qua 4 frame.
       3. **Bước 3:** Cuối cùng mới dùng ảnh Ref + Spritesheet Animation (`reference_images: [wXXX_ref_raw.png, wXXX_weapon_anim_2x2_raw.png]`) để tạo **Ảnh Bìa của Card (`wXXX_card_preview.png` `884x632` & `.webp` `354x253`)** đặt chéo tối ưu khung ngang, đảm bảo đồng nhất 100% thiết kế.
     - **Mỗi vũ khí có 2 Vị Trí Cầm (`Grip 1` & `Grip 2`) + Hỗ trợ Cầm Nhiều Vũ Khí (`Weapon_Front` & `Weapon_Back`):** Cho phép cầm 1 tay, cầm 2 tay (bám theo `Grip 1` và `Grip 2`) hoặc cầm 2 vũ khí ở cả 2 tay.
   - **Tạo Thread Mới trên Muse (`POST /v1/thread` với `{"new_thread": true}`):** Trước khi tạo vũ khí mới, gọi `POST http://127.0.0.1:3456/v1/thread` với `{"new_thread": true}` để tách biệt khỏi context cũ.
   - **Không tạo file `.gif` — Tích hợp vào HTML Editor (`assets/sticker_weapon_editor.html` & `<weapon_id>_editor.html`):** Cho phép chọn màu đội (4 màu), chọn vũ khí của từng thẻ bài, chỉnh 2 vị trí cầm (`Grip 1` & `Grip 2`), chỉnh animation 6 Action (`idle`, `walk`, `attack`, `cast`, `hurt`, `death`) và bấm **`Save to .tscn`** lưu vào `.tscn` của từng tướng.
