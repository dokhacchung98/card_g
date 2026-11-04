extends ColorRect

const CardWidget := preload("res://scripts/components/CardWidget.gd")

var current_card_id: String = "C001"
var current_element: String = "kim"

var card_widget: Control
var lbl_title: Label
var lbl_meta: Label
var lbl_skill: Label
var lbl_elem_mod: Label
var lbl_stats_summary: Label
var btn_toggle_deck: Button


func _init() -> void:
	size = Vector2(1080, 1920)
	color = Color(0.02, 0.03, 0.06, 0.88)
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	visible = false
	_build_ui()


func _build_ui() -> void:
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(980, 1440)
	panel.position = Vector2(50, 240)
	panel.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("dialog", 32))
	add_child(panel)

	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 20)
	panel.add_child(vbox)

	# Top Header
	var header := HBoxContainer.new()
	header.add_theme_constant_override("separation", 14)
	vbox.add_child(header)

	lbl_title = Label.new()
	lbl_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	lbl_title.clip_text = true
	lbl_title.add_theme_font_size_override("font_size", 32)
	lbl_title.add_theme_color_override("font_color", Color(1.0, 0.86, 0.32))
	header.add_child(lbl_title)

	var btn_close := Button.new()
	btn_close.text = "ĐÓNG"
	btn_close.custom_minimum_size = Vector2(160, 68)
	btn_close.add_theme_font_size_override("font_size", 25)
	GameState.apply_gui_button(btn_close, "wood", false)
	btn_close.pressed.connect(func(): visible = false)
	header.add_child(btn_close)

	# Body Row: Left HD Card + Right Clean Big-Font Info
	var body := HBoxContainer.new()
	body.add_theme_constant_override("separation", 24)
	body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	vbox.add_child(body)

	var left_col := VBoxContainer.new()
	left_col.alignment = BoxContainer.ALIGNMENT_CENTER
	left_col.add_theme_constant_override("separation", 14)
	body.add_child(left_col)

	card_widget = CardWidget.new()
	card_widget.custom_minimum_size = Vector2(420, 630)
	card_widget.show_lock_if_unowned = false
	left_col.add_child(card_widget)

	var right_scroll := ScrollContainer.new()
	right_scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	GameState.setup_touch_scroll(right_scroll)
	body.add_child(right_scroll)

	var right_col := VBoxContainer.new()
	right_col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right_col.custom_minimum_size = Vector2(440, 0)
	right_col.add_theme_constant_override("separation", 18)
	right_scroll.add_child(right_col)

	var meta_panel := PanelContainer.new()
	meta_panel.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("slot_active", 18))
	right_col.add_child(meta_panel)

	lbl_meta = Label.new()
	lbl_meta.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	lbl_meta.custom_minimum_size = Vector2(400, 0)
	lbl_meta.add_theme_font_size_override("font_size", 26)
	lbl_meta.add_theme_color_override("font_color", Color(0.72, 0.92, 1.0))
	meta_panel.add_child(lbl_meta)

	var skill_panel := PanelContainer.new()
	skill_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	skill_panel.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("header", 20))
	right_col.add_child(skill_panel)

	lbl_skill = Label.new()
	lbl_skill.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	lbl_skill.custom_minimum_size = Vector2(396, 0)
	lbl_skill.add_theme_font_size_override("font_size", 26)
	lbl_skill.add_theme_color_override("font_color", Color(1.0, 0.96, 0.86))
	skill_panel.add_child(lbl_skill)

	var elem_panel := PanelContainer.new()
	elem_panel.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("slot_active", 18))
	right_col.add_child(elem_panel)

	lbl_elem_mod = Label.new()
	lbl_elem_mod.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	lbl_elem_mod.custom_minimum_size = Vector2(400, 0)
	lbl_elem_mod.add_theme_font_size_override("font_size", 24)
	lbl_elem_mod.add_theme_color_override("font_color", Color(0.52, 0.98, 0.68))
	elem_panel.add_child(lbl_elem_mod)

	var stats_panel := PanelContainer.new()
	stats_panel.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("section", 18))
	right_col.add_child(stats_panel)

	lbl_stats_summary = Label.new()
	lbl_stats_summary.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	lbl_stats_summary.custom_minimum_size = Vector2(400, 0)
	lbl_stats_summary.add_theme_font_size_override("font_size", 25)
	lbl_stats_summary.add_theme_color_override("font_color", Color(0.98, 0.90, 0.72))
	stats_panel.add_child(lbl_stats_summary)

	# Bottom Action Bar
	btn_toggle_deck = Button.new()
	btn_toggle_deck.custom_minimum_size = Vector2(0, 92)
	btn_toggle_deck.add_theme_font_size_override("font_size", 28)
	GameState.apply_gui_button(btn_toggle_deck, "green", true, 28, 14)
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

	var energy_cost: int = GameState.get_card_energy_cost(current_card_id)
	lbl_title.text = "[%s] %s · Bậc %s" % [
		current_card_id,
		str(c.get("name", "")),
		rarity
	]
	lbl_meta.text = "Hệ %s  ·  %s  ·  Phí: %d Linh Lực\nSở hữu: %s" % [
		str(elem_meta.get("short", "")),
		str(c.get("role_label", "")),
		energy_cost,
		("x%d thẻ" % owned_cnt) if owned_cnt > 0 else "Chưa có",
	]

	var s_desc: String = str(c.get("skill_desc", "")).strip_edges()
	lbl_skill.text = "KỸ NĂNG:\n" + s_desc

	var gen_to: String = GameState.GEN_NEXT.get(current_element, "thuy")
	var cnt_to: String = GameState.COUNTER_TARGET.get(current_element, "moc")
	lbl_elem_mod.text = "NGŨ HÀNH & LIÊN KẾT Ô:\n• Sinh %s (Ô liền kề: +30%% Công, +25%% Thủ)\n• Khắc %s (+50%% Dame gây ra / -30%% Dame nhận)" % [
		str(GameState.ELEMENT_META[gen_to]["short"]),
		str(GameState.ELEMENT_META[cnt_to]["short"]),
	]

	if bool(c.get("is_item", false)):
		lbl_stats_summary.text = "VẬT PHẨM TỨC THÌ (Tốn 1 Linh Lực):\n• Mục tiêu: %s (Ưu tiên theo khu vực Ô đặt)\n• Dùng ngay khi bắt đầu trận & tự hủy thẻ." % str(c.get("auto_target", ""))
	else:
		var rg_c: String = str(c.get("role_group", "atk_phys"))
		var rec_slot := "Ô Giữa 4–7 (Tiền Tuyến: +25% HP & Khiên)" if (rg_c == "tanker" or (rg_c == "atk_phys" and float(c.get("range", 1.2)) < 2.2)) else "Ô Cánh 1–3, 8–10 (Hậu Phương: +20% Tầm & Tốc đánh)"
		lbl_stats_summary.text = (
			"CHỈ SỐ & VỊ TRÍ Ô:\n"
			+ "• Máu: %d   |   Dame: %d\n" % [int(c.get("hp", 0)), int(c.get("dame", 0))]
			+ "• Giáp: %d   |   K.Phép: %d   |   Tầm: %.1f\n" % [int(c.get("def", 0)), int(c.get("mdef", 0)), float(c.get("range", 1.2))]
			+ "• Gợi ý đặt: %s" % rec_slot
		)

	var in_deck := GameState.is_card_in_loadout(current_card_id, current_element)
	btn_toggle_deck.expand_icon = true
	if owned_cnt <= 0:
		btn_toggle_deck.icon = GameState.tex("res://assets/ui_hud/icons/icon_lock.png")
		btn_toggle_deck.text = "CHƯA SỞ HỮU THẺ NÀY"
		btn_toggle_deck.disabled = true
		GameState.apply_gui_button(btn_toggle_deck, "slate", true, 40, 14)
	elif in_deck:
		btn_toggle_deck.icon = GameState.tex("res://assets/ui_hud/icons/icon_cards_hand.png")
		btn_toggle_deck.text = "GỠ KHỎI BỘ 15 LÁ (%d/15)" % GameState.loadout_deck.size()
		btn_toggle_deck.disabled = false
		GameState.apply_gui_button(btn_toggle_deck, "red", true, 40, 14)
	else:
		btn_toggle_deck.icon = GameState.tex("res://assets/ui_hud/icons/icon_cards_hand.png")
		btn_toggle_deck.text = "CHỌN VÀO BỘ 15 LÁ (%d/15)" % GameState.loadout_deck.size()
		btn_toggle_deck.disabled = false
		GameState.apply_gui_button(btn_toggle_deck, "green", true, 40, 14)

	visible = true
