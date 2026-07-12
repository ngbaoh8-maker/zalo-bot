import os
import time
import base64
import random
import requests
from io import BytesIO
from PIL import (
    Image, ImageDraw, ImageFont, ImageOps,
    ImageEnhance, ImageFilter
)
import concurrent.futures
from zlapi.models import Message
from config import PREFIX

# ================= INFO =================

des = {
    'version': "2.5.0",
    'credits': "ngbao",
    'description': "Chế ảnh bàn thờ (có chữ trên ảnh)",
    'power': "Thành viên"
}

FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
BG_PATH = "modules/cache/bantho_bg.png"

# ================= UTIL =================

def fetch_image(url):
    try:
        if not url:
            return None
        if url.startswith("data:image"):
            return Image.open(
                BytesIO(base64.b64decode(url.split(",", 1)[1]))
            ).convert("RGBA")
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return Image.open(BytesIO(r.content)).convert("RGBA")
    except:
        return None

# ================= CREATE IMAGE =================

def draw_text_outline(draw, pos, text, font, text_color, outline_color, outline=2):
    x, y = pos
    for dx in range(-outline, outline + 1):
        for dy in range(-outline, outline + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
    draw.text((x, y), text, font=font, fill=text_color)

def create_bantho(avatar_url, member_name):
    bg = Image.open(BG_PATH).convert("RGBA")
    W, H = bg.size

    # ===== KHUNG ẢNH FIX THEO ẢNH THỜ 1080x1620 =====
    base_w, base_h = 1080, 1620
    scale_x = W / base_w
    scale_y = H / base_h

    frame_x = int(W * 0.29)
    frame_y = int(H * 0.18)
    frame_w = int(W * 0.41)
    frame_h = int(H * 0.51)

    avatar = fetch_image(avatar_url)
    if not avatar:
        avatar = Image.new("RGBA", (frame_w, frame_h), (150, 150, 150))

        # ================= CROP GIỮ ĐÚNG TỈ LỆ KHUNG =================
    target_ratio = frame_w / frame_h
    aw, ah = avatar.size
    avatar_ratio = aw / ah

    if avatar_ratio > target_ratio:
        # Cắt ngang
        new_w = int(ah * target_ratio)
        left = (aw - new_w) // 2
        avatar = avatar.crop((left, 0, left + new_w, ah))
    else:
        # Cắt dọc
        new_h = int(aw / target_ratio)
        top = (ah - new_h) // 2
        avatar = avatar.crop((0, top, aw, top + new_h))

    avatar = avatar.resize((frame_w, frame_h), Image.LANCZOS)

    # ================= HIỆU ỨNG ẢNH THỜ =================
    avatar = ImageOps.grayscale(avatar)
    avatar = ImageEnhance.Contrast(avatar).enhance(1.3)
    avatar = ImageEnhance.Brightness(avatar).enhance(0.95)
    avatar = avatar.filter(ImageFilter.SHARPEN)
    avatar = avatar.convert("RGBA")

    # ================= GHÉP VÀO KHUNG =================
    bg.paste(avatar, (frame_x, frame_y), avatar)

    draw = ImageDraw.Draw(bg)

    try:
        font_big = ImageFont.truetype(FONT_PATH, int(W * 0.055))
        font_small = ImageFont.truetype(FONT_PATH, int(W * 0.045))
    except:
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()

    text1 = "🕯️ Ra đi thảnh thản nhé 🕯️"

    text2 = member_name

    # Căn giữa
    w1 = draw.textlength(text1, font=font_big)
    w2 = draw.textlength(text2, font=font_small)

    x1 = (W - w1) // 2
    x2 = (W - w2) // 2

    y1 = int(H * 0.68)
    y2 = y1 + int(H * 0.06)

    draw_text_outline(draw, (x1, y1), text1, font_big, "black", "white", 3)
    draw_text_outline(draw, (x2, y2), text2, font_small, "black", "white", 3)

    return bg

    avatar.thumbnail((frame_w, frame_h), Image.LANCZOS)

    canvas = Image.new("RGBA", (frame_w, frame_h), (0, 0, 0, 255))
    ax = (frame_w - avatar.width) // 2
    ay = (frame_h - avatar.height) // 2
    canvas.paste(avatar, (ax, ay), avatar)

    # Đen trắng + nét
    canvas = ImageOps.grayscale(canvas).convert("RGBA")
    canvas = ImageEnhance.Contrast(canvas).enhance(1.25)
    canvas = canvas.filter(ImageFilter.SHARPEN)

    bg.paste(canvas, (frame_x, frame_y), canvas)

    return bg

# ================= COMMAND =================

def handle_bantho_command(message, message_object, thread_id, thread_type, author_id, client):
    text = message_object.text or ""
    parts = text.split()

    # ===== TARGET =====
    target_id = author_id
    if message_object.mentions:
        target_id = message_object.mentions[0]['uid']
    elif message_object.quote:
        target_id = message_object.quote.ownerId

    # ===== PARSE LÝ DO (SPACE) =====
    cause_custom = None
    if len(parts) > 1:
        parts = parts[1:]
        if message_object.mentions:
            parts = parts[1:]
        if parts:
            cause_custom = " ".join(parts)

    client.sendReaction(message_object, "🕯️", thread_id, thread_type)

    # ===== FIX USERNAME =====
    user_info = client.fetchUserInfo(target_id)

    user_name = None
    avatar_url = ""

    if hasattr(user_info, 'changed_profiles') and str(target_id) in user_info.changed_profiles:
        p = user_info.changed_profiles[str(target_id)]
        user_name = p.get('zaloName')
        avatar_url = p.get('avatar', "")
    else:
        user_name = getattr(user_info, 'name', None)
        avatar_url = getattr(user_info, 'avatar', "")

    if not user_name:
        user_name = "Người Vô Danh"

    # ===== DATA (TIN NHẮN) =====
    birth = random.randint(1990, 2010)
    death = random.randint(birth + 15, birth + 80)

    CAUSES = [
        "Ngã cầu thang do xem TikTok",
        "AFK quá lâu trong giờ cao điểm",
        "Lag server không hồi sinh",
        "Ngủ quên khi đang online",
        "Bị cuộc đời gank lén",
        "Out meta nhưng vẫn cố",
        "Lọ quá nhiều",
        "Bị mẹ gank nhưng chống cự không nổi"
    ]

    cause = cause_custom if cause_custom else random.choice(CAUSES)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        image = executor.submit(
            create_bantho,
            avatar_url,
            f"@{user_name}"
        ).result()

    if not os.path.exists("modules/cache"):
        os.makedirs("modules/cache")

    path = f"modules/cache/bantho_{int(time.time())}.jpg"
    image.convert("RGB").save(path, quality=95, subsampling=0)

    # ===== TIN NHẮN =====
    msg_text = (
        f"🕯️ Ảnh bàn thờ 🕯️\n"
        f"Họ tên: {user_name}\n"
        f"Năm sinh: {birth}\n"
        f"Năm mất: {death}\n"
        f"Lý do mất: {cause}"
    )

    client.sendLocalImage(
        path,
        thread_id=thread_id,
        thread_type=thread_type,
        message=Message(text=msg_text),
        ttl=120000
    )

    os.remove(path)

# ================= EXPORT =================

def PTA():
    return {
        'bantho': handle_bantho_command,
        'anthor': handle_bantho_command
    }