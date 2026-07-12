import requests
import re
import json
import os
from zlapi.models import Message
from config import PREFIX, ADMIN

des = {
    "version": "1.2.0",
    "credits": "ngbao",
    "description": "Check LIVE / DIE Facebook + thông báo",
    "power": "Admin"
}

API_URL = "https://adidaphat.site/facebook/getinfo"
API_KEY = "apikeysumi"
DATA_FILE = "modules/cache/fblive_data.json"

# ================= UTILS =================
def extract_fb_id(text):
    if "facebook.com" in text:
        m = re.search(r"facebook.com/([^/?]+)", text)
        if m:
            return m.group(1)
    return text.strip()

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ================= CHECK LIVE =================
def check_fb_live(uid):
    try:
        r = requests.get(
            API_URL,
            params={"uid": uid, "apikey": API_KEY},
            timeout=15
        ).json()
    except:
        return False

    if isinstance(r, dict) and (r.get("uid") or r.get("name")):
        return True
    return False

# ================= MAIN =================
def handle_fblive(message, message_object, thread_id, thread_type, author_id, client):
    if str(author_id) != str(ADMIN):
        client.replyMessage(
            Message(text="❌ Lệnh này chỉ ADMIN mới dùng được"),
            message_object, thread_id, thread_type
        )
        return

    args = message.split()
    if len(args) < 2:
        client.replyMessage(
            Message(text=f"❌ Dùng:\n"
                         f"{PREFIX}fblive <uid>\n"
                         f"{PREFIX}fblive on <uid>\n"
                         f"{PREFIX}fblive off <uid>"),
            message_object, thread_id, thread_type
        )
        return

    data = load_data()

    # ===== BẬT / TẮT =====
    if args[1] in ["on", "off"]:
        if len(args) < 3:
            client.replyMessage(
                Message(text="❌ Thiếu UID Facebook"),
                message_object, thread_id, thread_type
            )
            return

        uid = extract_fb_id(args[2])

        if args[1] == "on":
            live = check_fb_live(uid)
            data[uid] = {
                "status": "LIVE" if live else "DIE",
                "thread_id": thread_id,
                "thread_type": thread_type
            }
            save_data(data)
            client.replyMessage(
                Message(text=f"✅ Đã bật theo dõi FB `{uid}`"),
                message_object, thread_id, thread_type
            )
        else:
            if uid in data:
                del data[uid]
                save_data(data)
            client.replyMessage(
                Message(text=f"🛑 Đã tắt theo dõi FB `{uid}`"),
                message_object, thread_id, thread_type
            )
        return

    # ===== CHECK 1 LẦN =====
    uid = extract_fb_id(args[1])
    live = check_fb_live(uid)

    client.replyMessage(
        Message(
            text=(
                "🟢 FACEBOOK LIVE" if live else "🔴 FACEBOOK DIE"
            ) + f"\n👤 UID: {uid}"
        ),
        message_object, thread_id, thread_type
    )

# ================= AUTO SCAN =================
def auto_scan_fblive(client):
    data = load_data()
    changed = False

    for uid, info in data.items():
        old_status = info.get("status")
        new_status = "LIVE" if check_fb_live(uid) else "DIE"

        if new_status != old_status:
            text = (
                f"📢 FACEBOOK TRẠNG THÁI THAY ĐỔI\n\n"
                f"👤 UID: {uid}\n"
                f"{'🟢 LIVE' if new_status == 'LIVE' else '🔴 DIE'}"
            )
            client.sendMessage(
                Message(text=text),
                info["thread_id"],
                info["thread_type"]
            )
            data[uid]["status"] = new_status
            changed = True

    if changed:
        save_data(data)

# ================= REGISTER =================
def TQuan():
    return {
        "fblive": handle_fblive
    }