import os
import json
import random
import time
import requests
import colorsys
from datetime import datetime, timedelta, timezone
from threading import Thread
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import glob

from zlapi.models import *
from modules.AI.pro_gemini import get_user_name_by_id
from config import ADMIN, PREFIX

BACKGROUND_PATH = "background/"
CACHE_PATH = "modules/cache/"

GAME_NAME = "3Q Tam Quốc"
GAME_VERSION = "1.1.2"
GAME_UPDATE = "9-1-26"

DB_USER = os.path.join(CACHE_PATH, "3q_users.json")
DB_LOG_TOWER = os.path.join(CACHE_PATH, "3q_tower_log.json")

OUTPUT_IMAGE_PATH = os.path.join(CACHE_PATH, "3q_menu.png")
OUTPUT_BXH_THAP_PATH = os.path.join(CACHE_PATH, "3q_bxh_thap.png")
OUTPUT_BXH_POWER_PATH = os.path.join(CACHE_PATH, "3q_bxh_power.png")

FONT_ARIAL_PATH = "arial unicode ms.otf"
FONT_EMOJI_PATH = "emoji.ttf"

os.makedirs(CACHE_PATH, exist_ok=True)

des = {
    "version": "1.5.3",
    "credits": "ngbao",
    "description": "Game 3Q Tam Quốc",
    "power": "Thành Viên",
    "update": GAME_UPDATE
}

RARITY_COLOR = {"Cam": "🟠", "Đỏ": "🔴", "Bạch Kim": "⚪"}

ICON_ERR = "✖"
ICON_OK = "✅"

HERO_POOL_F0 = [
    "Tôn Sách", "Chu Du", "Triệu Vân", "Quan Vũ", "Trương Phi", "Lưu Bị",
    "Tào Tháo", "Tôn Quyền", "Gia Cát Lượng", "Tư Mã Ý", "Hoàng Trung",
    "Hứa Chử", "Trương Liêu", "Điển Vi", "Cam Ninh", "Lỗ Túc", "Lữ Mông",
    "Tôn Kiên", "Hạ Hầu Đôn", "Hạ Hầu Uyên"
]

HERO_POOL_F50 = [
    "Lữ Bố", "Điêu Thuyền", "Hạng Vũ", "Hậu Nghệ", "Vu Cát", "Ngưu Ma Vương",
    "Hồng Hài Nhi", "Hằng Nga", "Đại Kiều", "Tiểu Kiều", "Tôn Thượng Hương",
    "Trương Giác", "Viên Thiệu", "Mã Siêu", "Hoàng Cái", "Bàng Thống", "Tả Từ",
    "Quan Bình", "Trương Bao", "Từ Thứ", "Tào Phi", "Tào Nhân", "Tào Hồng",
    "Cự Linh Thần", "Lôi Công Báo", "Tam Tạng", "Thái Ất Chân Nhân", "Đại Thánh",
    "Nhiên Chi Đại Kiều", "Kiện Thân Chu Du"
]

HERO_POOL_F70 = [
    "Kiện Thân Chu Du", "Nhiên Chi Đại Kiều", "Bạch Kim Triệu Vân",
    "Bạch Kim Quan Vũ", "Bạch Kim Trương Phi", "Bạch Kim Tào Tháo",
    "Bạch Kim Gia Cát Lượng", "Bạch Kim Tư Mã Ý", "Bạch Kim Lữ Bố",
    "Bạch Kim Điêu Thuyền", "Đỏ Tôn Sách", "Đỏ Mã Siêu", "Đỏ Hứa Chử",
    "Đỏ Cam Ninh", "Đỏ Trương Liêu", "Đỏ Điển Vi", "Đỏ Lữ Mông", "Đỏ Hoàng Trung",
    "Đỏ Hạ Hầu Đôn", "Đỏ Hạ Hầu Uyên"
]

ITEM_LIBRARY = {
    "linhdao": {"name": "🍑 Linh Đào", "desc": "Hồi sinh khi tử nạn", "type": "consumable"},
    "huyentrai": {"name": "🍇 Huyễn Trái", "desc": "Dùng để leo Tháp", "type": "consumable"},
    "vequay": {"name": "🎟️ Vé chiêu mộ", "desc": "Dùng để quay tướng", "type": "ticket"},
    "baoruong": {"name": "🎁 Bảo rương", "desc": "Mở ra quà ngẫu nhiên", "type": "box"},
    "linhnguyen": {"name": "🍥 Linh Nguyên", "desc": "EXP trùng sinh (dùng bồi EXP)", "type": "exp"}
}

SHOP_ITEMS = {
    "vequay": {"price_gold": 1000, "price_gem": 0, "bundle": 1},
    "huyentrai": {"price_gold": 800, "price_gem": 0, "bundle": 1},
    "linhdao": {"price_gold": 1200, "price_gem": 0, "bundle": 1},
    "baoruong": {"price_gold": 5000, "price_gem": 2, "bundle": 1}
}

HUONG_DAN_TEXT = """🚦@{name}
📣Update 20/08/25:

 ➜ Đăng ký tranh cúp 🏆 trước 9h hàng ngày.
 ➜ Mở 🎁 Bảo rương có cơ hội nhận: 💰 Vàng, 🎟️ Vé Quay, 🍇 Huyễn Trái, 🍑 Linh Đào.
 ➜ Quay tướng x10. Chỉ cho tướng vàng. Tướng Đỏ và Bạch Kim người chơi phải nâng sao và đột phá lên
 ➜ PVP, leo Thông Thiên Tháp và Săn Boss để nâng tướng
 ➜ Chọn tướng chính khác thay cho tướng hiện thì lượng Exp sẽ chuyển thành 🍥 Linh Nguyên 60%
    Dùng 👉 {prefix}3q dung linhnguyen <id> để lên cấp
 ➜ Điểm danh hàng ngày để nhận quà

➡️ Khái niệm trong game:

 ➜ 💎 Linh thạch
 ➜ 🎟️ Vé quay tướng
 ➜ 🍥 Linh nguyên
 ➜ 🍑 Linh Đào
 ➜ 🍇 Huyễn Trái
 ➜ 🎁 Bảo rương
 ➜ 💰 Vàng
 ➜ 🧩 Mảnh tướng
"""


def load_json(path, default):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def is_admin_user(uid):
    try:
        if isinstance(ADMIN, (list, tuple, set)):
            return str(uid) in [str(x) for x in ADMIN]
        return str(uid) == str(ADMIN)
    except:
        return False


def get_user_display_name(bot, uid):
    try:
        user_info = bot.fetchUserInfo(uid)
        if user_info and hasattr(user_info, "changed_profiles"):
            key = str(uid)
            if key in user_info.changed_profiles:
                u = user_info.changed_profiles[key]
                name = getattr(u, "name", None) or getattr(u, "displayName", None)
                if name and name.strip():
                    return name.strip()
    except:
        pass
    try:
        return get_user_name_by_id(bot, uid)
    except:
        return f"User_{uid}"


def mention_header(name: str) -> str:
    return f"🚦@{name}"


# ✅ HIỂN THỊ LỆNH KHÔNG BỊ “#” TRONG MENU (không ảnh hưởng parser lệnh)
def display_prefix(p: str) -> str:
    if not p:
        return ""
    return p.lstrip("#")


# ✅ TÍNH OFFSET/LENGTH THEO UTF-16 (fix tag xanh trong group + tránh nhân đôi tên)
def _utf16_len(s: str) -> int:
    if not s:
        return 0
    try:
        return len(s.encode("utf-16-le")) // 2
    except:
        return len(s)


def build_mentions_from_text(text: str, pairs):
    if not text or not pairs:
        return None

    mentions = []
    for uid, name in pairs:
        tag = f"@{name}"

        # ưu tiên tag ở dòng đầu "🚦@name"
        off = -1
        if text.startswith("🚦@"):
            end = text.find("\n")
            if end == -1:
                end = len(text)
            first_line = text[:end]
            off = first_line.find(tag)
            if off >= 0:
                off = off  # giữ nguyên trong toàn text (vì first_line bắt đầu từ 0)

        if off < 0:
            off = text.find(tag)

        if off < 0:
            continue

        offset = _utf16_len(text[:off])
        length = _utf16_len(tag)
        try:
            mentions.append(Mention(uid, length=length, offset=offset))
        except:
            pass

    if not mentions:
        return None
    return mentions if len(mentions) > 1 else mentions[0]


def reply_mention(bot, message_object, thread_id, thread_type, uid, name: str, text: str):
    m = build_mentions_from_text(text, [(uid, name)])
    bot.replyMessage(
        Message(text=text, mention=m),
        message_object,
        thread_id=thread_id,
        thread_type=thread_type
    )


def send_mention(bot, thread_id, thread_type, uid, name: str, text: str):
    m = build_mentions_from_text(text, [(uid, name)])
    bot.sendMessage(
        Message(text=text, mention=m),
        thread_id=thread_id,
        thread_type=thread_type
    )


def extract_first_mention_uid(message_object):
    try:
        if hasattr(message_object, "mention") and message_object.mention:
            m = message_object.mention[0] if isinstance(message_object.mention, list) else message_object.mention
            for k in ("user_id", "uid", "id"):
                v = getattr(m, k, None)
                if v:
                    return str(v)
    except:
        pass
    try:
        if hasattr(message_object, "mentions") and message_object.mentions:
            m = message_object.mentions[0] if isinstance(message_object.mentions, list) else message_object.mentions
            for k in ("user_id", "uid", "id"):
                v = getattr(m, k, None)
                if v:
                    return str(v)
    except:
        pass
    return None


# =========================
# ✅ FIX ICON Ô VUÔNG (MENU IMAGE)
# - strip FE0F
# - fallback font theo độ rộng glyph
# =========================
def _strip_vs(text: str) -> str:
    if not text:
        return text
    return text.replace("\ufe0f", "")


def _is_emoji_char(ch: str) -> bool:
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


def _split_mixed_text(text: str):
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


def _text_bbox(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont):
    try:
        return draw.textbbox((0, 0), text, font=font)
    except:
        try:
            w, h = draw.textsize(text, font=font)
            return (0, 0, w, h)
        except:
            return (0, 0, 0, 0)


def _text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    b = _text_bbox(draw, text, font)
    return max(0, b[2] - b[0])


def _choose_font_for_chunk(draw, chunk: str, font_text, font_emoji):
    if not font_emoji:
        return font_text
    w_emoji = _text_width(draw, chunk, font_emoji)
    w_text = _text_width(draw, chunk, font_text)
    if w_emoji <= 0 and w_text > 0:
        return font_text
    if w_text <= 0 and w_emoji > 0:
        return font_emoji
    if w_emoji >= w_text and w_emoji > 0:
        return font_emoji
    return font_text


def draw_mixed(draw, x, y, text, font_text, font_emoji, fill, shadow=(0, 0, 0, 160), offset=(2, 2), anchor_center=False):
    parts = _split_mixed_text(text)
    widths = []
    total = 0

    for t, is_e in parts:
        f = _choose_font_for_chunk(draw, t, font_text, font_emoji if is_e else font_text)
        w = _text_width(draw, t, f)
        widths.append((w, f))
        total += w

    cx = x - total // 2 if anchor_center else x
    for (t, _), (w, f) in zip(parts, widths):
        draw.text((cx + offset[0], y + offset[1]), t, font=f, fill=shadow)
        draw.text((cx, y), t, font=f, fill=fill)
        cx += w


def download_avatar_url(url, save_path):
    if not url:
        return None
    try:
        resp = requests.get(url, stream=True, timeout=10)
        if resp.status_code == 200:
            with open(save_path, "wb") as f:
                for chunk in resp.iter_content(1024):
                    f.write(chunk)
            return save_path
    except:
        return None
    return None


def download_avatar_for_uid(bot, uid):
    try:
        user_info = bot.fetchUserInfo(uid)
        avatar_url = None
        if user_info and hasattr(user_info, "changed_profiles"):
            key = str(uid)
            if key in user_info.changed_profiles:
                avatar_url = getattr(user_info.changed_profiles[key], "avatar", None)
        if not avatar_url:
            return None
        path = os.path.join(CACHE_PATH, f"av_{str(uid)}.png")
        return download_avatar_url(avatar_url, path)
    except:
        return None


def generate_3q_menu_image(bot, author_id):
    images = (
        glob.glob(os.path.join(BACKGROUND_PATH, "*.jpg"))
        + glob.glob(os.path.join(BACKGROUND_PATH, "*.png"))
        + glob.glob(os.path.join(BACKGROUND_PATH, "*.jpeg"))
    )
    if not images:
        return None

    image_path = random.choice(images)
    try:
        W, H = 2000, 680
        CARD_W, CARD_H = 1820, 530  # giống bản 2

        bg = Image.open(image_path).convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)
        bg = bg.filter(ImageFilter.GaussianBlur(radius=7))

        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(overlay)

        box_color = random.choice([
            (0, 0, 0, 95),
            (20, 20, 30, 95),
            (40, 10, 60, 95),
            (10, 60, 30, 95),
            (30, 30, 90, 95),
        ])

        box_x1 = (W - CARD_W) // 2
        box_y1 = (H - CARD_H) // 2
        box_x2 = box_x1 + CARD_W
        box_y2 = box_y1 + CARD_H

        d.rounded_rectangle([(box_x1, box_y1), (box_x2, box_y2)], radius=95, fill=box_color)

        glass = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glass)
        gd.rounded_rectangle([(box_x1, box_y1), (box_x2, box_y2)], radius=95, fill=(255, 255, 255, 35))
        overlay = Image.alpha_composite(overlay, glass)
        d = ImageDraw.Draw(overlay)

        try:
            f_big = ImageFont.truetype(FONT_ARIAL_PATH, 90)
            f_mid = ImageFont.truetype(FONT_ARIAL_PATH, 66)
            f_small = ImageFont.truetype(FONT_ARIAL_PATH, 58)
            f_bot = ImageFont.truetype(FONT_ARIAL_PATH, 54)
            f_time = ImageFont.truetype(FONT_ARIAL_PATH, 60)
            f_emoji = ImageFont.truetype(FONT_EMOJI_PATH, 62)
            f_emoji_big = ImageFont.truetype(FONT_EMOJI_PATH, 185)
        except:
            f_big = f_mid = f_small = f_bot = f_time = ImageFont.load_default()
            f_emoji = f_emoji_big = ImageFont.load_default()

        vn_now = datetime.now(timezone(timedelta(hours=7)))
        hour = vn_now.hour
        formatted_time = vn_now.strftime("%H:%M")
        time_icon = "☀" if 6 <= hour < 18 else "☾"
        draw_mixed(d, box_x2 - 315, box_y1 + 14, f"{time_icon} {formatted_time}",
                   f_time, f_emoji, (255, 255, 255, 220), shadow=(0, 0, 0, 200))

        avatar_path = download_avatar_for_uid(bot, author_id)
        av_size = 235
        av_x = box_x1 + 85
        av_y = (box_y1 + box_y2 - av_size) // 2

        if avatar_path and os.path.exists(avatar_path):
            av = Image.open(avatar_path).convert("RGBA").resize((av_size, av_size), Image.Resampling.LANCZOS)
            mask = Image.new("L", (av_size, av_size), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, av_size, av_size), fill=255)

            ring_size = av_size + 20
            ring = Image.new("RGBA", (ring_size, ring_size), (0, 0, 0, 0))
            rd = ImageDraw.Draw(ring)
            for i in range(360):
                h = i / 360
                rr, gg, bb = colorsys.hsv_to_rgb(h, 1.0, 1.0)
                rd.arc([(0, 0), (ring_size - 1, ring_size - 1)], i, i + 1,
                       fill=(int(rr * 255), int(gg * 255), int(bb * 255), 255), width=8)
            overlay.paste(ring, (av_x - 10, av_y - 10), ring)
            overlay.paste(av, (av_x, av_y), mask)
        else:
            draw_mixed(d, av_x + 70, av_y + 30, "🐳", f_emoji_big, f_emoji_big,
                       (255, 255, 255, 230), shadow=(0, 0, 0, 220))

        uname = get_user_display_name(bot, author_id)
        greeting_name = "Chủ Nhân" if is_admin_user(author_id) else uname
        pfx = getattr(bot, "prefix", PREFIX)

        line1 = f"Hi, {greeting_name}"
        line2 = f"♡ Chào mừng đến với Game  3Q v{GAME_VERSION}"
        line3 = f"{pfx}3q on/off:  Bật/Tắt tính năng"
        line4 = "😁 Bot sẵn sàng phục  ♡"
        line5 = f"🤖Bot: {des['credits']}  💻Version: {getattr(bot, 'version', des['version'])}  📅Update: {GAME_UPDATE}"

        lines = [
            (line1, f_big, (220, 255, 220, 255)),
            (line2, f_mid, (255, 200, 230, 255)),
            (line3, f_small, (255, 255, 255, 235)),
            (line4, f_small, (255, 255, 255, 235)),
            (line5, f_bot, (255, 255, 255, 235)),
        ]

        text_left = box_x1 + 410
        text_right = box_x2 - 420
        yy = box_y1 + 52
        for text, ft, col in lines:
            cx = (text_left + text_right) // 2
            draw_mixed(d, cx, yy, text, ft, f_emoji, col, shadow=(0, 0, 0, 210), anchor_center=True)
            yy += 94

        draw_mixed(d, box_x2 - 285, (box_y1 + box_y2) // 2 - 100, "🔬",
                   f_emoji_big, f_emoji_big, (60, 60, 60, 255), shadow=(0, 0, 0, 230))

        final = Image.alpha_composite(bg, overlay)
        final.save(OUTPUT_IMAGE_PATH, "PNG", quality=95)
        return OUTPUT_IMAGE_PATH
    except:
        return None


def ensure_user(db, uid):
    uid = str(uid)
    if uid not in db:
        db[uid] = {
            "main_hero_id": None,
            "heroes": {},
            "inventory": {
                "vequay": 999,
                "huyentrai": 50,
                "linhdao": 20,
                "linhnguyen": 20000,
                "baoruong": 0,
                "gold": 70000,
                "gem": 10,
                "vip": 0,
                "shards": {}
            },
            "tower_floor": 1,
            "power": 0,
            "last_checkin": 0,
            "pvp_dead_until": 0
        }
    if "inventory" not in db[uid]:
        db[uid]["inventory"] = {}
    if "shards" not in db[uid]["inventory"]:
        db[uid]["inventory"]["shards"] = {}
    if "heroes" not in db[uid]:
        db[uid]["heroes"] = {}
    return db[uid]


def get_available_heroes(tower_floor):
    pool = list(HERO_POOL_F0)
    if int(tower_floor) >= 50:
        pool += HERO_POOL_F50
    if int(tower_floor) >= 70:
        pool += HERO_POOL_F70
    return pool


def roll_rarity(tower_floor):
    tf = int(tower_floor)
    r = random.random()
    if tf >= 70:
        if r < 0.08:
            return "Bạch Kim"
        if r < 0.28:
            return "Đỏ"
        return "Cam"
    if tf >= 50:
        if r < 0.04:
            return "Đỏ"
        return "Cam"
    return "Cam"


def new_hero(hero_name, rarity="Cam"):
    base_pow = random.randint(1800, 3200)
    atk = random.randint(180, 320)
    hp = random.randint(1800, 3800)
    df = random.randint(150, 320)
    spd = random.randint(4, 25)
    crit = round(random.uniform(7.5, 10.5), 2)
    crit_dmg = round(random.uniform(75, 90), 2)
    acc = round(random.uniform(90, 97), 2)
    dodge = round(random.uniform(5.5, 8.5), 2)
    counter = round(random.uniform(5.5, 8.0), 2)
    anti_crit = round(random.uniform(4.5, 6.0), 2)
    anti_counter = round(random.uniform(4.5, 7.0), 2)
    hid = f"{random.randint(0, 0xFFFFFF):06x}"
    return {
        "id": hid,
        "name": hero_name,
        "rarity": rarity,
        "level": 1,
        "exp": 0,
        "exp_need": 1000,
        "star": 0,
        "breakthrough": 0,
        "power": base_pow,
        "stats": {
            "atk": atk,
            "hp": hp,
            "def": df,
            "spd": spd,
            "crit": crit,
            "crit_dmg": crit_dmg,
            "acc": acc,
            "dodge": dodge,
            "counter": counter,
            "anti_crit": anti_crit,
            "anti_counter": anti_counter
        },
        "equip": {}
    }


def calc_power(hero):
    s = hero["stats"]
    powv = int(s["atk"] * 5 + s["hp"] * 1 + s["def"] * 4 + s["spd"] * 20)
    powv += int(hero.get("star", 0) * 250 + hero.get("breakthrough", 0) * 600)
    hero["power"] = powv
    return powv


def gold_to_van(gold):
    try:
        return f"{gold/10000:.1f} vạn"
    except:
        return "0.0 vạn"


def menu_text(owner_name, prefix):
    p = display_prefix(prefix)
    return (
        f"{mention_header(owner_name)}\n"
        f"📖 Game 3Q v{GAME_VERSION}\n"
        f"   ➜ {p}3q quay: 🎰 Quay tướng mới\n"
        f"   ➜ {p}3q chon <id>: 🎯 Chọn tướng chính\n"
        f"   ➜ {p}3q tuong/@tag: 🐉 Xem tướng chính\n"
        f"   ➜ {p}3q tuido/@tag: 🎒 Túi đồ\n"
        f"   ➜ {p}3q soi <item>: 🔎 Xem vật phẩm\n"
        f"   ➜ {p}3q dung <item> [id]: 🥤 Dùng vật phẩm\n"
        f"   ➜ {p}3q huy <item> <sl>: 🗑️ Hủy vật phẩm\n"
        f"   ➜ {p}3q leothap: 🏯 Leo Thông Thiên Tháp\n"
        f"   ➜ {p}3q leothaps: ⚡ Leo tháp nhanh\n"
        f"   ➜ {p}3q soithap: 🔎 Lịch sử leo tháp\n"
        f"   ➜ {p}3q pvp: ⚔️ PVP\n"
        f"   ➜ {p}3q danhboss: 🗡️ Săn Boss\n"
        f"   ➜ {p}3q diemdanh: 📅 Điểm danh\n"
        f"   ➜ {p}3q shop: 🛍️ Cửa hàng\n"
        f"   ➜ {p}3q mua <item> <sl>: 🛒 Mua vật phẩm\n"
        f"   ➜ {p}3q nap <sl> @tag: 💳 Admin nạp\n"
        f"   ➜ {p}3q bxh: 🎖️ BXH Lực chiến\n"
        f"   ➜ {p}3q bxhthap: 🏯 BXH Tháp\n"
        f"   ➜ {p}3q huongdan: 📄 Hướng dẫn\n"
        f"   ➜ {p}3q rest: 🔄 Reset\n"
    )


def format_hero_detail(owner_name, hero, show_level=True):
    rarity = hero["rarity"]
    s = hero["stats"]
    lines = []
    lines.append(f"{mention_header(owner_name)}")
    lines.append("🔖 Chúc mừng! 🎁")
    lines.append(f"🐉 {hero['name']} ({hero['id']})")
    lines.append(f"💪 Lực chiến: {hero['power']:,}")
    if show_level:
        lines.append(f"🏅 Cấp: {hero['level']}")
        lines.append(f"🆙 EXP: {hero['exp']:,}/{hero['exp_need']:,}")
    lines.append(f"🪬 Phẩm: {rarity} {RARITY_COLOR.get(rarity,'')}")
    lines.append("🧬 Chỉ số tăng thêm:")
    lines.append(f"➜ ⚔️ Công: {s['atk']}")
    lines.append(f"➜ ❤️ HP: {s['hp']:,}")
    lines.append(f"➜ 🛡️ Thủ: {s['def']}")
    lines.append(f"➜ ⚡ Tốc: {s['spd']}")
    lines.append(f"➜ 💢 Bạo Kích: {s['crit']}%")
    lines.append(f"➜ 💥 Sát Thương Bạo: {s['crit_dmg']}%")
    lines.append(f"➜ 🎯 Chính Xác: {s['acc']}%")
    lines.append(f"➜ 🌀 Né Tránh: {s['dodge']}%")
    lines.append(f"➜ 🔁 Phản Đòn: {s['counter']}%")
    lines.append(f"➜ 🔰 Kháng Bạo: {s['anti_crit']}%")
    lines.append(f"➜ 💫 Kháng Phản: {s['anti_counter']}%")
    return "\n".join(lines)


def format_spin_result(owner_name, hero_main, pulled_heroes, tickets_left, pfx):
    rarity = hero_main["rarity"]
    s = hero_main["stats"]
    lines = []
    lines.append(mention_header(owner_name))
    lines.append("Chúc mừng bạn chiêu mộ được tướng mới! 🎊")
    lines.append(f"🐉 {hero_main['name']}")
    lines.append(f"💪 Lực chiến: {hero_main['power']:,}")
    lines.append(f"🛡️ Thủ: {s['def']}")
    lines.append(f"🪬 Phẩm: {rarity} {RARITY_COLOR.get(rarity,'')}")
    lines.append("")
    lines.append("🎰 Kết quả x10 lượt chiêu mộ:")
    for h in pulled_heroes:
        lines.append(f"🐉 {h['name']}")
    lines.append("")
    lines.append(f"🎟️ Vé chiêu mộ còn lại: x{tickets_left}")
    lines.append(f"👉 Dùng {display_prefix(pfx)}3q chon {hero_main['id']} để chọn làm tướng chính!")
    return "\n".join(lines)


def cmd_quay(bot, uid, udb, pfx):
    inv = udb["inventory"]
    if inv.get("vequay", 0) < 10:
        owner = get_user_display_name(bot, uid)
        return f"{mention_header(owner)}\n{ICON_ERR} Bạn không đủ 🎟️ Vé chiêu mộ (cần x10).\nMua thêm bằng: {display_prefix(pfx)}3q shop / {display_prefix(pfx)}3q mua vequay 10"

    inv["vequay"] -= 10
    tf = int(udb.get("tower_floor", 1))
    pool = get_available_heroes(tf)

    pulled = []
    for _ in range(10):
        name = random.choice(pool)
        rarity = roll_rarity(tf)
        h = new_hero(name, rarity=rarity)
        calc_power(h)
        udb["heroes"][h["id"]] = h
        pulled.append(h)

    main = random.choice(pulled)
    if not udb["main_hero_id"]:
        udb["main_hero_id"] = main["id"]
    udb["power"] = max(int(udb.get("power", 0)), int(main["power"]))

    owner_name = get_user_display_name(bot, uid)
    return format_spin_result(owner_name, main, pulled, inv.get("vequay", 0), pfx)


def cmd_chon(bot, uid, udb, hero_id, pfx):
    hero = udb["heroes"].get(hero_id)
    owner = get_user_display_name(bot, uid)
    if not hero:
        return f"{mention_header(owner)}\n{ICON_ERR} Không tìm thấy tướng ID `{hero_id}`.\nDùng {display_prefix(pfx)}3q tuido để xem danh sách!"
    udb["main_hero_id"] = hero_id
    calc_power(hero)
    return format_hero_detail(owner, hero, show_level=True)


def cmd_tuong(bot, users_db, target_uid, pfx):
    tuid = str(target_uid)
    owner = get_user_display_name(bot, tuid)
    if tuid not in users_db:
        return f"{mention_header(owner)}\n📭 Người chơi chưa có dữ liệu game."
    tdb = users_db[tuid]
    mid = tdb.get("main_hero_id")
    if not mid or mid not in tdb.get("heroes", {}):
        return f"{mention_header(owner)}\n{ICON_ERR} Chưa chọn tướng chính.\nDùng: {display_prefix(pfx)}3q quay rồi {display_prefix(pfx)}3q chon <id>"
    hero = tdb["heroes"][mid]
    calc_power(hero)
    return format_hero_detail(owner, hero, show_level=True)


def cmd_tuido(bot, users_db, target_uid):
    tuid = str(target_uid)
    owner = get_user_display_name(bot, tuid)
    if tuid not in users_db:
        return f"{mention_header(owner)}\n📭 Người chơi chưa có dữ liệu game."
    tdb = users_db[tuid]
    inv = tdb.get("inventory", {})
    heroes = tdb.get("heroes", {})
    lines = []
    lines.append(mention_header(owner))
    lines.append("📢 Túi đồ 🎒:")
    lines.append(f"- 💎 Linh thạch: x{inv.get('gem',0)}")
    lines.append(f"- 🍥 Linh nguyên: x{int(inv.get('linhnguyen',0)):,} Exp")
    lines.append(f"- 🎟️ Vé quay: x{inv.get('vequay',0)}")
    lines.append(f"- 🍑 Linh Đào: x{inv.get('linhdao',0)}")
    lines.append(f"- 🍇 Huyễn Trái: x{inv.get('huyentrai',0)}")
    lines.append(f"- 💰 Vàng: {gold_to_van(inv.get('gold',0))}")
    lines.append(f"- 🎁 Bảo rương: x{inv.get('baoruong',0)}")
    for hid, h in list(heroes.items())[:120]:
        lines.append(f"- 🐉 {h['name']} ({hid})")
    return "\n".join(lines)


def cmd_soi(bot, uid, udb, item_key):
    owner = get_user_display_name(bot, uid)
    inv = udb["inventory"]
    if item_key not in ITEM_LIBRARY and item_key not in inv:
        return f"{mention_header(owner)}\n{ICON_ERR} Không có vật phẩm `{item_key}`."
    if item_key in ITEM_LIBRARY:
        it = ITEM_LIBRARY[item_key]
        qty = inv.get(item_key, 0)
        if item_key == "linhnguyen":
            return f"{mention_header(owner)}\n🔎 {it['name']}\n📝 {it['desc']}\n📦 Số lượng: x{int(qty):,} Exp"
        return f"{mention_header(owner)}\n🔎 {it['name']}\n📝 {it['desc']}\n📦 Số lượng: x{qty}"
    return f"{mention_header(owner)}\n🔎 {item_key}: {inv.get(item_key,0)}"


def cmd_huy(bot, uid, udb, item_key, qty):
    owner = get_user_display_name(bot, uid)
    inv = udb["inventory"]
    try:
        qty = max(1, int(qty))
    except:
        qty = 1
    if inv.get(item_key, 0) < qty:
        return f"{mention_header(owner)}\n{ICON_ERR} Không đủ `{item_key}` để hủy. Bạn có: x{inv.get(item_key,0)}"
    inv[item_key] -= qty
    return f"{mention_header(owner)}\n🗑️ Đã hủy `{item_key}` x{qty}. Còn lại: x{inv.get(item_key,0)}"


def cmd_dung(bot, uid, udb, item_key, hero_id=None):
    owner = get_user_display_name(bot, uid)
    inv = udb["inventory"]

    if item_key == "linhnguyen":
        gain = 2000
        if int(inv.get("linhnguyen", 0)) < gain:
            return f"{mention_header(owner)}\n{ICON_ERR} Không đủ 🍥 Linh nguyên (cần {gain:,} Exp)."
        target_id = hero_id or udb.get("main_hero_id")
        if not target_id or target_id not in udb["heroes"]:
            return f"{mention_header(owner)}\n{ICON_ERR} Chưa có tướng để dùng 🍥 Linh nguyên."
        hero = udb["heroes"][target_id]
        inv["linhnguyen"] = int(inv.get("linhnguyen", 0)) - gain
        before = dict(hero["stats"])

        hero["exp"] += gain
        leveled = 0
        while hero["exp"] >= hero["exp_need"]:
            hero["exp"] -= hero["exp_need"]
            hero["level"] += 1
            hero["exp_need"] = int(hero["exp_need"] * 1.15)
            hero["stats"]["atk"] += random.randint(10, 30)
            hero["stats"]["hp"] += random.randint(120, 280)
            hero["stats"]["def"] += random.randint(10, 30)
            hero["stats"]["spd"] += random.randint(1, 6)
            leveled += 1
            if leveled >= 10:
                break

        calc_power(hero)

        lines = []
        lines.append(mention_header(owner))
        lines.append("🔖 Chúc mừng! 🎁")
        lines.append(f"🐉 {hero['name']} đã thăng cấp lên {hero['level']}!")
        lines.append(f"🆙 EXP: {hero['exp']:,}/{hero['exp_need']:,}")
        lines.append("🧬 Chỉ số tăng thêm:")
        lines.append(f"➜ ⚔️ Công: {hero['stats']['atk']} (🔼+{hero['stats']['atk'] - before['atk']})")
        lines.append(f"➜ ❤️ HP: {hero['stats']['hp']:,} (🔼+{hero['stats']['hp'] - before['hp']})")
        lines.append(f"➜ 🛡️ Thủ: {hero['stats']['def']} (🔼+{hero['stats']['def'] - before['def']})")
        lines.append(f"➜ ⚡ Tốc: {hero['stats']['spd']} (🔼+{hero['stats']['spd'] - before['spd']})")
        lines.append(f"➜ 💢 Bạo Kích: {hero['stats']['crit']}%")
        lines.append(f"➜ 💥 Sát Thương Bạo: {hero['stats']['crit_dmg']}%")
        lines.append(f"➜ 🎯 Chính Xác: {hero['stats']['acc']}%")
        lines.append(f"➜ 🌀 Né Tránh: {hero['stats']['dodge']}%")
        lines.append(f"➜ 🔁 Phản Đòn: {hero['stats']['counter']}%")
        lines.append(f"➜ 🔰 Kháng Bạo: {hero['stats']['anti_crit']}%")
        lines.append(f"➜ 💫 Kháng Phản: {hero['stats']['anti_counter']}%")
        return "\n".join(lines)

    if inv.get(item_key, 0) <= 0:
        return f"{mention_header(owner)}\n{ICON_ERR} Bạn không có `{item_key}` trong túi."

    if item_key == "baoruong":
        inv["baoruong"] -= 1
        rewards = []
        gold = random.randint(2000, 10000)
        inv["gold"] = inv.get("gold", 0) + gold
        rewards.append(f"💰 Gold +{gold:,}")
        if random.random() < 0.55:
            inv["vequay"] = inv.get("vequay", 0) + 1
            rewards.append("🎟️ Vé quay +1")
        if random.random() < 0.35:
            inv["huyentrai"] = inv.get("huyentrai", 0) + 1
            rewards.append("🍇 Huyễn Trái +1")
        if random.random() < 0.22:
            inv["linhdao"] = inv.get("linhdao", 0) + 1
            rewards.append("🍑 Linh Đào +1")
        return f"{mention_header(owner)}\n🎁 Mở Bảo rương thành công!\n" + " , ".join(rewards)

    inv[item_key] -= 1
    itname = ITEM_LIBRARY.get(item_key, {}).get("name", item_key)
    return f"{mention_header(owner)}\n🥤 Đã dùng {itname}! (còn x{inv.get(item_key,0)})"


def _tower_enemy_name(floor: int) -> str:
    if floor <= 10:
        return random.choice(["Máy Bắn Đá", "Lính Canh", "Thủ Vệ Cổng"])
    if floor <= 30:
        return random.choice(["Thủ Vệ Tháp", "Kỵ Binh", "Cung Thủ"])
    if floor <= 60:
        return random.choice(["Hộ Vệ Thông Thiên", "Tướng Giữ Tháp", "Chiến Tướng"])
    return random.choice(["Boss Tháp", "Ma Tướng", "Hộ Pháp"])


def _tower_flavor_text(floor: int) -> str:
    if floor % 10 == 0:
        return "🔥 Đã khiến boss tầng tháp phải nhập viện cấp cứu!"
    return ""


def cmd_leothap(bot, uid, udb, fast=False):
    owner = get_user_display_name(bot, uid)
    mid = udb.get("main_hero_id")
    pfx = getattr(bot, "prefix", PREFIX)
    if not mid or mid not in udb["heroes"]:
        return f"{mention_header(owner)}\n{ICON_ERR} Chưa có tướng chính.\nDùng {display_prefix(pfx)}3q quay rồi {display_prefix(pfx)}3q chon <id>"

    floor = int(udb.get("tower_floor", 1))
    hero = udb["heroes"][mid]
    calc_power(hero)

    enemy_name = _tower_enemy_name(floor)
    enemy_atk = int(60 + floor * 14)

    rounds = 1 if fast else min(max(2, floor), 10)

    avg_hit = int(hero["stats"]["atk"] * 0.95)
    enemy_hp = int(avg_hit * rounds * random.uniform(0.95, 1.10) + floor * 120)

    lines = []
    lines.append(mention_header(owner))
    lines.append(f"🏯 Vượt ải Thông Thiên Tháp Tầng {floor} thành công!")
    flavor = _tower_flavor_text(floor)
    if flavor:
        lines.append(flavor)
    lines.append("")

    def line_attack(attacker, defender, dmg, hp_left):
        return f"🔹{attacker} ⚔️ {dmg} dmg ➜ {defender}: {hp_left:,}❤️"

    def line_dodge(attacker, defender, defender_hp_left):
        return f"🔹{attacker} ⚔️ {defender} 🌀 né! {defender}: {defender_hp_left:,}❤️"

    e_hp = enemy_hp
    h_hp = int(hero["stats"]["hp"])

    for r in range(1, rounds + 1):
        lines.append(f"━━━━━🎯Hiệp {r}━━━━━")

        if random.random() < 0.12 and floor >= 3 and not fast:
            lines.append(line_dodge(hero["name"], enemy_name, e_hp))
        else:
            h_dmg = max(1, int(hero["stats"]["atk"] * random.uniform(0.85, 1.10)))
            e_hp -= h_dmg
            lines.append(line_attack(hero["name"], enemy_name, max(1, h_dmg), max(0, e_hp)))

        if not fast:
            if random.random() < 0.10 and floor >= 3:
                lines.append(line_dodge(enemy_name, hero["name"], h_hp))
            else:
                e_dmg = max(1, int(enemy_atk * random.uniform(0.75, 1.15)))
                h_hp -= e_dmg
                lines.append(line_attack(enemy_name, hero["name"], e_dmg, max(0, h_hp)))

        if h_hp <= 0:
            break

    lines.append("")
    lines.append(f"✨ {hero['name']} đã hạ gục {enemy_name}! Dậy đi 🌞")
    lines.append("")
    lines.append(f"🏆 Kết quả: {get_user_display_name(bot, uid)} Thắng!")

    exp_gain = 20000 + floor * 450
    gold_gain = 10000 + floor * 350
    ticket_gain = 3

    hero["exp"] += exp_gain
    udb["inventory"]["gold"] = udb["inventory"].get("gold", 0) + gold_gain
    udb["inventory"]["vequay"] = udb["inventory"].get("vequay", 0) + ticket_gain
    udb["tower_floor"] = floor + 1

    lines.append(f"🎁 Phần thưởng:🧪 EXP: +{exp_gain:,}, 💰 Gold: +{gold_to_van(gold_gain)}, 🎟️ Vé quay: +{ticket_gain}")

    logs = load_json(DB_LOG_TOWER, {})
    logs.setdefault(str(uid), [])
    logs[str(uid)].append({"time": int(time.time()), "floor": floor, "win": True})
    logs[str(uid)] = logs[str(uid)][-200:]
    save_json(DB_LOG_TOWER, logs)

    msg_tower = "\n".join(lines)

    # ✅ XÓA THÔNG BÁO THĂNG CẤP (không tạo level_msg nữa)
    level_msg = None

    return msg_tower, level_msg


def cmd_soithap(bot, uid):
    owner = get_user_display_name(bot, uid)
    logs = load_json(DB_LOG_TOWER, {})
    items = logs.get(str(uid), [])
    if not items:
        return f"{mention_header(owner)}\n📭 Chưa có lịch sử leo tháp."
    last = items[-10:]
    lines = [mention_header(owner), "🔎 Lịch sử leo Thông Thiên Tháp (10 gần nhất):"]
    for it in reversed(last):
        t = datetime.fromtimestamp(it["time"], tz=timezone(timedelta(hours=7))).strftime("%d/%m %H:%M")
        lines.append(f"➜ [{t}] Tầng {it['floor']} - {ICON_OK if it.get('win') else ICON_ERR}")
    return "\n".join(lines)


def cmd_diemdanh(bot, uid, udb):
    owner = get_user_display_name(bot, uid)
    now = int(time.time())
    last = int(udb.get("last_checkin", 0))
    if now - last < 24 * 3600:
        remain = 24 * 3600 - (now - last)
        hh = remain // 3600
        mm = (remain % 3600) // 60
        return f"{mention_header(owner)}\n⏳ Bạn đã điểm danh rồi! Quay lại sau {hh}h{mm}m."
    udb["last_checkin"] = now
    gold = random.randint(5000, 20000)
    udb["inventory"]["gold"] = udb["inventory"].get("gold", 0) + gold
    extra = ""
    if random.random() < 0.6:
        udb["inventory"]["vequay"] = udb["inventory"].get("vequay", 0) + 1
        extra = " + 🎟️ Vé quay x1"
    return f"{mention_header(owner)}\n📅 Điểm danh thành công!\n🎁 Nhận: 💰 Gold +{gold:,}{extra}"


def cmd_shop(bot, uid, pfx):
    owner = get_user_display_name(bot, uid)
    lines = [mention_header(owner), "🛍️ Cửa hàng 3Q:"]
    for k, v in SHOP_ITEMS.items():
        it = ITEM_LIBRARY.get(k, {"name": k})
        price = []
        if v.get("price_gold", 0) > 0:
            price.append(f"💰{v['price_gold']:,}")
        if v.get("price_gem", 0) > 0:
            price.append(f"💎{v['price_gem']}")
        lines.append(f"➜ {k}: {it['name']} | Giá: {' + '.join(price)} | Gói: x{v.get('bundle',1)}")
    lines.append(f"👉 Mua: {display_prefix(pfx)}3q mua <item> <sl>")
    return "\n".join(lines)


def cmd_mua(bot, uid, udb, item_key, qty):
    owner = get_user_display_name(bot, uid)
    try:
        qty = max(1, int(qty))
    except:
        qty = 1
    if item_key not in SHOP_ITEMS:
        return f"{mention_header(owner)}\n{ICON_ERR} Shop không có `{item_key}`."
    shop = SHOP_ITEMS[item_key]
    inv = udb["inventory"]
    need_gold = shop.get("price_gold", 0) * qty
    need_gem = shop.get("price_gem", 0) * qty
    if inv.get("gold", 0) < need_gold:
        return f"{mention_header(owner)}\n{ICON_ERR} Không đủ 💰 Gold. Cần {need_gold:,}, bạn có {inv.get('gold',0):,}"
    if inv.get("gem", 0) < need_gem:
        return f"{mention_header(owner)}\n{ICON_ERR} Không đủ 💎 Linh thạch. Cần {need_gem}, bạn có {inv.get('gem',0)}"
    inv["gold"] -= need_gold
    inv["gem"] -= need_gem
    inv[item_key] = inv.get(item_key, 0) + shop.get("bundle", 1) * qty
    itname = ITEM_LIBRARY.get(item_key, {"name": item_key})["name"]
    return f"{mention_header(owner)}\n🛒 Mua thành công: {itname} x{shop.get('bundle',1)*qty}\n💰 -{need_gold:,} | 💎 -{need_gem}"


def cmd_reset(bot, uid, users_db):
    owner = get_user_display_name(bot, uid)
    users_db[str(uid)] = {
        "main_hero_id": None,
        "heroes": {},
        "inventory": {
            "vequay": 999,
            "huyentrai": 50,
            "linhdao": 20,
            "linhnguyen": 20000,
            "baoruong": 0,
            "gold": 70000,
            "gem": 10,
            "vip": 0,
            "shards": {}
        },
        "tower_floor": 1,
        "power": 0,
        "last_checkin": 0,
        "pvp_dead_until": 0
    }
    return f"{mention_header(owner)}\n🔄 Đã reset toàn bộ dữ liệu Game 3Q!"


def cmd_nap(bot, author_id, users_db, amount, target_uid=None):
    owner_name = get_user_display_name(bot, author_id)
    if not is_admin_user(author_id):
        return f"{mention_header(owner_name)}\n{ICON_ERR} Bạn không có quyền dùng lệnh này."
    try:
        amount = int(amount)
    except:
        return f"{mention_header(owner_name)}\n{ICON_ERR} Số nạp không hợp lệ. Ví dụ: {display_prefix(getattr(bot,'prefix',PREFIX))}3q nap 20 @tag"
    if amount <= 0:
        return f"{mention_header(owner_name)}\n{ICON_ERR} Số nạp phải > 0."
    tuid = str(target_uid or author_id)
    udb = ensure_user(users_db, tuid)
    udb["inventory"]["gem"] = int(udb["inventory"].get("gem", 0)) + amount
    target_name = get_user_display_name(bot, tuid)
    return f"{mention_header(owner_name)}\n{ICON_OK} Đã nạp x{amount} 💎 Linh thạch cho {mention_header(target_name)}"


# ===== BXH giữ nguyên code của bạn (không thay đổi) =====
def rounded_rect(draw, xy, r, fill):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle([x1, y1, x2, y2], radius=r, fill=fill)


def circle_crop(im, size):
    im = im.resize((size, size), Image.Resampling.LANCZOS).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(im, (0, 0), mask)
    return out


def _load_fonts_bxh():
    try:
        f_title = ImageFont.truetype(FONT_ARIAL_PATH, 54)
        f_name = ImageFont.truetype(FONT_ARIAL_PATH, 42)
        f_val = ImageFont.truetype(FONT_ARIAL_PATH, 36)
        f_rank = ImageFont.truetype(FONT_ARIAL_PATH, 40)
        f_emoji = ImageFont.truetype(FONT_EMOJI_PATH, 42)
    except:
        f_title = f_name = f_val = f_rank = ImageFont.load_default()
        f_emoji = ImageFont.load_default()
    return f_title, f_name, f_val, f_rank, f_emoji


def generate_bxh_thap_image(bot, users_db, topn=5):
    try:
        items = [(str(uid), int(u.get("tower_floor", 1))) for uid, u in users_db.items()]
        items.sort(key=lambda x: x[1], reverse=True)
        items = items[:topn]

        w, h = 1080, 1500
        bg = Image.new("RGBA", (w, h), (250, 244, 255, 255))
        d = ImageDraw.Draw(bg)
        f_title, f_name, f_val, f_rank, f_emoji = _load_fonts_bxh()

        draw_mixed(d, w // 2, 55, "BXH THÔNG THIÊN THÁP 🏯", f_title, f_emoji, (45, 140, 90, 255),
                   shadow=(0, 0, 0, 90), anchor_center=True)

        y = 140
        row_h = 130
        left_pad = 65

        for idx, (uid, floor) in enumerate(items, start=1):
            x1 = left_pad
            x2 = w - left_pad
            y1 = y + (idx - 1) * (row_h + 28)
            y2 = y1 + row_h

            rounded_rect(d, (x1, y1, x2, y2), 34, (35, 35, 45, 220))
            rounded_rect(d, (x1 + 8, y1 + 8, x2 - 8, y2 - 8), 30, (180, 110, 210, 255))

            rank_color = (235, 195, 80, 255) if idx == 1 else (190, 190, 210, 255) if idx == 2 else (215, 150, 115, 255) if idx == 3 else (120, 200, 240, 255)
            d.ellipse((x1 - 24, y1 + 30, x1 + 44, y1 + 98), fill=rank_color)
            d.text((x1 + 10, y1 + row_h / 2), str(idx), font=f_rank, fill=(255, 255, 255, 255), anchor="mm")

            av_size = 88
            av_x = x1 + 80
            av_y = y1 + (row_h - av_size) // 2
            av_path = download_avatar_for_uid(bot, uid)
            if av_path and os.path.exists(av_path):
                try:
                    av = Image.open(av_path)
                    av = circle_crop(av, av_size)
                    bg.paste(av, (av_x, av_y), av)
                except:
                    d.ellipse((av_x, av_y, av_x + av_size, av_y + av_size), fill=(60, 60, 60, 255))
            else:
                d.ellipse((av_x, av_y, av_x + av_size, av_y + av_size), fill=(60, 60, 60, 255))

            name = get_user_display_name(bot, uid)
            d.text((av_x + av_size + 20, y1 + 46), name, font=f_name, fill=(255, 255, 255, 255), anchor="lm")

            val = f"🏯 Tầng: {floor}"
            draw_mixed(d, x2 - 210, y1 + 40, val, f_val, f_emoji, (255, 255, 255, 255),
                       shadow=(0, 0, 0, 110), anchor_center=True)

        bg.save(OUTPUT_BXH_THAP_PATH, "PNG", quality=95)
        return OUTPUT_BXH_THAP_PATH
    except:
        return None


def generate_bxh_power_image(bot, users_db, topn=5):
    try:
        items = []
        for uid, u in users_db.items():
            uid = str(uid)
            pw = int(u.get("power", 0))
            df = 0
            mid = u.get("main_hero_id")
            if mid and mid in u.get("heroes", {}):
                hero = u["heroes"][mid]
                try:
                    df = int(hero["stats"].get("def", 0))
                except:
                    df = 0
            items.append((uid, pw, df))

        items.sort(key=lambda x: x[1], reverse=True)
        items = items[:topn]

        w, h = 1080, 1500
        bg = Image.new("RGBA", (w, h), (245, 250, 255, 255))
        d = ImageDraw.Draw(bg)
        f_title, f_name, f_val, f_rank, f_emoji = _load_fonts_bxh()

        draw_mixed(d, w // 2, 55, "BXH LỰC CHIẾN 💪", f_title, f_emoji, (35, 120, 220, 255),
                   shadow=(0, 0, 0, 90), anchor_center=True)

        y = 140
        row_h = 130
        left_pad = 65

        for idx, (uid, pw, df) in enumerate(items, start=1):
            x1 = left_pad
            x2 = w - left_pad
            y1 = y + (idx - 1) * (row_h + 28)
            y2 = y1 + row_h

            rounded_rect(d, (x1, y1, x2, y2), 34, (35, 35, 45, 220))
            rounded_rect(d, (x1 + 8, y1 + 8, x2 - 8, y2 - 8), 30, (70, 145, 235, 255))

            rank_color = (235, 195, 80, 255) if idx == 1 else (190, 190, 210, 255) if idx == 2 else (215, 150, 115, 255) if idx == 3 else (120, 200, 240, 255)
            d.ellipse((x1 - 24, y1 + 30, x1 + 44, y1 + 98), fill=rank_color)
            d.text((x1 + 10, y1 + row_h / 2), str(idx), font=f_rank, fill=(255, 255, 255, 255), anchor="mm")

            av_size = 88
            av_x = x1 + 80
            av_y = y1 + (row_h - av_size) // 2
            av_path = download_avatar_for_uid(bot, uid)
            if av_path and os.path.exists(av_path):
                try:
                    av = Image.open(av_path)
                    av = circle_crop(av, av_size)
                    bg.paste(av, (av_x, av_y), av)
                except:
                    d.ellipse((av_x, av_y, av_x + av_size, av_y + av_size), fill=(60, 60, 60, 255))
            else:
                d.ellipse((av_x, av_y, av_x + av_size, av_y + av_size), fill=(60, 60, 60, 255))

            name = get_user_display_name(bot, uid)
            d.text((av_x + av_size + 20, y1 + 46), name, font=f_name, fill=(255, 255, 255, 255), anchor="lm")

            val1 = f"💪 Lực chiến: {pw:,}"
            val2 = f"🛡️ Thủ: {df}"
            draw_mixed(d, x2 - 250, y1 + 32, val1, f_val, f_emoji, (255, 255, 255, 255),
                       shadow=(0, 0, 0, 120), anchor_center=True)
            draw_mixed(d, x2 - 250, y1 + 78, val2, f_val, f_emoji, (255, 255, 255, 255),
                       shadow=(0, 0, 0, 120), anchor_center=True)

        bg.save(OUTPUT_BXH_POWER_PATH, "PNG", quality=95)
        return OUTPUT_BXH_POWER_PATH
    except:
        return None


def handle_3q_command(message, message_object, thread_id, thread_type, author_id, bot):
    def run():
        try:
            parts = message.strip().split()
            action = parts[1].lower() if len(parts) > 1 else ""

            users_db = load_json(DB_USER, {})
            udb = ensure_user(users_db, author_id)

            owner_name = get_user_display_name(bot, author_id)
            pfx = getattr(bot, "prefix", PREFIX)

            if not action:
                txt = menu_text(owner_name, pfx)
                img = generate_3q_menu_image(bot, author_id)
                if img:
                    m = build_mentions_from_text(txt, [(author_id, owner_name)])
                    bot.sendLocalImage(
                        imagePath=img,
                        message=Message(text=txt, mention=m),
                        thread_id=thread_id,
                        thread_type=thread_type,
                        width=2000,
                        height=680,
                        ttl=240000
                    )
                    try:
                        os.remove(img)
                    except:
                        pass
                else:
                    reply_mention(bot, message_object, thread_id, thread_type, author_id, owner_name, txt)

                save_json(DB_USER, users_db)
                return

            if action == "huongdan":
                txt = HUONG_DAN_TEXT.format(name=owner_name, prefix=display_prefix(pfx))
                reply_mention(bot, message_object, thread_id, thread_type, author_id, owner_name, txt)
                save_json(DB_USER, users_db)
                return

            if action == "quay":
                response = cmd_quay(bot, author_id, udb, pfx)
                save_json(DB_USER, users_db)
                reply_mention(bot, message_object, thread_id, thread_type, author_id, owner_name, response)
                return

            if action == "chon":
                if len(parts) < 3:
                    response = f"{mention_header(owner_name)}\n{ICON_ERR} Thiếu ID. Dùng: {display_prefix(pfx)}3q chon <id>"
                else:
                    response = cmd_chon(bot, author_id, udb, parts[2], pfx)
                save_json(DB_USER, users_db)
                reply_mention(bot, message_object, thread_id, thread_type, author_id, owner_name, response)
                return

            if action == "tuong" or action.startswith("@"):
                target_uid = extract_first_mention_uid(message_object) or str(author_id)
                response = cmd_tuong(bot, users_db, target_uid, pfx)
                save_json(DB_USER, users_db)
                reply_mention(bot, message_object, thread_id, thread_type, author_id, owner_name, response)
                return

            if action == "tuido":
                target_uid = extract_first_mention_uid(message_object) or str(author_id)
                response = cmd_tuido(bot, users_db, target_uid)
                save_json(DB_USER, users_db)
                reply_mention(bot, message_object, thread_id, thread_type, author_id, owner_name, response)
                return

            if action == "soi":
                if len(parts) < 3:
                    response = f"{mention_header(owner_name)}\n{ICON_ERR} Thiếu item. Dùng: {display_prefix(pfx)}3q soi <item>"
                else:
                    response = cmd_soi(bot, author_id, udb, parts[2].lower())
                save_json(DB_USER, users_db)
                reply_mention(bot, message_object, thread_id, thread_type, author_id, owner_name, response)
                return

            if action == "dung":
                if len(parts) < 3:
                    response = f"{mention_header(owner_name)}\n{ICON_ERR} Thiếu item. Dùng: {display_prefix(pfx)}3q dung <item> [hero_id]"
                else:
                    item = parts[2].lower()
                    hid = parts[3] if len(parts) >= 4 else None
                    response = cmd_dung(bot, author_id, udb, item, hero_id=hid)
                save_json(DB_USER, users_db)
                reply_mention(bot, message_object, thread_id, thread_type, author_id, owner_name, response)
                return

            if action == "huy":
                if len(parts) < 4:
                    response = f"{mention_header(owner_name)}\n{ICON_ERR} Thiếu tham số. Dùng: {display_prefix(pfx)}3q huy <item> <sl>"
                else:
                    response = cmd_huy(bot, author_id, udb, parts[2].lower(), parts[3])
                save_json(DB_USER, users_db)
                reply_mention(bot, message_object, thread_id, thread_type, author_id, owner_name, response)
                return

            if action == "leothap":
                msg_tower, level_msg = cmd_leothap(bot, author_id, udb, fast=False)
                save_json(DB_USER, users_db)
                reply_mention(bot, message_object, thread_id, thread_type, author_id, owner_name, msg_tower)
                # ✅ XÓA GỬI THÔNG BÁO THĂNG CẤP
                return

            if action == "leothaps":
                msg_tower, level_msg = cmd_leothap(bot, author_id, udb, fast=True)
                save_json(DB_USER, users_db)
                reply_mention(bot, message_object, thread_id, thread_type, author_id, owner_name, msg_tower)
                # ✅ XÓA GỬI THÔNG BÁO THĂNG CẤP
                return

            if action == "soithap":
                response = cmd_soithap(bot, author_id)
                save_json(DB_USER, users_db)
                reply_mention(bot, message_object, thread_id, thread_type, author_id, owner_name, response)
                return

            if action == "diemdanh":
                response = cmd_diemdanh(bot, author_id, udb)
                save_json(DB_USER, users_db)
                reply_mention(bot, message_object, thread_id, thread_type, author_id, owner_name, response)
                return

            if action == "shop":
                response = cmd_shop(bot, author_id, pfx)
                save_json(DB_USER, users_db)
                reply_mention(bot, message_object, thread_id, thread_type, author_id, owner_name, response)
                return

            if action == "mua":
                if len(parts) < 4:
                    response = f"{mention_header(owner_name)}\n{ICON_ERR} Thiếu tham số. Dùng: {display_prefix(pfx)}3q mua <item> <sl>"
                else:
                    response = cmd_mua(bot, author_id, udb, parts[2].lower(), parts[3])
                save_json(DB_USER, users_db)
                reply_mention(bot, message_object, thread_id, thread_type, author_id, owner_name, response)
                return

            if action == "nap":
                if len(parts) < 3:
                    response = f"{mention_header(owner_name)}\n{ICON_ERR} Thiếu số nạp. Ví dụ: {display_prefix(pfx)}3q nap 20 @tag"
                else:
                    amount = parts[2]
                    target_uid = extract_first_mention_uid(message_object) or str(author_id)
                    response = cmd_nap(bot, author_id, users_db, amount, target_uid=target_uid)
                save_json(DB_USER, users_db)
                reply_mention(bot, message_object, thread_id, thread_type, author_id, owner_name, response)
                return

            if action == "bxhthap":
                save_json(DB_USER, users_db)
                img = generate_bxh_thap_image(bot, users_db, topn=5)
                if img:
                    txt = f"{mention_header(owner_name)}\n🏯 BXH Tháp TOP 5"
                    m = build_mentions_from_text(txt, [(author_id, owner_name)])
                    bot.sendLocalImage(
                        imagePath=img,
                        message=Message(text=txt, mention=m),
                        thread_id=thread_id,
                        thread_type=thread_type,
                        width=1080,
                        height=1500,
                        ttl=240000
                    )
                    try:
                        os.remove(img)
                    except:
                        pass
                else:
                    reply_mention(bot, message_object, thread_id, thread_type, author_id, owner_name,
                                 f"{mention_header(owner_name)}\n{ICON_ERR} Không thể tạo ảnh BXH Tháp.")
                return

            if action == "bxh":
                save_json(DB_USER, users_db)
                img = generate_bxh_power_image(bot, users_db, topn=5)
                if img:
                    txt = f"{mention_header(owner_name)}\n💪 BXH Lực chiến TOP 5"
                    m = build_mentions_from_text(txt, [(author_id, owner_name)])
                    bot.sendLocalImage(
                        imagePath=img,
                        message=Message(text=txt, mention=m),
                        thread_id=thread_id,
                        thread_type=thread_type,
                        width=1080,
                        height=1500,
                        ttl=240000
                    )
                    try:
                        os.remove(img)
                    except:
                        pass
                else:
                    reply_mention(bot, message_object, thread_id, thread_type, author_id, owner_name,
                                 f"{mention_header(owner_name)}\n{ICON_ERR} Không thể tạo ảnh BXH Lực chiến.")
                return

            if action == "rest":
                response = cmd_reset(bot, author_id, users_db)
                save_json(DB_USER, users_db)
                reply_mention(bot, message_object, thread_id, thread_type, author_id, owner_name, response)
                return

            response = f"{mention_header(owner_name)}\n{ICON_ERR} Sai cú pháp! Gõ: {display_prefix(pfx)}3q để xem menu."
            save_json(DB_USER, users_db)
            reply_mention(bot, message_object, thread_id, thread_type, author_id, owner_name, response)

        except:
            try:
                owner_name2 = get_user_display_name(bot, author_id)
                reply_mention(bot, message_object, thread_id, thread_type, author_id, owner_name2,
                             f"{mention_header(owner_name2)}\n{ICON_ERR} Đã xảy ra lỗi gì đó 🤧")
            except:
                bot.replyMessage(Message(text="Lỗi."), message_object, thread_id=thread_id, thread_type=thread_type)

    Thread(target=run).start()


def PTA():
    return {"3q": handle_3q_command}