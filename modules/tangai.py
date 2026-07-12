import time
import threading
from zlapi.models import Message

# ================= INFO =================
des = {
    "version": "1.1.0",
    "credits": "ngbao",
    "description": "Chế độ sĩ từ file txt (gửi lặp lại đến khi /dungsi)",
    "power": "Thành viên"
}

TXT_PATH = "modules/cache/tangai.txt"

RUNNING = False
THREAD = None


# ================= READ FILE TXT =================
def load_lines():
    try:
        with open(TXT_PATH, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
            return lines
    except Exception as e:
        print("[TangAi] Lỗi đọc file:", e)
        return []


# ================= LOOP SENDER =================
def loop_send(client, thread_id, thread_type, lines, tag_name, tag_uid):
    global RUNNING

    idx = 0
    total = len(lines)

    while RUNNING and total > 0:

        base_text = lines[idx]
        tag_text = f"@{tag_name}"
        full_text = base_text + "\n" + tag_text

        offset = len(base_text) + 1
        length = len(tag_text)

        try:
            client.sendMessage(
                Message(
                    text=full_text,
                    mentions=[{
                        "uid": tag_uid,
                        "offset": offset,
                        "length": length
                    }]
                ),
                thread_id=thread_id,
                thread_type=thread_type
            )
        except Exception as e:
            print("[TangAi] lỗi send:", e)

        idx = (idx + 1) % total

        time.sleep(2)  # chờ 2s rồi gửi tin tiếp


# ================= COMMAND START =================
def handle_tangai(message, message_object, thread_id, thread_type, author_id, client):
    global RUNNING, THREAD

    if RUNNING:
        client.sendMessage(
            Message(text="⚠️ Bot đang sĩ rồi, dùng /dungsi để tắt ❗"),
            thread_id=thread_id,
            thread_type=thread_type
        )
        return

    lines = load_lines()

    if not lines:
        client.sendMessage(
            Message(text="❌ File tangai.txt trống hoặc không đọc được ❗"),
            thread_id=thread_id,
            thread_type=thread_type
        )
        return

    # chọn uid để tag
    target_id = author_id
    if message_object.mentions:
        if isinstance(message_object.mentions[0], dict):
            target_id = message_object.mentions[0].get("uid", author_id)

    # fetch userinfo
    try:
        user_info = client.fetchUserInfo(target_id)
    except:
        user_info = None

    tag_name = "bạn"

    try:
        if (
            user_info and 
            hasattr(user_info, "changed_profiles") and 
            str(target_id) in user_info.changed_profiles
        ):
            tag_name = user_info.changed_profiles[str(target_id)].get("zaloName", "bạn")
        elif user_info and hasattr(user_info, "name"):
            tag_name = user_info.name
    except:
        pass

    RUNNING = True

    THREAD = threading.Thread(
        target=loop_send,
        args=(client, thread_id, thread_type, lines, tag_name, target_id),
        daemon=True
    )
    THREAD.start()

    client.sendMessage(
        Message(text=f"🚀 Bắt đầu sĩ @{tag_name} rồi 🤭 (dùng /dungsi để dừng)"),
        thread_id=thread_id,
        thread_type=thread_type
    )


# ================= COMMAND STOP =================
def handle_dungsi(message, message_object, thread_id, thread_type, author_id, client):
    global RUNNING
    RUNNING = False

    client.sendMessage(
        Message(text="😓 Đã dừng sĩ ❌"),
        thread_id=thread_id,
        thread_type=thread_type
    )


# ================= EXPORT =================
def PTA():
    return {
        "tangai": handle_tangai,
        "dungsi": handle_dungsi
    }
