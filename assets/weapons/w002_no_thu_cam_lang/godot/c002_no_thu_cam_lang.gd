extends Node2D
class_name C002_NoThuCamLang

@export_enum("team_blue", "team_red", "team_green", "team_amber") var team_color: String = "team_blue":
	set(value):
		team_color = value
		if is_node_ready():
			apply_team_color(value)

@export_range(1, 2) var active_grip_slot: int = 1:
	set(value):
		active_grip_slot = value
		if is_node_ready():
			apply_weapon_grip(value)

@export var dual_wield_enabled: bool = false:
	set(value):
		dual_wield_enabled = value
		if is_node_ready() and has_node("Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Hand_R/Weapon_Back/Sprite"):
			$"Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Hand_R/Weapon_Back/Sprite".visible = value

const STICKER_BONE_PARTS := {
	"Skeleton2D/Hip/Sprite": "hip_kilt",
	"Skeleton2D/Hip/Thigh_L/Sprite": "leg_thigh_back",
	"Skeleton2D/Hip/Thigh_L/Shin_L/Sprite": "leg_shin_back",
	"Skeleton2D/Hip/Thigh_L/Shin_L/Foot_L/Sprite": "foot_back",
	"Skeleton2D/Hip/Thigh_R/Sprite": "leg_thigh_front",
	"Skeleton2D/Hip/Thigh_R/Shin_R/Sprite": "leg_shin_front",
	"Skeleton2D/Hip/Thigh_R/Shin_R/Foot_R/Sprite": "foot_front",
	"Skeleton2D/Hip/Chest/Sprite": "chest",
	"Skeleton2D/Hip/Chest/Neck/Sprite": "neck",
	"Skeleton2D/Hip/Chest/Neck/Head/Sprite": "head",
	"Skeleton2D/Hip/Chest/UpperArm_R/Sprite": "arm_upper_back",
	"Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Sprite": "arm_lower_back",
	"Skeleton2D/Hip/Chest/UpperArm_R/Forearm_R/Hand_R/Sprite": "hand_back",
	"Skeleton2D/Hip/Chest/UpperArm_L/Sprite": "arm_upper_front",
	"Skeleton2D/Hip/Chest/UpperArm_L/Forearm_L/Sprite": "arm_lower_front",
	"Skeleton2D/Hip/Chest/UpperArm_L/Forearm_L/Hand_L/Sprite": "hand_front",
}

func _ready() -> void:
	apply_team_color(team_color)
	apply_weapon_grip(active_grip_slot)
	dual_wield_enabled = dual_wield_enabled

func apply_team_color(t_color: String) -> void:
	for node_path in STICKER_BONE_PARTS.keys():
		if has_node(node_path):
			var spr: Sprite2D = get_node(node_path)
			var part_name: String = STICKER_BONE_PARTS[node_path]
			var tex_path := "res://assets/sticker_hero/godot/parts/%s/%s.png" % [t_color, part_name]
			if ResourceLoader.exists(tex_path):
				spr.texture = load(tex_path)

func apply_weapon_grip(slot: int) -> void:
	var w_bone_path := "Skeleton2D/Hip/Chest/UpperArm_L/Forearm_L/Hand_L/Weapon_Front"
	if not has_node(w_bone_path):
		return
	var w_bone: Bone2D = get_node(w_bone_path)
	var w_spr: Sprite2D = w_bone.get_node("Sprite")
	var grip: Vector2 = w_bone.get_meta("grip1") if slot == 1 else w_bone.get_meta("grip2")
	if w_spr.texture:
		var sz := w_spr.texture.get_size()
		w_spr.offset = Vector2(sz.x / 2.0 - grip.x, sz.y / 2.0 - grip.y)
