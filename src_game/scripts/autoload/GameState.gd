extends Node

signal state_changed
signal screen_requested(screen_name: String)
signal card_inspect_requested(card_id: String, element_override: String)
signal guide_requested(initial_tab: int)

const SAVE_PATH := "user://arcana_five_save_v3_auth_15cards.json"
const TOTAL_COLLECTION_CARDS := 500        # 100 base card templates x 5 Wuxing elements = 500 distinct cards

# 15 Default Starter Cards gifted on first Google Login when the player has 0 cards:
# 3 Physical Offense + 3 Magic Offense + 3 Tanker + 3 Support + 3 Items (3 of each Wuxing Element!)
const DEFAULT_STARTER_15_UIDS := [
	"C001_kim", "C002_moc", "C003_thuy",
	"C021_hoa", "C022_tho", "C024_kim",
	"C041_moc", "C042_thuy", "C047_hoa",
	"C061_tho", "C063_kim", "C066_moc",
	"C081_thuy", "C082_hoa", "C085_tho",
]

var just_granted_starter_15: bool = false

const ELEMENTS := ["kim", "moc", "thuy", "hoa", "tho"]

const ELEMENT_META := {
	"kim": {
		"id": "kim",
		"name": "Hệ Kim",
		"short": "Kim",
		"color": Color(0.92, 0.84, 0.55),
		"icon": "res://assets/cards/icons/elements/kim/prop.png",
		"vfx_dir": "res://assets/vfx_elements/kim_metal",
		"modifier_desc": "+35% sát thương lên Khiên & xuyên 15% Giáp",
	},
	"moc": {
		"id": "moc",
		"name": "Hệ Mộc",
		"short": "Mộc",
		"color": Color(0.28, 0.85, 0.45),
		"icon": "res://assets/cards/icons/elements/moc/prop.png",
		"vfx_dir": "res://assets/vfx_elements/moc_wood",
		"modifier_desc": "Hút 10% máu (hoặc +15% hồi máu) & gây độc nhẹ",
	},
	"thuy": {
		"id": "thuy",
		"name": "Hệ Thủy",
		"short": "Thủy",
		"color": Color(0.32, 0.75, 0.98),
		"icon": "res://assets/cards/icons/elements/thuy/prop.png",
		"vfx_dir": "res://assets/vfx_elements/thuy_water",
		"modifier_desc": "+15% Mana mỗi đòn đánh & Skill làm chậm 15%",
	},
	"hoa": {
		"id": "hoa",
		"name": "Hệ Hỏa",
		"short": "Hỏa",
		"color": Color(0.98, 0.38, 0.24),
		"icon": "res://assets/cards/icons/elements/hoa/prop.png",
		"vfx_dir": "res://assets/vfx_elements/hoa_fire",
		"modifier_desc": "+12% Dame gốc & Skill gây Thiêu đốt 3% HP/s",
	},
	"tho": {
		"id": "tho",
		"name": "Hệ Thổ",
		"short": "Thổ",
		"color": Color(0.82, 0.62, 0.36),
		"icon": "res://assets/cards/icons/elements/tho/prop.png",
		"vfx_dir": "res://assets/vfx_elements/tho_earth",
		"modifier_desc": "Nhận Khiên = 10% HP khi xuất trận & +12% Giáp/K.Phép",
	},
}

# Tương Sinh: Kim -> Thủy -> Mộc -> Hỏa -> Thổ -> Kim
const GEN_NEXT := {
	"kim": "thuy",
	"thuy": "moc",
	"moc": "hoa",
	"hoa": "tho",
	"tho": "kim",
}

# Tương Khắc: Kim -> Mộc -> Thổ -> Thủy -> Hỏa -> Kim
const COUNTER_TARGET := {
	"kim": "moc",
	"moc": "tho",
	"tho": "thuy",
	"thuy": "hoa",
	"hoa": "kim",
}

const RARITY_ORDER := {"N": 1, "R": 2, "S": 3, "SSR": 4}
const RARITY_COLOR := {
	"N": Color(0.75, 0.79, 0.84),
	"R": Color(0.28, 0.65, 0.98),
	"S": Color(0.76, 0.42, 0.98),
	"SSR": Color(0.98, 0.75, 0.18),
}

const ROLE_META := {
	"atk_phys": {
		"label": "Tấn Công Vật Lý",
		"short": "Vật Lý",
		"icon": "res://assets/cards/icons/types/atk-phys/prop.png",
		"color": Color(0.95, 0.42, 0.38),
	},
	"atk_mag": {
		"label": "Tấn Công Ma Pháp",
		"short": "Ma Pháp",
		"icon": "res://assets/cards/icons/types/atk-mag/prop.png",
		"color": Color(0.68, 0.46, 0.98),
	},
	"tanker": {
		"label": "Tanker Đỡ Đòn",
		"short": "Tanker",
		"icon": "res://assets/cards/icons/types/tanker/prop.png",
		"color": Color(0.35, 0.76, 0.96),
	},
	"support": {
		"label": "Hỗ Trợ Support",
		"short": "Hỗ Trợ",
		"icon": "res://assets/cards/icons/types/support/prop.png",
		"color": Color(0.32, 0.88, 0.56),
	},
	"item": {
		"label": "Vật Phẩm Tức Thì",
		"short": "Vật Phẩm",
		"icon": "res://assets/cards/icons/types/item/prop.png",
		"color": Color(0.96, 0.76, 0.28),
	},
}

const PACK_TYPES := {
	1: {
		"id": 1,
		"name": "Pack #1 · Rương Thiết Ấn (Phổ Thông)",
		"short_name": "PACK #1",
		"sub": "Phổ Thông",
		"currency": "coin",
		"price": 200,
		"currency_label": "Coin",
		"currency_icon": "res://assets/ui_hud/icons/icon_coin_gold.png",
		"rates": {"N": 94.0, "R": 5.5, "S": 0.5, "SSR": 0.0},
		"rate_text": "N: 94.0%  |  R: 5.5%  |  S: 0.5%  |  SSR: 0%",
		"desc": "Mua bằng Coin (200 Coin/Pack) — Cố định 10 thẻ/pack (mỗi thẻ tự sinh 1 hệ Ngũ Hành cố định).",
		"color": Color(0.74, 0.78, 0.84),
		"tint": Color(0.86, 0.90, 0.96),
	},
	2: {
		"id": 2,
		"name": "Pack #2 · Rương Thanh Đồng (Tinh Nhuệ)",
		"short_name": "PACK #2",
		"sub": "Tinh Nhuệ",
		"currency": "coin",
		"price": 500,
		"currency_label": "Coin",
		"currency_icon": "res://assets/ui_hud/icons/icon_coin_gold.png",
		"rates": {"N": 47.9, "R": 47.0, "S": 5.0, "SSR": 0.1},
		"rate_text": "N: 47.9%  |  R: 47.0%  |  S: 5.0%  |  SSR: 0.1%",
		"desc": "Mua bằng Coin (500 Coin/Pack) — Cố định 10 thẻ/pack, tỷ lệ N & R ngang nhau (~47.5%), S 5% & SSR 0.1%.",
		"color": Color(0.32, 0.86, 0.72),
		"tint": Color(0.68, 0.98, 0.88),
	},
	3: {
		"id": 3,
		"name": "Pack #3 · Rương Bạch Ngân (Cao Cấp)",
		"short_name": "PACK #3",
		"sub": "Cao Cấp",
		"currency": "coin",
		"price": 1000,
		"currency_label": "Coin",
		"currency_icon": "res://assets/ui_hud/icons/icon_coin_gold.png",
		"rates": {"N": 30.0, "R": 60.0, "S": 9.0, "SSR": 1.0},
		"rate_text": "N: 30.0%  |  R: 60.0%  |  S: 9.0%  |  SSR: 1.0%",
		"desc": "Mua bằng Coin (1000 Coin/Pack) — Pack cao nhất mua được bằng Coin! Chủ lực thẻ R (60%), S 9% & SSR 1%.",
		"color": Color(0.32, 0.68, 0.98),
		"tint": Color(0.68, 0.86, 1.0),
	},
	4: {
		"id": 4,
		"name": "Pack #4 · Rương Hoàng Kim (Sử Thi)",
		"short_name": "PACK #4",
		"sub": "Sử Thi",
		"currency": "diamond",
		"price": 150,
		"currency_label": "Kim Cương",
		"currency_icon": "res://assets/ui_hud/icons/icon_diamond_gem.png",
		"rates": {"N": 20.0, "R": 50.0, "S": 25.0, "SSR": 5.0},
		"rate_text": "N: 20.0%  |  R: 50.0%  |  S: 25.0%  |  SSR: 5.0%",
		"desc": "Chỉ mua bằng Kim Cương (150 Kim Cương/Pack) — Tỷ lệ đột phá: 20% N, 50% R, 25% S và 5% Huyền Thoại SSR.",
		"color": Color(0.78, 0.44, 0.98),
		"tint": Color(0.92, 0.72, 1.0),
	},
	5: {
		"id": 5,
		"name": "Pack #5 · Rương Thần Thoại (Chí Tôn)",
		"short_name": "PACK #5",
		"sub": "Chí Tôn",
		"currency": "diamond",
		"price": 300,
		"currency_label": "Kim Cương",
		"currency_icon": "res://assets/ui_hud/icons/icon_diamond_gem.png",
		"rates": {"N": 10.0, "R": 40.0, "S": 40.0, "SSR": 10.0},
		"rate_text": "N: 10.0%  |  R: 40.0%  |  S: 40.0%  |  SSR: 10.0%",
		"desc": "Chỉ mua bằng Kim Cương (300 Kim Cương/Pack) — Đỉnh cao Gacha: 10% N, 40% R, 40% S và 10% Huyền Thoại SSR!",
		"color": Color(0.98, 0.76, 0.18),
		"tint": Color(1.0, 0.90, 0.55),
	},
}

var base_cards_db: Array = []              # 100 base card templates (C001..C100)
var base_cards_by_id: Dictionary = {}      # "C001" -> base card Dictionary
var cards_db: Array = []                   # 500 distinct cards (100 base templates x 5 elements)
var cards_by_uid: Dictionary = {}          # "C001_kim" -> 500-card Dictionary
var cards_by_id: Dictionary = {}           # Supports both "C001_kim" and "C001" lookups

# Player persistent state (500-card collection: each card's element is fixed when pulled from a pack!)
var owned_counts: Dictionary = {}          # "C001_kim" -> int (copies owned of that exact elemental card, 0 if unowned)
var card_elements: Dictionary = {}         # "C001_kim" -> "kim" (also maps base "C001" -> first owned element for legacy callers)
var unlocked_elements: Dictionary = {}     # "C001" -> Array[String] of elements owned for that base template
var loadout_deck: Array = []               # Array of 15 unique variant UIDs (e.g. "C001_kim", "C018_hoa")
var pack_counts_by_type: Dictionary = {1: 4, 2: 3, 3: 2, 4: 2, 5: 1}
var selected_pack_type: int = 3
var pack_count: int = 12
var gold: int = 3500                       # Coin (Mua được Pack #1, #2, #3)
var diamonds: int = 600                    # Kim Cương (Chỉ mua được 2 Pack cuối: Pack #4 & Pack #5)

# Match configuration
var selected_player_count: int = 4         # 2, 3, or 4 players
var player_is_bot: bool = false            # Human player always plays manually (no auto-bot for player)
var match_speed: float = 1.0

# Texture, Font & JSON caches
var _tex_cache: Dictionary = {}
var _style_cache: Dictionary = {}
var _weapon_cfg_cache: Dictionary = {}
var _base_text_font: Font = null
var _lilita_full_font: FontFile = null
var _lilita_num_only_font: FontFile = null
var _ui_theme: Theme = null


func _ready() -> void:
	randomize()
	_init_fonts()
	if _ui_theme and get_tree() and get_tree().root:
		get_tree().root.theme = _ui_theme
	_load_cards_database()
	_load_or_init_save()


func _load_font_from_res(res_path: String) -> FontFile:
	if FileAccess.file_exists(res_path):
		var bytes := FileAccess.get_file_as_bytes(res_path)
		if not bytes.is_empty():
			var ff := FontFile.new()
			ff.data = bytes
			return ff
	var abs_p := ProjectSettings.globalize_path(res_path)
	if FileAccess.file_exists(abs_p):
		var ff2 := FontFile.new()
		if ff2.load_dynamic_font(abs_p) == OK:
			return ff2
	if ResourceLoader.exists(res_path):
		var loaded = load(res_path)
		if loaded is FontFile:
			return loaded.duplicate()
	return null


func _init_fonts() -> void:
	if _lilita_num_only_font != null and _lilita_full_font != null:
		return
	var fallback_sys := ThemeDB.fallback_font
	_base_text_font = fallback_sys
	var bf := _load_font_from_res("res://assets/fonts/BalooThambi2-Bold.ttf")
	if bf != null:
		if fallback_sys:
			bf.fallbacks = [fallback_sys]
		_base_text_font = bf

	var ff := _load_font_from_res("res://assets/fonts/LilitaOne-Regular.ttf")
	if ff != null:
		if _base_text_font:
			ff.fallbacks = [_base_text_font]
		_lilita_full_font = ff

	var nf := _load_font_from_res("res://assets/fonts/LilitaOne-NumbersOnly.ttf")
	if nf != null:
		if _base_text_font:
			nf.fallbacks = [_base_text_font]
		_lilita_num_only_font = nf
		_ui_theme = Theme.new()
		_ui_theme.default_font = _lilita_num_only_font
		_ui_theme.default_font_size = 24
		for ctrl_type in ["Label", "Button", "OptionButton", "PopupMenu", "LineEdit", "RichTextLabel"]:
			_ui_theme.set_font_size("font_size", ctrl_type, 24)
			_ui_theme.set_color("font_outline_color", ctrl_type, Color(0.01, 0.01, 0.03, 0.96))
			_ui_theme.set_constant("outline_size", ctrl_type, 4)
		_ui_theme.set_constant("v_separation", "PopupMenu", 14)


func get_ui_theme() -> Theme:
	if _ui_theme == null:
		_init_fonts()
	return _ui_theme


func get_font() -> Font:
	if _lilita_num_only_font == null:
		_init_fonts()
	return _lilita_num_only_font if _lilita_num_only_font != null else ThemeDB.fallback_font


func get_num_font() -> Font:
	if _lilita_full_font == null:
		_init_fonts()
	return _lilita_full_font if _lilita_full_font != null else get_font()


func make_variant_id(card_id_or_uid: String, elem: String = "") -> String:
	if card_id_or_uid.contains("_"):
		return card_id_or_uid
	var resolved_elem := elem if not elem.is_empty() else get_card_element(card_id_or_uid)
	return "%s_%s" % [card_id_or_uid, resolved_elem]


func get_base_card_id(card_id_or_uid: String) -> String:
	if card_id_or_uid.contains("_"):
		return card_id_or_uid.split("_")[0]
	return card_id_or_uid


func _load_cards_database() -> void:
	var res_db_path := "res://data/cards_db.json"
	var txt := ""
	if FileAccess.file_exists(res_db_path):
		txt = FileAccess.get_file_as_string(res_db_path)
	else:
		var db_path := ProjectSettings.globalize_path(res_db_path)
		if FileAccess.file_exists(db_path):
			txt = FileAccess.get_file_as_string(db_path)
	if txt.is_empty():
		push_error("Missing cards_db.json at " + res_db_path)
		return
	var parsed = JSON.parse_string(txt)
	if typeof(parsed) == TYPE_ARRAY:
		base_cards_db = parsed
		base_cards_by_id.clear()
		cards_db.clear()
		cards_by_uid.clear()
		cards_by_id.clear()
		owned_counts.clear()
		card_elements.clear()
		unlocked_elements.clear()

		var v_num := 1
		for c in base_cards_db:
			var base_id: String = str(c["id"])
			base_cards_by_id[base_id] = c
			cards_by_id[base_id] = c
			var default_idx: int = int(c["num"]) - 1
			var default_elem: String = ELEMENTS[default_idx % ELEMENTS.size()]
			card_elements[base_id] = default_elem
			unlocked_elements[base_id] = []

			for el_i in range(ELEMENTS.size()):
				var el: String = ELEMENTS[el_i]
				var uid := "%s_%s" % [base_id, el]
				var v_card: Dictionary = c.duplicate(true)
				v_card["uid"] = uid
				v_card["id"] = base_id
				v_card["base_id"] = base_id
				v_card["element"] = el
				v_card["variant_num"] = v_num
				v_num += 1
				cards_db.append(v_card)
				cards_by_uid[uid] = v_card
				cards_by_id[uid] = v_card
				owned_counts[uid] = 0
				card_elements[uid] = el


func _load_or_init_save() -> void:
	if FileAccess.file_exists(SAVE_PATH):
		var txt := FileAccess.get_file_as_string(SAVE_PATH)
		var data = JSON.parse_string(txt)
		if typeof(data) == TYPE_DICTIONARY:
			var saved_counts: Dictionary = data.get("owned_counts", {})
			for k in saved_counts.keys():
				var ks := str(k)
				if owned_counts.has(ks):
					owned_counts[ks] = int(saved_counts[k])
			_rebuild_unlocked_elements_from_owned()

			var saved_deck: Array = data.get("loadout_deck", [])
			loadout_deck.clear()
			for entry in saved_deck:
				var uid := make_variant_id(str(entry))
				if cards_by_uid.has(uid) and int(owned_counts.get(uid, 0)) > 0 and not loadout_deck.has(uid):
					loadout_deck.append(uid)
			var saved_packs_by_type: Dictionary = data.get("pack_counts_by_type", {})
			if not saved_packs_by_type.is_empty():
				for p_t in range(1, 6):
					pack_counts_by_type[p_t] = int(saved_packs_by_type.get(str(p_t), saved_packs_by_type.get(p_t, 2)))
			sync_total_pack_count()
			selected_pack_type = clampi(int(data.get("selected_pack_type", 3)), 1, 5)
			gold = int(data.get("gold", 3500))
			diamonds = int(data.get("diamonds", 600))
			selected_player_count = clampi(int(data.get("selected_player_count", 4)), 2, 4)
			player_is_bot = false
			return

	# Brand-new unauthenticated state: Player starts with 0 cards until First Google Login!
	loadout_deck.clear()
	sync_total_pack_count()


# Called upon Google Login: If the player has 0 cards (first-time login),
# gifts the 15 Default Starter Cards as in design and equips them into the 15-card Loadout Deck!
func grant_first_login_starter_15_cards() -> bool:
	if get_owned_unique_count() > 0:
		if not is_loadout_valid(loadout_deck).ok:
			auto_build_valid_loadout()
		return false

	loadout_deck.clear()
	for uid in DEFAULT_STARTER_15_UIDS:
		if cards_by_uid.has(uid):
			owned_counts[uid] = 1
			var base_id := get_base_card_id(uid)
			var el := get_card_element(uid)
			card_elements[base_id] = el
			loadout_deck.append(uid)

	_rebuild_unlocked_elements_from_owned()
	just_granted_starter_15 = true
	save_game()
	return true


func apply_cloud_profile(user_dict: Dictionary, is_first_login_flag: bool = false) -> void:
	var was_empty := (get_owned_unique_count() == 0)
	var cloud_owned: Dictionary = user_dict.get("ownedCounts", {})
	for k in cloud_owned.keys():
		var uid_str := str(k)
		# Normalize case if needed (e.g. "c001_kim" -> "C001_kim")
		if not cards_by_uid.has(uid_str) and uid_str.begins_with("c"):
			uid_str = "C" + uid_str.substr(1)
		if cards_by_uid.has(uid_str):
			var cnt := int(cloud_owned[k])
			if cnt > 0:
				owned_counts[uid_str] = maxi(int(owned_counts.get(uid_str, 0)), cnt)

	_rebuild_unlocked_elements_from_owned()

	if get_owned_unique_count() == 0:
		grant_first_login_starter_15_cards()
		return

	if was_empty or is_first_login_flag:
		just_granted_starter_15 = true

	var cloud_deck: Array = user_dict.get("loadoutDeck", [])
	if cloud_deck.size() == 15 and loadout_deck.is_empty():
		for d_entry in cloud_deck:
			var d_uid := str(d_entry)
			if not cards_by_uid.has(d_uid) and d_uid.begins_with("c"):
				d_uid = "C" + d_uid.substr(1)
			if cards_by_uid.has(d_uid) and int(owned_counts.get(d_uid, 0)) > 0 and not loadout_deck.has(d_uid):
				loadout_deck.append(d_uid)

	if not is_loadout_valid(loadout_deck).ok:
		auto_build_valid_loadout()
	else:
		save_game()


func _rebuild_unlocked_elements_from_owned() -> void:
	for c in base_cards_db:
		var base_id: String = str(c["id"])
		var u_list: Array = []
		for el in ELEMENTS:
			var uid := "%s_%s" % [base_id, el]
			if int(owned_counts.get(uid, 0)) > 0:
				u_list.append(el)
		unlocked_elements[base_id] = u_list
		if not u_list.is_empty():
			card_elements[base_id] = str(u_list[0])


func sync_total_pack_count() -> void:
	var total := 0
	for p_t in range(1, 6):
		total += int(pack_counts_by_type.get(p_t, 0))
	pack_count = total


func get_pack_type_count(pack_type_id: int) -> int:
	return int(pack_counts_by_type.get(clampi(pack_type_id, 1, 5), 0))


func save_game() -> void:
	sync_total_pack_count()
	_rebuild_unlocked_elements_from_owned()
	var data := {
		"owned_counts": owned_counts,
		"loadout_deck": loadout_deck,
		"pack_counts_by_type": pack_counts_by_type,
		"selected_pack_type": selected_pack_type,
		"pack_count": pack_count,
		"gold": gold,
		"diamonds": diamonds,
		"selected_player_count": selected_player_count,
		"player_is_bot": player_is_bot,
	}
	var f := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(data, "\t"))
		f.close()
	emit_signal("state_changed")


func get_card(card_id_or_uid: String) -> Dictionary:
	if cards_by_id.has(card_id_or_uid):
		return cards_by_id[card_id_or_uid]
	var base_id := get_base_card_id(card_id_or_uid)
	return base_cards_by_id.get(base_id, {})


func get_card_element(card_id_or_uid: String) -> String:
	if card_id_or_uid.contains("_"):
		var parts := card_id_or_uid.split("_")
		if parts.size() >= 2:
			return parts[1]
	return card_elements.get(card_id_or_uid, "kim")


func get_card_owned_count(card_id_or_uid: String, elem: String = "") -> int:
	var uid := make_variant_id(card_id_or_uid, elem)
	return int(owned_counts.get(uid, 0))


func is_card_owned(card_id_or_uid: String, elem: String = "") -> bool:
	return get_card_owned_count(card_id_or_uid, elem) > 0


func is_card_in_loadout(card_id_or_uid: String, elem: String = "") -> bool:
	var uid := make_variant_id(card_id_or_uid, elem)
	return loadout_deck.has(uid)


func get_owned_unique_count() -> int:
	var cnt := 0
	for uid in owned_counts.keys():
		if int(owned_counts[uid]) > 0:
			cnt += 1
	return cnt


func get_owned_base_templates_count() -> int:
	var cnt := 0
	for base_id in unlocked_elements.keys():
		var arr: Array = unlocked_elements[base_id]
		if not arr.is_empty():
			cnt += 1
	return cnt


func get_total_owned_copies() -> int:
	var total := 0
	for uid in owned_counts.keys():
		total += int(owned_counts[uid])
	return total


# Checks whether elem_a counters elem_b (+25% damage, target deals -15%)
func does_element_counter(elem_a: String, elem_b: String) -> bool:
	return COUNTER_TARGET.get(elem_a, "") == elem_b


# Checks whether elem_a generates elem_b (Tương Sinh: +15% ATK & regen, +25% support/item boost)
func does_element_generate(elem_a: String, elem_b: String) -> bool:
	return GEN_NEXT.get(elem_a, "") == elem_b


# Returns the element that counters target_elem (e.g. target="moc" -> returns "kim")
func get_counter_element_against(target_elem: String) -> String:
	for k in COUNTER_TARGET.keys():
		if COUNTER_TARGET[k] == target_elem:
			return k
	return "kim"


# Validates 15-card Loadout Deck per GDD Section 4.2
func is_loadout_valid(deck: Array) -> Dictionary:
	var unique := {}
	var offense_cnt := 0
	var tanker_cnt := 0
	var support_cnt := 0
	var item_cnt := 0

	for entry in deck:
		var uid := make_variant_id(str(entry))
		if unique.has(uid):
			return {"ok": false, "reason": "Bộ bài có thẻ trùng lặp (%s)!" % uid}
		unique[uid] = true
		var c := get_card(uid)
		if c.is_empty():
			continue
		var rg: String = str(c["role_group"])
		if rg == "atk_phys" or rg == "atk_mag":
			offense_cnt += 1
		elif rg == "tanker":
			tanker_cnt += 1
		elif rg == "support":
			support_cnt += 1
		elif rg == "item":
			item_cnt += 1

	var ok := (
		deck.size() == 15
		and offense_cnt >= 2
		and tanker_cnt >= 2
		and support_cnt >= 2
		and item_cnt >= 2
	)
	var msg := "Đủ 15/15 thẻ hợp lệ"
	if not ok:
		msg = "Đã chọn %d/15 thẻ (Cần đủ 15 thẻ & mỗi nhóm >= 2)" % deck.size()
	return {
		"ok": ok,
		"reason": msg,
		"count": deck.size(),
		"offense": offense_cnt,
		"tanker": tanker_cnt,
		"support": support_cnt,
		"item": item_cnt,
	}


func toggle_card_in_loadout(card_id_or_uid: String, elem: String = "") -> String:
	var uid := make_variant_id(card_id_or_uid, elem)
	var base_id := get_base_card_id(uid)
	var c_elem := get_card_element(uid)
	var elem_short: String = str(ELEMENT_META.get(c_elem, ELEMENT_META["kim"])["short"])
	var label_str := "%s (%s)" % [base_id, elem_short]

	if not is_card_owned(uid):
		return "Bạn chưa sở hữu thẻ %s! Hãy mở rương để thu thập." % label_str
	if loadout_deck.has(uid):
		loadout_deck.erase(uid)
		save_game()
		return "Đã gỡ %s khỏi Bộ Bài Xuất Chiến (%d/15)." % [label_str, loadout_deck.size()]
	if loadout_deck.size() >= 15:
		return "Bộ bài đã đủ 15/15 lá! Hãy gỡ bớt 1 lá trước khi thêm."
	loadout_deck.append(uid)
	save_game()
	return "Đã thêm %s vào Bộ Bài Xuất Chiến (%d/15)." % [label_str, loadout_deck.size()]


func auto_build_valid_loadout() -> void:
	loadout_deck.clear()
	var owned_uids: Array = []
	for c in cards_db:
		var uid: String = str(c["uid"])
		if int(owned_counts.get(uid, 0)) > 0:
			owned_uids.append(uid)

	# Sort owned cards by rarity descending (SSR -> S -> R -> N), then by variant_num
	owned_uids.sort_custom(func(a, b):
		var ca: Dictionary = cards_by_uid[a]
		var cb: Dictionary = cards_by_uid[b]
		var ra: int = RARITY_ORDER.get(ca["rarity"], 1)
		var rb: int = RARITY_ORDER.get(cb["rarity"], 1)
		if ra != rb:
			return ra > rb
		return int(ca["variant_num"]) < int(cb["variant_num"])
	)

	var buckets := {
		"offense": [],
		"tanker": [],
		"support": [],
		"item": [],
	}
	var used_base_ids := {}
	for uid in owned_uids:
		var base_id: String = str(cards_by_uid[uid]["base_id"])
		if used_base_ids.has(base_id):
			continue
		used_base_ids[base_id] = true
		var rg: String = str(cards_by_uid[uid]["role_group"])
		if rg == "atk_phys" or rg == "atk_mag":
			buckets["offense"].append(uid)
		elif rg == "tanker":
			buckets["tanker"].append(uid)
		elif rg == "support":
			buckets["support"].append(uid)
		else:
			buckets["item"].append(uid)

	# Pick at least 3 from each bucket first (12 cards), then fill to 15
	for bkey in ["tanker", "offense", "support", "item"]:
		var arr: Array = buckets[bkey]
		for i in range(min(3, arr.size())):
			if not loadout_deck.has(arr[i]):
				loadout_deck.append(arr[i])

	for uid in owned_uids:
		if loadout_deck.size() >= 15:
			break
		if not loadout_deck.has(uid):
			loadout_deck.append(uid)

	loadout_deck.sort_custom(func(a, b):
		return int(cards_by_uid[a]["variant_num"]) < int(cards_by_uid[b]["variant_num"])
	)
	save_game()


# Opens 1 Gacha Pack of the chosen type (1..5):
# Each pulled card randomly picks 1 base template (by rarity) AND randomly generates 1 fixed element (1 of 500 cards!)
func open_gacha_pack(pack_type_id: int = -1) -> Array:
	var p_type := selected_pack_type if pack_type_id < 1 else clampi(pack_type_id, 1, 5)
	var cur_cnt := int(pack_counts_by_type.get(p_type, 0))
	if cur_cnt <= 0:
		return []
	pack_counts_by_type[p_type] = cur_cnt - 1
	sync_total_pack_count()

	var p_meta: Dictionary = PACK_TYPES.get(p_type, PACK_TYPES[1])
	var rates: Dictionary = p_meta["rates"]
	var r_ssr: float = float(rates.get("SSR", 0.0))
	var r_s: float = float(rates.get("S", 0.5))
	var r_r: float = float(rates.get("R", 5.5))

	var by_tier := {"N": [], "R": [], "S": [], "SSR": []}
	for c in base_cards_db:
		by_tier[c["rarity"]].append(c["id"])

	var results: Array = []

	for _i in range(10):
		var tier := "N"
		var roll := randf() * 100.0
		if roll < r_ssr:
			tier = "SSR"
		elif roll < (r_ssr + r_s):
			tier = "S"
		elif roll < (r_ssr + r_s + r_r):
			tier = "R"
		else:
			tier = "N"

		var pool: Array = by_tier[tier]
		var picked_base_id: String = str(pool[randi() % pool.size()])
		var picked_elem: String = ELEMENTS[randi() % ELEMENTS.size()]
		var uid := "%s_%s" % [picked_base_id, picked_elem]
		var was_new: bool = int(owned_counts.get(uid, 0)) == 0

		owned_counts[uid] = int(owned_counts.get(uid, 0)) + 1
		card_elements[picked_base_id] = picked_elem

		results.append({
			"uid": uid,
			"card_id": picked_base_id,
			"element": picked_elem,
			"rarity": tier,
			"is_new": was_new,
			"total_owned": owned_counts[uid],
			"pack_type": p_type,
		})

	save_game()
	return results


func add_free_packs(amount_per_type: int = 1) -> void:
	for p_t in range(1, 6):
		pack_counts_by_type[p_t] = int(pack_counts_by_type.get(p_t, 0)) + maxi(1, amount_per_type)
	sync_total_pack_count()
	save_game()


func add_demo_currencies(coin_amt: int = 2000, diamond_amt: int = 300) -> void:
	gold += maxi(0, coin_amt)
	diamonds += maxi(0, diamond_amt)
	save_game()


# Buys Gacha Packs using Coin (for Packs #1, #2, #3) or Kim Cương (exclusively for Packs #4 & #5)
func buy_pack(pack_type_id: int = -1, amount: int = 1) -> Dictionary:
	var p_type := selected_pack_type if pack_type_id < 1 else clampi(pack_type_id, 1, 5)
	var qty := maxi(1, amount)
	var p_meta: Dictionary = PACK_TYPES.get(p_type, PACK_TYPES[1])
	var cur_type: String = str(p_meta.get("currency", "coin"))
	var unit_price: int = int(p_meta.get("price", 200))
	var total_cost: int = unit_price * qty

	if cur_type == "diamond":
		if diamonds < total_cost:
			return {
				"ok": false,
				"msg": "Không đủ Kim Cương! Cần %d Kim Cương để mua +%d %s (Hiện có %d)." % [total_cost, qty, str(p_meta["name"]), diamonds],
			}
		diamonds -= total_cost
		pack_counts_by_type[p_type] = int(pack_counts_by_type.get(p_type, 0)) + qty
		sync_total_pack_count()
		save_game()
		return {
			"ok": true,
			"msg": "Đã mua +%d %s bằng %d Kim Cương! (Hiện có x%d Pack #%d)" % [qty, str(p_meta["name"]), total_cost, int(pack_counts_by_type[p_type]), p_type],
		}
	else:
		if gold < total_cost:
			return {
				"ok": false,
				"msg": "Không đủ Coin! Cần %d Coin để mua +%d %s (Hiện có %d)." % [total_cost, qty, str(p_meta["name"]), gold],
			}
		gold -= total_cost
		pack_counts_by_type[p_type] = int(pack_counts_by_type.get(p_type, 0)) + qty
		sync_total_pack_count()
		save_game()
		return {
			"ok": true,
			"msg": "Đã mua +%d %s bằng %d Coin! (Hiện có x%d Pack #%d)" % [qty, str(p_meta["name"]), total_cost, int(pack_counts_by_type[p_type]), p_type],
		}


# Fast zero-import-lag texture loader from res:// path (works in Editor + Web/Android/iOS PCK)
func tex(res_path: String) -> Texture2D:
	if res_path.is_empty():
		return null
	if _tex_cache.has(res_path):
		return _tex_cache[res_path]

	if ResourceLoader.exists(res_path):
		var loaded = load(res_path)
		if loaded is Texture2D:
			_tex_cache[res_path] = loaded
			return loaded

	if FileAccess.file_exists(res_path):
		var buf := FileAccess.get_file_as_bytes(res_path)
		if not buf.is_empty():
			var b_img := Image.new()
			var err := ERR_FILE_UNRECOGNIZED
			if res_path.ends_with(".png"):
				err = b_img.load_png_from_buffer(buf)
			elif res_path.ends_with(".webp"):
				err = b_img.load_webp_from_buffer(buf)
			elif res_path.ends_with(".jpg") or res_path.ends_with(".jpeg"):
				err = b_img.load_jpg_from_buffer(buf)
			if err == OK and not b_img.is_empty():
				var b_tex := ImageTexture.create_from_image(b_img)
				_tex_cache[res_path] = b_tex
				return b_tex

	var abs_path := ProjectSettings.globalize_path(res_path)
	if FileAccess.file_exists(abs_path):
		var img := Image.load_from_file(abs_path)
		if img and not img.is_empty():
			var itex := ImageTexture.create_from_image(img)
			_tex_cache[res_path] = itex
			return itex

	_tex_cache[res_path] = null
	return null


func get_weapon_config(card_num: int) -> Dictionary:
	if _weapon_cfg_cache.has(card_num):
		return _weapon_cfg_cache[card_num]
	var res_cfg_path := "res://assets/weapons/configs/w%03d.json" % card_num
	var raw_json := ""
	if FileAccess.file_exists(res_cfg_path):
		raw_json = FileAccess.get_file_as_string(res_cfg_path)
	else:
		var cfg_path := ProjectSettings.globalize_path(res_cfg_path)
		if FileAccess.file_exists(cfg_path):
			raw_json = FileAccess.get_file_as_string(cfg_path)
	if not raw_json.is_empty():
		var parsed = JSON.parse_string(raw_json)
		if typeof(parsed) == TYPE_DICTIONARY:
			_weapon_cfg_cache[card_num] = parsed
			return parsed
	return {}


# ==============================================================================
# HAND-DRAWN 2D FANTASY GUI THEME HELPERS (<= 8 Colors, 9-Slice StyleBoxTexture)
# ==============================================================================
func make_gui_panel_style(variant: String = "section", pad: int = 18, mod_col: Color = Color.WHITE) -> StyleBoxTexture:
	var cache_key := "pnl_%s_%d_%s" % [variant, pad, mod_col.to_html()]
	if _style_cache.has(cache_key):
		return _style_cache[cache_key]

	var file_map := {
		"dialog": "res://assets/ui_hud/gui/dialog_board_bg.png",
		"section": "res://assets/ui_hud/gui/panel_section_bg.png",
		"header": "res://assets/ui_hud/gui/header_banner_bg.png",
		"slot_active": "res://assets/ui_hud/gui/slot_box_active_bg.png",
		"slot_gray": "res://assets/ui_hud/gui/slot_box_gray_bg.png",
	}
	var res_p: String = file_map.get(variant, file_map["section"])
	var sb := StyleBoxTexture.new()
	sb.texture = tex(res_p)
	sb.modulate_color = mod_col
	if variant == "slot_active" or variant == "slot_gray":
		sb.texture_margin_left = 12
		sb.texture_margin_right = 12
		sb.texture_margin_top = 12
		sb.texture_margin_bottom = 12
		var cp := maxi(10, pad)
		sb.content_margin_left = cp
		sb.content_margin_right = cp
		sb.content_margin_top = cp
		sb.content_margin_bottom = cp
	elif variant == "header":
		sb.texture_margin_left = 34
		sb.texture_margin_right = 34
		sb.texture_margin_top = 24
		sb.texture_margin_bottom = 24
		var cp_x := maxi(34, pad + 14)
		var cp_y := maxi(16, pad)
		sb.content_margin_left = cp_x
		sb.content_margin_right = cp_x
		sb.content_margin_top = cp_y
		sb.content_margin_bottom = cp_y
	else:
		sb.texture_margin_left = 34
		sb.texture_margin_right = 34
		sb.texture_margin_top = 34
		sb.texture_margin_bottom = 34
		var cp_x := maxi(26, pad + 8)
		var cp_y := maxi(22, pad + 2)
		sb.content_margin_left = cp_x
		sb.content_margin_right = cp_x
		sb.content_margin_top = cp_y
		sb.content_margin_bottom = cp_y
	_style_cache[cache_key] = sb
	return sb


func make_gui_button_style(variant: String = "slate", is_large: bool = false, mod_col: Color = Color.WHITE, pad_x: int = 16, pad_y: int = 8) -> StyleBoxTexture:
	var cache_key := "btn_%s_%d_%s_%d_%d" % [variant, 1 if is_large else 0, mod_col.to_html(), pad_x, pad_y]
	if _style_cache.has(cache_key):
		return _style_cache[cache_key]

	if variant == "back_home":
		var sb_back := StyleBoxTexture.new()
		sb_back.texture = tex("res://assets/ui_hud/gui/btn_back_home.png")
		sb_back.modulate_color = mod_col
		sb_back.content_margin_left = maxi(42, pad_x)
		sb_back.content_margin_right = maxi(16, int(pad_x * 0.7))
		sb_back.content_margin_top = pad_y
		sb_back.content_margin_bottom = pad_y
		_style_cache[cache_key] = sb_back
		return sb_back

	var base_map := {
		"red": "btn_red_battle",
		"gold": "btn_gold_primary",
		"purple": "btn_purple_gacha",
		"green": "btn_green_collection",
		"wood": "btn_wood_back",
		"slate": "btn_slate_normal",
	}
	var bname: String = base_map.get(variant, "btn_slate_normal")
	var suffix := ".png" if is_large else "_sm.png"
	var sb := StyleBoxTexture.new()
	sb.texture = tex("res://assets/ui_hud/gui/" + bname + suffix)
	sb.modulate_color = mod_col
	if is_large:
		sb.texture_margin_left = 42
		sb.texture_margin_right = 42
		sb.texture_margin_top = 20
		sb.texture_margin_bottom = 20
	else:
		sb.texture_margin_left = 22
		sb.texture_margin_right = 22
		sb.texture_margin_top = 10
		sb.texture_margin_bottom = 10
	var min_px := 48 if is_large else 10
	sb.content_margin_left = maxi(min_px, pad_x)
	sb.content_margin_right = maxi(min_px, pad_x)
	sb.content_margin_top = pad_y
	sb.content_margin_bottom = pad_y
	_style_cache[cache_key] = sb
	return sb


var is_touch_scrolling: bool = false


func apply_gui_button(btn: Button, variant: String = "slate", is_large: bool = false, pad_x: int = 16, pad_y: int = 8) -> void:
	btn.focus_mode = Control.FOCUS_NONE
	btn.mouse_filter = Control.MOUSE_FILTER_PASS
	btn.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	var sb_normal := make_gui_button_style(variant, is_large, Color.WHITE, pad_x, pad_y)
	var sb_hover := make_gui_button_style(variant, is_large, Color(1.08, 1.08, 1.08, 1.0), pad_x, pad_y)
	var sb_pressed := make_gui_button_style(variant, is_large, Color(0.88, 0.88, 0.90, 1.0), pad_x, pad_y)
	var sb_disabled := make_gui_button_style("slate", is_large, Color(0.65, 0.65, 0.70, 0.88), pad_x, pad_y)
	btn.add_theme_stylebox_override("normal", sb_normal)
	btn.add_theme_stylebox_override("hover", sb_hover)
	btn.add_theme_stylebox_override("pressed", sb_pressed)
	btn.add_theme_stylebox_override("disabled", sb_disabled)
	btn.add_theme_color_override("font_outline_color", Color(0.01, 0.01, 0.03, 0.98))
	btn.add_theme_constant_override("outline_size", 5)


func setup_touch_scroll(scroll: ScrollContainer) -> void:
	if scroll == null:
		return
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	scroll.follow_focus = false
	scroll.mouse_filter = Control.MOUSE_FILTER_PASS
	var vbar := scroll.get_v_scroll_bar()
	if vbar:
		vbar.custom_minimum_size.x = 14
		vbar.mouse_filter = Control.MOUSE_FILTER_PASS
	if not scroll.has_node("_TouchScrollController"):
		var helper := _TouchScrollController.new()
		helper.name = "_TouchScrollController"
		helper.target_scroll = scroll
		scroll.add_child(helper)


class _TouchScrollController extends Node:
	var target_scroll: ScrollContainer = null
	var _pressing: bool = false
	var _dragging: bool = false
	var _start_pos: Vector2 = Vector2.ZERO
	var _start_scroll_v: int = 0
	var _velocity_y: float = 0.0

	func _process(delta: float) -> void:
		if target_scroll == null or not is_instance_valid(target_scroll) or not target_scroll.is_visible_in_tree():
			_pressing = false
			_dragging = false
			_velocity_y = 0.0
			return
		if not _pressing and absf(_velocity_y) > 15.0:
			target_scroll.scroll_vertical = maxi(0, int(round(float(target_scroll.scroll_vertical) + _velocity_y * delta)))
			_velocity_y = move_toward(_velocity_y, 0.0, 2600.0 * delta)

	func _input(event: InputEvent) -> void:
		if target_scroll == null or not is_instance_valid(target_scroll) or not target_scroll.is_visible_in_tree():
			return

		if event is InputEventScreenTouch:
			if event.pressed:
				if target_scroll.get_global_rect().has_point(event.position):
					_pressing = true
					_dragging = false
					_velocity_y = 0.0
					_start_pos = event.position
					_start_scroll_v = target_scroll.scroll_vertical
					GameState.is_touch_scrolling = false
			else:
				_pressing = false
				if _dragging:
					_dragging = false
					get_tree().create_timer(0.06).timeout.connect(func(): GameState.is_touch_scrolling = false)
		elif event is InputEventScreenDrag and _pressing:
			var dy: float = _start_pos.y - event.position.y
			if not _dragging and absf(dy) > 10.0:
				_dragging = true
				GameState.is_touch_scrolling = true
			if _dragging:
				target_scroll.scroll_vertical = maxi(0, _start_scroll_v + int(round(dy)))
				_velocity_y = -event.velocity.y * 0.65
		elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
			if event.pressed:
				if target_scroll.get_global_rect().has_point(event.position):
					_pressing = true
					_dragging = false
					_velocity_y = 0.0
					_start_pos = event.position
					_start_scroll_v = target_scroll.scroll_vertical
					GameState.is_touch_scrolling = false
			else:
				_pressing = false
				if _dragging:
					_dragging = false
					get_tree().create_timer(0.06).timeout.connect(func(): GameState.is_touch_scrolling = false)
		elif event is InputEventMouseMotion and _pressing:
			var dy_m: float = _start_pos.y - event.position.y
			if not _dragging and absf(dy_m) > 10.0:
				_dragging = true
				GameState.is_touch_scrolling = true
			if _dragging:
				target_scroll.scroll_vertical = maxi(0, _start_scroll_v + int(round(dy_m)))
				_velocity_y = -event.velocity.y * 0.45


