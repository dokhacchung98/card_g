extends Control
class_name GuideModal

var current_tab: int = 0
var tab_buttons: Array = []
var tab_containers: Array = []
var subtitle_lbl: Label


func _init() -> void:
	size = Vector2(1080, 1920)
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)


func _ready() -> void:
	visible = false
	z_index = 210
	_build_ui()


func show_guide(initial_tab: int = 0) -> void:
	visible = true
	switch_tab(clampi(initial_tab, 0, 2))


func hide_guide() -> void:
	visible = false


func switch_tab(tab_idx: int) -> void:
	current_tab = clampi(tab_idx, 0, 2)
	for i in range(tab_containers.size()):
		if is_instance_valid(tab_containers[i]):
			tab_containers[i].visible = (i == current_tab)
	for i in range(tab_buttons.size()):
		var btn: Button = tab_buttons[i]
		if i == current_tab:
			GameState.apply_gui_button(btn, "gold", false, 14, 8)
			btn.add_theme_color_override("font_color", Color(1.0, 0.96, 0.82))
		else:
			GameState.apply_gui_button(btn, "slate", false, 14, 8)
			btn.add_theme_color_override("font_color", Color(0.84, 0.86, 0.92))

	if subtitle_lbl != null:
		match current_tab:
			0:
				subtitle_lbl.text = "QUY LUẬT TƯƠNG KHẮC · TƯƠNG SINH 5 HỆ NGŨ HÀNH & 500 THẺ BÀI CỐ ĐỊNH HỆ"
			1:
				subtitle_lbl.text = "LUẬT CHƠI BÀN ĐẤU 4 GÓC · BỘ BÀI CHUNG & 15 GIÂY ÚP BÀI ĐÒN TÂM LÝ"
			2:
				subtitle_lbl.text = "CƠ CHẾ 15 GIÂY GIAO CHIẾN TỰ ĐỘNG · ĐÓNG BĂNG & 2 TIỀN TỆ (COIN / KIM CƯƠNG)"


func _build_ui() -> void:
	for ch in get_children():
		ch.queue_free()
	tab_buttons.clear()
	tab_containers.clear()

	# Dimmed backdrop
	var backdrop := ColorRect.new()
	backdrop.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	backdrop.color = Color(0.02, 0.02, 0.05, 0.88)
	backdrop.gui_input.connect(func(ev: InputEvent):
		if ev is InputEventMouseButton and ev.pressed and ev.button_index == MOUSE_BUTTON_LEFT:
			hide_guide()
	)
	add_child(backdrop)

	# Dialog Board Frame (1000 x 1740 centered)
	var dialog := PanelContainer.new()
	dialog.position = Vector2(40, 90)
	dialog.size = Vector2(1000, 1740)
	dialog.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("dialog", 24))
	add_child(dialog)

	var root_v := VBoxContainer.new()
	root_v.add_theme_constant_override("separation", 14)
	dialog.add_child(root_v)

	# Top Header Banner
	var header_pnl := PanelContainer.new()
	header_pnl.custom_minimum_size = Vector2(0, 96)
	header_pnl.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("header", 14))
	root_v.add_child(header_pnl)

	var header_row := HBoxContainer.new()
	header_row.add_theme_constant_override("separation", 14)
	header_pnl.add_child(header_row)

	var book_ico := TextureRect.new()
	book_ico.texture = GameState.tex("res://assets/ui_hud/icons/icon_guide_book.png")
	book_ico.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	book_ico.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	book_ico.custom_minimum_size = Vector2(48, 48)
	header_row.add_child(book_ico)

	var title_v := VBoxContainer.new()
	title_v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title_v.add_theme_constant_override("separation", 2)
	header_row.add_child(title_v)

	var title_lbl := Label.new()
	title_lbl.text = "SỔ TAY HƯỚNG DẪN & CẨM NANG CHIẾN THUẬT"
	title_lbl.add_theme_font_size_override("font_size", 26)
	title_lbl.add_theme_color_override("font_color", Color(1.0, 0.90, 0.48))
	title_lbl.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.95))
	title_lbl.add_theme_constant_override("outline_size", 5)
	title_v.add_child(title_lbl)

	subtitle_lbl = Label.new()
	subtitle_lbl.text = "QUY LUẬT TƯƠNG KHẮC · TƯƠNG SINH 5 HỆ NGŨ HÀNH & 500 THẺ BÀI CỐ ĐỊNH HỆ"
	subtitle_lbl.add_theme_font_size_override("font_size", 14)
	subtitle_lbl.add_theme_color_override("font_color", Color(0.84, 0.88, 0.96))
	title_v.add_child(subtitle_lbl)

	var close_btn := Button.new()
	close_btn.text = "ĐÓNG"
	close_btn.icon = GameState.tex("res://assets/ui_hud/icons/icon_close_x.png")
	close_btn.expand_icon = true
	close_btn.custom_minimum_size = Vector2(130, 52)
	close_btn.add_theme_font_size_override("font_size", 18)
	close_btn.add_theme_color_override("font_color", Color(1.0, 0.94, 0.94))
	GameState.apply_gui_button(close_btn, "red", false, 14, 8)
	close_btn.pressed.connect(hide_guide)
	header_row.add_child(close_btn)

	# 3-Tab Switcher Row
	var tabs_row := HBoxContainer.new()
	tabs_row.add_theme_constant_override("separation", 12)
	root_v.add_child(tabs_row)

	var tab_defs := [
		{
			"title": "1. XUNG KHẮC 5 HỆ & 500 THẺ",
			"icon": "res://assets/board_map/props/prop_4_wuxing_synergy_seal.png",
		},
		{
			"title": "2. CÁCH CHƠI & ÚP BÀI TÂM LÝ",
			"icon": "res://assets/ui_hud/hud_bars/timer_prep_15s_compass.png",
		},
		{
			"title": "3. CHIẾN ĐẤU & 2 TIỀN TỆ",
			"icon": "res://assets/ui_hud/icons/icon_coin_gold.png",
		},
	]
	for i in range(tab_defs.size()):
		var t_def: Dictionary = tab_defs[i]
		var t_btn := Button.new()
		t_btn.text = str(t_def["title"])
		t_btn.icon = GameState.tex(str(t_def["icon"]))
		t_btn.expand_icon = true
		t_btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		t_btn.custom_minimum_size = Vector2(0, 62)
		t_btn.add_theme_font_size_override("font_size", 18)
		var captured_idx := i
		t_btn.pressed.connect(func(): switch_tab(captured_idx))
		tabs_row.add_child(t_btn)
		tab_buttons.append(t_btn)

	# Content Host (Scrollable)
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	root_v.add_child(scroll)

	var content_stack := VBoxContainer.new()
	content_stack.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	content_stack.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.add_child(content_stack)

	var tab0 := _build_tab_wuxing()
	var tab1 := _build_tab_how_to_play()
	var tab2 := _build_tab_combat_and_currencies()
	content_stack.add_child(tab0)
	content_stack.add_child(tab1)
	content_stack.add_child(tab2)
	tab_containers = [tab0, tab1, tab2]

	# Bottom Footer Action Bar
	var footer_row := HBoxContainer.new()
	footer_row.add_theme_constant_override("separation", 14)
	root_v.add_child(footer_row)

	var prev_btn := Button.new()
	prev_btn.text = "TRANG TRƯỚC"
	prev_btn.icon = GameState.tex("res://assets/ui_hud/icons/icon_cards_hand.png")
	prev_btn.expand_icon = true
	prev_btn.custom_minimum_size = Vector2(220, 58)
	prev_btn.add_theme_font_size_override("font_size", 18)
	GameState.apply_gui_button(prev_btn, "wood", false, 16, 8)
	prev_btn.pressed.connect(func(): switch_tab((current_tab + 2) % 3))
	footer_row.add_child(prev_btn)

	var next_btn := Button.new()
	next_btn.text = "XEM TIẾP MỤC SAU"
	next_btn.icon = GameState.tex("res://assets/ui_hud/icons/icon_guide_book.png")
	next_btn.expand_icon = true
	next_btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	next_btn.custom_minimum_size = Vector2(0, 58)
	next_btn.add_theme_font_size_override("font_size", 19)
	GameState.apply_gui_button(next_btn, "purple", false, 16, 8)
	next_btn.pressed.connect(func(): switch_tab((current_tab + 1) % 3))
	footer_row.add_child(next_btn)

	var ok_btn := Button.new()
	ok_btn.text = "ĐÃ HIỂU LUẬT CHƠI"
	ok_btn.icon = GameState.tex("res://assets/ui_hud/icons/icon_star_new.png")
	ok_btn.expand_icon = true
	ok_btn.custom_minimum_size = Vector2(260, 58)
	ok_btn.add_theme_font_size_override("font_size", 19)
	GameState.apply_gui_button(ok_btn, "green", false, 16, 8)
	ok_btn.pressed.connect(hide_guide)
	footer_row.add_child(ok_btn)

	switch_tab(0)


func _build_tab_wuxing() -> VBoxContainer:
	var box := VBoxContainer.new()
	box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	box.add_theme_constant_override("separation", 14)

	# Section 1: 500 Fixed-Element Cards Rule
	var card500_pnl := PanelContainer.new()
	card500_pnl.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("section", 16))
	box.add_child(card500_pnl)

	var c500_v := VBoxContainer.new()
	c500_v.add_theme_constant_override("separation", 8)
	card500_pnl.add_child(c500_v)

	c500_v.add_child(_make_section_header(
		"res://assets/board_map/props/prop_4_wuxing_synergy_seal.png",
		"1. HỆ THỐNG 500 THẺ BÀI — THUỘC TÍNH CỐ ĐỊNH KHI MỞ RƯƠNG",
		Color(1.0, 0.88, 0.44)
	))

	var rule500_lbl := Label.new()
	rule500_lbl.text = (
		"• Toàn bộ trò chơi gồm 100 Khuôn Vũ Khí / Trang Bị × 5 Hệ Ngũ Hành (Kim, Mộc, Thủy, Hỏa, Thổ) = TỔNG CỘNG 500 THẺ BÀI RIÊNG BIỆT.\n"
		+ "• Khi bạn mở bất kỳ Pack nào, mỗi lá bài rút ra được SINH NGẪU NHIÊN 1 HỆ CỐ ĐỊNH ngay từ lúc mở thẻ.\n"
		+ "• KHÔNG ĐƯỢC PHÉP TỰ Ý ĐỔI HỆ CỦA THẺ! Muốn có cùng cây vũ khí đó ở hệ khác để khắc chế đối phương, bạn cần mở Pack để sưu tầm đúng biến thể Ngũ Hành đó."
	)
	rule500_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	rule500_lbl.add_theme_font_size_override("font_size", 16)
	rule500_lbl.add_theme_color_override("font_color", Color(0.92, 0.94, 0.98))
	c500_v.add_child(rule500_lbl)

	# Section 2: Tương Khắc (Counter Cycle)
	var counter_pnl := PanelContainer.new()
	counter_pnl.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("section", 16))
	box.add_child(counter_pnl)

	var cnt_v := VBoxContainer.new()
	cnt_v.add_theme_constant_override("separation", 8)
	counter_pnl.add_child(cnt_v)

	cnt_v.add_child(_make_section_header(
		"res://assets/cards/icons/types/atk-phys/prop.png",
		"2. VÒNG TRÒN TƯƠNG KHẮC (KHẮC HỆ: +25% SÁT THƯƠNG & GIẢM 15% SÁT THƯƠNG ĐỊCH)",
		Color(1.0, 0.56, 0.46)
	))

	var cnt_desc := Label.new()
	cnt_desc.text = "Khi tướng của bạn tấn công mục tiêu bị Khắc Hệ: Gây THÊM +25% Sát Thương, đồng thời mục tiêu bị khắc chỉ gây được 85% Sát Thương (-15%) lên tướng của bạn!"
	cnt_desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	cnt_desc.add_theme_font_size_override("font_size", 16)
	cnt_desc.add_theme_color_override("font_color", Color(1.0, 0.86, 0.78))
	cnt_v.add_child(cnt_desc)

	var counter_pairs := [
		["kim", "moc", "KIM KHẮC MỘC: Lưỡi kim loại sắc bén chặt đứt cây cối rừng già."],
		["moc", "tho", "MỘC KHẮC THỔ: Rễ cây cổ thụ đâm xuyên và hút kiệt sức đất đá."],
		["tho", "thuy", "THỔ KHẮC THỦY: Đê đất và tường đá chặn đứng dòng nước lũ."],
		["thuy", "hoa", "THỦY KHẮC HỎA: Sóng nước băng giá dập tắt ngọn lửa hung tàn."],
		["hoa", "kim", "HỎA KHẮC KIM: Lửa rồng nhiệt độ cao nung chảy mọi giáp kim loại."],
	]
	for pair in counter_pairs:
		cnt_v.add_child(_make_element_relation_row(str(pair[0]), str(pair[1]), "KHẮC", Color(1.0, 0.45, 0.38), str(pair[2])))

	# Section 3: Tương Sinh (Generation Cycle)
	var gen_pnl := PanelContainer.new()
	gen_pnl.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("section", 16))
	box.add_child(gen_pnl)

	var gen_v := VBoxContainer.new()
	gen_v.add_theme_constant_override("separation", 8)
	gen_pnl.add_child(gen_v)

	gen_v.add_child(_make_section_header(
		"res://assets/cards/icons/types/support/prop.png",
		"3. VÒNG TRÒN TƯƠNG SINH (ĐỒNG MINH & TRANG BỊ: +15% CÔNG/HỒI MÁU & +25% HIỆU LỰC)",
		Color(0.46, 0.96, 0.62)
	))

	var gen_desc := Label.new()
	gen_desc.text = "Đặt 2 thẻ đồng minh có quan hệ Tương Sinh trên sân giúp kích hoạt hào quang Cộng Hưởng (+15% ATK & Hồi Máu). Đặc biệt: Dùng Thẻ Hỗ Trợ hoặc Trang Bị có hệ SINH ra hệ của tướng nhận sẽ tăng +25% toàn bộ chỉ số cộng thêm!"
	gen_desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	gen_desc.add_theme_font_size_override("font_size", 16)
	gen_desc.add_theme_color_override("font_color", Color(0.84, 0.98, 0.88))
	gen_v.add_child(gen_desc)

	var gen_pairs := [
		["kim", "thuy", "KIM SINH THỦY: Kim loại nung chảy hóa thành dòng chất lỏng tinh khiết."],
		["thuy", "moc", "THỦY SINH MỘC: Nước nguồn nuôi dưỡng mầm cây sinh trưởng mạnh mẽ."],
		["moc", "hoa", "MỘC SINH HỎA: Gỗ khô làm nhiên liệu bùng lên ngọn lửa bất diệt."],
		["hoa", "tho", "HỎA SINH THỔ: Lửa thiêu rụi vạn vật bồi đắp thành tro đất màu mỡ."],
		["tho", "kim", "THỔ SINH KIM: Lòng đất sâu kết tinh quặng quý và kim loại thần."],
	]
	for pair in gen_pairs:
		gen_v.add_child(_make_element_relation_row(str(pair[0]), str(pair[1]), "SINH", Color(0.38, 0.95, 0.56), str(pair[2])))

	return box


func _build_tab_how_to_play() -> VBoxContainer:
	var box := VBoxContainer.new()
	box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	box.add_theme_constant_override("separation", 14)

	# Section 1: Loadout 15 Cards & Shared Deck
	var deck_pnl := PanelContainer.new()
	deck_pnl.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("section", 16))
	box.add_child(deck_pnl)

	var deck_v := VBoxContainer.new()
	deck_v.add_theme_constant_override("separation", 10)
	deck_pnl.add_child(deck_v)

	deck_v.add_child(_make_section_header(
		"res://assets/ui_hud/icons/icon_cards_hand.png",
		"1. QUY TẮC LẬP ĐỘI HÌNH 15 LÁ & BỘ BÀI CHUNG (SHARED DECK)",
		Color(1.0, 0.88, 0.44)
	))

	var deck_lbl := Label.new()
	deck_lbl.text = (
		"• Trước trận đấu, mỗi người chơi chuẩn bị Bộ Bài Xuất Chiến gồm ĐÚNG 15 THẺ BÀI ĐỘC NHẤT từ Kho Thẻ 500 lá.\n"
		+ "• Để đảm bảo cân bằng chiến thuật, đội hình 15 lá bắt buộc có tối thiểu: >= 2 Thẻ Tấn Công (Vật Lý / Phép), >= 2 Thẻ Đỡ Đòn (Tanker), >= 2 Thẻ Hỗ Trợ (Support) và >= 2 Thẻ Trang Bị (Item).\n"
		+ "• Khi vào bàn đấu (2, 3 hoặc 4 người), toàn bộ bài của các người chơi được xáo trộn thành BỘ BÀI CHUNG ở trung tâm bàn cờ và chia đều 4 lá cho mỗi người vào đầu mỗi Hiệp!"
	)
	deck_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	deck_lbl.add_theme_font_size_override("font_size", 16)
	deck_lbl.add_theme_color_override("font_color", Color(0.92, 0.94, 0.98))
	deck_v.add_child(deck_lbl)

	# Role icons summary strip
	var role_row := HBoxContainer.new()
	role_row.add_theme_constant_override("separation", 10)
	deck_v.add_child(role_row)
	for r_key in ["atk_phys", "atk_mag", "tanker", "support", "item"]:
		var r_meta: Dictionary = GameState.ROLE_META[r_key]
		var r_chip := PanelContainer.new()
		r_chip.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		r_chip.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("slot_active", 8))
		role_row.add_child(r_chip)

		var rh := HBoxContainer.new()
		rh.alignment = BoxContainer.ALIGNMENT_CENTER
		rh.add_theme_constant_override("separation", 6)
		r_chip.add_child(rh)

		var rico := TextureRect.new()
		rico.texture = GameState.tex(str(r_meta["icon"]))
		rico.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		rico.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		rico.custom_minimum_size = Vector2(28, 28)
		rh.add_child(rico)

		var rlbl := Label.new()
		rlbl.text = str(r_meta["short"])
		rlbl.add_theme_font_size_override("font_size", 15)
		rlbl.add_theme_color_override("font_color", Color(1.0, 0.95, 0.82))
		rh.add_child(rlbl)

	# Section 2: 15s Preparation & Psychological Bluffing
	var prep_pnl := PanelContainer.new()
	prep_pnl.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("section", 16))
	box.add_child(prep_pnl)

	var prep_v := VBoxContainer.new()
	prep_v.add_theme_constant_override("separation", 10)
	prep_pnl.add_child(prep_v)

	prep_v.add_child(_make_section_header(
		"res://assets/ui_hud/hud_bars/timer_prep_15s_compass.png",
		"2. PHA 1 — 15 GIÂY DÀN TRẬN 10 Ô ÚP BÀI & ĐÒN TÂM LÝ (BLUFFING)",
		Color(0.45, 0.88, 1.0)
	))

	var prep_lbl := Label.new()
	prep_lbl.text = (
		"• Bàn cờ hình vuông chia làm 4 Góc Độc Lập cho tối đa 4 người chơi (Đội Xanh Dương, Đội Đỏ, Đội Xanh Lá, Đội Vàng Cam).\n"
		+ "• Cạnh bàn của mỗi người có 10 Ô ĐẶT BÀI (5 Ô Hàng Trước Tiền Tuyến + 5 Ô Hàng Sau Hậu Phương) và 1 Trụ Góc Căn Cứ 100 HP.\n"
		+ "• ĐẶT BÀI ÚP MẶT: Trong 15 giây Chuẩn Bị, mọi thẻ bài mới đặt xuống sân đều ở trạng thái ÚP MẶT (đối phương chỉ thấy vị trí ô có bài nhưng không biết bạn đặt tướng gì, trang bị gì hay hệ gì).\n"
		+ "• ĐÒN TÂM LÝ (NHẶT LẠI & ĐỔI VỊ TRÍ TỰ DO): Trước khi đồng hồ 15s kết thúc, bạn có quyền NHẤN VÀO Ô ĐANG ÚP ĐỂ NHẶT LẠI BÀI VỀ TAY và đặt sang ô khác nhằm đánh lừa hướng phán đoán của đối thủ!"
	)
	prep_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	prep_lbl.add_theme_font_size_override("font_size", 16)
	prep_lbl.add_theme_color_override("font_color", Color(0.92, 0.94, 0.98))
	prep_v.add_child(prep_lbl)

	# Section 3: Shared Deck Draw, History & Sudden Death 60s
	var mana_pnl := PanelContainer.new()
	mana_pnl.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("section", 16))
	box.add_child(mana_pnl)

	var mana_v := VBoxContainer.new()
	mana_v.add_theme_constant_override("separation", 10)
	mana_pnl.add_child(mana_v)

	mana_v.add_child(_make_section_header(
		"res://assets/board_map/props/prop_3_sudden_death_brazier.png",
		"3. RÚT BÀI TỪ BỘ BÀI CHUNG · LỊCH SỬ BÀI MỞ & 60 GIÂY SINH TỬ",
		Color(0.55, 0.82, 1.0)
	))

	var mana_lbl := Label.new()
	mana_lbl.text = (
		"• CHIA BÀI MỖI HIỆP: Đầu trận mỗi người rút 5 lá từ Bộ Bài Chung (50 / 75 / 100 lá tùy số người chơi). Sau mỗi hiệp giao chiến, mỗi người còn sống rút thêm 2 lá bài mới.\n"
		+ "• XEM LỊCH SỬ BÀI ĐÃ MỞ: Nhấn vào nút 'Bài mở' tại Trụ Góc của bất kỳ người chơi nào để thống kê những thẻ và hệ họ đã tung ra sân.\n"
		+ "• CUỘC CHIẾN SINH TỬ 60 GIÂY (SUDDEN DEATH): Khi Bộ Bài Chung đã rút cạn và mọi người chơi đã đánh hết bài trên tay, trận đấu bước vào 60 Giây Sinh Tử liên tục không nghỉ cho đến khi tìm ra người sống sót cuối cùng!"
	)
	mana_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	mana_lbl.add_theme_font_size_override("font_size", 16)
	mana_lbl.add_theme_color_override("font_color", Color(0.92, 0.94, 0.98))
	mana_v.add_child(mana_lbl)

	return box


func _build_tab_combat_and_currencies() -> VBoxContainer:
	var box := VBoxContainer.new()
	box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	box.add_theme_constant_override("separation", 14)

	# Section 1: 15s Auto-Combat, Freeze & Corner Base Breach
	var combat_pnl := PanelContainer.new()
	combat_pnl.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("section", 16))
	box.add_child(combat_pnl)

	var cmb_v := VBoxContainer.new()
	cmb_v.add_theme_constant_override("separation", 10)
	combat_pnl.add_child(cmb_v)

	cmb_v.add_child(_make_section_header(
		"res://assets/ui_hud/hud_bars/timer_combat_15s_crossed_swords.png",
		"1. PHA 2 — 15 GIÂY GIAO CHIẾN TỰ ĐỘNG · ĐÓNG BĂNG & PHÁ TRỤ GÓC",
		Color(1.0, 0.56, 0.46)
	))

	var cmb_lbl := Label.new()
	cmb_lbl.text = (
		"• LẬT BÀI & TỰ ĐỘNG CHIẾN ĐẤU (15 GIÂY): Ngay khi hết 15s Chuẩn Bị, toàn bộ thẻ úp của các góc đồng loạt LẬT NGỬA! Thẻ Trang Bị tự động gắn vào tướng cùng cột, kích hoạt Tương Sinh Ngũ Hành và các Tướng Stickman lao ra giữa bàn giao chiến thời gian thực.\n"
		+ "• ĐÓNG BĂNG GIỮA HIỆP (FREEZE MECHANIC): Khi hết 15s Giao Chiến mà trên sân vẫn còn tướng sống sót, toàn bộ tướng đó sẽ ĐÓNG BĂNG TẠI CHỖ (giữ nguyên lượng Máu hiện tại và vị trí đứng) để chiến đấu tiếp ở hiệp sau!\n"
		+ "• ĐỘT KÍCH PHÁ GÓC (100 HP): Nếu tướng của bạn tiêu diệt hết quân cản đường và tràn vào Góc Căn Cứ đối phương, chúng sẽ lao thẳng vào Trụ Góc phát nổ gây SÁT THƯƠNG CHUẨN (Cấp N: 10 HP | Cấp R: 15 HP | Cấp S: 22 HP | Cấp SSR: 30 HP). Ai về 0 HP sẽ bị loại!"
	)
	cmb_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	cmb_lbl.add_theme_font_size_override("font_size", 16)
	cmb_lbl.add_theme_color_override("font_color", Color(0.92, 0.94, 0.98))
	cmb_v.add_child(cmb_lbl)

	# Section 2: 2 Main Currencies (Coin vs Kim Cương)
	var cur_pnl := PanelContainer.new()
	cur_pnl.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("section", 16))
	box.add_child(cur_pnl)

	var cur_v := VBoxContainer.new()
	cur_v.add_theme_constant_override("separation", 12)
	cur_pnl.add_child(cur_v)

	cur_v.add_child(_make_section_header(
		"res://assets/ui_hud/icons/icon_shop_chest.png",
		"2. HỆ THỐNG 2 TIỀN TỆ CHÍNH: COIN & KIM CƯƠNG (QUY TẮC MUA 5 PACK)",
		Color(1.0, 0.88, 0.42)
	))

	# Two currency cards side by side
	var cur_cards_row := HBoxContainer.new()
	cur_cards_row.add_theme_constant_override("separation", 14)
	cur_v.add_child(cur_cards_row)

	# Coin Card (Packs 1, 2, 3)
	var coin_card := PanelContainer.new()
	coin_card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	coin_card.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("slot_active", 14))
	cur_cards_row.add_child(coin_card)

	var coin_v := VBoxContainer.new()
	coin_v.add_theme_constant_override("separation", 8)
	coin_card.add_child(coin_v)

	coin_v.add_child(_make_section_header(
		"res://assets/ui_hud/icons/icon_coin_gold.png",
		"COIN (ĐỒNG VÀNG) — MUA PACK 1, 2, 3",
		Color(1.0, 0.86, 0.34)
	))

	var coin_desc := Label.new()
	coin_desc.text = (
		"Tiền tệ phổ thông nhận được khi chiến đấu và hoàn thành trận đấu. Dùng để mua 3 Pack đầu:\n"
		+ "• PACK #1 — Rương Thiết Ấn (Phổ Thông): 200 Coin\n"
		+ "• PACK #2 — Rương Thanh Đồng (Tinh Nhuệ): 500 Coin\n"
		+ "• PACK #3 — Rương Bạch Ngân (Cao Cấp): 1000 Coin"
	)
	coin_desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	coin_desc.add_theme_font_size_override("font_size", 15)
	coin_desc.add_theme_color_override("font_color", Color(0.95, 0.92, 0.82))
	coin_v.add_child(coin_desc)

	# Diamond Card (Packs 4, 5 ONLY)
	var dia_card := PanelContainer.new()
	dia_card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	dia_card.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("slot_active", 14))
	cur_cards_row.add_child(dia_card)

	var dia_v := VBoxContainer.new()
	dia_v.add_theme_constant_override("separation", 8)
	dia_card.add_child(dia_v)

	dia_v.add_child(_make_section_header(
		"res://assets/ui_hud/icons/icon_diamond_gem.png",
		"KIM CƯƠNG — CHỈ MUA 2 PACK CUỐI (4 & 5)",
		Color(0.45, 0.90, 1.0)
	))

	var dia_desc := Label.new()
	dia_desc.text = (
		"Tiền tệ cao cấp quý hiếm, CHỈ DÙNG ĐỂ MUA 2 PACK CUỐI có tỉ lệ rớt thẻ S và SSR Thần Thoại cực cao:\n"
		+ "• PACK #4 — Rương Hoàng Kim (Sử Thi S): 150 Kim Cương\n"
		+ "• PACK #5 — Rương Thần Thoại (SSR Tối Thượng): 300 Kim Cương\n"
		+ "(Không thể dùng Coin để mua Pack #4 & #5!)"
	)
	dia_desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	dia_desc.add_theme_font_size_override("font_size", 15)
	dia_desc.add_theme_color_override("font_color", Color(0.84, 0.95, 1.0))
	dia_v.add_child(dia_desc)

	# 5 Pack Visual Pricing Strip
	var pack_strip := HBoxContainer.new()
	pack_strip.add_theme_constant_override("separation", 8)
	cur_v.add_child(pack_strip)

	for p_t in range(1, 6):
		var pm: Dictionary = GameState.PACK_TYPES[p_t]
		var is_dia: bool = str(pm.get("currency", "coin")) == "diamond"
		var p_box := PanelContainer.new()
		p_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		p_box.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("slot_active" if is_dia else "slot_gray", 8))
		pack_strip.add_child(p_box)

		var pv := VBoxContainer.new()
		pv.alignment = BoxContainer.ALIGNMENT_CENTER
		pv.add_theme_constant_override("separation", 4)
		p_box.add_child(pv)

		var pico := TextureRect.new()
		pico.texture = GameState.tex("res://assets/ui_hud/gacha_pack/pack_0_sealed.png")
		pico.self_modulate = pm["tint"]
		pico.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		pico.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		pico.custom_minimum_size = Vector2(58, 72)
		pv.add_child(pico)

		var pname := Label.new()
		pname.text = "%s (%s)" % [str(pm["short_name"]), str(pm["sub"])]
		pname.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		pname.add_theme_font_size_override("font_size", 13)
		pname.add_theme_color_override("font_color", pm["color"])
		pv.add_child(pname)

		var price_row := HBoxContainer.new()
		price_row.alignment = BoxContainer.ALIGNMENT_CENTER
		price_row.add_theme_constant_override("separation", 4)
		pv.add_child(price_row)

		var c_ico := TextureRect.new()
		c_ico.texture = GameState.tex(str(pm["currency_icon"]))
		c_ico.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		c_ico.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		c_ico.custom_minimum_size = Vector2(20, 20)
		price_row.add_child(c_ico)

		var plbl := Label.new()
		plbl.text = "%d %s" % [int(pm["price"]), str(pm["currency_label"])]
		plbl.add_theme_font_override("font", GameState.get_num_font())
		plbl.add_theme_font_size_override("font_size", 14)
		plbl.add_theme_color_override("font_color", Color(0.50, 0.92, 1.0) if is_dia else Color(1.0, 0.88, 0.40))
		price_row.add_child(plbl)

	return box


func _make_section_header(icon_path: String, title_text: String, col: Color) -> HBoxContainer:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)

	var ico := TextureRect.new()
	ico.texture = GameState.tex(icon_path)
	ico.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	ico.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	ico.custom_minimum_size = Vector2(32, 32)
	row.add_child(ico)

	var lbl := Label.new()
	lbl.text = title_text
	lbl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	lbl.add_theme_font_size_override("font_size", 19)
	lbl.add_theme_color_override("font_color", col)
	lbl.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.95))
	lbl.add_theme_constant_override("outline_size", 4)
	row.add_child(lbl)

	return row


func _make_element_relation_row(elem_a: String, elem_b: String, verb: String, verb_col: Color, desc_text: String) -> PanelContainer:
	var pnl := PanelContainer.new()
	pnl.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("slot_gray", 6))

	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	pnl.add_child(row)

	var meta_a: Dictionary = GameState.ELEMENT_META[elem_a]
	var meta_b: Dictionary = GameState.ELEMENT_META[elem_b]

	row.add_child(_make_elem_badge(meta_a))

	var verb_lbl := Label.new()
	verb_lbl.text = verb
	verb_lbl.custom_minimum_size = Vector2(68, 0)
	verb_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	verb_lbl.add_theme_font_size_override("font_size", 16)
	verb_lbl.add_theme_color_override("font_color", verb_col)
	verb_lbl.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.95))
	verb_lbl.add_theme_constant_override("outline_size", 3)
	row.add_child(verb_lbl)

	row.add_child(_make_elem_badge(meta_b))

	var desc_lbl := Label.new()
	desc_lbl.text = desc_text
	desc_lbl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	desc_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	desc_lbl.add_theme_font_size_override("font_size", 15)
	desc_lbl.add_theme_color_override("font_color", Color(0.92, 0.94, 0.98))
	row.add_child(desc_lbl)

	return pnl


func _make_elem_badge(meta: Dictionary) -> HBoxContainer:
	var h := HBoxContainer.new()
	h.custom_minimum_size = Vector2(110, 32)
	h.add_theme_constant_override("separation", 6)

	var ico := TextureRect.new()
	ico.texture = GameState.tex(str(meta["icon"]))
	ico.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	ico.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	ico.custom_minimum_size = Vector2(28, 28)
	h.add_child(ico)

	var lbl := Label.new()
	lbl.text = str(meta["short"]).to_upper()
	lbl.add_theme_font_size_override("font_size", 16)
	lbl.add_theme_color_override("font_color", meta["color"])
	lbl.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.95))
	lbl.add_theme_constant_override("outline_size", 3)
	h.add_child(lbl)

	return h
