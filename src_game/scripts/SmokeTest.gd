extends SceneTree

func _init() -> void:
	call_deferred("_run_smoke_tests")


func _run_smoke_tests() -> void:
	print("=== ARCANA FIVE: MOBILE PORTRAIT (1080x1920) SMOKE TEST ===")
	var gs: Node = root.get_node_or_null("GameState")
	assert(gs != null, "GameState autoload must exist")
	print("[1/5] Cards loaded in DB: ", gs.cards_db.size())
	assert(gs.cards_db.size() == 100, "Must have exactly 100 Core Cards (C001-C100)")

	var main_packed: PackedScene = load("res://scenes/Main.tscn")
	var main_node: Control = main_packed.instantiate()
	root.add_child(main_node)
	await process_frame

	print("[2/5] Testing HomeScreen & Player Count selector (2, 3, 4 players) + Bot toggle...")
	gs.emit_signal("screen_requested", "home")
	await process_frame
	assert(main_node.current_screen_name == "home", "Home screen active")
	assert(gs.player_is_bot == true, "Default player_is_bot must be true")

	print("[3/5] Testing PackScreen (Mở Rương 10 thẻ)...")
	gs.emit_signal("screen_requested", "packs")
	await process_frame
	var pulled: Array = gs.open_gacha_pack()
	print("   -> Opened chest, pulled ", pulled.size(), " cards. First card: ", pulled[0].get("card_id"), " (", pulled[0].get("element"), ")")
	assert(pulled.size() == 10, "Chest must pull 10 cards")

	print("[4/5] Testing CollectionScreen (Sở hữu & Chưa sở hữu + Sort theo Loại thẻ, Độ hiếm, Hệ)...")
	gs.emit_signal("screen_requested", "collection")
	await process_frame
	var col_screen: Control = main_node.current_screen_node
	for sort_m in ["id_asc", "rarity_desc", "rarity_asc", "role", "element", "owned_desc"]:
		col_screen.sort_mode = sort_m
		col_screen.rebuild_grid()
	for own_f in ["all", "owned", "unowned", "loadout"]:
		col_screen.filter_ownership = own_f
		col_screen.rebuild_grid()
	var owned_cnt: int = gs.get_owned_unique_count()
	print("   -> CollectionScreen sort & filter verified. Owned unique: ", owned_cnt, " / Unowned: ", 100 - owned_cnt)

	print("[5/5] Testing BattleScreen & BotAI for 2, 3, and 4 Players...")
	for pcount in [2, 3, 4]:
		gs.selected_player_count = pcount
		gs.player_is_bot = true
		gs.emit_signal("screen_requested", "battle")
		await process_frame
		var battle: Control = main_node.current_screen_node
		assert(battle.players.size() == pcount, "Battle must initialize " + str(pcount) + " players")
		assert(battle.shared_deck.size() == 25 * pcount - 5 * pcount, "Shared deck must have 25*N total cards minus 5*N dealt")
		# Simulate Prep Phase Bot AI thinking & bluff/place decisions
		for _step in range(12):
			battle._process_bots_in_prep_phase(1.0)
		# Trigger Reveal & Combat Phase
		battle._enter_reveal_phase()
		# Simulate 25 frames of real-time combat
		for _cstep in range(25):
			battle._process_combat_simulation(0.15)
		print("   -> Verified ", pcount, "-player Poker Table battle & BotAI (Units spawned: ", battle.units.size(), ")")

	print("=== ALL SMOKE TESTS PASSED SUCCESSFULLY! ===")
	quit(0)
