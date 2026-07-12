import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import requests
import random
import concurrent.futures
import time
import base64
from zlapi.models import Message

# --- IMPORT PREFIX TỪ CONFIG ---
from config import PREFIX

des = {
    'version': "1.0.0",
    'credits': "ngbao",
    'description': "Tạo giấy chứng nhận Simp Chúa (Simp Card)",
    'power': "Thành Viên"
}

FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
EMOJI_PATH = "modules/cache/font/NotoEmoji-Bold.ttf"

# ================= HÀM HỖ TRỢ =================

def get_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except:
        return ImageFont.load_default()

def get_emoji_font(size):
    try:
        return ImageFont.truetype(EMOJI_PATH, size)
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

def fit_text(text, max_width, initial_size):
    """Thu nhỏ font tự động"""
    size = initial_size
    font = get_font(size)
    while font.getlength(text) > max_width and size > 20:
        size -= 2
        font = get_font(size)
    return font

# ================= LOGIC VẼ SIMP CARD =================

def create_simp_card(user_name, avatar_url):
    # 1. Tạo nền (Màu hồng nam tính)
    W, H = 1000, 1200
    bg_color = (255, 240, 245) # Lavender Blush
    bg = Image.new("RGB", (W, H), bg_color)
    draw = ImageDraw.Draw(bg)

    # Họa tiết trái tim nền
    heart_font = get_emoji_font(60)
    for _ in range(30):
        x = random.randint(0, W)
        y = random.randint(0, H)
        opacity = random.randint(20, 50)
        draw.text((x, y), "❤", font=heart_font, fill=(255, 182, 193, opacity))

    # Khung viền hồng đậm
    border_gap = 25
    draw.rectangle((border_gap, border_gap, W-border_gap, H-border_gap), outline=(255, 105, 180), width=10)
    draw.rectangle((border_gap+15, border_gap+15, W-border_gap-15, H-border_gap-15), outline=(255, 192, 203), width=5)

    # 2. Header
    draw_centered_text(draw, "GIẤY CHỨNG NHẬN", get_font(60), W/2, 80, (255, 20, 147))
    draw_centered_text(draw, "SIMP CHÚA", get_font(120), W/2, 150, (220, 20, 60))
    
    draw_centered_text(draw, "(Simp Lord Certificate)", get_font(40), W/2, 280, (100, 100, 100))

    # 3. Avatar (Trái tim hoặc Tròn)
    raw_ava = fetch_image(avatar_url)
    if not raw_ava: raw_ava = Image.new("RGBA", (300, 300), (200, 200, 200))
    
    AVA_SIZE = 350
    raw_ava = raw_ava.resize((AVA_SIZE, AVA_SIZE), Image.Resampling.LANCZOS)
    
    # Mask tròn
    mask = Image.new("L", (AVA_SIZE, AVA_SIZE), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, AVA_SIZE, AVA_SIZE), fill=255)
    
    # Vị trí avatar
    AVA_X = (W - AVA_SIZE) // 2
    AVA_Y = 350
    bg.paste(raw_ava, (AVA_X, AVA_Y), mask)
    
    # Viền avatar
    draw.ellipse((AVA_X, AVA_Y, AVA_X+AVA_SIZE, AVA_Y+AVA_SIZE), outline=(255, 20, 147), width=8)

    # 4. Thông tin User
    NAME_Y = 730
    draw_centered_text(draw, "Chứng nhận Simper:", get_font(35), W/2, NAME_Y, (80, 80, 80))
    
    # Tên User (Auto fit)
    name_font = fit_text(user_name.upper(), 800, 80)
    draw_centered_text(draw, user_name.upper(), name_font, W/2, NAME_Y + 50, (0, 0, 0))

    # 5. Các chỉ số Simp (Random)
    STATS_Y = 880
    simp_level = random.randint(80, 1000) # Simp chúa phải cao
    
    funny_targets = ["Crush không yêu mình", "Waifu 2D", "Vợ thằng bạn", "Em gái mưa", "Chị Google", "Cô hàng xóm"]
    target = random.choice(funny_targets)
    
    # Dòng 1: Cấp độ
    draw_centered_text(draw, f"Cấp độ lụy tình: {simp_level}% (Vô cực)", get_font(45), W/2, STATS_Y, (255, 0, 0))
    
    # Dòng 2: Đối tượng
    draw_centered_text(draw, f"Đối tượng Simp: {target}", get_font(40), W/2, STATS_Y + 70, (0, 0, 0))

    # 6. Châm ngôn Simp
    mottos = [
        '"Em vui là anh vui, dù anh mọc sừng"',
        '"Nguyện làm lốp xe dự phòng cả đời"',
        '"Chỉ cần em gọi, anh sẽ đến (làm shipper)"',
        '"Tiền của anh là của em, tiền của em là của em"',
        '"Đội gái lên đầu, trường sinh bất tử"'
    ]
    motto = random.choice(mottos)
    draw_centered_text(draw, motto, get_font(30), W/2, STATS_Y + 140, (100, 100, 100))

    # 7. Con dấu (Stamp) - Góc phải dưới
    STAMP_X = W - 200
    STAMP_Y = H - 200
    
    # Vẽ vòng tròn con dấu
    draw.ellipse((STAMP_X-100, STAMP_Y-100, STAMP_X+100, STAMP_Y+100), outline=(255, 0, 0), width=6)
    draw.ellipse((STAMP_X-90, STAMP_Y-90, STAMP_X+90, STAMP_Y+90), outline=(255, 0, 0), width=2)
    
    # Chữ xoay trong con dấu
    stamp_layer = Image.new("RGBA", (300, 300), (0,0,0,0))
    stamp_draw = ImageDraw.Draw(stamp_layer)
    stamp_draw.text((40, 110), "VERIFIED", font=get_font(50), fill=(255, 0, 0, 200))
    stamp_draw.text((80, 160), "SIMP", font=get_font(50), fill=(255, 0, 0, 200))
    
    stamp_layer = stamp_layer.rotate(25, expand=1)
    bg.paste(stamp_layer, (STAMP_X-150, STAMP_Y-150), stamp_layer)

    return bg

# ================= XỬ LÝ LỆNH =================

def handle_simp_command(message, message_object, thread_id, thread_type, author_id, client):
    target_id = author_id
    if message_object.mentions:
        target_id = message_object.mentions[0]['uid']
    elif message_object.quote:
        target_id = message_object.quote.ownerId

    client.sendReaction(message_object, "🤤", thread_id, thread_type)

    try:
        user_info = client.fetchUserInfo(target_id)
        user_name = "Simp Lord"
        avatar_url = ""

        if hasattr(user_info, 'changed_profiles') and str(target_id) in user_info.changed_profiles:
            p = user_info.changed_profiles[str(target_id)]
            user_name = p.get('zaloName', user_name)
            avatar_url = p.get('avatar', avatar_url)
        elif hasattr(user_info, 'name'):
            user_name = user_info.name
            avatar_url = user_info.avatar

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(create_simp_card, user_name, avatar_url)
            image = future.result()

        timestamp = int(time.time())
        img_path = f"modules/cache/simp_{timestamp}.jpg"
        
        if not os.path.exists("modules/cache"):
            os.makedirs("modules/cache")

        image.save(img_path, quality=95)
        
        client.sendLocalImage(
            img_path,
            thread_id=thread_id,
            thread_type=thread_type,
            width=1000,
            height=1200,
            message=Message(text=f"📜 Phát hiện Simp Chúa: {user_name}"),
            ttl=120000
        )
        
        client.sendReaction(message_object, "✅", thread_id, thread_type)
        os.remove(img_path)

    except Exception as e:
        client.replyMessage(Message(text=f"❌ Lỗi: {str(e)}"), message_object, thread_id, thread_type)

def PTA():
    return {
        'simp': handle_simp_command,
        'simpchua': handle_simp_command
    }