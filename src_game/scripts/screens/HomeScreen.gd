extends Control

const CardWidget := preload("res://scripts/components/CardWidget.gd")

var lbl_owned_stat: Label
var lbl_pack_stat: Label
var lbl_deck_status: Label
var lbl_gacha_sub: Label
var lbl_col_sub: Label
var lbl_play_sub: Label
var btn_p2: Button
var btn_p3: Button
var btn_p4: Button
var btn_bot_toggle: Button
var deck_strip: HBoxContainer
var commander_cards: Array[PanelContainer] = []
var commander_avatars: Array[TextureRect] = []
var commander_status_lbls: Array[Label] = []


func _init() -> void:
	size = Vector2(1080, 1920)
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_build_ui()


func _ready() -> void:
	GameState.state_changed.connect(refresh_ui)
	refresh_ui()


func _build_ui() -> void:
	# 1. Full-bleed 1080x1920 Dark-Fantasy Sanctuary Citadel Background
	var bg_tex_rect := TextureRect.new()
	bg_tex_rect.texture = GameState.tex("res://assets/ui_hud/gui/home_sanctuary_bg_1080x1920.png")
	bg_tex_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	bg_tex_rect.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	bg_tex_rect.position = Vector2.ZERO
	bg_tex_rect.size = Vector2(1080, 1920)
	add_child(bg_tex_rect)
	bg_tex_rect.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)

	# Subtle dark atmospheric overlay for crisp UI readability
	var tint_overlay := ColorRect.new()
	tint_overlay.color = Color(0.02, 0.03, 0.06, 0.42)
	tint_overlay.position = Vector2.ZERO
	tint_overlay.size = Vector2(1080, 1920)
	add_child(tint_overlay)
	tint_overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)

	var main_vbox := VBoxContainer.new()
	main_vbox.position = Vector2(24, 20)
	main_vbox.size = Vector2(1032, 1880)
	main_vbox.add_theme_constant_override("separation", 14)
	add_child(main_vbox)

	# ==========================================================================
	# SECTION 1: TOP COMMANDER PROFILE & GAME TITLE HEADER
	# ==========================================================================
	var header_panel := _make_panel("header", 16)
	main_vbox.add_child(header_panel)

	var h_row := HBoxContainer.new()
	h_row.add_theme_constant_override("separation", 16)
	header_panel.add_child(h_row)

	var cmd_avatar := TextureRect.new()
	cmd_avatar.texture = GameState.tex("res://assets/ui_hud/avatars/commander_p1_blue.png")
	cmd_avatar.custom_minimum_size = Vector2(108, 108)
	cmd_avatar.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	cmd_avatar.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	h_row.add_child(cmd_avatar)

	var title_vbox := VBoxContainer.new()
	title_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title_vbox.alignment = BoxContainer.ALIGNMENT_CENTER
	title_vbox.add_theme_constant_override("separation", 4)
	h_row.add_child(title_vbox)

	var lbl_title := Label.new()
	lbl_title.text = "ARCANA FIVE: HUYẾT BÀI NGŨ HÀNH"
	lbl_title.add_theme_font_size_override("font_size", 29)
	lbl_title.add_theme_color_override("font_color", Color(1.0, 0.84, 0.28))
	lbl_title.add_theme_color_override("font_outline_color", Color(0.02, 0.02, 0.04, 0.98))
	lbl_title.add_theme_constant_override("outline_size", 4)
	title_vbox.add_child(lbl_title)

	var lbl_sub := Label.new()
	lbl_sub.text = "Đại Pháp Sư Lam Long (BẠN)  ·  Hạng: Huyền Thoại Ngũ Hành"
	lbl_sub.add_theme_font_size_override("font_size", 17)
	lbl_sub.add_theme_color_override("font_color", Color(0.68, 0.86, 1.0))
	title_vbox.add_child(lbl_sub)

	var stat_row := HBoxContainer.new()
	stat_row.add_theme_constant_override("separation", 14)
	title_vbox.add_child(stat_row)

	var coin_ico := TextureRect.new()
	coin_ico.texture = GameState.tex("res://assets/ui_hud/icons/icon_coin_gold.png")
	coin_ico.custom_minimum_size = Vector2(26, 26)
	coin_ico.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	coin_ico.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	stat_row.add_child(coin_ico)

	lbl_owned_stat = Label.new()
	lbl_owned_stat.add_theme_font_size_override("font_size", 17)
	lbl_owned_stat.add_theme_color_override("font_color", Color(1.0, 0.88, 0.38))
	stat_row.add_child(lbl_owned_stat)

	var dia_ico := TextureRect.new()
	dia_ico.texture = GameState.tex("res://assets/ui_hud/icons/icon_diamond_gem.png")
	dia_ico.custom_minimum_size = Vector2(26, 26)
	dia_ico.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	dia_ico.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	stat_row.add_child(dia_ico)

	lbl_pack_stat = Label.new()
	lbl_pack_stat.add_theme_font_size_override("font_size", 17)
	lbl_pack_stat.add_theme_color_override("font_color", Color(0.48, 0.92, 1.0))
	stat_row.add_child(lbl_pack_stat)

	var btn_guide := Button.new()
	btn_guide.text = "HƯỚNG DẪN\nLUẬT & 5 HỆ"
	btn_guide.icon = GameState.tex("res://assets/ui_hud/icons/icon_guide_book.png")
	btn_guide.expand_icon = true
	btn_guide.custom_minimum_size = Vector2(184, 88)
	btn_guide.add_theme_font_size_override("font_size", 16)
	btn_guide.add_theme_color_override("font_color", Color(1.0, 0.94, 0.72))
	GameState.apply_gui_button(btn_guide, "purple", false, 14, 8)
	btn_guide.pressed.connect(func():
		GameState.emit_signal("guide_requested", 0)
	)
	h_row.add_child(btn_guide)

	# ==========================================================================
	# SECTION 2: CENTRAL BATTLE ARENA & 4-COMMANDER MATCHMAKING PANEL
	# ==========================================================================
	var match_panel := _make_panel("section", 18)
	main_vbox.add_child(match_panel)

	var m_vbox := VBoxContainer.new()
	m_vbox.add_theme_constant_override("separation", 12)
	match_panel.add_child(m_vbox)

	var m_top_row := HBoxContainer.new()
	m_top_row.add_theme_constant_override("separation", 14)
	m_vbox.add_child(m_top_row)

	var m_icon := TextureRect.new()
	m_icon.texture = GameState.tex("res://assets/cards/icons/types/atk-phys/prop.png")
	m_icon.custom_minimum_size = Vector2(32, 32)
	m_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	m_icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	m_top_row.add_child(m_icon)

	var lbl_m_title := Label.new()
	lbl_m_title.text = "ĐẤU TRƯỜNG BÀN CỜ 4 GÓC — CHỌN CHẾ ĐỘ & ĐỐI THỦ"
	lbl_m_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	lbl_m_title.add_theme_font_size_override("font_size", 22)
	lbl_m_title.add_theme_color_override("font_color", Color(0.52, 0.86, 1.0))
	m_top_row.add_child(lbl_m_title)

	btn_bot_toggle = Button.new()
	btn_bot_toggle.icon = GameState.tex("res://assets/ui_hud/icons/icon_bot_ai.png")
	btn_bot_toggle.expand_icon = true
	btn_bot_toggle.custom_minimum_size = Vector2(330, 42)
	btn_bot_toggle.clip_text = true
	btn_bot_toggle.add_theme_font_size_override("font_size", 15)
	btn_bot_toggle.pressed.connect(func():
		GameState.player_is_bot = not GameState.player_is_bot
		GameState.save_game()
		refresh_ui()
	)
	m_top_row.add_child(btn_bot_toggle)

	# 4-Commander Corner Preview Strip (Shows P1..P4 with their distinct avatars; grays out empty corners in 2P/3P!)
	var cmd_row := HBoxContainer.new()
	cmd_row.add_theme_constant_override("separation", 12)
	m_vbox.add_child(cmd_row)

	var cmd_meta := [
		{"name": "GÓC P1 · BẠN", "role": "Lam Long Pháp Sư", "av": "res://assets/ui_hud/avatars/commander_p1_blue.png", "col": Color(0.32, 0.68, 1.0)},
		{"name": "GÓC P2 · ĐỎ", "role": "Huyết Ma Chiến Vương", "av": "res://assets/ui_hud/avatars/commander_p2_red.png", "col": Color(0.98, 0.36, 0.36)},
		{"name": "GÓC P3 · LÁ", "role": "Cổ Thụ Đại Drui", "av": "res://assets/ui_hud/avatars/commander_p3_green.png", "col": Color(0.35, 0.92, 0.55)},
		{"name": "GÓC P4 · VÀNG", "role": "Thái Dương Thánh Kỵ", "av": "res://assets/ui_hud/avatars/commander_p4_amber.png", "col": Color(0.98, 0.78, 0.24)},
	]
	commander_cards.clear()
	commander_avatars.clear()
	commander_status_lbls.clear()

	for i in range(4):
		var cm: Dictionary = cmd_meta[i]
		var cp := PanelContainer.new()
		cp.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		cp.custom_minimum_size = Vector2(0, 118)
		cmd_row.add_child(cp)
		commander_cards.append(cp)

		var cv := HBoxContainer.new()
		cv.add_theme_constant_override("separation", 10)
		cp.add_child(cv)

		var av := TextureRect.new()
		av.texture = GameState.tex(str(cm["av"]))
		av.custom_minimum_size = Vector2(78, 78)
		av.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		av.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		cv.add_child(av)
		commander_avatars.append(av)

		var iv := VBoxContainer.new()
		iv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		iv.alignment = BoxContainer.ALIGNMENT_CENTER
		iv.add_theme_constant_override("separation", 3)
		cv.add_child(iv)

		var l_name := Label.new()
		l_name.text = str(cm["name"])
		l_name.clip_text = true
		l_name.add_theme_font_size_override("font_size", 16)
		l_name.add_theme_color_override("font_color", cm["col"])
		iv.add_child(l_name)

		var l_role := Label.new()
		l_role.text = str(cm["role"])
		l_role.clip_text = true
		l_role.add_theme_font_size_override("font_size", 12)
		l_role.add_theme_color_override("font_color", Color(0.82, 0.86, 0.94))
		iv.add_child(l_role)

		var l_st := Label.new()
		l_st.clip_text = true
		l_st.add_theme_font_size_override("font_size", 13)
		iv.add_child(l_st)
		commander_status_lbls.append(l_st)

	# Player Count Selection Row (2, 3, or 4 Players)
	var p_btn_row := HBoxContainer.new()
	p_btn_row.add_theme_constant_override("separation", 12)
	m_vbox.add_child(p_btn_row)

	btn_p2 = _make_mode_button("2 NGƯỜI CHƠI (1v1)\nBộ bài 50 lá · Góc P3 & P4 Xám", 2)
	btn_p3 = _make_mode_button("3 NGƯỜI CHƠI (3 Góc)\nBộ bài 75 lá · Góc P4 Xám", 3)
	btn_p4 = _make_mode_button("4 NGƯỜI CHƠI (Đủ 4 Góc)\nBộ bài 100 lá · Hỗn Chiến 4 Bên", 4)
	p_btn_row.add_child(btn_p2)
	p_btn_row.add_child(btn_p3)
	p_btn_row.add_child(btn_p4)

	# Ornate Dragon-Crest PLAY BATTLE Button (Generated by Muse: btn_play_battle.png)
	var play_holder := HBoxContainer.new()
	play_holder.alignment = BoxContainer.ALIGNMENT_CENTER
	m_vbox.add_child(play_holder)

	var play_btn_info := _make_ornate_gui_button(
		"res://assets/ui_hud/gui/btn_play_battle.png",
		Vector2(880, 174),
		"VÀO BÀN ĐẤU NGAY (PLAY BATTLE)",
		"Chế độ 4 Người · Bộ Bài Chung 100 Lá · Hết Tướng Bị Đánh Thẳng Vào Góc!",
		Color(1.0, 0.92, 0.48),
		27,
		14,
		func():
			if not GameState.is_loadout_valid(GameState.loadout_deck).ok:
				GameState.auto_build_valid_loadout()
			GameState.emit_signal("screen_requested", "battle")
	)
	lbl_play_sub = play_btn_info["sub_label"]
	play_holder.add_child(play_btn_info["button"])

	# ==========================================================================
	# SECTION 3: DUAL ORNATE PORTAL NAVIGATION CARDS (GACHA PACKS & COLLECTION)
	# ==========================================================================
	var nav_row := HBoxContainer.new()
	nav_row.add_theme_constant_override("separation", 16)
	main_vbox.add_child(nav_row)

	var gacha_btn_info := _make_ornate_gui_button(
		"res://assets/ui_hud/gui/btn_nav_gacha.png",
		Vector2(508, 196),
		"ĐÀI TRIỆU HỒI RƯƠNG",
		"5 Cấp Pack · 10 Thẻ/Pack",
		Color(0.98, 0.84, 1.0),
		22,
		14,
		func(): GameState.emit_signal("screen_requested", "packs")
	)
	gacha_btn_info["button"].size_flags_horizontal = Control.SIZE_EXPAND_FILL
	lbl_gacha_sub = gacha_btn_info["sub_label"]
	nav_row.add_child(gacha_btn_info["button"])

	var col_btn_info := _make_ornate_gui_button(
		"res://assets/ui_hud/gui/btn_nav_collection.png",
		Vector2(508, 196),
		"KHO THẺ & BỘ BÀI",
		"500 Thẻ (100 Mẫu × 5 Hệ) · Xếp Bộ 15 Lá",
		Color(0.68, 0.98, 0.82),
		22,
		14,
		func(): GameState.emit_signal("screen_requested", "collection")
	)
	col_btn_info["button"].size_flags_horizontal = Control.SIZE_EXPAND_FILL
	lbl_col_sub = col_btn_info["sub_label"]
	nav_row.add_child(col_btn_info["button"])

	# ==========================================================================
	# SECTION 4: 15-CARD BATTLE LOADOUT DOCK
	# ==========================================================================
	var deck_panel := _make_panel("section", 16)
	deck_panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	main_vbox.add_child(deck_panel)

	var d_vbox := VBoxContainer.new()
	d_vbox.add_theme_constant_override("separation", 10)
	deck_panel.add_child(d_vbox)

	var d_head := HBoxContainer.new()
	d_head.add_theme_constant_override("separation", 12)
	d_vbox.add_child(d_head)

	var d_icon := TextureRect.new()
	d_icon.texture = GameState.tex("res://assets/cards/icons/types/tanker/prop.png")
	d_icon.custom_minimum_size = Vector2(30, 30)
	d_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	d_icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	d_head.add_child(d_icon)

	lbl_deck_status = Label.new()
	lbl_deck_status.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	lbl_deck_status.clip_text = true
	lbl_deck_status.add_theme_font_size_override("font_size", 15)
	lbl_deck_status.add_theme_color_override("font_color", Color(0.52, 0.96, 0.65))
	d_head.add_child(lbl_deck_status)

	var btn_auto_deck := Button.new()
	btn_auto_deck.text = "Tự Xếp 15 Lá Tối Ưu"
	btn_auto_deck.icon = GameState.tex("res://assets/cards/icons/stats/aspd/prop.png")
	btn_auto_deck.expand_icon = true
	btn_auto_deck.custom_minimum_size = Vector2(228, 46)
	btn_auto_deck.add_theme_font_size_override("font_size", 16)
	GameState.apply_gui_button(btn_auto_deck, "gold", false)
	btn_auto_deck.pressed.connect(func():
		GameState.auto_build_valid_loadout()
		refresh_ui()
	)
	d_head.add_child(btn_auto_deck)

	var btn_edit_deck := Button.new()
	btn_edit_deck.text = "Đổi Thẻ Trong Kho"
	btn_edit_deck.icon = GameState.tex("res://assets/ui_hud/icons/icon_cards_hand.png")
	btn_edit_deck.expand_icon = true
	btn_edit_deck.custom_minimum_size = Vector2(212, 46)
	btn_edit_deck.add_theme_font_size_override("font_size", 16)
	GameState.apply_gui_button(btn_edit_deck, "green", false)
	btn_edit_deck.pressed.connect(func(): GameState.emit_signal("screen_requested", "collection"))
	d_head.add_child(btn_edit_deck)

	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	d_vbox.add_child(scroll)

	deck_strip = HBoxContainer.new()
	deck_strip.add_theme_constant_override("separation", 14)
	scroll.add_child(deck_strip)


func _make_ornate_gui_button(
	tex_path: String,
	min_sz: Vector2,
	title_txt: String,
	sub_txt: String,
	title_col: Color,
	title_size: int,
	sub_size: int,
	on_click: Callable
) -> Dictionary:
	var btn := Button.new()
	btn.custom_minimum_size = min_sz
	btn.focus_mode = Control.FOCUS_NONE
	btn.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	var sb_n := StyleBoxTexture.new()
	sb_n.texture = GameState.tex(tex_path)
	var sb_h := sb_n.duplicate() as StyleBoxTexture
	sb_h.modulate_color = Color(1.08, 1.08, 1.08, 1.0)
	var sb_p := sb_n.duplicate() as StyleBoxTexture
	sb_p.modulate_color = Color(0.88, 0.88, 0.90, 1.0)
	btn.add_theme_stylebox_override("normal", sb_n)
	btn.add_theme_stylebox_override("hover", sb_h)
	btn.add_theme_stylebox_override("pressed", sb_p)
	btn.pressed.connect(on_click)

	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	margin.add_theme_constant_override("margin_left", 92)
	margin.add_theme_constant_override("margin_right", 34)
	margin.add_theme_constant_override("margin_top", 22)
	margin.add_theme_constant_override("margin_bottom", 22)
	margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	btn.add_child(margin)

	var vbox := VBoxContainer.new()
	vbox.alignment = BoxContainer.ALIGNMENT_CENTER
	vbox.add_theme_constant_override("separation", 4)
	vbox.mouse_filter = Control.MOUSE_FILTER_IGNORE
	margin.add_child(vbox)

	var l_title := Label.new()
	l_title.text = title_txt
	l_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l_title.clip_text = true
	l_title.add_theme_font_size_override("font_size", title_size)
	l_title.add_theme_color_override("font_color", title_col)
	l_title.add_theme_color_override("font_outline_color", Color(0.02, 0.01, 0.03, 0.98))
	l_title.add_theme_constant_override("outline_size", 5)
	l_title.mouse_filter = Control.MOUSE_FILTER_IGNORE
	vbox.add_child(l_title)

	var l_sub := Label.new()
	l_sub.text = sub_txt
	l_sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l_sub.clip_text = true
	l_sub.add_theme_font_size_override("font_size", sub_size)
	l_sub.add_theme_color_override("font_color", Color(0.92, 0.94, 0.98))
	l_sub.add_theme_color_override("font_outline_color", Color(0.02, 0.02, 0.04, 0.98))
	l_sub.add_theme_constant_override("outline_size", 4)
	l_sub.mouse_filter = Control.MOUSE_FILTER_IGNORE
	vbox.add_child(l_sub)

	return {"button": btn, "title_label": l_title, "sub_label": l_sub}


func _make_mode_button(label_txt: String, p_count: int) -> Button:
	var b := Button.new()
	b.text = label_txt
	b.clip_text = true
	b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	b.custom_minimum_size = Vector2(0, 74)
	b.add_theme_font_size_override("font_size", 16)
	b.pressed.connect(func():
		GameState.selected_player_count = p_count
		GameState.save_game()
		refresh_ui()
	)
	return b


func _style_mode_button(b: Button, active: bool) -> void:
	GameState.apply_gui_button(b, "gold" if active else "slate", false, 14, 10)
	b.add_theme_color_override("font_color", Color(1.0, 0.96, 0.80) if active else Color(0.84, 0.88, 0.94))


func _make_panel(variant: String = "section", pad: int = 16) -> PanelContainer:
	var p := PanelContainer.new()
	p.add_theme_stylebox_override("panel", GameState.make_gui_panel_style(variant, pad))
	return p


func refresh_ui() -> void:
	if not is_inside_tree():
		return
	var owned_u := GameState.get_owned_unique_count()
	var total_c := GameState.get_total_owned_copies()

	lbl_owned_stat.text = "Coin: %d   ·   Sở hữu: %d/500 Thẻ (%d Bản)" % [GameState.gold, owned_u, total_c]
	lbl_pack_stat.text = "Kim Cương: %d   ·   Rương: %d Pack" % [
		GameState.diamonds,
		GameState.pack_count,
	]

	var p_cnt := GameState.selected_player_count
	_style_mode_button(btn_p2, p_cnt == 2)
	_style_mode_button(btn_p3, p_cnt == 3)
	_style_mode_button(btn_p4, p_cnt == 4)

	# Update 4 Commander Corner Cards preview using hand-drawn 2D slot box frames
	for i in range(commander_cards.size()):
		var active_seat := (i < p_cnt)
		var cp: PanelContainer = commander_cards[i]
		if active_seat:
			cp.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("slot_active", 12))
			commander_avatars[i].modulate = Color(1, 1, 1, 1)
			commander_status_lbls[i].text = "100 HP · 10 Ô Thẻ"
			commander_status_lbls[i].add_theme_color_override("font_color", Color(0.48, 0.96, 0.62))
		else:
			cp.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("slot_gray", 12))
			commander_avatars[i].modulate = Color(0.42, 0.44, 0.48, 0.78)
			commander_status_lbls[i].text = "GÓC XÁM (Trống)"
			commander_status_lbls[i].add_theme_color_override("font_color", Color(0.75, 0.78, 0.82))

	if GameState.player_is_bot:
		btn_bot_toggle.text = "Bot Đánh Hộ: ĐANG BẬT"
		GameState.apply_gui_button(btn_bot_toggle, "green", false)
	else:
		btn_bot_toggle.text = "Tự Tay Chơi: ĐANG BẬT"
		GameState.apply_gui_button(btn_bot_toggle, "slate", false)

	if lbl_play_sub:
		lbl_play_sub.text = "Chế độ %d Người · Bộ Bài %d Lá · Hết Tướng Đánh Thẳng Vào Góc!" % [p_cnt, p_cnt * 25]
	if lbl_gacha_sub:
		lbl_gacha_sub.text = "Đang có %d Pack · P1-3 (Coin) · P4-5 (Kim Cương)" % GameState.pack_count
	if lbl_col_sub:
		lbl_col_sub.text = "Sở hữu %d/500 Thẻ (100 Mẫu × 5 Hệ) · Xếp Bộ 15 Lá" % owned_u

	var v_info := GameState.is_loadout_valid(GameState.loadout_deck)
	lbl_deck_status.text = "BỘ BÀI 15 LÁ — " + str(v_info.get("reason", ""))

	for child in deck_strip.get_children():
		child.queue_free()

	for entry in GameState.loadout_deck:
		var uid := str(entry)
		var base_id := GameState.get_base_card_id(uid)
		var el := GameState.get_card_element(uid)
		var cw: Control = CardWidget.new()
		cw.custom_minimum_size = Vector2(236, 354)
		cw.show_lock_if_unowned = false
		cw.setup(base_id, el)
		cw.card_clicked.connect(func(c_id, c_el): GameState.emit_signal("card_inspect_requested", c_id, c_el))
		deck_strip.add_child(cw)
