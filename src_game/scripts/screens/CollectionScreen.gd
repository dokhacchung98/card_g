extends Control

const CardWidget := preload("res://scripts/components/CardWidget.gd")

var filter_ownership: String = "all"     # all, owned, unowned, loadout
var filter_role: String = "all"          # all, atk_phys, atk_mag, tanker, support, item
var filter_rarity: String = "all"        # all, SSR, S, R, N
var filter_element: String = "all"       # all, kim, moc, thuy, hoa, tho
var sort_mode: String = "id_asc"         # id_asc, rarity_desc, rarity_asc, role, element, owned_desc
var quick_deck_toggle_mode: bool = false

var lbl_summary: Label
var lbl_loadout_bar: Label
var opt_ownership: OptionButton
var opt_role: OptionButton
var opt_rarity: OptionButton
var opt_element: OptionButton
var opt_sort: OptionButton
var btn_quick_mode: Button
var cards_grid: GridContainer


func _init() -> void:
	size = Vector2(1080, 1920)
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_build_ui()


func _ready() -> void:
	GameState.state_changed.connect(rebuild_grid)
	rebuild_grid()


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
	bg_overlay.color = Color(0.03, 0.04, 0.08, 0.65)
	bg_overlay.position = Vector2.ZERO
	bg_overlay.size = Vector2(1080, 1920)
	add_child(bg_overlay)
	bg_overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)

	var main_vbox := VBoxContainer.new()
	main_vbox.position = Vector2(24, 18)
	main_vbox.size = Vector2(1032, 1884)
	main_vbox.add_theme_constant_override("separation", 12)
	add_child(main_vbox)

	# 1. Header & Filter Panel
	var filter_panel := PanelContainer.new()
	filter_panel.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("section", 16))
	main_vbox.add_child(filter_panel)

	var f_vbox := VBoxContainer.new()
	f_vbox.add_theme_constant_override("separation", 10)
	filter_panel.add_child(f_vbox)

	var top_row := HBoxContainer.new()
	top_row.add_theme_constant_override("separation", 12)
	f_vbox.add_child(top_row)

	var btn_back := _make_back_home_button()
	top_row.add_child(btn_back)

	var col_icon := TextureRect.new()
	col_icon.texture = GameState.tex("res://assets/ui_hud/icons/icon_cards_hand.png")
	col_icon.custom_minimum_size = Vector2(34, 34)
	col_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	col_icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	top_row.add_child(col_icon)

	var lbl_title := Label.new()
	lbl_title.text = "KHO THẺ CỔ NGỮ"
	lbl_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	lbl_title.clip_text = true
	lbl_title.add_theme_font_size_override("font_size", 21)
	lbl_title.add_theme_color_override("font_color", Color(0.98, 0.80, 0.24))
	top_row.add_child(lbl_title)

	lbl_summary = Label.new()
	lbl_summary.add_theme_font_size_override("font_size", 16)
	lbl_summary.add_theme_color_override("font_color", Color(0.52, 0.95, 0.65))
	top_row.add_child(lbl_summary)

	var btn_guide := Button.new()
	btn_guide.text = "HƯỚNG DẪN"
	btn_guide.icon = GameState.tex("res://assets/ui_hud/icons/icon_guide_book.png")
	btn_guide.expand_icon = true
	btn_guide.custom_minimum_size = Vector2(158, 50)
	btn_guide.add_theme_font_size_override("font_size", 15)
	GameState.apply_gui_button(btn_guide, "purple", false, 12, 8)
	btn_guide.pressed.connect(func():
		GameState.emit_signal("guide_requested", 0)
	)
	top_row.add_child(btn_guide)

	# Filter Row 1: Ownership, Role, Rarity
	var row1 := HBoxContainer.new()
	row1.add_theme_constant_override("separation", 10)
	f_vbox.add_child(row1)

	opt_ownership = _make_dropdown([
		["all", "Sở hữu: Tất cả (500 Thẻ)", "res://assets/ui_hud/icons/icon_cards_hand.png"],
		["owned", "Đã sở hữu", "res://assets/ui_hud/icons/icon_star_new.png"],
		["unowned", "Chưa sở hữu", "res://assets/ui_hud/icons/icon_lock.png"],
		["loadout", "Trong Bộ Bài 15 Lá", "res://assets/cards/icons/types/tanker/prop.png"],
	], func(val):
		filter_ownership = val
		rebuild_grid()
	)
	row1.add_child(opt_ownership)

	opt_role = _make_dropdown([
		["all", "Loại thẻ: Tất cả (5 Nhóm)", "res://assets/cards/icons/types/atk-phys/prop.png"],
		["atk_phys", "Tấn Công Vật Lý (C01-C20)", "res://assets/cards/icons/types/atk-phys/prop.png"],
		["atk_mag", "Tấn Công Ma Pháp (C21-C40)", "res://assets/cards/icons/types/atk-mag/prop.png"],
		["tanker", "Tanker Đỡ Đòn (C41-C60)", "res://assets/cards/icons/types/tanker/prop.png"],
		["support", "Hỗ Trợ Support (C61-C80)", "res://assets/cards/icons/types/support/prop.png"],
		["item", "Vật Phẩm Item (C81-C100)", "res://assets/cards/icons/types/item/prop.png"],
	], func(val):
		filter_role = val
		rebuild_grid()
	)
	row1.add_child(opt_role)

	opt_rarity = _make_dropdown([
		["all", "Độ hiếm: Tất cả", "res://assets/ui_hud/icons/icon_star_new.png"],
		["SSR", "Bậc SSR (Huyền Thoại)", "res://assets/ui_hud/icons/icon_star_new.png"],
		["S", "Bậc S (Siêu Hiếm)", "res://assets/ui_hud/icons/icon_star_new.png"],
		["R", "Bậc R (Hiếm)", "res://assets/ui_hud/icons/icon_cards_hand.png"],
		["N", "Bậc N (Thường)", "res://assets/ui_hud/icons/icon_cards_hand.png"],
	], func(val):
		filter_rarity = val
		rebuild_grid()
	)
	row1.add_child(opt_rarity)

	# Filter Row 2: Element, Sort Mode, Quick Loadout Toggle
	var row2 := HBoxContainer.new()
	row2.add_theme_constant_override("separation", 10)
	f_vbox.add_child(row2)

	opt_element = _make_dropdown([
		["all", "Hệ Ngũ Hành: Tất cả", "res://assets/cards/icons/elements/ngu-hanh/prop.png"],
		["kim", "Hệ Kim (Metal)", "res://assets/cards/icons/elements/kim/prop.png"],
		["moc", "Hệ Mộc (Wood)", "res://assets/cards/icons/elements/moc/prop.png"],
		["thuy", "Hệ Thủy (Water)", "res://assets/cards/icons/elements/thuy/prop.png"],
		["hoa", "Hệ Hỏa (Fire)", "res://assets/cards/icons/elements/hoa/prop.png"],
		["tho", "Hệ Thổ (Earth)", "res://assets/cards/icons/elements/tho/prop.png"],
	], func(val):
		filter_element = val
		rebuild_grid()
	)
	row2.add_child(opt_element)

	opt_sort = _make_dropdown([
		["id_asc", "Sort: Mã thẻ (C001 -> C100)", "res://assets/ui_hud/icons/icon_cards_hand.png"],
		["rarity_desc", "Sort: Độ hiếm (SSR -> N)", "res://assets/ui_hud/icons/icon_star_new.png"],
		["rarity_asc", "Sort: Độ hiếm (N -> SSR)", "res://assets/ui_hud/icons/icon_star_new.png"],
		["role", "Sort: Theo Loại Thẻ", "res://assets/cards/icons/types/atk-phys/prop.png"],
		["element", "Sort: Theo Hệ Ngũ Hành", "res://assets/cards/icons/elements/ngu-hanh/prop.png"],
		["owned_desc", "Sort: Đã sở hữu lên đầu", "res://assets/ui_hud/icons/icon_cards_hand.png"],
	], func(val):
		sort_mode = val
		rebuild_grid()
	)
	row2.add_child(opt_sort)

	btn_quick_mode = Button.new()
	btn_quick_mode.custom_minimum_size = Vector2(280, 48)
	btn_quick_mode.add_theme_font_size_override("font_size", 17)
	btn_quick_mode.icon = GameState.tex("res://assets/ui_hud/icons/icon_cards_hand.png")
	btn_quick_mode.expand_icon = true
	btn_quick_mode.text = "Chạm Thẻ: Xem Chi Tiết"
	GameState.apply_gui_button(btn_quick_mode, "purple", false)
	btn_quick_mode.pressed.connect(func():
		quick_deck_toggle_mode = not quick_deck_toggle_mode
		btn_quick_mode.text = (
			"Chạm Thẻ: Chọn/Gỡ Bộ 15 Lá"
			if quick_deck_toggle_mode
			else "Chạm Thẻ: Xem Chi Tiết"
		)
		GameState.apply_gui_button(btn_quick_mode, "gold" if quick_deck_toggle_mode else "purple", false)
	)
	row2.add_child(btn_quick_mode)

	# Loadout Status Row
	var row3 := HBoxContainer.new()
	row3.add_theme_constant_override("separation", 12)
	f_vbox.add_child(row3)

	var ld_icon := TextureRect.new()
	ld_icon.texture = GameState.tex("res://assets/cards/icons/types/tanker/prop.png")
	ld_icon.custom_minimum_size = Vector2(28, 28)
	ld_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	ld_icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	row3.add_child(ld_icon)

	lbl_loadout_bar = Label.new()
	lbl_loadout_bar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	lbl_loadout_bar.clip_text = true
	lbl_loadout_bar.add_theme_font_size_override("font_size", 17)
	lbl_loadout_bar.add_theme_color_override("font_color", Color(0.86, 0.92, 0.98))
	row3.add_child(lbl_loadout_bar)

	var btn_reset_filters := Button.new()
	btn_reset_filters.text = "Đặt lại Bộ lọc"
	btn_reset_filters.custom_minimum_size = Vector2(170, 44)
	btn_reset_filters.add_theme_font_size_override("font_size", 16)
	GameState.apply_gui_button(btn_reset_filters, "wood", false)
	btn_reset_filters.pressed.connect(_reset_all_filters)
	row3.add_child(btn_reset_filters)

	# 2. Scrollable 4-Column Card Grid
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	main_vbox.add_child(scroll)

	cards_grid = GridContainer.new()
	cards_grid.columns = 4
	cards_grid.add_theme_constant_override("h_separation", 14)
	cards_grid.add_theme_constant_override("v_separation", 16)
	scroll.add_child(cards_grid)


func _make_back_home_button() -> Button:
	var b := Button.new()
	b.text = "SẢNH CHÍNH"
	b.custom_minimum_size = Vector2(190, 56)
	b.add_theme_font_size_override("font_size", 16)
	b.add_theme_color_override("font_color", Color(1.0, 0.92, 0.65))
	GameState.apply_gui_button(b, "back_home", false, 44, 8)
	b.pressed.connect(func(): GameState.emit_signal("screen_requested", "home"))
	return b


func _make_dropdown(items: Array, on_select: Callable) -> OptionButton:
	var ob := OptionButton.new()
	ob.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ob.clip_text = true
	ob.expand_icon = true
	ob.fit_to_longest_item = false
	ob.custom_minimum_size = Vector2(0, 48)
	ob.add_theme_font_size_override("font_size", 16)
	GameState.apply_gui_button(ob, "slate", false, 14, 8)
	for i in range(items.size()):
		if items[i].size() >= 3:
			var ic := GameState.tex(str(items[i][2]))
			if ic:
				ob.add_icon_item(ic, str(items[i][1]), i)
			else:
				ob.add_item(str(items[i][1]), i)
		else:
			ob.add_item(str(items[i][1]), i)
		ob.set_item_metadata(i, str(items[i][0]))
	ob.item_selected.connect(func(idx: int):
		var meta_val: String = str(ob.get_item_metadata(idx))
		on_select.call(meta_val)
	)
	return ob


func _reset_all_filters() -> void:
	filter_ownership = "all"
	filter_role = "all"
	filter_rarity = "all"
	filter_element = "all"
	sort_mode = "id_asc"
	opt_ownership.selected = 0
	opt_role.selected = 0
	opt_rarity.selected = 0
	opt_element.selected = 0
	opt_sort.selected = 0
	rebuild_grid()


func rebuild_grid() -> void:
	if not is_inside_tree():
		return

	var filtered: Array = []
	for c in GameState.cards_db:
		var cid: String = str(c["id"])
		var elem: String = str(c.get("element", "kim"))
		var is_owned := GameState.is_card_owned(cid, elem)
		var in_deck := GameState.is_card_in_loadout(cid, elem)

		if filter_ownership == "owned" and not is_owned:
			continue
		if filter_ownership == "unowned" and is_owned:
			continue
		if filter_ownership == "loadout" and not in_deck:
			continue
		if filter_role != "all" and str(c["role_group"]) != filter_role:
			continue
		if filter_rarity != "all" and str(c["rarity"]) != filter_rarity:
			continue
		if filter_element != "all" and elem != filter_element:
			continue

		filtered.append(c)

	var role_rank := {"atk_phys": 1, "atk_mag": 2, "tanker": 3, "support": 4, "item": 5}
	var elem_rank := {"kim": 1, "moc": 2, "thuy": 3, "hoa": 4, "tho": 5}

	filtered.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		var ca: String = str(a["id"])
		var cb: String = str(b["id"])
		var ea_str: String = str(a.get("element", "kim"))
		var eb_str: String = str(b.get("element", "kim"))
		var ra: int = int(GameState.RARITY_ORDER.get(str(a["rarity"]), 1))
		var rb: int = int(GameState.RARITY_ORDER.get(str(b["rarity"]), 1))

		if sort_mode == "rarity_desc":
			if ra != rb:
				return ra > rb
		elif sort_mode == "rarity_asc":
			if ra != rb:
				return ra < rb
		elif sort_mode == "role":
			var rga: int = int(role_rank.get(str(a["role_group"]), 9))
			var rgb: int = int(role_rank.get(str(b["role_group"]), 9))
			if rga != rgb:
				return rga < rgb
		elif sort_mode == "element":
			var ea: int = int(elem_rank.get(ea_str, 9))
			var eb: int = int(elem_rank.get(eb_str, 9))
			if ea != eb:
				return ea < eb
		elif sort_mode == "owned_desc":
			var oa: int = GameState.get_card_owned_count(ca, ea_str)
			var ob_cnt: int = GameState.get_card_owned_count(cb, eb_str)
			if oa != ob_cnt:
				return oa > ob_cnt

		return int(a.get("variant_num", a["num"])) < int(b.get("variant_num", b["num"]))
	)

	var existing_children := cards_grid.get_children()
	for i in range(filtered.size()):
		var c: Dictionary = filtered[i]
		var cid: String = str(c["id"])
		var elem: String = str(c.get("element", "kim"))
		var cw: Control
		if i < existing_children.size():
			cw = existing_children[i] as Control
			cw.visible = true
		else:
			cw = CardWidget.new()
			cw.custom_minimum_size = Vector2(244, 366)
			cw.show_lock_if_unowned = true
			cw.card_clicked.connect(func(c_id: String, el: String):
				if quick_deck_toggle_mode:
					var msg := GameState.toggle_card_in_loadout(c_id, el)
					lbl_loadout_bar.text = msg
				else:
					GameState.emit_signal("card_inspect_requested", c_id, el)
			)
			cw.card_secondary_clicked.connect(func(c_id: String, el: String):
				var msg := GameState.toggle_card_in_loadout(c_id, el)
				lbl_loadout_bar.text = msg
			)
			cards_grid.add_child(cw)
		cw.setup(cid, elem, false, false)

	for i in range(filtered.size(), existing_children.size()):
		var extra_cw := existing_children[i] as Control
		extra_cw.visible = false
		extra_cw.set_process(false)

	var owned_500 := GameState.get_owned_unique_count()
	lbl_summary.text = "Coin: %d · KC: %d | Hiển thị: %d/500 | Đã có: %d/500" % [
		GameState.gold,
		GameState.diamonds,
		filtered.size(),
		owned_500,
	]
	var v_info := GameState.is_loadout_valid(GameState.loadout_deck)
	lbl_loadout_bar.text = str(v_info.get("reason", ""))
