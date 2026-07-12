import os
import time
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from zlapi.models import Message

# ================= INFO =================
des = {
    'version': "2.1.0",
    'credits': "ngbao",
    'description': "Canvas – vẽ chữ vào ảnh (ổn định cho mọi bot)",
    'power': "Thành viên"
}

FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
MAX_SIZE = 1280

# cache ảnh theo thread
IMAGE_CACHE = {}

# ================= UTIL =================
def extract_image_url(msg):
    # attachments
    atts = getattr(msg, "attachments", None)
    if atts:
        att = atts[0]
        if att.get("type") == "photo":
            return att.get("url") or att.get("thumbUrl")

    # content
    content = getattr(msg, "content", None)
    if isinstance(content, dict):
        return (
            content.get("href")
            or content.get("thumb")
            or content.get("mediaUrl")
        )

    return None


def fast_canvas(img: Image.Image, text: str):
    w, h = img.size
    if max(w, h) > MAX_SIZE:
        s = MAX_SIZE / max(w, h)
        img = img.resize((int(w*s), int(h*s)), Image.LANCZOS)

    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)
    W, H = img.size

    try:
        font = ImageFont.truetype(FONT_PATH, int(W * 0.07))
    except:
        font = ImageFont.load_default()

    bbox = draw.multiline_textbbox((0,0), text, font=font, align="center")
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]

    x = (W - tw) // 2
    y = (H - th) // 2

    for dx, dy in [(-2,0),(2,0),(0,-2),(0,2)]:
        draw.multiline_text((x+dx, y+dy), text, font=font, fill="black", align="center")

    draw.multiline_text((x, y), text, font=font, fill="white", align="center")
    return img

# ================= COMMAND =================
def handle_canvas(message, message_object, thread_id, thread_type, author_id, client):
    img_url = None

    # 1️⃣ ưu tiên reply ảnh
    quote = getattr(message_object, "quote", None)
    if quote:
        img_url = extract_image_url(quote)

    # 2️⃣ nếu không reply → dùng ảnh cache
    if not img_url:
        img_url = IMAGE_CACHE.get(thread_id)

    if not img_url:
        client.sendMessage(
            Message(text="❌ Hãy gửi ảnh trước rồi gõ: canvas <nội dung>"),
            thread_id, thread_type
        )
        return

    text = message_object.text.replace("canvas", "", 1).strip() or "Canvas"

    try:
        img = Image.open(BytesIO(requests.get(img_url, timeout=8).content))
    except:
        client.sendMessage(
            Message(text="❌ Không tải được ảnh"),
            thread_id, thread_type
        )
        return

    img = fast_canvas(img, text)

    os.makedirs("modules/cache", exist_ok=True)
    path = f"modules/cache/canvas_{int(time.time())}.jpg"
    img.save(path, quality=88)

    client.sendLocalImage(
        path,
        thread_id=thread_id,
        thread_type=thread_type,
        message=Message(text="🎨 Canvas xong")
    )

    os.remove(path)

# ================= AUTO CACHE IMAGE =================
def cache_image(message_object, thread_id):
    url = extract_image_url(message_object)
    if url:
        IMAGE_CACHE[thread_id] = url

# ================= EXPORT =================
def PTA():
    return {
        "canvas": handle_canvas,
        "__any__": cache_image  # 👈 QUAN TRỌNG
    }
