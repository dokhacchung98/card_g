extends SceneTree

func _init() -> void:
	call_deferred("_run_verification")


func _run_verification() -> void:
	print("=== VERIFYING FIRST-SCREEN GOOGLE LOGIN & 15 STARTER CARDS ===")
	var gs := root.get_node_or_null("GameState")
	var bc := root.get_node_or_null("BackendClient")
	assert(gs != null and bc != null, "Autoloads must exist")

	# Reset to brand-new unauthenticated player state
	if FileAccess.file_exists(gs.SAVE_PATH):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(gs.SAVE_PATH))
	if FileAccess.file_exists(bc.AUTH_SAVE_PATH):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(bc.AUTH_SAVE_PATH))

	bc.logout()
	for k in gs.owned_counts.keys():
		gs.owned_counts[k] = 0
	gs.loadout_deck.clear()
	gs.just_granted_starter_15 = false
	gs._rebuild_unlocked_elements_from_owned()

	assert(not bc.is_logged_in(), "Must not be logged in initially")
	assert(gs.get_owned_unique_count() == 0, "Brand new account before first login must have 0 cards")
	assert(gs.loadout_deck.size() == 0, "Brand new account before first login must have 0 loadout cards")

	var main_scene: PackedScene = load("res://scenes/Main.tscn")
	var main_inst: Control = main_scene.instantiate()
	root.add_child(main_inst)
	await process_frame
	await process_frame

	print("Initial screen when not logged in: ", main_inst.current_screen_name)
	assert(main_inst.current_screen_name == "login", "First screen MUST be 'login' when not logged in!")

	# Simulate first-time Google login
	gs.grant_first_login_starter_15_cards()
	bc.current_user["isGoogleLinked"] = true
	bc.current_user["email"] = "dokhacchung98@gmail.com"
	bc.current_user["displayName"] = "Đại Pháp Sư Lam Long"
	bc._save_auth()
	bc.emit_signal("login_succeeded", bc.current_user, true)
	await process_frame
	await process_frame

	print("Screen after Google login: ", main_inst.current_screen_name)
	print("Owned unique cards after first login: ", gs.get_owned_unique_count())
	print("Loadout deck size after first login: ", gs.loadout_deck.size())
	var v_check: Dictionary = gs.is_loadout_valid(gs.loadout_deck)
	print("Loadout validation: ", v_check)

	assert(main_inst.current_screen_name == "home", "Must transition to 'home' after Google login!")
	assert(gs.get_owned_unique_count() == 15, "First login must grant 15 default starter cards!")
	assert(gs.loadout_deck.size() == 15, "First login must equip 15 default starter cards!")
	assert(bool(v_check.get("ok", false)), "15 default starter cards must form a valid 15/15 loadout!")
	assert(gs.just_granted_starter_15 == true, "just_granted_starter_15 flag must be true on first login!")

	# Clean up test save files so exported build starts clean for new users
	if FileAccess.file_exists(gs.SAVE_PATH):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(gs.SAVE_PATH))
	if FileAccess.file_exists(bc.AUTH_SAVE_PATH):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(bc.AUTH_SAVE_PATH))

	print("=== ALL LOGIN & 15 STARTER CARDS CHECKS PASSED! ===")
	quit(0)
