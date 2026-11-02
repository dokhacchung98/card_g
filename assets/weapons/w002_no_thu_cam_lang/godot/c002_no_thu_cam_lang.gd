extends Node2D

@onready var anim_player: AnimationPlayer = $AnimationPlayer
@onready var skeleton: Skeleton2D = $Skeleton2D
@onready var weapon_front: Bone2D = $Skeleton2D/Hip/Chest/UpperArm_L/Forearm_L/Hand_L/Weapon_Front
@onready var weapon_back: Bone2D = $Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Hand_R/Weapon_Back

var current_team: String = "team_blue"

func _ready() -> void:
	play_action("idle")

func play_action(action_name: String) -> void:
	if anim_player.has_animation(action_name):
		anim_player.play(action_name)

func set_team_color(team_key: String) -> void:
	current_team = team_key
	var base_path := "res://assets/sticker_hero/godot/parts/" + team_key + "/"
	for bone in skeleton.get_children():
		_update_bone_textures_recursive(bone, base_path)

func _update_bone_textures_recursive(node: Node, base_path: String) -> void:
	if node is Bone2D and not node.name.begins_with("Weapon"):
		var sprite := node.get_node_or_null("Sprite") as Sprite2D
		if sprite:
			var part_name: String = node.name.to_snake_case()
			var tex_path := base_path + part_name + ".png"
			if ResourceLoader.exists(tex_path):
				sprite.texture = load(tex_path)
	for child in node.get_children():
		_update_bone_textures_recursive(child, base_path)

func toggle_dual_wield(enabled: bool) -> void:
	if weapon_back:
		var sp := weapon_back.get_node_or_null("Sprite") as Sprite2D
		if sp:
			sp.visible = enabled
