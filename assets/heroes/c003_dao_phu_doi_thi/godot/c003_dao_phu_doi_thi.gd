extends Node2D
class_name HeroC003DaoPhuDoiThi

## Tướng 003 (C03): Đao Phủ Đồi Thi — Cấp độ hiếm N (Common)
## Hệ Vật Lý / Đấu Sĩ Cận Chiến (MeleeAoE) — 18 Bone2D Cutout Rig (Cầm Đại Đao Tay Front)
## Stats chuẩn GAME_DESIGN.md: HP 280 | Mana 65 | Khiên 20 | Dame 33 | ASPD 1.05/s | Range 1.3 (Gần) | Giáp 28 | K.Phép 18 | MSPD 120
## Kỹ năng [65 Mana]: Xoáy Trảm — Vung đại đao xoay tròn gây 115% Dame vật lý lên toàn bộ kẻ địch đứng xung quanh.

const HERO_ID: String = "c003_dao_phu_doi_thi"
const RARITY: String = "N"
const MAX_HP: int = 280
const MAX_MANA: int = 65
const INITIAL_SHIELD: int = 20
const BASE_DAMAGE: int = 33
const ATTACK_SPEED: float = 1.05
const ATTACK_RANGE: float = 1.3
const ARMOR: int = 28
const MAGIC_RESIST: int = 18
const MOVE_SPEED: int = 120

@onready var anim_player: AnimationPlayer = $AnimationPlayer
@onready var skeleton: Skeleton2D = $Skeleton2D

func _ready() -> void:
	play_action("idle")

func play_action(action_name: String) -> void:
	if anim_player and anim_player.has_animation(action_name):
		anim_player.play(action_name)
