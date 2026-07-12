import threading
import time
from zlapi.models import Message

des = {
    "version": "1.0.0",
    "credits": "ngbao",
    "description": "Spam từ khóa theo box (on/off)",
    "power": "Quản trị viên Bot"
}

# ================= DATA =================
spam_tasks = {}  # thread_id -> task info

# ================= SPAM LOOP =================
def spam_loop(client, thread_id):
    while spam_tasks.get(thread_id, {}).get("running"):
        data = spam_tasks.get(thread_id)
        if not data:
            break

        try:
            client.sendMessage(
                Message(text=data["text"]),
                thread_id,
                thread_type=1
            )
        except:
            pass

        time.sleep(data["delay"])

# ================= COMMAND =================
def handle_spam(message, message_object, thread_id, thread_type, author_id, client):
    args = message.strip().split()
    tid = str(thread_id)

    if len(args) < 2:
        client.replyMessage(
            Message(
                text=(
                    "📌 SPAM TỪ KHÓA\n\n"
                    "Dùng:\n"
                    "spam <nội dung> | <delay>\n"
                    "spam stop\n\n"
                    "VD:\n"
                    "spam hello | 3"
                )
            ),
            message_object,
            thread_id,
            thread_type
        )
        return

    # ===== STOP =====
    if args[1].lower() == "stop":
        if tid in spam_tasks:
            spam_tasks[tid]["running"] = False
            spam_tasks.pop(tid, None)
            msg = "🛑 Đã DỪNG spam cho box này"
        else:
            msg = "⚠️ Box này chưa spam"
        client.replyMessage(Message(text=msg), message_object, thread_id, thread_type)
        return

    # ===== START =====
    raw = message[len("spam"):].strip()

    if "|" not in raw:
        client.replyMessage(
            Message(text="⚠️ Sai định dạng\nVD: spam hello | 3"),
            message_object,
            thread_id,
            thread_type
        )
        return

    text, delay = raw.split("|", 1)
    text = text.strip()
    delay = delay.strip()

    if not delay.isdigit():
        client.replyMessage(
            Message(text="⚠️ Delay phải là số (giây)"),
            message_object,
            thread_id,
            thread_type
        )
        return

    delay = max(1, int(delay))  # tối thiểu 1s

    # nếu đang spam thì stop cũ
    if tid in spam_tasks:
        spam_tasks[tid]["running"] = False

    spam_tasks[tid] = {
        "text": text,
        "delay": delay,
        "running": True
    }

    t = threading.Thread(
        target=spam_loop,
        args=(client, tid),
        daemon=True
    )
    t.start()

    client.replyMessage(
        Message(
            text=(
                "✅ ĐÃ BẮT ĐẦU SPAM\n"
                f"• Nội dung: {text}\n"
                f"• Delay: {delay}s\n\n"
                "Dừng bằng: spam stop"
            )
        ),
        message_object,
        thread_id,
        thread_type
    )

# ================= PTA =================
def PTA():
    return {
        "spam2": handle_spam
    }