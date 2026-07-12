# -*- coding: utf-8 -*-
import os
import requests
from urllib.parse import urlparse
from PIL import Image
from zlapi.models import Message
from modules.menu import autosave

des = {
    'version': "1.0.3",
    'credits': "ngbao",
    'description': "Chụp ảnh trang web từ link",
    'power': "Thành viên"
}

TTL = 60000
CACHE_DIR = "modules/cache/webcaps"
os.makedirs(CACHE_DIR, exist_ok=True)

# --------- Lệnh chính ---------
def _cap_command(message, message_object, thread_id, thread_type, author_id, client):
    args = message.split()
    if len(args) < 2:
        client.replyMessage(
            Message("⚠️ Vui lòng gửi link web. VD: `.cap https://example.com`"),
            message_object, thread_id, thread_type, ttl=TTL
        )
        return

    url = args[1]
    parsed = urlparse(url)
    if not parsed.scheme:
        url = "http://" + url

    # Dùng image.thum.io miễn phí, fullpage
    api_url = f"https://image.thum.io/get/fullpage/{url}"
    filename = os.path.join(CACHE_DIR, f"{hash(url)}.png")

    try:
        r = requests.get(api_url, timeout=20)
        if r.status_code != 200:
            raise Exception(f"HTTP {r.status_code}")
        with open(filename, "wb") as f:
            f.write(r.content)

        # Resize max 1000x1000
        img = Image.open(filename)
        img.thumbnail((1000, 1000), Image.Resampling.LANCZOS)
        img.save(filename)

        # Gửi ảnh
        client.sendLocalImage(filename, thread_id=thread_id, thread_type=thread_type, ttl=TTL)
        os.remove(filename)

        # Thông báo thành công
        client.replyMessage(
            Message(f"✅ Thành công: Đã chụp trang web {url}"),
            message_object, thread_id, thread_type, ttl=TTL
        )

    except Exception as e:
        client.replyMessage(
            Message(f"⚠️ Lỗi khi chụp web: {e}"),
            message_object, thread_id, thread_type, ttl=TTL
        )

def PTA():
    return {'cap': _cap_command}