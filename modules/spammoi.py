from zlapi.models import Message
import requests
import time
import threading

des = {
    "version": "1.0.0",
    "credits": "ngbao",
    "description": "Spam Xin Vào Đội FF",
    "power": "Thành Viên"
}

API_URL = "http://103.157.204.204:4000/spam="
COOLDOWN_MS = 10000
TTL = 60000

queue = []
is_processing = False
threadCooldowns = {}
lock = threading.Lock()

def spamUid(uid):
    try:
        url = f"{API_URL}{uid}"
        res = requests.get(url, timeout=5)
        data = res.json()
        return {
            "status": data.get("status", "success"),
            "script": data.get("script", "join.py"),
            "param": data.get("param", uid),
            "output": data.get("output", "THANH TUNG"),
            "timestamp": data.get("timestamp", time.time())
        }
    except:
        return {
            "status": "error",
            "script": "join.py",
            "param": uid,
            "output": "THANH TUNG",
            "error": "Timeout or API error",
            "timestamp": time.time()
        }

def processQueue(client):
    global is_processing
    if is_processing:
        return

    is_processing = True

    while True:
        with lock:
            if not queue:
                is_processing = False
                return
            item = queue.pop(0)

        msg = item["message_object"]
        thread_id = item["thread_id"]
        thread_type = item["thread_type"]
        uid = item["uid"]

        last_used = threadCooldowns.get(thread_id, 0)
        now = int(time.time() * 1000)

        if now - last_used < COOLDOWN_MS:
            wait = int((COOLDOWN_MS - (now - last_used)) / 1000)
            client.replyMessage(
                Message(text=f"⏳ Thread này phải chờ thêm {wait}s mới được dùng lại."),
                msg, thread_id, thread_type, ttl=TTL
            )
            continue

        client.replyMessage(
            Message(text="⏳ Đang spam UID..."),
            msg, thread_id, thread_type, ttl=TTL
        )

        result = spamUid(uid)

        client.replyMessage(
            Message(text=f"✅ Hoàn tất!\nKết quả:\n{result}"),
            msg, thread_id, thread_type, ttl=TTL
        )

        threadCooldowns[thread_id] = int(time.time() * 1000)
        time.sleep(1)

def handle_spam_command(message, message_object, thread_id, thread_type, author_id, client):
    content = (message or "").strip()
    prefix = client.prefix if hasattr(client, "prefix") else "."
    if not content.startswith(prefix + "spammoi"):
        return

    args = content[len(prefix + "spammoi"):].strip().split()
    if len(args) == 0:
        client.replyMessage(
            Message(text=f"❌ Dùng: {prefix}spammoi <uid>"),
            message_object, thread_id, thread_type, ttl=TTL
        )
        return

    uid = args[0]
    last_used = threadCooldowns.get(thread_id, 0)
    now = int(time.time() * 1000)

    if now - last_used < COOLDOWN_MS:
        wait = int((COOLDOWN_MS - (now - last_used)) / 1000)
        client.replyMessage(
            Message(text=f"⏳ Thread này phải chờ {wait}s nữa."),
            message_object, thread_id, thread_type, ttl=TTL
        )
        return

    with lock:
        position = len(queue) + 1
        queue.append({
            "message_object": message_object,
            "thread_id": thread_id,
            "thread_type": thread_type,
            "uid": uid
        })

    if position == 1 and not is_processing:
        threading.Thread(target=processQueue, args=(client,), daemon=True).start()
        client.replyMessage(
            Message(text="🚀 Bạn là người đầu tiên, xử lý ngay!"),
            message_object, thread_id, thread_type, ttl=TTL
        )
    else:
        client.replyMessage(
            Message(text=f"⏳ Bạn đang ở vị trí thứ {position} trong hàng đợi."),
            message_object, thread_id, thread_type, ttl=TTL
        )

def PTA():
    return {
        "spammoi": handle_spam_command
    }
