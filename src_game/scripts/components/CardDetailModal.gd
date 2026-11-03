extends ColorRect

const CardWidget := preload("res://scripts/components/CardWidget.gd")

var current_card_id: String = "C001"
var current_element: String = "kim"

var card_widget: Control
var lbl_title: Label
var lbl_meta: Label
var lbl_fixed_elem_info: Label
var lbl_skill: Label
var lbl_elem_mod: Label
var lbl_stats_summary: Label
var btn_toggle_deck: Button


func _init() -> void:
	size = Vector2(1080, 1920)
	color = Color(0.02, 0.03, 0.06, 0.86)
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	visible = false
	_build_ui()


func _build_ui() -> void:
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(960, 1460)
	panel.position = Vector2(60, 230)
	panel.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("dialog", 28))
	add_child(panel)

	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 16)
	panel.add_child(vbox)

	# Top Header
	var header := HBoxContainer.new()
	vbox.add_child(header)

	lbl_title = Label.new()
	lbl_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	lbl_title.add_theme_font_size_override("font_size", 30)
	lbl_title.add_theme_color_override("font_color", Color(0.98, 0.82, 0.28))
	header.add_child(lbl_title)

	var btn_close := Button.new()
	btn_close.text = "ĐÓNG"
	btn_close.custom_minimum_size = Vector2(140, 52)
	btn_close.add_theme_font_size_override("font_size", 20)
	GameState.apply_gui_button(btn_close, "wood", false)
	btn_close.pressed.connect(func(): visible = false)
	header.add_child(btn_close)

	# Body Row: Left HD Card + Right Detailed Stats
	var body := HBoxContainer.new()
	body.add_theme_constant_override("separation", 24)
	body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	vbox.add_child(body)

	var left_col := VBoxContainer.new()
	left_col.add_theme_constant_override("separation", 12)
	body.add_child(left_col)

	card_widget = CardWidget.new()
	card_widget.custom_minimum_size = Vector2(420, 630)
	card_widget.show_lock_if_unowned = false
	left_col.add_child(card_widget)

	var fixed_elem_panel := PanelContainer.new()
	fixed_elem_panel.custom_minimum_size = Vector2(420, 0)
	fixed_elem_panel.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("slot_active", 14))
	left_col.add_child(fixed_elem_panel)

	lbl_fixed_elem_info = Label.new()
	lbl_fixed_elem_info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	lbl_fixed_elem_info.custom_minimum_size = Vector2(388, 0)
	lbl_fixed_elem_info.add_theme_font_size_override("font_size", 16)
	lbl_fixed_elem_info.add_theme_color_override("font_color", Color(0.90, 0.94, 0.98))
	fixed_elem_panel.add_child(lbl_fixed_elem_info)

	var right_scroll := ScrollContainer.new()
	right_scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	GameState.setup_touch_scroll(right_scroll)
	body.add_child(right_scroll)

	var right_col := VBoxContainer.new()
	right_col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right_col.custom_minimum_size = Vector2(420, 0)
	right_col.add_theme_constant_override("separation", 14)
	right_scroll.add_child(right_col)

	lbl_meta = Label.new()
	lbl_meta.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	lbl_meta.custom_minimum_size = Vector2(420, 0)
	lbl_meta.add_theme_font_size_override("font_size", 20)
	lbl_meta.add_theme_color_override("font_color", Color(0.68, 0.88, 1.0))
	right_col.add_child(lbl_meta)

	# Responsive Skill Description Panel (no skill_name header line — only concise skill description)
	var skill_panel := PanelContainer.new()
	skill_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	skill_panel.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("header", 16))
	right_col.add_child(skill_panel)

	lbl_skill = Label.new()
	lbl_skill.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	lbl_skill.custom_minimum_size = Vector2(376, 0)
	lbl_skill.add_theme_font_size_override("font_size", 21)
	lbl_skill.add_theme_color_override("font_color", Color(0.97, 0.96, 0.90))
	skill_panel.add_child(lbl_skill)

	lbl_elem_mod = Label.new()
	lbl_elem_mod.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	lbl_elem_mod.custom_minimum_size = Vector2(420, 0)
	lbl_elem_mod.add_theme_font_size_override("font_size", 18)
	lbl_elem_mod.add_theme_color_override("font_color", Color(0.45, 0.95, 0.62))
	right_col.add_child(lbl_elem_mod)

	lbl_stats_summary = Label.new()
	lbl_stats_summary.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	lbl_stats_summary.custom_minimum_size = Vector2(420, 0)
	lbl_stats_summary.add_theme_font_size_override("font_size", 18)
	lbl_stats_summary.add_theme_color_override("font_color", Color(0.92, 0.86, 0.72))
	right_col.add_child(lbl_stats_summary)

	# Bottom Action Bar
	btn_toggle_deck = Button.new()
	btn_toggle_deck.custom_minimum_size = Vector2(0, 74)
	btn_toggle_deck.add_theme_font_size_override("font_size", 22)
	GameState.apply_gui_button(btn_toggle_deck, "green", true, 24, 12)
	btn_toggle_deck.pressed.connect(func():
		GameState.toggle_card_in_loadout(current_card_id, current_element)
		show_card(current_card_id, current_element)
	)
	vbox.add_child(btn_toggle_deck)


func show_card(card_id: String, elem_override: String = "") -> void:
	current_card_id = GameState.get_base_card_id(card_id)
	current_element = elem_override if not elem_override.is_empty() else GameState.get_card_element(card_id)
	var c := GameState.get_card(current_card_id)
	if c.is_empty():
		return

	card_widget.setup(current_card_id, current_element, false, true)
	var rarity: String = str(c.get("rarity", "N"))
	var owned_cnt: int = GameState.get_card_owned_count(current_card_id, current_element)
	var elem_meta: Dictionary = GameState.ELEMENT_META.get(current_element, GameState.ELEMENT_META["kim"])

	var elem_status_parts: Array = []
	for el in GameState.ELEMENTS:
		var ecnt := GameState.get_card_owned_count(current_card_id, el)
		var eshort: String = str(GameState.ELEMENT_META[el]["short"])
		elem_status_parts.append("%s: x%d" % [eshort, ecnt])

	lbl_fixed_elem_info.text = (
		"• Thuộc tính cố định khi mở thẻ: %s (Không thể tự đổi hệ)\n" % str(elem_meta.get("name", ""))
		+ "• Kho 500 Thẻ (%s theo 5 Hệ):  %s" % [current_card_id, "  |  ".join(elem_status_parts)]
	)

	lbl_title.text = "[%s · %s] %s — Bậc %s" % [
		current_card_id,
		str(elem_meta.get("short", "")).to_upper(),
		str(c.get("name", "")),
		rarity
	]
	lbl_meta.text = "• Phân loại: %s (%s)\n• Trạng thái thẻ (%s - %s): %s" % [
		str(c.get("role_label", "")),
		str(c.get("sub_tag", "")),
		current_card_id,
		str(elem_meta.get("name", "")),
		("Đã sở hữu x%d bản sao" % owned_cnt) if owned_cnt > 0 else "Chưa sở hữu hệ này (Mở Rương để thu thập)",
	]

	# Only display the concise skill description (no skill_name header line), with responsive font sizing
	var s_desc: String = str(c.get("skill_desc", "")).strip_edges()
	var desc_len: int = s_desc.length()
	var resp_fsize: int = 21 if desc_len <= 60 else (19 if desc_len <= 85 else 17)
	lbl_skill.add_theme_font_size_override("font_size", resp_fsize)
	lbl_skill.text = s_desc

	var gen_to: String = GameState.GEN_NEXT.get(current_element, "thuy")
	var cnt_to: String = GameState.COUNTER_TARGET.get(current_element, "moc")
	lbl_elem_mod.text = "ĐẶC TÍNH HỆ %s (CỐ ĐỊNH TRÊN THẺ):\n• %s\n• Tương Sinh: Sinh %s (+15%% Công & Hồi 2%% HP/s)\n• Tương Khắc: Khắc %s (+25%% Sát thương đầu ra)" % [
		str(elem_meta.get("short", "")).to_upper(),
		str(elem_meta.get("modifier_desc", "")),
		str(GameState.ELEMENT_META[gen_to]["short"]),
		str(GameState.ELEMENT_META[cnt_to]["short"]),
	]

	if bool(c.get("is_item", false)):
		lbl_stats_summary.text = "THẺ VẬT PHẨM TỨC THỜI:\n• Mục tiêu: %s\n• Cơ chế: Kích hoạt ngay khi lật bài rồi giải phóng ô trống." % str(c.get("auto_target", ""))
	else:
		lbl_stats_summary.text = (
			"BỘ 9 CHỈ SỐ CHIẾN ĐẤU:\n"
			+ "• Máu (HP): %d   |   Năng lượng (Mana): %d   |   Khiên gốc: %d\n" % [int(c.get("hp", 0)), int(c.get("mana", 0)), int(c.get("shield", 0))]
			+ "• Dame: %d   |   Tốc đánh (ASPD): %.2f/s   |   Tầm đánh: %.1f (%s)\n" % [
				int(c.get("dame", 0)),
				float(c.get("aspd", 1.0)),
				float(c.get("range", 1.2)),
				"Đánh Xa" if bool(c.get("is_ranged", false)) else "Cận Chiến"
			]
			+ "• Giáp Vật Lý: %d   |   Kháng Phép: %d   |   Tốc Chạy (MSPD): %d" % [
				int(c.get("def", 0)), int(c.get("mdef", 0)), int(c.get("mspd", 100))
			]
		)

	var in_deck := GameState.is_card_in_loadout(current_card_id, current_element)
	btn_toggle_deck.expand_icon = true
	if owned_cnt <= 0:
		btn_toggle_deck.icon = GameState.tex("res://assets/ui_hud/icons/icon_lock.png")
		btn_toggle_deck.text = "CHƯA SỞ HỮU THẺ HỆ %s NÀY (MỞ RƯƠNG ĐỂ THU THẬP)" % str(elem_meta.get("short", "")).to_upper()
		btn_toggle_deck.disabled = true
		GameState.apply_gui_button(btn_toggle_deck, "slate", true, 48, 12)
	elif in_deck:
		btn_toggle_deck.icon = GameState.tex("res://assets/ui_hud/icons/icon_cards_hand.png")
		btn_toggle_deck.text = "GỠ KHỎI BỘ BÀI XUẤT CHIẾN 15 LÁ (Đang có %d/15)" % GameState.loadout_deck.size()
		btn_toggle_deck.disabled = false
		GameState.apply_gui_button(btn_toggle_deck, "red", true, 48, 12)
	else:
		btn_toggle_deck.icon = GameState.tex("res://assets/ui_hud/icons/icon_cards_hand.png")
		btn_toggle_deck.text = "ĐƯA VÀO BỘ BÀI XUẤT CHIẾN 15 LÁ (Đang có %d/15)" % GameState.loadout_deck.size()
		btn_toggle_deck.disabled = false
		GameState.apply_gui_button(btn_toggle_deck, "green", true, 48, 12)

	visible = true
