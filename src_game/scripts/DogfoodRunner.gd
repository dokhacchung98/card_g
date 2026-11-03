extends SceneTree

const OUT_DIR := "/Users/dochung/Desktop/card_g/src_game/dogfood_screenshots"

var sub_vp: SubViewport
var main_node: Control


func _init() -> void:
	call_deferred("_run_dogfood")


func _wait_frames(count: int = 4) -> void:
	for _i in range(count):
		await process_frame


func _capture(filename: String) -> void:
	await _wait_frames(6)
	var img: Image = sub_vp.get_texture().get_image()
	var full_path := OUT_DIR + "/" + filename
	var err := img.save_png(full_path)
	print("[DOGFOOD SNAPSHOT] Saved ", full_path, " (", img.get_width(), "x", img.get_height(), ") err=", err)


func _run_dogfood() -> void:
	print("=== STARTING VISUAL DOGFOOD & E2E VERIFICATION ===")
	DirAccess.make_dir_recursive_absolute(OUT_DIR)

	var gs: Node = root.get_node_or_null("GameState")
	assert(gs != null, "GameState must be loaded")

	# Reset to clean starter state for reproducible visual verification
	gs.gold = 3500
	gs.diamonds = 600
	gs.pack_counts_by_type = {1: 4, 2: 3, 3: 3, 4: 2, 5: 2}
	gs.selected_pack_type = 4
	gs.sync_total_pack_count()
	gs.selected_player_count = 4
	gs.player_is_bot = true
	gs.auto_build_valid_loadout()

	# Wrap 1080x1920 SubViewport inside a full-window SubViewportContainer so the OS window renders live UI (never gray!)
	var svc := SubViewportContainer.new()
	svc.position = Vector2.ZERO
	svc.size = Vector2(1080, 1920)
	svc.stretch = true
	root.add_child(svc)
	svc.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)

	sub_vp = SubViewport.new()
	sub_vp.size = Vector2i(1080, 1920)
	sub_vp.size_2d_override = Vector2i(1080, 1920)
	sub_vp.size_2d_override_stretch = true
	sub_vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	sub_vp.transparent_bg = false
	svc.add_child(sub_vp)

	var main_packed: PackedScene = load("res://scenes/Main.tscn")
	main_node = main_packed.instantiate()
	sub_vp.add_child(main_node)

	await _wait_frames(6)

	# 1. HOME SCREEN (4 Players selected, Bot AI ON, 15-card Loadout preview)
	gs.emit_signal("screen_requested", "home")
	await _wait_frames(6)
	await _capture("01_home_screen.png")

	# 1B, 1C, 1D. TUTORIAL & GUIDE MODAL (All 3 Tabs: Xung Khắc 5 Hệ | Cách Chơi & Úp Bài | Chiến Đấu & 2 Tiền Tệ Coin/Kim Cương)
	gs.emit_signal("guide_requested", 0)
	await _wait_frames(5)
	await _capture("01b_tutorial_guide_wuxing.png")
	main_node.guide_modal.switch_tab(1)
	await _wait_frames(5)
	await _capture("01d_tutorial_guide_howtoplay.png")
	main_node.guide_modal.switch_tab(2)
	await _wait_frames(5)
	await _capture("01c_tutorial_guide_currencies.png")
	main_node.guide_modal.hide_guide()
	await _wait_frames(4)

	# 2. PACK OPENING CEREMONY (Full-screen black overlay -> Pack rises to center & bursts -> White flash -> 10 Face-down cards & interactive flip)
	gs.emit_signal("screen_requested", "packs")
	await _wait_frames(5)
	var pack_screen: Control = main_node.current_screen_node
	# Verify buying Pack #2 with Coin and Pack #5 with Kim Cương
	var buy_coin_res: Dictionary = gs.buy_pack(2, 1)
	var buy_dia_res: Dictionary = gs.buy_pack(5, 1)
	assert(bool(buy_coin_res.get("ok", false)), "Buying Pack #2 with Coin must succeed")
	assert(bool(buy_dia_res.get("ok", false)), "Buying Pack #5 with Diamonds must succeed")
	gs.selected_pack_type = 5
	pack_screen.lbl_pull_summary.text = str(buy_dia_res.get("msg", ""))
	pack_screen.refresh_header()
	await _capture("02b_pack_shop_coin_diamond.png")
	gs.selected_pack_type = 4
	pack_screen.refresh_header()
	var sel_id := 4
	pack_screen.current_pulled_items = gs.open_gacha_pack(sel_id)
	pack_screen.current_pull_counts = {"SSR": 0, "S": 0, "R": 0, "N": 0, "NEW": 0}
	for item in pack_screen.current_pulled_items:
		var tier: String = str(item["rarity"])
		pack_screen.current_pull_counts[tier] = int(pack_screen.current_pull_counts.get(tier, 0)) + 1
		if bool(item["is_new"]):
			pack_screen.current_pull_counts["NEW"] += 1

	# Stage 2A: Capture the Pack at the center of the Black Overlay during its opening burst animation
	pack_screen.ceremony_overlay.visible = true
	pack_screen.ceremony_pack_stage.visible = true
	pack_screen.ceremony_cards_stage.visible = false
	pack_screen.ceremony_pack_sprite.position = Vector2(310, 710)
	pack_screen.ceremony_pack_sprite.scale = Vector2(1.18, 1.18)
	if pack_screen.pack_frames.size() >= 4:
		pack_screen.ceremony_pack_sprite.texture = pack_screen.pack_frames[2]
	pack_screen.ceremony_pack_label.text = "XÉ ĐỈNH RƯƠNG BÀI — CHUẨN BỊ BUNG NỔ HÀO QUANG!"
	await _capture("02a_pack_ceremony_pack_burst.png")

	# Stage 2B: Capture the 10 Cards on the Black Overlay (5 cards flipped face-up including S & SSR to showcase the glowing shadow effect, 5 cards face-down without border or button)
	if pack_screen.current_pulled_items.size() >= 4:
		pack_screen.current_pulled_items[0] = {"card_id": "C001", "element": "kim", "rarity": "N", "is_new": false}
		pack_screen.current_pulled_items[1] = {"card_id": "C018", "element": "hoa", "rarity": "SSR", "is_new": true}
		pack_screen.current_pulled_items[2] = {"card_id": "C013", "element": "hoa", "rarity": "S", "is_new": true}
		pack_screen.current_pulled_items[3] = {"card_id": "C007", "element": "thuy", "rarity": "R", "is_new": false}
	pack_screen._populate_ceremony_and_background_cards(sel_id)
	pack_screen.ceremony_pack_stage.visible = false
	pack_screen.ceremony_cards_stage.visible = true
	for i in range(min(4, pack_screen.ceremony_card_widgets.size())):
		var cw: Control = pack_screen.ceremony_card_widgets[i]
		cw.face_down = false
		cw.queue_redraw()
	pack_screen._update_ceremony_flip_counter()
	await _capture("02_pack_opening_10_cards.png")
	pack_screen._on_close_ceremony_pressed()

	# 3. COLLECTION SCREEN (Owned & Unowned cards side by side, sorted by ID)
	gs.emit_signal("screen_requested", "collection")
	await _wait_frames(6)
	var col_screen: Control = main_node.current_screen_node
	col_screen.filter_ownership = "all"
	col_screen.sort_mode = "id_asc"
	col_screen.rebuild_grid()
	await _capture("03_collection_owned_and_unowned.png")

	# 4. COLLECTION SCREEN (Sorted by Rarity SSR->N + Card Detail Modal open)
	gs.owned_counts["C018_hoa"] = maxi(1, int(gs.owned_counts.get("C018_hoa", 0)))
	col_screen.sort_mode = "rarity_desc"
	col_screen.rebuild_grid()
	await _wait_frames(4)
	gs.emit_signal("card_inspect_requested", "C018", "hoa")
	await _wait_frames(5)
	await _capture("04_collection_sort_ssr_and_modal.png")
	main_node.detail_modal.visible = false
	await _wait_frames(3)

	# 5. BATTLE SCREEN — 4 PLAYERS PREP PHASE (Bot AI placing & bluffing face-down cards)
	gs.selected_player_count = 4
	gs.player_is_bot = true
	gs.emit_signal("screen_requested", "battle")
	await _wait_frames(6)
	var battle_screen: Control = main_node.current_screen_node
	for _s in range(6):
		battle_screen._process_bots_in_prep_phase(1.0)
	battle_screen.phase_timer = 8.4
	battle_screen._update_top_hud_labels()
	battle_screen.board_canvas.queue_redraw()
	await _capture("05_battle_4p_prep_bluff_phase.png")

	# 6. BATTLE SCREEN — 4 PLAYERS REAL-TIME AUTO COMBAT (Stickman Heroes + Weapons + Projectiles + VFX)
	for _s in range(8):
		battle_screen._process_bots_in_prep_phase(1.0)
	battle_screen._enter_reveal_phase()
	for _c in range(18):
		battle_screen._process_combat_simulation(0.16)
	battle_screen.phase_timer = 11.2
	battle_screen._update_top_hud_labels()
	battle_screen.board_canvas.queue_redraw()
	battle_screen.fx_layer.queue_redraw()
	await _capture("06_battle_4p_realtime_combat.png")

	# 7. BATTLE SCREEN — 2 PLAYERS MODE (2 Gray Empty Corners + Enemy Heroes Attacking Defenseless Player's Corner HP Socket!)
	gs.selected_player_count = 2
	gs.emit_signal("screen_requested", "battle")
	await _wait_frames(6)
	battle_screen = main_node.current_screen_node
	for _s in range(8):
		battle_screen._process_bots_in_prep_phase(1.0)
	battle_screen._enter_reveal_phase()
	# Simulate P2 losing all heroes on the board so P1's heroes charge P2's Top-Right Corner HP Socket!
	for u in battle_screen.units:
		if int(u["owner_idx"]) == 1:
			battle_screen._on_unit_killed(u)
	for _c in range(32):
		battle_screen._process_combat_simulation(0.16)
	battle_screen.board_canvas.queue_redraw()
	battle_screen.fx_layer.queue_redraw()
	await _capture("07_battle_2p_and_history_modal.png")

	# Restore 4-player default before exiting so saved state has all 4 corners active
	gs.selected_player_count = 4
	gs.save_game()

	print("=== VISUAL DOGFOOD COMPLETED SUCCESSFULLY! ===")
	quit(0)
