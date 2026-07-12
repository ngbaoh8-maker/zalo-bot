import os
import time
import random
import requests
import datetime
import textwrap
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from zlapi.models import Message

# ================= INFO =================
des = {
    'version': "1.1.0",
    'credits': "ngbao",
    'description': "Chế ảnh bản tin thời sự",
    'power': "Thành Viên"
}

FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"

NEWS_TITLES = ["BẢN TIN NÓNG", "BREAKING NEWS", "CHUYỂN ĐỘNG 24H", "GÓC CẢNH GIÁC", "TIN ĐỘC QUYỀN"]
NEWS_CONTENT = [
    "Đối tượng này vừa bị phát hiện vì quá đẹp trai.",
    "Nghi vấn thanh niên này là tỷ phú ngầm trong nhóm.",
    "Cảnh báo: Đối tượng thường xuyên seen không rep.",
    "Phát hiện người dùng có dấu hiệu vả thính quá liều.",
    "Thanh niên ưu tú của năm vừa lộ diện."
]

# ================= UTIL =================
def fetch_image(url):
    try:
        if not url: return None
        r = requests.get(url, timeout=10)
        return Image.open(BytesIO(r.content)).convert("RGBA")
    except: return None

def create_news_img(avatar_url, name, content):
    W, H = 800, 450 
    img = Image.new("RGB", (W, H), (0, 0, 0))
    
    avatar = fetch_image(avatar_url)
    if not avatar:
        avatar = Image.new("RGBA", (W, H), (50, 50, 50))
    
    # Resize & Crop avatar làm nền
    img_aspect = W / H
    av_w, av_h = avatar.size
    av_aspect = av_w / av_h
    if av_aspect > img_aspect:
        new_w = int(av_aspect * H)
        avatar = avatar.resize((new_w, H))
        img.paste(avatar, ((W - new_w) // 2, 0))
    else:
        new_h = int(W / av_aspect)
        avatar = avatar.resize((W, new_h))
        img.paste(avatar, (0, (H - new_h) // 2))

    draw = ImageDraw.Draw(img)
    
    try:
        f_main = ImageFont.truetype(FONT_PATH, 32) # Giảm nhẹ cỡ chữ chính
        f_sub = ImageFont.truetype(FONT_PATH, 20)
        f_live = ImageFont.truetype(FONT_PATH, 18)
    except:
        f_main = f_sub = f_live = ImageFont.load_default()

    # 1. LIVE & CLOCK
    draw.rectangle([30, 30, 100, 60], fill=(200, 0, 0))
    draw.text((43, 34), "LIVE", fill=(255, 255, 255), font=f_live)
    now = datetime.datetime.now().strftime("%H:%M")
    draw.text((W-110, 25), now, fill=(255, 255, 255), font=ImageFont.truetype(FONT_PATH, 40) if FONT_PATH else f_main)

    # 2. BOX TIN TỨC
    draw.rectangle([0, H-120, W, H-35], fill=(0, 50, 150)) # Thanh xanh chính
    draw.rectangle([0, H-35, W, H], fill=(180, 0, 0))    # Thanh đỏ dưới cùng

    # Tên chương trình (Tag vàng)
    title = random.choice(NEWS_TITLES)
    draw.rectangle([0, H-155, 250, H-120], fill=(255, 200, 0))
    draw.text((20, H-150), title, fill=(0, 0, 0), font=f_sub)

    # 3. XỬ LÝ CHỮ TRÀN (Text Wrapping)
    full_text = f"{name.upper()}: {content}"
    # Tự động xuống dòng sau khoảng 45 ký tự
    lines = textwrap.wrap(full_text, width=45) 
    
    y_text = H - 110
    for line in lines[:2]: # Chỉ lấy tối đa 2 dòng để không đè lên thanh đỏ
        draw.text((30, y_text), line, fill=(255, 255, 255), font=f_main)
        y_text += 38

    # Dòng chữ chạy nhỏ dưới cùng
    running_msg = "TIN MỚI: Hệ thống đang giám sát đối tượng... Chúc bạn một ngày tốt lành!"
    draw.text((20, H-30), running_msg, fill=(255, 255, 255), font=f_sub)

    # Logo News
    draw.ellipse((W-80, H-180, W-30, H-130), outline=(255, 255, 255), width=2)
    draw.text((W-73, H-163), "NEWS", fill=(255, 255, 255), font=f_live)

    return img

# ================= COMMAND =================
def handle_thoisu(message, message_object, thread_id, thread_type, author_id, client):
    target_id = author_id
    if message_object.mentions:
        target_id = message_object.mentions[0]['uid']
    elif message_object.quote:
        target_id = message_object.quote.ownerId

    user_info = client.fetchUserInfo(target_id)
    if hasattr(user_info, 'changed_profiles') and str(target_id) in user_info.changed_profiles:
        p = user_info.changed_profiles[str(target_id)]
        name = p.get('zaloName', 'Cư dân mạng')
    else:
        name = getattr(user_info, 'name', 'Cư dân mạng')
    
    avatar = getattr(user_info, 'avatar', '') if not hasattr(user_info, 'changed_profiles') else user_info.changed_profiles[str(target_id)].get('avatar', '')

    text = message_object.text or ""
    parts = text.split()
    if len(parts) > 1 and not message_object.mentions:
        content = " ".join(parts[1:])
    else:
        content = random.choice(NEWS_CONTENT)

    img = create_news_img(avatar, name, content)
    path = f"modules/cache/news_fix_{int(time.time())}.png"
    if not os.path.exists("modules/cache"): os.makedirs("modules/cache")
    img.save(path)

    client.sendLocalImage(path, thread_id=thread_id, thread_type=thread_type, message=Message(text=f"📺 Bản tin thời sự vừa cập nhật về {name}!"))
    os.remove(path)

def PTA():
    return {'thoisu': handle_thoisu, 'news': handle_thoisu}