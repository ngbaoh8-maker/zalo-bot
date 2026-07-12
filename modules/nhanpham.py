import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import requests
import random
import concurrent.futures
import time
import base64
from zlapi.models import Message

# --- IMPORT PREFIX THEO MẪU CỦA BẠN ---
from config import PREFIX

des = {
    'version': "2.0.0",
    'credits': "ngbao",
    'description': "Xem thẻ bài nhân phẩm RPG (Style Game)",
    'power': "Thành viên"
}

FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"

# ================= HÀM HỖ TRỢ (GIỐNG MẪU) =================

def get_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except:
        return ImageFont.load_default()

def fetch_image(url):
    if not url: return None
    try:
        # Hỗ trợ cả Base64 như mẫu bạn gửi
        if url.startswith('data:image'):
            return Image.open(BytesIO(base64.b64decode(url.split(',', 1)[1]))).convert("RGBA")
        
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        return Image.open(BytesIO(response.content)).convert("RGBA")
    except: return None

def draw_rounded_rect(draw, box, radius, fill, outline=None, width=1):
    """Hàm vẽ hình chữ nhật bo góc"""
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

# ================= LOGIC VẼ CARD RPG =================

def create_rpg_card(user_name, avatar_url):
    # 1. Random Chỉ số
    stats = {
        "Sức Mạnh": random.randint(10, 100),
        "Trí Tuệ": random.randint(10, 100),
        "Nhan Sắc": random.randint(10, 100),
        "Nhân Phẩm": random.randint(1, 100)
    }
    
    # Tính Rank
    avg = sum(stats.values()) / 4
    if avg >= 90: rank, r_col = "SSS", (255, 215, 0)   # Vàng kim
    elif avg >= 80: rank, r_col = "S", (255, 50, 50)   # Đỏ
    elif avg >= 60: rank, r_col = "A", (180, 50, 255)  # Tím
    elif avg >= 40: rank, r_col = "B", (50, 150, 255)  # Xanh
    else: rank, r_col = "F", (150, 150, 150)           # Xám

    # 2. Tạo Nền (Dark Theme Gaming)
    W, H = 1000, 600
    bg_color = (25, 25, 35)
    bg = Image.new("RGBA", (W, H), bg_color)
    draw = ImageDraw.Draw(bg)

    # Decorate nền
    draw_rounded_rect(draw, (20, 20, W-20, H-20), 20, None, outline=(0, 200, 255), width=2)
    draw.line((350, 20, 350, H-20), fill=(0, 200, 255), width=2)

    # 3. Xử lý Avatar (Bên Trái)
    AVATAR_SIZE = 240
    
    raw_ava = fetch_image(avatar_url)
    if not raw_ava: 
        raw_ava = Image.new("RGBA", (AVATAR_SIZE, AVATAR_SIZE), (100,100,100))
    
    # Resize đẹp
    raw_ava = raw_ava.resize((AVATAR_SIZE, AVATAR_SIZE), Image.Resampling.LANCZOS)
    
    # Vẽ khung avatar
    ava_x, ava_y = 55, 60
    draw.rectangle((ava_x, ava_y, ava_x+AVATAR_SIZE, ava_y+AVATAR_SIZE), outline=(255, 255, 255), width=2)
    bg.paste(raw_ava, (ava_x, ava_y))

    # 4. Tên & Rank (Dưới Avatar)
    # Tự cắt tên nếu quá dài
    if len(user_name) > 12: user_name = user_name[:10] + ".."
    
    draw.text((ava_x, 330), "PLAYER:", font=get_font(25), fill=(150, 150, 150))
    draw.text((ava_x, 360), user_name.upper(), font=get_font(35), fill=(255, 255, 255))
    
    draw.text((ava_x, 430), "RANK:", font=get_font(25), fill=(150, 150, 150))
    draw.text((ava_x, 460), rank, font=get_font(100), fill=r_col)

    # 5. Thanh Chỉ Số (Bên Phải)
    START_X = 400
    START_Y = 80
    BAR_W = 550
    GAP = 120
    
    colors = [
        (255, 60, 60),   # Đỏ
        (60, 160, 255),  # Xanh
        (255, 120, 200), # Hồng
        (60, 255, 100)   # Lá
    ]
    
    for i, (key, val) in enumerate(stats.items()):
        y = START_Y + i * GAP
        # Tên chỉ số
        draw.text((START_X, y), key, font=get_font(35), fill=(255, 255, 255))
        
        # Số đo
        val_str = str(val)
        w_val = get_font(35).getlength(val_str)
        draw.text((START_X + BAR_W - w_val, y), val_str, font=get_font(35), fill=colors[i])
        
        # Thanh Bar
        by = y + 50
        draw_rounded_rect(draw, (START_X, by, START_X+BAR_W, by+30), 15, fill=(50, 50, 60))
        
        fill_w = int(BAR_W * (val/100))
        if fill_w > 0:
            draw_rounded_rect(draw, (START_X, by, START_X+fill_w, by+30), 15, fill=colors[i])

    return bg.convert("RGB")

# ================= XỬ LÝ LỆNH =================

def handle_card_command(message, message_object, thread_id, thread_type, author_id, client):
    # Xác định đối tượng: Tag -> Reply -> Bản thân
    target_id = author_id
    if message_object.mentions:
        target_id = message_object.mentions[0]['uid']
    elif message_object.quote:
        target_id = message_object.quote.ownerId

    client.sendReaction(message_object, "🎲", thread_id, thread_type)

    try:
        # Lấy thông tin user (Code chuẩn theo mẫu quote.py)
        user_info = client.fetchUserInfo(target_id)
        
        # Logic lấy tên/avatar an toàn từ object Zalo
        user_name = "Người bí ẩn"
        avatar_url = ""
        
        # Thử lấy từ changed_profiles (cách mới)
        if hasattr(user_info, 'changed_profiles') and str(target_id) in user_info.changed_profiles:
            p = user_info.changed_profiles[str(target_id)]
            user_name = p.get('zaloName', user_name)
            avatar_url = p.get('avatar', avatar_url)
        # Fallback về thuộc tính thường
        elif hasattr(user_info, 'name'):
            user_name = user_info.name
            avatar_url = user_info.avatar

        # Xử lý ảnh trong luồng riêng
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(create_rpg_card, user_name, avatar_url)
            image = future.result()

        # Lưu cache
        timestamp = int(time.time())
        img_path = f"modules/cache/card_{timestamp}.jpg"
        
        if not os.path.exists("modules/cache"):
            os.makedirs("modules/cache")

        image.save(img_path, quality=95)
        
        client.sendLocalImage(
            img_path,
            thread_id=thread_id,
            thread_type=thread_type,
            width=1000,
            height=600,
            message=Message(text=f"📊 Hồ sơ nhân phẩm: {user_name}"),
            ttl=120000
        )
        
        client.sendReaction(message_object, "✅", thread_id, thread_type)
        os.remove(img_path)

    except Exception as e:
        client.replyMessage(Message(text=f"❌ Lỗi: {str(e)}"), message_object, thread_id, thread_type)

def PTA():
    return {
        'thebai': handle_card_command,
        'nhanpham': handle_card_command,
        'thebainhanpham': handle_card_command
    }