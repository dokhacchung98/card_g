extends SceneTree

var overflow_count: int = 0

func _init() -> void:
	call_deferred("_run_audit")


func _dump_control(c: Control, depth: int = 0, max_depth: int = 4, inside_scroll: bool = false) -> void:
	if depth > max_depth:
		return
	var indent := "  ".repeat(depth)
	var r := c.get_global_rect()
	var min_sz := c.get_combined_minimum_size()
	var clip_warn := ""
	var is_scroll := c is ScrollContainer
	if not inside_scroll:
		if r.position.x < -0.5 or r.end.x > 1080.5 or r.position.y < -0.5 or r.end.y > 1920.5:
			clip_warn = " [!!! OVERFLOW: rect=%s end=(%.1f, %.1f) !!!]" % [str(r), r.end.x, r.end.y]
			overflow_count += 1
	else:
		# Inside a vertical ScrollContainer, horizontal must still stay within [0, 1080]!
		if r.position.x < -0.5 or r.end.x > 1080.5:
			clip_warn = " [!!! HORIZONTAL OVERFLOW IN SCROLL: rect=%s end_x=%.1f !!!]" % [str(r), r.end.x]
			overflow_count += 1
	print("%s- %s (%s): pos=(%.1f, %.1f) size=(%.1f, %.1f) min=(%.1f, %.1f)%s" % [
		indent, c.name, c.get_class(), r.position.x, r.position.y, r.size.x, r.size.y, min_sz.x, min_sz.y, clip_warn
	])
	for child in c.get_children():
		if child is Control and child.visible:
			_dump_control(child, depth + 1, max_depth, inside_scroll or is_scroll)


func _run_audit() -> void:
	var gs := root.get_node_or_null("GameState")
	var bc := root.get_node_or_null("BackendClient")

	var main_scene: PackedScene = load("res://scenes/Main.tscn")
	var main_inst: Control = main_scene.instantiate()
	root.add_child(main_inst)
	main_inst.set_deferred("size", Vector2(1080, 1920))
	await process_frame
	await process_frame

	for scr in ["login", "home_starter_modal", "home_normal", "home_lobby_modal", "packs", "collection", "battle"]:
		if scr == "login":
			main_inst._switch_screen("login")
		elif scr == "home_starter_modal":
			gs.grant_first_login_starter_15_cards()
			gs.just_granted_starter_15 = true
			bc.current_user["isGoogleLinked"] = true
			bc.current_user["email"] = "dokhacchung98@gmail.com"
			bc.current_user["displayName"] = "Đại Pháp Sư Lam Long"
			main_inst._switch_screen("home")
		elif scr == "home_normal":
			gs.just_granted_starter_15 = false
			main_inst.current_screen_node.refresh_ui()
		elif scr == "home_lobby_modal":
			main_inst.current_screen_node.lobby_overlay.visible = true
		else:
			main_inst._switch_screen(scr)

		await process_frame
		await process_frame
		await process_frame
		print("\n==================================================")
		print("SCREEN: ", scr)
		print("==================================================")
		_dump_control(main_inst.current_screen_node, 0, 4, false)

	print("\nTOTAL OVERFLOW ERRORS ACROSS ALL SCREENS: ", overflow_count)
	assert(overflow_count == 0, "UI overflow detected!")
	quit(0)
