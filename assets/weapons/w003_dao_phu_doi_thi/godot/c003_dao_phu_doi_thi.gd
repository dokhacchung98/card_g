extends Node2D

@export var dual_weapon_enabled: bool = false:
	set(value):
		dual_weapon_enabled = value
		if has_node("Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Hand_R/Weapon_Back"):
			$Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Hand_R/Weapon_Back.visible = value

@export var weapon_aura_enabled: bool = true:
	set(value):
		weapon_aura_enabled = value
		if has_node("Skeleton2D/Hip/Chest/UpperArm_L/Forearm_L/Hand_L/Weapon_Front/WeaponAura"):
			$Skeleton2D/Hip/Chest/UpperArm_L/Forearm_L/Hand_L/Weapon_Front/WeaponAura.visible = value

@onready var anim_player: AnimationPlayer = $AnimationPlayer
@onready var skeleton: Skeleton2D = $Skeleton2D
@onready var weapon_front: Bone2D = $Skeleton2D/Hip/Chest/UpperArm_L/Forearm_L/Hand_L/Weapon_Front
@onready var weapon_back: Bone2D = $Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Hand_R/Weapon_Back
@onready var weapon_aura: AnimatedSprite2D = $Skeleton2D/Hip/Chest/UpperArm_L/Forearm_L/Hand_L/Weapon_Front/WeaponAura

var current_team: String = "team_blue"

func _ready() -> void:
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
