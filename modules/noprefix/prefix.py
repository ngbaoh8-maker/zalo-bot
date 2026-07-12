# -*- coding: utf-8 -*-
import os, json, time, random, glob, tempfile, requests
from io import BytesIO
from datetime import datetime, timezone, timedelta
from zlapi.models import Message
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BACKGROUND_PATH = "background"
CACHE_PATH = "modules/cache"
AVATAR_CACHE_DIR = os.path.join(CACHE_PATH, "avatar_cache")

FONT_TEXT  = "arial unicode ms.otf"
FONT_EMOJI = "modules/cache/font/NotoEmoji-Bold.ttf"

os.makedirs(CACHE_PATH, exist_ok=True)
os.makedirs(AVATAR_CACHE_DIR, exist_ok=True)

des = {
    "version": "14.0",
    "credits": "ngbao",
    "description": "Check Prefix",
    "power": "Thành Viên"
}

COOLDOWN = 5
cooldown = {}

F_BIG = None
F_MID = None
F_BOT = None
F_SMALL = None
F_TIME = None
F_EMOJI = None
F_EMOJI_BIG = None


def prf():
    try:
        with open("seting.json", "r", encoding="utf-8") as f:
            return json.load(f).get("prefix", ".")
    except:
        return "."


def _load_font(path, px):
    try:
        if path and os.path.exists(path):
            return ImageFont.truetype(path, px)
    except:
        pass
    return ImageFont.load_default()


def _init_fonts():
    global F_BIG, F_MID, F_BOT, F_SMALL, F_TIME, F_EMOJI, F_EMOJI_BIG
    if F_BIG is not None:
        return
    F_BIG = _load_font(FONT_TEXT, 76)     # tăng nhẹ cho dòng Xin chào đẹp hơn
    F_MID = _load_font(FONT_TEXT, 56)
    F_BOT = _load_font(FONT_TEXT, 46)
    F_SMALL = _load_font(FONT_TEXT, 40)
    F_TIME = _load_font(FONT_TEXT, 50)
    F_EMOJI = _load_font(FONT_EMOJI, 52)
    F_EMOJI_BIG = _load_font(FONT_EMOJI, 150)


def _rand_color(a=255):
    return (random.randint(30, 255), random.randint(30, 255), random.randint(30, 255), a)


def _rand_pastel(a=255):
    return (random.randint(120, 255), random.randint(120, 255), random.randint(120, 255), a)


def _strip_vs(s):
    return s.replace("\ufe0f", "") if s else s


def _is_emoji_char(ch):
    if not ch:
        return False
    o = ord(ch)
    return (
        o > 0xFFFF
        or (0x2600 <= o <= 0x26FF)
        or (0x2700 <= o <= 0x27BF)
        or (0x1F300 <= o <= 0x1FAFF)
        or (0xFE00 <= o <= 0xFE0F)
    )


def _split_mixed_text(text):
    text = _strip_vs(text)
    parts = []
    cur = ""
    cur_is_emoji = None
    for ch in text:
        is_e = _is_emoji_char(ch)
        if cur_is_emoji is None:
            cur_is_emoji = is_e
            cur = ch
            continue
        if is_e == cur_is_emoji:
            cur += ch
        else:
            parts.append((cur, cur_is_emoji))
            cur = ch
            cur_is_emoji = is_e
    if cur:
        parts.append((cur, cur_is_emoji))
    return parts


def _text_bbox(draw, text, font):
    try:
        return draw.textbbox((0, 0), text, font=font)
    except:
        try:
            w, h = draw.textsize(text, font=font)
            return (0, 0, w, h)
        except:
            return (0, 0, 0, 0)


def _text_width(draw, text, font):
    b = _text_bbox(draw, text, font)
    return max(0, b[2] - b[0])


def _choose_font(draw, chunk, font_text, font_emoji):
    if not font_emoji:
        return font_text
    w_emoji = _text_width(draw, chunk, font_emoji)
    w_text = _text_width(draw, chunk, font_text)
    if w_emoji > 0 and w_text <= 0:
        return font_emoji
    if w_text > 0 and w_emoji <= 0:
        return font_text
    if w_emoji >= w_text and w_emoji > 0:
        return font_emoji
    return font_text


def _draw_mixed_colorful(draw, x, y, text, font_text, font_emoji, shadow=None, offset=(2, 2), anchor_center=False):
    if not text:
        return
    parts = _split_mixed_text(text)
    widths = []
    total = 0
    for t, is_e in parts:
        f = _choose_font(draw, t, font_text, font_emoji if is_e else font_text)
        w = _text_width(draw, t, f)
        widths.append((t, is_e, w, f))
        total += w
    cx = x - total // 2 if anchor_center else x
    for t, is_e, w, f in widths:
        fill = _rand_pastel(255) if is_e else _rand_color(255)
        if shadow:
            draw.text((cx + offset[0], y + offset[1]), t, font=f, fill=shadow)
        draw.text((cx, y), t, font=f, fill=fill)
        cx += w


def _pick_background(size):
    try:
        if os.path.isdir(BACKGROUND_PATH):
            files = [
                os.path.join(BACKGROUND_PATH, fn)
                for fn in os.listdir(BACKGROUND_PATH)
                if fn.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
            ]
            if files:
                path = random.choice(files)
                return Image.open(path).convert("RGBA").resize(size, Image.Resampling.LANCZOS)
    except:
        pass
    return Image.new("RGBA", size, (29, 32, 41, 255))


def _download_image(url, timeout=4):
    if not url:
        return None
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return Image.open(BytesIO(r.content)).convert("RGBA")
    except:
        return None


def _avatar_cache_path(uid):
    return os.path.join(AVATAR_CACHE_DIR, f"{uid}.png")


def _read_cached_avatar(uid, max_age_sec=6 * 3600):
    p = _avatar_cache_path(uid)
    try:
        if os.path.exists(p) and (time.time() - os.path.getmtime(p) <= max_age_sec):
            return Image.open(p).convert("RGBA")
    except:
        return None
    return None


def _write_cached_avatar(uid, img):
    p = _avatar_cache_path(uid)
    try:
        img.save(p, "PNG", optimize=False)
    except:
        pass


def _create_circle_avatar(img, size):
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out


def _draw_snow(img, flakes=160):
    W, H = img.size
    snow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(snow)
    for _ in range(flakes):
        x = random.randint(0, W)
        y = random.randint(0, H)
        r = random.randint(1, 3)
        a = random.randint(120, 220)
        d.ellipse((x, y, x + r, y + r), (255, 255, 255, a))
    return Image.alpha_composite(img, snow)


def _draw_neon_card(base_img, box, radius, neon_color):
    W, H = base_img.size
    neon = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(neon)
    for i in range(18):
        alpha = 180 - i * 8
        if alpha <= 0:
            break
        d.rounded_rectangle(
            (box[0] - i, box[1] - i, box[2] + i, box[3] + i),
            radius=radius + i,
            outline=(neon_color[0], neon_color[1], neon_color[2], alpha),
            width=6
        )
    neon = neon.filter(ImageFilter.GaussianBlur(26))
    return Image.alpha_composite(base_img, neon)


def _random_neon_color():
    return random.choice([(0, 255, 255), (255, 0, 255), (0, 255, 120), (255, 80, 0), (120, 0, 255)])


def _get_user_info(client, uid):
    try:
        info = client.fetchUserInfo(uid)
        p = None
        if info and hasattr(info, "changed_profiles") and info.changed_profiles:
            p = info.changed_profiles.get(str(uid)) or info.changed_profiles.get(uid)
        if isinstance(p, dict):
            name = p.get("zaloName") or p.get("displayName") or p.get("name") or f"ID_{uid}"
            avatar_url = p.get("avatar") or p.get("fullAvt")
            return name, avatar_url
        if p:
            name = getattr(p, "zaloName", None) or getattr(p, "displayName", None) or getattr(p, "name", None) or f"ID_{uid}"
            avatar_url = getattr(p, "avatar", None) or getattr(p, "fullAvt", None)
            return name, avatar_url
    except:
        pass
    return f"ID_{uid}", None


def _compose_prefix_card(client, author_id, prefix):
    _init_fonts()

    W, H = 2000, 680
    CARD_W, CARD_H = 1820, 530

    bg = _pick_background((W, H)).filter(ImageFilter.GaussianBlur(5))
    bg = _draw_snow(bg)

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay, "RGBA")

    box_color = random.choice([
        (0, 0, 0, 95),
        (20, 20, 30, 95),
        (40, 10, 60, 95),
        (10, 60, 30, 95),
        (30, 30, 90, 95),
        (138, 3, 3, 95),
    ])

    bx1 = (W - CARD_W) // 2
    by1 = (H - CARD_H) // 2
    bx2 = bx1 + CARD_W
    by2 = by1 + CARD_H

    d.rounded_rectangle((bx1, by1, bx2, by2), radius=95, fill=box_color)

    glass = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glass, "RGBA")
    gd.rounded_rectangle((bx1, by1, bx2, by2), radius=95, fill=(255, 255, 255, 35))
    overlay = Image.alpha_composite(overlay, glass)
    d = ImageDraw.Draw(overlay, "RGBA")

    vn_now = datetime.now(timezone(timedelta(hours=7)))
    formatted_time = vn_now.strftime("%H:%M")
    hour = vn_now.hour
    time_icon = "🌤" if 6 <= hour < 18 else "🌙"

    pad_r = 55
    y_top = by1 + 14

    time_w = _text_width(d, formatted_time, F_TIME)
    icon_w = _text_width(d, time_icon, F_EMOJI)
    gap = 10
    x_time = bx2 - pad_r - (time_w + gap + icon_w)
    x_icon = x_time + time_w + gap

    d.text((x_time + 2, y_top + 2), formatted_time, font=F_TIME, fill=(0, 0, 0, 200))
    d.text((x_time, y_top), formatted_time, font=F_TIME, fill=_rand_color(255))
    d.text((x_icon + 2, y_top + 2), time_icon, font=F_EMOJI, fill=(0, 0, 0, 200))
    d.text((x_icon, y_top), time_icon, font=F_EMOJI, fill=_rand_pastel(255))

    name, avatar_url = _get_user_info(client, author_id)
    uid_str = str(author_id)

    avatar = _read_cached_avatar(uid_str)
    if avatar is None:
        avatar = _download_image(avatar_url, timeout=4)
        if avatar is not None:
            _write_cached_avatar(uid_str, avatar)

    av_size = 235
    av_x = bx1 + 85
    av_y = (by1 + by2 - av_size) // 2

    ring_size = av_size + 20
    ring = Image.new("RGBA", (ring_size, ring_size), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring, "RGBA")
    rd.ellipse([0, 0, ring_size - 1, ring_size - 1], outline=_rand_pastel(255), width=8)
    overlay.paste(ring, (av_x - 10, av_y - 10), ring)

    if avatar is not None:
        av_circle = _create_circle_avatar(avatar, av_size)
        overlay.paste(av_circle, (av_x, av_y), av_circle)
    else:
        d.text((av_x + 20, av_y + 35), "🤖", font=F_EMOJI_BIG, fill=_rand_pastel(255))

    text_left = bx1 + 410
    text_right = bx2 - 420
    center_text_x = (text_left + text_right) // 2
    center_card_x = (bx1 + bx2) // 2

    line_spacing = 94
    yy = by1 + 52

    # FIX FONT DÒNG "Xin chào": vẽ THUẦN TEXT (không emoji) để không ra ô vuông
    greet = f"Xin chào {name}"
    gb = _text_bbox(d, greet, F_BIG)
    gw = gb[2] - gb[0]
    gx = center_text_x - gw // 2
    d.text((gx + 3, yy + 3), greet, font=F_BIG, fill=(0, 0, 0, 210))
    d.text((gx, yy), greet, font=F_BIG, fill=(255, 210, 60, 255))
    yy += line_spacing

    lines = [
        "❄️ Bot đang hoạt động",
        f"🚦 Prefix hiện tại: {prefix}",
        "💎 Bot sẵn sàng phục vụ 💗",
        "🤖 Bot: ngbao 💻 Version: 5.0 📅 14/02/2026",
    ]

    for i, line in enumerate(lines):
        ft = F_MID if i == 0 else (F_BOT if i < 3 else F_SMALL)
        cx = center_card_x if i == 0 else center_text_x
        _draw_mixed_colorful(d, cx, yy, line, ft, F_EMOJI, shadow=(0, 0, 0, 210), anchor_center=True)
        yy += line_spacing

    big_icon = random.choice(["🛠️", "⚙️", "🤖", "🔥", "💎", "✨"])
    x_big = bx2 - 320
    y_big = (by1 + by2) // 2 - 120
    d.text((x_big + 3, y_big + 3), big_icon, font=F_EMOJI_BIG, fill=(0, 0, 0, 200))
    d.text((x_big, y_big), big_icon, font=F_EMOJI_BIG, fill=_rand_pastel(230))

    bottom_icon = random.choice(["✅", "🟢", "✨", "💎"])
    x_bot = bx2 - 140
    y_bot = by2 - 110
    d.text((x_bot + 2, y_bot + 2), bottom_icon, font=F_EMOJI, fill=(0, 0, 0, 200))
    d.text((x_bot, y_bot), bottom_icon, font=F_EMOJI, fill=_rand_pastel(255))

    final = Image.alpha_composite(bg, overlay)
    final = _draw_neon_card(final, (bx1, by1, bx2, by2), 95, _random_neon_color())

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False, dir=CACHE_PATH) as tf:
        out = tf.name
    final.save(out, "PNG", optimize=False, compress_level=1)
    return out, W, H, name


def checkprefix(message, msg_obj, thread_id, thread_type, author_id, client):
    raw = (message or "").strip().lower()
    if raw != "prefix":
        return

    if author_id in cooldown and time.time() - cooldown[author_id] < COOLDOWN:
        return
    cooldown[author_id] = time.time()

    prefix = prf()
    img_path, w, h, name = _compose_prefix_card(client, author_id, prefix)

    try:
        client.sendLocalImage(
            imagePath=img_path,
            message=Message(text=f"🚦 {name}\n🔧 Prefix hiện tại của bot là: {prefix}\n Liên hệ zalo 0911037051 để được hỗ trợ!"),
            thread_id=thread_id,
            thread_type=thread_type,
            width=w,
            height=h,
            ttl=200000
        )
    finally:
        try:
            os.remove(img_path)
        except:
            pass


def PTA():
    return {"prefix": checkprefix}