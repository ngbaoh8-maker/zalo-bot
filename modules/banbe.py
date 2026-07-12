# =====================================================
# FRIEND LIST — GLASS CARD + MENU STYLE
# =====================================================

import os, time
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from zlapi.models import Message

des = {
    'version': "2.0.0",
    'credits': "ngbao",
    'description': "Xem danh Sách bạn bè",
    'power': "Thành viên"
}

CACHE = "modules/cache/friendimg"
os.makedirs(CACHE, exist_ok=True)

FONT = "modules/cache/font/BeVietnamPro-Bold.ttf"

PER_PAGE = 10  # Số bạn mỗi trang



def load_image(url, size):
    # nếu link avatar rỗng → trả về ảnh màu xám
    if not url or url.strip() == "":
        return Image.new("RGBA", (size, size), (120,120,120,255))

    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            raise Exception("bad status")

        im = Image.open(BytesIO(r.content)).convert("RGBA")

        return im.resize((size, size), Image.LANCZOS)

    except:
        # fallback an toàn
        return Image.new("RGBA", (size, size), (120,120,120,255))



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
    try:
        import random
        img = load_image_from_url(random.choice(bg_urls))
        return img.resize(size, Image.LANCZOS)
    except:
        return Image.new("RGBA", size, (25,20,40,255))


def format_last_online(ts):
    import time
    if not ts:
        return "Không rõ"

    now = int(time.time())
    diff = now - ts

    if diff < 60:
        return "Hoạt động: Vừa xong"
    if diff < 3600:
        return f"Hoạt động: {diff//60} phút trước"
    if diff < 86400:
        return f"Hoạt động: {diff//3600} giờ trước"
    if diff < 86400 * 7:
        return f"Hoạt động: {diff//86400} ngày trước"

    # Lâu quá → format ngày tháng
    return time.strftime("Hoạt động: %d/%m/%Y", time.localtime(ts))



def friend_card(draw, bg, cx, cy, name, uid, avatar_url, last_online_text):
    CARD_W = 880
    CARD_H = 380
    radius = 45


    neon = [
        (255,0,0,130),(255,127,0,130),(255,255,0,130),
        (0,255,0,130),(0,255,255,130),(0,127,255,130),
        (139,0,255,130)
    ]
    for g, col in enumerate(neon, 1):
        draw.rounded_rectangle(
            [cx-g, cy-g, cx+CARD_W+g, cy+CARD_H+g],
            radius=radius+g,
            outline=col,
            width=2
        )


    glass_h = 180
    glass_y = cy + CARD_H - glass_h

    area = bg.crop((cx, glass_y, cx+CARD_W, glass_y+glass_h)).filter(ImageFilter.GaussianBlur(6))
    overlay = Image.new("RGBA", (CARD_W, glass_h), (22,28,45,115))
    glass = Image.alpha_composite(area, overlay)

    mask = Image.new("L", (CARD_W, glass_h), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([0,0,CARD_W,glass_h], radius=radius, fill=255)
    bg.paste(glass, (cx, glass_y), mask)


    ICON_SIZE = 170
    av = load_image(avatar_url, ICON_SIZE)

    mask_icon = Image.new("L", (ICON_SIZE, ICON_SIZE), 0)
    di = ImageDraw.Draw(mask_icon)
    di.ellipse((0,0,ICON_SIZE,ICON_SIZE), fill=255)

    icon_final = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0,0,0,0))
    icon_final.paste(av, (0,0), mask_icon)

    icon_x = cx + CARD_W//2 - ICON_SIZE//2
    icon_y = cy + 25
    bg.alpha_composite(icon_final, (icon_x, icon_y))


    font_name = ImageFont.truetype(FONT, 48)
    font_uid  = ImageFont.truetype(FONT, 30)
    font_last = ImageFont.truetype(FONT, 28)

    # Giới hạn tên
    if len(name) > 20:
        name = name[:20] + "…"


    text_y = glass_y + 22

    # Tên
    draw.text(
        (cx + CARD_W//2 - font_name.getlength(name)//2, text_y),
        name, font=font_name, fill="white"
    )

    # UID — luôn hiển thị
    draw.text(
        (cx + CARD_W//2 - font_uid.getlength(f'UID: {uid}')//2, text_y + 70),
        f"UID: {uid}",
        font=font_uid,
        fill="#C8E2FF"
    )


    if last_online_text and last_online_text != "Không rõ":
        draw.text(
            (cx + CARD_W//2 - font_last.getlength(last_online_text)//2, text_y + 120),
            last_online_text,
            font=font_last,
            fill="#8DD7FF"
        )

    return cy + CARD_H + 45




def render_page(friends):


    friends = friends[:8]


    CARD_W = 920
    CARD_H = 330

    GRID_SPACING_X = 60
    GRID_SPACING_Y = 100


    W = 2000
    H = 1600

    bg = get_bg_image((W, H))
    draw = ImageDraw.Draw(bg)


    title_font = ImageFont.truetype(FONT, 85)
    title = "DANH SÁCH BẠN BÈ"
    draw.text(
        (W // 2 - title_font.getlength(title) // 2, 65),
        title, font=title_font, fill=(0, 255, 255)
    )


    x1 = W // 2 - CARD_W - GRID_SPACING_X // 2
    x2 = W // 2 + GRID_SPACING_X // 2


    top_y = 220


    bottom_y = top_y + CARD_H + GRID_SPACING_Y


    for i in range(min(4, len(friends))):

        name, uid, av, last_text = friends[i]

        col = i % 2        # 0 = trái, 1 = phải
        row = i // 2       # 0 = row 1, 1 = row 2

        x = x1 if col == 0 else x2
        y = top_y + row * (CARD_H + GRID_SPACING_Y)

        friend_card(draw, bg, x, y, name, uid, av, last_text)


    for i in range(4, min(8, len(friends))):

        name, uid, av, last_text = friends[i]

        col = i % 2
        row = (i - 4) // 2

        x = x1 if col == 0 else x2
        y = bottom_y + row * (CARD_H + GRID_SPACING_Y)

        friend_card(draw, bg, x, y, name, uid, av, last_text)


    out = os.path.join(CACHE, f"friend_{time.time()}.jpg")
    bg.convert("RGB").save(out, quality=97)

    return out, W, H





def handle_friend_command(message, msg_obj, thread_id, thread_type, author_id, client):
    try:
        page = 1
        parts = str(message).split()
        if len(parts) >= 2:
            try:
                page = max(1, int(parts[1]))
            except:
                page = 1

        frs = client.fetchAllFriends()
        total = len(frs)

        if not total:
            client.sendMessage(Message(text="📭 Không có bạn bè."), thread_id, thread_type)
            return

        start = (page - 1) * PER_PAGE
        end   = start + PER_PAGE

        selected = frs[start:end]
        if not selected:
            client.sendMessage(Message(text=f"⚠️ Trang {page} không tồn tại!"), thread_id, thread_type)
            return

        friends = []
        for fr in selected:
            name = getattr(fr, "zaloName", None) or getattr(fr, "displayName", None) or "Không rõ"
            uid  = getattr(fr, "userId", None)
            av   = getattr(fr, "avatar", None)

            #Lấy Thời gian
            last_seen = getattr(fr, "lastOnline", None) or getattr(fr, "lastSeen", None)
            last_text = format_last_online(last_seen)


            friends.append((name, uid, av, last_text))

        # Truyền vào render_page k được thì lỗi rồi Bii lườii fix=))
        path, W, H = render_page(friends)

        client.sendLocalImage(path, thread_id, thread_type, width=W, height=H)

        try:
            os.remove(path)
        except:
            pass

    except Exception as e:
        client.sendMessage(Message(text=f"❌ Lỗi: {e}"), thread_id, thread_type)


def PTA():
    return {"friend": handle_friend_command}
