import os
import json
import random
import threading
import time
from datetime import datetime, timedelta
from zlapi.models import Message, ThreadType

des = {
    "version": "1.3.0",
    "credits": "ngbao",
    "description": "Tự động gửi text theo giờ định sẵn, có emoji & timestamp.",
    "power": "Thành viên"
}

DATA_PATH = "modules/cache/autosend_text.json"
TIMEZONE_OFFSET = 7  # Asia/Ho_Chi_Minh UTC+7

CLOCK_EMOJIS = ["⌚", "🕰️", "📧", "⏳", "⏲️", "⏰", "⏱️", "🕛", "🛎️", "🗓️"]
FUN_EMOJIS = list("😁🤠❤️💕👐💐🌵🏜️🌚🌒🐺🐴🐗🌖🦢🐬🦐🐛🍌🍠🍗🥫🚲🚎🚔🚠🚤")


# ================== HỖ TRỢ ==================
def load_data():
    if os.path.exists(DATA_PATH):
        try:
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_data(data):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def format_times(times):
    return ", ".join(times) if times else "Không có"


# ================== LỆNH CHÍNH ==================
def handle_autosendtext_command(message, message_object, thread_id, thread_type, author_id, client):
    args = message.strip().split(" ", 2)
    if not args or args[0] != ".atst":
        return

    data = load_data()
    gid = str(thread_id)

    if gid not in data:
        data[gid] = {"on": False, "text": "", "times": []}

    cmd = args[1] if len(args) > 1 else ""

    # --- MENU ---
    if cmd == "":
        info = data[gid]
        status = "🟢 Bật" if info["on"] else "🔴 Tắt"
        times = format_times(info["times"])
        text = info["text"] if info["text"] else "(chưa đặt)"
        response_message = (
            f"🌙 AutoSend Text\n"
            f"Trạng thái: {status}\n"
            f"Nội dung: {text}\n"
            f"Khung giờ: {times}\n\n"
            f"Lệnh sử dụng:\n"
            f"> .atst set <nội_dung>\n"
            f"> .atst dl <03:30,04:30,...>\n"
            f"> .atst on / .atst off"
        )
        client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=10000)
        return

    # --- SET NỘI DUNG ---
    if cmd == "set":
        if len(args) < 3:
            client.replyMessage(Message(text="❗ Dùng: .atst set <nội_dung>"), message_object, thread_id, thread_type, ttl=5000)
            return
        content = args[2]
        data[gid]["text"] = content
        save_data(data)
        client.replyMessage(Message(text=f"✅ Đã đặt nội dung autosend: {content}"), message_object, thread_id, thread_type, ttl=5000)
        return

    # --- ĐẶT GIỜ ---
    if cmd == "dl":
        if len(args) < 3:
            client.replyMessage(Message(text="❗ Dùng: .atst dl 03:30,04:30,..."), message_object, thread_id, thread_type, ttl=5000)
            return
        times = [t.strip() for t in args[2].split(",") if ":" in t]
        data[gid]["times"] = times
        save_data(data)
        client.replyMessage(Message(text=f"✅ Đã đặt khung giờ: {format_times(times)}"), message_object, thread_id, thread_type, ttl=5000)
        return

    # --- BẬT / TẮT ---
    if cmd.lower() == "on":
        data[gid]["on"] = True
        save_data(data)
        client.replyMessage(Message(text="✅ Đã bật autosend text."), message_object, thread_id, thread_type, ttl=5000)
        return

    elif cmd.lower() == "off":
        data[gid]["on"] = False
        save_data(data)
        client.replyMessage(Message(text="🛑 Đã tắt autosend text."), message_object, thread_id, thread_type, ttl=5000)
        return

    else:
        client.replyMessage(Message(text="❓ Lệnh không hợp lệ. Gõ .atst để xem hướng dẫn."), message_object, thread_id, thread_type, ttl=5000)


# ================== LUỒNG TỰ GỬI ==================
def auto_send_loop(client):
    while True:
        now = datetime.utcnow() + timedelta(hours=TIMEZONE_OFFSET)
        current_time = now.strftime("%H:%M")
        data = load_data()

        for gid, info in data.items():
            if not info.get("on"):
                continue
            if current_time in info.get("times", []) and info.get("text"):
                try:
                    clock = random.choice(CLOCK_EMOJIS)
                    fun = random.choice(FUN_EMOJIS)
                    time_str = now.strftime("%H:%M")
                    bot_name = getattr(client.me, "name", "Bot")

                    message = f"{info['text']}\n{clock} {time_str} -- Bot {bot_name} autosend {fun}"
                    client.sendMessage(Message(text=message), int(gid), ThreadType.GROUP)
                except Exception as e:
                    print(f"[AutoSend lỗi] Nhóm {gid}: {e}")

        time.sleep(60)


def start_autosend_thread(client):
    t = threading.Thread(target=auto_send_loop, args=(client,), daemon=True)
    t.start()


# ================== TRẢ LỆNH ==================
def PTA():
    return {
        "atst": handle_autosendtext_command
    }
