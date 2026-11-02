extends Node2D
class_name C003_DaoPhuDoiThi

@export_enum("team_blue", "team_red", "team_green", "team_amber") var current_team: String = "team_blue":
	set(val):
		current_team = val
		if is_inside_tree():
			set_team(val)

@export var dual_weapon_enabled: bool = false:
	set(val):
		dual_weapon_enabled = val
		if is_inside_tree() and has_node("Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Hand_R/Weapon_Back"):
			$Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Hand_R/Weapon_Back.visible = val

@export var weapon_aura_enabled: bool = true

@onready var anim_player: AnimationPlayer = $AnimationPlayer
@onready var skeleton: Skeleton2D = $Skeleton2D

func _ready() -> void:
	set_team(current_team)
	if has_node("Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Hand_R/Weapon_Back"):
		$Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Hand_R/Weapon_Back.visible = dual_weapon_enabled
	play_action("idle")

func set_team(team_name: String) -> void:
	current_team = team_name
	var base_path := "res://assets/sticker_hero/godot/parts/" + team_name + "/"
	for bone in skeleton.get_children():
		_update_bone_texture(bone, base_path)

func _update_bone_texture(node: Node, base_path: String) -> void:
	if node is Bone2D and not node.name.begins_with("Weapon"):
		var sp := node.get_node_or_null("Sprite") as Sprite2D
		if sp:
			var part_name: String = node.name.to_lower()
			var tex_path := base_path + part_name + ".png"
			if ResourceLoader.exists(tex_path):
				sp.texture = load(tex_path)
	for child in node.get_children():
		_update_bone_texture(child, base_path)

func play_action(action_name: String) -> void:
	if anim_player and anim_player.has_animation(action_name):
		anim_player.play(action_name)

func toggle_dual_weapons(enabled: bool) -> void:
	dual_weapon_enabled = enabled

func toggle_weapon_aura(enabled: bool) -> void:
	weapon_aura_enabled = enabled
