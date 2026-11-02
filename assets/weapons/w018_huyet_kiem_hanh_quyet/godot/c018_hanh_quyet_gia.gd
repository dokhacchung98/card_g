extends Node2D
class_name C018HanhQuyetGia

@export_enum("team_blue", "team_red", "team_green", "team_amber") var team_color: String = "team_blue":
	set(value):
		team_color = value
		if is_node_ready():
			apply_team_color(team_color)

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

func _ready() -> void:
	apply_team_color(team_color)
	play_action("idle")

func apply_team_color(t_name: String) -> void:
	var stickman_nodes := {
		"Hip": "hip_kilt",
		"Hip/Thigh_L": "leg_thigh_back",
		"Hip/Thigh_L/Shin_L": "leg_shin_back",
		"Hip/Thigh_L/Shin_L/Foot_L": "foot_back",
		"Hip/Thigh_R": "leg_thigh_front",
		"Hip/Thigh_R/Shin_R": "leg_shin_front",
		"Hip/Thigh_R/Shin_R/Foot_R": "foot_front",
		"Hip/Chest": "chest",
		"Hip/Chest/Neck": "neck",
		"Hip/Chest/Neck/Head": "head",
		"Hip/Chest/UpperArm_R": "arm_upper_back",
		"Hip/Chest/UpperArm_R/Forearm_R": "arm_lower_back",
		"Hip/Chest/UpperArm_R/Forearm_R/Hand_R": "hand_back",
		"Hip/Chest/UpperArm_L": "arm_upper_front",
		"Hip/Chest/UpperArm_L/Forearm_L": "arm_lower_front",
		"Hip/Chest/UpperArm_L/Forearm_L/Hand_L": "hand_front",
	}
	for rel_path in stickman_nodes.keys():
		var spr := get_node_or_null("Skeleton2D/" + rel_path + "/Sprite") as Sprite2D
		if spr:
			var p_file: String = stickman_nodes[rel_path]
			spr.texture = load("res://assets/sticker_hero/godot/parts/%s/%s.png" % [t_name, p_file])

func play_action(action_name: String) -> void:
	if anim_player and anim_player.has_animation(action_name):
		anim_player.play(action_name)
