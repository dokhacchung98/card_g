extends Node

signal auth_state_changed(user_profile: Dictionary)
signal login_succeeded(user_profile: Dictionary, is_first_login: bool)
signal matchmaking_updated(room_data: Dictionary)
signal matchmaking_started_battle(room_data: Dictionary)
signal room_error(err_msg: String)

const DEFAULT_BACKEND_URL := "https://be-card-g.vercel.app"
const AUTH_SAVE_PATH := "user://arcana_five_google_auth_v2.json"
const MATCHMAKING_TIMEOUT_SEC := 10.0

# Firebase Project Metadata (arcana-five-card-g)
const FIREBASE_CONFIG := {
	"projectId": "arcana-five-card-g",
	"projectNumber": "673339667273",
	"packageName": "com.dochung.arcanafive",
	"androidAppId": "1:673339667273:android:03922dbe27f2e78336a098",
	"iosAppId": "1:673339667273:ios:8c700ab687abfdc236a098",
	"webAppId": "1:673339667273:web:24654b1b2267e9e136a098",
	"apiKey": "AIzaSyBf-cdTWa5rXQPFIcUXa1BI8b65Fp5u9M4",
	"authDomain": "arcana-five-card-g.firebaseapp.com",
}

var backend_url: String = DEFAULT_BACKEND_URL
var is_online: bool = false
var session_token: String = ""
var current_user: Dictionary = {
	"uid": "local_commander_01",
	"googleId": "",
	"email": "",
	"displayName": "Đại Pháp Sư Lam Long",
	"isGoogleLinked": false,
	"elo": 1200,
}

var active_room: Dictionary = {}
var is_searching_match: bool = false
var local_search_elapsed: float = 0.0
var local_search_mode: int = 4
var local_search_type: String = "matchmaking" # "matchmaking" or "custom_room"
var _poll_accum: float = 0.0


func _ready() -> void:
	_load_saved_auth()
	check_server_health()
	log_analytics_event("app_open", {
		"project_id": FIREBASE_CONFIG["projectId"],
		"platform": OS.get_name(),
	})


func _process(delta: float) -> void:
	if not is_searching_match:
		return

	local_search_elapsed += delta
	_poll_accum += delta

	var remaining := maxf(0.0, MATCHMAKING_TIMEOUT_SEC - local_search_elapsed)
	active_room["remainingWaitSec"] = snappedf(remaining, 0.1)

	# Poll backend every 0.8s if online
	if is_online and _poll_accum >= 0.8:
		_poll_accum = 0.0
		_poll_room_status_from_server()
	elif not is_online and _poll_accum >= 0.25:
		_poll_accum = 0.0
		emit_signal("matchmaking_updated", active_room)

	# Enforce strict 10-second rule: if 10s elapses without full players (online or offline),
	# automatically fill remaining corners with Bots and launch battle!
	if local_search_elapsed >= MATCHMAKING_TIMEOUT_SEC:
		_complete_match_with_bot_fallback("timeout_10s_filled_with_bots")


func is_logged_in() -> bool:
	return bool(current_user.get("isGoogleLinked", false))


func _load_saved_auth() -> void:
	if not FileAccess.file_exists(AUTH_SAVE_PATH):
		return
	var raw := FileAccess.get_file_as_string(AUTH_SAVE_PATH)
	var parsed = JSON.parse_string(raw)
	if typeof(parsed) == TYPE_DICTIONARY:
		session_token = str(parsed.get("token", ""))
		if parsed.has("user") and typeof(parsed["user"]) == TYPE_DICTIONARY:
			for k in parsed["user"].keys():
				current_user[k] = parsed["user"][k]
	if is_logged_in() and GameState.get_owned_unique_count() == 0:
		GameState.grant_first_login_starter_15_cards()


func _save_auth() -> void:
	var f := FileAccess.open(AUTH_SAVE_PATH, FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify({
			"token": session_token,
			"user": current_user,
		}, "\t"))


func logout() -> void:
	session_token = ""
	current_user = {
		"uid": "local_commander_01",
		"googleId": "",
		"email": "",
		"displayName": "Đại Pháp Sư Lam Long",
		"isGoogleLinked": false,
		"elo": 1200,
	}
	if FileAccess.file_exists(AUTH_SAVE_PATH):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(AUTH_SAVE_PATH))
	emit_signal("auth_state_changed", current_user)
	GameState.emit_signal("screen_requested", "login")


func check_server_health() -> void:
	var http := HTTPRequest.new()
	http.timeout = 2.5
	add_child(http)
	http.request_completed.connect(func(_res: int, code: int, _headers: PackedStringArray, body: PackedByteArray):
		http.queue_free()
		if code == 200:
			var parsed = JSON.parse_string(body.get_string_from_utf8())
			if typeof(parsed) == TYPE_DICTIONARY and parsed.get("ok", false):
				is_online = true
				emit_signal("auth_state_changed", current_user)
				return
		is_online = false
		emit_signal("auth_state_changed", current_user)
	)
	http.request(backend_url + "/api/v1/health")


# ==============================================================================
# 1. GOOGLE OAUTH 1-TAP LOGIN & ACCOUNT SYNC (Online Firebase + Offline Fallback)
# ==============================================================================
func sign_in_with_google_oauth() -> void:
	# 1-Tap Google OAuth Sign-In (No email/password input fields required)
	var device_seed := OS.get_unique_id()
	if device_seed.is_empty():
		device_seed = str(OS.get_name()) + "_arcana_google_oauth"
	var short_hash := "%06d" % (abs(device_seed.hash()) % 900000 + 100000)

	var oauth_email := str(current_user.get("email", "")).strip_edges()
	var oauth_name := str(current_user.get("displayName", "")).strip_edges()

	if OS.has_feature("web"):
		# Check if browser / Firebase Auth injected Google user info in localStorage or window
		var js_email = JavaScriptBridge.eval("window.__ARCANA_GOOGLE_EMAIL__ || localStorage.getItem('arcana_google_email') || ''", true)
		var js_name = JavaScriptBridge.eval("window.__ARCANA_GOOGLE_NAME__ || localStorage.getItem('arcana_google_name') || ''", true)
		if typeof(js_email) == TYPE_STRING and not str(js_email).strip_edges().is_empty():
			oauth_email = str(js_email).strip_edges()
		if typeof(js_name) == TYPE_STRING and not str(js_name).strip_edges().is_empty():
			oauth_name = str(js_name).strip_edges()

	if oauth_email.is_empty():
		oauth_email = "commander.%s@gmail.com" % short_hash
	if oauth_name.is_empty() or oauth_name == "Đại Pháp Sư Lam Long":
		oauth_name = "Google Pháp Sư #%s" % short_hash.substr(0, 4)

	login_with_google(oauth_email, oauth_name)


func login_with_google(email_input: String = "", display_name_input: String = "") -> void:
	var clean_email := email_input.strip_edges()
	if clean_email.is_empty():
		clean_email = "phapsu.nguhanh@gmail.com"
	var clean_name := display_name_input.strip_edges()
	if clean_name.is_empty():
		clean_name = clean_email.split("@")[0].capitalize()

	var had_zero_cards_before := (GameState.get_owned_unique_count() == 0)
	var payload := {
		"googleId": "g_" + str(abs(clean_email.hash())),
		"email": clean_email,
		"displayName": clean_name,
		"platform": OS.get_name().to_lower(),
	}
	if not had_zero_cards_before:
		payload["offlineProfile"] = {
			"gold": GameState.gold,
			"diamonds": GameState.diamonds,
			"ownedCounts": GameState.owned_counts,
			"loadoutDeck": GameState.loadout_deck,
		}

	var http := HTTPRequest.new()
	http.timeout = 4.0
	add_child(http)
	http.request_completed.connect(func(_res: int, code: int, _headers: PackedStringArray, body: PackedByteArray):
		http.queue_free()
		if code == 200:
			var data = JSON.parse_string(body.get_string_from_utf8())
			if typeof(data) == TYPE_DICTIONARY and data.get("ok", false):
				is_online = true
				session_token = str(data.get("token", ""))
				var u: Dictionary = data.get("user", {})
				var is_first := bool(data.get("isFirstLogin", had_zero_cards_before)) or had_zero_cards_before
				current_user = {
					"uid": str(u.get("uid", "google_user")),
					"googleId": str(u.get("googleId", "")),
					"email": str(u.get("email", clean_email)),
					"displayName": str(u.get("displayName", clean_name)),
					"isGoogleLinked": true,
					"elo": int(u.get("elo", 1200)),
				}
				GameState.apply_cloud_profile(u, is_first)
				_save_auth()
				emit_signal("auth_state_changed", current_user)
				emit_signal("login_succeeded", current_user, is_first)
				return

		# Offline Google Account Link Fallback (works 100% offline, gifts 15 starter cards on first login)
		is_online = false
		var gifted_offline := GameState.grant_first_login_starter_15_cards()
		current_user = {
			"uid": "google_" + str(abs(clean_email.hash())),
			"googleId": "g_" + str(abs(clean_email.hash())),
			"email": clean_email,
			"displayName": clean_name,
			"isGoogleLinked": true,
			"elo": 1200,
		}
		_save_auth()
		emit_signal("auth_state_changed", current_user)
		emit_signal("login_succeeded", current_user, gifted_offline or had_zero_cards_before)
	)
	var headers := PackedStringArray(["Content-Type: application/json"])
	var err := http.request(backend_url + "/api/v1/auth/google", headers, HTTPClient.METHOD_POST, JSON.stringify(payload))
	if err != OK:
		http.queue_free()
		var gifted_err := GameState.grant_first_login_starter_15_cards()
		current_user["email"] = clean_email
		current_user["displayName"] = clean_name
		current_user["isGoogleLinked"] = true
		_save_auth()
		emit_signal("auth_state_changed", current_user)
		emit_signal("login_succeeded", current_user, gifted_err or had_zero_cards_before)


func sync_profile_to_cloud() -> void:
	if not is_online:
		return
	var payload := {
		"uid": current_user.get("uid", "local_commander_01"),
		"displayName": current_user.get("displayName", "Đại Pháp Sư"),
		"gold": GameState.gold,
		"diamonds": GameState.diamonds,
		"ownedCounts": GameState.owned_counts,
		"loadoutDeck": GameState.loadout_deck,
	}
	var http := HTTPRequest.new()
	http.timeout = 3.5
	add_child(http)
	http.request_completed.connect(func(_r: int, _c: int, _h: PackedStringArray, _b: PackedByteArray):
		http.queue_free()
	)
	var headers := PackedStringArray(["Content-Type: application/json"])
	if not session_token.is_empty():
		headers.append("Authorization: Bearer " + session_token)
	http.request(backend_url + "/api/v1/profile/sync", headers, HTTPClient.METHOD_POST, JSON.stringify(payload))


# ==============================================================================
# 2. MATCHMAKING (10s Timeout -> Auto-Fill Bots) & CUSTOM ROOMS
# ==============================================================================
func start_quick_matchmaking(player_count: int = 4) -> void:
	local_search_mode = clampi(player_count, 2, 4)
	local_search_type = "matchmaking"
	local_search_elapsed = 0.0
	_poll_accum = 0.0
	is_searching_match = true

	var generated_code := "MM%04d" % (randi() % 9000 + 1000)
	active_room = {
		"roomId": "local_mm_" + str(Time.get_ticks_msec()),
		"roomCode": generated_code,
		"type": "matchmaking",
		"status": "waiting",
		"maxPlayers": local_search_mode,
		"humanCount": 1,
		"botCount": 0,
		"filledWithBots": false,
		"remainingWaitSec": MATCHMAKING_TIMEOUT_SEC,
		"players": [
			{
				"uid": current_user["uid"],
				"displayName": current_user["displayName"],
				"seatIndex": 0,
				"isBot": false,
			}
		],
	}
	emit_signal("matchmaking_updated", active_room)

	var payload := {
		"uid": current_user["uid"],
		"displayName": current_user["displayName"],
		"mode": local_search_mode,
		"loadoutDeck": GameState.loadout_deck,
		"timeoutMs": int(MATCHMAKING_TIMEOUT_SEC * 1000.0),
	}

	var http := HTTPRequest.new()
	http.timeout = 2.5
	add_child(http)
	http.request_completed.connect(func(_res: int, code: int, _headers: PackedStringArray, body: PackedByteArray):
		http.queue_free()
		if code == 200:
			var data = JSON.parse_string(body.get_string_from_utf8())
			if typeof(data) == TYPE_DICTIONARY and data.get("ok", false):
				is_online = true
				active_room = data.get("room", active_room)
				emit_signal("matchmaking_updated", active_room)
				if str(active_room.get("status", "")) == "playing":
					_on_server_room_ready(active_room)
				return
		is_online = false
	)
	var headers := PackedStringArray(["Content-Type: application/json"])
	if not session_token.is_empty():
		headers.append("Authorization: Bearer " + session_token)
	http.request(backend_url + "/api/v1/matchmaking/enqueue", headers, HTTPClient.METHOD_POST, JSON.stringify(payload))


func create_custom_room(player_count: int = 4) -> void:
	local_search_mode = clampi(player_count, 2, 4)
	local_search_type = "custom_room"
	local_search_elapsed = 0.0
	_poll_accum = 0.0
	is_searching_match = true

	var chars := "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
	var code_str := ""
	for _i in range(6):
		code_str += chars[randi() % chars.length()]

	active_room = {
		"roomId": "local_room_" + str(Time.get_ticks_msec()),
		"roomCode": code_str,
		"type": "custom_room",
		"status": "waiting",
		"maxPlayers": local_search_mode,
		"humanCount": 1,
		"botCount": 0,
		"filledWithBots": false,
		"remainingWaitSec": MATCHMAKING_TIMEOUT_SEC,
		"players": [
			{
				"uid": current_user["uid"],
				"displayName": current_user["displayName"],
				"seatIndex": 0,
				"isBot": false,
			}
		],
	}
	emit_signal("matchmaking_updated", active_room)

	var payload := {
		"uid": current_user["uid"],
		"displayName": current_user["displayName"],
		"mode": local_search_mode,
		"loadoutDeck": GameState.loadout_deck,
		"autoStartTimeoutMs": int(MATCHMAKING_TIMEOUT_SEC * 1000.0),
	}

	var http := HTTPRequest.new()
	http.timeout = 2.5
	add_child(http)
	http.request_completed.connect(func(_res: int, code: int, _headers: PackedStringArray, body: PackedByteArray):
		http.queue_free()
		if code == 200:
			var data = JSON.parse_string(body.get_string_from_utf8())
			if typeof(data) == TYPE_DICTIONARY and data.get("ok", false):
				is_online = true
				active_room = data.get("room", active_room)
				emit_signal("matchmaking_updated", active_room)
				return
		is_online = false
	)
	var headers := PackedStringArray(["Content-Type: application/json"])
	http.request(backend_url + "/api/v1/rooms/create", headers, HTTPClient.METHOD_POST, JSON.stringify(payload))


func join_custom_room(room_code_input: String) -> void:
	var clean_code := room_code_input.strip_edges().to_upper()
	if clean_code.is_empty():
		emit_signal("room_error", "Vui lòng nhập Mã Phòng (6 ký tự)!")
		return

	var payload := {
		"uid": current_user["uid"],
		"displayName": current_user["displayName"],
		"roomCode": clean_code,
		"loadoutDeck": GameState.loadout_deck,
	}

	var http := HTTPRequest.new()
	http.timeout = 3.0
	add_child(http)
	http.request_completed.connect(func(_res: int, code: int, _headers: PackedStringArray, body: PackedByteArray):
		http.queue_free()
		if code == 200:
			var data = JSON.parse_string(body.get_string_from_utf8())
			if typeof(data) == TYPE_DICTIONARY and data.get("ok", false):
				is_online = true
				active_room = data.get("room", {})
				local_search_mode = int(active_room.get("maxPlayers", GameState.selected_player_count))
				local_search_type = "custom_room"
				local_search_elapsed = 0.0
				is_searching_match = true
				emit_signal("matchmaking_updated", active_room)
				if str(active_room.get("status", "")) == "playing":
					_on_server_room_ready(active_room)
				return
			elif typeof(data) == TYPE_DICTIONARY:
				emit_signal("room_error", str(data.get("error", "Không tìm thấy phòng!")))
				return
		emit_signal("room_error", "Đang ở chế độ Offline hoặc Mã Phòng '%s' không tồn tại — hãy bấm Tạo Phòng hoặc Ghép Trận!" % clean_code)
	)
	var headers := PackedStringArray(["Content-Type: application/json"])
	http.request(backend_url + "/api/v1/rooms/join", headers, HTTPClient.METHOD_POST, JSON.stringify(payload))


func start_active_room_immediately() -> void:
	if not is_searching_match:
		return
	var r_id := str(active_room.get("roomId", ""))
	if is_online and not r_id.begins_with("local_"):
		var http := HTTPRequest.new()
		http.timeout = 2.5
		add_child(http)
		http.request_completed.connect(func(_res: int, code: int, _headers: PackedStringArray, body: PackedByteArray):
			http.queue_free()
			if code == 200:
				var data = JSON.parse_string(body.get_string_from_utf8())
				if typeof(data) == TYPE_DICTIONARY and data.get("ok", false):
					_on_server_room_ready(data.get("room", active_room))
					return
			_complete_match_with_bot_fallback("host_started_filled_with_bots")
		)
		var headers := PackedStringArray(["Content-Type: application/json"])
		http.request(backend_url + "/api/v1/rooms/start", headers, HTTPClient.METHOD_POST, JSON.stringify({"roomId": r_id}))
	else:
		_complete_match_with_bot_fallback("host_started_filled_with_bots")


func cancel_matchmaking() -> void:
	is_searching_match = false
	local_search_elapsed = 0.0
	if is_online:
		var http := HTTPRequest.new()
		http.timeout = 2.0
		add_child(http)
		http.request_completed.connect(func(_r: int, _c: int, _h: PackedStringArray, _b: PackedByteArray):
			http.queue_free()
		)
		var headers := PackedStringArray(["Content-Type: application/json"])
		http.request(backend_url + "/api/v1/matchmaking/cancel", headers, HTTPClient.METHOD_POST, JSON.stringify({"uid": current_user["uid"]}))
	active_room = {}
	emit_signal("matchmaking_updated", active_room)


func _poll_room_status_from_server() -> void:
	var r_id := str(active_room.get("roomId", ""))
	if r_id.is_empty() or r_id.begins_with("local_"):
		return
	var http := HTTPRequest.new()
	http.timeout = 2.0
	add_child(http)
	http.request_completed.connect(func(_res: int, code: int, _headers: PackedStringArray, body: PackedByteArray):
		http.queue_free()
		if not is_searching_match:
			return
		if code == 200:
			var data = JSON.parse_string(body.get_string_from_utf8())
			if typeof(data) == TYPE_DICTIONARY and data.get("ok", false):
				var srv_room: Dictionary = data.get("room", {})
				active_room = srv_room
				emit_signal("matchmaking_updated", active_room)
				if str(srv_room.get("status", "")) == "playing":
					_on_server_room_ready(srv_room)
	)
	http.request(backend_url + "/api/v1/matchmaking/status?roomId=" + r_id.uri_encode())


func _on_server_room_ready(room_data: Dictionary) -> void:
	if not is_searching_match:
		return
	is_searching_match = false
	active_room = room_data
	GameState.selected_player_count = int(room_data.get("maxPlayers", local_search_mode))
	emit_signal("matchmaking_updated", active_room)
	emit_signal("matchmaking_started_battle", active_room)


func _complete_match_with_bot_fallback(reason: String) -> void:
	if not is_searching_match:
		return
	is_searching_match = false

	var bot_names := [
		"Bot Huyết Ma Vương",
		"Bot Cổ Thụ Đại Drui",
		"Bot Thái Dương Thánh Kỵ",
	]
	var players: Array = active_room.get("players", [])
	if players.is_empty():
		players.append({
			"uid": current_user["uid"],
			"displayName": current_user["displayName"],
			"seatIndex": 0,
			"isBot": false,
		})

	var cur_cnt := players.size()
	for seat in range(cur_cnt, local_search_mode):
		players.append({
			"uid": "bot_seat_%d" % seat,
			"displayName": bot_names[(seat - 1) % bot_names.size()],
			"seatIndex": seat,
			"isBot": true,
		})

	active_room["players"] = players
	active_room["humanCount"] = 1
	active_room["botCount"] = maxi(0, local_search_mode - 1)
	active_room["filledWithBots"] = active_room["botCount"] > 0
	active_room["status"] = "playing"
	active_room["startReason"] = reason
	active_room["remainingWaitSec"] = 0.0

	GameState.selected_player_count = local_search_mode
	log_analytics_event("matchmaking_started", {
		"mode": local_search_mode,
		"reason": reason,
		"filled_with_bots": active_room["filledWithBots"],
	})
	emit_signal("matchmaking_updated", active_room)
	emit_signal("matchmaking_started_battle", active_room)


# ==============================================================================
# 3. FIREBASE ANALYTICS & CRASHLYTICS TELEMETRY
# ==============================================================================
func log_analytics_event(event_name: String, params: Dictionary = {}) -> void:
	if not is_online:
		return
	var http := HTTPRequest.new()
	http.timeout = 2.5
	add_child(http)
	http.request_completed.connect(func(_r: int, _c: int, _h: PackedStringArray, _b: PackedByteArray):
		http.queue_free()
	)
	var payload := {
		"name": event_name,
		"uid": current_user.get("uid", "anonymous"),
		"platform": OS.get_name().to_lower(),
		"params": params,
	}
	var headers := PackedStringArray(["Content-Type: application/json"])
	http.request(backend_url + "/api/v1/telemetry/analytics", headers, HTTPClient.METHOD_POST, JSON.stringify(payload))


func report_crash(message: String, stack_trace: String = "") -> void:
	if not is_online:
		return
	var http := HTTPRequest.new()
	http.timeout = 2.5
	add_child(http)
	http.request_completed.connect(func(_r: int, _c: int, _h: PackedStringArray, _b: PackedByteArray):
		http.queue_free()
	)
	var payload := {
		"uid": current_user.get("uid", "anonymous"),
		"message": message,
		"stackTrace": stack_trace,
		"platform": OS.get_name().to_lower(),
	}
	var headers := PackedStringArray(["Content-Type: application/json"])
	http.request(backend_url + "/api/v1/telemetry/crash", headers, HTTPClient.METHOD_POST, JSON.stringify(payload))
