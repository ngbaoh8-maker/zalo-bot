import os
import random
import tempfile
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from zlapi.models import Message

des = {
    "version": "5.0",
    "credits": "ngbao",
    "description": "Kiểm tra độ gay",
    "power": "Admin"
}

FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
os.makedirs("modules/cache", exist_ok=True)

def get_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except:
        return ImageFont.load_default()

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
    d = ImageDraw.Draw(mask)
    d.ellipse((0, 0, size, size), fill=255)
    out = Image.new("RGBA", (size, size))
    out.paste(img, (0, 0), mask)
    return out

def rainbow_border(avt, size):
    s = size + 28
    border = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(border)
    colors = [
        (255,0,0),(255,127,0),(255,255,0),
        (0,255,0),(0,0,255),(75,0,130),(148,0,211)
    ]
    for i in range(14):
        d.ellipse((i, i, s-i, s-i), outline=colors[i % 7], width=4)
    border.paste(avt, (14, 14), avt)
    return border

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

def make_gay_card(name, avatar_url, percent):
    W, H = 1200, 500
    AVATAR = 160

    bg = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(bg)
    for y in range(H):
        r = int(40 + y / H * 10)
        g = int(0 + y / H * 40)
        b = int(80 + y / H * 120)
        d.line((0, y, W, y), fill=(r, g, b))

    img = bg.convert("RGBA")
    draw = ImageDraw.Draw(img)

    av_img = fetch_image(avatar_url)
    if not av_img:
        av_img = Image.new("RGBA", (AVATAR, AVATAR), (0, 0, 0))

    avt = rainbow_border(circle_avatar(av_img, AVATAR), AVATAR)

    avt_x = 80
    avt_y = H // 2 - avt.height // 2
    img.paste(avt, (avt_x, avt_y), avt)

    name_font = get_font(42)
    pct_font = get_font(70)
    desc_font = get_font(32)
    btn_font = get_font(28)

    name_x = avt_x + avt.width + 40
    name_y = avt_y + 10
    draw.text((name_x, name_y), name, font=name_font, fill=(255, 255, 255))

    bar_x = name_x
    bar_y = name_y + 70
    bar_w = 520
    bar_h = 26

    draw.rounded_rectangle(
        (bar_x, bar_y, bar_x + bar_w, bar_y + bar_h),
        radius=20,
        outline=(255, 255, 255),
        width=3
    )

    fill_w = int(bar_w * percent / 100)
    draw.rounded_rectangle(
        (bar_x, bar_y, bar_x + fill_w, bar_y + bar_h),
        radius=20,
        fill=(0, 255, 0)
    )

    draw.text(
        (bar_x + bar_w + 25, bar_y - 20),
        f"{percent}%",
        font=pct_font,
        fill=(255, 50, 50)
    )

    if percent >= 50:
        desc = "Có tí nghi ngờ gay phết"
    elif percent >= 30:
        desc = "Cũng hơi nghi nghi"
    else:
        desc = "Khả năng thấp"

    draw.text(
        (bar_x, bar_y + bar_h + 18),
        desc,
        font=desc_font,
        fill=(255, 255, 255)
    )

    btn_text = "TEST ĐỘ GAY"
    btn_w, btn_h = 260, 56
    btn_x = W - btn_w - 40
    btn_y = 40

    draw.rounded_rectangle(
        (btn_x, btn_y, btn_x + btn_w, btn_y + btn_h),
        radius=28,
        outline=(0, 200, 255),
        width=4
    )

    text_w = draw.textlength(btn_text, font=btn_font)
    text_x = btn_x + (btn_w - text_w) // 2
    text_y = btn_y + (btn_h - btn_font.size) // 2 - 2

    draw.text(
        (text_x, text_y),
        btn_text,
        font=btn_font,
        fill=(0, 200, 255)
    )

    draw.text(
        (W - 180, H - 40),
        "Bot: By Bé Bii",
        font=get_font(24),
        fill=(255, 255, 255)
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
        img.convert("RGB").save(f.name, "JPEG", quality=95)
        return f.name, W, H

def handle_gay_command(message, message_object, thread_id, thread_type, author_id, client):
    if message_object.mentions:
        uid = message_object.mentions[0].uid
    else:
        uid = author_id

    name, avatar = safe_user_info(client, uid)
    percent = random.randint(1, 100)

    img_path, w, h = make_gay_card(name, avatar, percent)

    client.sendLocalImage(
        img_path,
        message=Message(text=f"🌈 Test độ gay của {name}: {percent}%"),
        thread_id=thread_id,
        thread_type=thread_type,
        width=w,
        height=h
    )

    os.remove(img_path)

def PTA():
    return {"gay": handle_gay_command}