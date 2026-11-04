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
var item_cast_beams: Array = []      # Active item cast beams & flying item orbs (slot -> target)
var shatter_popups: Array = []       # Enlarged pop-up 4-shard card shatter overlays on fx_layer
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
	item_cast_beams.clear()
	shatter_popups.clear()
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
				"energy_cost": 0,
			})
		players.append({
			"idx": i,
			"name": TEAM_NAMES[i],
			"team_color": TEAM_COLORS[i],
			"ui_color": TEAM_UI_COLS[i],
			"hp": 100.0,
			"max_hp": 100.0,
			"energy": GameState.ROUND_ENERGY_GAIN,
			"max_energy": GameState.MAX_ROUND_ENERGY,
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
		var max_e: int = int(players[i].get("max_energy", GameState.MAX_ROUND_ENERGY))
		if round_num <= 1:
			players[i]["energy"] = GameState.ROUND_ENERGY_GAIN
		else:
			players[i]["energy"] = mini(max_e, int(players[i].get("energy", 0)) + GameState.ROUND_ENERGY_GAIN)
		for s in players[i]["slots"]:
			if s["state"] == "trigger_break":
				s["state"] = "empty"

	var p0_e: int = int(players[0].get("energy", 4)) if not players.is_empty() else 4
	var p0_max_e: int = int(players[0].get("max_energy", 6)) if not players.is_empty() else 6
	lbl_bot_log.text = "Vòng %d · Linh Lực: %d/%d — Ghép Ô Liền Kề Tương Sinh & Tiền Tuyến (Ô 4-7) / Cánh!" % [round_num, p0_e, p0_max_e]
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

	# PASS 2: Immediately activate all Item cards and trigger Card Shatter Destruction on the board slots!
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
					_trigger_slot_card_destroy(p_i, s_i, "DÙNG & PHÁ HỦY!")

	_recalculate_team_synergies()
	if used_items_count > 0:
		lbl_bot_log.text = "LẬT %d THẺ (%d Item dùng ngay & phá hủy thẻ)! Chiến đấu!" % [revealed_count, used_items_count]
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
# PLACE & RECALL POKER MECHANICS (COMMAND ENERGY COST & ADJACENCY REFUND)
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
	var cost: int = GameState.get_card_energy_cost(cid)
	var cur_energy: int = int(p.get("energy", 0))
	var max_energy: int = int(p.get("max_energy", GameState.MAX_ROUND_ENERGY))
	if cur_energy < cost:
		if p_idx == 0:
			var c_data := GameState.get_card(cid)
			lbl_bot_log.text = "Không đủ Linh Lực! [%s] cần %dLL (Đang có: %d/%dLL). Chạm ô đang úp để nhặt lại bài!" % [
				str(c_data.get("name", cid)),
				cost,
				cur_energy,
				max_energy
			]
		return false

	var from_global := Vector2(540.0, 1460.0)
	if p_idx == 0 and hand_idx >= 0 and hand_idx < hand_cards_widgets.size():
		var cw_from: Control = hand_cards_widgets[hand_idx]
		if is_instance_valid(cw_from):
			from_global = cw_from.global_position

	p["energy"] = cur_energy - cost
	hand.remove_at(hand_idx)
	slots[slot_idx]["state"] = "facedown"
	slots[slot_idx]["card_id"] = cid
	slots[slot_idx]["element"] = elem
	slots[slot_idx]["energy_cost"] = cost

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
		var adj_info := _evaluate_slot_adjacency(0, slot_idx, elem, true)
		var zone_tag := "Tiền Tuyến (+25% HP/Khiên)" if _is_vanguard_slot(slot_idx) else "Hậu Phương (+20% Tầm/Tốc đánh)"
		var link_tag := ""
		if int(adj_info["gen_links"]) > 0:
			link_tag = " · LIÊN KẾT TƯƠNG SINH (+30% Công, +25% Thủ)!"
		elif int(adj_info["clash_links"]) > 0:
			link_tag = " · CẢNH BÁO XUNG KHẮC LIỀN KỀ (-20% Công/Tốc)!"
		lbl_bot_log.text = "Đặt [%s] (-%dLL, còn %d/%dLL) vào Ô #%d [%s]%s" % [
			cid,
			cost,
			int(p["energy"]),
			max_energy,
			slot_idx + 1,
			zone_tag,
			link_tag
		]
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

	var cid := str(slots[slot_idx]["card_id"])
	var refund: int = int(slots[slot_idx].get("energy_cost", GameState.get_card_energy_cost(cid)))
	var max_energy: int = int(p.get("max_energy", GameState.MAX_ROUND_ENERGY))
	p["energy"] = mini(max_energy, int(p.get("energy", 0)) + refund)

	p["hand"].append({
		"card_id": cid,
		"element": str(slots[slot_idx]["element"]),
	})
	slots[slot_idx]["state"] = "empty"
	slots[slot_idx]["card_id"] = ""
	slots[slot_idx]["energy_cost"] = 0

	if p_idx == 0:
		selected_hand_idx = -1
		carousel_target_pos = float(maxi(0, p["hand"].size() - 1))
		_rebuild_hand_ui()
		lbl_bot_log.text = "Đã nhặt lại [%s] từ Ô #%d (Hoàn +%dLL -> %d/%dLL)!" % [
			cid,
			slot_idx + 1,
			refund,
			int(p["energy"]),
			max_energy
		]
	board_canvas.queue_redraw()
	return true


# ==============================================================================
# HERO SPAWNING, POSITIONAL ROLES, ADJACENCY WUXING SYNERGY & ITEM ACTIVATION
# ==============================================================================
const COMBAT_MSPD_SCALE := 0.44
const COMBAT_ASPD_SCALE := 0.48
const MAX_SUMMONS_PER_PLAYER := 2
const SUMMONER_HERO_NUMS := [19, 24, 30, 34, 35, 36, 79]
const SUMMONER_SKILL_CD := 14.0
const DEFAULT_SKILL_CD := 5.0
var _next_unit_uid: int = 1


func _is_vanguard_slot(slot_idx: int) -> bool:
	# Center 4 slots (Ô #4, #5, #6, #7 -> indices 3..6) are Tiền Tuyến (Vanguard);
	# Outer 6 slots (Ô #1..#3 & Ô #8..#10 -> indices 0..2, 7..9) are Hậu Phương / Cánh (Flank).
	return slot_idx >= 3 and slot_idx <= 6


func _get_slot_link_relation(elem_a: String, elem_b: String) -> int:
	if elem_a.is_empty() or elem_b.is_empty():
		return 0
	if GameState.does_element_generate(elem_a, elem_b) or GameState.does_element_generate(elem_b, elem_a):
		return 1
	if GameState.does_element_counter(elem_a, elem_b) or GameState.does_element_counter(elem_b, elem_a):
		return -1
	return 0


func _evaluate_slot_adjacency(p_idx: int, slot_idx: int, elem: String, include_facedown: bool = true) -> Dictionary:
	var gen_links := 0
	var clash_links := 0
	if p_idx < 0 or p_idx >= players.size() or elem.is_empty():
		return {"gen_links": 0, "clash_links": 0}
	var slots: Array = players[p_idx]["slots"]
	for nb_idx in [slot_idx - 1, slot_idx + 1]:
		if nb_idx < 0 or nb_idx >= slots.size():
			continue
		var nb: Dictionary = slots[nb_idx]
		var st: String = str(nb.get("state", "empty"))
		var valid_nb := (st == "active_hero") or (include_facedown and st == "facedown")
		if not valid_nb:
			continue
		var nb_elem: String = str(nb.get("element", ""))
		var rel := _get_slot_link_relation(elem, nb_elem)
		if rel == 1:
			gen_links += 1
		elif rel == -1:
			clash_links += 1
	return {"gen_links": gen_links, "clash_links": clash_links}


func _spawn_hero_unit(p_idx: int, slot_idx: int, card_id: String, elem: String, is_summon: bool, summon_id: String, summoner_uid: int = -1, custom_spawn_pos: Vector2 = Vector2(-1, -1)) -> int:
	var c := GameState.get_card(card_id)
	var uid := _next_unit_uid
	_next_unit_uid += 1

	var spawn_pos := _get_slot_arena_spawn_pos(p_idx, slot_idx)
	if custom_spawn_pos.x >= 0.0 and custom_spawn_pos.y >= 0.0:
		spawn_pos = custom_spawn_pos
	elif is_summon:
		spawn_pos += Vector2(randf_range(-26.0, 26.0), randf_range(-22.0, 22.0))
	spawn_pos.x = clampf(spawn_pos.x, 196.0, 828.0)
	spawn_pos.y = clampf(spawn_pos.y, 196.0, 828.0)

	var raw_num: int = 0 if is_summon else int(c.get("num", 1))
	var is_summoner_hero: bool = (not is_summon) and (raw_num in SUMMONER_HERO_NUMS)
	var hp_val := float(c.get("hp", 250)) * (0.42 if is_summon else 1.0)
	var mana_max := 0.0 if is_summon else (maxf(150.0, float(c.get("mana", 160))) if is_summoner_hero else maxf(55.0, float(c.get("mana", 65))))
	var sh_val := 0.0 if is_summon else float(c.get("shield", 0))
	var dame_val := float(c.get("dame", 30)) * (0.42 if is_summon else 1.0)
	var aspd_val := float(c.get("aspd", 1.1)) * COMBAT_ASPD_SCALE * (0.85 if is_summon else 1.0)
	var rng_val := (1.2 if is_summon and summon_id != "s02_phao_co_ngu" else float(c.get("range", 1.2)))
	var pdef_val := float(c.get("def", 20))
	var mdef_val := float(c.get("mdef", 20))
	var mspd_val := (0.0 if summon_id == "s02_phao_co_ngu" else float(c.get("mspd", 120)) * COMBAT_MSPD_SCALE)

	# Positional Slot Role Bonus (Ô 4..7 Tiền Tuyến vs Ô 1..3 & 8..10 Hậu Phương)
	var is_vanguard := _is_vanguard_slot(slot_idx)
	if not is_summon and slot_idx >= 0:
		if is_vanguard:
			# Tiền Tuyến (4 Ô Giữa): +25% Máu tối đa & +25% Khiên khởi đầu (+10% HP chắn đòn)
			hp_val *= 1.25
			sh_val = sh_val * 1.25 + hp_val * 0.10
		else:
			# Hậu Phương / Cánh (6 Ô Hai Bên): +20% Tầm đánh & +20% Tốc đánh
			rng_val *= 1.20
			aspd_val *= 1.20

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
		"is_vanguard_slot": is_vanguard,
		"card_id": card_id,
		"num": raw_num,
		"is_summoner_hero": is_summoner_hero,
		"name": ("Linh Thú" if is_summon else str(c.get("name", card_id))),
		"rarity": ("N" if is_summon else str(c.get("rarity", "N"))),
		"role_group": ("atk_phys" if is_summon else str(c.get("role_group", "atk_phys"))),
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
		"atk_cd": randf_range(0.45, 0.95),
		"skill_cd": (6.5 if is_summoner_hero else 2.2),
		"summon_ttl": (10.0 if is_summon else 0.0),
		"summoner_uid": summoner_uid,
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
		"synergy_def_mult": 1.0,
		"synergy_aspd_mult": 1.0,
		"synergy_regen_pct": 0.0,
		"adj_gen_links": 0,
		"adj_clash_links": 0,
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

			var atk_mult := (1.20 if has_all_5 else (1.10 if generated_by_ally else 1.0))
			var def_mult := 1.0
			var aspd_mult := 1.0
			var regen_pct := (0.015 if (generated_by_ally or has_all_5) else 0.0)
			var g_links := 0
			var c_links := 0

			if not bool(u.get("is_summon", false)) and int(u["slot_idx"]) >= 0:
				var adj := _evaluate_slot_adjacency(p_i, int(u["slot_idx"]), my_e, false)
				g_links = int(adj["gen_links"])
				c_links = int(adj["clash_links"])
				if g_links > 0:
					# Liên Kết Ô Liền Kề Tương Sinh: +30% Công (+40% nếu nối 2 bên), +25% Giáp/Kháng Phép, +3% HP/s
					atk_mult += 0.30 + (0.10 if g_links >= 2 else 0.0)
					def_mult += 0.25
					regen_pct += 0.03
				if c_links > 0:
					# Xung Khắc Nội Bộ Liền Kề: -20% Công & -20% Tốc đánh
					atk_mult = maxf(0.55, atk_mult - 0.20 * float(c_links))
					aspd_mult = maxf(0.60, aspd_mult - 0.20 * float(c_links))

			u["has_wuxing_synergy"] = (generated_by_ally or has_all_5 or g_links > 0)
			u["synergy_atk_mult"] = atk_mult
			u["synergy_def_mult"] = def_mult
			u["synergy_aspd_mult"] = aspd_mult
			u["synergy_regen_pct"] = regen_pct
			u["adj_gen_links"] = g_links
			u["adj_clash_links"] = c_links

	var hand_cnt: int = players[0]["hand"].size() if not players.is_empty() else 0
	var p0_energy: int = int(players[0].get("energy", 0)) if not players.is_empty() else 0
	var p0_max_energy: int = int(players[0].get("max_energy", 6)) if not players.is_empty() else 6
	var has_sel := (selected_hand_idx >= 0 and selected_hand_idx < hand_cnt)
	var sel_cost := 1
	if has_sel:
		var sel_c_inst: Dictionary = players[0]["hand"][selected_hand_idx]
		sel_cost = GameState.get_card_energy_cost(str(sel_c_inst["card_id"]))

	if is_instance_valid(btn_place_selected):
		btn_place_selected.text = ("ĐẶT (%dLL)" % sel_cost) if has_sel else "ĐẶT LÊN BÀN"
		btn_place_selected.disabled = (phase != MatchPhase.PREP or not has_sel or p0_energy < sel_cost)
	if is_instance_valid(btn_inspect_selected):
		btn_inspect_selected.disabled = not has_sel
	if is_instance_valid(btn_hand_next):
		btn_hand_next.disabled = not has_sel

	if not is_instance_valid(lbl_synergy_info):
		return
	if hand_cnt <= 0:
		lbl_synergy_info.text = "Hết thẻ trên tay · Linh Lực: %d/%dLL" % [p0_energy, p0_max_energy]
	elif has_sel:
		var sel_c: Dictionary = players[0]["hand"][selected_hand_idx]
		var c_data := GameState.get_card(str(sel_c["card_id"]))
		var rg: String = str(c_data.get("role_group", "atk_phys"))
		var rec_zone := "Ô Giữa 4-7" if (rg == "tanker" or (rg == "atk_phys" and float(c_data.get("range", 1.2)) < 2.2)) else "Ô Cánh 1-3,8-10"
		if bool(c_data.get("is_item", false)):
			rec_zone = "Đặt vào Ô cần chi viện"
		lbl_synergy_info.text = "%s (%dLL · Đang có %d/%dLL · Gợi ý: %s)" % [
			str(c_data.get("name", sel_c["card_id"])),
			sel_cost,
			p0_energy,
			p0_max_energy,
			rec_zone
		]
	else:
		lbl_synergy_info.text = "Linh Lực: %d/%dLL · Chạm 1 thẻ để rút lên (%d lá)" % [p0_energy, p0_max_energy, hand_cnt]


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
		if float(u["hp"]) <= 0.0 or bool(u.get("is_summon", false)):
			continue
		if int(u["owner_idx"]) == p_idx:
			allies.append(u)
		else:
			enemies.append(u)

	var start_pos := _get_slot_center_pos(p_idx, slot_idx)
	var lane_focus_pos := _get_slot_arena_spawn_pos(p_idx, slot_idx)
	var target_pos := lane_focus_pos
	var st_icon: String = str(c.get("status_icon", "res://assets/items/status_icons/status_haste_frenzy_16x16.png"))

	# Execute Item logic by card number (C081..C100) — prioritizes targets near the placed slot's tactical lane!
	if c_num in [81, 83, 84, 85, 87, 90, 92, 94, 97, 99, 100]:
		if not allies.is_empty():
			allies.sort_custom(func(a, b):
				var score_a: float = (1.0 - float(a["hp"]) / maxf(1.0, float(a["max_hp"]))) * 100.0 - Vector2(a["pos"]).distance_to(lane_focus_pos) * 0.18
				var score_b: float = (1.0 - float(b["hp"]) / maxf(1.0, float(b["max_hp"]))) * 100.0 - Vector2(b["pos"]).distance_to(lane_focus_pos) * 0.18
				return score_a > score_b
			)
			var ally: Dictionary = allies[0]
			if c_num in [87, 90, 100]:
				allies.sort_custom(func(a, b):
					var score_a: float = float(a["dame"]) * 1.5 - Vector2(a["pos"]).distance_to(lane_focus_pos) * 0.22
					var score_b: float = float(b["dame"]) * 1.5 - Vector2(b["pos"]).distance_to(lane_focus_pos) * 0.22
					return score_a > score_b
				)
				ally = allies[0]
			target_pos = ally["pos"]
			var boost := 1.35 if GameState.does_element_generate(elem, str(ally["element"])) else 1.0

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
			target_pos = lane_focus_pos
			_add_floating_text(start_pos, "%s (Kích hoạt!)" % str(c.get("name", "Item")), Color(0.38, 0.98, 0.58))
	else:
		# Offensive / Debuff Items (C082, C086, C088, C089, C091, C093, C096, C098) — prioritizes enemies near this slot's lane!
		if not enemies.is_empty():
			enemies.sort_custom(func(a, b):
				var score_a: float = float(a["mana"]) * 1.2 + float(a["dame"]) - Vector2(a["pos"]).distance_to(lane_focus_pos) * 0.25
				var score_b: float = float(b["mana"]) * 1.2 + float(b["dame"]) - Vector2(b["pos"]).distance_to(lane_focus_pos) * 0.25
				return score_a > score_b
			)
			var target_e: Dictionary = enemies[0]
			target_pos = target_e["pos"]
			var mult := 1.50 if GameState.does_element_counter(elem, str(target_e["element"])) else 1.0

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
		else:
			target_pos = _get_slot_arena_spawn_pos(p_idx, slot_idx)
			_add_floating_text(start_pos, "%s (Kích hoạt!)" % str(c.get("name", "Item")), Color(0.98, 0.45, 0.35))

	# Spawn 4-frame Item Use Spritesheet animation at BOTH start_pos (slot) and target_pos (hero/arena),
	# plus a glowing Item Cast Beam & traveling orb from slot -> target_pos!
	var use_frames: Array = c.get("use_frames", [])
	var is_support_item := (c_num in [81, 83, 84, 85, 87, 90, 92, 94, 95, 97, 99, 100])
	if not use_frames.is_empty():
		vfx_bursts.append({
			"pos": start_pos,
			"frames": use_frames,
			"time": 0.0,
			"duration": 0.65,
			"scale": 0.48,
		})
		vfx_bursts.append({
			"pos": target_pos,
			"frames": use_frames,
			"time": 0.0,
			"duration": 0.92,
			"scale": 0.68,
		})
	item_cast_beams.append({
		"from": start_pos,
		"to": target_pos,
		"elem": elem,
		"is_support": is_support_item,
		"frames": use_frames,
		"name": str(c.get("name", "Item")),
		"time": 0.0,
		"duration": 0.88,
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

	# Update hit flash & trigger slot timers (card shatter destruction animation -> empty slot)
	for p in players:
		if float(p["hit_flash"]) > 0.0:
			p["hit_flash"] = maxf(0.0, float(p["hit_flash"]) - dt)
		for s in p["slots"]:
			if s["state"] == "trigger_break" and float(s["trigger_timer"]) > 0.0:
				s["trigger_timer"] -= dt
				if float(s["trigger_timer"]) <= 0.0:
					s["state"] = "empty"
					s["card_id"] = ""
					s["unit_uid"] = -1
					s["trigger_timer"] = 0.0

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
	# 1. Update Units AI, Movement, Attack & Full-Mana Skill Execution (iterate over snapshot so spawning never mutates active loop)
	var active_units := units.duplicate()
	for u in active_units:
		if float(u["hp"]) <= 0.0:
			continue
		var u_node: Node2D = u.get("node", null)
		if is_instance_valid(u_node):
			u_node.update_visual(dt)

		# Expire summoned units after their duration so summons never accumulate infinitely
		if bool(u.get("is_summon", false)):
			u["summon_ttl"] = float(u.get("summon_ttl", 14.0)) - dt
			if float(u["summon_ttl"]) <= 0.0:
				_on_unit_killed(u)
				continue

		# Timers & Synergy Regen (+1.5%..4.5% Max HP/s when Wuxing generated or adjacent Tương Sinh linked)
		var regen_pct := float(u.get("synergy_regen_pct", 0.02 if bool(u.get("has_wuxing_synergy", false)) else 0.0))
		if regen_pct > 0.0:
			u["hp"] = minf(float(u["max_hp"]), float(u["hp"]) + float(u["max_hp"]) * regen_pct * dt)
		if float(u.get("skill_cd", 0.0)) > 0.0:
			u["skill_cd"] = maxf(0.0, float(u["skill_cd"]) - dt)
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
				# In attack range -> Attack or Cast Skill if Full Mana (only real heroes can cast skills!)
				u["atk_cd"] = float(u["atk_cd"]) - dt
				var can_cast := (
					not bool(u.get("is_summon", false))
					and float(u["max_mana"]) > 0.0
					and float(u["mana"]) >= float(u["max_mana"])
					and float(u["silence_timer"]) <= 0.0
					and float(u.get("skill_cd", 0.0)) <= 0.0
				)
				var eff_aspd := maxf(0.22, float(u["aspd"]) * float(u.get("synergy_aspd_mult", 1.0)))
				if can_cast:
					u["atk_cd"] = 1.0 / eff_aspd
					u["skill_cd"] = SUMMONER_SKILL_CD if bool(u.get("is_summoner_hero", false)) else DEFAULT_SKILL_CD
					_execute_unit_unique_skill(u, target_u)
				elif float(u["atk_cd"]) <= 0.0:
					u["atk_cd"] = 1.0 / eff_aspd
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
						u["atk_cd"] = 1.0 / maxf(0.22, float(u["aspd"]))
						_attack_player_directly(u, target_p_idx)

	# Prune dead units so the array never grows unbounded
	for i in range(units.size() - 1, -1, -1):
		if float(units[i]["hp"]) <= 0.0:
			units.remove_at(i)

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

	# 3. Update VFX Bursts, Item Cast Beams, Card Shatter Popups & Floating Texts
	for i in range(vfx_bursts.size() - 1, -1, -1):
		vfx_bursts[i]["time"] = float(vfx_bursts[i]["time"]) + dt
		if float(vfx_bursts[i]["time"]) >= float(vfx_bursts[i]["duration"]):
			vfx_bursts.remove_at(i)

	for i in range(item_cast_beams.size() - 1, -1, -1):
		item_cast_beams[i]["time"] = float(item_cast_beams[i]["time"]) + dt
		if float(item_cast_beams[i]["time"]) >= float(item_cast_beams[i]["duration"]):
			item_cast_beams.remove_at(i)

	for i in range(shatter_popups.size() - 1, -1, -1):
		shatter_popups[i]["time"] = float(shatter_popups[i]["time"]) + dt
		if float(shatter_popups[i]["time"]) >= float(shatter_popups[i]["duration"]):
			shatter_popups.remove_at(i)

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

	# Gain Mana on basic attack (summons never gain mana; summoner heroes gain no mana while on skill_cd and gain slower mana)
	if not bool(attacker.get("is_summon", false)) and float(attacker["max_mana"]) > 0.0 and float(attacker["silence_timer"]) <= 0.0:
		var is_sum_hero := bool(attacker.get("is_summoner_hero", false))
		if not (is_sum_hero and float(attacker.get("skill_cd", 0.0)) > 0.0):
			var mana_gain := (6.5 if is_sum_hero else 10.0) * (1.15 if elem == "thuy" else 1.0)
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
			"speed": 250.0,
			"rot": (target["pos"] - attacker["pos"]).angle(),
		})
	else:
		_apply_damage(target, raw_dmg, is_magic, elem, attacker)


func _execute_unit_unique_skill(caster: Dictionary, target: Dictionary) -> void:
	if bool(caster.get("is_summon", false)):
		caster["mana"] = 0.0
		return
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

	# Summoner Heroes (C019 Clone, C024 Hound, C030 Turret, C034/C035/C036 Wraith/Skeleton) — high mana, long cooldown, max 1 summon per caster
	if c_num in [19, 24, 30, 34, 35, 36]:
		caster["skill_cd"] = SUMMONER_SKILL_CD
		var sum_id := "s01_linh_cau"
		if c_num == 30:
			sum_id = "s02_phao_co_ngu"
		elif c_num in [19, 34, 35, 36]:
			sum_id = "s03_chien_binh_xuong"

		var caster_uid: int = int(caster["uid"])
		var owner_i: int = int(caster["owner_idx"])
		var max_for_caster: int = 1
		var caster_summons: Array = []
		var team_summon_cnt: int = 0
		for su in units:
			if float(su["hp"]) > 0.0 and bool(su.get("is_summon", false)) and int(su["owner_idx"]) == owner_i:
				team_summon_cnt += 1
				if int(su.get("summoner_uid", -1)) == caster_uid:
					caster_summons.append(su)

		if caster_summons.size() < max_for_caster and team_summon_cnt < MAX_SUMMONS_PER_PLAYER:
			var sum_pos: Vector2 = caster["pos"] + Vector2(randf_range(-28.0, 28.0), randf_range(-24.0, 24.0))
			_spawn_hero_unit(owner_i, int(caster["slot_idx"]), str(caster["card_id"]), elem, true, sum_id, caster_uid, sum_pos)
		elif not caster_summons.is_empty():
			# Heal existing summon modestly instead of spawning duplicates
			var ex_s: Dictionary = caster_summons[0]
			ex_s["summon_ttl"] = 10.0
			_heal_unit(ex_s, float(ex_s["max_hp"]) * 0.35)
		_apply_damage(target, base_dame * 0.65, (rg == "atk_mag"), elem, caster)
		_spawn_element_impact_vfx(target["pos"], elem)
		return

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
				if not bool(low_ally.get("is_summon", false)) and float(low_ally["max_mana"]) > 0.0:
					low_ally["mana"] = minf(low_ally["max_mana"], float(low_ally["mana"]) + 20.0)
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

	var def_stat := (float(target["mdef"]) if is_magic else float(target["def"])) * float(target.get("synergy_def_mult", 1.0))
	if atk_elem == "kim":
		def_stat *= 0.85

	# Tactical Elemental Counter multiplier (+50% Dame dealt when countering / -30% Dame taken when countered)
	var elem_mult := 1.0
	var def_elem: String = str(target["element"])
	if GameState.does_element_counter(atk_elem, def_elem):
		elem_mult = 1.50
	elif GameState.does_element_counter(def_elem, atk_elem):
		elem_mult = 0.70

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
		# Target gains Mana when taking damage (summons never gain mana; summoner heroes gain no mana on skill_cd)
		if not bool(target.get("is_summon", false)) and float(target["max_mana"]) > 0.0 and float(target["silence_timer"]) <= 0.0:
			var is_t_sum := bool(target.get("is_summoner_hero", false))
			if not (is_t_sum and float(target.get("skill_cd", 0.0)) > 0.0):
				target["mana"] = minf(float(target["max_mana"]), float(target["mana"]) + (3.0 if is_t_sum else 5.0))

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


func _trigger_slot_card_destroy(p_idx: int, slot_idx: int, reason_txt: String = "PHÁ HỦY!") -> void:
	if p_idx < 0 or p_idx >= players.size():
		return
	var slots: Array = players[p_idx]["slots"]
	if slot_idx < 0 or slot_idx >= slots.size():
		return
	var slot: Dictionary = slots[slot_idx]
	var cid: String = str(slot.get("card_id", ""))
	var elem: String = str(slot.get("element", "hoa"))
	var c := GameState.get_card(cid) if not cid.is_empty() else {}
	var is_item_card := bool(c.get("is_item", false))

	slot["state"] = "trigger_break"
	slot["unit_uid"] = -1
	slot["trigger_timer"] = 1.45
	slot["trigger_max_timer"] = 1.45

	var sc_pos := _get_slot_center_pos(p_idx, slot_idx)
	var inward_dir := (Vector2(512.0, 512.0) - sc_pos).normalized()
	var popup_pos := sc_pos + inward_dir * 32.0

	_spawn_element_impact_vfx(sc_pos, elem)
	vfx_bursts.append({
		"pos": sc_pos,
		"frames": ["res://assets/board_map/slots/slot_4_trigger_break.png"],
		"time": 0.0,
		"duration": 1.25,
		"scale": 0.56,
	})
	if not cid.is_empty():
		shatter_popups.append({
			"pos": popup_pos,
			"card_id": cid,
			"element": elem,
			"is_item": is_item_card,
			"use_frames": c.get("use_frames", []),
			"time": 0.0,
			"duration": 1.38,
		})
	if not reason_txt.is_empty():
		_add_floating_text(sc_pos + Vector2(0, -18), reason_txt, Color(1.0, 0.64, 0.24))


func _on_unit_killed(u: Dictionary) -> void:
	u["hp"] = 0.0
	var owner_i: int = int(u["owner_idx"])
	var slot_i: int = int(u["slot_idx"])
	if owner_i >= 0 and owner_i < players.size():
		var slots: Array = players[owner_i]["slots"]
		if slot_i >= 0 and slot_i < slots.size() and int(slots[slot_i]["unit_uid"]) == int(u["uid"]):
			_trigger_slot_card_destroy(owner_i, slot_i, "VỠ THẺ!")

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
			"speed": 260.0,
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
	# Tiền Tuyến (Ô #4..#7 -> slot_idx 3..6) steps 26px deeper into the arena;
	# Hậu Phương / Cánh (Ô #1..#3 & #8..#10) stays 14px further back near the player's edge.
	var depth_offset := 26.0 if _is_vanguard_slot(slot_idx) else -14.0
	if p_idx == 0:
		return Vector2(sc.x, 785.0 - depth_offset)
	elif p_idx == 1:
		return Vector2(sc.x, 239.0 + depth_offset)
	elif p_idx == 2:
		return Vector2(239.0 + depth_offset, sc.y)
	else:
		return Vector2(785.0 - depth_offset, sc.y)


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


func _draw_card_in_carved_slot(p_i: int, s_i: int, s_rect: Rect2, slot: Dictionary, u_col: Color) -> void:
	var st: String = str(slot["state"])
	var outer_slot := s_rect.grow(-1.5)
	var inner_rect := s_rect.grow(-3.0)
	var is_vanguard := _is_vanguard_slot(s_i)

	# Always tint the slot background & frame slightly with the owner player's team color for instant visual grouping
	var bg_tint := Color(u_col.r * 0.42, u_col.g * 0.42, u_col.b * 0.42, 0.34)
	var border_tint := Color(
		lerpf(u_col.r, 1.0, 0.18),
		lerpf(u_col.g, 1.0, 0.18),
		lerpf(u_col.b, 1.0, 0.18),
		0.82
	)

	# 1. Empty Carved Socket: team-tinted background + team-colored frame + Tactical Adjacency/Zone preview
	if st == "empty":
		if p_i == 0 and phase == MatchPhase.PREP and selected_hand_idx >= 0 and selected_hand_idx < players[0]["hand"].size():
			var sel_c_inst: Dictionary = players[0]["hand"][selected_hand_idx]
			var sel_elem: String = str(sel_c_inst["element"])
			var adj_preview := _evaluate_slot_adjacency(0, s_i, sel_elem, true)
			var g_cnt: int = int(adj_preview["gen_links"])
			var c_cnt: int = int(adj_preview["clash_links"])
			var zone_lbl := "TIỀN" if is_vanguard else "CÁNH"
			var zone_col := Color(0.76, 0.92, 1.0, 0.90)

			if g_cnt > 0 and c_cnt == 0:
				# Highlight Tương Sinh combo slot in bright emerald-gold!
				board_canvas.draw_rect(inner_rect, Color(0.14, 0.68, 0.34, 0.48), true)
				board_canvas.draw_rect(outer_slot, Color(0.42, 1.0, 0.58, 0.98), false, 2.8)
				zone_lbl = "+SINH"
				zone_col = Color(0.52, 1.0, 0.64, 1.0)
			elif c_cnt > 0 and g_cnt == 0:
				# Highlight Xung Khắc warning slot in crimson!
				board_canvas.draw_rect(inner_rect, Color(0.68, 0.14, 0.20, 0.46), true)
				board_canvas.draw_rect(outer_slot, Color(1.0, 0.36, 0.38, 0.98), false, 2.6)
				zone_lbl = "-KHẮC"
				zone_col = Color(1.0, 0.52, 0.52, 1.0)
			else:
				board_canvas.draw_rect(inner_rect, Color(0.18, 0.62, 1.0, 0.38), true)
				board_canvas.draw_rect(outer_slot, Color(0.48, 0.92, 1.0, 0.96), false, 2.2)

			var f_slot := GameState.get_font()
			board_canvas.draw_string_outline(
				f_slot,
				Vector2(inner_rect.position.x, inner_rect.position.y + inner_rect.size.y * 0.56),
				zone_lbl,
				HORIZONTAL_ALIGNMENT_CENTER,
				inner_rect.size.x,
				11,
				3,
				Color(0.01, 0.01, 0.03, 0.96)
			)
			board_canvas.draw_string(
				f_slot,
				Vector2(inner_rect.position.x, inner_rect.position.y + inner_rect.size.y * 0.56),
				zone_lbl,
				HORIZONTAL_ALIGNMENT_CENTER,
				inner_rect.size.x,
				11,
				zone_col
			)
		else:
			board_canvas.draw_rect(inner_rect, bg_tint, true)
			board_canvas.draw_rect(outer_slot, border_tint, false, (2.2 if is_vanguard else 1.6))
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

	# 3. Trigger Break (Card Destruction / Shatter Effect into 4 Flying Burning Shards!)
	if st == "trigger_break":
		# First draw the team-colored empty socket underneath so it reveals cleanly as shards fly apart
		board_canvas.draw_rect(inner_rect, bg_tint, true)
		board_canvas.draw_rect(outer_slot, border_tint, false, 1.8)

		var cid_br: String = str(slot["card_id"])
		var el_br: String = str(slot["element"])
		var c_br := GameState.get_card(cid_br)
		var rarity_br: String = str(c_br.get("rarity", "N"))
		var rar_col_br: Color = GameState.RARITY_COLOR.get(rarity_br, Color(0.78, 0.82, 0.88))
		var art_tex_br := GameState.tex(str(c_br.get("card_art", "")))
		var sh_tex := GameState.tex("res://assets/board_map/slots/slot_4_trigger_break.png")

		var max_t := maxf(0.01, float(slot.get("trigger_max_timer", 1.45)))
		var rem_t := clampf(float(slot.get("trigger_timer", 0.0)), 0.0, max_t)
		var prog := clampf(1.0 - (rem_t / max_t), 0.0, 1.0) # 0.0 -> 1.0

		var shake_vec := Vector2.ZERO
		if prog < 0.55:
			var shake_amp := (1.0 - prog / 0.55) * 5.2
			shake_vec = Vector2(sin(prog * 95.0) * shake_amp, cos(prog * 82.0) * shake_amp)

		board_canvas.draw_set_transform(center + shake_vec, rot, Vector2.ONE)

		# Split card into 4 shattering quadrants that separate, rotate, burn dark orange-red, and fade out
		var shard_p := clampf((prog - 0.20) / 0.80, 0.0, 1.0)
		var shard_alpha := clampf(1.0 - pow(shard_p, 1.35), 0.0, 1.0)
		var burn_mod := Color(
			1.0,
			lerpf(1.0, 0.32, shard_p),
			lerpf(1.0, 0.12, shard_p),
			shard_alpha
		)
		var dirs := [
			Vector2(-1.0, -1.0),
			Vector2(1.0, -1.0),
			Vector2(-1.0, 1.0),
			Vector2(1.0, 1.0),
		]
		var rots := [-0.72, 0.72, -0.58, 0.58]
		var qw := cw * 0.5
		var qh := ch * 0.5

		for q_i in range(4):
			var d_vec: Vector2 = dirs[q_i]
			var q_center_local := Vector2(d_vec.x * qw * 0.5, d_vec.y * qh * 0.5) + d_vec * (shard_p * 25.0)
			var q_rot: float = float(rots[q_i]) * shard_p
			var q_scale := maxf(0.15, 1.08 - shard_p * 0.48)
			var q_xf := Transform2D(rot, center + shake_vec) * Transform2D(q_rot, q_center_local).scaled_local(Vector2(q_scale, q_scale))
			board_canvas.draw_set_transform_matrix(q_xf)

			var q_rect := Rect2(-qw * 0.5, -qh * 0.5, qw, qh)
			board_canvas.draw_rect(q_rect, Color(0.08, 0.04, 0.04, shard_alpha * 0.95), true)
			if art_tex_br:
				var uv_x := 0.0 if d_vec.x < 0.0 else 0.5
				var uv_y := 0.0 if d_vec.y < 0.0 else 0.5
				var asz := art_tex_br.get_size()
				board_canvas.draw_texture_rect_region(
					art_tex_br,
					q_rect,
					Rect2(asz.x * uv_x, asz.y * uv_y, asz.x * 0.5, asz.y * 0.5),
					burn_mod
				)
			# Rarity border + glowing fracture edge on each shard
			board_canvas.draw_rect(q_rect, Color(rar_col_br.r, rar_col_br.g, rar_col_br.b, shard_alpha * 0.85), false, 1.8)
			board_canvas.draw_rect(q_rect.grow(-1.0), Color(1.0, 0.62, 0.18, shard_alpha * 0.92), false, 1.4)

		# Draw expanding `slot_4_trigger_break.png` explosion & crack lines over the shattering slot
		var burst_sc := 1.05 + prog * 0.65
		var burst_alpha := clampf(1.25 - prog * 1.25, 0.0, 1.0)
		board_canvas.draw_set_transform(center + shake_vec, rot, Vector2(burst_sc, burst_sc))
		if sh_tex:
			board_canvas.draw_texture_rect(sh_tex, local_rect.grow(6.0), false, Color(1.0, 0.92, 0.78, burst_alpha))
		if prog < 0.55:
			var fl_a := (1.0 - prog / 0.55) * 0.85
			board_canvas.draw_line(Vector2(-cw * 0.48, -ch * 0.48), Vector2(cw * 0.48, ch * 0.48), Color(1.0, 0.88, 0.38, fl_a), 2.4)
			board_canvas.draw_line(Vector2(cw * 0.48, -ch * 0.48), Vector2(-cw * 0.48, ch * 0.48), Color(1.0, 0.52, 0.18, fl_a), 2.4)

		board_canvas.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
		return

	board_canvas.draw_set_transform(center, rot, Vector2.ONE)

	# 4. Opponent Face-Down Card -> Fit Card Back directly into the carved socket
	if st == "facedown" and p_i > 0:
		var back_tex := GameState.tex("res://assets/mobile/cards/frames/card_back_slot_256x384.png")
		if back_tex:
			board_canvas.draw_texture_rect(back_tex, full_tex_rect, false)
		else:
			board_canvas.draw_rect(local_rect, Color(0.10, 0.14, 0.24), true)
		board_canvas.draw_rect(local_rect, u_col * Color(1, 1, 1, 0.90), false, 1.5)
		board_canvas.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
		return

	# 5. Player 0 Face-Down Card OR Any Active Revealed Card (active_hero)
	#    -> Render Full-Bleed Card Artwork + 2 Circular Badges (Element & Card Type/Role) + Rarity Border!
	var cid: String = str(slot["card_id"])
	var el: String = str(slot["element"])
	var c := GameState.get_card(cid)
	var rarity: String = str(c.get("rarity", "N"))
	var rarity_col: Color = GameState.RARITY_COLOR.get(rarity, Color(0.78, 0.82, 0.88))
	var role_group: String = str(c.get("role_group", "atk_phys"))
	var elem_meta: Dictionary = GameState.ELEMENT_META.get(el, GameState.ELEMENT_META["kim"])
	var e_col: Color = elem_meta["color"]

	# Subtle outer rarity aura for S / SSR cards on the board
	if rarity == "SSR":
		board_canvas.draw_rect(local_rect.grow(2.5), Color(1.0, 0.78, 0.16, 0.55), false, 2.5)
	elif rarity == "S":
		board_canvas.draw_rect(local_rect.grow(2.0), Color(0.82, 0.38, 1.0, 0.50), false, 2.2)

	# Dark card base
	board_canvas.draw_rect(local_rect, Color(0.05, 0.07, 0.11, 0.98), true)

	# Full-Slot Weapon / Item Illustration (center-cropped so artwork fills the entire slot cleanly)
	var art_tex := GameState.tex(str(c.get("card_art", "")))
	var art_fill_rect := local_rect.grow(-1.5)
	if art_tex:
		var asz := art_tex.get_size()
		var crop_w := asz.x * 0.78
		var crop_x := (asz.x - crop_w) * 0.5
		board_canvas.draw_texture_rect_region(
			art_tex,
			art_fill_rect,
			Rect2(crop_x, 0.0, crop_w, asz.y),
			Color(1.0, 1.0, 1.0, 0.88 if st == "facedown" else 1.0)
		)

	# Crisp Rarity-Colored Card Border inside the carved slot (N=Silver, R=Blue, S=Purple, SSR=Gold)
	board_canvas.draw_rect(local_rect.grow(-1.5), Color(0.02, 0.03, 0.06, 0.88), false, 1.0)
	var rim_w := 2.6 if rarity in ["S", "SSR"] else 2.2
	board_canvas.draw_rect(local_rect, rarity_col, false, rim_w)

	# 2 Circular Badges at the top corners: Left = Element (Hệ Ngũ Hành), Right = Card Type / Role (Loại thẻ)
	var badge_r := 8.8
	var icon_sz := 15.0
	var e_pos := Vector2(-cw * 0.5 + 10.5, -ch * 0.5 + 10.5)
	var r_pos := Vector2(cw * 0.5 - 10.5, -ch * 0.5 + 10.5)

	board_canvas.draw_circle(e_pos, badge_r, Color(0.04, 0.06, 0.10, 0.94))
	board_canvas.draw_arc(e_pos, badge_r, 0.0, TAU, 20, e_col, 1.6)
	var e_icon := GameState.tex(str(elem_meta.get("icon", "")))
	if e_icon:
		board_canvas.draw_texture_rect(e_icon, Rect2(e_pos.x - icon_sz * 0.5, e_pos.y - icon_sz * 0.5, icon_sz, icon_sz), false)

	var role_meta: Dictionary = GameState.ROLE_META.get(role_group, GameState.ROLE_META["atk_phys"])
	var r_col: Color = role_meta.get("color", rarity_col)
	board_canvas.draw_circle(r_pos, badge_r, Color(0.04, 0.06, 0.10, 0.94))
	board_canvas.draw_arc(r_pos, badge_r, 0.0, TAU, 20, r_col, 1.6)
	var r_icon := GameState.tex(str(role_meta.get("icon", "")))
	if r_icon:
		board_canvas.draw_texture_rect(r_icon, Rect2(r_pos.x - icon_sz * 0.5, r_pos.y - icon_sz * 0.5, icon_sz, icon_sz), false)

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

		# Subtle team-colored strip behind the entire 10-slot row/column for this player
		if is_alive:
			var strip_rect := Rect2(201, 873, 621, 87)
			if seat_i == 1:
				strip_rect = Rect2(202, 64, 618, 87)
			elif seat_i == 2:
				strip_rect = Rect2(63, 199, 85, 620)
			elif seat_i == 3:
				strip_rect = Rect2(876, 198, 85, 623)
			board_canvas.draw_rect(strip_rect, Color(u_col.r * 0.35, u_col.g * 0.35, u_col.b * 0.35, 0.22), true)
			board_canvas.draw_rect(strip_rect, Color(u_col.r, u_col.g, u_col.b, 0.52), false, 1.6)

		for s_i in range(10):
			var s_rect := _get_slot_rect(seat_i, s_i)
			if not is_alive:
				var dead_s := s_rect.grow(-3.0)
				board_canvas.draw_rect(dead_s, Color(0.28, 0.30, 0.34, 0.80), true)
				board_canvas.draw_rect(dead_s, Color(0.48, 0.50, 0.55, 0.65), false, 1.0)
			else:
				_draw_card_in_carved_slot(seat_i, s_i, s_rect, slots[s_i], u_col)

		# Draw Adjacent Slot Elemental Links (Tương Sinh glowing beam vs Xung Khắc warning crack)
		if is_alive:
			_draw_slot_adjacency_links_for_player(seat_i, slots)

		# Inside the Carved Corner Socket: draw team-tinted 2D slot box + team-colored background & border
		var team_panel_mod := Color(
			lerpf(1.0, u_col.r, 0.52),
			lerpf(1.0, u_col.g, 0.52),
			lerpf(1.0, u_col.b, 0.52),
			1.0
		)
		var slot_mod := Color(1.22, 0.55, 0.55, 1.0) if float(p["hit_flash"]) > 0.0 else (team_panel_mod if is_alive else Color.WHITE)
		board_canvas.draw_style_box(
			GameState.make_gui_panel_style("slot_active" if is_alive else "slot_gray", 8, slot_mod),
			inner_corner
		)
		if is_alive:
			board_canvas.draw_rect(inner_corner.grow(-2.0), Color(u_col.r * 0.45, u_col.g * 0.45, u_col.b * 0.45, 0.34), true)
			board_canvas.draw_rect(inner_corner, Color(lerpf(u_col.r, 1.0, 0.22), lerpf(u_col.g, 1.0, 0.22), lerpf(u_col.b, 1.0, 0.22), 0.92), false, 2.5)

		# Draw directional connector bar from Corner Socket -> that player's 10 Card Slots
		var arrow_col := Color(lerpf(u_col.r, 1.0, 0.22), lerpf(u_col.g, 1.0, 0.22), lerpf(u_col.b, 1.0, 0.22), 0.92)
		if seat_i == 0:
			board_canvas.draw_line(Vector2(190, 916), Vector2(204, 916), arrow_col, 4.5)
		elif seat_i == 1:
			board_canvas.draw_line(Vector2(834, 108), Vector2(818, 108), arrow_col, 4.5)
		elif seat_i == 2:
			board_canvas.draw_line(Vector2(106, 190), Vector2(106, 202), arrow_col, 4.5)
		else:
			board_canvas.draw_line(Vector2(918, 834), Vector2(918, 818), arrow_col, 4.5)

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

		var cur_e: int = int(p.get("energy", 0))
		var status_line := "LL:%d · Tay:%d · Sân:%d" % [cur_e, p["hand"].size(), unit_cnt]
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


func _draw_slot_adjacency_links_for_player(seat_i: int, slots: Array) -> void:
	for s_i in range(9):
		var sa: Dictionary = slots[s_i]
		var sb: Dictionary = slots[s_i + 1]
		var sta: String = str(sa.get("state", "empty"))
		var stb: String = str(sb.get("state", "empty"))
		# Only reveal opponent links on active_hero cards; for Player 0, also show links on face-down cards during PREP!
		var vis_a := (sta == "active_hero") or (seat_i == 0 and sta == "facedown")
		var vis_b := (stb == "active_hero") or (seat_i == 0 and stb == "facedown")
		if not (vis_a and vis_b):
			continue
		var rel := _get_slot_link_relation(str(sa.get("element", "")), str(sb.get("element", "")))
		if rel == 0:
			continue
		var ra := _get_slot_rect(seat_i, s_i)
		var rb := _get_slot_rect(seat_i, s_i + 1)
		var pa := ra.get_center()
		var pb := rb.get_center()
		var mid := (pa + pb) * 0.5
		if rel == 1:
			# Tương Sinh Link: glowing emerald-gold energy bridge between the 2 adjacent slots
			board_canvas.draw_line(pa, pb, Color(0.24, 0.98, 0.52, 0.88), 4.2)
			board_canvas.draw_line(pa, pb, Color(0.98, 0.94, 0.52, 0.95), 2.0)
			board_canvas.draw_rect(Rect2(mid.x - 4.5, mid.y - 4.5, 9.0, 9.0), Color(0.32, 1.0, 0.58, 0.98), true)
			board_canvas.draw_rect(Rect2(mid.x - 4.5, mid.y - 4.5, 9.0, 9.0), Color(1.0, 0.96, 0.68, 1.0), false, 1.5)
		elif rel == -1:
			# Xung Khắc Clash: crimson-purple warning fracture between the 2 adjacent slots
			board_canvas.draw_line(pa, pb, Color(0.98, 0.22, 0.30, 0.90), 3.6)
			board_canvas.draw_rect(Rect2(mid.x - 4.0, mid.y - 4.0, 8.0, 8.0), Color(0.95, 0.18, 0.26, 0.96), true)


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

	# 2. Draw Item Cast Beams & Flying Item Orbs (Slot -> Target Hero)
	for bm in item_cast_beams:
		var b_prog := clampf(float(bm["time"]) / maxf(0.01, float(bm["duration"])), 0.0, 1.0)
		var b_from: Vector2 = bm["from"]
		var b_to: Vector2 = bm["to"]
		var is_sup: bool = bool(bm.get("is_support", false))
		var beam_col := Color(0.28, 0.98, 0.62) if is_sup else Color(1.0, 0.46, 0.26)
		var b_alpha := clampf(1.25 - b_prog * 1.25, 0.0, 1.0)

		# Glowing energy beam from item slot to target hero
		fx_layer.draw_line(b_from, b_to, Color(beam_col.r, beam_col.g, beam_col.b, b_alpha * 0.55), 8.0)
		fx_layer.draw_line(b_from, b_to, Color(1.0, 0.96, 0.78, b_alpha * 0.92), 3.2)

		# Traveling item orb along the beam during first 55% of duration
		var travel_t := clampf(b_prog / 0.55, 0.0, 1.0)
		var orb_pos := b_from.lerp(b_to, travel_t)
		var b_frames: Array = bm.get("frames", [])
		if not b_frames.is_empty():
			var bf_idx := int(b_prog * float(b_frames.size()) * 2.0) % b_frames.size()
			var orb_tex := GameState.tex(str(b_frames[bf_idx]))
			if orb_tex:
				var orb_sc := lerpf(0.38, 0.56, sin(b_prog * PI))
				fx_layer.draw_set_transform(orb_pos, b_prog * 4.5, Vector2(orb_sc, orb_sc))
				fx_layer.draw_texture(orb_tex, -orb_tex.get_size() * 0.5, Color(1, 1, 1, b_alpha))
				fx_layer.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

		# Expanding target lock-on ring at `b_to`
		var ring_r := lerpf(22.0, 56.0, b_prog)
		fx_layer.draw_arc(b_to, ring_r, 0.0, TAU, 28, Color(beam_col.r, beam_col.g, beam_col.b, b_alpha * 0.88), 3.2)

	# 3. Draw Hit Impact & Item Use Bursts
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

	# 4. Draw Enlarged Pop-Up 4-Shard Card Shatter & Item Activation Overlays
	var sh_break_tex := GameState.tex("res://assets/board_map/slots/slot_4_trigger_break.png")
	for sp in shatter_popups:
		var sp_prog := clampf(float(sp["time"]) / maxf(0.01, float(sp["duration"])), 0.0, 1.0)
		var sp_pos: Vector2 = sp["pos"]
		var sp_cid: String = str(sp["card_id"])
		var sp_c := GameState.get_card(sp_cid)
		var sp_rarity: String = str(sp_c.get("rarity", "N"))
		var sp_art := GameState.tex(str(sp_c.get("card_art", "")))
		var sp_rar_col: Color = GameState.RARITY_COLOR.get(sp_rarity, Color(0.82, 0.85, 0.92))
		var is_item_sp: bool = bool(sp.get("is_item", false))

		var pw := 92.0
		var ph := 138.0
		var shake_v := Vector2.ZERO
		if sp_prog < 0.45:
			var s_amp := (1.0 - sp_prog / 0.45) * 6.5
			shake_v = Vector2(sin(sp_prog * 96.0) * s_amp, cos(sp_prog * 84.0) * s_amp)

		var shard_t := clampf((sp_prog - 0.18) / 0.82, 0.0, 1.0)
		var shard_a := clampf(1.0 - pow(shard_t, 1.30), 0.0, 1.0)
		var burn_c := Color(
			1.0,
			lerpf(1.0, 0.34, shard_t),
			lerpf(1.0, 0.12, shard_t),
			shard_a
		)
		var s_dirs := [
			Vector2(-1.0, -1.0),
			Vector2(1.0, -1.0),
			Vector2(-1.0, 1.0),
			Vector2(1.0, 1.0),
		]
		var s_rots := [-0.82, 0.82, -0.64, 0.64]
		var qw := pw * 0.5
		var qh := ph * 0.5

		for q_i in range(4):
			var dv: Vector2 = s_dirs[q_i]
			var q_loc := Vector2(dv.x * qw * 0.5, dv.y * qh * 0.5) + dv * (shard_t * 44.0)
			var q_r: float = float(s_rots[q_i]) * shard_t
			var q_sc := maxf(0.18, 1.12 - shard_t * 0.52)
			var q_xf := Transform2D(0.0, sp_pos + shake_v) * Transform2D(q_r, q_loc).scaled_local(Vector2(q_sc, q_sc))
			fx_layer.draw_set_transform_matrix(q_xf)

			var qr := Rect2(-qw * 0.5, -qh * 0.5, qw, qh)
			fx_layer.draw_rect(qr, Color(0.08, 0.04, 0.05, shard_a * 0.96), true)
			if sp_art:
				var ux := 0.0 if dv.x < 0.0 else 0.5
				var uy := 0.0 if dv.y < 0.0 else 0.5
				var asz := sp_art.get_size()
				fx_layer.draw_texture_rect_region(
					sp_art,
					qr,
					Rect2(asz.x * ux, asz.y * uy, asz.x * 0.5, asz.y * 0.5),
					burn_c
				)
			fx_layer.draw_rect(qr, Color(sp_rar_col.r, sp_rar_col.g, sp_rar_col.b, shard_a * 0.85), false, 2.2)
			fx_layer.draw_rect(qr.grow(-1.5), Color(1.0, 0.58, 0.16, shard_a * 0.95), false, 1.6)

		# Overlay Item Use 4-frame burst or `slot_4_trigger_break.png` crack flash over the shattering card
		var b_sc := 1.05 + sp_prog * 0.65
		var b_al := clampf(1.25 - sp_prog * 1.25, 0.0, 1.0)
		fx_layer.draw_set_transform(sp_pos + shake_v, 0.0, Vector2(b_sc, b_sc))
		if is_item_sp:
			var u_frames: Array = sp.get("use_frames", [])
			if not u_frames.is_empty():
				var uf_i := mini(u_frames.size() - 1, int(sp_prog * float(u_frames.size()) * 1.5))
				var utex := GameState.tex(str(u_frames[uf_i]))
				if utex:
					fx_layer.draw_texture_rect(utex, Rect2(-56, -56, 112, 112), false, Color(1, 1, 1, b_al))
		if sh_break_tex:
			fx_layer.draw_texture_rect(sh_break_tex, Rect2(-pw * 0.55, -ph * 0.55, pw * 1.1, ph * 1.1), false, Color(1.0, 0.92, 0.78, b_al))
		fx_layer.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

	# 5. Draw Floating Combat Numbers & Skill Callouts
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
				elif slots[s_i]["state"] == "empty" and selected_hand_idx >= 0:
					place_card_from_hand(0, selected_hand_idx, s_i)
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
	var best_slot: int = BotAI.choose_best_slot(c_inst, players[0]["slots"])
	if best_slot >= 0:
		place_card_from_hand(0, idx, best_slot)
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
	var p0_e: int = int(players[0].get("energy", 0)) if not players.is_empty() else 0
	var p0_max_e: int = int(players[0].get("max_energy", 6)) if not players.is_empty() else 6
	var new_info := "Linh Lực: %d/%d · Cọc: %d · Tướng: %d" % [
		p0_e,
		p0_max_e,
		shared_deck.size(),
		living_units
	]
	if lbl_deck_info.text != new_info:
		lbl_deck_info.text = new_info
