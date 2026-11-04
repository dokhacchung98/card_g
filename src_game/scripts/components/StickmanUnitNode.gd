extends Node2D

# Renders a battlefield unit:
# - Hero Unit (C001..C080): Compact 17-Bone2D Stickman + Weapon_Front + Weapon_Back (Shield/Dual) + S/SSR Animated Weapon + Shared VFX
# - Summoned Unit (s01_linh_cau, s02_phao_co_ngu, s03_chien_binh_xuong): 4-Frame Animated Sprite
# - Overhead HUD: Redesigned HP & Mana Bar + Shield overlay + Element Icon Badge (replacing plain circle) + 16x16 Status Icons

const HERO_BODY_SCALE := 0.60
static var _shadow_poly: PackedVector2Array

var unit_data: Dictionary = {}
var anim_state: String = "idle"     # idle, walk, attack, cast, hurt, death
var anim_time: float = 0.0
var facing_dir: float = 1.0
var is_summon: bool = false
var summon_frames: Array[Texture2D] = []

# Stickman & Weapon textures
var team_parts: Dictionary = {}
var weapon_main_tex: Texture2D = null
var weapon_off_tex: Texture2D = null
var weapon_anim_texs: Array[Texture2D] = []
var grip1_norm := Vector2(0.28, 0.72)
var grip2_norm := Vector2(0.18, 0.82)
var show_offhand: bool = false
var is_s_or_ssr: bool = false
var vfx_flash_timer: float = 0.0
var active_vfx_key: String = ""
var action_anim_timer: float = 0.0
var action_anim_duration: float = 0.44

const STICKER_PART_LIST := [
	"hip_kilt", "chest", "neck", "head",
	"arm_upper_back", "arm_lower_back", "hand_back",
	"arm_upper_front", "arm_lower_front", "hand_front",
	"leg_thigh_back", "leg_shin_back", "foot_back",
	"leg_thigh_front", "leg_shin_front", "foot_front",
]


func setup_unit(u: Dictionary) -> void:
	unit_data = u
	var t_color: String = str(u.get("team_color", "team_blue"))
	is_summon = bool(u.get("is_summon", false))

	if is_summon:
		var sid: String = str(u.get("summon_id", "s01_linh_cau"))
		summon_frames.clear()
		for i in range(4):
			var stex := GameState.tex("res://assets/summons/%s/parts/anim_%d.png" % [sid, i])
			if stex:
				summon_frames.append(stex)
		queue_redraw()
		return

	# Load 16 Stickman parts for team color
	team_parts.clear()
	for pname in STICKER_PART_LIST:
		var ptex := GameState.tex("res://assets/sticker_hero/godot/parts/%s/%s.png" % [t_color, pname])
		if ptex:
			team_parts[pname] = ptex

	var c_num: int = int(u.get("num", 1))
	var cfg := GameState.get_weapon_config(c_num)
	var wid := "w%03d" % c_num
	var slug: String = str(cfg.get("slug", "%s_weapon" % wid))
	if not slug.begins_with(wid + "_"):
		slug = "%s_%s" % [wid, slug]

	var g1: Array = cfg.get("grip1_norm", [0.28, 0.72])
	var g2: Array = cfg.get("grip2_norm", [0.18, 0.82])
	grip1_norm = Vector2(float(g1[0]), float(g1[1]))
	grip2_norm = Vector2(float(g2[0]), float(g2[1]))

	var wdir := "res://assets/weapons/%s/parts" % slug
	weapon_main_tex = GameState.tex("%s/weapon_main.png" % wdir)
	weapon_off_tex = GameState.tex("%s/weapon_offhand.png" % wdir)

	var rarity: String = str(u.get("rarity", "N"))
	is_s_or_ssr = (rarity == "S" or rarity == "SSR")
	weapon_anim_texs.clear()
	if is_s_or_ssr:
		for i in range(4):
			var atex := GameState.tex("%s/weapon_anim_%d.png" % [wdir, i])
			if atex:
				weapon_anim_texs.append(atex)

	var role_group: String = str(u.get("role_group", "atk_phys"))
	show_offhand = (role_group == "tanker" or c_num == 7 or c_num == 13 or c_num == 19 or cfg.has("prompt_offhand"))
	queue_redraw()


func trigger_combat_vfx(vfx_name: String, duration: float = 0.28) -> void:
	active_vfx_key = vfx_name
	vfx_flash_timer = duration
	action_anim_duration = 0.56 if anim_state == "cast" else 0.44
	action_anim_timer = action_anim_duration
	queue_redraw()


func update_visual(dt: float) -> void:
	anim_time += dt
	if vfx_flash_timer > 0.0:
		vfx_flash_timer = maxf(0.0, vfx_flash_timer - dt)
	if action_anim_timer > 0.0:
		action_anim_timer = maxf(0.0, action_anim_timer - dt)
		if action_anim_timer <= 0.0 and (anim_state == "attack" or anim_state == "cast"):
			anim_state = "idle"
	queue_redraw()


func _draw() -> void:
	if unit_data.is_empty():
		return

	var elem: String = str(unit_data.get("element", "kim"))
	var elem_meta: Dictionary = GameState.ELEMENT_META.get(elem, GameState.ELEMENT_META["kim"])
	var has_synergy: bool = bool(unit_data.get("has_wuxing_synergy", false))

	# 1. Compact Ground Shadow & Elemental Synergy Foot Aura
	if _shadow_poly.is_empty():
		_shadow_poly = _make_ellipse_poly(Vector2(0, 16.0), 14.5, 5.5)
	draw_colored_polygon(
		_shadow_poly,
		Color(0, 0, 0, 0.44)
	)
	if has_synergy:
		var aura_tex := GameState.tex("%s/synergy_aura.png" % str(elem_meta.get("vfx_dir", "res://assets/vfx_elements/kim_metal")))
		if aura_tex:
			draw_set_transform(Vector2(0, 15.0), anim_time * 0.9, Vector2(0.21, 0.11))
			draw_texture(aura_tex, -aura_tex.get_size() * 0.5, Color(1, 1, 1, 0.85))
			draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

	# 2. Compact Body Rendering (Summon vs 17-Bone2D Stickman Hero)
	var bob := sin(anim_time * 3.6) * 1.0
	var walk_swing := sin(anim_time * 5.2) * 0.36 if anim_state == "walk" else sin(anim_time * 2.4) * 0.06
	var atk_swing := 0.0
	if anim_state == "attack" and action_anim_timer > 0.0:
		var prog := 1.0 - (action_anim_timer / maxf(0.01, action_anim_duration))
		atk_swing = sin(prog * PI) * 1.18
	elif anim_state == "cast" and action_anim_timer > 0.0:
		var prog_c := 1.0 - (action_anim_timer / maxf(0.01, action_anim_duration))
		atk_swing = -0.75 * sin(prog_c * PI) + sin(prog_c * PI * 3.0) * 0.22

	var unit_scale := 0.28 * HERO_BODY_SCALE
	var flip_x := -1.0 if facing_dir < 0.0 else 1.0

	if is_summon and not summon_frames.is_empty():
		var f_idx := int(anim_time * 4.2) % summon_frames.size()
		var stex: Texture2D = summon_frames[f_idx]
		draw_set_transform(Vector2(0, -6.0 + bob), 0.0, Vector2(0.22 * flip_x, 0.22))
		draw_texture(stex, -stex.get_size() * 0.5)
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	else:
		_draw_stickman_rig(flip_x, unit_scale, bob, walk_swing, atk_swing)

	# 3. Active Combat VFX Overlay (fx_slash, fx_slash_heavy, fx_spark, fx_dust)
	if vfx_flash_timer > 0.0 and not active_vfx_key.is_empty():
		var vtex := GameState.tex("res://assets/vfx_shared/%s.png" % active_vfx_key)
		if vtex:
			var vpos := Vector2(14.0 * flip_x, -11.0)
			if active_vfx_key == "fx_dust":
				vpos = Vector2(-5.0 * flip_x, 12.0)
			draw_set_transform(vpos, 0.25 * flip_x, Vector2(0.11 * flip_x, 0.11))
			draw_texture(vtex, -vtex.get_size() * 0.5, Color(1, 1, 1, clampf(vfx_flash_timer * 4.0, 0.0, 0.95)))
			draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

	# 4. Redesigned Overhead Combat HUD (HP, Mana, Shield & Element Icon Badge)
	_draw_overhead_hud(elem_meta)


func _draw_stickman_rig(flip_x: float, sc: float, bob: float, walk_swing: float, atk_swing: float) -> void:
	var k := HERO_BODY_SCALE
	var hip_pos := Vector2(0.0, -2.5 * k + bob)

	# Back Leg
	_draw_part("leg_thigh_back", hip_pos + Vector2(-4.0 * flip_x, 2.0) * k, -walk_swing * 0.6 * flip_x, sc, flip_x)
	_draw_part("leg_shin_back", hip_pos + Vector2(-6.0 * flip_x, 14.0) * k, walk_swing * 0.4 * flip_x, sc, flip_x)
	_draw_part("foot_back", hip_pos + Vector2(-5.0 * flip_x, 25.0) * k, 0.0, sc, flip_x)

	# Back Arm & Offhand Shield/Weapon
	var back_arm_rot := (walk_swing * 0.5 - atk_swing * 0.3) * flip_x
	_draw_part("arm_upper_back", hip_pos + Vector2(5.0 * flip_x, -14.0) * k, back_arm_rot, sc, flip_x)
	_draw_part("arm_lower_back", hip_pos + Vector2(9.0 * flip_x, -5.0) * k, back_arm_rot * 1.1, sc, flip_x)
	_draw_part("hand_back", hip_pos + Vector2(12.0 * flip_x, 2.0) * k, back_arm_rot, sc, flip_x)
	if show_offhand and weapon_off_tex:
		draw_set_transform(hip_pos + Vector2(16.0 * flip_x, -2.0) * k, back_arm_rot * 0.6, Vector2(sc * 0.9 * flip_x, sc * 0.9))
		draw_texture(weapon_off_tex, -weapon_off_tex.get_size() * 0.5)
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

	# Torso, Neck & Head
	_draw_part("hip_kilt", hip_pos, 0.0, sc, flip_x)
	_draw_part("chest", hip_pos + Vector2(0.0, -13.0) * k, atk_swing * 0.12 * flip_x, sc, flip_x)
	_draw_part("neck", hip_pos + Vector2(0.0, -24.0) * k, 0.0, sc, flip_x)
	_draw_part("head", hip_pos + Vector2(0.0, -34.0) * k, -atk_swing * 0.08 * flip_x, sc, flip_x)

	# Front Leg
	_draw_part("leg_thigh_front", hip_pos + Vector2(4.0 * flip_x, 2.0) * k, walk_swing * 0.6 * flip_x, sc, flip_x)
	_draw_part("leg_shin_front", hip_pos + Vector2(6.0 * flip_x, 14.0) * k, -walk_swing * 0.35 * flip_x, sc, flip_x)
	_draw_part("foot_front", hip_pos + Vector2(7.0 * flip_x, 25.0) * k, 0.0, sc, flip_x)

	# Front Arm & Main Weapon (at Grip 1)
	var front_arm_rot := (-0.35 + atk_swing - walk_swing * 0.35) * flip_x
	var hand_pos := hip_pos + (Vector2(11.0 * flip_x, -4.0) + Vector2(cos(front_arm_rot), sin(front_arm_rot)) * 6.0) * k
	_draw_part("arm_upper_front", hip_pos + Vector2(-5.0 * flip_x, -14.0) * k, front_arm_rot * 0.6, sc, flip_x)
	_draw_part("arm_lower_front", hip_pos + Vector2(3.0 * flip_x, -8.0) * k, front_arm_rot * 0.85, sc, flip_x)

	var wtex := weapon_main_tex
	if is_s_or_ssr and weapon_anim_texs.size() >= 4:
		var a_idx := int(anim_time * 6.5) % 4
		wtex = weapon_anim_texs[a_idx]
	if wtex:
		var wsz := wtex.get_size()
		var grip_px := Vector2(wsz.x * grip1_norm.x, wsz.y * grip1_norm.y)
		var w_rot := (-0.25 + atk_swing * 1.15) * flip_x
		draw_set_transform(hand_pos, w_rot, Vector2(sc * 0.92 * flip_x, sc * 0.92))
		draw_texture(wtex, -grip_px)
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

	_draw_part("hand_front", hand_pos, front_arm_rot, sc, flip_x)


func _draw_part(part_name: String, pos: Vector2, rot: float, sc: float, flip_x: float) -> void:
	var ptex: Texture2D = team_parts.get(part_name, null)
	if not ptex:
		return
	draw_set_transform(pos, rot, Vector2(sc * flip_x, sc))
	draw_texture(ptex, -ptex.get_size() * 0.5)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


func _draw_overhead_hud(elem_meta: Dictionary) -> void:
	var hp_cur: float = maxf(0.0, float(unit_data.get("hp", 100)))
	var hp_max: float = maxf(1.0, float(unit_data.get("max_hp", 100)))
	var mana_cur: float = clampf(float(unit_data.get("mana", 0)), 0.0, float(unit_data.get("max_mana", 100)))
	var mana_max: float = maxf(1.0, float(unit_data.get("max_mana", 100)))
	var shield_cur: float = maxf(0.0, float(unit_data.get("shield", 0)))

	var bar_w := 44.0
	var bar_x := -bar_w * 0.5 + 5.0
	var bar_y := -38.0

	# 1. Outer Dark-Iron & Gold Beveled Frame Backing
	var frame_rect := Rect2(bar_x - 2.0, bar_y - 2.0, bar_w + 4.0, 13.5)
	draw_rect(frame_rect, Color(0.03, 0.04, 0.07, 0.96), true)

	var frame_tex := GameState.tex("res://assets/ui_hud/hud_bars/unit_bar_empty_frame.png")
	if frame_tex:
		draw_texture_rect(frame_tex, Rect2(bar_x - 14.0, bar_y - 3.0, bar_w + 18.0, 15.5), false, Color(1, 1, 1, 0.92))

	# Recessed dark tracks for HP (top) and Mana (bottom)
	draw_rect(Rect2(bar_x, bar_y, bar_w, 5.5), Color(0.08, 0.10, 0.14, 0.96), true)
	draw_rect(Rect2(bar_x, bar_y + 6.5, bar_w, 3.5), Color(0.05, 0.08, 0.16, 0.96), true)

	# 2. HP Fill Strip (Textured + Vivid Team Color Tinted + Glossy Top Highlight)
	var p_idx: int = int(unit_data.get("owner_idx", 0))
	var hp_tint := Color(0.22, 0.98, 0.48)
	if p_idx == 1:
		hp_tint = Color(1.0, 0.28, 0.30)
	elif p_idx == 2:
		hp_tint = Color(0.32, 0.95, 0.62)
	elif p_idx == 3:
		hp_tint = Color(1.0, 0.78, 0.20)

	var hp_ratio := clampf(hp_cur / hp_max, 0.0, 1.0)
	var hp_fill_w := bar_w * hp_ratio
	if hp_fill_w > 0.5:
		var hp_tex := GameState.tex("res://assets/ui_hud/hud_bars/unit_hp_fill_strip.png")
		if hp_tex:
			draw_texture_rect_region(
				hp_tex,
				Rect2(bar_x, bar_y, hp_fill_w, 5.5),
				Rect2(0, 0, hp_tex.get_width() * hp_ratio, hp_tex.get_height()),
				hp_tint
			)
		else:
			draw_rect(Rect2(bar_x, bar_y, hp_fill_w, 5.5), hp_tint, true)
		draw_rect(Rect2(bar_x, bar_y, hp_fill_w, 1.5), Color(1.0, 1.0, 1.0, 0.38), true)

	# Subtle tick marks every 150 HP so tankiness is visually clear
	var ticks := clampi(int(hp_max / 150.0), 1, 5)
	for t_i in range(1, ticks + 1):
		var tx := bar_x + (float(t_i) * 150.0 / hp_max) * bar_w
		if tx < bar_x + bar_w - 2.0:
			draw_line(Vector2(tx, bar_y), Vector2(tx, bar_y + 5.5), Color(0.02, 0.03, 0.05, 0.70), 1.0)

	# 3. Shield Bar Overlay (Gleaming Diamond-Cyan Strip & Frame when Shield > 0)
	if shield_cur > 0.0:
		var sh_ratio := clampf(shield_cur / hp_max, 0.0, 1.0)
		var sh_w := bar_w * sh_ratio
		var sh_tex := GameState.tex("res://assets/ui_hud/hud_bars/unit_shield_fill_strip.png")
		if sh_tex and sh_w > 0.5:
			draw_texture_rect_region(
				sh_tex,
				Rect2(bar_x, bar_y - 1.5, sh_w, 2.8),
				Rect2(0, 0, sh_tex.get_width() * sh_ratio, sh_tex.get_height())
			)
		else:
			draw_rect(Rect2(bar_x, bar_y - 1.5, sh_w, 2.6), Color(0.78, 0.98, 1.0, 0.96), true)
		draw_rect(frame_rect, Color(0.52, 0.92, 1.0, 0.95), false, 1.4)
	else:
		draw_rect(frame_rect, Color(0.82, 0.66, 0.30, 0.92), false, 1.1)

	# 4. Mana Fill Strip (Sapphire-Blue Arcane Bar on bottom track)
	var mana_ratio := clampf(mana_cur / mana_max, 0.0, 1.0)
	var mana_fill_w := bar_w * mana_ratio
	if mana_fill_w > 0.5:
		var mana_tex := GameState.tex("res://assets/ui_hud/hud_bars/unit_mana_fill_strip.png")
		if mana_tex:
			draw_texture_rect_region(
				mana_tex,
				Rect2(bar_x, bar_y + 6.5, mana_fill_w, 3.5),
				Rect2(0, 0, mana_tex.get_width() * mana_ratio, mana_tex.get_height())
			)
		else:
			draw_rect(Rect2(bar_x, bar_y + 6.5, mana_fill_w, 3.5), Color(0.28, 0.72, 1.0), true)
		draw_rect(Rect2(bar_x, bar_y + 6.5, mana_fill_w, 1.1), Color(0.85, 0.96, 1.0, 0.45), true)

	# 5. Element Icon Medallion on the Left of the HP/Mana Bar (replaces the old circle!)
	var icon_path: String = str(elem_meta.get("icon", "res://assets/cards/icons/elements/kim/prop.png"))
	var elem_icon_tex := GameState.tex(icon_path)
	var icon_center := Vector2(bar_x - 8.5, bar_y + 4.8)
	var icon_size := Vector2(18.0, 18.0)
	var e_col: Color = elem_meta.get("color", Color.GOLD)
	if elem_icon_tex:
		draw_circle(icon_center, 9.5, Color(0.03, 0.04, 0.07, 0.98))
		draw_texture_rect(
			elem_icon_tex,
			Rect2(icon_center - icon_size * 0.5, icon_size),
			false
		)
		draw_arc(icon_center, 9.5, 0.0, TAU, 24, e_col, 1.3)
	else:
		draw_circle(icon_center, 6.0, e_col)

	# 6. 16x16 Status Effect Icons above the HP bar
	var statuses: Array = unit_data.get("status_icons", [])
	var s_count := mini(statuses.size(), 4)
	for i in range(s_count):
		var st_path: String = str(statuses[i])
		var st_tex := GameState.tex(st_path)
		if st_tex:
			var sx := -((s_count * 13.0) * 0.5) + i * 13.0
			draw_texture_rect(st_tex, Rect2(sx, bar_y - 15.0, 12.0, 12.0), false)


func _make_ellipse_poly(center: Vector2, rx: float, ry: float) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for i in range(16):
		var ang := i * TAU / 16.0
		pts.append(center + Vector2(cos(ang) * rx, sin(ang) * ry))
	return pts
