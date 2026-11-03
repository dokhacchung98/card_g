extends Control
class_name MainController

const LoginScreenScript := preload("res://scripts/screens/LoginScreen.gd")
const HomeScreenScript := preload("res://scripts/screens/HomeScreen.gd")
const PackScreenScript := preload("res://scripts/screens/PackScreen.gd")
const CollectionScreenScript := preload("res://scripts/screens/CollectionScreen.gd")
const BattleScreenScript := preload("res://scripts/screens/BattleScreen.gd")
const CardDetailModalScript := preload("res://scripts/components/CardDetailModal.gd")
const GuideModalScript := preload("res://scripts/components/GuideModal.gd")

var screen_host: Control
var current_screen_name: String = ""
var current_screen_node: Control = null
var detail_modal: Control = null
var guide_modal: Control = null


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	theme = GameState.get_ui_theme()
	_build_root_layout()
	GameState.screen_requested.connect(_on_screen_requested)
	GameState.card_inspect_requested.connect(_on_card_inspect_requested)
	GameState.guide_requested.connect(_on_guide_requested)
	if BackendClient.is_logged_in():
		_switch_screen("home")
	else:
		_switch_screen("login")


func _build_root_layout() -> void:
	# Full 1080x1920 Portrait Viewport (No bottom tab bar — Home screen is the navigation hub)
	screen_host = Control.new()
	screen_host.position = Vector2.ZERO
	screen_host.size = Vector2(1080, 1920)
	screen_host.clip_contents = true
	add_child(screen_host)

	# Global Card Detail Modal Overlay (1080x1920)
	detail_modal = CardDetailModalScript.new()
	add_child(detail_modal)
	detail_modal.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)

	# Global Tutorial & Guide Modal Overlay (1080x1920)
	guide_modal = GuideModalScript.new()
	add_child(guide_modal)
	guide_modal.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)


func _on_screen_requested(screen_name: String) -> void:
	_switch_screen(screen_name)


func _on_card_inspect_requested(card_id: String, elem_override: String) -> void:
	if detail_modal != null and is_instance_valid(detail_modal):
		detail_modal.show_card(card_id, elem_override)


func _on_guide_requested(initial_tab: int = 0) -> void:
	if guide_modal != null and is_instance_valid(guide_modal):
		guide_modal.show_guide(initial_tab)


func _switch_screen(screen_name: String) -> void:
	if current_screen_node != null and is_instance_valid(current_screen_node):
		current_screen_node.queue_free()
		current_screen_node = null

	current_screen_name = screen_name
	match screen_name:
		"login":
			current_screen_node = LoginScreenScript.new()
		"packs":
			current_screen_node = PackScreenScript.new()
		"collection":
			current_screen_node = CollectionScreenScript.new()
		"battle":
			current_screen_node = BattleScreenScript.new()
		_:
			current_screen_name = "home"
			current_screen_node = HomeScreenScript.new()

	screen_host.add_child(current_screen_node)
	current_screen_node.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
