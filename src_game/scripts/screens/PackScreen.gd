extends Control

const CardWidget := preload("res://scripts/components/CardWidget.gd")

var lbl_pack_count: Label
var lbl_selected_pack_title: Label
var lbl_rates: Label
var lbl_pull_summary: Label
var pack_sprite: TextureRect
var btn_buy_pack: Button
var btn_open_pack: Button
var pack_tab_btns: Dictionary = {}
var results_grid: GridContainer

# Full-screen Pack Opening Ceremony Overlay nodes
var ceremony_overlay: ColorRect
var ceremony_pack_stage: Control
var ceremony_seal_bg: TextureRect
var ceremony_pack_sprite: TextureRect
var ceremony_pack_label: Label
var ceremony_cards_stage: VBoxContainer
var ceremony_title_lbl: Label
var ceremony_status_lbl: Label
var ceremony_cards_grid: GridContainer
var btn_flip_all: Button
var btn_collect_close: Button
var white_flash_rect: ColorRect

var ceremony_card_widgets: Array[Control] = []
var current_pulled_items: Array = []
var current_pull_counts: Dictionary = {}
var is_animating: bool = false
var pack_frames: Array[Texture2D] = []


func _init() -> void:
	size = Vector2(1080, 1920)
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for f_name in ["pack_0_sealed.png", "pack_1_cracking.png", "pack_2_ripping.png", "pack_3_burst_open.png"]:
		var t := GameState.tex("res://assets/ui_hud/gacha_pack/" + f_name)
		if t:
			pack_frames.append(t)
	_build_ui()


func _ready() -> void:
	GameState.state_changed.connect(refresh_header)
	refresh_header()


func _build_ui() -> void:
	var bg_tex := TextureRect.new()
	bg_tex.texture = GameState.tex("res://assets/ui_hud/gui/home_sanctuary_bg_1080x1920.png")
	bg_tex.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	bg_tex.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	bg_tex.position = Vector2.ZERO
	bg_tex.size = Vector2(1080, 1920)
	add_child(bg_tex)
	bg_tex.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)

	var bg_overlay := ColorRect.new()
	bg_overlay.color = Color(0.03, 0.04, 0.08, 0.62)
	bg_overlay.position = Vector2.ZERO
	bg_overlay.size = Vector2(1080, 1920)
	add_child(bg_overlay)
	bg_overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)

	var main_vbox := VBoxContainer.new()
	main_vbox.position = Vector2(24, 18)
	main_vbox.size = Vector2(1032, 1884)
	main_vbox.add_theme_constant_override("separation", 12)
	add_child(main_vbox)

	# 1. Top Bar with Ornate Back-to-Home Button
	var top_panel := PanelContainer.new()
	top_panel.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("header", 16))
	main_vbox.add_child(top_panel)

	var top_hbox := HBoxContainer.new()
	top_hbox.add_theme_constant_override("separation", 14)
	top_panel.add_child(top_hbox)

	var btn_back := _make_back_home_button()
	top_hbox.add_child(btn_back)

	var title_vbox := VBoxContainer.new()
	title_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top_hbox.add_child(title_vbox)

	var lbl_t := Label.new()
	lbl_t.text = "ĐÀI MỞ RƯƠNG (10 THẺ)"
	lbl_t.clip_text = true
	lbl_t.add_theme_font_size_override("font_size", 28)
	lbl_t.add_theme_color_override("font_color", Color(0.98, 0.84, 0.28))
	title_vbox.add_child(lbl_t)

	lbl_pack_count = Label.new()
	lbl_pack_count.clip_text = true
	lbl_pack_count.add_theme_font_size_override("font_size", 22)
	lbl_pack_count.add_theme_color_override("font_color", Color(0.55, 0.94, 0.68))
	title_vbox.add_child(lbl_pack_count)

	var btn_guide := Button.new()
	btn_guide.text = "LUẬT"
	btn_guide.icon = GameState.tex("res://assets/ui_hud/icons/icon_guide_book.png")
	btn_guide.expand_icon = true
	btn_guide.custom_minimum_size = Vector2(168, 66)
	btn_guide.add_theme_font_size_override("font_size", 24)
	GameState.apply_gui_button(btn_guide, "purple", false, 12, 8)
	btn_guide.pressed.connect(func():
		GameState.emit_signal("guide_requested", 2)
	)
	top_hbox.add_child(btn_guide)

	# 2. 5-Pack Tier Selector Row (Pack #1 .. Pack #5)
	var tabs_hbox := HBoxContainer.new()
	tabs_hbox.add_theme_constant_override("separation", 10)
	main_vbox.add_child(tabs_hbox)

	for p_id in range(1, 6):
		var b := Button.new()
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.custom_minimum_size = Vector2(0, 104)
		b.clip_text = true
		b.add_theme_font_size_override("font_size", 22)
		var captured_id := p_id
		b.pressed.connect(func():
			if not is_animating:
				GameState.selected_pack_type = captured_id
				GameState.save_game()
				refresh_header()
		)
		tabs_hbox.add_child(b)
		pack_tab_btns[p_id] = b

	# 3. Pack Stage Box (Selected Pack Preview + Exact Tier Probability Table)
	var stage_panel := PanelContainer.new()
	stage_panel.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("section", 18))
	main_vbox.add_child(stage_panel)

	var stage_hbox := HBoxContainer.new()
	stage_hbox.add_theme_constant_override("separation", 20)
	stage_hbox.alignment = BoxContainer.ALIGNMENT_CENTER
	stage_panel.add_child(stage_hbox)

	pack_sprite = TextureRect.new()
	if not pack_frames.is_empty():
		pack_sprite.texture = pack_frames[0]
	pack_sprite.custom_minimum_size = Vector2(180, 180)
	pack_sprite.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	pack_sprite.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	pack_sprite.pivot_offset = Vector2(90, 90)
	stage_hbox.add_child(pack_sprite)

	var ctrl_vbox := VBoxContainer.new()
	ctrl_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ctrl_vbox.alignment = BoxContainer.ALIGNMENT_CENTER
	ctrl_vbox.add_theme_constant_override("separation", 10)
	stage_hbox.add_child(ctrl_vbox)

	lbl_selected_pack_title = Label.new()
	lbl_selected_pack_title.clip_text = true
	lbl_selected_pack_title.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	lbl_selected_pack_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	lbl_selected_pack_title.add_theme_font_size_override("font_size", 26)
	ctrl_vbox.add_child(lbl_selected_pack_title)

	lbl_rates = Label.new()
	lbl_rates.clip_text = true
	lbl_rates.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	lbl_rates.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	lbl_rates.add_theme_font_size_override("font_size", 22)
	lbl_rates.add_theme_color_override("font_color", Color(0.84, 0.90, 0.96))
	ctrl_vbox.add_child(lbl_rates)

	var action_btns_row := HBoxContainer.new()
	action_btns_row.add_theme_constant_override("separation", 12)
	ctrl_vbox.add_child(action_btns_row)

	btn_buy_pack = Button.new()
	btn_buy_pack.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	btn_buy_pack.custom_minimum_size = Vector2(0, 76)
	btn_buy_pack.clip_text = true
	btn_buy_pack.add_theme_font_size_override("font_size", 24)
	btn_buy_pack.pressed.connect(_on_buy_pack_pressed)
	action_btns_row.add_child(btn_buy_pack)

	btn_open_pack = Button.new()
	btn_open_pack.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	btn_open_pack.custom_minimum_size = Vector2(0, 76)
	btn_open_pack.clip_text = true
	btn_open_pack.add_theme_font_size_override("font_size", 24)
	GameState.apply_gui_button(btn_open_pack, "gold", false)
	btn_open_pack.pressed.connect(_on_open_pack_pressed)
	action_btns_row.add_child(btn_open_pack)

	lbl_pull_summary = Label.new()
	lbl_pull_summary.clip_text = true
	lbl_pull_summary.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	lbl_pull_summary.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	lbl_pull_summary.text = "Chọn Rương và bấm MỞ RƯƠNG để nhận 10 thẻ!"
	lbl_pull_summary.add_theme_font_size_override("font_size", 22)
	lbl_pull_summary.add_theme_color_override("font_color", Color(0.98, 0.84, 0.36))
	ctrl_vbox.add_child(lbl_pull_summary)

	# 4. Last-Pulled 10-Card History Grid on main screen (Large 3-Column Grid + Touch Scroll)
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	GameState.setup_touch_scroll(scroll)
	main_vbox.add_child(scroll)

	var grid_center_bg := HBoxContainer.new()
	grid_center_bg.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	grid_center_bg.alignment = BoxContainer.ALIGNMENT_CENTER
	grid_center_bg.mouse_filter = Control.MOUSE_FILTER_PASS
	scroll.add_child(grid_center_bg)

	results_grid = GridContainer.new()
	results_grid.columns = 3
	results_grid.add_theme_constant_override("h_separation", 18)
	results_grid.add_theme_constant_override("v_separation", 18)
	results_grid.mouse_filter = Control.MOUSE_FILTER_PASS
	grid_center_bg.add_child(results_grid)

	# 5. Build Full-Screen Black Pack Opening Ceremony & Interactive Flip Overlay
	_build_ceremony_overlay()


func _build_ceremony_overlay() -> void:
	ceremony_overlay = ColorRect.new()
	ceremony_overlay.color = Color(0.01, 0.01, 0.02, 0.97)
	ceremony_overlay.position = Vector2.ZERO
	ceremony_overlay.size = Vector2(1080, 1920)
	ceremony_overlay.mouse_filter = Control.MOUSE_FILTER_STOP
	ceremony_overlay.visible = false
	add_child(ceremony_overlay)

	# Stage A: Pack rising from bottom to center + opening animation
	ceremony_pack_stage = Control.new()
	ceremony_pack_stage.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	ceremony_pack_stage.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ceremony_overlay.add_child(ceremony_pack_stage)

	ceremony_seal_bg = TextureRect.new()
	ceremony_seal_bg.texture = GameState.tex("res://assets/board_map/props/prop_4_wuxing_synergy_seal.png")
	ceremony_seal_bg.position = Vector2(220, 620)
	ceremony_seal_bg.size = Vector2(640, 640)
	ceremony_seal_bg.pivot_offset = Vector2(320, 320)
	ceremony_seal_bg.modulate = Color(1, 1, 1, 0.30)
	ceremony_seal_bg.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	ceremony_seal_bg.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	ceremony_pack_stage.add_child(ceremony_seal_bg)

	ceremony_pack_sprite = TextureRect.new()
	if not pack_frames.is_empty():
		ceremony_pack_sprite.texture = pack_frames[0]
	ceremony_pack_sprite.position = Vector2(310, 1960)
	ceremony_pack_sprite.size = Vector2(460, 460)
	ceremony_pack_sprite.pivot_offset = Vector2(230, 230)
	ceremony_pack_sprite.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	ceremony_pack_sprite.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	ceremony_pack_stage.add_child(ceremony_pack_sprite)

	ceremony_pack_label = Label.new()
	ceremony_pack_label.position = Vector2(60, 440)
	ceremony_pack_label.size = Vector2(960, 80)
	ceremony_pack_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	ceremony_pack_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	ceremony_pack_label.add_theme_font_size_override("font_size", 32)
	ceremony_pack_label.add_theme_color_override("font_color", Color(1.0, 0.86, 0.32))
	ceremony_pack_stage.add_child(ceremony_pack_label)

	# Stage B: 10 Face-Down Cards Interactive Flip Grid + Bottom Action Buttons
	ceremony_cards_stage = VBoxContainer.new()
	ceremony_cards_stage.position = Vector2(28, 64)
	ceremony_cards_stage.size = Vector2(1024, 1792)
	ceremony_cards_stage.alignment = BoxContainer.ALIGNMENT_CENTER
	ceremony_cards_stage.add_theme_constant_override("separation", 20)
	ceremony_cards_stage.visible = false
	ceremony_overlay.add_child(ceremony_cards_stage)

	var head_panel := PanelContainer.new()
	head_panel.custom_minimum_size = Vector2(980, 0)
	head_panel.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	head_panel.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("dialog", 18))
	ceremony_cards_stage.add_child(head_panel)

	var head_vbox := VBoxContainer.new()
	head_vbox.custom_minimum_size = Vector2(936, 0)
	head_vbox.add_theme_constant_override("separation", 6)
	head_panel.add_child(head_vbox)

	ceremony_title_lbl = Label.new()
	ceremony_title_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	ceremony_title_lbl.clip_text = true
	ceremony_title_lbl.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	ceremony_title_lbl.add_theme_font_size_override("font_size", 30)
	ceremony_title_lbl.add_theme_color_override("font_color", Color(1.0, 0.86, 0.32))
	head_vbox.add_child(ceremony_title_lbl)

	ceremony_status_lbl = Label.new()
	ceremony_status_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	ceremony_status_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	ceremony_status_lbl.custom_minimum_size = Vector2(920, 0)
	ceremony_status_lbl.add_theme_font_size_override("font_size", 24)
	ceremony_status_lbl.add_theme_color_override("font_color", Color(0.76, 0.90, 1.0))
	head_vbox.add_child(ceremony_status_lbl)

	var grid_center := HBoxContainer.new()
	grid_center.alignment = BoxContainer.ALIGNMENT_CENTER
	ceremony_cards_stage.add_child(grid_center)

	ceremony_cards_grid = GridContainer.new()
	ceremony_cards_grid.columns = 5
	ceremony_cards_grid.add_theme_constant_override("h_separation", 14)
	ceremony_cards_grid.add_theme_constant_override("v_separation", 18)
	grid_center.add_child(ceremony_cards_grid)

	# Bottom Buttons Row: "LẬT TẤT CẢ" & "THU VÀO KHO"
	var btn_row := HBoxContainer.new()
	btn_row.alignment = BoxContainer.ALIGNMENT_CENTER
	btn_row.add_theme_constant_override("separation", 18)
	ceremony_cards_stage.add_child(btn_row)

	btn_flip_all = _make_ceremony_ornate_button(
		"res://assets/ui_hud/gui/btn_nav_gacha.png",
		Vector2(450, 124),
		"LẬT TẤT CẢ 10 THẺ",
		"",
		Color(0.98, 0.86, 1.0),
		_on_flip_all_pressed
	)
	btn_row.add_child(btn_flip_all)

	btn_collect_close = _make_ceremony_ornate_button(
		"res://assets/ui_hud/gui/btn_play_battle.png",
		Vector2(470, 124),
		"THU VÀO KHO (ĐÓNG)",
		"",
		Color(1.0, 0.92, 0.48),
		_on_close_ceremony_pressed
	)
	btn_row.add_child(btn_collect_close)

	# Full-screen White Flash Rect (on top of everything inside ceremony_overlay)
	white_flash_rect = ColorRect.new()
	white_flash_rect.color = Color(1, 1, 1, 0.0)
	white_flash_rect.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	white_flash_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	white_flash_rect.visible = false
	ceremony_overlay.add_child(white_flash_rect)


func _make_ceremony_ornate_button(
	tex_path: String,
	min_sz: Vector2,
	title_txt: String,
	_sub_txt: String,
	title_col: Color,
	on_click: Callable
) -> Button:
	var b := Button.new()
	b.custom_minimum_size = min_sz
	b.focus_mode = Control.FOCUS_NONE
	b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	var sb_n := StyleBoxTexture.new()
	sb_n.texture = GameState.tex(tex_path)
	var sb_h := sb_n.duplicate() as StyleBoxTexture
	sb_h.modulate_color = Color(1.08, 1.08, 1.08, 1.0)
	var sb_p := sb_n.duplicate() as StyleBoxTexture
	sb_p.modulate_color = Color(0.88, 0.88, 0.90, 1.0)
	b.add_theme_stylebox_override("normal", sb_n)
	b.add_theme_stylebox_override("hover", sb_h)
	b.add_theme_stylebox_override("pressed", sb_p)
	b.pressed.connect(on_click)

	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	margin.add_theme_constant_override("margin_left", 84)
	margin.add_theme_constant_override("margin_right", 28)
	margin.add_theme_constant_override("margin_top", 14)
	margin.add_theme_constant_override("margin_bottom", 14)
	margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	b.add_child(margin)

	var l1 := Label.new()
	l1.text = title_txt
	l1.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l1.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l1.clip_text = true
	l1.add_theme_font_size_override("font_size", 28)
	l1.add_theme_color_override("font_color", title_col)
	l1.add_theme_color_override("font_outline_color", Color(0.02, 0.01, 0.03, 0.98))
	l1.add_theme_constant_override("outline_size", 5)
	l1.mouse_filter = Control.MOUSE_FILTER_IGNORE
	margin.add_child(l1)

	return b


func _make_back_home_button() -> Button:
	var b := Button.new()
	b.text = "SẢNH"
	b.custom_minimum_size = Vector2(168, 66)
	b.add_theme_font_size_override("font_size", 24)
	b.add_theme_color_override("font_color", Color(1.0, 0.92, 0.65))
	GameState.apply_gui_button(b, "back_home", false, 44, 8)
	b.pressed.connect(func():
		if not is_animating:
			GameState.emit_signal("screen_requested", "home")
	)
	return b


func refresh_header() -> void:
	if not is_inside_tree():
		return
	var sel_id := clampi(GameState.selected_pack_type, 1, 5)
	var sel_meta: Dictionary = GameState.PACK_TYPES[sel_id]
	var sel_cnt := GameState.get_pack_type_count(sel_id)

	lbl_pack_count.text = "Vàng: %d · KC: %d · Rương: %d" % [
		GameState.gold,
		GameState.diamonds,
		GameState.pack_count
	]

	var tab_variants := {1: "wood", 2: "green", 3: "slate", 4: "purple", 5: "gold"}
	for p_id in range(1, 6):
		var b: Button = pack_tab_btns[p_id]
		var pm: Dictionary = GameState.PACK_TYPES[p_id]
		var cnt := GameState.get_pack_type_count(p_id)
		var is_sel := (p_id == sel_id)
		var p_col: Color = pm["color"]
		var price_val: int = int(pm.get("price", 200))
		var cur_label: String = "KC" if str(pm.get("currency", "coin")) == "diamond" else "Vàng"
		b.icon = null
		b.text = "RƯƠNG #%d [x%d]\n%d %s" % [
			p_id,
			cnt,
			price_val,
			cur_label
		]
		GameState.apply_gui_button(b, str(tab_variants.get(p_id, "gold")) if is_sel else "slate", false, 8, 8)
		b.add_theme_color_override("font_color", Color(1.0, 0.97, 0.85) if is_sel else p_col)

	var sel_price: int = int(sel_meta.get("price", 200))
	var sel_cur_name: String = "KC" if str(sel_meta.get("currency", "coin")) == "diamond" else "Vàng"
	var is_diamond_pack: bool = str(sel_meta.get("currency", "coin")) == "diamond"
	lbl_selected_pack_title.text = "%s (Đang có: x%d)" % [sel_meta["name"], sel_cnt]
	lbl_selected_pack_title.add_theme_color_override("font_color", sel_meta["color"])

	lbl_rates.text = "Tỷ lệ: %s" % sel_meta["rate_text"]

	if pack_sprite:
		pack_sprite.self_modulate = sel_meta["tint"]

	if not is_animating:
		if btn_buy_pack:
			btn_buy_pack.icon = GameState.tex(str(sel_meta.get("currency_icon", "res://assets/ui_hud/icons/icon_coin_gold.png")))
			btn_buy_pack.expand_icon = true
			btn_buy_pack.text = "MUA +1 (%d %s)" % [sel_price, sel_cur_name]
			GameState.apply_gui_button(btn_buy_pack, "purple" if is_diamond_pack else "green", false, 12, 8)
			btn_buy_pack.add_theme_color_override("font_color", Color(0.86, 0.96, 1.0) if is_diamond_pack else Color(1.0, 0.96, 0.80))

		btn_open_pack.disabled = (sel_cnt <= 0)
		btn_open_pack.icon = GameState.tex("res://assets/ui_hud/icons/icon_star_new.png")
		btn_open_pack.expand_icon = true
		if sel_cnt <= 0:
			btn_open_pack.text = "HẾT RƯƠNG"
		else:
			btn_open_pack.text = "MỞ RƯƠNG (x%d)" % sel_cnt


func _on_buy_pack_pressed() -> void:
	if is_animating:
		return
	var sel_id := clampi(GameState.selected_pack_type, 1, 5)
	var res: Dictionary = GameState.buy_pack(sel_id, 1)
	lbl_pull_summary.text = str(res.get("msg", ""))
	if bool(res.get("ok", false)):
		lbl_pull_summary.add_theme_color_override("font_color", Color(0.52, 0.98, 0.68))
	else:
		lbl_pull_summary.add_theme_color_override("font_color", Color(1.0, 0.52, 0.48))
	refresh_header()


func _on_open_pack_pressed() -> void:
	var sel_id := clampi(GameState.selected_pack_type, 1, 5)
	if is_animating or GameState.get_pack_type_count(sel_id) <= 0:
		return
	is_animating = true
	btn_open_pack.disabled = true

	# Auto-save pulled 10 cards into Collection immediately
	current_pulled_items = GameState.open_gacha_pack(sel_id)
	current_pull_counts = {"SSR": 0, "S": 0, "R": 0, "N": 0, "NEW": 0}
	for item in current_pulled_items:
		var tier: String = str(item["rarity"])
		current_pull_counts[tier] = int(current_pull_counts.get(tier, 0)) + 1
		if bool(item["is_new"]):
			current_pull_counts["NEW"] += 1

	var sel_meta: Dictionary = GameState.PACK_TYPES[sel_id]

	# 1. Show Full-Screen Black Overlay & Pack Rising from Bottom to Center
	ceremony_overlay.visible = true
	ceremony_pack_stage.visible = true
	ceremony_cards_stage.visible = false
	white_flash_rect.visible = false

	if not pack_frames.is_empty():
		ceremony_pack_sprite.texture = pack_frames[0]
	ceremony_pack_sprite.self_modulate = sel_meta["tint"]
	ceremony_pack_sprite.position = Vector2(310, 1960)
	ceremony_pack_sprite.scale = Vector2(0.85, 0.85)
	ceremony_pack_sprite.rotation_degrees = 0.0
	ceremony_seal_bg.rotation_degrees = 0.0
	ceremony_pack_label.text = "ĐANG TRIỆU HỒI %s..." % str(sel_meta["name"]).to_upper()

	var tw_rise := create_tween().set_parallel(true)
	tw_rise.tween_property(ceremony_pack_sprite, "position", Vector2(310, 710), 0.52).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw_rise.tween_property(ceremony_pack_sprite, "scale", Vector2(1.0, 1.0), 0.52).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw_rise.tween_property(ceremony_seal_bg, "rotation_degrees", 90.0, 0.52)
	await tw_rise.finished

	# 2. Play 4-Frame Pack Opening Animation at Center of Screen
	var stage_texts := [
		"KÍCH HOẠT ẤN CHÚ NGŨ HÀNH...",
		"RẠN NỨT PHONG ẤN CỔ NGỮ...",
		"XÉ ĐỈNH RƯƠNG BÀI...",
		"BUNG NỔ HÀO QUANG — 10 TẤM THẺ XUẤT HIỆN!"
	]
	for idx in range(pack_frames.size()):
		ceremony_pack_sprite.texture = pack_frames[idx]
		ceremony_pack_label.text = stage_texts[idx]
		var tw_step := create_tween().set_parallel(true)
		var target_sc := 1.0 + idx * 0.10
		var target_rot := (-7.0 if idx % 2 == 1 else 7.0) if idx < 3 else 0.0
		tw_step.tween_property(ceremony_pack_sprite, "scale", Vector2(target_sc, target_sc), 0.20)
		tw_step.tween_property(ceremony_pack_sprite, "rotation_degrees", target_rot, 0.20)
		tw_step.tween_property(ceremony_seal_bg, "rotation_degrees", 90.0 + (idx + 1) * 65.0, 0.20)
		await tw_step.finished

	# 3. Full-Screen White Flash -> Transition to 10 Face-Down Cards
	white_flash_rect.visible = true
	white_flash_rect.color = Color(1, 1, 1, 0.0)
	var tw_flash_in := create_tween()
	tw_flash_in.tween_property(white_flash_rect, "color:a", 1.0, 0.16).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	await tw_flash_in.finished

	# Populate the 10 Face-Down Cards on the Black Overlay (and behind on the main screen)
	_populate_ceremony_and_background_cards(sel_id)
	ceremony_pack_stage.visible = false
	ceremony_cards_stage.visible = true

	var tw_flash_out := create_tween()
	tw_flash_out.tween_property(white_flash_rect, "color:a", 0.0, 0.38).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	await tw_flash_out.finished
	white_flash_rect.visible = false


func _populate_ceremony_and_background_cards(sel_id: int) -> void:
	for ch in ceremony_cards_grid.get_children():
		ch.queue_free()
	for ch in results_grid.get_children():
		ch.queue_free()
	ceremony_card_widgets.clear()

	var p_short: String = str(GameState.PACK_TYPES[sel_id]["short_name"])
	ceremony_title_lbl.text = "KHAI MỞ %s — 10 TẤM THẺ CỔ NGỮ" % p_short

	for item in current_pulled_items:
		var cid: String = str(item["card_id"])
		var elem: String = str(item["element"])
		var is_new: bool = bool(item["is_new"])

		# 1. Interactive Face-Down Card inside the Ceremony Overlay
		var cw_ceremony: Control = CardWidget.new()
		cw_ceremony.custom_minimum_size = Vector2(184, 276)
		cw_ceremony.show_lock_if_unowned = false
		cw_ceremony.is_new_badge = is_new
		cw_ceremony.show_gacha_glow = true
		cw_ceremony.setup(cid, elem, true, false) # Starts face-down!
		cw_ceremony.card_clicked.connect(func(c_id: String, el: String):
			if cw_ceremony.face_down:
				await cw_ceremony.play_flip_reveal_anim(0.0)
				_update_ceremony_flip_counter()
			else:
				GameState.emit_signal("card_inspect_requested", c_id, el)
		)
		ceremony_cards_grid.add_child(cw_ceremony)
		ceremony_card_widgets.append(cw_ceremony)

		# 2. Face-Up Card in the background PackScreen history grid
		var cw_bg: Control = CardWidget.new()
		cw_bg.custom_minimum_size = Vector2(314, 470)
		cw_bg.show_lock_if_unowned = false
		cw_bg.is_new_badge = is_new
		cw_bg.setup(cid, elem, false, false)
		cw_bg.card_clicked.connect(func(c_id: String, el: String):
			if not GameState.is_touch_scrolling:
				GameState.emit_signal("card_inspect_requested", c_id, el)
		)
		results_grid.add_child(cw_bg)

	lbl_pull_summary.text = "Kết quả %s: %d SSR · %d S · %d R · %d N (Mới: %d)" % [
		p_short,
		current_pull_counts.get("SSR", 0),
		current_pull_counts.get("S", 0),
		current_pull_counts.get("R", 0),
		current_pull_counts.get("N", 0),
		current_pull_counts.get("NEW", 0)
	]
	_update_ceremony_flip_counter()
	refresh_header()


func _update_ceremony_flip_counter() -> void:
	var flipped := 0
	for cw in ceremony_card_widgets:
		if is_instance_valid(cw) and not cw.face_down:
			flipped += 1
	var total := ceremony_card_widgets.size()
	if flipped < total:
		ceremony_status_lbl.text = "Chạm từng thẻ để lật (%d/%d) hoặc bấm LẬT TẤT CẢ" % [flipped, total]
		btn_flip_all.visible = true
	else:
		ceremony_status_lbl.text = "ĐÃ LẬT ĐỦ 10/10 THẺ (%d SSR · %d S · %d R · %d N) — Chạm thẻ xem chi tiết!" % [
			current_pull_counts.get("SSR", 0),
			current_pull_counts.get("S", 0),
			current_pull_counts.get("R", 0),
			current_pull_counts.get("N", 0)
		]
		btn_flip_all.visible = false


func _on_flip_all_pressed() -> void:
	var delay := 0.0
	for cw in ceremony_card_widgets:
		if is_instance_valid(cw) and cw.face_down and not cw.is_flipping:
			cw.play_flip_reveal_anim(delay)
			delay += 0.045
	await get_tree().create_timer(delay + 0.36).timeout
	_update_ceremony_flip_counter()


func _on_close_ceremony_pressed() -> void:
	ceremony_overlay.visible = false
	if not pack_frames.is_empty():
		pack_sprite.texture = pack_frames[0]
	is_animating = false
	refresh_header()
