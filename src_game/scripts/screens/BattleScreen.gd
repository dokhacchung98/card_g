extends Control

const CardWidget := preload("res://scripts/components/CardWidget.gd")
const StickmanUnitNode := preload("res://scripts/components/StickmanUnitNode.gd")
const BotAI := preload("res://scripts/ai/BotAI.gd")

enum MatchPhase { PREP, REVEAL, COMBAT, SUDDEN_DEATH, GAME_OVER }

const TEAM_COLORS := ["team_blue", "team_red", "team_green", "team_amber"]
const TEAM_NAMES := ["BẠN (Đội Xanh)", "BOT ĐỎ (Cạnh Trên)", "BOT LÁ (Cạnh Trái)", "BOT VÀNG (Cạnh Phải)"]
const TEAM_UI_COLS := [
	Color(0.28, 0.65, 0.98),
	Color(0.96, 0.35, 0.35),
	Color(0.28, 0.88, 0.48),
	Color(0.98, 0.72, 0.22),
]

var phase: int = MatchPhase.PREP
var phase_timer: float = 15.0
var round_num: int = 1
var player_count: int = 4

var shared_deck: Array = []          # Array of {"card_id": String, "element": String}
var players: Array = []              # Array of player dictionaries
var bot_profiles: Array = []         # Array of BotAI profiles
var units: Array = []                # Active battlefield units (persisted across freeze phases!)
var projectiles: Array = []          # Active projectiles
var vfx_bursts: Array = []           # Active hit impacts / item animations
var floating_texts: Array = []       # Floating combat numbers & skill callouts
var last_opponent_item_id: String = "C082"

var selected_hand_idx: int = -1
var carousel_pos: float = 2.0
var carousel_target_pos: float = 2.0
var hand_cards_widgets: Array = []
var hand_pull_progress: Array[float] = []
var hand_entry_offset_y: Array[float] = []
var _carousel_pressing: bool = false
var _carousel_is_dragging: bool = false
var _carousel_drag_start_x: float = 0.0
var _carousel_drag_start_y: float = 0.0
var _carousel_start_pos: float = 0.0

# UI Nodes
var tex_phase_icon: TextureRect
var lbl_phase_title: Label
var lbl_timer: Label
var lbl_deck_info: Label
var lbl_bot_log: Label

var board_canvas: Control
var units_layer: Node2D
var fx_layer: Node2D

var lbl_synergy_info: Label
var btn_hand_prev: Button
var btn_hand_next: Button
var btn_place_selected: Button
var btn_inspect_selected: Button
var hand_carousel_stage: Control
var draw_anim_layer: Control
var history_modal: ColorRect
var history_title: Label
var history_grid: GridContainer


func _init() -> void:
	size = Vector2(1080, 1920)
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_build_ui()


func _ready() -> void:
	start_new_match(GameState.selected_player_count)


func _build_ui() -> void:
	var bg_tex := TextureRect.new()
	bg_tex.texture = GameState.tex("res://assets/ui_hud/gui/home_sanctuary_bg_1080x1920.png")
	bg_tex.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	bg_tex.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	bg_tex.position = Vector2.ZERO
	bg_tex.size = Vector2(1080, 1920)
	add_child(bg_tex)
	bg_tex.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)

	var bg := ColorRect.new()
	bg.color = Color(0.03, 0.04, 0.08, 0.68)
	bg.position = Vector2.ZERO
	bg.size = Vector2(1080, 1920)
	add_child(bg)
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)

	# 1. Top Match HUD Bar (y=12..182)
	var top_panel := PanelContainer.new()
	top_panel.position = Vector2(20, 12)
	top_panel.size = Vector2(1040, 168)
	top_panel.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("header", 14))
	add_child(top_panel)

	var top_vbox := VBoxContainer.new()
	top_vbox.add_theme_constant_override("separation", 8)
	top_panel.add_child(top_vbox)

	var top_row1 := HBoxContainer.new()
	top_row1.add_theme_constant_override("separation", 14)
	top_vbox.add_child(top_row1)

	var btn_home := Button.new()
	btn_home.text = "SẢNH"
	btn_home.custom_minimum_size = Vector2(150, 62)
	btn_home.add_theme_font_size_override("font_size", 25)
	btn_home.add_theme_color_override("font_color", Color(1.0, 0.92, 0.65))
	GameState.apply_gui_button(btn_home, "back_home", false, 38, 6)
	btn_home.pressed.connect(func(): GameState.emit_signal("screen_requested", "home"))
	top_row1.add_child(btn_home)

	tex_phase_icon = TextureRect.new()
	tex_phase_icon.custom_minimum_size = Vector2(54, 54)
	tex_phase_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tex_phase_icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	top_row1.add_child(tex_phase_icon)

	var phase_vbox := VBoxContainer.new()
	phase_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top_row1.add_child(phase_vbox)

	lbl_phase_title = Label.new()
	lbl_phase_title.add_theme_font_size_override("font_size", 28)
	lbl_phase_title.add_theme_color_override("font_color", Color(0.98, 0.84, 0.28))
	phase_vbox.add_child(lbl_phase_title)

	lbl_deck_info = Label.new()
	lbl_deck_info.add_theme_font_size_override("font_size", 22)
	lbl_deck_info.add_theme_color_override("font_color", Color(0.72, 0.90, 1.0))
	phase_vbox.add_child(lbl_deck_info)

	lbl_timer = Label.new()
	lbl_timer.add_theme_font_size_override("font_size", 42)
	lbl_timer.add_theme_color_override("font_color", Color(0.45, 0.98, 0.62))
	lbl_timer.add_theme_color_override("font_outline_color", Color(0.02, 0.02, 0.04, 0.98))
	lbl_timer.add_theme_constant_override("outline_size", 6)
	top_row1.add_child(lbl_timer)

	var btn_guide := Button.new()
	btn_guide.text = "LUẬT CHƠI"
	btn_guide.icon = GameState.tex("res://assets/ui_hud/icons/icon_guide_book.png")
	btn_guide.expand_icon = true
	btn_guide.custom_minimum_size = Vector2(196, 62)
	btn_guide.add_theme_font_size_override("font_size", 24)
	GameState.apply_gui_button(btn_guide, "purple", false, 12, 6)
	btn_guide.pressed.connect(func():
		GameState.emit_signal("guide_requested", 1)
	)
	top_row1.add_child(btn_guide)

	var top_row2 := HBoxContainer.new()
	top_row2.add_theme_constant_override("separation", 12)
	top_vbox.add_child(top_row2)

	var bot_log_icon := TextureRect.new()
	bot_log_icon.texture = GameState.tex("res://assets/ui_hud/icons/icon_cards_hand.png")
	bot_log_icon.custom_minimum_size = Vector2(30, 30)
	bot_log_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	bot_log_icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	top_row2.add_child(bot_log_icon)

	lbl_bot_log = Label.new()
	lbl_bot_log.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	lbl_bot_log.clip_text = true
	lbl_bot_log.text = "Vuốt ngang xem bài · Chạm vào 1 thẻ để rút lên!"
	lbl_bot_log.add_theme_font_size_override("font_size", 22)
	lbl_bot_log.add_theme_color_override("font_color", Color(0.55, 0.95, 0.72))
	top_row2.add_child(lbl_bot_log)

	# 2. Central 1:1 Square 4-Player Poker Battle Board (1024x1024 at x=28, y=188)
	board_canvas = Control.new()
	board_canvas.position = Vector2(28, 188)
	board_canvas.size = Vector2(1024, 1024)
	board_canvas.mouse_filter = Control.MOUSE_FILTER_STOP
	board_canvas.draw.connect(_draw_board_canvas)
	board_canvas.gui_input.connect(_on_board_gui_input)
	add_child(board_canvas)

	units_layer = Node2D.new()
	board_canvas.add_child(units_layer)

	fx_layer = Node2D.new()
	fx_layer.draw.connect(_draw_fx_layer)
	board_canvas.add_child(fx_layer)

	# 3. Bottom Curved Stack & Carousel Hand Panel (y=1220..1900 — Large 340x510 HD Cards)
	var hand_panel := PanelContainer.new()
	hand_panel.position = Vector2(20, 1220)
	hand_panel.size = Vector2(1040, 680)
	hand_panel.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("section", 14))
	add_child(hand_panel)

	var hand_vbox := VBoxContainer.new()
	hand_vbox.add_theme_constant_override("separation", 6)
	hand_panel.add_child(hand_vbox)

	var hand_top_bar := HBoxContainer.new()
	hand_top_bar.add_theme_constant_override("separation", 10)
	hand_vbox.add_child(hand_top_bar)

	lbl_synergy_info = Label.new()
	lbl_synergy_info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	lbl_synergy_info.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	lbl_synergy_info.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	lbl_synergy_info.clip_text = true
	lbl_synergy_info.add_theme_font_size_override("font_size", 23)
	lbl_synergy_info.add_theme_color_override("font_color", Color(0.98, 0.86, 0.36))
	hand_top_bar.add_child(lbl_synergy_info)

	btn_place_selected = Button.new()
	btn_place_selected.text = "ĐẶT LÊN BÀN"
	btn_place_selected.icon = GameState.tex("res://assets/cards/icons/stats/dame/prop.png")
	btn_place_selected.expand_icon = true
	btn_place_selected.custom_minimum_size = Vector2(236, 60)
	btn_place_selected.add_theme_font_size_override("font_size", 24)
	GameState.apply_gui_button(btn_place_selected, "gold", false, 14, 6)
	btn_place_selected.pressed.connect(func(): _place_currently_selected_card())
	hand_top_bar.add_child(btn_place_selected)

	btn_inspect_selected = Button.new()
	btn_inspect_selected.text = "CHI TIẾT"
	btn_inspect_selected.icon = GameState.tex("res://assets/ui_hud/icons/icon_guide_book.png")
	btn_inspect_selected.expand_icon = true
	btn_inspect_selected.custom_minimum_size = Vector2(174, 60)
	btn_inspect_selected.add_theme_font_size_override("font_size", 23)
	GameState.apply_gui_button(btn_inspect_selected, "purple", false, 12, 6)
	btn_inspect_selected.pressed.connect(func(): _inspect_currently_selected_card())
	hand_top_bar.add_child(btn_inspect_selected)

	btn_hand_next = Button.new()
	btn_hand_next.text = "HẠ XUỐNG"
	btn_hand_next.custom_minimum_size = Vector2(164, 60)
	btn_hand_next.add_theme_font_size_override("font_size", 23)
	GameState.apply_gui_button(btn_hand_next, "slate", false, 12, 6)
	btn_hand_next.pressed.connect(func():
		selected_hand_idx = -1
		_recalculate_team_synergies()
		board_canvas.queue_redraw()
	)
	hand_top_bar.add_child(btn_hand_next)

	hand_carousel_stage = Control.new()
	hand_carousel_stage.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hand_carousel_stage.size_flags_vertical = Control.SIZE_EXPAND_FILL
	hand_carousel_stage.custom_minimum_size = Vector2(1012, 580)
	hand_carousel_stage.clip_contents = false
	hand_carousel_stage.mouse_filter = Control.MOUSE_FILTER_STOP
	hand_carousel_stage.gui_input.connect(_on_hand_carousel_gui_input)
	hand_vbox.add_child(hand_carousel_stage)

	draw_anim_layer = Control.new()
	draw_anim_layer.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	draw_anim_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	draw_anim_layer.z_index = 140
	add_child(draw_anim_layer)

	_build_history_modal()


func _build_history_modal() -> void:
	history_modal = ColorRect.new()
	history_modal.color = Color(0.02, 0.03, 0.06, 0.88)
	history_modal.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	history_modal.visible = false
	add_child(history_modal)

	var p := PanelContainer.new()
	p.position = Vector2(60, 240)
	p.size = Vector2(960, 1380)
	p.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("dialog", 24))
	history_modal.add_child(p)

	var vb := VBoxContainer.new()
	vb.add_theme_constant_override("separation", 16)
	p.add_child(vb)

	var hb := HBoxContainer.new()
	vb.add_child(hb)

	history_title = Label.new()
	history_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	history_title.add_theme_font_size_override("font_size", 30)
	history_title.add_theme_color_override("font_color", Color(0.98, 0.84, 0.28))
	hb.add_child(history_title)

	var b_close := Button.new()
	b_close.text = "ĐÓNG"
	b_close.custom_minimum_size = Vector2(160, 68)
	b_close.add_theme_font_size_override("font_size", 26)
	GameState.apply_gui_button(b_close, "wood", false)
	b_close.pressed.connect(func(): history_modal.visible = false)
	hb.add_child(b_close)

	var sc := ScrollContainer.new()
	sc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	GameState.setup_touch_scroll(sc)
	vb.add_child(sc)

	history_grid = GridContainer.new()
	history_grid.columns = 3
	history_grid.add_theme_constant_override("h_separation", 16)
	history_grid.add_theme_constant_override("v_separation", 16)
	sc.add_child(history_grid)


# ==============================================================================
# MATCH INITIALIZATION & SHARED CHAOS DECK (25 x N Cards)
# ==============================================================================
func start_new_match(p_count: int) -> void:
	player_count = clampi(p_count, 2, 4)
	round_num = 1
	selected_hand_idx = -1
	carousel_pos = 2.0
	carousel_target_pos = 2.0
	GameState.player_is_bot = false

	for ch in units_layer.get_children():
		ch.queue_free()
	if is_instance_valid(draw_anim_layer):
		for ch in draw_anim_layer.get_children():
			ch.queue_free()
	units.clear()
	projectiles.clear()
	vfx_bursts.clear()
	floating_texts.clear()
	players.clear()
	bot_profiles.clear()
	shared_deck.clear()

	# Initialize N Players (Player 0 = Bottom Human Player, Player 1..3 = Bot Opponents)
	for i in range(player_count):
		var slots_arr: Array = []
		for s_i in range(10):
			slots_arr.append({
				"state": "empty",      # empty, facedown, active_hero, trigger_break
				"card_id": "",
				"element": "kim",
				"unit_uid": -1,
				"trigger_timer": 0.0,
			})
		players.append({
			"idx": i,
			"name": TEAM_NAMES[i],
			"team_color": TEAM_COLORS[i],
			"ui_color": TEAM_UI_COLS[i],
			"hp": 100.0,
			"max_hp": 100.0,
			"alive": true,
			"is_bot": (i > 0),
			"hand": [],
			"slots": slots_arr,
			"played_history": [],
			"hit_flash": 0.0,
		})
		bot_profiles.append(BotAI.create_bot_profile(i))

	# Build Shared Chaos Deck: 15 cards from each player + 10*N random balanced system cards = 25*N cards
	if not GameState.is_loadout_valid(GameState.loadout_deck).ok:
		GameState.auto_build_valid_loadout()

	# Player 0's 15 cards (each card has its fixed Wuxing element from the 500-card collection)
	for entry in GameState.loadout_deck:
		var uid := str(entry)
		shared_deck.append({
			"card_id": GameState.get_base_card_id(uid),
			"element": GameState.get_card_element(uid),
		})

	# Bot Players' 15 singleton cards each + 10*N system cards (drawn from 100 base templates x 5 elements)
	var all_base_ids: Array = GameState.base_cards_by_id.keys()
	for _bot_i in range(1, player_count):
		var bot_pool := all_base_ids.duplicate()
		bot_pool.shuffle()
		for k in range(15):
			var bcid: String = str(bot_pool[k])
			shared_deck.append({
				"card_id": bcid,
				"element": GameState.ELEMENTS[randi() % GameState.ELEMENTS.size()],
			})

	# System 10*N balanced cards
	for _sys_i in range(10 * player_count):
		var scid: String = str(all_base_ids[randi() % all_base_ids.size()])
		shared_deck.append({
			"card_id": scid,
			"element": GameState.ELEMENTS[randi() % GameState.ELEMENTS.size()],
		})

	shared_deck.shuffle()

	# Deal initial 5 cards to each player and play +2 new cards animation
	_deal_cards_to_alive_players(5, true)
	_enter_prep_phase()


func _deal_cards_to_alive_players(cards_per_player: int, play_anim: bool = true) -> void:
	var newly_drawn_p0: Array = []
	for _c in range(cards_per_player):
		for i in range(player_count):
			if not bool(players[i]["alive"]) or shared_deck.is_empty():
				continue
			var drawn_card: Dictionary = shared_deck.pop_back()
			players[i]["hand"].append(drawn_card)
			if i == 0:
				newly_drawn_p0.append(drawn_card)

	if not players.is_empty():
		var h_sz: int = players[0]["hand"].size()
		selected_hand_idx = -1
		if h_sz > 0:
			carousel_target_pos = float(h_sz - 1) * 0.5 if round_num == 1 else float(maxi(0, h_sz - 2))
			carousel_pos = carousel_target_pos

	if play_anim and not newly_drawn_p0.is_empty():
		var anim_cards: Array = []
		var start_idx: int = maxi(0, newly_drawn_p0.size() - 2)
		for k in range(start_idx, newly_drawn_p0.size()):
			anim_cards.append(newly_drawn_p0[k])
		_play_draw_new_cards_animation(anim_cards)


# ==============================================================================
# PHASE TRANSITIONS (PREP 15s -> REVEAL -> COMBAT 15s -> FREEZE / DEAL / 60s)
# ==============================================================================
func _enter_prep_phase() -> void:
	phase = MatchPhase.PREP
	phase_timer = 15.0
	selected_hand_idx = -1
	tex_phase_icon.texture = GameState.tex("res://assets/ui_hud/hud_bars/timer_prep_15s_compass.png")

	for i in range(player_count):
		BotAI.reset_round_profile(bot_profiles[i], round_num)
		for s in players[i]["slots"]:
			if s["state"] == "trigger_break":
				s["state"] = "empty"

	lbl_bot_log.text = "Vòng %d — Vuốt ngang xem bài · Chạm 1 thẻ để rút lên!" % round_num
	_rebuild_hand_ui()
	board_canvas.queue_redraw()


func _enter_reveal_phase() -> void:
	phase = MatchPhase.REVEAL
	selected_hand_idx = -1
	if is_instance_valid(btn_place_selected):
		btn_place_selected.disabled = true

	var revealed_count := 0
	var used_items_count := 0

	# PASS 1: Reveal and spawn all Hero cards first so all heroes are present on the battlefield
	for p_i in range(player_count):
		if not bool(players[p_i]["alive"]):
			continue
		var slots: Array = players[p_i]["slots"]
		for s_i in range(slots.size()):
			var slot: Dictionary = slots[s_i]
			if slot["state"] == "facedown":
				var cid: String = str(slot["card_id"])
				var elem: String = str(slot["element"])
				var c := GameState.get_card(cid)
				if not bool(c.get("is_item", false)):
					revealed_count += 1
					players[p_i]["played_history"].append({"card_id": cid, "element": elem, "round": round_num})
					slot["state"] = "active_hero"
					var uid := _spawn_hero_unit(p_i, s_i, cid, elem, false, "")
					slot["unit_uid"] = uid

	# PASS 2: Immediately activate all Item cards and remove them from the board slots right away!
	for p_i in range(player_count):
		if not bool(players[p_i]["alive"]):
			continue
		var slots: Array = players[p_i]["slots"]
		for s_i in range(slots.size()):
			var slot: Dictionary = slots[s_i]
			if slot["state"] == "facedown":
				var cid: String = str(slot["card_id"])
				var elem: String = str(slot["element"])
				var c := GameState.get_card(cid)
				if bool(c.get("is_item", false)):
					revealed_count += 1
					used_items_count += 1
					players[p_i]["played_history"].append({"card_id": cid, "element": elem, "round": round_num})
					_activate_item_card(p_i, s_i, cid, elem)
					_spawn_element_impact_vfx(_get_slot_center_pos(p_i, s_i), elem)
					# Immediately clear the item card from the slot so it disappears right as battle starts
					slot["state"] = "empty"
					slot["card_id"] = ""
					slot["unit_uid"] = -1
					slot["trigger_timer"] = 0.0

	_recalculate_team_synergies()
	if used_items_count > 0:
		lbl_bot_log.text = "LẬT %d THẺ (%d Item dùng luôn & biến mất)! Chiến đấu!" % [revealed_count, used_items_count]
	else:
		lbl_bot_log.text = "LẬT %d THẺ — BẮT ĐẦU 15s CHIẾN ĐẤU!" % revealed_count
	_enter_combat_phase(false)


func _enter_combat_phase(is_sudden_death: bool) -> void:
	if is_sudden_death:
		phase = MatchPhase.SUDDEN_DEATH
		phase_timer = 60.0
		tex_phase_icon.texture = GameState.tex("res://assets/board_map/props/prop_3_sudden_death_brazier.png")
		lbl_bot_log.text = "TỬ CHIẾN 60 GIÂY (Hết bài — Đánh đến cùng)!"
	else:
		phase = MatchPhase.COMBAT
		phase_timer = 15.0
		tex_phase_icon.texture = GameState.tex("res://assets/ui_hud/hud_bars/timer_combat_15s_crossed_swords.png")
	board_canvas.queue_redraw()


func _on_combat_15s_finished() -> void:
	# Freeze all units in place and check deck & hands per GDD Section 5.6
	for u in units:
		if is_instance_valid(u.get("node", null)):
			u["node"].anim_state = "idle"

	round_num += 1
	if not shared_deck.is_empty():
		_deal_cards_to_alive_players(2, true)
		_enter_prep_phase()
		return

	var any_hand_left := false
	for p in players:
		if bool(p["alive"]) and not p["hand"].is_empty():
			any_hand_left = true
			break

	if any_hand_left:
		_enter_prep_phase()
	else:
		_enter_combat_phase(true)


# ==============================================================================
# PLACE & RECALL POKER MECHANICS (FREE PLACE & RECALL TO HAND)
# ==============================================================================
func place_card_from_hand(p_idx: int, hand_idx: int, slot_idx: int) -> bool:
	if phase != MatchPhase.PREP:
		return false
	var p: Dictionary = players[p_idx]
	if not bool(p["alive"]):
		return false
	var hand: Array = p["hand"]
	var slots: Array = p["slots"]
	if hand_idx < 0 or hand_idx >= hand.size() or slot_idx < 0 or slot_idx >= slots.size():
		return false
	if slots[slot_idx]["state"] != "empty":
		return false

	var card_inst: Dictionary = hand[hand_idx]
	var cid := str(card_inst["card_id"])
	var elem := str(card_inst["element"])

	var from_global := Vector2(540.0, 1460.0)
	if p_idx == 0 and hand_idx >= 0 and hand_idx < hand_cards_widgets.size():
		var cw_from: Control = hand_cards_widgets[hand_idx]
		if is_instance_valid(cw_from):
			from_global = cw_from.global_position

	hand.remove_at(hand_idx)
	slots[slot_idx]["state"] = "facedown"
	slots[slot_idx]["card_id"] = cid
	slots[slot_idx]["element"] = elem

	if p_idx == 0:
		# Reset selected_hand_idx to -1 so the next card in hand does NOT automatically pop up!
		selected_hand_idx = -1
		if hand.is_empty():
			carousel_pos = 0.0
			carousel_target_pos = 0.0
		else:
			carousel_target_pos = clampf(carousel_target_pos, 0.0, float(hand.size() - 1))
			carousel_pos = clampf(carousel_pos, 0.0, float(hand.size() - 1))
		_play_card_fly_to_slot_animation(cid, elem, from_global, slot_idx)
		_rebuild_hand_ui()
	board_canvas.queue_redraw()
	return true


func recall_card_from_slot(p_idx: int, slot_idx: int) -> bool:
	if phase != MatchPhase.PREP:
		return false
	var p: Dictionary = players[p_idx]
	if not bool(p["alive"]):
		return false
	var slots: Array = p["slots"]
	if slot_idx < 0 or slot_idx >= slots.size():
		return false
	if slots[slot_idx]["state"] != "facedown":
		return false

	p["hand"].append({
		"card_id": str(slots[slot_idx]["card_id"]),
		"element": str(slots[slot_idx]["element"]),
	})
	slots[slot_idx]["state"] = "empty"
	slots[slot_idx]["card_id"] = ""

	if p_idx == 0:
		selected_hand_idx = -1
		carousel_target_pos = float(maxi(0, p["hand"].size() - 1))
		_rebuild_hand_ui()
	board_canvas.queue_redraw()
	return true


# ==============================================================================
# HERO SPAWNING, WUXING SYNERGY & ITEM ACTIVATION
# ==============================================================================
var _next_unit_uid: int = 1

func _spawn_hero_unit(p_idx: int, slot_idx: int, card_id: String, elem: String, is_summon: bool, summon_id: String) -> int:
	var c := GameState.get_card(card_id)
	var uid := _next_unit_uid
	_next_unit_uid += 1

	var spawn_pos := _get_slot_arena_spawn_pos(p_idx, slot_idx)
	var hp_val := float(c.get("hp", 250)) * (0.52 if is_summon else 1.0)
	var mana_max := float(c.get("mana", 60))
	var sh_val := float(c.get("shield", 0))
	var dame_val := float(c.get("dame", 30)) * (0.55 if is_summon else 1.0)
	var aspd_val := float(c.get("aspd", 1.1))
	var rng_val := (1.2 if is_summon and summon_id != "s02_phao_co_ngu" else float(c.get("range", 1.2)))
	var pdef_val := float(c.get("def", 20))
	var mdef_val := float(c.get("mdef", 20))
	var mspd_val := (0.0 if summon_id == "s02_phao_co_ngu" else float(c.get("mspd", 120)))

	# Apply Elemental Passive Modifier per GDD Section 3.0
	if elem == "hoa":
		dame_val *= 1.12
	elif elem == "tho":
		sh_val += hp_val * 0.10
		pdef_val *= 1.12
		mdef_val *= 1.12

	var u_dict := {
		"uid": uid,
		"owner_idx": p_idx,
		"slot_idx": slot_idx,
		"card_id": card_id,
		"num": int(c.get("num", 1)),
		"name": str(c.get("name", card_id)),
		"rarity": str(c.get("rarity", "N")),
		"role_group": str(c.get("role_group", "atk_phys")),
		"element": elem,
		"team_color": TEAM_COLORS[p_idx],
		"pos": spawn_pos,
		"hp": hp_val,
		"max_hp": hp_val,
		"mana": 0.0,
		"max_mana": mana_max,
		"shield": sh_val,
		"dame": dame_val,
		"aspd": aspd_val,
		"range_px": rng_val * 54.0,
		"is_ranged": rng_val >= 2.5,
		"def": pdef_val,
		"mdef": mdef_val,
		"mspd": mspd_val,
		"atk_cd": randf_range(0.1, 0.4),
		"stun_timer": 0.0,
		"silence_timer": 0.0,
		"taunt_target_uid": -1,
		"taunt_timer": 0.0,
		"invert_heal_timer": 0.0,
		"reflect_ratio": 0.0,
		"reflect_timer": 0.0,
		"undying_timer": 0.0,
		"has_wuxing_synergy": false,
		"synergy_atk_mult": 1.0,
		"is_summon": is_summon,
		"summon_id": summon_id,
		"status_icons": [],
		"node": null,
	}

	var u_node: Node2D = StickmanUnitNode.new()
	u_node.position = spawn_pos
	u_node.setup_unit(u_dict)
	units_layer.add_child(u_node)
	u_dict["node"] = u_node
	units.append(u_dict)
	return uid


func _recalculate_team_synergies() -> void:
	for p_i in range(player_count):
		var elems_set := {}
		for u in units:
			if float(u["hp"]) > 0.0 and int(u["owner_idx"]) == p_i:
				elems_set[str(u["element"])] = true

		var has_all_5 := (elems_set.size() >= 5)
		for u in units:
			if float(u["hp"]) <= 0.0 or int(u["owner_idx"]) != p_i:
				continue
			var my_e: String = str(u["element"])
			var generated_by_ally := false
			for other_e in elems_set.keys():
				if GameState.does_element_generate(str(other_e), my_e):
					generated_by_ally = true
					break
			u["has_wuxing_synergy"] = (generated_by_ally or has_all_5)
			u["synergy_atk_mult"] = (1.25 if has_all_5 else (1.15 if generated_by_ally else 1.0))

	var hand_cnt: int = players[0]["hand"].size() if not players.is_empty() else 0
	var has_sel := (selected_hand_idx >= 0 and selected_hand_idx < hand_cnt)
	if is_instance_valid(btn_place_selected):
		btn_place_selected.disabled = (phase != MatchPhase.PREP or not has_sel)
	if is_instance_valid(btn_inspect_selected):
		btn_inspect_selected.disabled = not has_sel
	if is_instance_valid(btn_hand_next):
		btn_hand_next.disabled = not has_sel

	if not is_instance_valid(lbl_synergy_info):
		return
	if hand_cnt <= 0:
		lbl_synergy_info.text = "Đã hết thẻ trên tay"
	elif has_sel:
		var sel_c: Dictionary = players[0]["hand"][selected_hand_idx]
		var c_data := GameState.get_card(str(sel_c["card_id"]))
		lbl_synergy_info.text = "Đang rút: %s (%d/%d)" % [
			str(c_data.get("name", sel_c["card_id"])),
			selected_hand_idx + 1,
			hand_cnt
		]
	else:
		lbl_synergy_info.text = "Chạm 1 thẻ để rút lên (%d lá)" % hand_cnt


func _activate_item_card(p_idx: int, slot_idx: int, card_id: String, elem: String) -> void:
	var c := GameState.get_card(card_id)
	var c_num: int = int(c.get("num", 81))
	if p_idx > 0 and c_num != 95:
		last_opponent_item_id = card_id

	if c_num == 95:
		# C095 Mirror Item: copies last opponent item!
		c = GameState.get_card(last_opponent_item_id)
		c_num = int(c.get("num", 82))

	var allies: Array = []
	var enemies: Array = []
	for u in units:
		if float(u["hp"]) <= 0.0:
			continue
		if int(u["owner_idx"]) == p_idx:
			allies.append(u)
		else:
			enemies.append(u)

	var start_pos := _get_slot_center_pos(p_idx, slot_idx)
	var target_pos := Vector2(512, 512)
	var st_icon: String = str(c.get("status_icon", "res://assets/items/status_icons/status_haste_frenzy_16x16.png"))

	# Execute Item logic by card number (C081..C100)
	if c_num in [81, 83, 84, 85, 87, 90, 92, 94, 97, 99, 100]:
		if allies.is_empty():
			_add_floating_text(start_pos, "%s (Trống đồng minh!)" % str(c.get("name", "")), Color(0.75, 0.75, 0.78))
			return
		allies.sort_custom(func(a, b): return (a["hp"] / a["max_hp"]) < (b["hp"] / b["max_hp"]))
		var ally: Dictionary = allies[0]
		if c_num in [87, 90, 100]:
			allies.sort_custom(func(a, b): return float(a["dame"]) > float(b["dame"]))
			ally = allies[0]
		target_pos = ally["pos"]
		var boost := 1.25 if GameState.does_element_generate(elem, str(ally["element"])) else 1.0

		if c_num == 81:
			_heal_unit(ally, 160.0 * boost)
		elif c_num == 83:
			ally["mana"] = minf(ally["max_mana"], float(ally["mana"]) + 45.0 * boost)
			ally["aspd"] = float(ally["aspd"]) * 1.15
		elif c_num == 84:
			ally["mspd"] = float(ally["mspd"]) * 1.40
			ally["aspd"] = float(ally["aspd"]) * 1.25
		elif c_num == 85:
			ally["shield"] = float(ally["shield"]) + 150.0 * boost
		elif c_num == 87:
			ally["dame"] = float(ally["dame"]) * (1.0 + 0.25 * boost)
			ally["aspd"] = float(ally["aspd"]) * 1.25
		elif c_num == 90:
			ally["dame"] = float(ally["dame"]) * 1.20
			ally["def"] = float(ally["def"]) + 20.0
		elif c_num == 92:
			ally["def"] = float(ally["def"]) + 50.0 * boost
			ally["mdef"] = float(ally["mdef"]) + 50.0 * boost
			_heal_unit(ally, 120.0 * boost)
		elif c_num == 94:
			for a_i in range(mini(2, allies.size())):
				allies[a_i]["shield"] = float(allies[a_i]["shield"]) + 220.0 * boost
				allies[a_i]["def"] = float(allies[a_i]["def"]) + 35.0
		elif c_num == 97:
			for al in allies:
				al["stun_timer"] = 0.0
				al["silence_timer"] = 0.0
				al["mana"] = minf(al["max_mana"], float(al["mana"]) + 20.0)
				_heal_unit(al, 60.0 * boost)
		elif c_num == 99:
			ally["shield"] = float(ally["shield"]) + 150.0 * boost
			ally["reflect_ratio"] = 0.40
			ally["reflect_timer"] = 6.0
		elif c_num == 100:
			if not enemies.is_empty():
				enemies.sort_custom(func(a, b): return float(a["dame"]) > float(b["dame"]))
				ally["element"] = GameState.get_counter_element_against(str(enemies[0]["element"]))
			ally["dame"] = float(ally["dame"]) * 1.25
			ally["mana"] = minf(ally["max_mana"], float(ally["mana"]) + 35.0)
		_attach_status_icon(ally, st_icon)
		_add_floating_text(target_pos, str(c.get("name", "Item")), Color(0.38, 0.98, 0.58))
	else:
		# Offensive / Debuff Items (C082, C086, C088, C089, C091, C093, C096, C098)
		if enemies.is_empty():
			return
		enemies.sort_custom(func(a, b): return float(a["mana"]) > float(b["mana"]))
		var target_e: Dictionary = enemies[0]
		target_pos = target_e["pos"]
		var mult := 1.25 if GameState.does_element_counter(elem, str(target_e["element"])) else 1.0

		if c_num == 82:
			for en in enemies:
				if en["pos"].distance_to(target_pos) <= 180.0:
					_apply_damage(en, 125.0 * mult, true, elem, null)
					_attach_status_icon(en, st_icon)
		elif c_num == 86:
			_apply_damage(target_e, 95.0 * mult, true, elem, null)
			target_e["stun_timer"] = 1.4
			_attach_status_icon(target_e, st_icon)
		elif c_num == 88:
			_apply_damage(target_e, 110.0 * mult, true, elem, null)
			target_e["def"] = maxf(0.0, float(target_e["def"]) - 30.0)
			target_e["mdef"] = maxf(0.0, float(target_e["mdef"]) - 30.0)
			_attach_status_icon(target_e, st_icon)
		elif c_num == 89:
			target_e["mana"] = maxf(0.0, float(target_e["mana"]) - 40.0)
			target_e["stun_timer"] = 2.0
			_attach_status_icon(target_e, st_icon)
			if not allies.is_empty():
				allies[0]["shield"] = float(allies[0]["shield"]) + 130.0
		elif c_num == 91:
			target_e["mana"] = maxf(0.0, float(target_e["mana"]) - 30.0)
			target_e["silence_timer"] = 3.5
			_apply_damage(target_e, 100.0 * mult, true, elem, null)
			_attach_status_icon(target_e, st_icon)
		elif c_num == 93:
			for en in enemies:
				en["aspd"] = float(en["aspd"]) * 0.65
				en["mspd"] = float(en["mspd"]) * 0.65
				_attach_status_icon(en, st_icon)
			for al in allies:
				al["mana"] = minf(al["max_mana"], float(al["mana"]) + 25.0)
		elif c_num == 96:
			if not allies.is_empty():
				var tmp_m: float = float(target_e["mana"])
				target_e["mana"] = float(allies[0]["mana"])
				allies[0]["mana"] = minf(allies[0]["max_mana"], tmp_m)
		elif c_num == 98:
			enemies.sort_custom(func(a, b): return float(a["shield"]) > float(b["shield"]))
			target_e = enemies[0]
			target_pos = target_e["pos"]
			target_e["shield"] = 0.0
			target_e["stun_timer"] = 1.5
			_attach_status_icon(target_e, st_icon)
		_add_floating_text(target_pos, str(c.get("name", "Item")), Color(0.98, 0.45, 0.35))

	# Spawn 4-frame Item Use Spritesheet animation at target_pos
	var use_frames: Array = c.get("use_frames", [])
	if not use_frames.is_empty():
		vfx_bursts.append({
			"pos": target_pos,
			"frames": use_frames,
			"time": 0.0,
			"duration": 0.45,
			"scale": 0.44,
		})


func _attach_status_icon(u: Dictionary, icon_path: String) -> void:
	if icon_path.is_empty():
		return
	var arr: Array = u.get("status_icons", [])
	if not arr.has(icon_path):
		arr.append(icon_path)
		u["status_icons"] = arr


# ==============================================================================
# REAL-TIME AUTO-BATTLER SIMULATION & BOT AI LOOP
# ==============================================================================
func _process(delta: float) -> void:
	var dt := delta * GameState.match_speed

	# Update hit flash & trigger slot timers
	for p in players:
		if float(p["hit_flash"]) > 0.0:
			p["hit_flash"] = maxf(0.0, float(p["hit_flash"]) - dt)
		for s in p["slots"]:
			if s["state"] == "trigger_break" and float(s["trigger_timer"]) > 0.0:
				s["trigger_timer"] -= dt
				if float(s["trigger_timer"]) <= 0.0:
					s["state"] = "empty"

	if phase == MatchPhase.PREP:
		phase_timer -= dt
		_process_bots_in_prep_phase(dt)
		if phase_timer <= 0.0:
			_enter_reveal_phase()
	elif phase == MatchPhase.COMBAT or phase == MatchPhase.SUDDEN_DEATH:
		phase_timer -= dt
		_process_combat_simulation(dt)
		_check_victory_or_elimination()
		if phase != MatchPhase.GAME_OVER and phase_timer <= 0.0:
			if phase == MatchPhase.COMBAT:
				_on_combat_15s_finished()
			else:
				_resolve_sudden_death_timeout()

	_update_hand_carousel_layout(delta)
	_update_top_hud_labels()
	board_canvas.queue_redraw()
	fx_layer.queue_redraw()


func _process_bots_in_prep_phase(dt: float) -> void:
	for p_i in range(1, player_count):
		var p: Dictionary = players[p_i]
		if not bool(p["alive"]) or not bool(p["is_bot"]):
			continue
		var prof: Dictionary = bot_profiles[p_i]
		prof["next_think_wait"] = float(prof.get("next_think_wait", 0.5)) - dt
		if float(prof["next_think_wait"]) <= 0.0:
			prof["next_think_wait"] = randf_range(0.65, 1.35)
			var decision: Dictionary = BotAI.decide_prep_step(p_i, players, units, phase_timer, round_num, prof)
			var act: String = str(decision.get("action", "none"))
			if act == "place":
				if place_card_from_hand(p_i, int(decision["hand_idx"]), int(decision["slot_idx"])):
					lbl_bot_log.text = "[%s] %s" % [p["name"], str(decision.get("reason", ""))]
			elif act == "recall":
				if recall_card_from_slot(p_i, int(decision["slot_idx"])):
					lbl_bot_log.text = "[%s] %s" % [p["name"], str(decision.get("reason", ""))]


func _process_combat_simulation(dt: float) -> void:
	# 1. Update Units AI, Movement, Attack & Full-Mana Skill Execution
	for u in units:
		if float(u["hp"]) <= 0.0:
			continue
		var u_node: Node2D = u.get("node", null)
		if is_instance_valid(u_node):
			u_node.update_visual(dt)

		# Timers & Synergy Regen (+2% Max HP/s when Wuxing generated)
		if bool(u.get("has_wuxing_synergy", false)):
			u["hp"] = minf(float(u["max_hp"]), float(u["hp"]) + float(u["max_hp"]) * 0.02 * dt)
		if float(u["stun_timer"]) > 0.0:
			u["stun_timer"] = maxf(0.0, float(u["stun_timer"]) - dt)
			continue
		if float(u["silence_timer"]) > 0.0:
			u["silence_timer"] = maxf(0.0, float(u["silence_timer"]) - dt)
		if float(u["taunt_timer"]) > 0.0:
			u["taunt_timer"] = maxf(0.0, float(u["taunt_timer"]) - dt)
		if float(u["invert_heal_timer"]) > 0.0:
			u["invert_heal_timer"] = maxf(0.0, float(u["invert_heal_timer"]) - dt)
		if float(u["reflect_timer"]) > 0.0:
			u["reflect_timer"] = maxf(0.0, float(u["reflect_timer"]) - dt)
			if float(u["reflect_timer"]) <= 0.0:
				u["reflect_ratio"] = 0.0
		if float(u["undying_timer"]) > 0.0:
			u["undying_timer"] = maxf(0.0, float(u["undying_timer"]) - dt)

		# Find nearest enemy unit AND check if any alive enemy player has 0 heroes on the board ("hết tướng ở mặt bàn")
		var target_u := _find_target_for_unit(u)
		var exposed_p_idx := _find_nearest_exposed_enemy_player(int(u["owner_idx"]), u["pos"])
		var attack_corner_directly := false

		if target_u.is_empty() and exposed_p_idx >= 0:
			attack_corner_directly = true
		elif exposed_p_idx >= 0 and float(u["taunt_timer"]) <= 0.0:
			var d_unit: float = u["pos"].distance_to(target_u["pos"])
			var d_corner: float = u["pos"].distance_to(_get_player_corner_attack_stand_pos(exposed_p_idx))
			if d_corner < d_unit * 0.95:
				attack_corner_directly = true

		if not attack_corner_directly and not target_u.is_empty():
			var to_vec: Vector2 = target_u["pos"] - u["pos"]
			var dist := to_vec.length()
			var rng_px: float = float(u["range_px"])
			if is_instance_valid(u_node):
				u_node.facing_dir = -1.0 if to_vec.x < -2.0 else 1.0

			if dist > rng_px:
				var move_step := to_vec.normalized() * float(u["mspd"]) * dt
				u["pos"] += move_step
				u["pos"].x = clampf(u["pos"].x, 196.0, 828.0)
				u["pos"].y = clampf(u["pos"].y, 196.0, 828.0)
				if is_instance_valid(u_node):
					u_node.position = u["pos"]
					u_node.anim_state = "walk"
			else:
				# In attack range -> Attack or Cast Skill if Full Mana!
				u["atk_cd"] = float(u["atk_cd"]) - dt
				if float(u["mana"]) >= float(u["max_mana"]) and float(u["silence_timer"]) <= 0.0:
					_execute_unit_unique_skill(u, target_u)
				elif float(u["atk_cd"]) <= 0.0:
					u["atk_cd"] = 1.0 / maxf(0.35, float(u["aspd"]))
					_perform_basic_attack(u, target_u)
		else:
			# Enemy player has 0 heroes on the board -> March to that player's Corner Info/HP Socket and attack it!
			var target_p_idx := exposed_p_idx if exposed_p_idx >= 0 else _find_nearest_enemy_player(int(u["owner_idx"]), u["pos"])
			if target_p_idx >= 0:
				var stand_pos: Vector2 = _get_player_corner_attack_stand_pos(target_p_idx)
				var corner_center: Vector2 = _get_player_avatar_rect(target_p_idx).get_center()
				var to_stand: Vector2 = stand_pos - Vector2(u["pos"])
				var face_vec: Vector2 = corner_center - Vector2(u["pos"])
				if is_instance_valid(u_node):
					u_node.facing_dir = -1.0 if face_vec.x < -2.0 else 1.0
				var reach_dist := maxf(48.0, float(u["range_px"]) * 0.78) if bool(u["is_ranged"]) else 36.0
				if to_stand.length() > reach_dist:
					u["pos"] += to_stand.normalized() * float(u["mspd"]) * dt
					u["pos"].x = clampf(u["pos"].x, 196.0, 828.0)
					u["pos"].y = clampf(u["pos"].y, 196.0, 828.0)
					if is_instance_valid(u_node):
						u_node.position = u["pos"]
						u_node.anim_state = "walk"
				else:
					u["atk_cd"] = float(u["atk_cd"]) - dt
					if float(u["atk_cd"]) <= 0.0:
						u["atk_cd"] = 1.0 / maxf(0.4, float(u["aspd"]))
						_attack_player_directly(u, target_p_idx)

	# 2. Update Flying Projectiles
	for i in range(projectiles.size() - 1, -1, -1):
		var pr: Dictionary = projectiles[i]
		var t_u: Dictionary = pr.get("target_unit", {})
		var t_p_idx: int = int(pr.get("target_player_idx", -1))
		if not t_u.is_empty() and float(t_u.get("hp", 0.0)) > 0.0:
			pr["target_pos"] = t_u["pos"] + Vector2(0, -16)
		var diff: Vector2 = pr["target_pos"] - pr["pos"]
		var step := float(pr["speed"]) * dt
		pr["anim_t"] = float(pr["anim_t"]) + dt
		if diff.length() <= step:
			if t_p_idx >= 0 and t_p_idx < players.size() and bool(players[t_p_idx]["alive"]):
				_apply_direct_player_hp_damage(t_p_idx, float(pr["damage"]), str(pr["element"]))
			elif not t_u.is_empty() and float(t_u.get("hp", 0.0)) > 0.0:
				_apply_damage(t_u, float(pr["damage"]), bool(pr["is_magic"]), str(pr["element"]), pr.get("attacker", null))
				_spawn_element_impact_vfx(pr["target_pos"], str(pr["element"]))
			projectiles.remove_at(i)
		else:
			pr["pos"] += diff.normalized() * step
			pr["rot"] = diff.angle()

	# 3. Update VFX Bursts & Floating Texts
	for i in range(vfx_bursts.size() - 1, -1, -1):
		vfx_bursts[i]["time"] = float(vfx_bursts[i]["time"]) + dt
		if float(vfx_bursts[i]["time"]) >= float(vfx_bursts[i]["duration"]):
			vfx_bursts.remove_at(i)

	for i in range(floating_texts.size() - 1, -1, -1):
		floating_texts[i]["pos"] += Vector2(0, -34.0 * dt)
		floating_texts[i]["time"] = float(floating_texts[i]["time"]) - dt
		if float(floating_texts[i]["time"]) <= 0.0:
			floating_texts.remove_at(i)


func _find_target_for_unit(u: Dictionary) -> Dictionary:
	var my_owner: int = int(u["owner_idx"])
	if float(u["taunt_timer"]) > 0.0 and int(u["taunt_target_uid"]) > 0:
		for cand in units:
			if int(cand["uid"]) == int(u["taunt_target_uid"]) and float(cand["hp"]) > 0.0:
				return cand

	var best_u := {}
	var best_dist := 999999.0
	for cand in units:
		if float(cand["hp"]) <= 0.0 or int(cand["owner_idx"]) == my_owner:
			continue
		var d: float = u["pos"].distance_to(cand["pos"])
		if d < best_dist:
			best_dist = d
			best_u = cand
	return best_u


func _perform_basic_attack(attacker: Dictionary, target: Dictionary) -> void:
	var u_node: Node2D = attacker.get("node", null)
	var elem: String = str(attacker["element"])
	var rg: String = str(attacker["role_group"])
	var is_magic := (rg == "atk_mag" or rg == "support")
	var raw_dmg := float(attacker["dame"]) * float(attacker.get("synergy_atk_mult", 1.0))

	# Gain Mana on basic attack (+14 Mana; +15% bonus if Water element)
	if float(attacker["silence_timer"]) <= 0.0:
		var mana_gain := 14.0 * (1.15 if elem == "thuy" else 1.0)
		attacker["mana"] = minf(float(attacker["max_mana"]), float(attacker["mana"]) + mana_gain)

	if is_instance_valid(u_node):
		u_node.anim_state = "attack"
		u_node.trigger_combat_vfx("fx_slash" if not bool(attacker["is_ranged"]) else "fx_spark", 0.24)

	if bool(attacker["is_ranged"]):
		var proj_frames: Array = []
		if is_magic:
			var vdir: String = str(GameState.ELEMENT_META[elem]["vfx_dir"])
			for f_i in range(4):
				proj_frames.append("%s/projectile_%d.png" % [vdir, f_i])
		else:
			var p_num: int = int(attacker["num"])
			var phys_f := "proj_arrow.png"
			if p_num in [2, 6]:
				phys_f = "proj_crossbow_bolt.png"
			elif p_num == 8:
				phys_f = "proj_harpoon_javelin.png"
			proj_frames.append("res://assets/vfx_elements/physical_projectiles/" + phys_f)

		projectiles.append({
			"pos": attacker["pos"] + Vector2(0, -18),
			"target_pos": target["pos"] + Vector2(0, -16),
			"target_unit": target,
			"attacker": attacker,
			"damage": raw_dmg,
			"is_magic": is_magic,
			"element": elem,
			"frames": proj_frames,
			"anim_t": 0.0,
			"speed": 420.0,
			"rot": (target["pos"] - attacker["pos"]).angle(),
		})
	else:
		_apply_damage(target, raw_dmg, is_magic, elem, attacker)


func _execute_unit_unique_skill(caster: Dictionary, target: Dictionary) -> void:
	caster["mana"] = 0.0
	var u_node: Node2D = caster.get("node", null)
	if is_instance_valid(u_node):
		u_node.anim_state = "cast"
		u_node.trigger_combat_vfx("fx_slash_heavy", 0.38)

	var c := GameState.get_card(str(caster["card_id"]))
	var skill_name: String = str(c.get("skill_name", "Tuyệt Kỹ"))
	var rg: String = str(caster["role_group"])
	var elem: String = str(caster["element"])
	var c_num: int = int(caster["num"])
	var base_dame := float(caster["dame"]) * float(caster.get("synergy_atk_mult", 1.0))

	_add_floating_text(caster["pos"] + Vector2(0, -45), skill_name + "!", GameState.ELEMENT_META[elem]["color"])

	# Summoner Heroes (C024 Hound, C030 Turret, C034/C036 Skeleton)
	if c_num in [24, 30, 34, 36]:
		var sum_id := "s01_linh_cau"
		if c_num == 30:
			sum_id = "s02_phao_co_ngu"
		elif c_num in [34, 36]:
			sum_id = "s03_chien_binh_xuong"
		_spawn_hero_unit(int(caster["owner_idx"]), int(caster["slot_idx"]), str(caster["card_id"]), elem, true, sum_id)

	if rg == "tanker":
		# Tanker Skill: Self/Team Shield + Area Taunt + Counter
		var sh_gain := float(caster["max_hp"]) * 0.28
		caster["shield"] = float(caster["shield"]) + sh_gain
		if c_num in [42, 48, 56, 58]:
			for en in units:
				if float(en["hp"]) > 0.0 and int(en["owner_idx"]) != int(caster["owner_idx"]):
					if en["pos"].distance_to(caster["pos"]) <= 220.0:
						en["taunt_target_uid"] = int(caster["uid"])
						en["taunt_timer"] = 3.0
		if c_num in [47, 51, 58]:
			caster["reflect_ratio"] = 0.35
			caster["reflect_timer"] = 4.5
		if c_num == 60:
			caster["undying_timer"] = 3.5
		_apply_damage(target, base_dame * 1.45, false, elem, caster)
	elif rg == "support":
		# Support Skill: Heal lowest ally, grant Shield, or boost Mana
		var allies: Array = []
		for al in units:
			if float(al["hp"]) > 0.0 and int(al["owner_idx"]) == int(caster["owner_idx"]):
				allies.append(al)
		allies.sort_custom(func(a, b): return (a["hp"] / a["max_hp"]) < (b["hp"] / b["max_hp"]))
		if not allies.is_empty():
			var low_ally: Dictionary = allies[0]
			var boost := 1.25 if GameState.does_element_generate(elem, str(low_ally["element"])) else 1.0
			if c_num in [66, 68, 73, 78]:
				for al in allies:
					al["shield"] = float(al["shield"]) + 135.0 * boost
			else:
				_heal_unit(low_ally, 155.0 * boost)
				low_ally["mana"] = minf(low_ally["max_mana"], float(low_ally["mana"]) + 25.0)
	else:
		# Physical or Magic Offense Skill
		var is_mag := (rg == "atk_mag")
		if c_num == 18:
			# C018 Execute / Shield-breaker SSR
			if float(target["shield"]) > 0.0:
				target["shield"] = 0.0
				_apply_damage(target, base_dame * 2.5, false, elem, caster)
			elif (float(target["hp"]) / float(target["max_hp"])) <= 0.22:
				_apply_damage(target, float(target["hp"]) + 999.0, false, elem, caster)
			else:
				_apply_damage(target, base_dame * 1.95, false, elem, caster)
		elif c_num == 39:
			target["invert_heal_timer"] = 4.0
			_apply_damage(target, base_dame * 1.65, true, elem, caster)
		elif c_num in [3, 12, 13, 16, 22, 29, 33, 38]:
			# AoE Skill
			for en in units:
				if float(en["hp"]) > 0.0 and int(en["owner_idx"]) != int(caster["owner_idx"]):
					if en["pos"].distance_to(target["pos"]) <= 170.0:
						_apply_damage(en, base_dame * 1.65, is_mag, elem, caster)
			_spawn_element_impact_vfx(target["pos"], elem)
		else:
			_apply_damage(target, base_dame * 1.85, is_mag, elem, caster)
			_spawn_element_impact_vfx(target["pos"], elem)


func _apply_damage(target: Dictionary, raw_dmg: float, is_magic: bool, atk_elem: String, attacker) -> void:
	if float(target["hp"]) <= 0.0:
		return

	var def_stat := float(target["mdef"]) if is_magic else float(target["def"])
	if atk_elem == "kim":
		def_stat *= 0.85

	# GDD Section 3.1 Elemental Counter multiplier (+25% / -15%)
	var elem_mult := 1.0
	var def_elem: String = str(target["element"])
	if GameState.does_element_counter(atk_elem, def_elem):
		elem_mult = 1.25
	elif GameState.does_element_counter(def_elem, atk_elem):
		elem_mult = 0.85

	var final_dmg := raw_dmg * (100.0 / (100.0 + maxf(0.0, def_stat))) * elem_mult

	# Reflect damage if target has Thorns / Mirror Shield
	if float(target.get("reflect_ratio", 0.0)) > 0.0 and typeof(attacker) == TYPE_DICTIONARY and not attacker.is_empty():
		var ref_dmg := final_dmg * float(target["reflect_ratio"])
		attacker["hp"] = maxf(1.0, float(attacker["hp"]) - ref_dmg)

	# Wood Element Lifesteal (+10% HP)
	if typeof(attacker) == TYPE_DICTIONARY and not attacker.is_empty() and str(attacker.get("element", "")) == "moc":
		_heal_unit(attacker, final_dmg * 0.12)

	# Metal Element +35% bonus vs Shield
	var cur_sh := float(target["shield"])
	if cur_sh > 0.0:
		var sh_dmg := final_dmg * (1.35 if atk_elem == "kim" else 1.0)
		if sh_dmg <= cur_sh:
			target["shield"] = cur_sh - sh_dmg
			final_dmg = 0.0
		else:
			var leftover_ratio := (sh_dmg - cur_sh) / maxf(1.0, sh_dmg)
			target["shield"] = 0.0
			final_dmg = final_dmg * leftover_ratio

	if final_dmg > 0.0:
		target["hp"] = float(target["hp"]) - final_dmg
		if float(target.get("undying_timer", 0.0)) > 0.0 and float(target["hp"]) < 1.0:
			target["hp"] = 1.0
		# Target gains Mana when taking damage
		if float(target["silence_timer"]) <= 0.0:
			target["mana"] = minf(float(target["max_mana"]), float(target["mana"]) + 8.0)

	_add_floating_text(target["pos"] + Vector2(randf_range(-12, 12), -28), "-%d" % int(round(maxf(1.0, final_dmg))), Color(1.0, 0.36, 0.32))

	if float(target["hp"]) <= 0.0:
		_on_unit_killed(target)


func _heal_unit(u: Dictionary, amount: float) -> void:
	if float(u["hp"]) <= 0.0:
		return
	if float(u.get("invert_heal_timer", 0.0)) > 0.0:
		# C039 InvertHeal turns healing into damage!
		_apply_damage(u, amount, true, "hoa", null)
		return
	u["hp"] = minf(float(u["max_hp"]), float(u["hp"]) + amount)
	_add_floating_text(u["pos"] + Vector2(0, -32), "+%d HP" % int(round(amount)), Color(0.35, 0.98, 0.55))


func _on_unit_killed(u: Dictionary) -> void:
	u["hp"] = 0.0
	var owner_i: int = int(u["owner_idx"])
	var slot_i: int = int(u["slot_idx"])
	if owner_i >= 0 and owner_i < players.size():
		var slots: Array = players[owner_i]["slots"]
		if slot_i >= 0 and slot_i < slots.size() and int(slots[slot_i]["unit_uid"]) == int(u["uid"]):
			slots[slot_i]["state"] = "empty"
			slots[slot_i]["unit_uid"] = -1

	var u_node: Node2D = u.get("node", null)
	if is_instance_valid(u_node):
		u_node.queue_free()
	_recalculate_team_synergies()


func _player_has_living_units(p_idx: int) -> bool:
	for u in units:
		if int(u["owner_idx"]) == p_idx and float(u["hp"]) > 0.0:
			return true
	return false


func _find_nearest_exposed_enemy_player(my_idx: int, from_pos: Vector2) -> int:
	# Returns the nearest alive enemy player who currently has 0 living heroes on the board ("hết tướng ở mặt bàn")
	var best_p := -1
	var best_d := 999999.0
	for i in range(player_count):
		if i == my_idx or not bool(players[i]["alive"]):
			continue
		if _player_has_living_units(i):
			continue
		var d := from_pos.distance_to(_get_player_corner_attack_stand_pos(i))
		if d < best_d:
			best_d = d
			best_p = i
	return best_p


func _attack_player_directly(u: Dictionary, target_p_idx: int) -> void:
	var p: Dictionary = players[target_p_idx]
	if not bool(p["alive"]):
		return
	var u_node: Node2D = u.get("node", null)
	var elem: String = str(u["element"])
	var rg: String = str(u["role_group"])
	var is_magic := (rg == "atk_mag" or rg == "support")
	var tier_dmg := {"N": 3.0, "R": 4.0, "S": 6.0, "SSR": 8.0}
	var dmg: float = float(tier_dmg.get(str(u["rarity"]), 3.0))
	var corner_pos := _get_player_avatar_rect(target_p_idx).get_center()

	if is_instance_valid(u_node):
		u_node.anim_state = "attack"
		u_node.trigger_combat_vfx("fx_slash" if not bool(u["is_ranged"]) else "fx_spark", 0.24)

	if bool(u["is_ranged"]):
		var proj_frames: Array = []
		if is_magic:
			var vdir: String = str(GameState.ELEMENT_META[elem]["vfx_dir"])
			for f_i in range(4):
				proj_frames.append("%s/projectile_%d.png" % [vdir, f_i])
		else:
			proj_frames.append("res://assets/vfx_elements/physical_projectiles/proj_arrow.png")
		projectiles.append({
			"pos": u["pos"] + Vector2(0, -14),
			"target_pos": corner_pos,
			"target_unit": {},
			"target_player_idx": target_p_idx,
			"attacker": u,
			"damage": dmg,
			"is_magic": is_magic,
			"element": elem,
			"frames": proj_frames,
			"anim_t": 0.0,
			"speed": 460.0,
			"rot": (corner_pos - Vector2(u["pos"])).angle(),
		})
	else:
		_apply_direct_player_hp_damage(target_p_idx, dmg, elem)


func _apply_direct_player_hp_damage(target_p_idx: int, dmg: float, elem: String) -> void:
	if target_p_idx < 0 or target_p_idx >= players.size():
		return
	var p: Dictionary = players[target_p_idx]
	if not bool(p["alive"]):
		return
	p["hp"] = maxf(0.0, float(p["hp"]) - dmg)
	p["hit_flash"] = 0.45
	var corner_pos := _get_player_avatar_rect(target_p_idx).get_center()
	_spawn_element_impact_vfx(corner_pos, elem)
	_add_floating_text(corner_pos + Vector2(0, -16), "-%d HP!" % int(dmg), Color(1.0, 0.22, 0.28))

	if float(p["hp"]) <= 0.0:
		_eliminate_player(target_p_idx)


func _eliminate_player(p_idx: int) -> void:
	var p: Dictionary = players[p_idx]
	if not bool(p["alive"]):
		return
	p["alive"] = false
	p["hp"] = 0.0
	p["hand"].clear()
	for s in p["slots"]:
		s["state"] = "empty"
		s["unit_uid"] = -1

	for u in units:
		if int(u["owner_idx"]) == p_idx and float(u["hp"]) > 0.0:
			u["hp"] = 0.0
			if is_instance_valid(u.get("node", null)):
				u["node"].queue_free()

	lbl_bot_log.text = "%s ĐÃ BỊ LOẠI KHỎI BÀN CHƠI (0 HP)!" % str(p["name"])


func _check_victory_or_elimination() -> void:
	var alive_players: Array = []
	for p in players:
		if bool(p["alive"]):
			alive_players.append(p)
	if alive_players.size() <= 1:
		phase = MatchPhase.GAME_OVER
		var winner_name: String = str(alive_players[0]["name"]) if alive_players.size() == 1 else "HÒA"
		lbl_bot_log.text = "KẾT THÚC TRẬN ĐẤU — NHÀ VÔ ĐỊCH: %s!" % winner_name
		GameState.gold += 250
		GameState.pack_count += 1
		GameState.save_game()


func _resolve_sudden_death_timeout() -> void:
	phase = MatchPhase.GAME_OVER
	var best_hp := -1.0
	var winners: Array = []
	for p in players:
		if not bool(p["alive"]):
			continue
		var h: float = float(p["hp"])
		if h > best_hp:
			best_hp = h
			winners = [str(p["name"])]
		elif is_equal_approx(h, best_hp):
			winners.append(str(p["name"]))
	lbl_bot_log.text = "HẾT 60s TỬ CHIẾN — XẾP HẠNG THEO HP CÒN LẠI (%d HP): %s CHIẾN THẮNG!" % [
		int(best_hp), ", ".join(winners)
	]


# ==============================================================================
# BOARD GEOMETRY (1024x1024 SQUARE 4-PLAYER POKER TABLE) & RENDERING
# ==============================================================================
const TOP_SLOT_XS := [
	Vector2(206, 259), Vector2(267, 321), Vector2(329, 383), Vector2(391, 445), Vector2(453, 506),
	Vector2(515, 568), Vector2(576, 630), Vector2(638, 692), Vector2(700, 754), Vector2(762, 816),
]
const BOT_SLOT_XS := [
	Vector2(205, 258), Vector2(266, 320), Vector2(329, 383), Vector2(391, 444), Vector2(453, 507),
	Vector2(515, 570), Vector2(578, 632), Vector2(640, 694), Vector2(702, 756), Vector2(764, 818),
]
const LEFT_SLOT_YS := [
	Vector2(203, 255), Vector2(264, 318), Vector2(326, 379), Vector2(388, 442), Vector2(450, 504),
	Vector2(513, 566), Vector2(574, 628), Vector2(636, 690), Vector2(698, 753), Vector2(761, 815),
]
const RIGHT_SLOT_YS := [
	Vector2(202, 255), Vector2(264, 318), Vector2(326, 380), Vector2(388, 442), Vector2(450, 504),
	Vector2(513, 567), Vector2(575, 629), Vector2(638, 691), Vector2(700, 754), Vector2(763, 817),
]


func _get_slot_rect(p_idx: int, slot_idx: int) -> Rect2:
	var idx := clampi(slot_idx, 0, 9)
	if p_idx == 0:
		# Bottom Edge 10 carved slots (Player 0)
		var xr: Vector2 = BOT_SLOT_XS[idx]
		return Rect2(xr.x, 877.0, xr.y - xr.x, 79.0)
	elif p_idx == 1:
		# Top Edge 10 carved slots (Player 1)
		var xr: Vector2 = TOP_SLOT_XS[idx]
		return Rect2(xr.x, 68.0, xr.y - xr.x, 79.0)
	elif p_idx == 2:
		# Left Edge 10 carved slots (Player 2)
		var yr: Vector2 = LEFT_SLOT_YS[idx]
		return Rect2(67.0, yr.x, 77.0, yr.y - yr.x)
	else:
		# Right Edge 10 carved slots (Player 3)
		var yr: Vector2 = RIGHT_SLOT_YS[idx]
		return Rect2(880.0, yr.x, 77.0, yr.y - yr.x)


func _get_slot_center_pos(p_idx: int, slot_idx: int) -> Vector2:
	return _get_slot_rect(p_idx, slot_idx).get_center()


func _get_slot_arena_spawn_pos(p_idx: int, slot_idx: int) -> Vector2:
	var sc := _get_slot_center_pos(p_idx, slot_idx)
	if p_idx == 0:
		return Vector2(sc.x, 785.0)
	elif p_idx == 1:
		return Vector2(sc.x, 239.0)
	elif p_idx == 2:
		return Vector2(239.0, sc.y)
	else:
		return Vector2(785.0, sc.y)


func _get_player_corner_attack_stand_pos(p_idx: int) -> Vector2:
	# Arena floor stand position right next to each player's carved Corner HP Socket
	if p_idx == 0:
		# Bottom-Left Corner (P1)
		return Vector2(214.0, 810.0)
	elif p_idx == 1:
		# Top-Right Corner (P2)
		return Vector2(810.0, 214.0)
	elif p_idx == 2:
		# Top-Left Corner (P3)
		return Vector2(214.0, 214.0)
	else:
		# Bottom-Right Corner (P4)
		return Vector2(810.0, 810.0)


func _get_player_edge_target_pos(p_idx: int) -> Vector2:
	return _get_player_avatar_rect(p_idx).get_center()


func _find_nearest_enemy_player(my_idx: int, from_pos: Vector2) -> int:
	var best_p := -1
	var best_d := 999999.0
	for i in range(player_count):
		if i == my_idx or not bool(players[i]["alive"]):
			continue
		var d := from_pos.distance_to(_get_player_corner_attack_stand_pos(i))
		if d < best_d:
			best_d = d
			best_p = i
	return best_p


func _get_player_avatar_rect(p_idx: int) -> Rect2:
	# Exact 4 carved Corner Sockets on poker_battle_table_square_1024x1024.png:
	# Left of each player's 10-card strip from that player's seat perspective
	if p_idx == 0:
		# Bottom-Left Carved Corner (Player 0 - Bottom: Left = Corner Info/HP, Right = 10 Bottom Slots)
		return Rect2(24, 834, 166, 162)
	elif p_idx == 1:
		# Top-Right Carved Corner (Player 1 - Top: Left from P2's seat = Corner Info/HP, Right = 10 Top Slots)
		return Rect2(834, 28, 166, 162)
	elif p_idx == 2:
		# Top-Left Carved Corner (Player 2 - Left: Left from P3's seat = Corner Info/HP, Right = 10 Left Slots)
		return Rect2(24, 28, 166, 162)
	else:
		# Bottom-Right Carved Corner (Player 3 - Right: Left from P4's seat = Corner Info/HP, Right = 10 Right Slots)
		return Rect2(834, 834, 166, 162)


func _get_player_history_btn_rect(p_idx: int) -> Rect2:
	var c_rect := _get_player_avatar_rect(p_idx)
	return Rect2(c_rect.position.x + 8, c_rect.position.y + 118, c_rect.size.x - 16, 36)


func _draw_card_in_carved_slot(p_i: int, s_rect: Rect2, slot: Dictionary, u_col: Color) -> void:
	var st: String = str(slot["state"])
	var inner_rect := s_rect.grow(-3.0)

	# 1. Empty Carved Socket: keep the hollowed-out board socket visible!
	if st == "empty":
		if p_i == 0 and phase == MatchPhase.PREP and selected_hand_idx >= 0:
			board_canvas.draw_rect(inner_rect, Color(0.28, 0.78, 1.0, 0.18), true)
			board_canvas.draw_rect(inner_rect, Color(0.45, 0.90, 1.0, 0.85), false, 1.5)
		else:
			board_canvas.draw_rect(inner_rect, u_col * Color(1, 1, 1, 0.28), false, 1.0)
		return

	# Orientation: Top/Bottom slots are vertical (2:3), Left/Right slots are horizontal (rotated 90 deg)
	var is_side := (p_i == 2 or p_i == 3)
	var rot := 0.0
	if p_i == 2:
		rot = PI * 0.5
	elif p_i == 3:
		rot = -PI * 0.5

	var cw := inner_rect.size.y if is_side else inner_rect.size.x
	var ch := inner_rect.size.x if is_side else inner_rect.size.y
	var center := inner_rect.get_center()
	var local_rect := Rect2(-cw * 0.5, -ch * 0.5, cw, ch)
	# Map the (46, 38, 419, 697) card bounds of the 512x768 frame texture 1:1 onto local_rect
	var full_tex_rect := Rect2(
		-cw * 0.5 - cw * (46.0 / 419.0),
		-ch * 0.5 - ch * (38.0 / 697.0),
		cw * (512.0 / 419.0),
		ch * (768.0 / 697.0)
	)

	board_canvas.draw_set_transform(center, rot, Vector2.ONE)

	# 2. Opponent Face-Down Card -> Fit Card Back directly into the carved socket
	if st == "facedown" and p_i > 0:
		var back_tex := GameState.tex("res://assets/mobile/cards/frames/card_back_slot_256x384.png")
		if back_tex:
			board_canvas.draw_texture_rect(back_tex, full_tex_rect, false)
		else:
			board_canvas.draw_rect(local_rect, Color(0.10, 0.14, 0.24), true)
		board_canvas.draw_rect(local_rect, u_col * Color(1, 1, 1, 0.90), false, 1.5)
		board_canvas.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
		return

	# 3. Player 0 Face-Down Card OR Any Revealed Card (active_hero / trigger_break) -> Render Actual Miniature Card!
	var cid: String = str(slot["card_id"])
	var el: String = str(slot["element"])
	var c := GameState.get_card(cid)
	var rarity: String = str(c.get("rarity", "N"))
	var role_group: String = str(c.get("role_group", "atk_phys"))
	var elem_meta: Dictionary = GameState.ELEMENT_META.get(el, GameState.ELEMENT_META["kim"])
	var e_col: Color = elem_meta["color"]

	# Dark card base
	board_canvas.draw_rect(local_rect, Color(0.06, 0.08, 0.12, 0.98), true)

	# Weapon / Item Illustration inside the card art window (79, 133, 354, 253 in 512x768 space)
	var art_tex := GameState.tex(str(c.get("card_art", "")))
	var art_rect := Rect2(
		-cw * 0.5 + cw * (33.0 / 419.0),
		-ch * 0.5 + ch * (95.0 / 697.0),
		cw * (354.0 / 419.0),
		ch * (253.0 / 697.0)
	)
	if art_tex:
		board_canvas.draw_texture_rect(art_tex, art_rect, false)

	# Rarity Card Frame overlay (N / R / S / SSR) fitted 1:1 to local_rect
	var frame_path := "res://assets/mobile/cards/frames/frame_%s_slot_256x384.png" % rarity
	var frame_tex := GameState.tex(frame_path)
	if frame_tex:
		board_canvas.draw_texture_rect(frame_tex, full_tex_rect, false)

	# Element Icon & Role Icon in the 2 top sockets of the miniature Card
	var e_icon := GameState.tex(str(elem_meta.get("icon", "")))
	if e_icon:
		var e_pos := Vector2(-cw * 0.5 + cw * (44.0 / 419.0), -ch * 0.5 + ch * (101.0 / 697.0))
		board_canvas.draw_texture_rect(e_icon, Rect2(e_pos.x - 5.5, e_pos.y - 5.5, 11.0, 11.0), false)

	var role_meta: Dictionary = GameState.ROLE_META.get(role_group, GameState.ROLE_META["atk_phys"])
	var r_icon := GameState.tex(str(role_meta.get("icon", "")))
	if r_icon:
		var r_pos := Vector2(-cw * 0.5 + cw * (376.0 / 419.0), -ch * 0.5 + ch * (101.0 / 697.0))
		board_canvas.draw_texture_rect(r_icon, Rect2(r_pos.x - 5.5, r_pos.y - 5.5, 11.0, 11.0), false)

	# Lower Plate on Card showing Card ID / Face-down indicator
	var font := GameState.get_font()
	var plate_rect := Rect2(-cw * 0.44, ch * 0.06, cw * 0.88, ch * 0.30)
	board_canvas.draw_rect(plate_rect, Color(0.03, 0.05, 0.09, 0.90), true)
	var label_txt := cid
	var txt_pos := Vector2(plate_rect.position.x, plate_rect.position.y + plate_rect.size.y * 0.76)
	board_canvas.draw_string_outline(
		font,
		txt_pos,
		label_txt,
		HORIZONTAL_ALIGNMENT_CENTER,
		plate_rect.size.x,
		12,
		3,
		Color(0.01, 0.01, 0.03, 0.98)
	)
	board_canvas.draw_string(
		font,
		txt_pos,
		label_txt,
		HORIZONTAL_ALIGNMENT_CENTER,
		plate_rect.size.x,
		12,
		Color(0.98, 0.88, 0.42) if st == "facedown" else e_col
	)

	# Trigger Break Shatter Effect for Item Cards
	if st == "trigger_break":
		var sh_tex := GameState.tex("res://assets/board_map/slots/slot_4_trigger_break.png")
		if sh_tex:
			board_canvas.draw_texture_rect(sh_tex, local_rect, false, Color(1, 1, 1, 0.82))

	# Crisp Team / Element Outer Card Rim inside the carved slot
	var rim_col := Color(0.98, 0.84, 0.28) if st == "facedown" else u_col
	board_canvas.draw_rect(local_rect, rim_col, false, 1.5)

	board_canvas.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


func _draw_board_canvas() -> void:
	var font := GameState.get_font()
	var num_font := GameState.get_num_font()

	# 1. 1:1 Square 4-Player Poker Battle Table Background (1024x1024 with 40 carved card sockets)
	var bg_tex := GameState.tex("res://assets/board_map/poker_battle_table_square_1024x1024.png")
	if bg_tex:
		board_canvas.draw_texture_rect(bg_tex, Rect2(0, 0, 1024, 1024), false)
	else:
		board_canvas.draw_rect(Rect2(0, 0, 1024, 1024), Color(0.09, 0.11, 0.16), true)

	# 2. Central Arena Freeze Overlay when in PREP Phase (Round > 1)
	var arena_rect := Rect2(195, 195, 634, 634)
	if phase == MatchPhase.PREP and round_num > 1:
		board_canvas.draw_rect(arena_rect, Color(0.22, 0.65, 0.98, 0.16), true)
		var freeze_tex := GameState.tex("res://assets/board_map/props/prop_2_freeze_pause_crystal.png")
		if freeze_tex:
			board_canvas.draw_texture_rect(freeze_tex, Rect2(464, 464, 96, 96), false, Color(1, 1, 1, 0.55))

	# 3. Draw all 4 Carved Corners & 40 Carved Card Slots (Active Players vs Gray Empty Seats)
	var hp_strip_tex := GameState.tex("res://assets/ui_hud/hud_bars/unit_hp_fill_strip.png")
	var seat_short_titles := ["BẠN", "BOT ĐỎ", "BOT LÁ", "BOT VÀNG"]

	for seat_i in range(4):
		var av_rect := _get_player_avatar_rect(seat_i)
		var inner_corner := av_rect.grow(-4.0)

		# Case A: Seat has NO player in this match (e.g., 2P or 3P mode) -> Display in Gray ("hiển thị màu xám")
		if seat_i >= player_count:
			for s_i in range(10):
				var empty_s_rect := _get_slot_rect(seat_i, s_i).grow(-3.0)
				board_canvas.draw_rect(empty_s_rect, Color(0.36, 0.38, 0.42, 0.78), true)
				board_canvas.draw_rect(empty_s_rect, Color(0.54, 0.56, 0.62, 0.65), false, 1.0)

			board_canvas.draw_style_box(GameState.make_gui_panel_style("slot_gray", 8), inner_corner)

			var av_dead := GameState.tex("res://assets/ui_hud/avatars/avatar_3_eliminated_0hp.png")
			if av_dead:
				board_canvas.draw_texture_rect(
					av_dead,
					Rect2(inner_corner.position.x + 55, inner_corner.position.y + 18, 48, 48),
					false,
					Color(0.75, 0.77, 0.82, 0.72)
				)
			board_canvas.draw_string_outline(
				font,
				Vector2(inner_corner.position.x + 6, inner_corner.position.y + 98),
				"TRỐNG",
				HORIZONTAL_ALIGNMENT_CENTER,
				inner_corner.size.x - 12,
				20,
				4,
				Color(0.02, 0.02, 0.04, 0.96)
			)
			board_canvas.draw_string(
				font,
				Vector2(inner_corner.position.x + 6, inner_corner.position.y + 98),
				"TRỐNG",
				HORIZONTAL_ALIGNMENT_CENTER,
				inner_corner.size.x - 12,
				20,
				Color(0.86, 0.88, 0.92)
			)
			continue

		# Case B: Active Player Seat (0 .. player_count - 1)
		var p: Dictionary = players[seat_i]
		var slots: Array = p["slots"]
		var is_alive: bool = bool(p["alive"])
		var u_col: Color = p["ui_color"] if is_alive else Color(0.46, 0.48, 0.52)

		for s_i in range(10):
			var s_rect := _get_slot_rect(seat_i, s_i)
			if not is_alive:
				var dead_s := s_rect.grow(-3.0)
				board_canvas.draw_rect(dead_s, Color(0.28, 0.30, 0.34, 0.80), true)
				board_canvas.draw_rect(dead_s, Color(0.48, 0.50, 0.55, 0.65), false, 1.0)
			else:
				_draw_card_in_carved_slot(seat_i, s_rect, slots[s_i], u_col)

		# Inside the Carved Corner Socket: draw hand-crafted 2D stone/bronze slot box
		var slot_mod := Color(1.18, 0.65, 0.65, 1.0) if float(p["hit_flash"]) > 0.0 else Color.WHITE
		board_canvas.draw_style_box(
			GameState.make_gui_panel_style("slot_active" if is_alive else "slot_gray", 8, slot_mod),
			inner_corner
		)

		# Draw directional connector arrow from Corner Socket -> that player's 10 Card Slots
		var arrow_col := u_col * Color(1, 1, 1, 0.85)
		if seat_i == 0:
			board_canvas.draw_line(Vector2(191, 916), Vector2(204, 916), arrow_col, 3.0)
		elif seat_i == 1:
			board_canvas.draw_line(Vector2(833, 108), Vector2(817, 108), arrow_col, 3.0)
		elif seat_i == 2:
			board_canvas.draw_line(Vector2(106, 191), Vector2(106, 202), arrow_col, 3.0)
		else:
			board_canvas.draw_line(Vector2(918, 833), Vector2(918, 818), arrow_col, 3.0)

		var commander_avatars := [
			"res://assets/ui_hud/avatars/commander_p1_blue.png",
			"res://assets/ui_hud/avatars/commander_p2_red.png",
			"res://assets/ui_hud/avatars/commander_p3_green.png",
			"res://assets/ui_hud/avatars/commander_p4_amber.png",
		]
		var av_tex_path: String = commander_avatars[seat_i]
		if not is_alive:
			av_tex_path = "res://assets/ui_hud/avatars/avatar_3_eliminated_0hp.png"
		elif float(p["hit_flash"]) > 0.0:
			av_tex_path = "res://assets/ui_hud/avatars/avatar_2_direct_hit.png"
		var av_tex := GameState.tex(av_tex_path)
		if av_tex:
			board_canvas.draw_texture_rect(av_tex, Rect2(av_rect.position.x + 8, av_rect.position.y + 8, 48, 48), false)

		var name_pos := Vector2(av_rect.position.x + 60, av_rect.position.y + 28)
		board_canvas.draw_string_outline(
			font,
			name_pos,
			seat_short_titles[seat_i],
			HORIZONTAL_ALIGNMENT_LEFT,
			98,
			19,
			4,
			Color(0.02, 0.02, 0.04, 0.98)
		)
		board_canvas.draw_string(
			font,
			name_pos,
			seat_short_titles[seat_i],
			HORIZONTAL_ALIGNMENT_LEFT,
			98,
			19,
			u_col
		)

		# Remaining HP Icon + Text + Crystal HP Bar inside the Corner Socket
		var hp_val: float = float(p["hp"])
		var hp_ratio := clampf(hp_val / maxf(1.0, float(p["max_hp"])), 0.0, 1.0)
		var hp_icon_tex := GameState.tex("res://assets/cards/icons/stats/hp/prop.png")
		if hp_icon_tex:
			board_canvas.draw_texture_rect(hp_icon_tex, Rect2(av_rect.position.x + 60, av_rect.position.y + 33, 20, 20), false)
		var hp_str := "%d HP" % int(ceil(hp_val))
		var hp_pos := Vector2(av_rect.position.x + 84, av_rect.position.y + 51)
		board_canvas.draw_string_outline(
			num_font,
			hp_pos,
			hp_str,
			HORIZONTAL_ALIGNMENT_LEFT,
			76,
			19,
			4,
			Color(0.02, 0.02, 0.04, 0.98)
		)
		board_canvas.draw_string(
			num_font,
			hp_pos,
			hp_str,
			HORIZONTAL_ALIGNMENT_LEFT,
			76,
			19,
			Color(0.98, 0.42, 0.42) if hp_val < 40.0 else Color(0.48, 0.96, 0.58)
		)

		var hp_bar_rect := Rect2(av_rect.position.x + 12, av_rect.position.y + 60, av_rect.size.x - 24, 14)
		board_canvas.draw_rect(hp_bar_rect, Color(0.03, 0.04, 0.07, 0.95), true)
		if hp_ratio > 0.0:
			var fill_w := hp_bar_rect.size.x * hp_ratio
			var bar_col := Color(0.96, 0.30, 0.30) if hp_val < 40.0 else u_col
			if hp_strip_tex:
				board_canvas.draw_texture_rect(hp_strip_tex, Rect2(hp_bar_rect.position.x, hp_bar_rect.position.y, fill_w, hp_bar_rect.size.y), false, bar_col)
			else:
				board_canvas.draw_rect(Rect2(hp_bar_rect.position.x, hp_bar_rect.position.y, fill_w, hp_bar_rect.size.y), bar_col, true)
		board_canvas.draw_rect(hp_bar_rect, u_col * Color(1, 1, 1, 0.75), false, 1.0)

		var unit_cnt := 0
		for u in units:
			if int(u["owner_idx"]) == seat_i and float(u["hp"]) > 0.0:
				unit_cnt += 1

		var status_line := "Tay: %d · Sân: %d" % [p["hand"].size(), unit_cnt]
		var status_col := Color(0.96, 0.96, 1.0)
		var is_exposed := (phase == MatchPhase.COMBAT or phase == MatchPhase.SUDDEN_DEATH) and is_alive and not _player_has_living_units(seat_i)
		if is_exposed:
			status_line = "HẾT TƯỚNG!"
			status_col = Color(1.0, 0.42, 0.36)

		var st_pos := Vector2(av_rect.position.x + 8, av_rect.position.y + 98)
		board_canvas.draw_string_outline(
			font,
			st_pos,
			status_line,
			HORIZONTAL_ALIGNMENT_CENTER,
			av_rect.size.x - 16,
			16,
			4,
			Color(0.02, 0.02, 0.04, 0.98)
		)
		board_canvas.draw_string(
			font,
			st_pos,
			status_line,
			HORIZONTAL_ALIGNMENT_CENTER,
			av_rect.size.x - 16,
			16,
			status_col
		)

		# Draw Played History Scroll Button inside the bottom of the Carved Corner Socket
		var h_rect := _get_player_history_btn_rect(seat_i)
		board_canvas.draw_style_box(GameState.make_gui_button_style("wood", false, Color.WHITE, 4, 2), h_rect)
		var scroll_ic := GameState.tex("res://assets/ui_hud/avatars/icon_played_history_scroll.png")
		if scroll_ic:
			board_canvas.draw_texture_rect(scroll_ic, Rect2(h_rect.position.x + 12, h_rect.position.y + 7, 22, 22), false)
		var h_pos := Vector2(h_rect.position.x + 28, h_rect.position.y + h_rect.size.y * 0.72)
		board_canvas.draw_string_outline(
			font,
			h_pos,
			"Bài mở (%d)" % p["played_history"].size(),
			HORIZONTAL_ALIGNMENT_CENTER,
			h_rect.size.x - 32,
			17,
			3,
			Color(0.02, 0.02, 0.04, 0.98)
		)
		board_canvas.draw_string(
			font,
			h_pos,
			"Bài mở (%d)" % p["played_history"].size(),
			HORIZONTAL_ALIGNMENT_CENTER,
			h_rect.size.x - 32,
			17,
			Color(0.98, 0.90, 0.62)
		)


func _draw_fx_layer() -> void:
	var font := GameState.get_font()

	# 1. Draw Flying Projectiles (Compact scale proportionate to 0.60x heroes)
	for pr in projectiles:
		var frames: Array = pr["frames"]
		if not frames.is_empty():
			var f_idx := int(float(pr["anim_t"]) * 12.0) % frames.size()
			var ptex := GameState.tex(str(frames[f_idx]))
			if ptex:
				var p_sc := 0.11 if bool(pr.get("is_magic", false)) else 0.14
				fx_layer.draw_set_transform(pr["pos"], float(pr["rot"]), Vector2(p_sc, p_sc))
				fx_layer.draw_texture(ptex, -ptex.get_size() * 0.5)
				fx_layer.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

	# 2. Draw Hit Impact & Item Use Bursts
	for b in vfx_bursts:
		var frames: Array = b["frames"]
		if not frames.is_empty():
			var ratio := clampf(float(b["time"]) / maxf(0.01, float(b["duration"])), 0.0, 0.99)
			var f_idx := int(ratio * frames.size())
			var btex := GameState.tex(str(frames[f_idx]))
			if btex:
				var sc: float = float(b.get("scale", 0.18))
				fx_layer.draw_set_transform(b["pos"], 0.0, Vector2(sc, sc))
				fx_layer.draw_texture(btex, -btex.get_size() * 0.5, Color(1, 1, 1, 1.0 - ratio * 0.35))
				fx_layer.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

	# 3. Draw Floating Combat Numbers & Skill Callouts
	for ft in floating_texts:
		var ft_txt := str(ft["text"])
		fx_layer.draw_string_outline(
			font,
			ft["pos"],
			ft_txt,
			HORIZONTAL_ALIGNMENT_CENTER,
			220,
			22,
			5,
			Color(0.02, 0.02, 0.04, 0.98)
		)
		fx_layer.draw_string(
			font,
			ft["pos"],
			ft_txt,
			HORIZONTAL_ALIGNMENT_CENTER,
			220,
			22,
			ft["color"]
		)


func _spawn_element_impact_vfx(pos: Vector2, elem: String) -> void:
	var vdir: String = str(GameState.ELEMENT_META.get(elem, GameState.ELEMENT_META["kim"])["vfx_dir"])
	vfx_bursts.append({
		"pos": pos + Vector2(0, -14),
		"frames": [
			"%s/impact_0.png" % vdir,
			"%s/impact_1.png" % vdir,
			"%s/impact_2.png" % vdir,
		],
		"time": 0.0,
		"duration": 0.28,
		"scale": 0.17,
	})


func _add_floating_text(pos: Vector2, txt: String, col: Color) -> void:
	floating_texts.append({
		"pos": pos + Vector2(-110, 0),
		"text": txt,
		"color": col,
		"time": 0.95,
	})


func _on_board_gui_input(event: InputEvent) -> void:
	var mpos := Vector2.ZERO
	var is_tap := false
	if event is InputEventMouseButton:
		var mb: InputEventMouseButton = event as InputEventMouseButton
		if mb.pressed and mb.button_index == MOUSE_BUTTON_LEFT:
			is_tap = true
			mpos = mb.position
	if not is_tap:
		return

	# 1. Check Played History Buttons (`Bài mở`)
	for p_i in range(player_count):
		if _get_player_history_btn_rect(p_i).has_point(mpos):
			_open_player_history_modal(p_i)
			return

	# 2. Check Player 0's 10 Slots for Manual Place or Recall during 15s Prep Phase
	if phase == MatchPhase.PREP and not players.is_empty():
		var slots: Array = players[0]["slots"]
		for s_i in range(10):
			if _get_slot_rect(0, s_i).has_point(mpos):
				if slots[s_i]["state"] == "facedown":
					recall_card_from_slot(0, s_i)
					lbl_bot_log.text = "Đã nhặt lại bài từ Ô #%d về tay!" % (s_i + 1)
				elif slots[s_i]["state"] == "empty" and selected_hand_idx >= 0:
					place_card_from_hand(0, selected_hand_idx, s_i)
					lbl_bot_log.text = "Đã đặt thẻ xuống Ô #%d!" % (s_i + 1)
				elif slots[s_i]["state"] == "empty":
					lbl_bot_log.text = "Hãy chạm vào 1 thẻ trên tay để rút thẻ lên trước khi đặt!"
				elif slots[s_i]["state"] == "active_hero":
					GameState.emit_signal("card_inspect_requested", str(slots[s_i]["card_id"]), str(slots[s_i]["element"]))
				return

	# 3. Check any Revealed Card in the 40 Carved Slots to Inspect Card Detail
	for p_i in range(player_count):
		var p_slots: Array = players[p_i]["slots"]
		for s_i in range(10):
			if _get_slot_rect(p_i, s_i).has_point(mpos) and str(p_slots[s_i]["state"]) == "active_hero":
				GameState.emit_signal("card_inspect_requested", str(p_slots[s_i]["card_id"]), str(p_slots[s_i]["element"]))
				return


func _open_player_history_modal(p_idx: int) -> void:
	var p: Dictionary = players[p_idx]
	history_title.text = "BÀI ĐÃ MỞ — %s (%d lá)" % [str(p["name"]), p["played_history"].size()]
	for ch in history_grid.get_children():
		ch.queue_free()
	for entry in p["played_history"]:
		var cw: Control = CardWidget.new()
		cw.custom_minimum_size = Vector2(276, 414)
		cw.show_lock_if_unowned = false
		cw.setup(str(entry["card_id"]), str(entry["element"]), false, false)
		cw.card_clicked.connect(func(c_id, el): GameState.emit_signal("card_inspect_requested", c_id, el))
		history_grid.add_child(cw)
	history_modal.visible = true


func _rebuild_hand_ui() -> void:
	hand_cards_widgets.clear()
	hand_pull_progress.clear()
	hand_entry_offset_y.clear()
	if is_instance_valid(hand_carousel_stage):
		for ch in hand_carousel_stage.get_children():
			ch.queue_free()
	if players.is_empty():
		return

	var hand: Array = players[0]["hand"]
	if hand.is_empty():
		selected_hand_idx = -1
		carousel_pos = 0.0
		carousel_target_pos = 0.0
		_recalculate_team_synergies()
		return

	if selected_hand_idx >= hand.size():
		selected_hand_idx = -1
	carousel_target_pos = clampf(carousel_target_pos, 0.0, float(maxi(0, hand.size() - 1)))
	carousel_pos = clampf(carousel_pos, 0.0, float(maxi(0, hand.size() - 1)))

	for h_i in range(hand.size()):
		var c_inst: Dictionary = hand[h_i]
		var cid: String = str(c_inst["card_id"])
		var elem: String = str(c_inst["element"])

		var cw: Control = CardWidget.new()
		cw.custom_minimum_size = Vector2(340, 510)
		cw.size = Vector2(340, 510)
		cw.pivot_offset = Vector2(170, 255)
		cw.use_hd_frame = true
		cw.show_lock_if_unowned = false
		cw.is_selected_highlight = (h_i == selected_hand_idx)
		cw.setup(cid, elem, false, false)
		cw.mouse_filter = Control.MOUSE_FILTER_IGNORE
		hand_carousel_stage.add_child(cw)
		hand_cards_widgets.append(cw)
		hand_pull_progress.append(1.0 if h_i == selected_hand_idx else 0.0)
		hand_entry_offset_y.append(0.0)

	_update_hand_carousel_layout(1.0)
	_recalculate_team_synergies()


func _update_hand_carousel_layout(delta: float) -> void:
	if hand_cards_widgets.is_empty() or not is_instance_valid(hand_carousel_stage):
		return
	var cnt: int = hand_cards_widgets.size()
	if selected_hand_idx >= cnt:
		selected_hand_idx = -1

	carousel_target_pos = clampf(carousel_target_pos, 0.0, float(maxi(0, cnt - 1)))
	if not _carousel_is_dragging:
		carousel_pos = lerpf(carousel_pos, carousel_target_pos, clampf(delta * 10.5, 0.0, 1.0))

	var stage_w: float = maxf(1008.0, hand_carousel_stage.size.x)
	var center_x: float = stage_w * 0.5
	var card_w: float = 340.0

	var sel_pull: float = 0.0
	if selected_hand_idx >= 0 and selected_hand_idx < hand_pull_progress.size():
		sel_pull = hand_pull_progress[selected_hand_idx]

	for i in range(cnt):
		var cw: Control = hand_cards_widgets[i]
		if not is_instance_valid(cw):
			continue
		var is_sel: bool = (i == selected_hand_idx)
		var target_pull: float = 1.0 if is_sel else 0.0
		if i < hand_pull_progress.size():
			hand_pull_progress[i] = move_toward(hand_pull_progress[i], target_pull, delta * 6.8)
		var p: float = hand_pull_progress[i] if i < hand_pull_progress.size() else target_pull
		# Smooth ease-out curve for the card pull-out effect ("hiệu ứng rút thẻ ra")
		var pull_ease: float = 1.0 - pow(1.0 - p, 3.0)
		var pull_hop: float = sin(p * PI) * 20.0

		if i < hand_entry_offset_y.size() and hand_entry_offset_y[i] > 0.0:
			hand_entry_offset_y[i] = move_toward(hand_entry_offset_y[i], 0.0, delta * 460.0)
		var entry_y: float = hand_entry_offset_y[i] if i < hand_entry_offset_y.size() else 0.0

		var rel: float = float(i) - carousel_pos
		var abs_rel: float = absf(rel)

		# Neighbors gently part ways when a card is pulled up
		var neighbor_push: float = 0.0
		if selected_hand_idx >= 0 and i != selected_hand_idx:
			var diff_sel := float(i - selected_hand_idx)
			neighbor_push = signf(diff_sel) * (36.0 / maxf(1.0, absf(diff_sel))) * sel_pull

		# Curved fan & overlapping stack ("dạng stack và carousel, danh sách thẻ sẽ dạng cong cong")
		var spread_x: float = rel * 144.0 - signf(rel) * pow(abs_rel, 1.28) * 14.0 + neighbor_push
		var base_arc_y: float = 4.0 + minf((rel * rel) * 6.5 + abs_rel * 4.0, 36.0)
		var pulled_y: float = -18.0
		var final_y: float = lerpf(base_arc_y, pulled_y, pull_ease) - pull_hop + entry_y

		var base_rot: float = clampf(rel * 6.2, -18.0, 18.0)
		var rot_deg: float = lerpf(base_rot, 0.0, pull_ease)

		var base_sc: float = clampf(0.95 - abs_rel * 0.04, 0.82, 0.95)
		var sc: float = lerpf(base_sc, 1.04, pull_ease)

		cw.position = Vector2(center_x + spread_x - card_w * 0.5, final_y)
		cw.rotation_degrees = rot_deg
		cw.scale = Vector2(sc, sc)
		cw.z_index = (95 if p > 0.25 else (60 - int(round(abs_rel * 10.0))))
		if cw.is_selected_highlight != is_sel:
			cw.is_selected_highlight = is_sel
			cw.queue_redraw()
		cw.modulate = Color(1.0, 1.0, 1.0, 1.0) if p > 0.2 else Color(0.90, 0.92, 0.97, 0.98)


func _shift_hand_selection(dir: int) -> void:
	if players.is_empty():
		return
	var hand: Array = players[0]["hand"]
	if hand.is_empty():
		return
	carousel_target_pos = clampf(carousel_target_pos + float(dir), 0.0, float(hand.size() - 1))
	_update_hand_carousel_layout(0.25)
	_recalculate_team_synergies()
	board_canvas.queue_redraw()


func _place_currently_selected_card() -> void:
	if players.is_empty() or phase != MatchPhase.PREP:
		return
	var hand: Array = players[0]["hand"]
	if hand.is_empty() or selected_hand_idx < 0 or selected_hand_idx >= hand.size():
		lbl_bot_log.text = "Hãy chạm vào 1 thẻ trên tay để rút thẻ lên trước!"
		return
	var idx: int = selected_hand_idx
	var c_inst: Dictionary = hand[idx]
	var cid: String = str(c_inst["card_id"])
	var best_slot: int = BotAI.choose_best_slot(c_inst, players[0]["slots"])
	if best_slot >= 0:
		place_card_from_hand(0, idx, best_slot)
		lbl_bot_log.text = "Đã rút & đặt [%s] xuống Ô #%d!" % [cid, best_slot + 1]
	else:
		lbl_bot_log.text = "Cả 10 ô trên bàn đã đầy! Chạm vào 1 ô đang úp để nhặt bài về."


func _inspect_currently_selected_card() -> void:
	if players.is_empty():
		return
	var hand: Array = players[0]["hand"]
	if hand.is_empty():
		return
	var idx: int = selected_hand_idx if (selected_hand_idx >= 0 and selected_hand_idx < hand.size()) else clampi(int(round(carousel_pos)), 0, hand.size() - 1)
	var c_inst: Dictionary = hand[idx]
	GameState.emit_signal("card_inspect_requested", str(c_inst["card_id"]), str(c_inst["element"]))


func _on_hand_carousel_gui_input(event: InputEvent) -> void:
	if players.is_empty():
		return
	var hand: Array = players[0]["hand"]
	if hand.is_empty():
		return

	if event is InputEventMouseButton:
		var mb: InputEventMouseButton = event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_LEFT:
			if mb.pressed:
				_carousel_pressing = true
				_carousel_is_dragging = false
				_carousel_drag_start_x = mb.position.x
				_carousel_drag_start_y = mb.position.y
				_carousel_start_pos = carousel_pos
			elif _carousel_pressing:
				var was_drag_m: bool = _carousel_is_dragging
				_carousel_pressing = false
				_carousel_is_dragging = false
				if not was_drag_m:
					_handle_hand_carousel_tap(mb.position)
		elif mb.button_index == MOUSE_BUTTON_RIGHT and mb.pressed:
			_inspect_currently_selected_card()
		elif mb.button_index == MOUSE_BUTTON_WHEEL_UP and mb.pressed:
			_shift_hand_selection(-1)
		elif mb.button_index == MOUSE_BUTTON_WHEEL_DOWN and mb.pressed:
			_shift_hand_selection(1)
	elif event is InputEventMouseMotion and _carousel_pressing:
		var mm: InputEventMouseMotion = event as InputEventMouseMotion
		var dx_m: float = mm.position.x - _carousel_drag_start_x
		if absf(dx_m) > 12.0:
			_carousel_is_dragging = true
			carousel_pos = clampf(_carousel_start_pos - dx_m / 144.0, 0.0, float(maxi(0, hand.size() - 1)))
			carousel_target_pos = carousel_pos
			_update_hand_carousel_layout(1.0)
			board_canvas.queue_redraw()


func _hit_test_hand_card(local_pos: Vector2) -> Dictionary:
	var best_idx: int = -1
	var best_z: int = -99999
	var best_card_local := Vector2.ZERO
	for i in range(hand_cards_widgets.size()):
		var cw: Control = hand_cards_widgets[i]
		if not is_instance_valid(cw):
			continue
		var inv_xform: Transform2D = cw.get_transform().affine_inverse()
		var pt: Vector2 = inv_xform * local_pos
		if Rect2(Vector2.ZERO, cw.size).has_point(pt):
			if cw.z_index >= best_z:
				best_z = cw.z_index
				best_idx = i
				best_card_local = pt
	return {"idx": best_idx, "card_local": best_card_local}


func _trigger_card_pull_up_effect(cw: Control) -> void:
	if not is_instance_valid(cw):
		return
	cw.modulate = Color(1.28, 1.22, 1.06, 1.0)
	var tw := create_tween()
	tw.tween_property(cw, "modulate", Color(1.0, 1.0, 1.0, 1.0), 0.24).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)


func _handle_hand_carousel_tap(local_pos: Vector2) -> void:
	if players.is_empty():
		return
	var hand: Array = players[0]["hand"]
	if hand.is_empty():
		return

	var hit: Dictionary = _hit_test_hand_card(local_pos)
	var tapped_idx: int = int(hit.get("idx", -1))
	var card_local: Vector2 = hit.get("card_local", Vector2.ZERO)

	# 1. Tapped outside any card -> lower currently raised card back into the fan
	if tapped_idx < 0:
		if selected_hand_idx >= 0:
			selected_hand_idx = -1
			_recalculate_team_synergies()
			board_canvas.queue_redraw()
		return

	# 2. Tapped a card that is NOT currently raised -> pull ONLY that card up out of the fan!
	if tapped_idx != selected_hand_idx:
		selected_hand_idx = tapped_idx
		carousel_target_pos = clampf(float(tapped_idx), 0.0, float(maxi(0, hand.size() - 1)))
		if tapped_idx < hand_cards_widgets.size():
			_trigger_card_pull_up_effect(hand_cards_widgets[tapped_idx])
		var c_inst: Dictionary = hand[tapped_idx]
		var c_data := GameState.get_card(str(c_inst["card_id"]))
		lbl_bot_log.text = "Đã rút [%s] lên! Chạm ô trên bàn hoặc bấm ĐẶT LÊN BÀN để úp." % str(c_data.get("name", c_inst["card_id"]))
		_recalculate_team_synergies()
		board_canvas.queue_redraw()
		return

	# 3. Tapped the ALREADY raised card -> if fully pulled up and tapped on upper body in PREP, place it; otherwise lower it
	var cur_pull: float = hand_pull_progress[tapped_idx] if tapped_idx < hand_pull_progress.size() else 1.0
	if phase == MatchPhase.PREP and cur_pull >= 0.75 and card_local.y <= 320.0:
		_place_currently_selected_card()
	else:
		selected_hand_idx = -1
		lbl_bot_log.text = "Đã hạ thẻ xuống tay."
		_recalculate_team_synergies()
		board_canvas.queue_redraw()


func _play_card_fly_to_slot_animation(card_id: String, elem: String, from_global_pos: Vector2, slot_idx: int) -> void:
	if not is_instance_valid(draw_anim_layer) or not is_instance_valid(board_canvas):
		return
	var ghost: Control = CardWidget.new()
	ghost.custom_minimum_size = Vector2(340, 510)
	ghost.size = Vector2(340, 510)
	ghost.pivot_offset = Vector2(170, 255)
	ghost.use_hd_frame = true
	ghost.show_lock_if_unowned = false
	ghost.setup(card_id, elem, false, false)
	ghost.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ghost.position = from_global_pos
	ghost.scale = Vector2(1.08, 1.08)
	draw_anim_layer.add_child(ghost)

	var slot_rect := _get_slot_rect(0, slot_idx)
	var slot_global_center := board_canvas.global_position + slot_rect.get_center()
	var pull_peak_pos := from_global_pos + Vector2(0.0, -90.0)
	var target_pos := slot_global_center - Vector2(170.0, 255.0)

	var tw := create_tween()
	# Step 1: Pull upward out of the hand ("hiệu ứng rút thẻ ra")
	tw.tween_property(ghost, "position", pull_peak_pos, 0.14).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.parallel().tween_property(ghost, "scale", Vector2(1.16, 1.16), 0.14)
	# Step 2: Fly and shrink into the carved board slot
	tw.tween_property(ghost, "position", target_pos, 0.24).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN)
	tw.parallel().tween_property(ghost, "scale", Vector2(0.18, 0.18), 0.24)
	tw.parallel().tween_property(ghost, "modulate:a", 0.15, 0.24)
	tw.tween_callback(func():
		if is_instance_valid(ghost):
			ghost.queue_free()
		_spawn_element_impact_vfx(_get_slot_center_pos(0, slot_idx), elem)
	)


func _play_draw_new_cards_animation(new_cards: Array) -> void:
	if not is_instance_valid(draw_anim_layer) or new_cards.is_empty():
		return
	for ch in draw_anim_layer.get_children():
		ch.queue_free()

	# Mark the newly added cards in hand so they slide smoothly into the curved fan
	var cnt: int = new_cards.size()
	var total_hand := hand_entry_offset_y.size()
	for k in range(maxi(0, total_hand - cnt), total_hand):
		hand_entry_offset_y[k] = 220.0

	var banner := PanelContainer.new()
	banner.mouse_filter = Control.MOUSE_FILTER_IGNORE
	banner.position = Vector2(140, 490)
	banner.size = Vector2(800, 82)
	banner.add_theme_stylebox_override("panel", GameState.make_gui_panel_style("header", 14))
	draw_anim_layer.add_child(banner)

	var lbl := Label.new()
	lbl.mouse_filter = Control.MOUSE_FILTER_IGNORE
	lbl.text = "VÒNG %d — RÚT +%d THẺ MỚI TỪ CỌC BÀI!" % [round_num, cnt]
	lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lbl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	lbl.add_theme_font_size_override("font_size", 28)
	lbl.add_theme_color_override("font_color", Color(1.0, 0.88, 0.34))
	lbl.add_theme_color_override("font_outline_color", Color(0.02, 0.02, 0.05, 0.98))
	lbl.add_theme_constant_override("outline_size", 5)
	banner.add_child(lbl)

	# Visual Deck Stack at center from which cards are pulled out
	var deck_stack := TextureRect.new()
	deck_stack.mouse_filter = Control.MOUSE_FILTER_IGNORE
	deck_stack.texture = GameState.tex("res://assets/mobile/cards/frames/card_back_slot_256x384.png")
	deck_stack.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	deck_stack.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	deck_stack.size = Vector2(180, 270)
	deck_stack.position = Vector2(450, 610)
	draw_anim_layer.add_child(deck_stack)

	for i in range(cnt):
		var c_inst: Dictionary = new_cards[i]
		var cw: Control = CardWidget.new()
		cw.custom_minimum_size = Vector2(300, 450)
		cw.size = Vector2(300, 450)
		cw.pivot_offset = Vector2(150, 225)
		cw.use_hd_frame = true
		cw.show_lock_if_unowned = false
		cw.setup(str(c_inst["card_id"]), str(c_inst["element"]), true, false)
		cw.mouse_filter = Control.MOUSE_FILTER_IGNORE

		var offset_x: float = (float(i) - float(cnt - 1) * 0.5) * 320.0
		var deck_origin := Vector2(390.0, 560.0)
		var pull_up_pos := Vector2(390.0 + offset_x * 0.25, 470.0)
		var showcase_pos := Vector2(540.0 + offset_x - 150.0, 620.0)
		var target_pos := Vector2(540.0 + offset_x * 0.55 - 150.0, 1340.0)

		cw.position = deck_origin
		cw.scale = Vector2(0.56, 0.56)
		cw.rotation_degrees = (float(i) - float(cnt - 1) * 0.5) * 8.0
		draw_anim_layer.add_child(cw)
		cw.play_flip_reveal_anim(0.16 + float(i) * 0.08)

		var tw := create_tween()
		# 1. Slide/pull card upward out of the deck stack ("rút thẻ ra")
		tw.tween_property(cw, "position", pull_up_pos, 0.18).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
		tw.parallel().tween_property(cw, "scale", Vector2(0.78, 0.78), 0.18)
		# 2. Fan out to center showcase while flipping face-up
		tw.tween_property(cw, "position", showcase_pos, 0.24).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
		tw.parallel().tween_property(cw, "scale", Vector2(1.0, 1.0), 0.24).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
		tw.tween_interval(0.38)
		# 3. Fly down into the curved hand fan
		tw.tween_property(cw, "position", target_pos, 0.34).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN)
		tw.parallel().tween_property(cw, "scale", Vector2(1.06, 1.06), 0.34)
		tw.parallel().tween_property(cw, "modulate:a", 0.0, 0.34)
		tw.tween_callback(cw.queue_free)

	var d_tw := create_tween()
	d_tw.tween_interval(0.65)
	d_tw.tween_property(deck_stack, "modulate:a", 0.0, 0.25)
	d_tw.tween_callback(deck_stack.queue_free)

	var b_tw := create_tween()
	b_tw.tween_interval(0.90)
	b_tw.tween_property(banner, "modulate:a", 0.0, 0.28)
	b_tw.tween_callback(banner.queue_free)


func _update_top_hud_labels() -> void:
	var new_title := ""
	if phase == MatchPhase.PREP:
		new_title = "VÒNG %d · CHUẨN BỊ" % round_num
	elif phase == MatchPhase.COMBAT:
		new_title = "VÒNG %d · CHIẾN ĐẤU" % round_num
	elif phase == MatchPhase.SUDDEN_DEATH:
		new_title = "TỬ CHIẾN 60s"
	elif phase == MatchPhase.GAME_OVER:
		new_title = "KẾT THÚC TRẬN"
	if lbl_phase_title.text != new_title:
		lbl_phase_title.text = new_title

	var new_timer := "%02.1fs" % maxf(0.0, phase_timer)
	if lbl_timer.text != new_timer:
		lbl_timer.text = new_timer

	var living_units := 0
	for u in units:
		if float(u["hp"]) > 0.0:
			living_units += 1
	var new_info := "Cọc bài: %d lá · Tướng: %d" % [
		shared_deck.size(),
		living_units
	]
	if lbl_deck_info.text != new_info:
		lbl_deck_info.text = new_info
