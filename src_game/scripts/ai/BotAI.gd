extends RefCounted

# ==============================================================================
# ARCANA FIVE — THUẬT TOÁN AI BOT CHIẾN THUẬT & TÂM LÝ CHIẾN POKER (BotAI.gd)
# ==============================================================================
# Điều khiển cả Người chơi chính (khi bật chế độ Bot) lẫn 1–3 Đối thủ máy:
# 1. Phân tích thế trận thời gian thực (Tanker/DPS/Support, Khiên địch, Mana địch, Hệ Ngũ Hành).
# 2. Chấm điểm Utility từng lá bài theo Tương Khắc (+25% Dame), Tương Sinh (+15% Công & Hồi HP),
#    Ngũ Hành Tụ Hội (đủ 5 hệ) và Ngữ cảnh dùng Item (không bao giờ phí Item Buff khi trống sân).
# 3. Tâm lý chiến bàn Poker 3 giai đoạn trong 15s Chuẩn Bị:
#    - Giai đoạn 1 (15s -> 9s): Dàn trận tiền tuyến + Tung hỏa mù (Fake-out Overcommit úp bài dọa All-in).
#    - Giai đoạn 2 (9s -> 4s): Đọc bài úp đối thủ & Nhặt lại bài mồi về tay (Tactical Recall).
#    - Giai đoạn 3 (4s -> 0.5s): Đánh úp giây cuối (Last-Second Trump Card / Counter Item Commit).


static func create_bot_profile(player_idx: int) -> Dictionary:
	var styles := ["BALANCED_SYNERGY", "FAKE_ALL_IN_BLUFF", "LATE_SNIPE_COUNTER", "AGGRO_TEMPO"]
	var style: String = styles[player_idx % styles.size()]
	return {
		"style": style,
		"next_think_wait": randf_range(0.6, 1.3),
		"has_done_fakeout": false,
		"has_done_recall": false,
		"has_done_late_snipe": false,
		"decoy_slot": -1,
	}


static func reset_round_profile(profile: Dictionary, round_num: int) -> void:
	var styles := ["BALANCED_SYNERGY", "FAKE_ALL_IN_BLUFF", "LATE_SNIPE_COUNTER", "AGGRO_TEMPO"]
	profile["style"] = styles[(round_num + randi()) % styles.size()]
	profile["next_think_wait"] = randf_range(0.55, 1.25)
	profile["has_done_fakeout"] = false
	profile["has_done_recall"] = false
	profile["has_done_late_snipe"] = false
	profile["decoy_slot"] = -1


static func analyze_battlefield(player_idx: int, players: Array, units: Array) -> Dictionary:
	var my_tankers := 0
	var my_dps := 0
	var my_supports := 0
	var my_elems := {}
	var lowest_ally_hp_ratio := 1.0
	var my_alive_units := 0

	var enemy_elems := {}
	var max_enemy_shield := 0.0
	var max_enemy_mana_ratio := 0.0
	var enemy_alive_units := 0

	for u in units:
		if float(u.get("hp", 0.0)) <= 0.0:
			continue
		var owner_i: int = int(u.get("owner_idx", -1))
		var elem: String = str(u.get("element", "kim"))
		var rg: String = str(u.get("role_group", "atk_phys"))
		var hp_r: float = float(u.get("hp", 100.0)) / maxf(1.0, float(u.get("max_hp", 100.0)))

		if owner_i == player_idx:
			my_alive_units += 1
			my_elems[elem] = int(my_elems.get(elem, 0)) + 1
			if hp_r < lowest_ally_hp_ratio:
				lowest_ally_hp_ratio = hp_r
			if rg == "tanker":
				my_tankers += 1
			elif rg == "support":
				my_supports += 1
			else:
				my_dps += 1
		else:
			enemy_alive_units += 1
			enemy_elems[elem] = int(enemy_elems.get(elem, 0)) + 1
			var sh: float = float(u.get("shield", 0.0))
			if sh > max_enemy_shield:
				max_enemy_shield = sh
			var mr: float = float(u.get("mana", 0.0)) / maxf(1.0, float(u.get("max_mana", 100.0)))
			if mr > max_enemy_mana_ratio:
				max_enemy_mana_ratio = mr

	# Also count face-down heroes already placed by this player in current prep phase
	var p_data: Dictionary = players[player_idx]
	var my_slots: Array = p_data.get("slots", [])
	var placed_heroes_this_turn := 0
	var placed_facedown_count := 0
	for s in my_slots:
		if s.get("state", "empty") == "facedown":
			placed_facedown_count += 1
			var cid: String = str(s.get("card_id", ""))
			var selem: String = str(s.get("element", "kim"))
			var c := GameState.get_card(cid)
			if not c.is_empty() and not bool(c.get("is_item", false)):
				placed_heroes_this_turn += 1
				my_elems[selem] = int(my_elems.get(selem, 0)) + 1
				var rg2: String = str(c.get("role_group", "atk_phys"))
				if rg2 == "tanker":
					my_tankers += 1
				elif rg2 == "support":
					my_supports += 1
				else:
					my_dps += 1

	# Dominant enemy element
	var dom_enemy_elem := "moc"
	var best_cnt := -1
	for ek in enemy_elems.keys():
		if int(enemy_elems[ek]) > best_cnt:
			best_cnt = int(enemy_elems[ek])
			dom_enemy_elem = ek

	var opp_facedown_total := 0
	for i in range(players.size()):
		if i == player_idx or not bool(players[i].get("alive", true)):
			continue
		for s in players[i].get("slots", []):
			if s.get("state", "empty") == "facedown":
				opp_facedown_total += 1

	return {
		"my_alive_units": my_alive_units,
		"my_total_heroes": my_alive_units + placed_heroes_this_turn,
		"my_tankers": my_tankers,
		"my_dps": my_dps,
		"my_supports": my_supports,
		"my_elems": my_elems,
		"lowest_ally_hp_ratio": lowest_ally_hp_ratio,
		"enemy_alive_units": enemy_alive_units,
		"dom_enemy_elem": dom_enemy_elem,
		"max_enemy_shield": max_enemy_shield,
		"max_enemy_mana_ratio": max_enemy_mana_ratio,
		"placed_facedown_count": placed_facedown_count,
		"opp_facedown_total": opp_facedown_total,
	}


static func score_card(card_inst: Dictionary, info: Dictionary) -> float:
	var cid: String = str(card_inst.get("card_id", "C001"))
	var elem: String = str(card_inst.get("element", "kim"))
	var c := GameState.get_card(cid)
	if c.is_empty():
		return -999.0

	var rarity: String = str(c.get("rarity", "N"))
	var rg: String = str(c.get("role_group", "atk_phys"))
	var is_item: bool = bool(c.get("is_item", false))
	var c_num: int = int(c.get("num", 1))

	# 1. Base Rarity Power Budget
	var score := 24.0
	if rarity == "R":
		score = 34.0
	elif rarity == "S":
		score = 46.0
	elif rarity == "SSR":
		score = 62.0

	# 2. Wuxing Counter & Generation Synergy
	var dom_enemy: String = str(info.get("dom_enemy_elem", "moc"))
	if int(info.get("enemy_alive_units", 0)) > 0:
		if GameState.does_element_counter(elem, dom_enemy):
			score += 28.0
		elif GameState.does_element_counter(dom_enemy, elem):
			score -= 12.0

	var my_elems: Dictionary = info.get("my_elems", {})
	for existing_e in my_elems.keys():
		if GameState.does_element_generate(existing_e, elem) or GameState.does_element_generate(elem, existing_e):
			score += 18.0
			break

	if not my_elems.has(elem) and my_elems.size() == 4:
		# Completes 5-Element Unity (Ngũ Hành Tụ Hội)!
		score += 42.0

	# 3. Role & Tactical Context Evaluation
	if not is_item:
		var tankers: int = int(info.get("my_tankers", 0))
		var dps: int = int(info.get("my_dps", 0))
		var sups: int = int(info.get("my_supports", 0))

		if rg == "tanker":
			if tankers == 0:
				score += 52.0
			elif tankers == 1:
				score += 22.0
			else:
				score -= 10.0
		elif rg == "atk_phys" or rg == "atk_mag":
			if tankers >= 1 and dps < 2:
				score += 36.0
			elif dps == 0:
				score += 28.0
		elif rg == "support":
			if tankers >= 1 and dps >= 1 and sups == 0:
				score += 34.0
			elif float(info.get("lowest_ally_hp_ratio", 1.0)) < 0.65:
				score += 38.0
			elif tankers == 0 and dps == 0:
				score -= 22.0

		# Counter-shield hero bonus (e.g. C018 Execute / C078 ShieldSteal)
		if (c_num == 18 or c_num == 78) and float(info.get("max_enemy_shield", 0.0)) >= 50.0:
			score += 35.0
	else:
		# Item Card Evaluation (C081..C100)
		var is_offensive_item := (c_num in [82, 86, 88, 89, 91, 93, 96, 98])
		var my_total_heroes: int = int(info.get("my_total_heroes", 0))
		var enemy_alive: int = int(info.get("enemy_alive_units", 0))

		if not is_offensive_item and my_total_heroes == 0:
			# Never waste a buff/heal/shield item when we have 0 heroes!
			return -500.0

		if is_offensive_item and enemy_alive == 0:
			score -= 35.0

		if c_num in [81, 92, 97] and float(info.get("lowest_ally_hp_ratio", 1.0)) < 0.70:
			score += 44.0
		elif c_num == 81 and float(info.get("lowest_ally_hp_ratio", 1.0)) > 0.92:
			score -= 28.0

		if c_num == 98 and float(info.get("max_enemy_shield", 0.0)) >= 60.0:
			score += 55.0
		if c_num in [86, 89, 91, 96] and float(info.get("max_enemy_mana_ratio", 0.0)) >= 0.50:
			score += 38.0
		if c_num in [85, 87, 90, 94, 99, 100] and my_total_heroes >= 2:
			score += 26.0

	return score


static func choose_best_slot(card_inst: Dictionary, slots: Array) -> int:
	var cid: String = str(card_inst.get("card_id", "C001"))
	var c := GameState.get_card(cid)
	var rg: String = str(c.get("role_group", "atk_phys"))
	var is_ranged: bool = bool(c.get("is_ranged", false))

	var preferred_order: Array = [4, 5, 3, 6, 2, 7, 1, 8, 0, 9]
	if rg == "tanker":
		# Tankers take central vanguard slots (4, 5, 3, 6)
		preferred_order = [4, 5, 3, 6, 2, 7, 1, 8, 0, 9]
	elif rg == "support" or is_ranged:
		# Ranged / Support prefer safe backline flank slots (1, 8, 0, 9, 2, 7)
		preferred_order = [1, 8, 0, 9, 2, 7, 3, 6, 4, 5]
	else:
		# Melee Strikers take inner-flank slots (3, 6, 2, 7, 4, 5)
		preferred_order = [3, 6, 2, 7, 4, 5, 1, 8, 0, 9]

	for s_idx in preferred_order:
		if s_idx >= 0 and s_idx < slots.size() and slots[s_idx].get("state", "empty") == "empty":
			return s_idx
	return -1


# Executes 1 real-time decision step during the 15s Preparation Phase.
# Returns a dictionary describing the action:
#   {"action": "none"}
#   {"action": "place", "hand_idx": int, "slot_idx": int, "reason": String}
#   {"action": "recall", "slot_idx": int, "reason": String}
static func decide_prep_step(
	player_idx: int,
	players: Array,
	units: Array,
	prep_time_left: float,
	round_num: int,
	profile: Dictionary
) -> Dictionary:
	var p: Dictionary = players[player_idx]
	if not bool(p.get("alive", true)):
		return {"action": "none"}

	var hand: Array = p.get("hand", [])
	var slots: Array = p.get("slots", [])
	var info := analyze_battlefield(player_idx, players, units)

	var my_alive: int = int(info.get("my_alive_units", 0))
	var placed_now: int = int(info.get("placed_facedown_count", 0))
	var style: String = str(profile.get("style", "BALANCED_SYNERGY"))

	# Target number of cards to deploy this round based on tactical situation & hand size
	var target_deploy := 2
	if round_num == 1:
		target_deploy = 3
	elif my_alive == 0:
		target_deploy = mini(3, hand.size() + placed_now)
	elif float(p.get("hp", 100.0)) <= 40.0:
		# Desperate defense / All-in when low HP
		target_deploy = mini(4, hand.size() + placed_now)
	elif my_alive >= 4 and int(info.get("enemy_alive_units", 0)) <= 1:
		# Already dominating board -> Hold cards in hand!
		target_deploy = 1

	# --------------------------------------------------------------------------
	# STAGE 2 (9.0s -> 4.2s): POKER MIND-GAME RECALL (Nhặt lại bài mồi / bài lỗ)
	# --------------------------------------------------------------------------
	if prep_time_left <= 9.2 and prep_time_left >= 4.0 and not bool(profile.get("has_done_recall", false)):
		# Check if we placed a decoy bluff slot earlier
		var decoy_s: int = int(profile.get("decoy_slot", -1))
		if decoy_s >= 0 and decoy_s < slots.size() and slots[decoy_s].get("state", "") == "facedown":
			profile["has_done_recall"] = true
			profile["decoy_slot"] = -1
			return {
				"action": "recall",
				"slot_idx": decoy_s,
				"reason": "Mind-Game Fake-out: Nhặt lại bài dọa từ Ô #%d về tay!" % (decoy_s + 1),
			}

		# Or check if any currently face-down card has low/negative tactical value
		if placed_now > target_deploy:
			var worst_slot := -1
			var worst_score := 9999.0
			for s_i in range(slots.size()):
				if slots[s_i].get("state", "") == "facedown":
					var sc := score_card(slots[s_i], info)
					if sc < worst_score:
						worst_score = sc
						worst_slot = s_i
			if worst_slot >= 0:
				profile["has_done_recall"] = true
				return {
					"action": "recall",
					"slot_idx": worst_slot,
					"reason": "Đọc bàn: Nhặt lại bài ở Ô #%d về tay giữ lực lượng!" % (worst_slot + 1),
				}

	# --------------------------------------------------------------------------
	# STAGE 1 (15.0s -> 9.2s): OPENING DEPLOY & FAKE-OUT OVERCOMMIT BLUFF
	# --------------------------------------------------------------------------
	if hand.is_empty():
		return {"action": "none"}

	# Score all cards in hand
	var best_h_idx := -1
	var best_score := -999.0
	var lowest_h_idx := 0
	var lowest_score := 9999.0

	for h_i in range(hand.size()):
		var sc := score_card(hand[h_i], info)
		if sc > best_score:
			best_score = sc
			best_h_idx = h_i
		if sc < lowest_score:
			lowest_score = sc
			lowest_h_idx = h_i

	# Fake-out bluff in Stage 1: place an extra decoy card early to scare opponents, then recall it in Stage 2
	if (
		style == "FAKE_ALL_IN_BLUFF"
		and prep_time_left > 9.5
		and not bool(profile.get("has_done_fakeout", false))
		and placed_now >= 1
		and hand.size() >= 2
	):
		var decoy_slot := choose_best_slot(hand[lowest_h_idx], slots)
		if decoy_slot >= 0:
			profile["has_done_fakeout"] = true
			profile["decoy_slot"] = decoy_slot
			return {
				"action": "place",
				"hand_idx": lowest_h_idx,
				"slot_idx": decoy_slot,
				"reason": "Tung Hỏa Mù (Bluff): Úp bài dọa All-in vào Ô #%d" % (decoy_slot + 1),
			}

	# If style is LATE_SNIPE_COUNTER, hold the final trump card until the last 4.2 seconds!
	var allow_cap := target_deploy
	if style == "LATE_SNIPE_COUNTER" and prep_time_left > 4.2:
		allow_cap = maxi(1, target_deploy - 1)

	if placed_now < allow_cap and best_h_idx >= 0 and best_score > 10.0:
		var chosen_slot := choose_best_slot(hand[best_h_idx], slots)
		if chosen_slot >= 0:
			var c_data := GameState.get_card(str(hand[best_h_idx].get("card_id", "C001")))
			var tag_note := "Chiến thuật" if prep_time_left > 4.2 else "Đánh úp giây cuối"
			return {
				"action": "place",
				"hand_idx": best_h_idx,
				"slot_idx": chosen_slot,
				"reason": "%s: Úp [%s] vào Ô #%d" % [tag_note, str(c_data.get("role_label", "Thẻ")), chosen_slot + 1],
			}

	return {"action": "none"}
