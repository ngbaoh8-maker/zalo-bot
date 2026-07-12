import time
import threading
import os
from zlapi.models import Message

# ================= INFO =================
des = {
    "version": "1.0.1",
    "credits": "ngbao",
    "description": "Gửi tin nhắn chọc từ file .txt (gửi đến khi tắt).",
    "power": "Thành Viên"
}

# ================= PATH =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TXT_PATH = os.path.join(BASE_DIR, "cache", "choc.txt")

RUNNING = False
THREAD = None

# ================= LOAD FILE =================
def load_lines():
    try:
        with open(TXT_PATH, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
            print("[CHOC] loaded:", len(lines))
            return lines
    except Exception as e:
        print("[CHOC] load error:", e)
        return []

# ================= LOOP SEND =================
def loop_send(client, message_object, thread_id, thread_type, lines, tag_name):
    global RUNNING
    idx = 0
    total = len(lines)

    print("[CHOC] loop start")

    while RUNNING and total > 0:
        base_text = lines[idx]
        full_text = base_text + "\n@" + tag_name

        print("[CHOC] sending:", full_text)

        try:
            client.replyMessage(
                Message(text=full_text),
                message_object,
                thread_id,
                thread_type
            )
        except Exception as e:
            print("[CHOC] send error:", e)

        idx = (idx + 1) % total
        time.sleep(2)

# ================= COMMAND =================
def handle_choc(message, message_object, thread_id, thread_type, author_id, client):
    global RUNNING, THREAD

    if RUNNING:
        client.replyMessage(
            Message(text="⚠️ Dang choc roi, dung /dungchoc de tat"),
            message_object,
            thread_id,
            thread_type
        )
        return

    lines = load_lines()
    if not lines:
        client.replyMessage(
            Message(text="❌ File choc.txt trong hoac loi"),
            message_object,
            thread_id,
            thread_type
        )
        return

    target_id = author_id
    if message_object.mentions:
        target_id = message_object.mentions[0]["uid"]

    user_info = client.fetchUserInfo(target_id)
    if hasattr(user_info, "changed_profiles") and str(target_id) in user_info.changed_profiles:
        tag_name = user_info.changed_profiles[str(target_id)].get("zaloName", "ban")
    else:
        tag_name = getattr(user_info, "name", "ban")

    RUNNING = True
    THREAD = threading.Thread(
        target=loop_send,
        args=(client, message_object, thread_id, thread_type, lines, tag_name),
        daemon=True
    )
    THREAD.start()

    client.replyMessage(
        Message(text="😏 Da bat dau choc (dung /dungchoc de dung)"),
        message_object,
        thread_id,
        thread_type
    )

def handle_dungchoc(message, message_object, thread_id, thread_type, author_id, client):
    global RUNNING
    RUNNING = False
    client.replyMessage(
        Message(text="🙂 Da dung choc"),
        message_object,
        thread_id,
        thread_type
    )

# ================= EXPORT =================
def PTA():
    return {
        "choc": handle_choc,
        "dungchoc": handle_dungchoc
    }