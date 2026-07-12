from zlapi.models import Message
import requests
import time
import threading

des = {
    "version": "1.0.0",
    "credits": "ngbao",
    "description": "Lag teamcode code ff",
    "power": "Thành Viên"
}

API_URL = "http://103.157.204.204:4000/lag="
COOLDOWN_MS = 10000
TTL = 60000

queue = []
is_processing = False
threadCooldowns = {}
lock = threading.Lock()

def lagTeamcode(teamcode):
    try:
        url = f"{API_URL}{teamcode}"
        res = requests.get(url, timeout=5)
        data = res.json()
        return {
            "status": data.get("status", "success"),
            "script": data.get("script", "lag.py"),
            "param": data.get("param", teamcode),
            "output": data.get("output", "ngbao"),
            "timestamp": data.get("timestamp", time.time())
        }
    except:
        return {
            "status": "error",
            "script": "lag.py",
            "param": teamcode,
            "output": "ngbao",
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
        teamcode = item["teamcode"]

        last_used = threadCooldowns.get(thread_id, 0)
        now = int(time.time() * 1000)

        if now - last_used < COOLDOWN_MS:
            wait = int((COOLDOWN_MS - (now - last_used)) / 1000)
            client.replyMessage(
                Message(text=f"⏳ Thread nay phai cho them {wait}s moi co the dung lai."),
                msg, thread_id, thread_type, ttl=TTL
            )
            continue

        client.replyMessage(
            Message(text="⏳ Đang xử lý Teamcode..."),
            msg, thread_id, thread_type, ttl=TTL
        )

        result = lagTeamcode(teamcode)

        client.replyMessage(
            Message(text=f"✅ Hoàn tất!\nKết quả:\n{result}"),
            msg, thread_id, thread_type, ttl=TTL
        )

        threadCooldowns[thread_id] = int(time.time() * 1000)
        time.sleep(1)

def handle_lag_command(message, message_object, thread_id, thread_type, author_id, client):
    content = (message or "").strip()
    prefix = client.prefix if hasattr(client, "prefix") else "."
    if not content.startswith(prefix + "lag"):
        return

    args = content[len(prefix + "lag"):].strip().split()
    if len(args) == 0:
        client.replyMessage(
            Message(text=f"❌ Dùng: {prefix}lag <teamcode>"),
            message_object, thread_id, thread_type, ttl=TTL
        )
        return

    teamcode = args[0]
    last_used = threadCooldowns.get(thread_id, 0)
    now = int(time.time() * 1000)

    if now - last_used < COOLDOWN_MS:
        wait = int((COOLDOWN_MS - (now - last_used)) / 1000)
        client.replyMessage(
            Message(text=f"⏳ Thread này phải cho {wait}s nữa."),
            message_object, thread_id, thread_type, ttl=TTL
        )
        return

    with lock:
        position = len(queue) + 1
        queue.append({
            "message_object": message_object,
            "thread_id": thread_id,
            "thread_type": thread_type,
            "teamcode": teamcode
        })

    if position == 1 and not is_processing:
        threading.Thread(target=processQueue, args=(client,), daemon=True).start()
        client.replyMessage(
            Message(text="🚀 Bạn là người đầu tiên, xử lý ngay!"),
            message_object, thread_id, thread_type, ttl=TTL
        )
    else:
        client.replyMessage(
            Message(text=f"⏳ Bạn đang ở vị trí thứ {position} trong hàng đội."),
            message_object, thread_id, thread_type, ttl=TTL
        )

def PTA():
    return {
        "lag": handle_lag_command
    }
