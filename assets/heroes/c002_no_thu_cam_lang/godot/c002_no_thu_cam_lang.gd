extends Node2D
class_name HeroC002NoThuCamLang

## Tướng 002 (C02): Nỏ Thủ Câm Lặng — Cấp độ hiếm N (Common)
## Hệ Vật Lý / Tầm Xa (Xạ Thủ Nỏ) — 18 Bone2D Cutout Rig
## Stats chuẩn GAME_DESIGN.md: HP 200 | Mana 50 | Dame 34 | ASPD 1.25/s | Range 4.8 (Xa) | Giáp 15 | K.Phép 15 | MSPD 110
## Kỹ năng [50 Mana]: Tiễn Xuyên Tâm — Bắn mũi tên thép lớn xuyên 2 mục tiêu thẳng hàng, gây 95 sát thương vật lý.

const HERO_ID: String = "c002_no_thu_cam_lang"
const RARITY: String = "N"
const MAX_HP: int = 200
const MAX_MANA: int = 50
const BASE_DAMAGE: int = 34
const ATTACK_SPEED: float = 1.25
const ATTACK_RANGE: float = 4.8
const ARMOR: int = 15
const MAGIC_RESIST: int = 15
const MOVE_SPEED: int = 110

@onready var anim_player: AnimationPlayer = $AnimationPlayer
@onready var skeleton: Skeleton2D = $Skeleton2D

func _ready() -> void:
	play_action("idle")

func play_action(action_name: String) -> void:
	if anim_player and anim_player.has_animation(action_name):
		anim_player.play(action_name)
