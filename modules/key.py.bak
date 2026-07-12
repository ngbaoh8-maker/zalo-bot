import os, requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from zlapi.models import Message

des = {
    'version': "2.0.0",
    'credits': "ChatGPT Rebuild",
    'description': "Danh sách key nhóm (style banbe.py)",
    'power': "Quản trị viên Bot"
}

CACHE = "modules/cache/keyimg"
os.makedirs(CACHE, exist_ok=True)

FONT = "modules/cache/font/BeVietnamPro-Bold.ttf"

# ===============================
# LOAD BACKGROUND (giống banbe.py)
# ===============================
def load_image_from_url(url):
    r = requests.get(url, timeout=10)
    return Image.open(BytesIO(r.content)).convert("RGBA")

def get_bg_image(size):
    bg_urls = [
        "https://files.catbox.moe/y5fg9j.jpg",
        "https://files.catbox.moe/t31gfd.jpg",
        "https://files.catbox.moe/77c4by.jpg",
        "https://files.catbox.moe/d7p28q.jpg"
    ]
    import random
    try:
        img = load_image_from_url(random.choice(bg_urls))
        return img.resize(size, Image.LANCZOS)
    except:
        return Image.new("RGBA", size, (25,20,40,255))

# ===============================
# LOAD AVATAR
# ===============================
def load_image(url, size):
    try:
        r = requests.get(url, timeout=6)
        im = Image.open(BytesIO(r.content)).convert("RGBA")
    except:
        im = Image.new("RGBA", (size, size), (130, 130, 130, 255))
    return im.resize((size, size), Image.LANCZOS)

# ===============================
# CARD STYLE GIỐNG banbe.py
# ===============================
def card_user(draw, bg, cx, cy, name, uid, avatar_url, neon_color=(80,150,255)):
    CARD_W = 880
    CARD_H = 380
    radius = 45

    # NEON BORDER
    neon = [
        (255,0,0,130),(255,127,0,130),(255,255,0,130),
        (0,255,0,130),(0,255,255,130),(0,127,255,130),
        (139,0,255,130)
    ]

    for g, col in enumerate(neon, 1):
        draw.rounded_rectangle(
            [cx-g, cy-g, cx + CARD_W + g, cy + CARD_H + g],
            radius = radius + g,
            outline = col,
            width = 2
        )

    # GLASS BOTTOM
    glass_h = 180
    glass_y = cy + CARD_H - glass_h

    area = bg.crop((cx, glass_y, cx + CARD_W, glass_y + glass_h)).filter(ImageFilter.GaussianBlur(8))
    overlay = Image.new("RGBA", (CARD_W, glass_h), (22, 28, 45, 125))
    glass = Image.alpha_composite(area, overlay)

    mask = Image.new("L", (CARD_W, glass_h), 0)
    m = ImageDraw.Draw(mask)
    m.rounded_rectangle([0,0,CARD_W,glass_h], radius=radius, fill=255)
    bg.paste(glass, (cx, glass_y), mask)

    # AVATAR TRÒN
    ICON = 170
    av = load_image(avatar_url, ICON)

    mask_icon = Image.new("L", (ICON, ICON), 0)
    dmask = ImageDraw.Draw(mask_icon)
    dmask.ellipse((0,0,ICON,ICON), fill=255)

    av_final = Image.new("RGBA", (ICON, ICON), (0,0,0,0))
    av_final.paste(av, (0,0), mask_icon)

    x_icon = cx + CARD_W//2 - ICON//2
    y_icon = cy + 25

    bg.alpha_composite(av_final, (x_icon, y_icon))

    # TEXT
    fn_name = ImageFont.truetype(FONT, 50)
    fn_uid  = ImageFont.truetype(FONT, 32)

    if len(name) > 20:
        name = name[:20] + "…"

    text_y = glass_y + 25

    draw.text((cx + CARD_W//2 - fn_name.getlength(name)//2, text_y),
              name, font=fn_name, fill="white")

    draw.text((cx + CARD_W//2 - fn_uid.getlength(f"UID: {uid}")//2, text_y + 75),
              f"UID: {uid}", font=fn_uid, fill="#C8E2FF")

    return cy + CARD_H + 55

# ===============================
# LEADER CARD (vàng)
# ===============================
def card_leader(draw, bg, cx, cy, name, uid, avatar_url):
    return card_user(draw, bg, cx, cy, name, uid, avatar_url, neon_color=(255,220,80))

# ===============================
# ADMIN CARD (xanh)
# ===============================
def card_admin(draw, bg, cx, cy, name, uid, avatar_url):
    return card_user(draw, bg, cx, cy, name, uid, avatar_url, neon_color=(80,150,255))

# ===============================
# MAIN RENDER KEY LIST
# ===============================
def handle_key_command(message, msg_obj, thread_id, thread_type, author_id, client):

    info = client.fetchGroupInfo(thread_id)
    g = info.gridInfoMap.get(thread_id)

    if not g:
        client.replyMessage(Message(text="❌ Không thể lấy thông tin nhóm"), msg_obj, thread_id, thread_type)
        return

    leader = g.creatorId
    admins = list(set(g.adminIds))
    if leader in admins:
        admins.remove(leader)

    # BACKGROUND
    W, H = 2100, 2600
    bg = get_bg_image((W, H))
    draw = ImageDraw.Draw(bg)

    # TITLE
    fn_title = ImageFont.truetype(FONT, 80)
    fn_name  = ImageFont.truetype(FONT, 60)

    draw.text((W//2 - fn_title.getlength("DANH SÁCH GIỮ KEY")//2, 70),
              "DANH SÁCH GIỮ KEY", font=fn_title, fill=(255,220,60))

    draw.text((W//2 - fn_name.getlength(g.name)//2, 160),
              g.name, font=fn_name, fill=(120,220,255))

    # LEADER
    try:
        u = client.fetchUserInfo(leader)
        p = u.changed_profiles.get(leader, {})
        n = p.get("zaloName", "Không rõ")
        av = p.get("avatar")
    except:
        n, av = "Không rõ", None

    y = 300
    y = card_leader(draw, bg, W//2 - 880//2, y, n, leader, av)

    # 2 COLUMN ADMIN
    x1 = 180
    x2 = 1180

    yL = y
    yR = y

    half = len(admins) // 2
    left = admins[:half]
    right = admins[half:]

    for uid in left:
        try:
            u = client.fetchUserInfo(uid)
            p = u.changed_profiles.get(uid, {})
            n = p.get("zaloName", "Không rõ")
            av = p.get("avatar")
        except:
            n, av = "Không rõ", None

        yL = card_admin(draw, bg, x1, yL, n, uid, av)

    for uid in right:
        try:
            u = client.fetchUserInfo(uid)
            p = u.changed_profiles.get(uid, {})
            n = p.get("zaloName", "Không rõ")
            av = p.get("avatar")
        except:
            n, av = "Không rõ", None

        yR = card_admin(draw, bg, x2, yR, n, uid, av)

    # SAVE IMAGE
    out = f"{CACHE}/keyimg.png"
    bg.convert("RGB").save(out, quality=95)

    client.sendLocalImage(out, thread_id, thread_type, width=W, height=H)

def PTA():
    return {'key': handle_key_command}
