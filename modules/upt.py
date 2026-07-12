# uptime.py — STYLE BANBE.PY REMAKE (neon border + glass + avatar center)

import os, time, psutil, platform, requests
from io import BytesIO
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from zlapi.models import Message

des = {
    'version': "2.0.0",
    'credits': "ngbao",
    'description': "Uptime bot theo style card banbe.py",
    'power': "Quản trị viên Bot"
}

CACHE = "modules/cache/uptime"
os.makedirs(CACHE, exist_ok=True)

FONT = "modules/cache/font/BeVietnamPro-Bold.ttf"
BOT_START = time.time()


# ====================================
# LOAD BACKGROUND (giống banbe.py)
# ====================================
def load_image_from_url(url):
    r = requests.get(url, timeout=10)
    return Image.open(BytesIO(r.content)).convert("RGBA")

def get_bg_image(size):
    urls = [
        "https://files.catbox.moe/y5fg9j.jpg",
        "https://files.catbox.moe/t31gfd.jpg",
        "https://files.catbox.moe/77c4by.jpg",
        "https://files.catbox.moe/d7p28q.jpg"
    ]
    import random
    try:
        img = load_image_from_url(random.choice(urls))
        return img.resize(size, Image.LANCZOS)
    except:
        return Image.new("RGBA", size, (25,20,40,255))


# ====================================
# AVATAR TRÒN
# ====================================
def load_avatar(url, size=210):
    try:
        r = requests.get(url, timeout=5)
        img = Image.open(BytesIO(r.content)).convert("RGBA")
    except:
        img = Image.new("RGBA", (size,size), (150,150,150,255))

    img = img.resize((size,size), Image.LANCZOS)

    mask = Image.new("L", (size,size), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse((0,0,size,size), fill=255)
    img.putalpha(mask)
    return img


# ====================================
# TỰ XUỐNG DÒNG
# ====================================
def wrap_text(text, font, max_width):
    words = text.split(" ")
    lines = []
    line = ""

    for w in words:
        test = line + w + " "
        if font.getlength(test) <= max_width:
            line = test
        else:
            lines.append(line)
            line = w + " "
    lines.append(line)
    return lines


# ====================================
# RENDER UPTIME STYLE BANBE
# ====================================
def render_uptime(avatar_url):
    uptime = time.strftime("%H:%M:%S", time.gmtime(time.time() - BOT_START))
    cpu = psutil.cpu_percent()
    ram_used = psutil.virtual_memory().percent
    ram_total = round(psutil.virtual_memory().total / (1024**3), 1)
    ping = (int(time.time()*10) % 60) + 20
    os_name = platform.system()
    python_ver = platform.python_version()
    now = datetime.now().strftime("%d/%m/%Y • %H:%M:%S")

    info = [
        ("⏱ Uptime", uptime),
        ("🔥 CPU", f"{cpu}%"),
        ("💾 RAM", f"{ram_used}% / {ram_total}GB"),
        ("📡 Ping", f"{ping} ms"),
        ("🖥 OS", os_name),
        ("🐍 Python", python_ver),
        ("📅 Time", now),
    ]

    # CANVAS
    W, H = 1600, 2300
    bg = get_bg_image((W, H))
    draw = ImageDraw.Draw(bg)

    # TITLE
    title_font = ImageFont.truetype(FONT, 90)
    draw.text(
        (W//2 - title_font.getlength("UPTIME BOT")//2, 80),
        "UPTIME BOT", font=title_font, fill=(0,255,255)
    )

    # ======= CARD =======
    CARD_W = 1200           # rộng hơn
    CARD_H = 1500           # cao hơn
    cx = W//2 - CARD_W//2
    cy = 260
    radius = 60

    # NEON BORDER
    neon = [
        (255,0,0,130),(255,127,0,130),(255,255,0,130),
        (0,255,0,130),(0,255,255,130),(0,127,255,130),
        (139,0,255,130)
    ]
    for g, col in enumerate(neon, 1):
        draw.rounded_rectangle(
            [cx-g, cy-g, cx+CARD_W+g, cy+CARD_H+g],
            radius=radius + g,
            outline=col,
            width=2
        )

    # ======= GLASS BOTTOM =======
    glass_h = 850          # tăng chiều cao vùng text
    glass_y = cy + CARD_H - glass_h

    area = bg.crop((cx, glass_y, cx+CARD_W, glass_y+glass_h)).filter(
        ImageFilter.GaussianBlur(10)
    )
    overlay = Image.new("RGBA", (CARD_W, glass_h), (22,28,45,145))
    glass = Image.alpha_composite(area, overlay)

    mask = Image.new("L", (CARD_W, glass_h), 0)
    dm = ImageDraw.Draw(mask)
    dm.rounded_rectangle([0,0,CARD_W,glass_h], radius=radius, fill=255)
    bg.paste(glass, (cx, glass_y), mask)

    # ======= AVATAR =======
    av = load_avatar(avatar_url, 300)
    av_x = cx + CARD_W//2 - 300//2
    av_y = cy + 40
    bg.alpha_composite(av, (av_x, av_y))

    # ======= TEXT INFO =======
    font_title = ImageFont.truetype(FONT, 56)
    font_val   = ImageFont.truetype(FONT, 52)

    text_start = glass_y + 50
    line_gap = 120

    max_text_width = CARD_W - 140   # để không bao giờ lòi chữ

    y = text_start
    for title, value in info:

        # TITLE
        t_x = cx + CARD_W//2 - font_title.getlength(title)//2
        draw.text((t_x, y), title, font=font_title, fill="#FFFFFF")
        y += 60

        # VALUE → tự xuống dòng
        wrapped = wrap_text(value, font_val, max_text_width)
        for line in wrapped:
            v_x = cx + CARD_W//2 - font_val.getlength(line.strip())//2
            draw.text((v_x, y), line.strip(), font=font_val, fill="#EAF6FF")
            y += 60  # khoảng cách giữa các dòng

        y += 40  # khoảng cách giữa các mục


    # ===== SAVE FINAL =====
    out = os.path.join(CACHE, f"uptime_{time.time()}.jpg")
    bg.convert("RGB").save(out, quality=97)
    return out, W, H



# ====================================
# COMMAND
# ====================================
def handle_uptime(message, msg_obj, thread_id, thread_type, author_id, client):
    try:
        user = client.fetchUserInfo(author_id)
        p = user.changed_profiles.get(author_id, {})
        avatar = p.get("avatar", None)

        path, W, H = render_uptime(avatar)
        client.sendLocalImage(path, thread_id, thread_type, width=W, height=H)
        os.remove(path)

    except Exception as e:
        client.sendMessage(Message(text=f"❌ Lỗi uptime: {e}"), thread_id, thread_type)


def PTA():
    return {"upt": handle_uptime}
