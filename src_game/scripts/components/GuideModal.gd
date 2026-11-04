extends Control
class_name GuideModal

var current_tab: int = 0
var tab_buttons: Array = []
var tab_containers: Array = []


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
			GameState.apply_gui_button(btn, "gold", false, 16, 10)
			btn.add_theme_color_override("font_color", Color(1.0, 0.96, 0.82))
		else:
			GameState.apply_gui_button(btn, "slate", false, 16, 10)
			btn.add_theme_color_override("font_color", Color(0.84, 0.86, 0.92))


func _build_ui() -> void:
	for ch in get_children():
		ch.queue_free()
	tab_buttons.clear()
	tab_containers.clear()

	var backdrop := ColorRect.new()
	backdrop.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	backdrop.color = Color(0.02, 0.02, 0.05, 0.88)
	backdrop.gui_input.connect(func(ev: InputEvent):
		if ev is InputEventMouseButton and ev.pressed and ev.button_index == MOUSE_BUTTON_LEFT:
			hide_guide()
	)
	add_child(backdrop)

	var dialog := PanelContainer.new()
	dialog.position = Vector2(40, 130)
	dialog.size = Vector2(1000, 1660)
	dialog.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("dialog", 28))
	add_child(dialog)

	var root_v := VBoxContainer.new()
	root_v.add_theme_constant_override("separation", 18)
	dialog.add_child(root_v)

	# Top Header Banner
	var header_pnl := PanelContainer.new()
	header_pnl.custom_minimum_size = Vector2(0, 96)
	header_pnl.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("header", 16))
	root_v.add_child(header_pnl)

	var header_row := HBoxContainer.new()
	header_row.add_theme_constant_override("separation", 14)
	header_pnl.add_child(header_row)

	var book_ico := TextureRect.new()
	book_ico.texture = GameState.tex("res://assets/ui_hud/icons/icon_guide_book.png")
	book_ico.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	book_ico.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	book_ico.custom_minimum_size = Vector2(52, 52)
	header_row.add_child(book_ico)

	var title_lbl := Label.new()
	title_lbl.text = "LUẬT CHƠI & NGŨ HÀNH"
	title_lbl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title_lbl.add_theme_font_size_override("font_size", 32)
	title_lbl.add_theme_color_override("font_color", Color(1.0, 0.90, 0.44))
	header_row.add_child(title_lbl)

	var close_btn := Button.new()
	close_btn.text = "ĐÓNG"
	close_btn.icon = GameState.tex("res://assets/ui_hud/icons/icon_close_x.png")
	close_btn.expand_icon = true
	close_btn.custom_minimum_size = Vector2(160, 66)
	close_btn.add_theme_font_size_override("font_size", 24)
	GameState.apply_gui_button(close_btn, "red", false, 16, 10)
	close_btn.pressed.connect(hide_guide)
	header_row.add_child(close_btn)

	# 3-Tab Switcher Row
	var tabs_row := HBoxContainer.new()
	tabs_row.add_theme_constant_override("separation", 14)
	root_v.add_child(tabs_row)

	var tab_defs := [
		{"title": "1. NGŨ HÀNH", "icon": "res://assets/board_map/props/prop_4_wuxing_synergy_seal.png"},
		{"title": "2. CÁCH CHƠI", "icon": "res://assets/ui_hud/hud_bars/timer_prep_15s_compass.png"},
		{"title": "3. RƯƠNG & TIỀN", "icon": "res://assets/ui_hud/icons/icon_coin_gold.png"},
	]
	for i in range(tab_defs.size()):
		var t_def: Dictionary = tab_defs[i]
		var t_btn := Button.new()
		t_btn.text = str(t_def["title"])
		t_btn.icon = GameState.tex(str(t_def["icon"]))
		t_btn.expand_icon = true
		t_btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		t_btn.custom_minimum_size = Vector2(0, 74)
		t_btn.add_theme_font_size_override("font_size", 24)
		var captured_idx := i
		t_btn.pressed.connect(func(): switch_tab(captured_idx))
		tabs_row.add_child(t_btn)
		tab_buttons.append(t_btn)

	# Content Host (Scrollable)
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	GameState.setup_touch_scroll(scroll)
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
	footer_row.add_theme_constant_override("separation", 16)
	root_v.add_child(footer_row)

	var next_btn := Button.new()
	next_btn.text = "TRANG TIẾP"
	next_btn.icon = GameState.tex("res://assets/ui_hud/icons/icon_guide_book.png")
	next_btn.expand_icon = true
	next_btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	next_btn.custom_minimum_size = Vector2(0, 76)
	next_btn.add_theme_font_size_override("font_size", 25)
	GameState.apply_gui_button(next_btn, "purple", false, 18, 12)
	next_btn.pressed.connect(func(): switch_tab((current_tab + 1) % 3))
	footer_row.add_child(next_btn)

	var ok_btn := Button.new()
	ok_btn.text = "ĐÃ HIỂU"
	ok_btn.icon = GameState.tex("res://assets/ui_hud/icons/icon_star_new.png")
	ok_btn.expand_icon = true
	ok_btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ok_btn.custom_minimum_size = Vector2(0, 76)
	ok_btn.add_theme_font_size_override("font_size", 25)
	GameState.apply_gui_button(ok_btn, "green", false, 18, 12)
	ok_btn.pressed.connect(hide_guide)
	footer_row.add_child(ok_btn)

	switch_tab(0)


func _build_tab_wuxing() -> VBoxContainer:
	var box := VBoxContainer.new()
	box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	box.add_theme_constant_override("separation", 18)

	var counter_pnl := PanelContainer.new()
	counter_pnl.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("section", 20))
	box.add_child(counter_pnl)

	var cnt_v := VBoxContainer.new()
	cnt_v.add_theme_constant_override("separation", 12)
	counter_pnl.add_child(cnt_v)

	cnt_v.add_child(_make_section_header(
		"res://assets/cards/icons/types/atk-phys/prop.png",
		"TƯƠNG KHẮC (+50% DAME GÂY RA / -30% DAME NHẬN)",
		Color(1.0, 0.56, 0.46)
	))

	var counter_pairs := [
		["kim", "moc", "Kim khắc Mộc (+50% Dame / -30% Nhận)"],
		["moc", "tho", "Mộc khắc Thổ (+50% Dame / -30% Nhận)"],
		["tho", "thuy", "Thổ khắc Thủy (+50% Dame / -30% Nhận)"],
		["thuy", "hoa", "Thủy khắc Hỏa (+50% Dame / -30% Nhận)"],
		["hoa", "kim", "Hỏa khắc Kim (+50% Dame / -30% Nhận)"],
	]
	for pair in counter_pairs:
		cnt_v.add_child(_make_element_relation_row(str(pair[0]), str(pair[1]), "KHẮC", Color(1.0, 0.48, 0.40), str(pair[2])))

	var gen_pnl := PanelContainer.new()
	gen_pnl.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("section", 20))
	box.add_child(gen_pnl)

	var gen_v := VBoxContainer.new()
	gen_v.add_theme_constant_override("separation", 12)
	gen_pnl.add_child(gen_v)

	gen_v.add_child(_make_section_header(
		"res://assets/cards/icons/types/support/prop.png",
		"TƯƠNG SINH Ô LIỀN KỀ (+30% CÔNG, +25% THỦ, +3% HP/s)",
		Color(0.46, 0.98, 0.62)
	))

	var gen_pairs := [
		["kim", "thuy", "Kim sinh Thủy (Ô kề: +30% Công, +25% Thủ)"],
		["thuy", "moc", "Thủy sinh Mộc (Ô kề: +30% Công, +25% Thủ)"],
		["moc", "hoa", "Mộc sinh Hỏa (Ô kề: +30% Công, +25% Thủ)"],
		["hoa", "tho", "Hỏa sinh Thổ (Ô kề: +30% Công, +25% Thủ)"],
		["tho", "kim", "Thổ sinh Kim (Ô kề: +30% Công, +25% Thủ)"],
	]
	for pair in gen_pairs:
		gen_v.add_child(_make_element_relation_row(str(pair[0]), str(pair[1]), "SINH", Color(0.42, 0.96, 0.58), str(pair[2])))

	return box


func _build_tab_how_to_play() -> VBoxContainer:
	var box := VBoxContainer.new()
	box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	box.add_theme_constant_override("separation", 18)

	var deck_pnl := PanelContainer.new()
	deck_pnl.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("section", 22))
	box.add_child(deck_pnl)

	var deck_v := VBoxContainer.new()
	deck_v.add_theme_constant_override("separation", 14)
	deck_pnl.add_child(deck_v)

	deck_v.add_child(_make_section_header(
		"res://assets/ui_hud/icons/icon_cards_hand.png",
		"1. BỘ BÀI 15 LÁ & RÚT BÀI",
		Color(1.0, 0.88, 0.44)
	))

	var deck_lbl := Label.new()
	deck_lbl.text = (
		"• Mỗi người mang 15 thẻ bài vào trận.\n"
		+ "• Vòng 1 rút 5 thẻ. Mỗi vòng sau rút thêm +2 thẻ mới.\n"
		+ "• Vuốt trái/phải để xem bài trên tay, BẤM VÀO THẺ để rút thẻ nhô lên."
	)
	deck_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	deck_lbl.add_theme_font_size_override("font_size", 25)
	deck_lbl.add_theme_color_override("font_color", Color(0.94, 0.96, 1.0))
	deck_v.add_child(deck_lbl)

	var prep_pnl := PanelContainer.new()
	prep_pnl.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("section", 22))
	box.add_child(prep_pnl)

	var prep_v := VBoxContainer.new()
	prep_v.add_theme_constant_override("separation", 14)
	prep_pnl.add_child(prep_v)

	prep_v.add_child(_make_section_header(
		"res://assets/ui_hud/hud_bars/timer_prep_15s_compass.png",
		"2. PHA CHUẨN BỊ (15s) & GIAO CHIẾN (15s)",
		Color(0.48, 0.90, 1.0)
	))

	var prep_lbl := Label.new()
	prep_lbl.text = (
		"• LINH LỰC MỖI VÒNG: Mỗi vòng hồi +4 Linh Lực (tích trữ tối đa 6). Thẻ N / Item tốn 1, R tốn 2, S tốn 3, SSR tốn 4 Linh Lực. Nhặt lại bài đang úp hoàn trả 100% Linh Lực!\n"
		+ "• LIÊN KẾT Ô LIỀN KỀ: Đặt 2 thẻ Tương Sinh ở 2 ô sát nhau nhận +30% Công, +25% Giáp/K.Phép & +3% HP/s; đặt 2 thẻ Khắc nhau cạnh nhau bị phạt -20% Công & Tốc đánh!\n"
		+ "• VỊ TRÍ 10 Ô: 4 Ô Giữa (#4–#7 Tiền Tuyến) tăng +25% Máu & Khiên; 6 Ô Cánh (#1–#3, #8–#10 Hậu Phương) tăng +20% Tầm & Tốc đánh."
	)
	prep_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	prep_lbl.add_theme_font_size_override("font_size", 25)
	prep_lbl.add_theme_color_override("font_color", Color(0.94, 0.96, 1.0))
	prep_v.add_child(prep_lbl)

	return box


func _build_tab_combat_and_currencies() -> VBoxContainer:
	var box := VBoxContainer.new()
	box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	box.add_theme_constant_override("separation", 18)

	var combat_pnl := PanelContainer.new()
	combat_pnl.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("section", 22))
	box.add_child(combat_pnl)

	var cmb_v := VBoxContainer.new()
	cmb_v.add_theme_constant_override("separation", 14)
	combat_pnl.add_child(cmb_v)

	cmb_v.add_child(_make_section_header(
		"res://assets/ui_hud/hud_bars/timer_combat_15s_crossed_swords.png",
		"1. PHÁ TRỤ GÓC (100 HP)",
		Color(1.0, 0.56, 0.46)
	))

	var cmb_lbl := Label.new()
	cmb_lbl.text = (
		"• Khi đối thủ hết tướng trên bàn, tướng của bạn sẽ tiến thẳng vào Góc của đối thủ để trừ máu trực tiếp.\n"
		+ "• Ai về 0 HP sẽ bị loại. Người sống sót cuối cùng chiến thắng!"
	)
	cmb_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	cmb_lbl.add_theme_font_size_override("font_size", 25)
	cmb_lbl.add_theme_color_override("font_color", Color(0.94, 0.96, 1.0))
	cmb_v.add_child(cmb_lbl)

	var cur_pnl := PanelContainer.new()
	cur_pnl.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("section", 22))
	box.add_child(cur_pnl)

	var cur_v := VBoxContainer.new()
	cur_v.add_theme_constant_override("separation", 14)
	cur_pnl.add_child(cur_v)

	cur_v.add_child(_make_section_header(
		"res://assets/ui_hud/icons/icon_shop_chest.png",
		"2. VÀNG & KIM CƯƠNG (5 CẤP RƯƠNG)",
		Color(1.0, 0.88, 0.42)
	))

	var cur_lbl := Label.new()
	cur_lbl.text = (
		"• VÀNG (Coin): Mua Rương #1 (200), Rương #2 (500), Rương #3 (1000).\n"
		+ "• KIM CƯƠNG (KC): Mua Rương #4 Sử Thi (150 KC) & Rương #5 Thần Thoại (300 KC)."
	)
	cur_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	cur_lbl.add_theme_font_size_override("font_size", 25)
	cur_lbl.add_theme_color_override("font_color", Color(0.94, 0.96, 1.0))
	cur_v.add_child(cur_lbl)

	return box


func _make_section_header(icon_path: String, title_text: String, col: Color) -> HBoxContainer:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 12)

	var ico := TextureRect.new()
	ico.texture = GameState.tex(icon_path)
	ico.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	ico.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	ico.custom_minimum_size = Vector2(42, 42)
	row.add_child(ico)

	var lbl := Label.new()
	lbl.text = title_text
	lbl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	lbl.add_theme_font_size_override("font_size", 28)
	lbl.add_theme_color_override("font_color", col)
	row.add_child(lbl)

	return row


func _make_element_relation_row(elem_a: String, elem_b: String, verb: String, verb_col: Color, desc_text: String) -> PanelContainer:
	var pnl := PanelContainer.new()
	pnl.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("slot_gray", 10))

	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 12)
	pnl.add_child(row)

	var meta_a: Dictionary = GameState.ELEMENT_META[elem_a]
	var meta_b: Dictionary = GameState.ELEMENT_META[elem_b]

	row.add_child(_make_elem_badge(meta_a))

	var verb_lbl := Label.new()
	verb_lbl.text = verb
	verb_lbl.custom_minimum_size = Vector2(88, 0)
	verb_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	verb_lbl.add_theme_font_size_override("font_size", 23)
	verb_lbl.add_theme_color_override("font_color", verb_col)
	row.add_child(verb_lbl)

	row.add_child(_make_elem_badge(meta_b))

	var desc_lbl := Label.new()
	desc_lbl.text = desc_text
	desc_lbl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	desc_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	desc_lbl.add_theme_font_size_override("font_size", 23)
	desc_lbl.add_theme_color_override("font_color", Color(0.94, 0.96, 1.0))
	row.add_child(desc_lbl)

	return pnl


func _make_elem_badge(meta: Dictionary) -> HBoxContainer:
	var h := HBoxContainer.new()
	h.custom_minimum_size = Vector2(128, 40)
	h.add_theme_constant_override("separation", 8)

	var ico := TextureRect.new()
	ico.texture = GameState.tex(str(meta["icon"]))
	ico.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	ico.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	ico.custom_minimum_size = Vector2(36, 36)
	h.add_child(ico)

	var lbl := Label.new()
	lbl.text = str(meta["short"]).to_upper()
	lbl.add_theme_font_size_override("font_size", 23)
	lbl.add_theme_color_override("font_color", meta["color"])
	h.add_child(lbl)

	return h
