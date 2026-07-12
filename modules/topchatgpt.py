import os
import json
import tempfile
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from zlapi.models import Message
import requests
from io import BytesIO
import threading
import time

file_lock = threading.Lock()

des = {
    "version": "7.5.0",
    "credits": "ngbao",
    "description": "Top nhắn tin style banbe/key 2 cột",
    "power": "Admin"
}

CACHE_DIR = "modules/cache/topchat_temp"
FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
os.makedirs(CACHE_DIR, exist_ok=True)

DATA_FILE = os.path.join(os.getcwd(), "rank-info.json")


# ==========================
# FONT
# ==========================
def get_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except:
        return ImageFont.load_default()


# ==========================
# RANK FILE
# ==========================
def read_rank_info():
    with file_lock:
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
                        if "groups" not in data:
                            data["groups"] = {}
                        return data
            except:
                pass
    return {"groups": {}}


def save_rank_info(data):
    try:
        with file_lock:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
    except:
        pass


# ==========================
# GET USER NAME
# ==========================
def get_user_name(client, user_id, cache_data=None):
    try:
        info = client.fetchUserInfo(user_id)
        if info and hasattr(info, 'changed_profiles') and user_id in info.changed_profiles:
            p = info.changed_profiles[user_id]
            name = p.get("zaloName") or p.get("name") or p.get("displayName")
            if name:
                return name
    except:
        pass

    if cache_data:
        for u in cache_data:
            if u.get("UserID") == user_id:
                return u.get("UserName", "Ẩn danh")

    return "Ẩn danh"


# ==========================
# UPDATE RANK
# ==========================
def update_rank(client, thread_id, author_id):
    data = read_rank_info()
    group = data["groups"].setdefault(str(thread_id), {"users": []})
    users = group["users"]

    username = get_user_name(client, author_id, users)
    found = False

    for u in users:
        if u["UserID"] == author_id:
            u["Rank"] += 1
            u["UserName"] = username
            u["LastActive"] = datetime.now().isoformat()
            found = True
            break

    if not found:
        users.append({
            "UserID": author_id,
            "UserName": username,
            "Rank": 1,
            "LastActive": datetime.now().isoformat()
        })

    save_rank_info(data)


update_user_rank = update_rank  # alias


def reset_rank(thread_id=None):
    data = read_rank_info()
    if thread_id is None:
        for g in data["groups"]:
            data["groups"][g]["users"] = []
    else:
        if str(thread_id) in data["groups"]:
            data["groups"][str(thread_id)]["users"] = []
    save_rank_info(data)


# ==========================
# LOAD BG STYLE BANBE
# ==========================
def load_bg(size):
    urls = [
        "https://files.catbox.moe/y5fg9j.jpg",
        "https://files.catbox.moe/t31gfd.jpg",
        "https://files.catbox.moe/77c4by.jpg",
        "https://files.catbox.moe/d7p28q.jpg"
    ]
    import random
    try:
        r = requests.get(random.choice(urls), timeout=5)
        img = Image.open(BytesIO(r.content)).convert("RGBA")
        return img.resize(size, Image.LANCZOS)
    except:
        return Image.new("RGBA", size, (25, 30, 45, 255))


# ==========================
# AVATAR ROUND
# ==========================
def fetch_avatar_round(url, size=170):
    try:
        r = requests.get(url, timeout=4)
        img = Image.open(BytesIO(r.content)).convert("RGBA")
    except:
        img = Image.new("RGBA", (size, size), (140,140,140))

    img = img.resize((size,size), Image.LANCZOS)

    mask = Image.new("L", (size,size), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse((0,0,size,size), fill=255)
    img.putalpha(mask)
    return img


# ==========================
# WRAP TEXT
# ==========================
def wrap_text(text, font, max_w):
    words = text.split(" ")
    lines, line = [], ""
    for w in words:
        test = line + w + " "
        if font.getlength(test) <= max_w:
            line = test
        else:
            lines.append(line)
            line = w + " "
    lines.append(line)
    return [l.strip() for l in lines]


# ==========================
# DRAW TOPCHAT (STYLE BANBE)
# ==========================
def draw_topchat_image(client, thread_id, page=1):
    data = read_rank_info()
    group = data["groups"].get(str(thread_id), {"users": []})
    users = group.get("users", [])

    if not users:
        return None, None, None

    users = sorted(users, key=lambda u: u["Rank"], reverse=True)[:10]  # top 10

    W, H = 2000, 2600
    bg = load_bg((W, H))
    draw = ImageDraw.Draw(bg)

    # TITLE
    title_font = ImageFont.truetype(FONT_PATH, 90)
    group_font = ImageFont.truetype(FONT_PATH, 60)

    try:
        g = client.fetchGroupInfo(thread_id).gridInfoMap.get(thread_id)
        group_name = getattr(g, "name", "TOP CHAT")
    except:
        group_name = "TOP CHAT"

    draw.text((W//2 - title_font.getlength("TOP CHAT")//2, 70),
              "TOP CHAT", font=title_font, fill=(0,255,255))

    draw.text((W//2 - group_font.getlength(group_name)//2, 170),
              group_name, font=group_font, fill=(200,220,255))

    # CARD SIZE
    CARD_W = 880
    CARD_H = 380

    x1 = 150
    x2 = 150 + CARD_W + 100
    yL = 300
    yR = 300

    rank_colors = {
        1: "#FFD700",
        2: "#C0C0C0",
        3: "#CD7F32"
    }

    for index, user in enumerate(users, start=1):
        uid  = user["UserID"]
        name = user["UserName"]
        count = user["Rank"]

        # avatar
        try:
            info = client.fetchUserInfo(uid)
            p = info.changed_profiles.get(uid, {})
            avatar_url = p.get("avatar", None)
        except:
            avatar_url = None

        if index % 2 != 0:
            x = x1
            y = yL
        else:
            x = x2
            y = yR

        # neon border
        neon = [
            (255,0,0,130),(255,127,0,130),(255,255,0,130),
            (0,255,0,130),(0,255,255,130),(0,127,255,130),
            (139,0,255,130)
        ]
        radius = 45
        for g2, col in enumerate(neon, 1):
            draw.rounded_rectangle(
                (x-g2, y-g2, x+CARD_W+g2, y+CARD_H+g2),
                radius=radius+g2,
                outline=col, width=2
            )

        # glass
        glass_h = 180
        gy = y + CARD_H - glass_h

        area = bg.crop((x, gy, x+CARD_W, gy+glass_h)).filter(ImageFilter.GaussianBlur(8))
        overlay = Image.new("RGBA", (CARD_W, glass_h), (22,28,45,120))
        glass = Image.alpha_composite(area, overlay)

        mask = Image.new("L", (CARD_W, glass_h), 0)
        dm = ImageDraw.Draw(mask)
        dm.rounded_rectangle((0,0,CARD_W,glass_h), radius=radius, fill=255)

        bg.paste(glass, (x, gy), mask)

        # avatar
        av = fetch_avatar_round(avatar_url, 170)
        bg.alpha_composite(av, (x + CARD_W//2 - 85, y + 20))

        # TEXT
        fn_name = ImageFont.truetype(FONT_PATH, 48)
        fn_uid  = ImageFont.truetype(FONT_PATH, 32)
        fn_cnt  = ImageFont.truetype(FONT_PATH, 36)

        name_lines = wrap_text(name, fn_name, CARD_W - 120)

        ty = gy + 20
        for line in name_lines:
            draw.text((x + CARD_W//2 - fn_name.getlength(line)//2, ty),
                      line, font=fn_name, fill="white")
            ty += 55

        uid_txt = f"UID: {uid}"
        draw.text((x + CARD_W//2 - fn_uid.getlength(uid_txt)//2, ty),
                  uid_txt, font=fn_uid, fill="#C8E2FF")
        ty += 55

        color = rank_colors.get(index, "#EAF6FF")
        cnt_txt = f"Tin nhắn: {count:,}"
        draw.text((x + CARD_W//2 - fn_cnt.getlength(cnt_txt)//2, ty),
                  cnt_txt, font=fn_cnt, fill=color)

        # update Y
        if index % 2 != 0:
            yL += CARD_H + 55
        else:
            yR += CARD_H + 55

    out = os.path.join(CACHE_DIR, f"topchat_{time.time()}.jpg")
    bg.convert("RGB").save(out, quality=97)
    return out, W, H


# ==========================
# COMMAND
# ==========================
def handle_topchat_command(message, msg_obj, thread_id, thread_type, author_id, client):
    try:
        parts = message.strip().split()

        if len(parts) > 1 and parts[1] == "reset":
            from config import ADMIN
            if author_id not in ADMIN:
                client.sendMessage(Message(text="❌ Bạn không có quyền reset rank."), thread_id, thread_type)
                return
            reset_rank(thread_id)
            client.sendMessage(Message(text="✅ Đã reset dữ liệu topchat."), thread_id, thread_type)
            return

        update_rank(client, thread_id, author_id)

        img, w, h = draw_topchat_image(client, thread_id)
        if not img:
            client.sendMessage(Message(text="📭 Chưa có dữ liệu topchat."), thread_id, thread_type)
            return

        client.sendLocalImage(img, thread_id, thread_type, width=w, height=h)
        os.remove(img)

    except Exception as e:
        client.sendMessage(Message(text=f"❌ Lỗi topchat: {e}"), thread_id, thread_type)


def PTA():
    return {"topchatgpt": handle_topchat_command}
