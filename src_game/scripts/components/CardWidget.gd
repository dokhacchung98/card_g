extends Control

signal card_clicked(card_id: String, element: String)
signal card_secondary_clicked(card_id: String, element: String)

var card_id: String = "C001"
var element: String = "kim"
var face_down: bool = false
var show_lock_if_unowned: bool = true
var is_new_badge: bool = false
var is_selected_highlight: bool = false
var use_hd_frame: bool = false
var show_gacha_glow: bool = false
var is_flipping: bool = false
var glow_time: float = 0.0
var _glow_accum: float = 0.0
var _cached_card: Dictionary = {}
var _cached_rarity: String = "N"
var _sb_glow_outer: StyleBoxFlat
var _sb_glow_mid: StyleBoxFlat
var _sb_glow_core: StyleBoxFlat
static var _text_layout_cache: Dictionary = {}

var flip_scale_x: float = 1.0:
	set(v):
		flip_scale_x = clampf(v, 0.02, 1.2)
		queue_redraw()
var flip_flash_alpha: float = 0.0:
	set(v):
		flip_flash_alpha = clampf(v, 0.0, 1.0)
		queue_redraw()


func _ready() -> void:
	clip_contents = false
	_update_process_mode()


func _update_process_mode() -> void:
	var should_pulse := (not face_down) and (_cached_rarity == "S" or _cached_rarity == "SSR")
	set_process(should_pulse)


func _process(delta: float) -> void:
	if not is_visible_in_tree() or face_down:
		return
	glow_time += delta * 3.2
	_glow_accum += delta
	if _glow_accum >= 0.05:
		_glow_accum = 0.0
		queue_redraw()


func play_flip_reveal_anim(delay_sec: float = 0.0) -> void:
	if not face_down or is_flipping:
		return
	is_flipping = true
	if delay_sec > 0.0:
		await get_tree().create_timer(delay_sec).timeout
	if not is_inside_tree():
		return
	var tw1 := create_tween()
	tw1.tween_property(self, "flip_scale_x", 0.04, 0.14).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN)
	await tw1.finished
	if not is_inside_tree():
		return
	face_down = false
	_update_process_mode()
	flip_flash_alpha = 0.90
	queue_redraw()
	var tw2 := create_tween().set_parallel(true)
	tw2.tween_property(self, "flip_scale_x", 1.0, 0.18).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw2.tween_property(self, "flip_flash_alpha", 0.0, 0.36).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	await tw2.finished
	is_flipping = false
	queue_redraw()


var _press_global_pos: Vector2 = Vector2.ZERO
var _is_pressed_down: bool = false


func setup(p_card_id: String, p_element: String = "", p_face_down: bool = false, p_hd: bool = false) -> void:
	card_id = GameState.get_base_card_id(p_card_id)
	element = p_element if not p_element.is_empty() else GameState.get_card_element(p_card_id)
	face_down = p_face_down
	use_hd_frame = p_hd
	_cached_card = GameState.get_card(card_id)
	_cached_rarity = str(_cached_card.get("rarity", "N"))
	clip_contents = false
	mouse_filter = Control.MOUSE_FILTER_PASS
	mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	_update_process_mode()
	queue_redraw()


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		var mb: InputEventMouseButton = event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_LEFT:
			if mb.pressed:
				_is_pressed_down = true
				_press_global_pos = mb.global_position
			else:
				if _is_pressed_down:
					_is_pressed_down = false
					var dist: float = mb.global_position.distance_to(_press_global_pos)
					if dist <= 18.0 and not GameState.is_touch_scrolling:
						emit_signal("card_clicked", card_id, element)
		elif mb.button_index == MOUSE_BUTTON_RIGHT and mb.pressed:
			if not GameState.is_touch_scrolling:
				emit_signal("card_secondary_clicked", card_id, element)



func _draw() -> void:
	var w := size.x
	var h := size.y
	if w <= 4 or h <= 4:
		return

	draw_set_transform(Vector2(w * (1.0 - flip_scale_x) * 0.5, 0.0), 0.0, Vector2(flip_scale_x, 1.0))

	if _cached_card.is_empty():
		_cached_card = GameState.get_card(card_id)
		_cached_rarity = str(_cached_card.get("rarity", "N"))
	var card := _cached_card
	var rarity := _cached_rarity

	if face_down:
		var back_tex := GameState.tex("res://assets/mobile/cards/frames/card_back_slot_256x384.png")
		if back_tex:
			draw_texture_rect(back_tex, Rect2(0, 0, w, h), false)
		else:
			draw_rect(Rect2(0, 0, w, h), Color(0.12, 0.14, 0.22), true)
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
		return

	if card.is_empty():
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
		return

	var role_group: String = card.get("role_group", "atk_phys")
	var owned_cnt: int = GameState.get_card_owned_count(card_id, element)
	var is_owned: bool = owned_cnt > 0
	var in_loadout: bool = GameState.is_card_in_loadout(card_id, element)
	var font := GameState.get_font()
	var num_font := GameState.get_num_font()

	# Scale factors from 512x768 reference layout
	var sx := w / 512.0
	var sy := h / 768.0

	# 1. Backing inside card outer bounds (46, 38, 419, 697) + Glowing Shadow Aura for flipped S / SSR cards
	var outer_rect := Rect2(46.0 * sx, 38.0 * sy, 419.0 * sx, 697.0 * sy)
	if rarity in ["S", "SSR"] and (not show_lock_if_unowned or is_owned):
		_draw_rarity_glow_shadow(outer_rect, rarity, sx)

	draw_rect(outer_rect, Color(0.06, 0.08, 0.12, 0.96), true)

	# 2. Card Artwork Window (79, 133, 354, 253)
	var art_rect := Rect2(79.0 * sx, 133.0 * sy, 354.0 * sx, 253.0 * sy)
	var art_tex := GameState.tex(str(card.get("card_art", "")))
	if art_tex:
		draw_texture_rect(art_tex, art_rect, false)
	else:
		draw_rect(art_rect, Color(0.14, 0.16, 0.22), true)

	# 3. Rarity Frame Overlay + Crisp Rarity-Colored Card Border (N=Silver, R=Blue, S=Purple, SSR=Gold)
	var rarity_col: Color = GameState.RARITY_COLOR.get(rarity, Color(0.78, 0.82, 0.88))
	var frame_suffix := "hd_512x768" if use_hd_frame else "slot_256x384"
	var frame_path := "res://assets/mobile/cards/frames/frame_%s_%s.png" % [rarity, frame_suffix]
	var frame_tex := GameState.tex(frame_path)
	if frame_tex:
		draw_texture_rect(frame_tex, Rect2(0, 0, w, h), false)
	var border_w := maxf(2.0, (4.2 if rarity in ["S", "SSR"] else 3.2) * sx)
	draw_rect(outer_rect, Color(rarity_col.r, rarity_col.g, rarity_col.b, 0.96), false, border_w)
	draw_rect(art_rect, Color(rarity_col.r, rarity_col.g, rarity_col.b, 0.72), false, maxf(1.5, 2.2 * sx))

	# 4. Element Socket Icon (cx=90, cy=139, r=23) & Type Socket Icon (cx=422, cy=139, r=23)
	var elem_meta: Dictionary = GameState.ELEMENT_META.get(element, GameState.ELEMENT_META["kim"])
	var elem_tex := GameState.tex(str(elem_meta.get("icon", "")))
	var sock_r := 22.0 * sx
	if elem_tex:
		draw_texture_rect(elem_tex, Rect2(90.0 * sx - sock_r, 139.0 * sy - sock_r, sock_r * 2.0, sock_r * 2.0), false)

	var role_meta: Dictionary = GameState.ROLE_META.get(role_group, GameState.ROLE_META["atk_phys"])
	var role_tex := GameState.tex(str(role_meta.get("icon", "")))
	if role_tex:
		draw_texture_rect(role_tex, Rect2(422.0 * sx - sock_r, 139.0 * sy - sock_r, sock_r * 2.0, sock_r * 2.0), false)

	# 5. Name Header Slot (77, 63, 358, 42) — Auto-fitted Outlined Title (never clips!)
	var name_rect := Rect2(74.0 * sx, 62.0 * sy, 364.0 * sx, 44.0 * sy)
	var card_name: String = str(card.get("name", card_id))
	var max_name_w := name_rect.size.x - 8.0 * sx
	var name_fsize := maxi(11, int(30.0 * sx))
	var min_name_fsize := maxi(9, int(18.0 * sx))
	while name_fsize > min_name_fsize:
		var measured_w := font.get_string_size(card_name, HORIZONTAL_ALIGNMENT_LEFT, -1, name_fsize).x
		if measured_w <= max_name_w:
			break
		name_fsize -= 1
	var name_outline := maxi(2, int(5.0 * sx))
	var name_pos := Vector2(name_rect.position.x + 4.0 * sx, name_rect.position.y + name_rect.size.y * 0.5 + float(name_fsize) * 0.36)
	draw_string_outline(
		font,
		name_pos,
		card_name,
		HORIZONTAL_ALIGNMENT_CENTER,
		max_name_w,
		name_fsize,
		name_outline,
		Color(0.01, 0.01, 0.03, 0.98)
	)
	draw_string(
		font,
		name_pos,
		card_name,
		HORIZONTAL_ALIGNMENT_CENTER,
		max_name_w,
		name_fsize,
		Color(1.0, 0.96, 0.84)
	)

	# 6. Skill Description Box (78, 410, 357, 118) — Strictly Clamped inside Box
	var skill_rect := Rect2(80.0 * sx, 410.0 * sy, 352.0 * sx, 118.0 * sy)
	var skill_desc: String = str(card.get("skill_desc", ""))
	if w >= 120.0 and not skill_desc.is_empty():
		_draw_responsive_text_box(
			font,
			skill_rect,
			skill_desc,
			maxi(11, int(25.5 * sx)),
			maxi(9, int(17.5 * sx)),
			Color(0.96, 0.98, 1.0),
			HORIZONTAL_ALIGNMENT_CENTER
		)

	# 7. Stats Grid (76, 547, 360, 112) — Clean 2x2 Grid of 4 Core Stats (HP, Dame, Def, Range)
	var is_item: bool = bool(card.get("is_item", false))
	var stat_fsize := maxi(12, int(31.0 * sx))
	var stat_outline := maxi(2, int(5.0 * sx))
	var stats_bg := Rect2(76.0 * sx, 547.0 * sy, 360.0 * sx, 112.0 * sy)
	draw_rect(stats_bg, Color(0.05, 0.07, 0.12, 0.94), true)
	draw_rect(stats_bg, Color(rarity_col.r, rarity_col.g, rarity_col.b, 0.62), false, 1.8)

	if is_item:
		var item_box := Rect2(82.0 * sx, 552.0 * sy, 348.0 * sx, 102.0 * sy)
		var item_txt := "DÙNG NGAY KHI LẬT BÀI"
		_draw_responsive_text_box(
			font,
			item_box,
			item_txt,
			maxi(11, int(27.0 * sx)),
			maxi(9, int(19.0 * sx)),
			Color(1.0, 0.88, 0.36),
			HORIZONTAL_ALIGNMENT_CENTER
		)
	else:
		var stat_vals := [
			["hp", "%d" % int(round(float(card.get("hp", 0)))), Color(0.46, 0.98, 0.56)],
			["dame", "%d" % int(round(float(card.get("dame", 0)))), Color(1.0, 0.56, 0.44)],
			["def", "%d" % int(round(float(card.get("def", 0)))), Color(0.96, 0.84, 0.56)],
			["range", "%.1f" % float(card.get("range", 1.2)), Color(0.64, 0.88, 1.0)],
		]
		var col_x := [92.0, 268.0]
		var row_y := [554.0, 606.0]
		for s_i in range(4):
			var r_idx := s_i / 2
			var c_idx := s_i % 2
			var bx: float = col_x[c_idx] * sx
			var by: float = row_y[r_idx] * sy
			var s_info: Array = stat_vals[s_i]
			var s_icon := GameState.tex("res://assets/cards/icons/stats/%s/prop.png" % s_info[0])
			if s_icon:
				draw_texture_rect(s_icon, Rect2(bx, by + 2.0 * sy, 38.0 * sx, 38.0 * sy), false)
			var s_pos := Vector2(bx + 44.0 * sx, by + 20.0 * sy + float(stat_fsize) * 0.38)
			draw_string_outline(
				num_font,
				s_pos,
				str(s_info[1]),
				HORIZONTAL_ALIGNMENT_LEFT,
				120.0 * sx,
				stat_fsize,
				stat_outline,
				Color(0.01, 0.01, 0.03, 0.98)
			)
			draw_string(
				num_font,
				s_pos,
				str(s_info[1]),
				HORIZONTAL_ALIGNMENT_LEFT,
				120.0 * sx,
				stat_fsize,
				s_info[2]
			)

	# 8. Card ID Slot & Clean Loadout / Owned / Linh Lực Cost Badge
	var energy_cost: int = GameState.get_card_energy_cost(card_id)
	var id_fsize := maxi(9, int(20.0 * sx))
	var id_outline := maxi(2, int(4.5 * sx))
	var id_text := "%s · %dLL" % [card_id, energy_cost] if show_lock_if_unowned else card_id
	draw_string_outline(
		font,
		Vector2(316.0 * sx, 688.0 * sy + float(id_fsize) * 0.45),
		id_text,
		HORIZONTAL_ALIGNMENT_CENTER,
		126.0 * sx,
		id_fsize,
		id_outline,
		Color(0.01, 0.01, 0.03, 0.98)
	)
	draw_string(
		font,
		Vector2(316.0 * sx, 688.0 * sy + float(id_fsize) * 0.45),
		id_text,
		HORIZONTAL_ALIGNMENT_CENTER,
		126.0 * sx,
		id_fsize,
		GameState.RARITY_COLOR.get(rarity, Color.WHITE)
	)

	if not show_lock_if_unowned:
		var cost_rect := Rect2(76.0 * sx, 672.0 * sy, 162.0 * sx, 34.0 * sy)
		draw_rect(cost_rect, Color(0.06, 0.20, 0.34, 0.96), true)
		draw_rect(cost_rect, Color(0.36, 0.86, 1.0, 0.92), false, 2.0)
		var bolt_tex := GameState.tex("res://assets/ui_hud/icons/icon_bolt_fast.png")
		if bolt_tex:
			draw_texture_rect(bolt_tex, Rect2(cost_rect.position.x + 6.0 * sx, cost_rect.position.y + 4.0 * sy, 26.0 * sx, 26.0 * sy), false)
		var cost_fsize := maxi(9, int(19.0 * sx))
		var cost_str := "%d LINH LỰC" % energy_cost
		draw_string_outline(
			font,
			Vector2(cost_rect.position.x + 28.0 * sx, cost_rect.position.y + cost_rect.size.y * 0.5 + float(cost_fsize) * 0.36),
			cost_str,
			HORIZONTAL_ALIGNMENT_CENTER,
			cost_rect.size.x - 30.0 * sx,
			cost_fsize,
			maxi(2, int(4.0 * sx)),
			Color(0.01, 0.01, 0.03, 0.98)
		)
		draw_string(
			font,
			Vector2(cost_rect.position.x + 28.0 * sx, cost_rect.position.y + cost_rect.size.y * 0.5 + float(cost_fsize) * 0.36),
			cost_str,
			HORIZONTAL_ALIGNMENT_CENTER,
			cost_rect.size.x - 30.0 * sx,
			cost_fsize,
			Color(0.56, 0.94, 1.0)
		)
	elif in_loadout and show_lock_if_unowned:
		var badge_rect := Rect2(76.0 * sx, 672.0 * sy, 180.0 * sx, 34.0 * sy)
		draw_rect(badge_rect, Color(0.12, 0.56, 0.28, 0.96), true)
		draw_rect(badge_rect, Color(0.42, 0.98, 0.58), false, 2.0)
		var b_fsize := maxi(9, int(20.0 * sx))
		draw_string_outline(
			font,
			Vector2(badge_rect.position.x, badge_rect.position.y + badge_rect.size.y * 0.5 + float(b_fsize) * 0.36),
			"ĐÃ CHỌN",
			HORIZONTAL_ALIGNMENT_CENTER,
			badge_rect.size.x,
			b_fsize,
			maxi(2, int(4.0 * sx)),
			Color(0.01, 0.01, 0.03, 0.98)
		)
		draw_string(
			font,
			Vector2(badge_rect.position.x, badge_rect.position.y + badge_rect.size.y * 0.5 + float(b_fsize) * 0.36),
			"ĐÃ CHỌN",
			HORIZONTAL_ALIGNMENT_CENTER,
			badge_rect.size.x,
			b_fsize,
			Color.WHITE
		)
	elif is_owned and owned_cnt > 0 and show_lock_if_unowned:
		var cnt_rect := Rect2(76.0 * sx, 672.0 * sy, 110.0 * sx, 34.0 * sy)
		draw_rect(cnt_rect, Color(0.08, 0.14, 0.22, 0.92), true)
		var c_fsize := maxi(9, int(20.0 * sx))
		draw_string_outline(
			font,
			Vector2(cnt_rect.position.x, cnt_rect.position.y + cnt_rect.size.y * 0.5 + float(c_fsize) * 0.36),
			"x%d" % owned_cnt,
			HORIZONTAL_ALIGNMENT_CENTER,
			cnt_rect.size.x,
			c_fsize,
			maxi(2, int(4.0 * sx)),
			Color(0.01, 0.01, 0.03, 0.98)
		)
		draw_string(
			font,
			Vector2(cnt_rect.position.x, cnt_rect.position.y + cnt_rect.size.y * 0.5 + float(c_fsize) * 0.36),
			"x%d" % owned_cnt,
			HORIZONTAL_ALIGNMENT_CENTER,
			cnt_rect.size.x,
			c_fsize,
			Color(0.56, 0.96, 0.68)
		)

	if is_new_badge:
		var new_rect := Rect2(54.0 * sx, 14.0 * sy, 134.0 * sx, 38.0 * sy)
		draw_rect(new_rect, Color(0.92, 0.18, 0.24, 0.96), true)
		draw_rect(new_rect, Color(1.0, 0.86, 0.28), false, 1.5)
		var star_tex := GameState.tex("res://assets/ui_hud/icons/icon_star_new.png")
		if star_tex:
			draw_texture_rect(star_tex, Rect2(new_rect.position.x + 5.0 * sx, new_rect.position.y + 5.0 * sy, 28.0 * sx, 28.0 * sy), false)
		var new_fsize := maxi(9, int(20.0 * sx))
		draw_string(
			font,
			Vector2(new_rect.position.x + 28.0 * sx, new_rect.position.y + new_rect.size.y * 0.5 + float(new_fsize) * 0.36),
			"MỚI!",
			HORIZONTAL_ALIGNMENT_CENTER,
			new_rect.size.x - 28.0 * sx,
			new_fsize,
			Color(1.0, 0.96, 0.75)
		)

	if show_lock_if_unowned and not is_owned:
		draw_rect(outer_rect, Color(0.03, 0.04, 0.07, 0.68), true)
		var lock_banner := Rect2(76.0 * sx, 232.0 * sy, 360.0 * sx, 60.0 * sy)
		draw_rect(lock_banner, Color(0.08, 0.09, 0.14, 0.96), true)
		draw_rect(lock_banner, Color(0.55, 0.60, 0.70, 0.85), false, 2.0)
		var lock_tex := GameState.tex("res://assets/ui_hud/icons/icon_lock.png")
		if lock_tex:
			draw_texture_rect(lock_tex, Rect2(lock_banner.position.x + 48.0 * sx, lock_banner.position.y + 10.0 * sy, 40.0 * sx, 40.0 * sy), false)
		draw_string(
			font,
			Vector2(lock_banner.position.x + 36.0 * sx, lock_banner.position.y + 40.0 * sy),
			"CHƯA CÓ",
			HORIZONTAL_ALIGNMENT_CENTER,
			lock_banner.size.x - 36.0 * sx,
			maxi(15, int(25.0 * sx)),
			Color(0.90, 0.92, 0.98)
		)

	if is_selected_highlight:
		var sel_rim := Color(
			lerpf(rarity_col.r, 1.0, 0.25),
			lerpf(rarity_col.g, 1.0, 0.25),
			lerpf(rarity_col.b, 1.0, 0.25),
			0.98
		)
		draw_rect(outer_rect.grow(5.0 * sx), sel_rim, false, maxf(2.5, 4.2 * sx))

	if flip_flash_alpha > 0.01:
		var fl_col: Color = GameState.RARITY_COLOR.get(rarity, Color.WHITE)
		draw_rect(outer_rect, Color(fl_col.r, fl_col.g, fl_col.b, flip_flash_alpha * 0.55), true)
		draw_rect(outer_rect.grow(3.0), Color(1.0, 0.96, 0.78, flip_flash_alpha), false, 4.0)

	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


func _draw_rarity_glow_shadow(outer_rect: Rect2, rarity: String, sx: float) -> void:
	if _sb_glow_outer == null:
		_sb_glow_outer = StyleBoxFlat.new()
		_sb_glow_outer.bg_color = Color(0.06, 0.08, 0.12, 1.0)
		_sb_glow_mid = StyleBoxFlat.new()
		_sb_glow_mid.bg_color = Color(0.06, 0.08, 0.12, 1.0)
		_sb_glow_core = StyleBoxFlat.new()
		_sb_glow_core.bg_color = Color(0.06, 0.08, 0.12, 1.0)

	var pulse := 0.88 + 0.12 * sin(glow_time)
	var boost := 1.15 if show_gacha_glow else 1.0
	var corner_r := maxi(8, int(22.0 * sx))
	_sb_glow_outer.set_corner_radius_all(corner_r)
	_sb_glow_mid.set_corner_radius_all(corner_r)
	_sb_glow_core.set_corner_radius_all(corner_r)

	if rarity == "SSR":
		_sb_glow_outer.shadow_color = Color(1.0, 0.56, 0.06, clampf(0.76 * pulse * boost, 0.0, 1.0))
		_sb_glow_outer.shadow_size = maxi(14, int(38.0 * sx * boost))
		draw_style_box(_sb_glow_outer, outer_rect)

		_sb_glow_mid.shadow_color = Color(1.0, 0.84, 0.20, clampf(0.90 * pulse * boost, 0.0, 1.0))
		_sb_glow_mid.shadow_size = maxi(8, int(20.0 * sx * boost))
		draw_style_box(_sb_glow_mid, outer_rect)

		_sb_glow_core.shadow_color = Color(1.0, 0.96, 0.68, clampf(0.96 * pulse, 0.0, 1.0))
		_sb_glow_core.shadow_size = maxi(4, int(9.0 * sx))
		draw_style_box(_sb_glow_core, outer_rect)
	elif rarity == "S":
		_sb_glow_outer.shadow_color = Color(0.68, 0.16, 0.98, clampf(0.72 * pulse * boost, 0.0, 1.0))
		_sb_glow_outer.shadow_size = maxi(12, int(32.0 * sx * boost))
		draw_style_box(_sb_glow_outer, outer_rect)

		_sb_glow_mid.shadow_color = Color(0.86, 0.42, 1.0, clampf(0.86 * pulse * boost, 0.0, 1.0))
		_sb_glow_mid.shadow_size = maxi(7, int(17.0 * sx * boost))
		draw_style_box(_sb_glow_mid, outer_rect)

		_sb_glow_core.shadow_color = Color(0.96, 0.78, 1.0, clampf(0.92 * pulse, 0.0, 1.0))
		_sb_glow_core.shadow_size = maxi(4, int(8.0 * sx))
		draw_style_box(_sb_glow_core, outer_rect)


func _draw_responsive_text_box(
	font: Font,
	box: Rect2,
	text: String,
	max_fsize: int,
	min_fsize: int,
	col: Color,
	align: HorizontalAlignment = HORIZONTAL_ALIGNMENT_CENTER
) -> void:
	var cache_key := "%d_%d_%d_%d_%s" % [int(box.size.x), int(box.size.y), max_fsize, min_fsize, text]
	var chosen_fsize := min_fsize
	var chosen_lines: PackedStringArray

	if _text_layout_cache.has(cache_key):
		var cached: Dictionary = _text_layout_cache[cache_key]
		chosen_fsize = int(cached["fsize"])
		chosen_lines = cached["lines"]
	else:
		chosen_lines = PackedStringArray()
		for fs in range(max_fsize, min_fsize - 1, -1):
			var wrapped := _wrap_text(font, text, box.size.x, fs)
			var line_h := float(fs) * 1.28
			var total_h := wrapped.size() * line_h
			if total_h <= box.size.y + 2.0 and wrapped.size() <= 4:
				chosen_fsize = fs
				chosen_lines = wrapped
				break

		if chosen_lines.is_empty():
			chosen_fsize = min_fsize
			chosen_lines = _wrap_text(font, text, box.size.x, chosen_fsize)

		var max_fit_lines := maxi(1, int(floor((box.size.y + 5.0) / (float(chosen_fsize) * 1.20))))
		if chosen_lines.size() > max_fit_lines:
			var clamped := PackedStringArray()
			for li in range(max_fit_lines):
				var ln := chosen_lines[li]
				if li == max_fit_lines - 1 and not ln.ends_with("..."):
					ln = ln + "..."
				clamped.append(ln)
			chosen_lines = clamped

		_text_layout_cache[cache_key] = {
			"fsize": chosen_fsize,
			"lines": chosen_lines,
		}

	var line_step := float(chosen_fsize) * 1.20
	var block_h := chosen_lines.size() * line_step
	var start_y := box.position.y + maxf(0.0, (box.size.y - block_h) * 0.5) + float(chosen_fsize) * 0.88
	var out_sz := maxi(2, int(float(chosen_fsize) * 0.18))

	for i in range(chosen_lines.size()):
		var lpos := Vector2(box.position.x, start_y + i * line_step)
		draw_string_outline(
			font,
			lpos,
			chosen_lines[i],
			align,
			box.size.x,
			chosen_fsize,
			out_sz,
			Color(0.01, 0.01, 0.03, 0.96)
		)
		draw_string(
			font,
			lpos,
			chosen_lines[i],
			align,
			box.size.x,
			chosen_fsize,
			col
		)


func _wrap_text(font: Font, text: String, max_w: float, fsize: int) -> PackedStringArray:
	var result := PackedStringArray()
	for paragraph in text.split("\n"):
		var words := paragraph.strip_edges().split(" ", false)
		if words.is_empty():
			continue
		var cur_line := words[0]
		for w_i in range(1, words.size()):
			var candidate := cur_line + " " + words[w_i]
			var cand_w := font.get_string_size(candidate, HORIZONTAL_ALIGNMENT_LEFT, -1, fsize).x
			if cand_w <= max_w:
				cur_line = candidate
			else:
				result.append(cur_line)
				cur_line = words[w_i]
		result.append(cur_line)
	return result
