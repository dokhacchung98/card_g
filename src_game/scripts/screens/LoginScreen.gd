extends Control

var lbl_status: Label
var btn_google_login: Button
var is_submitting: bool = false


func _init() -> void:
	size = Vector2(1080, 1920)
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_build_ui()


func _ready() -> void:
	BackendClient.login_succeeded.connect(_on_login_succeeded)
	BackendClient.login_failed.connect(_on_login_failed)
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

	var root_scroll := ScrollContainer.new()
	root_scroll.position = Vector2(36, 40)
	root_scroll.size = Vector2(1008, 1840)
	GameState.setup_touch_scroll(root_scroll)
	add_child(root_scroll)

	var main_vbox := VBoxContainer.new()
	main_vbox.custom_minimum_size = Vector2(988, 1780)
	main_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	main_vbox.alignment = BoxContainer.ALIGNMENT_CENTER
	main_vbox.add_theme_constant_override("separation", 36)
	main_vbox.mouse_filter = Control.MOUSE_FILTER_PASS
	root_scroll.add_child(main_vbox)

	# 2. Top Branding Header Banner (Large Game Logo + Clean Title)
	var brand_panel := PanelContainer.new()
	brand_panel.mouse_filter = Control.MOUSE_FILTER_PASS
	brand_panel.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("header", 32))
	main_vbox.add_child(brand_panel)

	var brand_vbox := VBoxContainer.new()
	brand_vbox.alignment = BoxContainer.ALIGNMENT_CENTER
	brand_vbox.add_theme_constant_override("separation", 18)
	brand_vbox.mouse_filter = Control.MOUSE_FILTER_PASS
	brand_panel.add_child(brand_vbox)

	var logo_row := HBoxContainer.new()
	logo_row.alignment = BoxContainer.ALIGNMENT_CENTER
	logo_row.mouse_filter = Control.MOUSE_FILTER_PASS
	brand_vbox.add_child(logo_row)

	var logo_rect := TextureRect.new()
	logo_rect.texture = GameState.tex("res://assets/ui_hud/branding/game_logo.png")
	logo_rect.custom_minimum_size = Vector2(680, 260)
	logo_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	logo_rect.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	logo_rect.mouse_filter = Control.MOUSE_FILTER_PASS
	logo_row.add_child(logo_rect)

	var lbl_sub := Label.new()
	lbl_sub.text = "ĐẤU TRƯỜNG THẺ BÀI NGŨ HÀNH 4 GÓC"
	lbl_sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lbl_sub.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	lbl_sub.add_theme_font_size_override("font_size", 34)
	lbl_sub.add_theme_color_override("font_color", Color(1.0, 0.88, 0.36))
	lbl_sub.add_theme_constant_override("outline_size", 6)
	brand_vbox.add_child(lbl_sub)

	lbl_status = Label.new()
	lbl_status.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lbl_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	lbl_status.add_theme_font_size_override("font_size", 25)
	lbl_status.add_theme_color_override("font_color", Color(0.56, 0.98, 0.70))
	brand_vbox.add_child(lbl_status)

	# 3. Clean, Bold 1-Tap Google Sign-In Dialog
	var login_panel := PanelContainer.new()
	login_panel.mouse_filter = Control.MOUSE_FILTER_PASS
	login_panel.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("dialog", 36))
	main_vbox.add_child(login_panel)

	var login_vbox := VBoxContainer.new()
	login_vbox.alignment = BoxContainer.ALIGNMENT_CENTER
	login_vbox.add_theme_constant_override("separation", 28)
	login_vbox.mouse_filter = Control.MOUSE_FILTER_PASS
	login_panel.add_child(login_vbox)

	var title_row := HBoxContainer.new()
	title_row.alignment = BoxContainer.ALIGNMENT_CENTER
	title_row.add_theme_constant_override("separation", 16)
	title_row.mouse_filter = Control.MOUSE_FILTER_PASS
	login_vbox.add_child(title_row)

	var g_icon := TextureRect.new()
	g_icon.texture = GameState.tex("res://assets/cards/icons/elements/ngu-hanh/prop.png")
	g_icon.custom_minimum_size = Vector2(56, 56)
	g_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	g_icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	g_icon.mouse_filter = Control.MOUSE_FILTER_PASS
	title_row.add_child(g_icon)

	var lbl_login_title := Label.new()
	lbl_login_title.text = "ĐĂNG NHẬP GOOGLE"
	lbl_login_title.add_theme_font_size_override("font_size", 38)
	lbl_login_title.add_theme_color_override("font_color", Color(1.0, 0.88, 0.34))
	lbl_login_title.add_theme_constant_override("outline_size", 6)
	title_row.add_child(lbl_login_title)

	var gift_badge := PanelContainer.new()
	gift_badge.mouse_filter = Control.MOUSE_FILTER_PASS
	gift_badge.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("slot_active", 22))
	login_vbox.add_child(gift_badge)

	var lbl_desc := Label.new()
	lbl_desc.text = "Quà Tân Thủ: Tặng 15 Thẻ Khởi Đầu + 1.000 Vàng + 100 Kim Cương!"
	lbl_desc.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lbl_desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	lbl_desc.add_theme_font_size_override("font_size", 28)
	lbl_desc.add_theme_color_override("font_color", Color(0.96, 0.98, 1.0))
	gift_badge.add_child(lbl_desc)

	btn_google_login = Button.new()
	btn_google_login.custom_minimum_size = Vector2(0, 138)
	btn_google_login.icon = GameState.tex("res://assets/ui_hud/icons/icon_star_new.png")
	btn_google_login.expand_icon = true
	btn_google_login.text = "ĐĂNG NHẬP BẰNG GOOGLE"
	btn_google_login.add_theme_font_size_override("font_size", 34)
	btn_google_login.add_theme_color_override("font_color", Color(1.0, 0.97, 0.82))
	GameState.apply_gui_button(btn_google_login, "gold", true, 40, 22)
	btn_google_login.pressed.connect(_on_google_login_pressed)
	login_vbox.add_child(btn_google_login)


func _refresh_status() -> void:
	if not is_inside_tree() or lbl_status == null:
		return
	var srv_txt := "Trực tuyến (Cloud & Offline)" if BackendClient.is_online else "Chế độ Offline (Chơi với Bot)"
	lbl_status.text = "Trạng thái: %s" % srv_txt


func _on_auth_state_changed(_u: Dictionary) -> void:
	_refresh_status()


func _on_google_login_pressed() -> void:
	if is_submitting or GameState.is_touch_scrolling:
		return
	is_submitting = true
	btn_google_login.disabled = true
	btn_google_login.text = "ĐANG MỞ CỬA SỔ GOOGLE..."
	lbl_status.text = "Vui lòng chọn tài khoản và chấp thuận trong cửa sổ Google..."
	lbl_status.add_theme_color_override("font_color", Color(1.0, 0.9, 0.4))
	BackendClient.sign_in_with_google_oauth()


func _on_login_failed(err_msg: String) -> void:
	is_submitting = false
	btn_google_login.disabled = false
	btn_google_login.text = "ĐĂNG NHẬP BẰNG GOOGLE"
	lbl_status.text = "Lỗi đăng nhập: %s" % err_msg
	lbl_status.add_theme_color_override("font_color", Color(1.0, 0.42, 0.42))


func _on_login_succeeded(_user_profile: Dictionary, _is_first_login: bool) -> void:
	is_submitting = false
	btn_google_login.disabled = false
	btn_google_login.text = "ĐĂNG NHẬP BẰNG GOOGLE"
	GameState.emit_signal("screen_requested", "home")
