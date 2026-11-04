extends Control

const CardWidget := preload("res://scripts/components/CardWidget.gd")

var lbl_packs: Label
var lbl_owned: Label
var lbl_gold: Label
var lbl_diamonds: Label
var lbl_account_status: Label
var btn_google_auth: Button
var first_login_banner: PanelContainer
var mode_buttons: Dictionary = {}
var lbl_role_counts: Dictionary = {}
var lbl_deck_status: Label
var btn_start_battle: Button
var btn_start_title: Label
var loadout_grid: GridContainer

# Online Matchmaking & Custom Room Overlay Modal
var matchmaking_overlay: ColorRect
var lbl_mm_title: Label
var lbl_mm_room_code: Label
var lbl_mm_timer: Label
var lbl_mm_seats: Label
var inp_join_code: LineEdit
var btn_mm_cancel: Button


func _init() -> void:
	size = Vector2(1080, 1920)
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_build_ui()


func _ready() -> void:
	GameState.state_changed.connect(refresh_ui)
	BackendClient.auth_state_changed.connect(_on_auth_changed)
	BackendClient.matchmaking_updated.connect(_on_matchmaking_updated)
	BackendClient.matchmaking_started_battle.connect(_on_matchmaking_started_battle)
	BackendClient.room_error.connect(_on_room_error)
	refresh_ui()


func _build_ui() -> void:
	# Full-screen painted dark-fantasy sanctuary backdrop
	var bg_tex := TextureRect.new()
	bg_tex.texture = GameState.tex("res://assets/ui_hud/gui/home_sanctuary_bg_1080x1920.png")
	bg_tex.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	bg_tex.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	bg_tex.position = Vector2.ZERO
	bg_tex.size = Vector2(1080, 1920)
	bg_tex.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bg_tex)
	bg_tex.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)

	var bg_overlay := ColorRect.new()
	bg_overlay.color = Color(0.02, 0.03, 0.07, 0.58)
	bg_overlay.position = Vector2.ZERO
	bg_overlay.size = Vector2(1080, 1920)
	bg_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bg_overlay)
	bg_overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)

	# Full-screen vertical touch ScrollContainer for smooth swipe scrolling on App & Web
	var root_scroll := ScrollContainer.new()
	root_scroll.position = Vector2(24, 18)
	root_scroll.size = Vector2(1032, 1884)
	GameState.setup_touch_scroll(root_scroll)
	add_child(root_scroll)

	var main_vbox := VBoxContainer.new()
	main_vbox.custom_minimum_size = Vector2(1012, 0)
	main_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	main_vbox.add_theme_constant_override("separation", 22)
	main_vbox.mouse_filter = Control.MOUSE_FILTER_PASS
	root_scroll.add_child(main_vbox)

	# 1. Top Header Banner (Player Profile, Guide, Logout & Large Currencies)
	var header_panel := PanelContainer.new()
	header_panel.mouse_filter = Control.MOUSE_FILTER_PASS
	header_panel.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("header", 22))
	main_vbox.add_child(header_panel)

	var header_vbox := VBoxContainer.new()
	header_vbox.add_theme_constant_override("separation", 16)
	header_vbox.mouse_filter = Control.MOUSE_FILTER_PASS
	header_panel.add_child(header_vbox)

	var header_top_row := HBoxContainer.new()
	header_top_row.add_theme_constant_override("separation", 14)
	header_top_row.mouse_filter = Control.MOUSE_FILTER_PASS
	header_vbox.add_child(header_top_row)

	var title_icon := TextureRect.new()
	title_icon.texture = GameState.tex("res://assets/cards/icons/elements/ngu-hanh/prop.png")
	title_icon.custom_minimum_size = Vector2(58, 58)
	title_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	title_icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	title_icon.mouse_filter = Control.MOUSE_FILTER_PASS
	header_top_row.add_child(title_icon)

	lbl_account_status = Label.new()
	lbl_account_status.text = "Pháp Sư Google"
	lbl_account_status.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	lbl_account_status.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	lbl_account_status.clip_text = true
	lbl_account_status.add_theme_font_size_override("font_size", 28)
	lbl_account_status.add_theme_color_override("font_color", Color(1.0, 0.90, 0.36))
	header_top_row.add_child(lbl_account_status)

	var btn_guide := Button.new()
	btn_guide.text = "LUẬT CHƠI"
	btn_guide.icon = GameState.tex("res://assets/ui_hud/icons/icon_guide_book.png")
	btn_guide.expand_icon = true
	btn_guide.custom_minimum_size = Vector2(210, 72)
	btn_guide.add_theme_font_size_override("font_size", 24)
	GameState.apply_gui_button(btn_guide, "purple", false, 16, 10)
	btn_guide.pressed.connect(func():
		if not GameState.is_touch_scrolling:
			GameState.emit_signal("guide_requested", 0)
	)
	header_top_row.add_child(btn_guide)

	btn_google_auth = Button.new()
	btn_google_auth.text = "ĐỔI TK"
	btn_google_auth.icon = GameState.tex("res://assets/ui_hud/icons/icon_star_new.png")
	btn_google_auth.expand_icon = true
	btn_google_auth.custom_minimum_size = Vector2(180, 72)
	btn_google_auth.add_theme_font_size_override("font_size", 24)
	GameState.apply_gui_button(btn_google_auth, "gold", false, 16, 10)
	btn_google_auth.pressed.connect(func():
		if not GameState.is_touch_scrolling:
			BackendClient.logout()
	)
	header_top_row.add_child(btn_google_auth)

	# Currency Bar Row (Large, High-Contrast Badges)
	var stats_row := HBoxContainer.new()
	stats_row.alignment = BoxContainer.ALIGNMENT_CENTER
	stats_row.add_theme_constant_override("separation", 32)
	stats_row.mouse_filter = Control.MOUSE_FILTER_PASS
	header_vbox.add_child(stats_row)

	lbl_gold = _make_icon_stat(stats_row, "res://assets/ui_hud/icons/icon_coin_gold.png", Color(1.0, 0.88, 0.32), 28)
	lbl_diamonds = _make_icon_stat(stats_row, "res://assets/ui_hud/icons/icon_diamond_blue.png", Color(0.48, 0.92, 1.0), 28)
	lbl_packs = _make_icon_stat(stats_row, "res://assets/ui_hud/icons/icon_pack_chest.png", Color(1.0, 0.80, 0.44), 28)
	lbl_owned = _make_icon_stat(stats_row, "res://assets/ui_hud/icons/icon_cards_hand.png", Color(0.56, 0.98, 0.68), 28)

	# 1B. Non-Blocking First-Login 15 Starter Cards Celebration Banner
	first_login_banner = PanelContainer.new()
	first_login_banner.mouse_filter = Control.MOUSE_FILTER_PASS
	first_login_banner.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("slot_active", 20))
	first_login_banner.visible = false
	main_vbox.add_child(first_login_banner)

	var fl_hbox := HBoxContainer.new()
	fl_hbox.add_theme_constant_override("separation", 16)
	fl_hbox.alignment = BoxContainer.ALIGNMENT_CENTER
	fl_hbox.mouse_filter = Control.MOUSE_FILTER_PASS
	first_login_banner.add_child(fl_hbox)

	var fl_icon := TextureRect.new()
	fl_icon.texture = GameState.tex("res://assets/ui_hud/icons/icon_star_new.png")
	fl_icon.custom_minimum_size = Vector2(52, 52)
	fl_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	fl_icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	fl_icon.mouse_filter = Control.MOUSE_FILTER_PASS
	fl_hbox.add_child(fl_icon)

	var fl_lbl := Label.new()
	fl_lbl.text = "QUÀ TÂN THỦ: Đã nhận 15 Thẻ Khởi Đầu + 1.000 Vàng + 100 KC!"
	fl_lbl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	fl_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	fl_lbl.add_theme_font_size_override("font_size", 26)
	fl_lbl.add_theme_color_override("font_color", Color(1.0, 0.92, 0.42))
	fl_hbox.add_child(fl_lbl)

	var btn_fl_ok := Button.new()
	btn_fl_ok.text = "ĐÓNG"
	btn_fl_ok.custom_minimum_size = Vector2(150, 68)
	btn_fl_ok.add_theme_font_size_override("font_size", 24)
	GameState.apply_gui_button(btn_fl_ok, "gold", false, 16, 10)
	btn_fl_ok.pressed.connect(func():
		GameState.just_granted_starter_15 = false
		first_login_banner.visible = false
	)
	fl_hbox.add_child(btn_fl_ok)

	# 2. Primary Navigation & Battle Launch Panel (Clean Single-Line Giant Buttons)
	var nav_vbox := VBoxContainer.new()
	nav_vbox.add_theme_constant_override("separation", 18)
	nav_vbox.mouse_filter = Control.MOUSE_FILTER_PASS
	main_vbox.add_child(nav_vbox)

	var battle_btn_info := _make_ornate_home_button(
		"res://assets/ui_hud/gui/btn_play_battle.png",
		Vector2(0, 156),
		"VÀO TRẬN NGAY (4 NGƯỜI)",
		Color(1.0, 0.94, 0.48),
		36,
		_on_start_battle_pressed
	)
	btn_start_battle = battle_btn_info["button"]
	btn_start_title = battle_btn_info["title_lbl"]
	nav_vbox.add_child(btn_start_battle)

	var sub_nav_row := HBoxContainer.new()
	sub_nav_row.add_theme_constant_override("separation", 18)
	sub_nav_row.mouse_filter = Control.MOUSE_FILTER_PASS
	nav_vbox.add_child(sub_nav_row)

	var gacha_info := _make_ornate_home_button(
		"res://assets/ui_hud/gui/btn_nav_gacha.png",
		Vector2(0, 138),
		"MỞ RƯƠNG GACHA",
		Color(0.98, 0.88, 1.0),
		29,
		func():
			if not GameState.is_touch_scrolling:
				GameState.emit_signal("screen_requested", "packs")
	)
	sub_nav_row.add_child(gacha_info["button"])

	var col_info := _make_ornate_home_button(
		"res://assets/ui_hud/gui/btn_nav_collection.png",
		Vector2(0, 138),
		"KHO THẺ 500 LÁ",
		Color(0.68, 1.0, 0.82),
		29,
		func():
			if not GameState.is_touch_scrolling:
				GameState.emit_signal("screen_requested", "collection")
	)
	sub_nav_row.add_child(col_info["button"])

	# 3. Clean Match Mode & Online Panel (No redundant 4-corner text boxes!)
	var match_panel := PanelContainer.new()
	match_panel.mouse_filter = Control.MOUSE_FILTER_PASS
	match_panel.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("section", 22))
	main_vbox.add_child(match_panel)

	var m_vbox := VBoxContainer.new()
	m_vbox.add_theme_constant_override("separation", 16)
	m_vbox.mouse_filter = Control.MOUSE_FILTER_PASS
	match_panel.add_child(m_vbox)

	var lbl_m_title := Label.new()
	lbl_m_title.text = "CHẾ ĐỘ ĐẤU TRƯỜNG"
	lbl_m_title.add_theme_font_size_override("font_size", 28)
	lbl_m_title.add_theme_color_override("font_color", Color(1.0, 0.88, 0.34))
	m_vbox.add_child(lbl_m_title)

	# Row A: 2P / 3P / 4P Mode Buttons
	var mode_row := HBoxContainer.new()
	mode_row.add_theme_constant_override("separation", 16)
	mode_row.mouse_filter = Control.MOUSE_FILTER_PASS
	m_vbox.add_child(mode_row)

	for cnt in [2, 3, 4]:
		var b := Button.new()
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.custom_minimum_size = Vector2(0, 84)
		b.clip_text = true
		b.icon = GameState.tex("res://assets/ui_hud/icons/icon_swords_battle.png")
		b.expand_icon = true
		b.text = "%d NGƯỜI" % cnt
		b.add_theme_font_size_override("font_size", 27)
		var captured_cnt: int = cnt
		b.pressed.connect(func():
			if not GameState.is_touch_scrolling:
				GameState.selected_player_count = captured_cnt
				GameState.save_game()
		)
		mode_row.add_child(b)
		mode_buttons[cnt] = b

	# Row B: Online Quick Matchmaking & Custom Room Buttons
	var online_row := HBoxContainer.new()
	online_row.add_theme_constant_override("separation", 16)
	online_row.mouse_filter = Control.MOUSE_FILTER_PASS
	m_vbox.add_child(online_row)

	var btn_quick_mm := Button.new()
	btn_quick_mm.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	btn_quick_mm.custom_minimum_size = Vector2(0, 86)
	btn_quick_mm.clip_text = true
	btn_quick_mm.icon = GameState.tex("res://assets/ui_hud/icons/icon_swords_battle.png")
	btn_quick_mm.expand_icon = true
	btn_quick_mm.text = "GHÉP TRẬN ONLINE"
	btn_quick_mm.add_theme_font_size_override("font_size", 26)
	GameState.apply_gui_button(btn_quick_mm, "red", false, 18, 12)
	btn_quick_mm.pressed.connect(func():
		if not GameState.is_touch_scrolling:
			_on_quick_matchmaking_pressed()
	)
	online_row.add_child(btn_quick_mm)

	var btn_custom_room := Button.new()
	btn_custom_room.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	btn_custom_room.custom_minimum_size = Vector2(0, 86)
	btn_custom_room.clip_text = true
	btn_custom_room.icon = GameState.tex("res://assets/ui_hud/icons/icon_human_crown.png")
	btn_custom_room.expand_icon = true
	btn_custom_room.text = "PHÒNG BẠN BÈ"
	btn_custom_room.add_theme_font_size_override("font_size", 26)
	GameState.apply_gui_button(btn_custom_room, "purple", false, 18, 12)
	btn_custom_room.pressed.connect(func():
		if not GameState.is_touch_scrolling:
			_on_open_custom_room_modal()
	)
	online_row.add_child(btn_custom_room)

	# 4. 15-Card Battle Loadout Deck Section (3x5 Grid of Large Cards)
	var deck_panel := PanelContainer.new()
	deck_panel.mouse_filter = Control.MOUSE_FILTER_PASS
	deck_panel.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("section", 22))
	main_vbox.add_child(deck_panel)

	var d_vbox := VBoxContainer.new()
	d_vbox.add_theme_constant_override("separation", 18)
	d_vbox.mouse_filter = Control.MOUSE_FILTER_PASS
	deck_panel.add_child(d_vbox)

	var d_head := HBoxContainer.new()
	d_head.add_theme_constant_override("separation", 14)
	d_head.mouse_filter = Control.MOUSE_FILTER_PASS
	d_vbox.add_child(d_head)

	var d_icon := TextureRect.new()
	d_icon.texture = GameState.tex("res://assets/ui_hud/icons/icon_cards_hand.png")
	d_icon.custom_minimum_size = Vector2(44, 44)
	d_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	d_icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	d_icon.mouse_filter = Control.MOUSE_FILTER_PASS
	d_head.add_child(d_icon)

	var lbl_d_title := Label.new()
	lbl_d_title.text = "BỘ BÀI XUẤT CHIẾN (15 LÁ)"
	lbl_d_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	lbl_d_title.clip_text = true
	lbl_d_title.add_theme_font_size_override("font_size", 28)
	lbl_d_title.add_theme_color_override("font_color", Color(1.0, 0.88, 0.34))
	d_head.add_child(lbl_d_title)

	lbl_deck_status = Label.new()
	lbl_deck_status.add_theme_font_size_override("font_size", 24)
	d_head.add_child(lbl_deck_status)

	var d_actions_row := HBoxContainer.new()
	d_actions_row.add_theme_constant_override("separation", 16)
	d_actions_row.mouse_filter = Control.MOUSE_FILTER_PASS
	d_vbox.add_child(d_actions_row)

	var btn_auto := Button.new()
	btn_auto.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	btn_auto.text = "TỰ XẾP 15 LÁ MẠNH NHẤT"
	btn_auto.icon = GameState.tex("res://assets/ui_hud/icons/icon_refresh.png")
	btn_auto.expand_icon = true
	btn_auto.custom_minimum_size = Vector2(0, 78)
	btn_auto.add_theme_font_size_override("font_size", 25)
	GameState.apply_gui_button(btn_auto, "purple", false, 18, 12)
	btn_auto.pressed.connect(func():
		if not GameState.is_touch_scrolling:
			GameState.auto_build_valid_loadout()
	)
	d_actions_row.add_child(btn_auto)

	var btn_edit_col := Button.new()
	btn_edit_col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	btn_edit_col.text = "ĐỔI THẺ TRONG KHO"
	btn_edit_col.icon = GameState.tex("res://assets/ui_hud/icons/icon_cards_hand.png")
	btn_edit_col.expand_icon = true
	btn_edit_col.custom_minimum_size = Vector2(0, 78)
	btn_edit_col.add_theme_font_size_override("font_size", 25)
	GameState.apply_gui_button(btn_edit_col, "green", false, 18, 12)
	btn_edit_col.pressed.connect(func():
		if not GameState.is_touch_scrolling:
			GameState.emit_signal("screen_requested", "collection")
	)
	d_actions_row.add_child(btn_edit_col)

	# 5 Role Requirement Badges Row (Big Icons + Short Numbers)
	var role_bar := HBoxContainer.new()
	role_bar.add_theme_constant_override("separation", 12)
	role_bar.mouse_filter = Control.MOUSE_FILTER_PASS
	d_vbox.add_child(role_bar)

	var role_defs := [
		["atk_phys", "VL", "res://assets/cards/icons/types/atk-phys/prop.png"],
		["atk_mag", "Phép", "res://assets/cards/icons/types/atk-mag/prop.png"],
		["tanker", "Tank", "res://assets/cards/icons/types/tanker/prop.png"],
		["support", "Hỗ Trợ", "res://assets/cards/icons/types/support/prop.png"],
		["item", "Item", "res://assets/cards/icons/types/item/prop.png"],
	]
	for rd in role_defs:
		var r_key: String = rd[0]
		var r_badge := PanelContainer.new()
		r_badge.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		r_badge.mouse_filter = Control.MOUSE_FILTER_PASS
		r_badge.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("slot_active", 12))
		role_bar.add_child(r_badge)

		var rh := HBoxContainer.new()
		rh.alignment = BoxContainer.ALIGNMENT_CENTER
		rh.add_theme_constant_override("separation", 8)
		rh.mouse_filter = Control.MOUSE_FILTER_PASS
		r_badge.add_child(rh)

		var ric := TextureRect.new()
		ric.texture = GameState.tex(rd[2])
		ric.custom_minimum_size = Vector2(36, 36)
		ric.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		ric.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		ric.mouse_filter = Control.MOUSE_FILTER_PASS
		rh.add_child(ric)

		var rlbl := Label.new()
		rlbl.text = "%s: 3" % rd[1]
		rlbl.clip_text = true
		rlbl.add_theme_font_size_override("font_size", 23)
		rh.add_child(rlbl)
		lbl_role_counts[r_key] = rlbl

	# Large 3x5 Grid of 15 Loadout Cards (306x459 per card)
	var grid_center := HBoxContainer.new()
	grid_center.alignment = BoxContainer.ALIGNMENT_CENTER
	grid_center.mouse_filter = Control.MOUSE_FILTER_PASS
	d_vbox.add_child(grid_center)

	loadout_grid = GridContainer.new()
	loadout_grid.columns = 3
	loadout_grid.add_theme_constant_override("h_separation", 16)
	loadout_grid.add_theme_constant_override("v_separation", 18)
	loadout_grid.mouse_filter = Control.MOUSE_FILTER_PASS
	grid_center.add_child(loadout_grid)

	# 5. Build Online Matchmaking & Custom Room Modal Overlay
	_build_matchmaking_modal()


func _make_icon_stat(parent: Control, icon_path: String, col: Color, fsize: int = 28) -> Label:
	var hb := HBoxContainer.new()
	hb.add_theme_constant_override("separation", 10)
	hb.mouse_filter = Control.MOUSE_FILTER_PASS
	parent.add_child(hb)

	var ic := TextureRect.new()
	ic.texture = GameState.tex(icon_path)
	ic.custom_minimum_size = Vector2(42, 42)
	ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	ic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	ic.mouse_filter = Control.MOUSE_FILTER_PASS
	hb.add_child(ic)

	var l := Label.new()
	l.add_theme_font_size_override("font_size", fsize)
	l.add_theme_color_override("font_color", col)
	hb.add_child(l)
	return l


func _make_ornate_home_button(
	tex_path: String,
	min_sz: Vector2,
	title_txt: String,
	title_col: Color,
	title_fsize: int,
	on_click: Callable
) -> Dictionary:
	var b := Button.new()
	b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	b.custom_minimum_size = min_sz
	b.focus_mode = Control.FOCUS_NONE
	b.mouse_filter = Control.MOUSE_FILTER_PASS
	b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND

	var sb_normal := StyleBoxTexture.new()
	sb_normal.texture = GameState.tex(tex_path)
	var sb_hover := sb_normal.duplicate() as StyleBoxTexture
	sb_hover.modulate_color = Color(1.08, 1.08, 1.08, 1.0)
	var sb_pressed := sb_normal.duplicate() as StyleBoxTexture
	sb_pressed.modulate_color = Color(0.88, 0.88, 0.90, 1.0)
	var sb_disabled := sb_normal.duplicate() as StyleBoxTexture
	sb_disabled.modulate_color = Color(0.50, 0.50, 0.55, 0.85)

	b.add_theme_stylebox_override("normal", sb_normal)
	b.add_theme_stylebox_override("hover", sb_hover)
	b.add_theme_stylebox_override("pressed", sb_pressed)
	b.add_theme_stylebox_override("disabled", sb_disabled)
	b.pressed.connect(on_click)

	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	margin.add_theme_constant_override("margin_left", 96)
	margin.add_theme_constant_override("margin_right", 28)
	margin.add_theme_constant_override("margin_top", 16)
	margin.add_theme_constant_override("margin_bottom", 16)
	margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	b.add_child(margin)

	var lbl_t := Label.new()
	lbl_t.text = title_txt
	lbl_t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lbl_t.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	lbl_t.clip_text = true
	lbl_t.add_theme_font_size_override("font_size", title_fsize)
	lbl_t.add_theme_color_override("font_color", title_col)
	lbl_t.add_theme_color_override("font_outline_color", Color(0.01, 0.01, 0.03, 0.98))
	lbl_t.add_theme_constant_override("outline_size", 6)
	lbl_t.mouse_filter = Control.MOUSE_FILTER_IGNORE
	margin.add_child(lbl_t)

	return {"button": b, "title_lbl": lbl_t}


func refresh_ui() -> void:
	if not is_inside_tree():
		return

	lbl_gold.text = "%d Vàng" % GameState.gold
	lbl_diamonds.text = "%d KC" % GameState.diamonds
	lbl_packs.text = "%d Rương" % GameState.pack_count
	lbl_owned.text = "%d/500 Thẻ" % GameState.get_owned_unique_count()

	first_login_banner.visible = GameState.just_granted_starter_15

	var u: Dictionary = BackendClient.current_user
	var disp_name := str(u.get("displayName", "Pháp Sư"))
	lbl_account_status.text = disp_name

	# Refresh Mode Buttons (2P / 3P / 4P)
	for cnt in [2, 3, 4]:
		var b: Button = mode_buttons[cnt]
		var active: bool = (int(GameState.selected_player_count) == int(cnt))
		GameState.apply_gui_button(b, "gold" if active else "slate", false, 16, 10)
		b.add_theme_color_override("font_color", Color(1.0, 0.97, 0.84) if active else Color(0.80, 0.84, 0.92))

	# Refresh Loadout Validation & 5 Role Counters
	var v_info: Dictionary = GameState.is_loadout_valid(GameState.loadout_deck)
	var is_ok: bool = bool(v_info.get("ok", false))
	var r_counts := {"atk_phys": 0, "atk_mag": 0, "tanker": 0, "support": 0, "item": 0}
	for uid_entry in GameState.loadout_deck:
		var c_data: Dictionary = GameState.get_card(str(uid_entry))
		var rg_str: String = str(c_data.get("role_group", ""))
		if r_counts.has(rg_str):
			r_counts[rg_str] = int(r_counts[rg_str]) + 1
	var short_names := {
		"atk_phys": "VL",
		"atk_mag": "Phép",
		"tanker": "Tank",
		"support": "Hỗ Trợ",
		"item": "Item",
	}
	for r_k in short_names.keys():
		var cnt: int = int(r_counts.get(r_k, 0))
		var rl: Label = lbl_role_counts[r_k]
		rl.text = "%s: %d" % [short_names[r_k], cnt]
		rl.add_theme_color_override("font_color", Color(0.45, 0.98, 0.62) if cnt >= 2 else Color(1.0, 0.76, 0.38))

	lbl_deck_status.text = "Đủ 15/15" if is_ok else ("Thiếu: %d/15" % GameState.loadout_deck.size())
	lbl_deck_status.add_theme_color_override("font_color", Color(0.48, 0.98, 0.64) if is_ok else Color(1.0, 0.48, 0.44))

	btn_start_battle.disabled = not is_ok
	if is_ok:
		btn_start_title.text = "VÀO TRẬN NGAY (%d NGƯỜI)" % GameState.selected_player_count
	else:
		btn_start_title.text = "CẦN ĐỦ 15 THẺ XUẤT CHIẾN"

	# Rebuild 3x5 Grid of 15 Loadout Cards (306x459 each)
	for ch in loadout_grid.get_children():
		ch.queue_free()

	for i in range(15):
		if i < GameState.loadout_deck.size():
			var uid: String = GameState.loadout_deck[i]
			var cid: String = GameState.get_base_card_id(uid)
			var elem: String = GameState.get_card_element(uid)
			var cw := CardWidget.new()
			cw.custom_minimum_size = Vector2(306, 459)
			cw.show_lock_if_unowned = false
			cw.setup(cid, elem, false, false)
			cw.card_clicked.connect(func(c_id: String, el: String):
				GameState.emit_signal("card_inspect_requested", c_id, el)
			)
			cw.card_secondary_clicked.connect(func(c_id: String, el: String):
				GameState.toggle_card_in_loadout(c_id, el)
			)
			loadout_grid.add_child(cw)
		else:
			var empty_slot := PanelContainer.new()
			empty_slot.custom_minimum_size = Vector2(306, 459)
			empty_slot.mouse_filter = Control.MOUSE_FILTER_PASS
			empty_slot.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("slot_gray", 16))
			var elbl := Label.new()
			elbl.text = "Ô TRỐNG #%d" % (i + 1)
			elbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			elbl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
			elbl.add_theme_font_size_override("font_size", 26)
			elbl.add_theme_color_override("font_color", Color(0.68, 0.72, 0.80))
			empty_slot.add_child(elbl)
			loadout_grid.add_child(empty_slot)


func _on_start_battle_pressed() -> void:
	if GameState.is_touch_scrolling:
		return
	var v_info := GameState.is_loadout_valid(GameState.loadout_deck)
	if not v_info["ok"]:
		return
	GameState.emit_signal("screen_requested", "battle")


# ==============================================================================
# ONLINE MATCHMAKING (10s Timeout -> Auto-Fill Bots) & CUSTOM ROOMS MODAL
# ==============================================================================
func _build_matchmaking_modal() -> void:
	matchmaking_overlay = ColorRect.new()
	matchmaking_overlay.color = Color(0.01, 0.02, 0.05, 0.90)
	matchmaking_overlay.position = Vector2.ZERO
	matchmaking_overlay.size = Vector2(1080, 1920)
	matchmaking_overlay.mouse_filter = Control.MOUSE_FILTER_STOP
	matchmaking_overlay.visible = false
	matchmaking_overlay.z_index = 120
	add_child(matchmaking_overlay)

	var box := PanelContainer.new()
	box.position = Vector2(46, 360)
	box.size = Vector2(988, 1140)
	box.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("dialog", 32))
	matchmaking_overlay.add_child(box)

	var vb := VBoxContainer.new()
	vb.add_theme_constant_override("separation", 24)
	box.add_child(vb)

	var top_bar := HBoxContainer.new()
	top_bar.add_theme_constant_override("separation", 14)
	vb.add_child(top_bar)

	var mm_ic := TextureRect.new()
	mm_ic.texture = GameState.tex("res://assets/ui_hud/icons/icon_swords_battle.png")
	mm_ic.custom_minimum_size = Vector2(52, 52)
	mm_ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	mm_ic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	top_bar.add_child(mm_ic)

	lbl_mm_title = Label.new()
	lbl_mm_title.text = "GHÉP TRẬN ONLINE"
	lbl_mm_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	lbl_mm_title.clip_text = true
	lbl_mm_title.add_theme_font_size_override("font_size", 32)
	lbl_mm_title.add_theme_color_override("font_color", Color(1.0, 0.88, 0.34))
	top_bar.add_child(lbl_mm_title)

	var btn_close_mm := Button.new()
	btn_close_mm.text = "ĐÓNG"
	btn_close_mm.custom_minimum_size = Vector2(160, 68)
	btn_close_mm.add_theme_font_size_override("font_size", 25)
	GameState.apply_gui_button(btn_close_mm, "wood", false)
	btn_close_mm.pressed.connect(_on_cancel_matchmaking)
	top_bar.add_child(btn_close_mm)

	var status_panel := PanelContainer.new()
	status_panel.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("section", 24))
	vb.add_child(status_panel)

	var st_vb := VBoxContainer.new()
	st_vb.add_theme_constant_override("separation", 16)
	status_panel.add_child(st_vb)

	lbl_mm_room_code = Label.new()
	lbl_mm_room_code.text = "MÃ PHÒNG: ------"
	lbl_mm_room_code.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lbl_mm_room_code.add_theme_font_size_override("font_size", 36)
	lbl_mm_room_code.add_theme_color_override("font_color", Color(0.48, 0.96, 1.0))
	st_vb.add_child(lbl_mm_room_code)

	lbl_mm_timer = Label.new()
	lbl_mm_timer.text = "Tự thêm Bot sau: 10.0s"
	lbl_mm_timer.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lbl_mm_timer.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	lbl_mm_timer.add_theme_font_size_override("font_size", 26)
	lbl_mm_timer.add_theme_color_override("font_color", Color(1.0, 0.86, 0.38))
	st_vb.add_child(lbl_mm_timer)

	lbl_mm_seats = Label.new()
	lbl_mm_seats.text = "• Góc 1: Bạn\n• Góc 2: Đang chờ...\n• Góc 3: Đang chờ...\n• Góc 4: Đang chờ..."
	lbl_mm_seats.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	lbl_mm_seats.add_theme_font_size_override("font_size", 26)
	lbl_mm_seats.add_theme_color_override("font_color", Color(0.92, 0.96, 1.0))
	st_vb.add_child(lbl_mm_seats)

	# Room Actions Row
	var room_panel := PanelContainer.new()
	room_panel.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("slot_active", 22))
	vb.add_child(room_panel)

	var r_vb := VBoxContainer.new()
	r_vb.add_theme_constant_override("separation", 16)
	room_panel.add_child(r_vb)

	var lbl_r_head := Label.new()
	lbl_r_head.text = "PHÒNG BẠN BÈ"
	lbl_r_head.add_theme_font_size_override("font_size", 27)
	lbl_r_head.add_theme_color_override("font_color", Color(1.0, 0.86, 0.36))
	r_vb.add_child(lbl_r_head)

	var join_row := HBoxContainer.new()
	join_row.add_theme_constant_override("separation", 14)
	r_vb.add_child(join_row)

	var btn_create_r := Button.new()
	btn_create_r.text = "TẠO PHÒNG"
	btn_create_r.icon = GameState.tex("res://assets/ui_hud/icons/icon_human_crown.png")
	btn_create_r.expand_icon = true
	btn_create_r.custom_minimum_size = Vector2(260, 76)
	btn_create_r.add_theme_font_size_override("font_size", 24)
	GameState.apply_gui_button(btn_create_r, "purple", false, 16, 12)
	btn_create_r.pressed.connect(func():
		BackendClient.create_custom_room(GameState.selected_player_count)
	)
	join_row.add_child(btn_create_r)

	inp_join_code = LineEdit.new()
	inp_join_code.placeholder_text = "Nhập mã phòng..."
	inp_join_code.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	inp_join_code.custom_minimum_size = Vector2(0, 76)
	inp_join_code.add_theme_font_size_override("font_size", 25)
	inp_join_code.add_theme_stylebox_override("normal", GameState.make_gui_panel_style("slot_gray", 16))
	inp_join_code.add_theme_stylebox_override("focus", GameState.make_gui_panel_style("slot_active", 16))
	join_row.add_child(inp_join_code)

	var btn_join_r := Button.new()
	btn_join_r.text = "VÀO PHÒNG"
	btn_join_r.custom_minimum_size = Vector2(220, 76)
	btn_join_r.add_theme_font_size_override("font_size", 24)
	GameState.apply_gui_button(btn_join_r, "green", false, 16, 12)
	btn_join_r.pressed.connect(func():
		BackendClient.join_custom_room(inp_join_code.text)
	)
	join_row.add_child(btn_join_r)

	var bottom_row := HBoxContainer.new()
	bottom_row.alignment = BoxContainer.ALIGNMENT_CENTER
	bottom_row.add_theme_constant_override("separation", 18)
	vb.add_child(bottom_row)

	var btn_force_bot_now := Button.new()
	btn_force_bot_now.text = "VÀO TRẬN NGAY VỚI BOT"
	btn_force_bot_now.icon = GameState.tex("res://assets/ui_hud/icons/icon_bot_gear.png")
	btn_force_bot_now.expand_icon = true
	btn_force_bot_now.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	btn_force_bot_now.custom_minimum_size = Vector2(0, 88)
	btn_force_bot_now.add_theme_font_size_override("font_size", 27)
	GameState.apply_gui_button(btn_force_bot_now, "gold", true, 24, 14)
	btn_force_bot_now.pressed.connect(func():
		BackendClient.cancel_matchmaking()
		matchmaking_overlay.visible = false
		GameState.save_game()
		GameState.emit_signal("screen_requested", "battle")
	)
	bottom_row.add_child(btn_force_bot_now)

	btn_mm_cancel = Button.new()
	btn_mm_cancel.text = "HỦY"
	btn_mm_cancel.custom_minimum_size = Vector2(200, 88)
	btn_mm_cancel.add_theme_font_size_override("font_size", 26)
	GameState.apply_gui_button(btn_mm_cancel, "wood", false, 18, 14)
	btn_mm_cancel.pressed.connect(_on_cancel_matchmaking)
	bottom_row.add_child(btn_mm_cancel)


func _on_quick_matchmaking_pressed() -> void:
	var v_info := GameState.is_loadout_valid(GameState.loadout_deck)
	if not v_info["ok"]:
		return
	matchmaking_overlay.visible = true
	lbl_mm_title.text = "GHÉP TRẬN (%d NGƯỜI)" % GameState.selected_player_count
	BackendClient.start_quick_matchmaking(GameState.selected_player_count)


func _on_open_custom_room_modal() -> void:
	matchmaking_overlay.visible = true
	lbl_mm_title.text = "PHÒNG BẠN BÈ"
	if not BackendClient.is_searching_match:
		BackendClient.create_custom_room(GameState.selected_player_count)


func _on_cancel_matchmaking() -> void:
	BackendClient.cancel_matchmaking()
	matchmaking_overlay.visible = false
	refresh_ui()


func _on_auth_changed(_user: Dictionary) -> void:
	refresh_ui()


func _on_room_error(err_msg: String) -> void:
	if lbl_mm_timer:
		lbl_mm_timer.text = err_msg
		lbl_mm_timer.add_theme_color_override("font_color", Color(1.0, 0.48, 0.44))


func _on_matchmaking_updated(room_data: Dictionary) -> void:
	if not is_inside_tree() or not matchmaking_overlay.visible:
		return
	var r_code := str(room_data.get("roomCode", "------"))
	var rem_sec := float(room_data.get("remainingWaitSec", 10.0))
	var max_p := int(room_data.get("maxPlayers", GameState.selected_player_count))
	var players: Array = room_data.get("players", [])

	lbl_mm_room_code.text = "MÃ PHÒNG: %s (%d GÓC)" % [r_code, max_p]
	lbl_mm_timer.text = "Tự thêm Bot sau: %.1fs" % rem_sec
	lbl_mm_timer.add_theme_color_override("font_color", Color(1.0, 0.86, 0.36))

	var lines: Array[String] = []
	for s_i in range(max_p):
		var found_p: Dictionary = {}
		for p in players:
			if int(p.get("seatIndex", -1)) == s_i:
				found_p = p
				break
		if not found_p.is_empty():
			var p_tag := "BOT" if bool(found_p.get("isBot", false)) else "NGƯỜI"
			lines.append("• Góc %d: %s [%s]" % [s_i + 1, str(found_p.get("displayName", "Pháp Sư")), p_tag])
		else:
			lines.append("• Góc %d: Đang chờ (%.1fs)..." % [s_i + 1, rem_sec])
	lbl_mm_seats.text = "\n".join(lines)


func _on_matchmaking_started_battle(_room_data: Dictionary) -> void:
	if not is_inside_tree():
		return
	matchmaking_overlay.visible = false
	GameState.emit_signal("screen_requested", "battle")
