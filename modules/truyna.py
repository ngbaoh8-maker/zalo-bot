import os
import time
import random
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from zlapi.models import Message

# ================= INFO =================
des = {
    'version': "1.2.0",
    'credits': "ngbao",
    'description': "Lệnh truy nã One Piece (troll)",
    'power': "Thành viên"
}

FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"

CRIMES = [
    "AFK giữa trận",
    "Feed không lý do",
    "Out meta vẫn cố",
    "Seen không rep",
    "Nợ kèo nhưng off",
    "Ping lag đổ tại game",
    "Trộm trái ác quỷ của thuyền trưởng",
    "Tội quá đẹp trai làm loạn nhóm"
]

# ================= UTIL =================
def fetch_image(url):
    try:
        if not url: return None
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return Image.open(BytesIO(r.content)).convert("RGB")
    except:
        return None

def paper_bg(W, H):
    # Tạo nền giấy cổ điển màu vàng úa
    img = Image.new("RGB", (W, H), (230, 214, 170))
    draw = ImageDraw.Draw(img)
    # Thêm hiệu ứng nhiễu (noise) để tạo cảm giác giấy cũ
    for _ in range(3500):
        x = random.randint(0, W-1)
        y = random.randint(0, H-1)
        c = random.randint(180, 220)
        draw.point((x, y), fill=(c, c-10, c-30))
    img = ImageEnhance.Contrast(img).enhance(1.1)
    img = img.filter(ImageFilter.GaussianBlur(0.4))
    return img

# ================= CREATE IMAGE =================
def create_wanted_op(avatar_url, name, uid, crime):
    W, H = 900, 1200
    img = paper_bg(W, H)
    draw = ImageDraw.Draw(img)

    try:
        f_title = ImageFont.truetype(FONT_PATH, 110)
        f_big   = ImageFont.truetype(FONT_PATH, 55)
        f_mid   = ImageFont.truetype(FONT_PATH, 42)
        f_small = ImageFont.truetype(FONT_PATH, 34)
    except:
        f_title = f_big = f_mid = f_small = ImageFont.load_default()

    # 1. TIÊU ĐỀ WANTED
    title = "Truy nã"
    tw = draw.textlength(title, font=f_title)
    draw.text(((W-tw)//2, 50), title, fill=(70, 35, 10), font=f_title)

    sub = "Sống hoặc Chết"
    sw = draw.textlength(sub, font=f_mid)
    draw.text(((W-sw)//2, 160), sub, fill=(80, 45, 15), font=f_mid)

    # 2. XỬ LÝ AVATAR (Làm hiệu ứng ảnh cũ)
    avatar = fetch_image(avatar_url)
    if not avatar:
        avatar = Image.new("RGB", (550, 550), (150,150,150))
    
    avatar = avatar.resize((550, 550))
    # Chỉnh màu ảnh hơi ngả vàng/tối cho giống lệnh truy nã
    avatar = ImageEnhance.Color(avatar).enhance(0.6) 
    avatar = ImageEnhance.Contrast(avatar).enhance(1.2)
    img.paste(avatar, ((W-550)//2, 230))

    # Viền ảnh
    draw.rectangle(((W-550)//2-8, 222, (W+550)//2+8, 230+550+8), outline=(80,40,15), width=6)

    # 3. TÊN VÀ TỘI DANH
    name = name.upper()
    nw = draw.textlength(name, font=f_big)
    draw.text(((W-nw)//2, 820), name, fill=(50,25,10), font=f_big)

    crime_text = f"Tội danh: {crime}"
    cw = draw.textlength(crime_text, font=f_small)
    draw.text(((W-cw)//2, 890), crime_text, fill=(70,40,20), font=f_small)

    # 4. TIỀN THƯỞNG (BOUNTY)
    bounty = f"{random.randint(100, 999)},000,000 -"
    bw = draw.textlength(bounty, font=f_big)
    draw.text(((W-bw)//2, 980), bounty, fill=(120,30,20), font=f_big)

    # 5. CHI TIẾT PHỤ
    draw.text((100, 1080), f"UID: {uid[:8]}", fill=(90,60,40), font=f_small)
    draw.text((W-300, 1080), "MARINE HQ", fill=(90,60,40), font=f_small)

    # Viền khung ngoài cùng
    draw.rectangle((20,20,W-20,H-20), outline=(90,50,20), width=10)

    return img

# ================= COMMAND =================
def handle_truyna(message, message_object, thread_id, thread_type, author_id, client):
    text = message_object.text or ""
    parts = text.split()

    target_id = author_id
    if message_object.mentions:
        target_id = message_object.mentions[0]['uid']
    elif message_object.quote:
        target_id = message_object.quote.ownerId

    user_info = client.fetchUserInfo(target_id)
    if hasattr(user_info, 'changed_profiles') and str(target_id) in user_info.changed_profiles:
        p = user_info.changed_profiles[str(target_id)]
        name = p.get('zaloName', 'UNKNOWN')
        avatar = p.get('avatar', '')
    else:
        name = getattr(user_info, 'name', 'UNKNOWN')
        avatar = getattr(user_info, 'avatar', '')

    crime = " ".join(parts[1:]) if len(parts) > 1 else random.choice(CRIMES)

    img = create_wanted_op(avatar, name, target_id, crime)

    if not os.path.exists("modules/cache"):
        os.makedirs("modules/cache")

    path = f"modules/cache/wanted_{int(time.time())}.jpg"
    img.save(path, quality=90)

    msg = Message(text=f"🏴‍☠️ LỆNH TRUY NÃ 🏴‍☠️\nĐã xác định đối tượng nguy hiểm: {name}!\nCẩn thận, hắn đang bị truy nã bởi Hải Quân!")
    client.sendLocalImage(path, thread_id=thread_id, thread_type=thread_type, message=msg)

    os.remove(path)

# ================= EXPORT =================
def PTA():
    return {
        'truyna': handle_truyna,
        'wanted': handle_truyna
    }