import os
import time
import random
import re
import requests
from zlapi.models import Message

# ===========================
# CONFIG
# ===========================
CACHE_DIR = "modules/cache/gif"
os.makedirs(CACHE_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

des = {
    "version": "1.3.0",
    "credits": "ngbao",
    "description": "Tìm và gửi GIF (không cần API, đã fix thumbnailUrl)",
    "power": "Thành viên"
}

# ===========================
# SEARCH GIF (NO API)
# ===========================
def search_gif_no_api(keyword):
    """
    Trả về: (gif_url, thumbnail_url)
    """
    url = f"https://tenor.com/search/{keyword.replace(' ', '-')}-gifs"
    r = requests.get(url, headers=HEADERS, timeout=10)
    r.raise_for_status()

    # Lấy gif và thumbnail từ Tenor page
    gif_uris = re.findall(r'https://media\.tenor\.com/[^"]+\.gif', r.text)
    thumb_uris = re.findall(r'https://media\.tenor\.com/[^"]+\.png', r.text)

    if not gif_uris:
        return None, None

    gif_url = random.choice(gif_uris)

    # Ưu tiên png làm thumbnail, fallback gif
    if thumb_uris:
        thumbnail_url = random.choice(thumb_uris)
    else:
        thumbnail_url = gif_url

    return gif_url, thumbnail_url

def download_gif(url):
    path = os.path.join(CACHE_DIR, f"gif_{int(time.time())}.gif")
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()

    with open(path, "wb") as f:
        f.write(r.content)

    return path

# ===========================
# HANDLE COMMAND
# ===========================
def handle_gif_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        parts = message.split(maxsplit=1)
        if len(parts) < 2:
            client.replyMessage(
                Message(text="⚠️ Cú pháp: !gif <từ khóa>\nví dụ: gif mèo cute"),
                message_object,
                thread_id,
                thread_type
            )
            return

        keyword = parts[1].strip()

        # Báo đang tìm
        client.replyMessage(
            Message(text=f"🔍 Đang tìm GIF cho: {keyword}"),
            message_object,
            thread_id,
            thread_type
        )

        gif_url, thumb_url = search_gif_no_api(keyword)
        if not gif_url:
            raise Exception("Không tìm thấy GIF phù hợp.")

        gif_path = download_gif(gif_url)

        # GỬI GIF ĐÚNG CHUẨN CLIENT (CÓ thumbnailUrl)
        client.sendLocalGif(
            gif_path,      # gifPath
            thumb_url,     # thumbnailUrl (BẮT BUỘC)
            thread_id,
            thread_type,
            ttl=120000
        )

        if os.path.exists(gif_path):
            os.remove(gif_path)

    except Exception as e:
        client.replyMessage(
            Message(text=f"❌ Lỗi gửi GIF:\n{str(e)}"),
            message_object,
            thread_id,
            thread_type
        )

# ===========================
# REGISTER
# ===========================
def PTA():
    return {
        'gif': handle_gif_command
    }