extends Control

const CardWidget := preload("res://scripts/components/CardWidget.gd")

var inp_email: LineEdit
var inp_name: LineEdit
var btn_google_login: Button
var lbl_status: Label
var lbl_server_state: Label
var _is_logging_in: bool = false


func _init() -> void:
	size = Vector2(1080, 1920)
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_build_ui()


func _ready() -> void:
	BackendClient.login_succeeded.connect(_on_login_succeeded)
	BackendClient.auth_state_changed.connect(_on_auth_state_changed)
	_refresh_status()


func _build_ui() -> void:
	# 1. Full-bleed 1080x1920 Dark-Fantasy Sanctuary Citadel Background
	var bg_tex := TextureRect.new()
	bg_tex.texture = GameState.tex("res://assets/ui_hud/gui/home_sanctuary_bg_1080x1920.png")
	bg_tex.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	bg_tex.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	bg_tex.position = Vector2.ZERO
	bg_tex.size = Vector2(1080, 1920)
	add_child(bg_tex)
	bg_tex.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)

	var dark_tint := ColorRect.new()
	dark_tint.color = Color(0.02, 0.03, 0.06, 0.62)
	dark_tint.position = Vector2.ZERO
	dark_tint.size = Vector2(1080, 1920)
	add_child(dark_tint)
	dark_tint.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)

	var main_vbox := VBoxContainer.new()
	main_vbox.position = Vector2(36, 36)
	main_vbox.size = Vector2(1008, 1848)
	main_vbox.alignment = BoxContainer.ALIGNMENT_CENTER
	main_vbox.add_theme_constant_override("separation", 18)
	add_child(main_vbox)

	# ==========================================================================
	# TOP BRANDING BANNER: ARCANA FIVE LOGO & SERVER STATUS
	# ==========================================================================
	var brand_panel := PanelContainer.new()
	brand_panel.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("header", 20))
	main_vbox.add_child(brand_panel)

	var brand_vbox := VBoxContainer.new()
	brand_vbox.alignment = BoxContainer.ALIGNMENT_CENTER
	brand_vbox.add_theme_constant_override("separation", 8)
	brand_panel.add_child(brand_vbox)

	var logo_row := HBoxContainer.new()
	logo_row.alignment = BoxContainer.ALIGNMENT_CENTER
	logo_row.add_theme_constant_override("separation", 20)
	brand_vbox.add_child(logo_row)

	var app_ico := TextureRect.new()
	app_ico.texture = GameState.tex("res://assets/ui_hud/branding/app_icon.png")
	app_ico.custom_minimum_size = Vector2(124, 124)
	app_ico.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	app_ico.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	logo_row.add_child(app_ico)

	var game_logo := TextureRect.new()
	game_logo.texture = GameState.tex("res://assets/ui_hud/branding/game_logo.png")
	game_logo.custom_minimum_size = Vector2(360, 150)
	game_logo.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	game_logo.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	logo_row.add_child(game_logo)

	var lbl_title := Label.new()
	lbl_title.text = "ARCANA FIVE: WUXING BLOOD CARDS"
	lbl_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lbl_title.add_theme_font_size_override("font_size", 28)
	lbl_title.add_theme_color_override("font_color", Color(1.0, 0.86, 0.32))
	lbl_title.add_theme_color_override("font_outline_color", Color(0.02, 0.02, 0.04, 0.98))
	lbl_title.add_theme_constant_override("outline_size", 5)
	brand_vbox.add_child(lbl_title)

	lbl_server_state = Label.new()
	lbl_server_state.text = "Máy chủ Cloud: https://be-card-g.vercel.app  ·  Hỗ trợ Online & Offline"
	lbl_server_state.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lbl_server_state.add_theme_font_size_override("font_size", 16)
	lbl_server_state.add_theme_color_override("font_color", Color(0.56, 0.90, 1.0))
	brand_vbox.add_child(lbl_server_state)

	# ==========================================================================
	# CENTER DIALOG: GOOGLE SIGN-IN & ACCOUNT AUTHENTICATION
	# ==========================================================================
	var auth_dialog := PanelContainer.new()
	auth_dialog.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("dialog", 26))
	main_vbox.add_child(auth_dialog)

	var auth_vbox := VBoxContainer.new()
	auth_vbox.add_theme_constant_override("separation", 16)
	auth_dialog.add_child(auth_vbox)

	var h_title_row := HBoxContainer.new()
	h_title_row.alignment = BoxContainer.ALIGNMENT_CENTER
	h_title_row.add_theme_constant_override("separation", 12)
	auth_vbox.add_child(h_title_row)

	var star_ico := TextureRect.new()
	star_ico.texture = GameState.tex("res://assets/ui_hud/icons/icon_star_new.png")
	star_ico.custom_minimum_size = Vector2(34, 34)
	star_ico.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	star_ico.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	h_title_row.add_child(star_ico)

	var lbl_auth_header := Label.new()
	lbl_auth_header.text = "YÊU CẦU ĐĂNG NHẬP TÀI KHOẢN GOOGLE"
	lbl_auth_header.add_theme_font_size_override("font_size", 26)
	lbl_auth_header.add_theme_color_override("font_color", Color(1.0, 0.88, 0.36))
	lbl_auth_header.add_theme_color_override("font_outline_color", Color(0.02, 0.02, 0.05, 0.98))
	lbl_auth_header.add_theme_constant_override("outline_size", 5)
	h_title_row.add_child(lbl_auth_header)

	var lbl_auth_desc := Label.new()
	lbl_auth_desc.text = "Đăng nhập bằng Google để đồng bộ hồ sơ Pháp Sư, bộ sưu tập 500 thẻ bài Ngũ Hành và tham gia ghép trận 2-4 người (tự động bù Bot sau 10s nếu thiếu người hoặc khi chơi Offline)."
	lbl_auth_desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	lbl_auth_desc.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lbl_auth_desc.add_theme_font_size_override("font_size", 17)
	lbl_auth_desc.add_theme_color_override("font_color", Color(0.86, 0.90, 0.96))
	auth_vbox.add_child(lbl_auth_desc)

	# Email & Commander Name inputs inside hand-drawn slot frames
	var form_grid := VBoxContainer.new()
	form_grid.add_theme_constant_override("separation", 12)
	auth_vbox.add_child(form_grid)

	var email_box := PanelContainer.new()
	email_box.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("slot_active", 12))
	form_grid.add_child(email_box)

	var email_row := HBoxContainer.new()
	email_row.add_theme_constant_override("separation", 14)
	email_box.add_child(email_row)

	var lbl_email_tag := Label.new()
	lbl_email_tag.text = "Tài khoản Google (Email):"
	lbl_email_tag.custom_minimum_size = Vector2(270, 0)
	lbl_email_tag.add_theme_font_size_override("font_size", 18)
	lbl_email_tag.add_theme_color_override("font_color", Color(1.0, 0.88, 0.42))
	email_row.add_child(lbl_email_tag)

	inp_email = LineEdit.new()
	inp_email.text = "dokhacchung98@gmail.com"
	inp_email.placeholder_text = "Nhập địa chỉ Gmail của bạn..."
	inp_email.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	inp_email.custom_minimum_size = Vector2(0, 52)
	inp_email.add_theme_font_size_override("font_size", 20)
	inp_email.add_theme_color_override("font_color", Color(0.96, 0.98, 1.0))
	inp_email.add_theme_stylebox_override("normal", GameState.make_gui_panel_style("slot_gray", 10))
	inp_email.add_theme_stylebox_override("focus", GameState.make_gui_panel_style("slot_active", 10))
	email_row.add_child(inp_email)

	var name_box := PanelContainer.new()
	name_box.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("slot_active", 12))
	form_grid.add_child(name_box)

	var name_row := HBoxContainer.new()
	name_row.add_theme_constant_override("separation", 14)
	name_box.add_child(name_row)

	var lbl_name_tag := Label.new()
	lbl_name_tag.text = "Danh hiệu Đại Pháp Sư:"
	lbl_name_tag.custom_minimum_size = Vector2(270, 0)
	lbl_name_tag.add_theme_font_size_override("font_size", 18)
	lbl_name_tag.add_theme_color_override("font_color", Color(0.62, 0.92, 1.0))
	name_row.add_child(lbl_name_tag)

	inp_name = LineEdit.new()
	inp_name.text = "Đại Pháp Sư Lam Long"
	inp_name.placeholder_text = "Nhập tên hiển thị trong trận..."
	inp_name.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	inp_name.custom_minimum_size = Vector2(0, 52)
	inp_name.add_theme_font_size_override("font_size", 20)
	inp_name.add_theme_color_override("font_color", Color(0.96, 0.98, 1.0))
	inp_name.add_theme_stylebox_override("normal", GameState.make_gui_panel_style("slot_gray", 10))
	inp_name.add_theme_stylebox_override("focus", GameState.make_gui_panel_style("slot_active", 10))
	name_row.add_child(inp_name)

	# Prominent Google Login Button
	btn_google_login = Button.new()
	btn_google_login.text = "ĐĂNG NHẬP BẰNG GOOGLE  —  VÀO ĐẠI SẢNH NGŨ HÀNH"
	btn_google_login.icon = GameState.tex("res://assets/ui_hud/icons/icon_star_new.png")
	btn_google_login.expand_icon = true
	btn_google_login.custom_minimum_size = Vector2(0, 92)
	btn_google_login.add_theme_font_size_override("font_size", 24)
	btn_google_login.add_theme_color_override("font_color", Color(1.0, 0.96, 0.82))
	GameState.apply_gui_button(btn_google_login, "gold", true, 28, 16)
	btn_google_login.pressed.connect(_on_google_login_pressed)
	auth_vbox.add_child(btn_google_login)

	lbl_status = Label.new()
	lbl_status.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lbl_status.add_theme_font_size_override("font_size", 17)
	lbl_status.add_theme_color_override("font_color", Color(0.55, 0.96, 0.68))
	auth_vbox.add_child(lbl_status)

	# ==========================================================================
	# BOTTOM SECTION: FIRST-LOGIN 15 DEFAULT STARTER CARDS GIFT PREVIEW
	# ==========================================================================
	var gift_panel := PanelContainer.new()
	gift_panel.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("section", 18))
	main_vbox.add_child(gift_panel)

	var gift_vbox := VBoxContainer.new()
	gift_vbox.add_theme_constant_override("separation", 10)
	gift_panel.add_child(gift_vbox)

	var gift_top := HBoxContainer.new()
	gift_top.add_theme_constant_override("separation", 12)
	gift_vbox.add_child(gift_top)

	var chest_ico := TextureRect.new()
	chest_ico.texture = GameState.tex("res://assets/ui_hud/icons/icon_pack_chest.png")
	chest_ico.custom_minimum_size = Vector2(36, 36)
	chest_ico.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	chest_ico.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	gift_top.add_child(chest_ico)

	var lbl_gift_title := Label.new()
	lbl_gift_title.text = "QUÀ TÂN THỦ ĐĂNG NHẬP LẦN ĐẦU: TẶNG NGAY 15 THẺ BÀI MẶC ĐỊNH CHUẨN DESIGN"
	lbl_gift_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	lbl_gift_title.add_theme_font_size_override("font_size", 19)
	lbl_gift_title.add_theme_color_override("font_color", Color(1.0, 0.86, 0.34))
	gift_top.add_child(lbl_gift_title)

	var lbl_gift_sub := Label.new()
	lbl_gift_sub.text = "Khi mới cài game và chưa có thẻ bài nào (0/500 thẻ), ngay trong lần đầu tiên đăng nhập Google bạn sẽ được tặng trọn bộ 15 Thẻ Khởi Đầu (3 Vật Lý · 3 Phép Thuật · 3 Đỡ Đòn · 3 Hỗ Trợ · 3 Trang Bị trải đều đủ 5 Hệ Kim - Mộc - Thủy - Hỏa - Thổ) và tự động lắp vào Bộ Bài Xuất Chiến 15/15!"
	lbl_gift_sub.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	lbl_gift_sub.add_theme_font_size_override("font_size", 15)
	lbl_gift_sub.add_theme_color_override("font_color", Color(0.82, 0.88, 0.95))
	gift_vbox.add_child(lbl_gift_sub)

	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(0, 366)
	scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	gift_vbox.add_child(scroll)

	var preview_strip := HBoxContainer.new()
	preview_strip.add_theme_constant_override("separation", 12)
	scroll.add_child(preview_strip)

	for uid_entry in GameState.DEFAULT_STARTER_15_UIDS:
		var uid := str(uid_entry)
		var base_id := GameState.get_base_card_id(uid)
		var el := GameState.get_card_element(uid)
		var cw: Control = CardWidget.new()
		cw.custom_minimum_size = Vector2(228, 342)
		cw.show_lock_if_unowned = false
		cw.setup(base_id, el)
		cw.card_clicked.connect(func(c_id, c_el): GameState.emit_signal("card_inspect_requested", c_id, c_el))
		preview_strip.add_child(cw)


func _refresh_status() -> void:
	if not is_inside_tree():
		return
	var owned_cnt := GameState.get_owned_unique_count()
	if BackendClient.is_online:
		lbl_server_state.text = "Máy chủ Cloud: ONLINE (%s)  ·  Firebase Auth & Matchmaking Sẵn Sàng" % BackendClient.backend_url
		lbl_server_state.add_theme_color_override("font_color", Color(0.48, 0.96, 0.65))
	else:
		lbl_server_state.text = "Máy chủ Cloud: Chế độ Offline Tự Động  ·  Đăng nhập Google & Đấu Bot 100% Hoạt Động"
		lbl_server_state.add_theme_color_override("font_color", Color(0.68, 0.88, 1.0))

	if owned_cnt == 0:
		lbl_status.text = "Trạng thái hiện tại: Chưa có thẻ bài nào (0/500)  ->  Đăng nhập Google lần đầu nhận ngay 15 Thẻ Mặc Định!"
	else:
		lbl_status.text = "Trạng thái hiện tại: Đã có %d/500 thẻ bài trong máy  ->  Đăng nhập Google để tiếp tục!" % owned_cnt


func _on_google_login_pressed() -> void:
	if _is_logging_in:
		return
	_is_logging_in = true
	btn_google_login.disabled = true
	btn_google_login.text = "ĐANG XÁC THỰC GOOGLE & NHẬN 15 THẺ KHỞI ĐẦU..."
	lbl_status.text = "Đang kết nối tài khoản Google và kiểm tra quà tân thủ 15 thẻ mặc định..."
	BackendClient.login_with_google(inp_email.text, inp_name.text)


func _on_auth_state_changed(_user: Dictionary) -> void:
	_refresh_status()


func _on_login_succeeded(_user: Dictionary, _is_first: bool) -> void:
	_is_logging_in = false
	GameState.emit_signal("screen_requested", "home")
