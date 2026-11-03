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
var seat_bot_buttons: Dictionary = {}
var seat_status_labels: Dictionary = {}
var seat_boxes: Dictionary = {}
var lbl_role_counts: Dictionary = {}
var lbl_deck_status: Label
var btn_start_battle: Button
var btn_start_title: Label
var btn_start_sub: Label
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
	bg_overlay.color = Color(0.02, 0.03, 0.07, 0.56)
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
	main_vbox.add_theme_constant_override("separation", 20)
	main_vbox.mouse_filter = Control.MOUSE_FILTER_PASS
	root_scroll.add_child(main_vbox)

	# 1. Top Header Banner (Large Title, Google Account Info, Guide & Currencies)
	var header_panel := PanelContainer.new()
	header_panel.mouse_filter = Control.MOUSE_FILTER_PASS
	header_panel.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("header", 22))
	main_vbox.add_child(header_panel)

	var header_vbox := VBoxContainer.new()
	header_vbox.add_theme_constant_override("separation", 14)
	header_vbox.mouse_filter = Control.MOUSE_FILTER_PASS
	header_panel.add_child(header_vbox)

	var header_top_row := HBoxContainer.new()
	header_top_row.add_theme_constant_override("separation", 14)
	header_top_row.mouse_filter = Control.MOUSE_FILTER_PASS
	header_vbox.add_child(header_top_row)

	var title_icon := TextureRect.new()
	title_icon.texture = GameState.tex("res://assets/cards/icons/elements/ngu-hanh/prop.png")
	title_icon.custom_minimum_size = Vector2(56, 56)
	title_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	title_icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	title_icon.mouse_filter = Control.MOUSE_FILTER_PASS
	header_top_row.add_child(title_icon)

	var title_box := VBoxContainer.new()
	title_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title_box.add_theme_constant_override("separation", 4)
	title_box.mouse_filter = Control.MOUSE_FILTER_PASS
	header_top_row.add_child(title_box)

	var lbl_title := Label.new()
	lbl_title.text = "ARCANA OF THE FIVE ELEMENTS"
	lbl_title.clip_text = true
	lbl_title.add_theme_font_size_override("font_size", 28)
	lbl_title.add_theme_color_override("font_color", Color(1.0, 0.86, 0.32))
	title_box.add_child(lbl_title)

	lbl_account_status = Label.new()
	lbl_account_status.text = "Google: Đã kết nối · Cloud Online"
	lbl_account_status.clip_text = true
	lbl_account_status.add_theme_font_size_override("font_size", 19)
	lbl_account_status.add_theme_color_override("font_color", Color(0.56, 0.96, 0.68))
	title_box.add_child(lbl_account_status)

	btn_google_auth = Button.new()
	btn_google_auth.text = "ĐỔI TK GOOGLE"
	btn_google_auth.icon = GameState.tex("res://assets/ui_hud/icons/icon_star_new.png")
	btn_google_auth.expand_icon = true
	btn_google_auth.custom_minimum_size = Vector2(210, 64)
	btn_google_auth.add_theme_font_size_override("font_size", 19)
	GameState.apply_gui_button(btn_google_auth, "gold", false, 14, 10)
	btn_google_auth.pressed.connect(func():
		if GameState.is_touch_scrolling:
			return
		BackendClient.logout()
	)
	header_top_row.add_child(btn_google_auth)

	var btn_guide := Button.new()
	btn_guide.text = "CẨM NANG"
	btn_guide.icon = GameState.tex("res://assets/ui_hud/icons/icon_guide_book.png")
	btn_guide.expand_icon = true
	btn_guide.custom_minimum_size = Vector2(185, 64)
	btn_guide.add_theme_font_size_override("font_size", 19)
	GameState.apply_gui_button(btn_guide, "purple", false, 14, 10)
	btn_guide.pressed.connect(func():
		if GameState.is_touch_scrolling:
			return
		GameState.emit_signal("guide_requested", 0)
	)
	header_top_row.add_child(btn_guide)

	# Currency Bar Row (Large, High-Contrast Badges)
	var stats_row := HBoxContainer.new()
	stats_row.alignment = BoxContainer.ALIGNMENT_CENTER
	stats_row.add_theme_constant_override("separation", 28)
	stats_row.mouse_filter = Control.MOUSE_FILTER_PASS
	header_vbox.add_child(stats_row)

	lbl_gold = _make_icon_stat(stats_row, "res://assets/ui_hud/icons/icon_coin_gold.png", Color(1.0, 0.88, 0.32), 23)
	lbl_diamonds = _make_icon_stat(stats_row, "res://assets/ui_hud/icons/icon_diamond_blue.png", Color(0.48, 0.90, 1.0), 23)
	lbl_packs = _make_icon_stat(stats_row, "res://assets/ui_hud/icons/icon_pack_chest.png", Color(0.98, 0.78, 0.42), 23)
	lbl_owned = _make_icon_stat(stats_row, "res://assets/ui_hud/icons/icon_cards_hand.png", Color(0.55, 0.96, 0.68), 23)

	# 1B. Non-Blocking First-Login 15 Starter Cards Celebration Banner (Never blocks screen!)
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
	fl_icon.custom_minimum_size = Vector2(48, 48)
	fl_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	fl_icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	fl_icon.mouse_filter = Control.MOUSE_FILTER_PASS
	fl_hbox.add_child(fl_icon)

	var fl_lbl := Label.new()
	fl_lbl.text = "QUÀ TÂN THỦ GOOGLE: Đã nhận 15 Thẻ Khởi Đầu Mặc Định + 1.000 Coin + 100 Kim Cương! Bộ 15 lá đã sẵn sàng bên dưới."
	fl_lbl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	fl_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	fl_lbl.add_theme_font_size_override("font_size", 21)
	fl_lbl.add_theme_color_override("font_color", Color(1.0, 0.92, 0.42))
	fl_hbox.add_child(fl_lbl)

	var btn_fl_ok := Button.new()
	btn_fl_ok.text = "ĐÃ HIỂU"
	btn_fl_ok.custom_minimum_size = Vector2(150, 60)
	btn_fl_ok.add_theme_font_size_override("font_size", 20)
	GameState.apply_gui_button(btn_fl_ok, "gold", false, 16, 10)
	btn_fl_ok.pressed.connect(func():
		GameState.just_granted_starter_15 = false
		first_login_banner.visible = false
	)
	fl_hbox.add_child(btn_fl_ok)

	# 2. Primary Navigation & Battle Launch Panel (Large Ornate Fantasy Buttons)
	var nav_vbox := VBoxContainer.new()
	nav_vbox.add_theme_constant_override("separation", 16)
	nav_vbox.mouse_filter = Control.MOUSE_FILTER_PASS
	main_vbox.add_child(nav_vbox)

	var battle_btn_info := _make_ornate_home_button(
		"res://assets/ui_hud/gui/btn_play_battle.png",
		Vector2(0, 152),
		"BẮT ĐẦU TRẬN ĐẤU",
		"Vào Đấu Trường 4 Góc — Đủ 15 Thẻ Xuất Chiến",
		Color(1.0, 0.92, 0.48),
		30,
		20,
		_on_start_battle_pressed
	)
	btn_start_battle = battle_btn_info["button"]
	btn_start_title = battle_btn_info["title_lbl"]
	btn_start_sub = battle_btn_info["sub_lbl"]
	nav_vbox.add_child(btn_start_battle)

	var sub_nav_row := HBoxContainer.new()
	sub_nav_row.add_theme_constant_override("separation", 16)
	sub_nav_row.mouse_filter = Control.MOUSE_FILTER_PASS
	nav_vbox.add_child(sub_nav_row)

	var gacha_info := _make_ornate_home_button(
		"res://assets/ui_hud/gui/btn_nav_gacha.png",
		Vector2(0, 144),
		"MỞ RƯƠNG GACHA",
		"5 Cấp Rương · 10 Thẻ/Pack",
		Color(0.98, 0.84, 1.0),
		25,
		18,
		func():
			if not GameState.is_touch_scrolling:
				GameState.emit_signal("screen_requested", "packs")
	)
	sub_nav_row.add_child(gacha_info["button"])

	var col_info := _make_ornate_home_button(
		"res://assets/ui_hud/gui/btn_nav_collection.png",
		Vector2(0, 144),
		"KHO THẺ 500 LÁ",
		"100 Vũ Khí × 5 Hệ Ngũ Hành",
		Color(0.68, 1.0, 0.80),
		25,
		18,
		func():
			if not GameState.is_touch_scrolling:
				GameState.emit_signal("screen_requested", "collection")
	)
	sub_nav_row.add_child(col_info["button"])

	# 3. Match Configuration Panel (Player Count, Online Matchmaking & 2x2 Commander Grid)
	var match_panel := PanelContainer.new()
	match_panel.mouse_filter = Control.MOUSE_FILTER_PASS
	match_panel.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("section", 22))
	main_vbox.add_child(match_panel)

	var m_vbox := VBoxContainer.new()
	m_vbox.add_theme_constant_override("separation", 16)
	m_vbox.mouse_filter = Control.MOUSE_FILTER_PASS
	match_panel.add_child(m_vbox)

	var lbl_m_title := Label.new()
	lbl_m_title.text = "CHẾ ĐỘ ĐẤU TRƯỜNG & CẤU HÌNH 4 GÓC PHÁP SƯ"
	lbl_m_title.add_theme_font_size_override("font_size", 24)
	lbl_m_title.add_theme_color_override("font_color", Color(1.0, 0.86, 0.34))
	m_vbox.add_child(lbl_m_title)

	# Row A: 2P / 3P / 4P Mode Buttons
	var mode_row := HBoxContainer.new()
	mode_row.add_theme_constant_override("separation", 14)
	mode_row.mouse_filter = Control.MOUSE_FILTER_PASS
	m_vbox.add_child(mode_row)

	for cnt in [2, 3, 4]:
		var b := Button.new()
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.custom_minimum_size = Vector2(0, 72)
		b.clip_text = true
		b.icon = GameState.tex("res://assets/ui_hud/icons/icon_swords_battle.png")
		b.expand_icon = true
		b.text = "%d NGƯỜI (%d GÓC)" % [cnt, cnt]
		b.add_theme_font_size_override("font_size", 21)
		var captured_cnt: int = cnt
		b.pressed.connect(func():
			if not GameState.is_touch_scrolling:
				GameState.selected_player_count = captured_cnt
				GameState.save_game()
		)
		mode_row.add_child(b)
		mode_buttons[cnt] = b

	# Row B: Online Quick Matchmaking (10s -> Bot) & Custom Room Buttons
	var online_row := HBoxContainer.new()
	online_row.add_theme_constant_override("separation", 14)
	online_row.mouse_filter = Control.MOUSE_FILTER_PASS
	m_vbox.add_child(online_row)

	var btn_quick_mm := Button.new()
	btn_quick_mm.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	btn_quick_mm.custom_minimum_size = Vector2(0, 74)
	btn_quick_mm.clip_text = true
	btn_quick_mm.icon = GameState.tex("res://assets/ui_hud/icons/icon_swords_battle.png")
	btn_quick_mm.expand_icon = true
	btn_quick_mm.text = "GHÉP TRẬN ONLINE (10s -> BOT)"
	btn_quick_mm.add_theme_font_size_override("font_size", 21)
	GameState.apply_gui_button(btn_quick_mm, "red", false, 18, 12)
	btn_quick_mm.pressed.connect(func():
		if not GameState.is_touch_scrolling:
			_on_quick_matchmaking_pressed()
	)
	online_row.add_child(btn_quick_mm)

	var btn_custom_room := Button.new()
	btn_custom_room.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	btn_custom_room.custom_minimum_size = Vector2(0, 74)
	btn_custom_room.clip_text = true
	btn_custom_room.icon = GameState.tex("res://assets/ui_hud/icons/icon_human_crown.png")
	btn_custom_room.expand_icon = true
	btn_custom_room.text = "TẠO / VÀO PHÒNG BẠN BÈ"
	btn_custom_room.add_theme_font_size_override("font_size", 21)
	GameState.apply_gui_button(btn_custom_room, "purple", false, 18, 12)
	btn_custom_room.pressed.connect(func():
		if not GameState.is_touch_scrolling:
			_on_open_custom_room_modal()
	)
	online_row.add_child(btn_custom_room)

	# Row C: 2x2 Grid of Large Commander Corner Cards (Instead of 4 tiny cramped columns!)
	var seats_grid := GridContainer.new()
	seats_grid.columns = 2
	seats_grid.add_theme_constant_override("h_separation", 16)
	seats_grid.add_theme_constant_override("v_separation", 16)
	seats_grid.mouse_filter = Control.MOUSE_FILTER_PASS
	m_vbox.add_child(seats_grid)

	var seat_Meta := [
		{"idx": 0, "title": "GÓC 1 · DƯỚI TRÁI", "name": "Lam Long (Bạn)", "col": Color(0.38, 0.76, 1.0), "icon": "res://assets/cards/icons/elements/thuy/prop.png"},
		{"idx": 1, "title": "GÓC 2 · TRÊN PHẢI", "name": "Xích Hỏa", "col": Color(1.0, 0.46, 0.42), "icon": "res://assets/cards/icons/elements/hoa/prop.png"},
		{"idx": 2, "title": "GÓC 3 · TRÊN TRÁI", "name": "Lục Lâm", "col": Color(0.42, 0.94, 0.56), "icon": "res://assets/cards/icons/elements/moc/prop.png"},
		{"idx": 3, "title": "GÓC 4 · DƯỚI PHẢI", "name": "Hoàng Thổ", "col": Color(1.0, 0.84, 0.34), "icon": "res://assets/cards/icons/elements/tho/prop.png"},
	]

	for sm in seat_Meta:
		var s_idx: int = sm["idx"]
		var p_card := PanelContainer.new()
		p_card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		p_card.mouse_filter = Control.MOUSE_FILTER_PASS
		p_card.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("slot_active", 18))
		seats_grid.add_child(p_card)
		seat_boxes[s_idx] = p_card

		var sv := VBoxContainer.new()
		sv.add_theme_constant_override("separation", 10)
		sv.mouse_filter = Control.MOUSE_FILTER_PASS
		p_card.add_child(sv)

		var st_row := HBoxContainer.new()
		st_row.add_theme_constant_override("separation", 10)
		st_row.mouse_filter = Control.MOUSE_FILTER_PASS
		sv.add_child(st_row)

		var s_ic := TextureRect.new()
		s_ic.texture = GameState.tex(sm["icon"])
		s_ic.custom_minimum_size = Vector2(36, 36)
		s_ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		s_ic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		s_ic.mouse_filter = Control.MOUSE_FILTER_PASS
		st_row.add_child(s_ic)

		var l_head := Label.new()
		l_head.text = "%s · %s" % [sm["title"], sm["name"]]
		l_head.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		l_head.clip_text = true
		l_head.add_theme_font_size_override("font_size", 21)
		l_head.add_theme_color_override("font_color", sm["col"])
		st_row.add_child(l_head)

		var l_state := Label.new()
		l_state.clip_text = true
		l_state.add_theme_font_size_override("font_size", 18)
		sv.add_child(l_state)
		seat_status_labels[s_idx] = l_state

		var btn_toggle := Button.new()
		btn_toggle.custom_minimum_size = Vector2(0, 62)
		btn_toggle.clip_text = true
		btn_toggle.add_theme_font_size_override("font_size", 20)
		btn_toggle.expand_icon = true
		var captured_seat: int = s_idx
		btn_toggle.pressed.connect(func():
			if not GameState.is_touch_scrolling and captured_seat == 0:
				GameState.player_is_bot = not GameState.player_is_bot
				GameState.save_game()
		)
		sv.add_child(btn_toggle)
		seat_bot_buttons[s_idx] = btn_toggle

	# 4. 15-Card Battle Loadout Deck Section (Large 3 Columns x 5 Rows Grid of 306x459 Cards)
	var deck_panel := PanelContainer.new()
	deck_panel.mouse_filter = Control.MOUSE_FILTER_PASS
	deck_panel.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("section", 22))
	main_vbox.add_child(deck_panel)

	var d_vbox := VBoxContainer.new()
	d_vbox.add_theme_constant_override("separation", 16)
	d_vbox.mouse_filter = Control.MOUSE_FILTER_PASS
	deck_panel.add_child(d_vbox)

	var d_head := HBoxContainer.new()
	d_head.add_theme_constant_override("separation", 14)
	d_head.mouse_filter = Control.MOUSE_FILTER_PASS
	d_vbox.add_child(d_head)

	var d_icon := TextureRect.new()
	d_icon.texture = GameState.tex("res://assets/ui_hud/icons/icon_cards_hand.png")
	d_icon.custom_minimum_size = Vector2(40, 40)
	d_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	d_icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	d_icon.mouse_filter = Control.MOUSE_FILTER_PASS
	d_head.add_child(d_icon)

	var lbl_d_title := Label.new()
	lbl_d_title.text = "BỘ BÀI XUẤT CHIẾN 15 LÁ (3 LÁ × 5 LOẠI THẺ)"
	lbl_d_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	lbl_d_title.clip_text = true
	lbl_d_title.add_theme_font_size_override("font_size", 24)
	lbl_d_title.add_theme_color_override("font_color", Color(1.0, 0.86, 0.32))
	d_head.add_child(lbl_d_title)

	var d_actions_row := HBoxContainer.new()
	d_actions_row.add_theme_constant_override("separation", 14)
	d_actions_row.mouse_filter = Control.MOUSE_FILTER_PASS
	d_vbox.add_child(d_actions_row)

	var btn_auto := Button.new()
	btn_auto.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	btn_auto.text = "TỰ XẾP ĐỦ 15 LÁ MẠNH NHẤT"
	btn_auto.icon = GameState.tex("res://assets/ui_hud/icons/icon_refresh.png")
	btn_auto.expand_icon = true
	btn_auto.custom_minimum_size = Vector2(0, 66)
	btn_auto.add_theme_font_size_override("font_size", 20)
	GameState.apply_gui_button(btn_auto, "purple", false, 18, 10)
	btn_auto.pressed.connect(func():
		if not GameState.is_touch_scrolling:
			GameState.auto_build_valid_loadout()
	)
	d_actions_row.add_child(btn_auto)

	var btn_edit_col := Button.new()
	btn_edit_col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	btn_edit_col.text = "ĐỔI THẺ TRONG KHO 500 LÁ"
	btn_edit_col.icon = GameState.tex("res://assets/ui_hud/icons/icon_cards_hand.png")
	btn_edit_col.expand_icon = true
	btn_edit_col.custom_minimum_size = Vector2(0, 66)
	btn_edit_col.add_theme_font_size_override("font_size", 20)
	GameState.apply_gui_button(btn_edit_col, "green", false, 18, 10)
	btn_edit_col.pressed.connect(func():
		if not GameState.is_touch_scrolling:
			GameState.emit_signal("screen_requested", "collection")
	)
	d_actions_row.add_child(btn_edit_col)

	# 5 Role Requirement Badges Row
	var role_bar := HBoxContainer.new()
	role_bar.add_theme_constant_override("separation", 10)
	role_bar.mouse_filter = Control.MOUSE_FILTER_PASS
	d_vbox.add_child(role_bar)

	var role_defs := [
		["atk_phys", "Vật Lý", "res://assets/cards/icons/types/atk-phys/prop.png"],
		["atk_mag", "Ma Pháp", "res://assets/cards/icons/types/atk-mag/prop.png"],
		["tanker", "Đỡ Đòn", "res://assets/cards/icons/types/tanker/prop.png"],
		["support", "Hỗ Trợ", "res://assets/cards/icons/types/support/prop.png"],
		["item", "Vật Phẩm", "res://assets/cards/icons/types/item/prop.png"],
	]
	for rd in role_defs:
		var r_key: String = rd[0]
		var r_badge := PanelContainer.new()
		r_badge.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		r_badge.mouse_filter = Control.MOUSE_FILTER_PASS
		r_badge.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("slot_active", 10))
		role_bar.add_child(r_badge)

		var rh := HBoxContainer.new()
		rh.alignment = BoxContainer.ALIGNMENT_CENTER
		rh.add_theme_constant_override("separation", 6)
		rh.mouse_filter = Control.MOUSE_FILTER_PASS
		r_badge.add_child(rh)

		var ric := TextureRect.new()
		ric.texture = GameState.tex(rd[2])
		ric.custom_minimum_size = Vector2(28, 28)
		ric.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		ric.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		ric.mouse_filter = Control.MOUSE_FILTER_PASS
		rh.add_child(ric)

		var rlbl := Label.new()
		rlbl.text = "%s: 3/3" % rd[1]
		rlbl.clip_text = true
		rlbl.add_theme_font_size_override("font_size", 18)
		rh.add_child(rlbl)
		lbl_role_counts[r_key] = rlbl

	lbl_deck_status = Label.new()
	lbl_deck_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	lbl_deck_status.add_theme_font_size_override("font_size", 20)
	d_vbox.add_child(lbl_deck_status)

	# Large 3x5 Grid of 15 Loadout Cards (306x459 per card — crystal clear on App & Web!)
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


func _make_icon_stat(parent: Control, icon_path: String, col: Color, fsize: int = 22) -> Label:
	var hb := HBoxContainer.new()
	hb.add_theme_constant_override("separation", 8)
	hb.mouse_filter = Control.MOUSE_FILTER_PASS
	parent.add_child(hb)

	var ic := TextureRect.new()
	ic.texture = GameState.tex(icon_path)
	ic.custom_minimum_size = Vector2(34, 34)
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
	sub_txt: String,
	title_col: Color,
	title_fsize: int,
	sub_fsize: int,
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

	var vb := VBoxContainer.new()
	vb.alignment = BoxContainer.ALIGNMENT_CENTER
	vb.add_theme_constant_override("separation", 4)
	vb.mouse_filter = Control.MOUSE_FILTER_IGNORE
	margin.add_child(vb)

	var lbl_t := Label.new()
	lbl_t.text = title_txt
	lbl_t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lbl_t.clip_text = true
	lbl_t.add_theme_font_size_override("font_size", title_fsize)
	lbl_t.add_theme_color_override("font_color", title_col)
	lbl_t.add_theme_color_override("font_outline_color", Color(0.02, 0.01, 0.03, 0.98))
	lbl_t.add_theme_constant_override("outline_size", 4)
	lbl_t.mouse_filter = Control.MOUSE_FILTER_IGNORE
	vb.add_child(lbl_t)

	var lbl_s := Label.new()
	lbl_s.text = sub_txt
	lbl_s.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lbl_s.clip_text = true
	lbl_s.add_theme_font_size_override("font_size", sub_fsize)
	lbl_s.add_theme_color_override("font_color", Color(0.92, 0.94, 0.98))
	lbl_s.add_theme_color_override("font_outline_color", Color(0.02, 0.01, 0.03, 0.98))
	lbl_s.add_theme_constant_override("outline_size", 3)
	lbl_s.mouse_filter = Control.MOUSE_FILTER_IGNORE
	vb.add_child(lbl_s)

	return {"button": b, "title_lbl": lbl_t, "sub_lbl": lbl_s}


func refresh_ui() -> void:
	if not is_inside_tree():
		return

	lbl_gold.text = "%d Coin" % GameState.gold
	lbl_diamonds.text = "%d KC" % GameState.diamonds
	lbl_packs.text = "%d Rương" % GameState.pack_count
	lbl_owned.text = "%d/500 Thẻ" % GameState.get_owned_unique_count()

	first_login_banner.visible = GameState.just_granted_starter_15

	# Refresh Google Account & Online status
	var u: Dictionary = BackendClient.current_user
	var net_tag := "ONLINE" if BackendClient.is_online else "OFFLINE (Chơi với Bot)"
	if bool(u.get("isGoogleLinked", false)):
		lbl_account_status.text = "Google: %s (%s) · %s" % [
			str(u.get("displayName", "Pháp Sư")),
			str(u.get("email", "")),
			net_tag,
		]
		lbl_account_status.add_theme_color_override("font_color", Color(0.48, 0.98, 0.66))
	else:
		lbl_account_status.text = "Tài khoản: %s · %s" % [str(u.get("displayName", "Khách")), net_tag]
		lbl_account_status.add_theme_color_override("font_color", Color(0.84, 0.90, 0.98))

	# Refresh Mode Buttons (2P / 3P / 4P)
	for cnt in [2, 3, 4]:
		var b: Button = mode_buttons[cnt]
		var active: bool = (int(GameState.selected_player_count) == int(cnt))
		GameState.apply_gui_button(b, "gold" if active else "slate", false, 14, 10)
		b.add_theme_color_override("font_color", Color(1.0, 0.97, 0.84) if active else Color(0.80, 0.84, 0.92))

	# Refresh 4 Seat Cards (in 2x2 Grid)
	for s_idx in range(4):
		var box: PanelContainer = seat_boxes[s_idx]
		var lbl_st: Label = seat_status_labels[s_idx]
		var btn_b: Button = seat_bot_buttons[s_idx]
		var is_active_seat: bool = (s_idx < int(GameState.selected_player_count))
		var is_bot: bool = GameState.player_is_bot if s_idx == 0 else true

		if not is_active_seat:
			box.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("slot_gray", 18, Color(0.65, 0.65, 0.72, 0.78)))
			lbl_st.text = "Không tham chiến (Trận %d Người)" % GameState.selected_player_count
			lbl_st.add_theme_color_override("font_color", Color(0.55, 0.58, 0.65))
			btn_b.text = "Đang Khóa Góc"
			btn_b.icon = GameState.tex("res://assets/ui_hud/icons/icon_lock.png")
			btn_b.disabled = true
			GameState.apply_gui_button(btn_b, "slate", false)
		elif s_idx == 0:
			btn_b.disabled = true
			box.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("slot_active", 18))
			lbl_st.text = "Bạn: TRỰC TIẾP ĐIỀU KHIỂN"
			lbl_st.add_theme_color_override("font_color", Color(0.46, 0.96, 0.62))
			btn_b.text = "Người Chơi Chính (Bạn)"
			btn_b.icon = GameState.tex("res://assets/ui_hud/icons/icon_human_crown.png")
			GameState.apply_gui_button(btn_b, "green", false, 12, 8)
		else:
			btn_b.disabled = true
			box.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("slot_active", 18))
			lbl_st.text = "Đối thủ: BOT AI / ONLINE (10s)"
			lbl_st.add_theme_color_override("font_color", Color(0.98, 0.72, 0.38))
			btn_b.text = "Tự ghép Người thật hoặc Bot AI"
			btn_b.icon = GameState.tex("res://assets/ui_hud/icons/icon_bot_gear.png")
			GameState.apply_gui_button(btn_b, "slate", false, 12, 8)

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
		"atk_phys": "Vật Lý",
		"atk_mag": "Ma Pháp",
		"tanker": "Đỡ Đòn",
		"support": "Hỗ Trợ",
		"item": "Vật Phẩm",
	}
	for r_k in short_names.keys():
		var cnt: int = int(r_counts.get(r_k, 0))
		var rl: Label = lbl_role_counts[r_k]
		rl.text = "%s: %d" % [short_names[r_k], cnt]
		rl.add_theme_color_override("font_color", Color(0.45, 0.96, 0.60) if cnt >= 2 else Color(1.0, 0.76, 0.38))

	lbl_deck_status.text = "%s  —  Vuốt lên/xuống để cuộn trang, chạm thẻ để xem chi tiết:" % str(v_info["reason"])
	lbl_deck_status.add_theme_color_override("font_color", Color(0.48, 0.96, 0.64) if is_ok else Color(1.0, 0.48, 0.44))

	btn_start_battle.disabled = not is_ok
	if is_ok:
		btn_start_title.text = "BẮT ĐẦU TRẬN ĐẤU (%d NGƯỜI)" % GameState.selected_player_count
		btn_start_sub.text = "Bộ 15 Lá Hợp Lệ — Chạm để vào trận ngay hoặc Ghép Trận 10s"
	else:
		btn_start_title.text = "CHƯA ĐỦ ĐIỀU KIỆN XUẤT CHIẾN"
		btn_start_sub.text = str(v_info["reason"])

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
			elbl.text = "Ô TRỐNG #%d\nChạm để mở Kho Thẻ" % (i + 1)
			elbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			elbl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
			elbl.add_theme_font_size_override("font_size", 20)
			elbl.add_theme_color_override("font_color", Color(0.65, 0.70, 0.78))
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
	box.position = Vector2(50, 260)
	box.size = Vector2(980, 1340)
	box.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("dialog", 28))
	matchmaking_overlay.add_child(box)

	var vb := VBoxContainer.new()
	vb.add_theme_constant_override("separation", 18)
	box.add_child(vb)

	var top_bar := HBoxContainer.new()
	top_bar.add_theme_constant_override("separation", 12)
	vb.add_child(top_bar)

	var mm_ic := TextureRect.new()
	mm_ic.texture = GameState.tex("res://assets/ui_hud/icons/icon_swords_battle.png")
	mm_ic.custom_minimum_size = Vector2(44, 44)
	mm_ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	mm_ic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	top_bar.add_child(mm_ic)

	lbl_mm_title = Label.new()
	lbl_mm_title.text = "ĐANG GHÉP TRẬN ONLINE (10 GIÂY -> TỰ LẤP BOT)"
	lbl_mm_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	lbl_mm_title.clip_text = true
	lbl_mm_title.add_theme_font_size_override("font_size", 25)
	lbl_mm_title.add_theme_color_override("font_color", Color(1.0, 0.86, 0.32))
	top_bar.add_child(lbl_mm_title)

	var btn_close_mm := Button.new()
	btn_close_mm.text = "ĐÓNG"
	btn_close_mm.custom_minimum_size = Vector2(140, 56)
	btn_close_mm.add_theme_font_size_override("font_size", 20)
	GameState.apply_gui_button(btn_close_mm, "wood", false)
	btn_close_mm.pressed.connect(_on_cancel_matchmaking)
	top_bar.add_child(btn_close_mm)

	var status_panel := PanelContainer.new()
	status_panel.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("section", 20))
	vb.add_child(status_panel)

	var st_vb := VBoxContainer.new()
	st_vb.add_theme_constant_override("separation", 12)
	status_panel.add_child(st_vb)

	lbl_mm_room_code = Label.new()
	lbl_mm_room_code.text = "MÃ PHÒNG: ------"
	lbl_mm_room_code.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lbl_mm_room_code.add_theme_font_size_override("font_size", 28)
	lbl_mm_room_code.add_theme_color_override("font_color", Color(0.48, 0.96, 1.0))
	st_vb.add_child(lbl_mm_room_code)

	lbl_mm_timer = Label.new()
	lbl_mm_timer.text = "Thời gian chờ người chơi thật: 10.0s (Sau 10s tự động thêm Bot vào góc trống)"
	lbl_mm_timer.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lbl_mm_timer.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	lbl_mm_timer.add_theme_font_size_override("font_size", 20)
	lbl_mm_timer.add_theme_color_override("font_color", Color(1.0, 0.84, 0.38))
	st_vb.add_child(lbl_mm_timer)

	lbl_mm_seats = Label.new()
	lbl_mm_seats.text = "• Góc 1: Bạn\n• Góc 2: Đang tìm người chơi...\n• Góc 3: Đang tìm người chơi...\n• Góc 4: Đang tìm người chơi..."
	lbl_mm_seats.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	lbl_mm_seats.add_theme_font_size_override("font_size", 20)
	lbl_mm_seats.add_theme_color_override("font_color", Color(0.88, 0.94, 1.0))
	st_vb.add_child(lbl_mm_seats)

	# Room Actions Row: Create New Room or Join by Room Code
	var room_panel := PanelContainer.new()
	room_panel.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("slot_active", 20))
	vb.add_child(room_panel)

	var r_vb := VBoxContainer.new()
	r_vb.add_theme_constant_override("separation", 14)
	room_panel.add_child(r_vb)

	var lbl_r_head := Label.new()
	lbl_r_head.text = "PHÒNG TÙY CHỌN (TẠO PHÒNG MỚI HOẶC NHẬP MÃ PHÒNG BẠN BÈ)"
	lbl_r_head.add_theme_font_size_override("font_size", 21)
	lbl_r_head.add_theme_color_override("font_color", Color(0.98, 0.84, 0.36))
	r_vb.add_child(lbl_r_head)

	var join_row := HBoxContainer.new()
	join_row.add_theme_constant_override("separation", 14)
	r_vb.add_child(join_row)

	var btn_create_r := Button.new()
	btn_create_r.text = "TẠO PHÒNG MỚI (10s -> BOT)"
	btn_create_r.icon = GameState.tex("res://assets/ui_hud/icons/icon_human_crown.png")
	btn_create_r.expand_icon = true
	btn_create_r.custom_minimum_size = Vector2(360, 66)
	btn_create_r.add_theme_font_size_override("font_size", 19)
	GameState.apply_gui_button(btn_create_r, "purple", false, 14, 10)
	btn_create_r.pressed.connect(func():
		BackendClient.create_custom_room(GameState.selected_player_count)
	)
	join_row.add_child(btn_create_r)

	inp_join_code = LineEdit.new()
	inp_join_code.placeholder_text = "Nhập Mã Phòng (VD: AB12CD)..."
	inp_join_code.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	inp_join_code.custom_minimum_size = Vector2(0, 66)
	inp_join_code.add_theme_font_size_override("font_size", 20)
	inp_join_code.add_theme_stylebox_override("normal", GameState.make_gui_panel_style("slot_gray", 14))
	inp_join_code.add_theme_stylebox_override("focus", GameState.make_gui_panel_style("slot_active", 14))
	join_row.add_child(inp_join_code)

	var btn_join_r := Button.new()
	btn_join_r.text = "VÀO PHÒNG"
	btn_join_r.custom_minimum_size = Vector2(190, 66)
	btn_join_r.add_theme_font_size_override("font_size", 20)
	GameState.apply_gui_button(btn_join_r, "green", false, 14, 10)
	btn_join_r.pressed.connect(func():
		BackendClient.join_custom_room(inp_join_code.text)
	)
	join_row.add_child(btn_join_r)

	var bottom_row := HBoxContainer.new()
	bottom_row.alignment = BoxContainer.ALIGNMENT_CENTER
	bottom_row.add_theme_constant_override("separation", 18)
	vb.add_child(bottom_row)

	var btn_force_bot_now := Button.new()
	btn_force_bot_now.text = "VÀO TRẬN NGAY VỚI BOT (KHÔNG CẦN ĐỢI 10s)"
	btn_force_bot_now.icon = GameState.tex("res://assets/ui_hud/icons/icon_bot_gear.png")
	btn_force_bot_now.expand_icon = true
	btn_force_bot_now.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	btn_force_bot_now.custom_minimum_size = Vector2(0, 78)
	btn_force_bot_now.add_theme_font_size_override("font_size", 21)
	GameState.apply_gui_button(btn_force_bot_now, "gold", true, 24, 12)
	btn_force_bot_now.pressed.connect(func():
		BackendClient.cancel_matchmaking()
		matchmaking_overlay.visible = false
		GameState.save_game()
		GameState.emit_signal("screen_requested", "battle")
	)
	bottom_row.add_child(btn_force_bot_now)

	btn_mm_cancel = Button.new()
	btn_mm_cancel.text = "HỦY TÌM TRẬN"
	btn_mm_cancel.custom_minimum_size = Vector2(230, 78)
	btn_mm_cancel.add_theme_font_size_override("font_size", 20)
	GameState.apply_gui_button(btn_mm_cancel, "wood", false, 18, 12)
	btn_mm_cancel.pressed.connect(_on_cancel_matchmaking)
	bottom_row.add_child(btn_mm_cancel)


func _on_quick_matchmaking_pressed() -> void:
	var v_info := GameState.is_loadout_valid(GameState.loadout_deck)
	if not v_info["ok"]:
		return
	matchmaking_overlay.visible = true
	lbl_mm_title.text = "ĐANG TÌM ĐỐI THỦ (%d NGƯỜI — TỰ LẤP BOT SAU 10 GIÂY)" % GameState.selected_player_count
	BackendClient.start_quick_matchmaking(GameState.selected_player_count)


func _on_open_custom_room_modal() -> void:
	matchmaking_overlay.visible = true
	lbl_mm_title.text = "PHÒNG ĐẤU TÙY CHỌN & ĐĂNG NHẬP GOOGLE CLOUD"
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
		lbl_mm_timer.text = "Thông báo: " + err_msg
		lbl_mm_timer.add_theme_color_override("font_color", Color(1.0, 0.48, 0.44))


func _on_matchmaking_updated(room_data: Dictionary) -> void:
	if not is_inside_tree() or not matchmaking_overlay.visible:
		return
	var r_code := str(room_data.get("roomCode", "------"))
	var r_type := str(room_data.get("type", "matchmaking"))
	var rem_sec := float(room_data.get("remainingWaitSec", 10.0))
	var max_p := int(room_data.get("maxPlayers", GameState.selected_player_count))
	var players: Array = room_data.get("players", [])

	lbl_mm_room_code.text = "MÃ PHÒNG: %s  (%s · %d GÓC)" % [
		r_code,
		"PHÒNG BẠN BÈ" if r_type == "custom_room" else "GHÉP NHANH",
		max_p,
	]
	lbl_mm_timer.text = "Đang chờ người chơi khác tham gia: còn %.1f giây (Quá 10s hệ thống tự thêm BOT vào các góc trống)" % rem_sec
	lbl_mm_timer.add_theme_color_override("font_color", Color(1.0, 0.86, 0.36))

	var lines: Array[String] = []
	for s_i in range(max_p):
		var found_p: Dictionary = {}
		for p in players:
			if int(p.get("seatIndex", -1)) == s_i:
				found_p = p
				break
		if not found_p.is_empty():
			var p_tag := "BOT AI" if bool(found_p.get("isBot", false)) else "NGƯỜI CHƠI"
			lines.append("• Góc %d: %s  [%s]" % [s_i + 1, str(found_p.get("displayName", "Pháp Sư")), p_tag])
		else:
			lines.append("• Góc %d: Đang chờ người chơi (Sẽ tự lấp Bot sau %.1fs)..." % [s_i + 1, rem_sec])
	lbl_mm_seats.text = "\n".join(lines)


func _on_matchmaking_started_battle(_room_data: Dictionary) -> void:
	if not is_inside_tree():
		return
	matchmaking_overlay.visible = false
	GameState.emit_signal("screen_requested", "battle")
