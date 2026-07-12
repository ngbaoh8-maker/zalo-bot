import os
import json
import requests
from zlapi import Message

# -------- CONFIG --------
API_URL = "https://wsapi.simsimi.com/190410/talk"
DEFAULT_LANG = "vi"
API_KEY = "YOUR_API_KEY_HERE"   # thay bằng API key của bạn

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "simsimi_settings.json")

# -------- SETTINGS --------
def _load_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    except Exception:
        return {}

def _save_settings(data):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Simsimi] Lỗi lưu settings: {e}")

def is_simsimi_enabled(bot_uid, thread_id):
    data = _load_settings()
    per_bot = data.get(str(bot_uid), {})
    return bool(per_bot.get(str(thread_id), {}).get("enabled", False))

def set_simsimi_enabled(bot_uid, thread_id, enabled: bool):
    data = _load_settings()
    per_bot = data.get(str(bot_uid), {})
    if not isinstance(per_bot, dict):
        per_bot = {}
    settings = per_bot.get(str(thread_id), {})
    settings["enabled"] = bool(enabled)
    per_bot[str(thread_id)] = settings
    data[str(bot_uid)] = per_bot
    _save_settings(data)

def get_simsimi_mode(bot_uid, thread_id):
    data = _load_settings()
    per_bot = data.get(str(bot_uid), {})
    settings = per_bot.get(str(thread_id), {})
    return settings.get("mode", 1)

def set_simsimi_mode(bot_uid, thread_id, mode: int):
    data = _load_settings()
    per_bot = data.get(str(bot_uid), {})
    if not isinstance(per_bot, dict):
        per_bot = {}
    settings = per_bot.get(str(thread_id), {})
    settings["mode"] = int(mode)
    per_bot[str(thread_id)] = settings
    data[str(bot_uid)] = per_bot
    _save_settings(data)

# -------- SEND MESSAGE SAFELY --------
def _safe_send(bot, text, message_object, thread_id, thread_type):
    try:
        bot.replyMessage(Message(text=text), message_object, thread_id=thread_id, thread_type=thread_type)
    except Exception:
        try:
            bot.sendMessage(text, thread_id, thread_type)
        except Exception as e:
            print(f"[Simsimi] Không gửi được tin nhắn: {e}")

# -------- EXTRACT TEXT --------
def _extract_text_from_inputs(message, message_object):
    if isinstance(message, str) and message.strip():
        return message.strip()
    if hasattr(message, "text"):
        try:
            return message.text.strip()
        except Exception:
            pass
    if isinstance(message_object, str) and message_object.strip():
        return message_object.strip()
    if hasattr(message_object, "text"):
        try:
            return message_object.text.strip()
        except Exception:
            pass
    return ""

# -------- CALL SIMSIMI API --------
def _call_simsimi_api(query_text, lang=DEFAULT_LANG):
    if not query_text:
        raise ValueError("query_text không được rỗng")

    data = {"utext": query_text, "lang": lang}
    headers = {"Content-Type": "application/json", "x-api-key": API_KEY}

    resp = requests.post(API_URL, json=data, headers=headers, timeout=10)
    resp.raise_for_status()
    try:
        result = resp.json()
    except Exception:
        return resp.text

    if "atext" in result:
        return result["atext"]
    if "success" in result:
        return result["success"]
    return json.dumps(result, ensure_ascii=False)

# -------- PERSONALITY --------
def _apply_personality(reply, mode):
    if mode == 2:  # hung dữ
        return f"😡 {reply}! Nói chuyện cho đàng hoàng coi."
    elif mode == 3:  # vợ quốc dân
        return f"💖 {reply} ~ Em luôn ở bên cạnh anh nhé."
    elif mode == 4:  # chồng
        return f"🤵 {reply}. Anh sẽ luôn bảo vệ em."
    return reply  # bình thường

# -------- HANDLE COMMAND --------
def handle_simsimi_command(message, message_object, thread_id, thread_type, author_id, bot, prefix=None):
    try:
        if prefix is None:
            prefix = getattr(bot, "prefix", "") or ""

        text = _extract_text_from_inputs(message, message_object)
        if not text:
            return

        text_stripped = text.strip()
        text_lower = text_stripped.lower()
        trigger = f"{prefix}sim" if prefix else "sim"

        # --- command ---
        if text_lower.startswith(trigger):
            tail = text_stripped[len(trigger):].strip().lower()

            if tail in ("on", "bật", "enable"):
                set_simsimi_enabled(bot.uid, thread_id, True)
                _safe_send(bot, "✅ Đã bật Simsimi cho cuộc trò chuyện này.", message_object, thread_id, thread_type)
                return

            if tail in ("off", "tắt", "disable"):
                set_simsimi_enabled(bot.uid, thread_id, False)
                _safe_send(bot, "✅ Đã tắt Simsimi cho cuộc trò chuyện này.", message_object, thread_id, thread_type)
                return

            if tail.startswith("mode"):
                try:
                    mode_num = int(tail.replace("mode", "").strip())
                    if mode_num in (1, 2, 3, 4):
                        set_simsimi_mode(bot.uid, thread_id, mode_num)
                        _safe_send(bot, f"🔄 Đã đổi Simsimi sang mode {mode_num}.", message_object, thread_id, thread_type)
                    else:
                        _safe_send(bot, "⚠️ Mode không hợp lệ (chọn 1-4).", message_object, thread_id, thread_type)
                except Exception:
                    _safe_send(bot, "⚠️ Sai cú pháp. Dùng: sim mode <1-4>", message_object, thread_id, thread_type)
                return

            if tail in ("help", "?"):
                help_text = (
                    "🤖 **Hướng dẫn dùng Simsimi**\n\n"
                    f"{trigger} on / off → Bật hoặc tắt Simsimi trong nhóm\n"
                    f"{trigger} → Xem trạng thái hiện tại (bật/tắt)\n"
                    f"{trigger} mode <số> → Đổi phong cách trả lời\n\n"
                    "📌 Các mode có sẵn:\n"
                    "1️⃣ Bình thường\n"
                    "2️⃣ Hung dữ (gắt gỏng)\n"
                    "3️⃣ Vợ quốc dân (hiền dịu)\n"
                    "4️⃣ Người chồng (ấm áp)\n"
                )
                _safe_send(bot, help_text, message_object, thread_id, thread_type)
                return

            if tail == "":
                status = is_simsimi_enabled(bot.uid, thread_id)
                mode = get_simsimi_mode(bot.uid, thread_id)
                _safe_send(bot, f"🔔 Simsimi đang {'bật' if status else 'tắt'} (mode {mode}).", message_object, thread_id, thread_type)
                return

        # --- check ---
        mentioned = f"@{getattr(bot, 'uid', '')}" in text
        if not is_simsimi_enabled(bot.uid, thread_id) and not text_lower.startswith(trigger) and not mentioned:
            return

        # --- content ---
        if text_lower.startswith(trigger):
            content = text_stripped[len(trigger):].strip()
        elif mentioned:
            content = text_stripped.replace(f"@{bot.uid}", "").strip()
        else:
            content = text_stripped

        if not content:
            _safe_send(bot, "⚠️ Vui lòng nhập câu hỏi để Simsimi trả lời.", message_object, thread_id, thread_type)
            return

        # --- API call ---
        try:
            reply = _call_simsimi_api(content, lang=DEFAULT_LANG)
            if not reply:
                reply = "⚠️ Simsimi không trả lời (rỗng)."
            mode = get_simsimi_mode(bot.uid, thread_id)
            reply = _apply_personality(reply, mode)
            _safe_send(bot, reply, message_object, thread_id, thread_type)
        except Exception as e:
            _safe_send(bot, f"⚠️ Lỗi khi gọi Simsimi: {e}", message_object, thread_id, thread_type)

    except Exception as e:
        try:
            bot.sendMessage(f"[Simsimi] Lỗi nội bộ: {e}", thread_id, thread_type)
        except Exception:
            print(f"[Simsimi] Lỗi khi xử lý: {e}")
