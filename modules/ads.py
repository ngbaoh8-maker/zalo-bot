import time
import threading
import json
from zlapi.models import Message, ThreadType
from config import ADMIN

des = {
    "version": "1.0.3",
    "credits": "ngbao",
    "description": "Auto rải ADS",
    "power": "Quyền Admin"
}

ADS_FILE = "ads_config.json"
ads_running = False
ads_thread = None
json_lock = threading.Lock()
TTL = 120000

def is_admin(author_id):
    return str(author_id) == str(ADMIN)

def load_config():
    with json_lock:
        try:
            with open(ADS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            default = {
                "message": ["Auto ADS đang chạy..."],   # ← giờ là LIST
                "delay": 10,
                "card_enabled": False,
                "card_user": None,
                "card_phone": None
            }
            with open(ADS_FILE, "w", encoding="utf-8") as f:
                json.dump(default, f, indent=2, ensure_ascii=False)
            return default

def save_config(config):
    with json_lock:
        with open(ADS_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

def get_user_name(client, author_id):
    try:
        user_info = client.fetchUserInfo(author_id)
        author_info = user_info.changed_profiles.get(author_id, {}) if user_info and user_info.changed_profiles else {}
        return author_info.get("zaloName", "Không xác định")
    except:
        return "Không xác định"

def loop_ads(client):
    global ads_running
    while ads_running:
        config = load_config()

        # Nếu message là list → ghép bằng xuống dòng
        msg_send = "\n".join(config.get("message", []))

        try:
            all_groups = list(client.fetchAllGroups().gridVerMap.keys())
        except Exception as e:
            print(f"[ADS] Lỗi fetchAllGroups: {e}")
            all_groups = []

        for gid in all_groups:
            try:
                client.sendMessage(
                    Message(text=msg_send),
                    thread_id=gid,
                    thread_type=ThreadType.GROUP
                )

                if config.get("card_enabled") and config.get("card_user") and config.get("card_phone"):
                    try:
                        client.sendBusinessCard(
                            userId=config["card_user"],
                            phone=config["card_phone"],
                            thread_id=gid,
                            thread_type=ThreadType.GROUP
                        )
                    except:
                        pass

            except Exception as e:
                print(f"[ADS] Lỗi gửi nhóm {gid}: {e}")

        time.sleep(config.get("delay", 10))

def handle_ads(message, message_object, thread_id, thread_type, author_id, client):
    global ads_running, ads_thread
    name = get_user_name(client, author_id)

    if not is_admin(author_id):
        client.replyMessage(Message(text=f"{name}\n➜Bạn không có quyền sử dụng lệnh này. 🚦"), message_object, thread_id, thread_type, ttl=TTL)
        return

    args = message.strip().split()

    if len(args) < 2:
        client.replyMessage(Message(text=f"{name}\n➜Lệnh ADS: start | stop | setmsg | delay <giây> | setcard <id> <text> | card | info"), message_object, thread_id, thread_type, ttl=TTL)
        return

    cmd = args[1].lower()
    config = load_config()

    if cmd == "start":
        if ads_running:
            client.replyMessage(Message(text=f"{name}\n➜Auto ADS đang chạy."), message_object, thread_id, thread_type, ttl=TTL)
            return
        ads_running = True
        ads_thread = threading.Thread(target=loop_ads, args=(client,), daemon=True)
        ads_thread.start()
        client.replyMessage(Message(text=f"{name}\n➜Đã bật Auto ADS."), message_object, thread_id, thread_type, ttl=TTL)

    elif cmd == "stop":
        ads_running = False
        client.replyMessage(Message(text=f"{name}\n➜Đã tắt Auto ADS."), message_object, thread_id, thread_type, ttl=TTL)

    elif cmd == "setmsg":
        # LẤY TOÀN BỘ PHẦN SAU "ads setmsg" GIỮ NGUYÊN XUỐNG DÒNG
        raw = message.split("\n")[1:]  # bỏ dòng đầu chứa lệnh
        lines = [l for l in raw if l.strip() != ""]

        if not lines:
            client.replyMessage(Message(text=f"{name}\n➜Bạn phải nhập nội dung nhiều dòng sau lệnh."), message_object, thread_id, thread_type, ttl=TTL)
            return

        config["message"] = lines
        save_config(config)

        client.replyMessage(Message(text=f"{name}\n➜Đã cập nhật nội dung ADS (đa dòng)."), message_object, thread_id, thread_type, ttl=TTL)

    elif cmd == "delay":
        if len(args) < 3 or not args[2].isdigit():
            client.replyMessage(Message(text=f"{name}\n➜Dùng: ads delay <giây>"), message_object, thread_id, thread_type, ttl=TTL)
            return
        config["delay"] = int(args[2])
        save_config(config)
        client.replyMessage(Message(text=f"{name}\n➜Đã đổi delay thành {args[2]} giây."), message_object, thread_id, thread_type, ttl=TTL)

    elif cmd == "setcard":
        if len(args) < 4:
            client.replyMessage(Message(text=f"{name}\n➜Dùng: ads setcard <id_user> <phone/text>"), message_object, thread_id, thread_type, ttl=TTL)
            return
        config["card_user"] = args[2]
        config["card_phone"] = " ".join(args[3:])
        save_config(config)
        client.replyMessage(Message(text=f"{name}\n➜Đã đặt danh thiếp cho user {args[2]}."), message_object, thread_id, thread_type, ttl=TTL)

    elif cmd == "card":
        config["card_enabled"] = not config.get("card_enabled", False)
        save_config(config)
        status_text = "bật" if config["card_enabled"] else "tắt"
        client.replyMessage(Message(text=f"{name}\n➜Đã {status_text} gửi danh thiếp!"), message_object, thread_id, thread_type, ttl=TTL)

    elif cmd == "info":
        try:
            all_groups = list(client.fetchAllGroups().gridVerMap.keys())
        except:
            all_groups = []

        msg = f"{name}\n➜Thông tin ADS:\n" \
              f"- Trạng thái: {'Đang chạy' if ads_running else 'Đã tắt'}\n" \
              f"- Số nhóm: {len(all_groups)}\n" \
              f"- Nội dung:\n" + "\n".join(config.get("message", [])) + "\n" \
              f"- Delay: {config.get('delay',10)} giây\n" \
              f"- Danh thiếp: {'Bật' if config.get('card_enabled') else 'Tắt'}\n" \
              f"- User Card: {config.get('card_user') or 'Chưa đặt'}\n" \
              f"- Phone/Note: {config.get('card_phone') or 'Chưa đặt'}"

        client.replyMessage(Message(text=msg), message_object, thread_id, thread_type, ttl=TTL)

    else:
        client.replyMessage(Message(text=f"{name}\n➜Lệnh không hợp lệ."), message_object, thread_id, thread_type, ttl=TTL)

def PTA():
    return {
        "ads": handle_ads
    }