import os
import time
import random
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from zlapi.models import Message

# ================= INFO =================
des = {
    'version': "1.1.0",
    'credits': "ngbao",
    'description': "Mô phỏng kết quả tương lai ngẫu nhiên",
    'power': "Thành viên"
}

FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"

# Dữ liệu mô phỏng vui nhộn
JOBS = ["PHI HÀNH GIA", "GIÁM ĐỐC APPLE", "BÁN CƠM TẤM SAO HỎA", "TOP 1 SERVER", "TỶ PHÚ BITCOIN", "CHỦ TỊCH TẬP ĐOÀN ĐA TRỤ", "TRÙM ĐỒ CỔ", "KỸ SƯ ROBOT"]
CAREERS = ["Nông dân vũ trụ", "Kỹ sư hệ thống Dyson", "Người du hành thời gian", "Lập trình viên AI", "Kinh doanh bất động sản Mặt Trăng", "Chăm sóc thú cưng ngoài hành tinh"]
ASSETS = ["Tàu SpaceX", "1000 BTC", "Trạm vũ trụ riêng", "Cỗ máy thời gian v1.0", "Thẻ xanh Thiên hà", "Mảnh đất trên Sao Kim"]
QUOTES = [
    "Người Việt đầu tiên đặt chân lên sao Hỏa... để trồng khoai lang.",
    "Tiền nhiều để làm gì? Để mua thêm oxy chứ gì.",
    "Vũ trụ này là của chúng mình.",
    "Đừng bao giờ từ bỏ ước mơ, trừ khi buồn ngủ.",
    "Thành công là khi bạn không cần nhìn giá khi mua phi thuyền.",
    "Hồi đó tui chỉ là một con bot, giờ tui đã có cơ thể robot rồi!"
]

# ================= UTIL =================
def fetch_image(url):
    try:
        if not url: return None
        r = requests.get(url, timeout=10)
        return Image.open(BytesIO(r.content)).convert("RGBA")
    except: return None

def create_future_img(avatar_url, name, uid, random_year):
    W, H = 800, 500
    img = Image.new("RGB", (W, H), (2, 12, 22))
    draw = ImageDraw.Draw(img)

    try:
        f_big = ImageFont.truetype(FONT_PATH, 45)
        f_mid = ImageFont.truetype(FONT_PATH, 22)
        f_small = ImageFont.truetype(FONT_PATH, 16)
        f_title = ImageFont.truetype(FONT_PATH, 28)
    except:
        f_big = f_mid = f_small = f_title = ImageFont.load_default()

    # Vẽ họa tiết lưới (grid)
    for i in range(0, W, 40):
        draw.line([(i, 0), (i, H)], fill=(10, 40, 60), width=1)
    for i in range(0, H, 40):
        draw.line([(0, i), (W, i)], fill=(10, 40, 60), width=1)

    # 1. HEADER (Sử dụng năm ngẫu nhiên)
    draw.text((30, 20), "SIMULATION RESULT", fill=(0, 150, 255), font=f_title)
    draw.text((W-150, 15), str(random_year), fill=(0, 180, 255), font=f_big)
    draw.text((W-170, 65), "TIME MACHINE v9.0", fill=(0, 100, 180), font=f_small)

    # 2. AVATAR
    avatar = fetch_image(avatar_url)
    if not avatar:
        avatar = Image.new("RGBA", (180, 180), (50, 50, 50))
    avatar = avatar.resize((180, 180))
    mask = Image.new("L", (180, 180), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((0, 0, 180, 180), fill=255)
    img.paste(avatar, (60, 110), mask)
    
    draw.ellipse((55, 105, 245, 295), outline=(0, 255, 255), width=3)
    draw.arc((50, 100, 250, 300), start=0, end=270, fill=(0, 150, 255), width=5)

    # 3. THÔNG TIN CÁ NHÂN
    name_txt = name.upper()
    tw = draw.textlength(name_txt, font=f_title)
    draw.text((60 + (180-tw)//2, 310), name_txt, fill=(0, 255, 255), font=f_title)
    draw.text((110, 350), f"ID: {uid[:6]}", fill=(0, 150, 255), font=f_small)

    # 4. KẾT QUẢ MÔ PHỎNG
    job = random.choice(JOBS)
    career = random.choice(CAREERS)
    asset = random.choice(ASSETS)
    quote = random.choice(QUOTES)

    draw.line([(350, 120), (370, 120)], fill=(0, 255, 255), width=3)
    draw.line([(350, 120), (350, 140)], fill=(0, 255, 255), width=3)
    
    draw.text((380, 125), job, fill=(0, 180, 255), font=f_big)
    draw.text((380, 190), f"Nghề nghiệp:", fill=(150, 150, 150), font=f_small)
    draw.text((500, 190), career, fill=(255, 255, 255), font=f_small)
    draw.text((380, 220), f"Tài sản:", fill=(150, 150, 150), font=f_small)
    draw.text((500, 220), asset, fill=(0, 255, 0), font=f_small)
    
    draw.text((380, 260), f"\"{quote}\"", fill=(180, 180, 180), font=f_small)

    # 5. FOOTER
    draw.text((30, 430), "PROCESSING DATA...", fill=(0, 255, 255), font=f_small)
    draw.text((W-150, 430), "SYSTEM STABLE", fill=(0, 255, 255), font=f_small)

    return img, job

# ================= COMMAND =================
def handle_tuonglai(message, message_object, thread_id, thread_type, author_id, client):
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

    # RANDOM NĂM TỪ 2030 ĐẾN 2080
    random_year = random.randint(2030, 2080)

    img, job = create_future_img(avatar, name, target_id, random_year)
    
    path = f"modules/cache/future_{int(time.time())}.png"
    if not os.path.exists("modules/cache"): os.makedirs("modules/cache")
    img.save(path)

    msg_text = (
        f"🌌 KẾT QUẢ MÔ PHỎNG TƯƠNG LAI 🌌\n\n"
        f"Đối tượng: {name}\n"
        f"Thời gian: Năm {random_year}\n"
        f"Trạng thái: {job}"
    )
    
    client.sendLocalImage(path, thread_id=thread_id, thread_type=thread_type, message=Message(text=msg_text))
    os.remove(path)

# ================= EXPORT =================
def PTA():
    return {
        'tuonglai': handle_tuonglai,
        'future': handle_tuonglai
    }