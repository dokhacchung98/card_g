extends Control

const CardWidget := preload("res://scripts/components/CardWidget.gd")

var lbl_status: Label
var btn_google_login: Button
var is_submitting: bool = false


func _init() -> void:
	size = Vector2(1080, 1920)
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_build_ui()


func _ready() -> void:
	BackendClient.login_succeeded.connect(_on_login_succeeded)
	BackendClient.auth_state_changed.connect(_on_auth_state_changed)
	_refresh_status()


func _build_ui() -> void:
	# 1. Full-Screen Dark-Fantasy Sanctuary Backdrop
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
	bg_overlay.color = Color(0.02, 0.03, 0.07, 0.72)
	bg_overlay.position = Vector2.ZERO
	bg_overlay.size = Vector2(1080, 1920)
	bg_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bg_overlay)
	bg_overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)

	# Full-screen vertical touch ScrollContainer for smooth swipe scrolling on App & Web
	var root_scroll := ScrollContainer.new()
	root_scroll.position = Vector2(24, 20)
	root_scroll.size = Vector2(1032, 1880)
	GameState.setup_touch_scroll(root_scroll)
	add_child(root_scroll)

	var main_vbox := VBoxContainer.new()
	main_vbox.custom_minimum_size = Vector2(1012, 0)
	main_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	main_vbox.add_theme_constant_override("separation", 22)
	main_vbox.mouse_filter = Control.MOUSE_FILTER_PASS
	root_scroll.add_child(main_vbox)

	# 2. Top Branding Header Banner (Logo + Game Title)
	var brand_panel := PanelContainer.new()
	brand_panel.mouse_filter = Control.MOUSE_FILTER_PASS
	brand_panel.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("header", 24))
	main_vbox.add_child(brand_panel)

	var brand_vbox := VBoxContainer.new()
	brand_vbox.alignment = BoxContainer.ALIGNMENT_CENTER
	brand_vbox.add_theme_constant_override("separation", 12)
	brand_vbox.mouse_filter = Control.MOUSE_FILTER_PASS
	brand_panel.add_child(brand_vbox)

	var logo_row := HBoxContainer.new()
	logo_row.alignment = BoxContainer.ALIGNMENT_CENTER
	logo_row.mouse_filter = Control.MOUSE_FILTER_PASS
	brand_vbox.add_child(logo_row)

	var logo_rect := TextureRect.new()
	logo_rect.texture = GameState.tex("res://assets/branding/arcana_five_game_logo.png")
	logo_rect.custom_minimum_size = Vector2(560, 210)
	logo_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	logo_rect.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	logo_rect.mouse_filter = Control.MOUSE_FILTER_PASS
	logo_row.add_child(logo_rect)

	var lbl_sub := Label.new()
	lbl_sub.text = "ARCANA OF THE FIVE ELEMENTS — ĐẤU TRƯỜNG THẺ BÀI NGŨ HÀNH 4 GÓC"
	lbl_sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lbl_sub.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	lbl_sub.add_theme_font_size_override("font_size", 24)
	lbl_sub.add_theme_color_override("font_color", Color(1.0, 0.88, 0.38))
	brand_vbox.add_child(lbl_sub)

	lbl_status = Label.new()
	lbl_status.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lbl_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	lbl_status.add_theme_font_size_override("font_size", 20)
	lbl_status.add_theme_color_override("font_color", Color(0.56, 0.96, 0.68))
	brand_vbox.add_child(lbl_status)

	# 3. One-Tap Google OAuth Sign-In Box (NO Email/Password Input Fields)
	var login_panel := PanelContainer.new()
	login_panel.mouse_filter = Control.MOUSE_FILTER_PASS
	login_panel.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("dialog", 28))
	main_vbox.add_child(login_panel)

	var login_vbox := VBoxContainer.new()
	login_vbox.add_theme_constant_override("separation", 18)
	login_vbox.mouse_filter = Control.MOUSE_FILTER_PASS
	login_panel.add_child(login_vbox)

	var title_row := HBoxContainer.new()
	title_row.alignment = BoxContainer.ALIGNMENT_CENTER
	title_row.add_theme_constant_override("separation", 14)
	title_row.mouse_filter = Control.MOUSE_FILTER_PASS
	login_vbox.add_child(title_row)

	var g_icon := TextureRect.new()
	g_icon.texture = GameState.tex("res://assets/cards/icons/elements/ngu-hanh/prop.png")
	g_icon.custom_minimum_size = Vector2(46, 46)
	g_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	g_icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	g_icon.mouse_filter = Control.MOUSE_FILTER_PASS
	title_row.add_child(g_icon)

	var lbl_login_title := Label.new()
	lbl_login_title.text = "ĐĂNG NHẬP TÀI KHOẢN GOOGLE"
	lbl_login_title.add_theme_font_size_override("font_size", 30)
	lbl_login_title.add_theme_color_override("font_color", Color(1.0, 0.88, 0.34))
	title_row.add_child(lbl_login_title)

	var lbl_desc := Label.new()
	lbl_desc.text = (
		"• Chạm 1 lần vào nút bên dưới để đăng nhập trực tiếp thông qua tài khoản Google (OAuth 2.0 / Firebase Auth).\n"
		+ "• Lần đăng nhập đầu tiên (tài khoản mới): Hệ thống TẶNG NGAY 15 THẺ BÀI KHỞI ĐẦU MẶC ĐỊNH + 1.000 Coin + 100 Kim Cương!"
	)
	lbl_desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	lbl_desc.add_theme_font_size_override("font_size", 21)
	lbl_desc.add_theme_color_override("font_color", Color(0.88, 0.94, 1.0))
	login_vbox.add_child(lbl_desc)

	btn_google_login = Button.new()
	btn_google_login.custom_minimum_size = Vector2(0, 118)
	btn_google_login.icon = GameState.tex("res://assets/ui_hud/icons/icon_star_new.png")
	btn_google_login.expand_icon = true
	btn_google_login.text = "ĐĂNG NHẬP BẰNG GOOGLE  —  VÀO GAME NGAY"
	btn_google_login.add_theme_font_size_override("font_size", 27)
	btn_google_login.add_theme_color_override("font_color", Color(1.0, 0.96, 0.78))
	GameState.apply_gui_button(btn_google_login, "gold", true, 36, 18)
	btn_google_login.pressed.connect(_on_google_login_pressed)
	login_vbox.add_child(btn_google_login)

	# 4. Preview of the 15 Default Starter Cards (Large 3x5 Grid — Swipe Up/Down to Scroll)
	var gift_panel := PanelContainer.new()
	gift_panel.mouse_filter = Control.MOUSE_FILTER_PASS
	gift_panel.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("section", 22))
	main_vbox.add_child(gift_panel)

	var gift_vbox := VBoxContainer.new()
	gift_vbox.add_theme_constant_override("separation", 16)
	gift_vbox.mouse_filter = Control.MOUSE_FILTER_PASS
	gift_panel.add_child(gift_vbox)

	var gift_head := HBoxContainer.new()
	gift_head.alignment = BoxContainer.ALIGNMENT_CENTER
	gift_head.add_theme_constant_override("separation", 12)
	gift_head.mouse_filter = Control.MOUSE_FILTER_PASS
	gift_vbox.add_child(gift_head)

	var star_ic := TextureRect.new()
	star_ic.texture = GameState.tex("res://assets/ui_hud/icons/icon_cards_hand.png")
	star_ic.custom_minimum_size = Vector2(38, 38)
	star_ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	star_ic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	star_ic.mouse_filter = Control.MOUSE_FILTER_PASS
	gift_head.add_child(star_ic)

	var lbl_gift_title := Label.new()
	lbl_gift_title.text = "QUÀ TẶNG TÂN THỦ LẦN ĐẦU LOGIN: BỘ 15 THẺ KHỞI ĐẦU CHUẨN"
	lbl_gift_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	lbl_gift_title.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	lbl_gift_title.add_theme_font_size_override("font_size", 23)
	lbl_gift_title.add_theme_color_override("font_color", Color(0.52, 0.96, 0.68))
	gift_head.add_child(lbl_gift_title)

	var lbl_gift_sub := Label.new()
	lbl_gift_sub.text = "Gồm 3 Công Vật Lý · 3 Công Phép · 3 Tanker · 3 Hỗ Trợ · 3 Vật Phẩm (5 Hệ Kim/Mộc/Thủy/Hỏa/Thổ) — Vuốt lên/xuống để xem, chạm thẻ để đọc chi tiết:"
	lbl_gift_sub.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	lbl_gift_sub.add_theme_font_size_override("font_size", 19)
	lbl_gift_sub.add_theme_color_override("font_color", Color(0.84, 0.90, 0.98))
	gift_vbox.add_child(lbl_gift_sub)

	var grid_center := HBoxContainer.new()
	grid_center.alignment = BoxContainer.ALIGNMENT_CENTER
	grid_center.mouse_filter = Control.MOUSE_FILTER_PASS
	gift_vbox.add_child(grid_center)

	var starter_grid := GridContainer.new()
	starter_grid.columns = 3
	starter_grid.add_theme_constant_override("h_separation", 16)
	starter_grid.add_theme_constant_override("v_separation", 18)
	starter_grid.mouse_filter = Control.MOUSE_FILTER_PASS
	grid_center.add_child(starter_grid)

	for uid in GameState.DEFAULT_STARTER_15_UIDS:
		var cid := GameState.get_base_card_id(uid)
		var elem := GameState.get_card_element(uid)
		var cw := CardWidget.new()
		cw.custom_minimum_size = Vector2(306, 459)
		cw.show_lock_if_unowned = false
		cw.is_new_badge = true
		cw.setup(cid, elem, false, false)
		cw.card_clicked.connect(func(c_id: String, el: String):
			GameState.emit_signal("card_inspect_requested", c_id, el)
		)
		starter_grid.add_child(cw)


func _refresh_status() -> void:
	if not is_inside_tree() or lbl_status == null:
		return
	var srv_txt := "ONLINE (https://be-card-g.vercel.app)" if BackendClient.is_online else "Sẵn sàng kết nối Cloud / Hỗ trợ Offline 100%"
	lbl_status.text = "Máy chủ Firebase & Vercel: %s" % srv_txt


func _on_auth_state_changed(_u: Dictionary) -> void:
	_refresh_status()


func _on_google_login_pressed() -> void:
	if is_submitting or GameState.is_touch_scrolling:
		return
	is_submitting = true
	btn_google_login.disabled = true
	btn_google_login.text = "ĐANG XÁC THỰC GOOGLE OAUTH & NHẬN 15 THẺ KHỞI ĐẦU..."
	BackendClient.sign_in_with_google_oauth()


func _on_login_succeeded(_user_profile: Dictionary, _is_first_login: bool) -> void:
	is_submitting = false
	GameState.emit_signal("screen_requested", "home")
