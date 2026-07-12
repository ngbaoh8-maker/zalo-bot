# -*- coding: utf-8 -*-
import os
import time
import random
import tempfile
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from zlapi.models import Message

des = {
    "version": "3.0",
    "credits": "ngbao",
    "description": "Test độ les • Neon glass",
    "power": "Thành Viên"
}

FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
os.makedirs("modules/cache", exist_ok=True)

# ================= FONT =================
def get_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except:
        return ImageFont.load_default()

# ================= IMAGE =================
def fetch_image(url):
    try:
        if not url:
            return None
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return Image.open(BytesIO(r.content)).convert("RGBA")
    except:
        return None

def circle_avatar(img, size):
    img = img.resize((size, size))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    out = Image.new("RGBA", (size, size))
    out.paste(img, (0, 0), mask)
    return out

def rainbow_border(avt, size):
    s = size + 26
    border = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(border)
    colors = [
        (0,255,255),(255,0,255),(0,255,120),
        (255,255,0),(0,180,255)
    ]
    for i in range(12):
        d.ellipse((i,i,s-i,s-i), outline=colors[i % len(colors)], width=3)
    border.paste(avt, (13,13), avt)
    return border

# ================= GLASS + NEON =================
def glass_card(bg, box, radius=30):
    x1,y1,x2,y2 = box
    w,h = x2-x1, y2-y1
    blur = bg.crop(box).filter(ImageFilter.GaussianBlur(14))
    overlay = Image.new("RGBA",(w,h),(255,255,255,35))
    glass = Image.alpha_composite(blur, overlay)

    mask = Image.new("L",(w,h),0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0,0,w,h), radius=radius, fill=255
    )
    bg.paste(glass,(x1,y1),mask)

# ================= RAIN EFFECT =================
# ================= HEAVY RAIN EFFECT =================
def draw_rain(img, layers=3):
    W, H = img.size

    for layer in range(layers):
        rain = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(rain)

        drops = 220 + layer * 120   # càng layer càng dày
        speed = 18 + layer * 8
        blur  = 0.6 + layer * 0.4

        for _ in range(drops):
            x = random.randint(-50, W)
            y = random.randint(-H, H)
            length = random.randint(22, 50 + layer * 10)
            alpha = random.randint(70, 180)

            color = (0, 255, 255, alpha)  # neon cyan
            d.line(
                (x, y, x + speed, y + length),
                fill=color,
                width=2
            )

        rain = rain.filter(ImageFilter.GaussianBlur(blur))
        img.alpha_composite(rain)


def neon_border(draw, box, radius=30):
    x1,y1,x2,y2 = box
    neon = [
        (0,255,255,140),
        (0,200,255,90),
        (0,150,255,60)
    ]
    for i,c in enumerate(neon):
        draw.rounded_rectangle(
            (x1-i,y1-i,x2+i,y2+i),
            radius=radius+i,
            outline=c,
            width=3
        )

# ================= USER INFO =================
def safe_user_info(client, uid):
    try:
        info = client.fetchUserInfo(uid)
        name = f"User_{uid}"
        avatar = None
        if isinstance(info, dict):
            p = info.get("changed_profiles", {}).get(str(uid)) or info
            name = p.get("zaloName", name)
            avatar = p.get("avatar") or p.get("photo")
        return name, avatar
    except:
        return f"User_{uid}", None

# ================= DRAW CARD =================
def make_less_card(name, avatar_url, percent):
    W, H = 1200, 520

    # nền gradient tối
    bg = Image.new("RGB",(W,H))
    d = ImageDraw.Draw(bg)
    for y in range(H):
        d.line((0,y,W,y), fill=(20,30+y//4,60+y//2))

    img = bg.convert("RGBA")
    draw = ImageDraw.Draw(img)
    # 🌧️ mưa rơi nền neon
    draw_rain(img, layers=4)

    # CARD
    card = (80,80,W-80,H-80)
    glass_card(img, card, 35)
    neon_border(draw, card, 35)

    # avatar
    AVT = 150
    av = fetch_image(avatar_url)
    if not av:
        av = Image.new("RGBA",(AVT,AVT),(0,0,0))
    avt = rainbow_border(circle_avatar(av, AVT), AVT)
    img.paste(avt,(120,H//2-avt.height//2),avt)

    # text
    font_name = get_font(44)
    font_pct  = get_font(76)
    font_desc = get_font(34)

    tx = 120 + avt.width + 50
    ty = 160

    draw.text((tx,ty), name, font=font_name, fill=(255,255,255))
    draw.text((tx,ty+60), f"{percent}%", font=font_pct, fill=(0,255,255))

    # bar
    bar_x, bar_y = tx, ty+150
    bar_w, bar_h = 520, 26
    draw.rounded_rectangle(
        (bar_x,bar_y,bar_x+bar_w,bar_y+bar_h),
        radius=20, outline=(0,255,255), width=3
    )
    draw.rounded_rectangle(
        (bar_x,bar_y,bar_x+int(bar_w*percent/100),bar_y+bar_h),
        radius=20, fill=(0,255,255)
    )

    # desc
    if percent >= 80:
        desc = "Cong toàn tập 🌈"
    elif percent >= 60:
        desc = "Nghi vấn rất cao 😳"
    elif percent >= 40:
        desc = "Có mùi mùi 👀"
    elif percent >= 20:
        desc = "Bình thường 🤔"
    else:
        desc = "Thẳng như cột điện ⚡"

    draw.text((tx,bar_y+50), desc, font=font_desc, fill=(220,240,255))

    with tempfile.NamedTemporaryFile(delete=False,suffix=".jpg") as f:
        img.convert("RGB").save(f.name,"JPEG",quality=95)
        return f.name,W,H

# ================= HANDLE =================
def handle_less(message, message_object, thread_id, thread_type, author_id, client):
    if message_object.mentions:
        uid = message_object.mentions[0].uid
    else:
        uid = author_id

    name, avatar = safe_user_info(client, uid)

    # 👉 MESSAGE CHỜ
    client.replyMessage(
        Message(text=f"⏳ Đang check độ les của {name}..."),
        message_object,
        thread_id,
        thread_type
    )

    time.sleep(5)

    percent = random.randint(0,100)
    img_path,w,h = make_less_card(name, avatar, percent)

    client.sendLocalImage(
        img_path,
        thread_id=thread_id,
        thread_type=thread_type,
        width=w,
        height=h,
        message=Message(text=f"💗 Kết quả độ les của {name}")
    )

    os.remove(img_path)

def PTA():
    return {"les": handle_less}
