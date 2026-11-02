extends Node2D
class_name StickerHeroWithWeapon

## Tướng Stickman 4 Màu Đội (team_blue, team_red, team_green, team_amber) + Hệ Thống Vũ Khí Theo Thẻ Bài
## Hỗ trợ 2 vị trí cầm trên mỗi vũ khí (Grip 1 & Grip 2) và cầm nhiều vũ khí (Weapon_Front & Weapon_Back)

@export_enum("team_blue", "team_red", "team_green", "team_amber") var team_color: String = "team_blue":
	set(value):
		team_color = value
		_apply_team_textures()

@export var use_secondary_grip: bool = false:
	set(value):
		use_secondary_grip = value
		_apply_weapon_grip()

@export var dual_wield_enabled: bool = false:
	set(value):
		dual_wield_enabled = value
		if has_node("Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Hand_R/Weapon_Back/Sprite"):
			$Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Hand_R/Weapon_Back/Sprite.visible = dual_wield_enabled

@onready var anim_player: AnimationPlayer = $AnimationPlayer

func _ready() -> void:
	_apply_team_textures()
	_apply_weapon_grip()
	play_action("idle")

func play_action(action_name: String) -> void:
	if anim_player and anim_player.has_animation(action_name):
		anim_player.play(action_name)

func _apply_team_textures() -> void:
	if not is_inside_tree():
		return
	var bone_parts := {
		"Skeleton2D/Hip/Sprite": "hip_kilt",
		"Skeleton2D/Hip/Chest/Sprite": "chest",
		"Skeleton2D/Hip/Chest/Neck/Sprite": "neck",
		"Skeleton2D/Hip/Chest/Neck/Head/Sprite": "head",
		"Skeleton2D/Hip/Chest/UpperArm_L/Sprite": "arm_upper_front",
		"Skeleton2D/Hip/Chest/UpperArm_L/Forearm_L/Sprite": "arm_lower_front",
		"Skeleton2D/Hip/Chest/UpperArm_L/Forearm_L/Hand_L/Sprite": "hand_front",
		"Skeleton2D/Hip/Chest/UpperArm_R/Sprite": "arm_upper_back",
		"Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Sprite": "arm_lower_back",
		"Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Hand_R/Sprite": "hand_back",
		"Skeleton2D/Hip/Thigh_R/Sprite": "leg_thigh_front",
		"Skeleton2D/Hip/Thigh_R/Shin_R/Sprite": "leg_shin_front",
		"Skeleton2D/Hip/Thigh_R/Shin_R/Foot_R/Sprite": "foot_front",
		"Skeleton2D/Hip/Thigh_L/Sprite": "leg_thigh_back",
		"Skeleton2D/Hip/Thigh_L/Shin_L/Sprite": "leg_shin_back",
		"Skeleton2D/Hip/Thigh_L/Shin_L/Foot_L/Sprite": "foot_back",
	}
	for np in bone_parts.keys():
		if has_node(np):
			var tex_path := "res://assets/sticker_hero/godot/parts/%s/%s.png" % [team_color, bone_parts[np]]
			if ResourceLoader.exists(tex_path):
				get_node(np).texture = load(tex_path)

func _apply_weapon_grip() -> void:
	if not has_node("Skeleton2D/Hip/Chest/UpperArm_L/Forearm_L/Hand_L/Weapon_Front"):
		return
	var wf: Bone2D = $Skeleton2D/Hip/Chest/UpperArm_L/Forearm_L/Hand_L/Weapon_Front
	var sp: Sprite2D = wf.get_node("Sprite")
	var g: Vector2 = wf.get_meta("grip2", Vector2(30, 24)) if use_secondary_grip else wf.get_meta("grip1", Vector2(58, 38))
	if sp and sp.texture:
		sp.offset = Vector2(sp.texture.get_width() / 2.0 - g.x, sp.texture.get_height() / 2.0 - g.y)
