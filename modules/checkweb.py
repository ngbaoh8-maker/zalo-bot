import requests
import time
from zlapi.models import Message

des = {
    "version": "1.9.3",
    "credits": "ngbao",
    "description": "Kiểm tra tốc độ phản hồi website",
    "power": "Thành Viên"
}

def handle_checkweb_command(message, message_object, thread_id, thread_type, author_id, client):
    parts = message.strip().split()
    
    if len(parts) < 2:
        content = "⚠️ Dùng: .checkweb <link> để tui check web nha!"
        client.replyMessage(
            Message(text=content),
            message_object,
            thread_id,
            thread_type,
            ttl=120000
        )
        return

    url = parts[1]

    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    client.replyMessage(
        Message(text=f"🔍 Đang kiểm tra tốc độ cho web: {url} ..."),
        message_object,
        thread_id,
        thread_type,
        ttl=120000
    )

    try:
        start = time.perf_counter()
        res = requests.get(url, timeout=10)
        end = time.perf_counter()

        ms = round((end - start) * 1000, 2)

        if ms < 100:
            speed = "⚡ Rất nhanh"
        elif ms < 500:
            speed = "🙂 Bình thường"
        elif ms < 1000:
            speed = "🐌 Hơi chậm"
        else:
            speed = "⛔ Rất chậm"

        content = (
            f"🌐 Kết quả kiểm tra tốc độ web\n"
            f"🔗 Link: {url}\n"
            f"📡 Trạng thái HTTP: {res.status_code}\n"
            f"⚡ Thời gian phản hồi: {ms} ms\n"
            f"📊 Đánh giá: {speed}"
        )

        client.replyMessage(
            Message(text=content),
            message_object,
            thread_id,
            thread_type,
            ttl=30000
        )

    except requests.exceptions.Timeout:
        client.replyMessage(
            Message(text="⏳ Web phản hồi quá lâu (timeout > 10s)!"),
            message_object,
            thread_id,
            thread_type,
            ttl=30000
        )

    except Exception as e:
        client.replyMessage(
            Message(text=f"❌ Lỗi: {e}"),
            message_object,
            thread_id,
            thread_type,
            ttl=120000
        )

def PTA():
    return {
        "checkweb": handle_checkweb_command
    }