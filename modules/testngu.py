import os
import time
import random
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from zlapi.models import Message

# ================= INFO =================
des = {
    'version': "1.0.0",
    'credits': "ngbao",
    'description': "Kiểm tra độ thông minh (troll)",
    'power': "Thành viên"
}

FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"

# Các nhận xét dựa trên mức độ %
def get_comment(percent):
    if percent < 10:
        return "Thiên tài lỗi lạc, bộ não của Einstein tái thế!"
    elif percent < 30:
        return "Bình thường, đủ dùng để không bị lừa bán sang biên giới."
    elif percent < 50:
        return "Có dấu hiệu thiếu hụt chất xám, cần bổ sung muối gấp."
    elif percent < 70:
        return "Khá nặng, thường xuyên quên mật khẩu Zalo và ATM."
    elif percent < 90:
        return "Cấp độ báo động! Não đang trong trạng thái chờ cài đặt lại."
    else:
        return "Vô phương cứu chữa! Nên nộp đơn vào hội người mù chữ."

# ================= UTIL =================
def fetch_image(url):
    try:
        if not url: return None
        r = requests.get(url, timeout=10)
        return Image.open(BytesIO(r.content)).convert("RGBA")
    except: return None

def create_stupidity_img(avatar_url, name, uid):
    W, H = 700, 400
    # Nền tối mang phong cách công nghệ y sinh
    img = Image.new("RGB", (W, H), (10, 20, 30))
    draw = ImageDraw.Draw(img)

    try:
        f_title = ImageFont.truetype(FONT_PATH, 35)
        f_percent = ImageFont.truetype(FONT_PATH, 80)
        f_name = ImageFont.truetype(FONT_PATH, 28)
        f_msg = ImageFont.truetype(FONT_PATH, 20)
    except:
        f_title = f_percent = f_name = f_msg = ImageFont.load_default()

    # 1. VẼ HIỆU ỨNG SCAN (RADAR)
    for i in range(1, 4):
        draw.ellipse([W-250-i*10, 50-i*10, W-50+i*10, 250+i*10], outline=(0, 255, 100, 100), width=1)
    
    # 2. AVATAR
    avatar = fetch_image(avatar_url)
    if not avatar:
        avatar = Image.new("RGBA", (180, 180), (100, 100, 100))
    avatar = avatar.resize((180, 180))
    
    # Bo tròn avatar
    mask = Image.new("L", (180, 180), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 180, 180), fill=255)
    img.paste(avatar, (50, 80), mask)
    draw.ellipse((45, 75, 235, 265), outline=(0, 200, 255), width=4)

    # 3. KẾT QUẢ PHÂN TÍCH
    percent = random.randint(0, 100)
    color = (0, 255, 100) # Xanh lá (An toàn)
    if percent > 50: color = (255, 200, 0) # Vàng (Cảnh báo)
    if percent > 80: color = (255, 50, 50) # Đỏ (Nguy hiểm)

    draw.text((300, 40), "MÁY QUÉT ĐỘ NGU", fill=(0, 255, 255), font=f_title)
    draw.text((320, 100), f"{percent}%", fill=color, font=f_percent)
    
    # Tên người dùng
    draw.text((50, 280), name.upper(), fill=(255, 255, 255), font=f_name)
    
    # Nhận xét (Tự động xuống dòng)
    comment = get_comment(percent)
    import textwrap
    lines = textwrap.wrap(f"Nhận xét: {comment}", width=35)
    y_text = 320
    for line in lines:
        draw.text((50, y_text), line, fill=(200, 200, 200), font=f_msg)
        y_text += 25

    # Trang trí thêm vài dòng code ảo ma
    draw.text((W-150, H-30), "STATUS: ANALYZED", fill=(0, 150, 150), font=ImageFont.load_default())

    return img, percent

# ================= COMMAND =================
def handle_testngu(message, message_object, thread_id, thread_type, author_id, client):
    target_id = author_id
    if message_object.mentions:
        target_id = message_object.mentions[0]['uid']
    elif message_object.quote:
        target_id = message_object.quote.ownerId

    user_info = client.fetchUserInfo(target_id)
    if hasattr(user_info, 'changed_profiles') and str(target_id) in user_info.changed_profiles:
        p = user_info.changed_profiles[str(target_id)]
        name = p.get('zaloName', 'Người dùng')
        avatar = p.get('avatar', '')
    else:
        name = getattr(user_info, 'name', 'Người dùng')
        avatar = getattr(user_info, 'avatar', '')

    img, pcent = create_stupidity_img(avatar, name, target_id)
    path = f"modules/cache/testngu_{int(time.time())}.png"
    if not os.path.exists("modules/cache"): os.makedirs("modules/cache")
    img.save(path)

    msg = f"🔍 Đang tiến hành quét não bộ của {name}...\n📊 Kết quả: {pcent}% độ ngu!"
    client.sendLocalImage(path, thread_id=thread_id, thread_type=thread_type, message=Message(text=msg))
    os.remove(path)

# ================= EXPORT =================
def PTA():
    return {
        'testngu': handle_testngu,
        'stupid': handle_testngu,
        'docao': handle_testngu
    }