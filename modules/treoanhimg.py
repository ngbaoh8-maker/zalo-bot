# -*- coding: UTF-8 -*-
import os
import time
import threading
import random
import requests
import json
from io import BytesIO
from PIL import Image
from zlapi.models import Message
from config import ADMIN

des = {
    'version': "4.0.0",
    'credits': "ngbao",
    'description': "Treo ảnh kèm ngôn",
    'power': "Quản Trị Viên Bot"
}

# ====== DATA ======
is_war_running = False
delay_time = 5
IMAGE_FILE = "war_image.jpg"
ONETAG_FILE = "onetag.txt"

words = [
    "ngu", "vl", "đừng tưởng", "tao không biết", "cười", "chọc",
    "ẩn", "thoát", "hết thuốc", "khỏi nói", "giờ thì", "xong", "chửi tiếp"
]
emojis = ["😡", "🔥", "🤬", "💀", "🐧", "🤯", "😤", "👀", "💢"]

# ====== RANDOM TEXT ======
def make_sentence():
    s = random.sample(words, 6)
    s.insert(random.randint(0, 5), "mày")
    return " ".join(s) + " " + random.choice(emojis)

# ====== IMAGE PIPELINE ======
def convert_image_to_webp(url, out="temp.webp"):
    try:
        data = requests.get(url, timeout=10).content
        img = Image.open(BytesIO(data)).convert("RGBA")
        img.save(out, "WEBP", quality=85)
        return out
    except:
        return None

def upload_to_uguu(path):
    try:
        res = requests.post("https://uguu.se/upload", files={"files[]": open(path, "rb")})
        return res.json()['files'][0]['url']
    except:
        return None

def extract_reply_image(message_object):
    try:
        if not hasattr(message_object, "quote") or not message_object.quote:
            return None
        attach = json.loads(message_object.quote.get("attach", "{}"))
        return attach.get("hdUrl") or attach.get("href")
    except:
        return None

# ====== HANDLER ======
def handle_treoanh_command(message, message_object, thread_id, thread_type, author_id, client):
    global is_war_running, delay_time

    if str(author_id) not in ADMIN:
        client.sendMessage(Message(text="❌ Bạn không có quyền dùng lệnh này."), thread_id, thread_type)
        return

    parts = message.split()
    if len(parts) < 2:
        client.sendMessage(Message(text="⚙️ treoanh on / stop / set / text / info / img"), thread_id, thread_type)
        return

    cmd = parts[1].lower()

    # ====== SET DELAY ======
    if cmd == "set":
        if len(parts) < 3 or not parts[2].isdigit():
            client.sendMessage(Message(text="⚠️ Dùng: treoanh set <giây>"), thread_id, thread_type)
            return
        delay_time = int(parts[2])
        client.sendMessage(Message(text=f"⏳ Delay set thành: {delay_time}s"), thread_id, thread_type)
        return

    # ====== SET TEXT ======
    if cmd == "text":
        content = " ".join(parts[2:]) if len(parts) >= 3 else make_sentence()
        with open(ONETAG_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        client.sendMessage(Message(text="📄 Đã lưu nội dung WAR."), thread_id, thread_type)
        return

    # ====== INFO ======
    if cmd == "info":
        status = "Đang chạy 🔥" if is_war_running else "Đang tắt 🟢"
        img_status = "Có" if os.path.exists(IMAGE_FILE) else "Không"
        client.sendMessage(Message(text=f"📊 INFO WAR\n• Trạng thái: {status}\n• Ảnh: {img_status}"), thread_id, thread_type)
        return

    # ====== SET IMAGE ======
    if cmd == "img":
        url = parts[2] if len(parts) >= 3 else extract_reply_image(message_object)
        if not url:
            client.sendMessage(Message(text="❌ Hãy nhập link hoặc reply 1 ảnh!"), thread_id, thread_type)
            return

        temp = convert_image_to_webp(url)
        if not temp:
            client.sendMessage(Message(text="❌ Lỗi chuyển đổi ảnh."), thread_id, thread_type)
            return

        link = upload_to_uguu(temp)
        os.remove(temp)

        if not link:
            client.sendMessage(Message(text="❌ Upload thất bại."), thread_id, thread_type)
            return

        data = requests.get(link).content
        with open(IMAGE_FILE, "wb") as f:
            f.write(data)

        client.sendMessage(Message(text="✅ Setup ảnh WAR thành công!"), thread_id, thread_type)
        return

    # ====== STOP ======
    if cmd == "stop":
        is_war_running = False
        client.sendMessage(Message(text="🛑 Đã dừng WAR."), thread_id, thread_type)
        return

    # ====== START WAR ======
    if cmd == "on":
        if not os.path.exists(ONETAG_FILE):
            client.sendMessage(Message(text="⚠️ Chưa có nội dung WAR."), thread_id, thread_type)
            return

        if not os.path.exists(IMAGE_FILE):
            client.sendMessage(Message(text="⚠️ Chưa có ảnh WAR."), thread_id, thread_type)
            return

        is_war_running = True
        client.sendMessage(Message(text="🔥 WAR bắt đầu!"), thread_id, thread_type)

        def war_loop():
            global is_war_running
            while is_war_running:
                with open(ONETAG_FILE, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                for line in lines:
                    if not is_war_running:
                        break
                    msg = line.strip().upper()
                    try:
                        client.sendLocalImage(IMAGE_FILE, thread_id, thread_type, Message(text=msg))
                    except:
                        pass
                    time.sleep(delay_time)

        threading.Thread(target=war_loop, daemon=True).start()
        return

    # ====== DEFAULT HELP ======
    client.sendMessage(Message(text="⚙️ treoimg on / stop / set / text / info / img"), thread_id, thread_type)

# ====== HÀM TRẢ LỆNH ======
def PTA():
    return {
        'treoimg': handle_treoanh_command
    }