import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import requests
import random
import concurrent.futures
import time
import base64
from zlapi.models import Message

# Import Prefix
from config import PREFIX

des = {
    'version': "1.1.0",
    'credits': "ngbao",
    'description': "Chế ảnh CCCD (Fix lỗi đè QR)",
    'power': "Thành Viên"
}

FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"

# ================= HÀM HỖ TRỢ =================

def get_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except:
        return ImageFont.load_default()

def fetch_image(url):
    if not url: return None
    try:
        if url.startswith('data:image'):
            return Image.open(BytesIO(base64.b64decode(url.split(',', 1)[1]))).convert("RGBA")
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        return Image.open(BytesIO(response.content)).convert("RGBA")
    except: return None

def draw_centered_text(draw, text, font, center_x, y, color):
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
    except:
        w = font.getlength(text)
    draw.text((center_x - w / 2, y), text, font=font, fill=color)

# ================= LOGIC VẼ CCCD =================

def create_fake_cccd(user_name, avatar_url, gender_input):
    # 1. Tạo nền (Xanh nhạt)
    W, H = 1000, 630
    bg_color = (210, 235, 245)
    bg = Image.new("RGB", (W, H), bg_color)
    draw = ImageDraw.Draw(bg)

    # Vân nền trang trí
    for i in range(0, W, 25):
        draw.line((i, 160, i+150, H), fill=(190, 220, 235), width=2)

    # 2. Quốc Huy (Góc Trái) - Đẩy sang trái để không đè chữ
    draw.ellipse((40, 20, 140, 120), fill=(200, 160, 50)) 
    draw_centered_text(draw, "★", get_font(60), 90, 30, (255, 0, 0))

    # 3. Header (Căn giữa chuẩn W/2 = 500)
    # Thu nhỏ font một chút để an toàn
    draw_centered_text(draw, "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", get_font(28), 500, 30, (0, 0, 0))
    draw_centered_text(draw, "Độc lập - Tự do - Hạnh phúc", get_font(24), 500, 65, (0, 0, 0))
    draw.line((400, 95, 600, 95), fill=(0,0,0), width=2)

    # Tên thẻ
    draw_centered_text(draw, "CĂN CƯỚC CÔNG DÂN", get_font(55), 500, 115, (200, 30, 30))
    
    # Số ID
    id_num = f"0{random.randint(10,99)}0{random.randint(10,99)}{random.randint(100000,999999)}"
    draw_centered_text(draw, f"Số: {id_num}", get_font(32), 500, 180, (0, 0, 0))

    # 4. Mã QR (Góc Phải) - Đẩy xa ra và thu nhỏ lại
    QR_SIZE = 100
    QR_X = 860
    QR_Y = 25
    qr_noise = Image.effect_noise((QR_SIZE, QR_SIZE), 50).convert("RGB")
    bg.paste(qr_noise, (QR_X, QR_Y))

    # 5. Ảnh chân dung (Góc Trái dưới)
    raw_ava = fetch_image(avatar_url)
    if not raw_ava: raw_ava = Image.new("RGBA", (300, 400), (128,128,128))
    
    AVA_W, AVA_H = 250, 330
    raw_ava = raw_ava.resize((AVA_W, AVA_H), Image.Resampling.LANCZOS)
    
    AVA_X, AVA_Y = 50, 230
    bg.paste(raw_ava, (AVA_X, AVA_Y))
    draw.rectangle((AVA_X, AVA_Y, AVA_X+AVA_W, AVA_Y+AVA_H), outline=(150, 150, 150), width=1)

    # 6. Thông tin chi tiết (Bên Phải)
    INFO_X = 330
    START_Y = 240
    LINE_GAP = 55
    
    label_font = get_font(26)
    value_font = get_font(28)
    name_font = get_font(38)

    # Data chế
    places = ["Gầm Cầu Sài Gòn", "Biệt Thự 0 Đồng", "Sao Hỏa", "Viện Tâm Thần", "Trái Tim Em", "Nhà Tù Côn Đảo"]
    origins = ["Vũ Trụ", "Sao Kim", "Thùng Rác", "Wakanda", "Làng Lá"]
    
    place = random.choice(places)
    origin = random.choice(origins)
    dob = f"{random.randint(1,28)}/{random.randint(1,12)}/{random.randint(1995, 2005)}"
    
    sex = "Nam" if gender_input == 1 else "Nữ"
    if gender_input == 0: sex = random.choice(["Nam", "Nữ", "Khác", "Bê Đê"])

    # Vẽ Text
    # Họ tên
    draw.text((INFO_X, START_Y), "Họ và tên:", font=label_font, fill=(80,80,80))
    # Tên màu đỏ, viết hoa
    draw.text((INFO_X + 140, START_Y - 5), user_name.upper(), font=name_font, fill=(200, 30, 30))

    # Ngày sinh
    draw.text((INFO_X, START_Y + LINE_GAP), "Ngày sinh:", font=label_font, fill=(80,80,80))
    draw.text((INFO_X + 140, START_Y + LINE_GAP), dob, font=value_font, fill=(0,0,0))

    # Giới tính & Quốc tịch
    draw.text((INFO_X, START_Y + LINE_GAP*2), "Giới tính:", font=label_font, fill=(80,80,80))
    draw.text((INFO_X + 130, START_Y + LINE_GAP*2), sex, font=value_font, fill=(0,0,0))
    
    draw.text((INFO_X + 250, START_Y + LINE_GAP*2), "Quốc tịch:", font=label_font, fill=(80,80,80))
    draw.text((INFO_X + 400, START_Y + LINE_GAP*2), "Việt Nam", font=value_font, fill=(0,0,0))

    # Quê quán
    draw.text((INFO_X, START_Y + LINE_GAP*3), "Quê quán:", font=label_font, fill=(80,80,80))
    draw.text((INFO_X + 140, START_Y + LINE_GAP*3), origin, font=value_font, fill=(0,0,0))

    # Thường trú
    draw.text((INFO_X, START_Y + LINE_GAP*4), "Nơi thường trú:", font=label_font, fill=(80,80,80))
    draw.text((INFO_X, START_Y + LINE_GAP*4 + 35), place, font=value_font, fill=(0,0,0))

    # Footer
    draw.text((50, 580), "Có giá trị đến: Vô Thời Hạn", font=get_font(22), fill=(0,0,0))
    draw.text((W - 300, 580), "CỤC TRƯỞNG CỤC CHÉM GIÓ", font=get_font(20), fill=(0,0,0))

    return bg

# ================= XỬ LÝ LỆNH =================

def handle_cccd_command(message, message_object, thread_id, thread_type, author_id, client):
    target_id = author_id
    if message_object.mentions:
        target_id = message_object.mentions[0]['uid']
    elif message_object.quote:
        target_id = message_object.quote.ownerId

    client.sendReaction(message_object, "💳", thread_id, thread_type)

    try:
        user_info = client.fetchUserInfo(target_id)
        user_name = "Công Dân Gương Mẫu"
        avatar_url = ""
        gender = 0

        if hasattr(user_info, 'changed_profiles') and str(target_id) in user_info.changed_profiles:
            p = user_info.changed_profiles[str(target_id)]
            user_name = p.get('zaloName', user_name)
            avatar_url = p.get('avatar', avatar_url)
        elif hasattr(user_info, 'name'):
            user_name = user_info.name
            avatar_url = user_info.avatar
            if hasattr(user_info, 'gender'): gender = user_info.gender

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(create_fake_cccd, user_name, avatar_url, gender)
            image = future.result()

        timestamp = int(time.time())
        img_path = f"modules/cache/cccd_{timestamp}.jpg"
        
        if not os.path.exists("modules/cache"):
            os.makedirs("modules/cache")

        image.save(img_path, quality=95)
        
        client.sendLocalImage(
            img_path,
            thread_id=thread_id,
            thread_type=thread_type,
            width=1000,
            height=630,
            message=Message(text=f"💳 Căn cước công dân: {user_name}"),
            ttl=120000
        )
        
        client.sendReaction(message_object, "✅", thread_id, thread_type)
        os.remove(img_path)

    except Exception as e:
        client.replyMessage(Message(text=f"❌ Lỗi: {str(e)}"), message_object, thread_id, thread_type)

def PTA():
    return {
        'cccd': handle_cccd_command,
        'cmnd': handle_cccd_command
    }