import os
import requests
import random
import time
import concurrent.futures
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from zlapi.models import Message, Mention
from config import PREFIX

# --- PHẦN KHAI BÁO ---
des = {
    'version': "4.6.0",
    'credits': "ngbao",
    'description': "Ghép đôi với giao diện tối ưu",
    'power': "Thành viên"
}

# --- CẤU HÌNH ĐƯỜNG DẪN ---
CACHE_PATH = "modules/cache"
# Tự động tạo thư mục nếu chưa có
os.makedirs(CACHE_PATH, exist_ok=True)

def get_font(size):
    """Tối ưu hóa việc tìm font hệ thống để tránh crash"""
    font_paths = [
        "modules/cache/font/BeVietnamPro-Bold.ttf",
        "C:/Windows/Fonts/Arial.ttf", # Windows
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", # Linux/VPS
        "arial.ttf"
    ]
    for path in font_paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def process_avatar(url, size):
    """Tải và bo tròn avatar, thêm viền trắng"""
    try:
        response = requests.get(url, timeout=5)
        img = Image.open(BytesIO(response.content)).convert("RGBA")
        img = img.resize((size, size), Image.LANCZOS)
        
        # Tạo mặt nạ tròn
        mask = Image.new('L', (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        
        output = ImageOps.fit(img, mask.size, centering=(0.5, 0.5))
        output.putalpha(mask)
        return output
    except:
        # Nếu lỗi avatar, trả về một hình tròn màu xám
        fallback = Image.new('RGBA', (size, size), (200, 200, 200, 255))
        mask = Image.new('L', (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        fallback.putalpha(mask)
        return fallback

def draw_ship_card(u1, u2, percent):
    """Vẽ ảnh ghép đôi chuyên nghiệp"""
    width, height = 1200, 600
    # Tạo background gradient
    base = Image.new('RGB', (width, height), (30, 30, 30))
    draw = ImageDraw.Draw(base)
    
    # Vẽ màu nền gradient hồng tím
    for i in range(width):
        r = int(255 - (i / width) * 100)
        g = int(100 + (i / width) * 50)
        b = int(150 + (i / width) * 100)
        draw.line([(i, 0), (i, height)], fill=(r, g, b))

    # Xử lý 2 avatar
    ava1 = process_avatar(u1['avatar'], 250)
    ava2 = process_avatar(u2['avatar'], 250)
    
    base.paste(ava1, (150, 150), ava1)
    base.paste(ava2, (800, 150), ava2)

    # Vẽ trái tim ở giữa
    heart_size = 150
    font_heart = get_font(100)
    draw.text((550, 200), "❤️", font=font_heart, fill=(255, 255, 255))
    
    # Vẽ thông tin tên và phần trăm
    font_name = get_font(50)
    font_percent = get_font(80)
    
    # Căn giữa tên
    draw.text((150, 420), u1['name'][:15], font=font_name, fill=(255, 255, 255))
    draw.text((800, 420), u2['name'][:15], font=font_name, fill=(255, 255, 255))
    draw.text((510, 350), f"{percent}%", font=font_percent, fill=(255, 255, 0))

    return base

def get_love_comment(percent):
    if percent > 80: return "Cặp đôi trời sinh, cưới ngay kẻo lỡ! 💍"
    if percent > 50: return "Khá là hợp nhau đấy, tiến tới thôi! ❤️"
    return "Cần cố gắng nhiều hơn nếu muốn thành đôi. 💔"

def handle_ghepdoi_command(message, message_object, thread_id, thread_type, author_id, client):
    # Lấy danh sách thành viên trong nhóm để random
    try:
        group_info = client.fetchGroupInfo(thread_id).gridInfoMap[thread_id]
        member_ids = [m for m in group_info['memData'] if str(m) != str(author_id)]
        
        if not member_ids:
            return client.replyMessage(Message(text="Nhóm này chả có ai để ghép với bạn cả!"), message_object, thread_id, thread_type)
        
        target_id = random.choice(member_ids)
        
        # Lấy info 2 người
        def get_user_data(uid):
            try:
                info = client.fetchUserInfo(uid).changedNames.get(uid, "Người dùng")
                avatar = f"https://s120-ava-talk.zadn.vn/a/b/c/{uid}.jpg"
                return {'name': info, 'avatar': avatar}
            except:
                return {'name': "Ẩn danh", 'avatar': ""}

        u1 = get_user_data(author_id)
        u2 = get_user_data(target_id)
        percent = random.randint(0, 100)

        # Tạo banner
        img = draw_ship_card(u1, u2, percent)
        
        img_path = f"{CACHE_PATH}/ship_{thread_id}.jpg"
        img.save(img_path, quality=90)
        
        caption = f"💘 Kết quả ghép đôi: {u1['name']} ❤️ {u2['name']}\n📊 Tỉ lệ hợp nhau: {percent}%\n💬 Nhận xét: {get_love_comment(percent)}"
        
        client.sendLocalImage(
            img_path,
            thread_id=thread_id,
            thread_type=thread_type,
            message=Message(text=caption)
        )
        
        if os.path.exists(img_path):
            os.remove(img_path)

    except Exception as e:
        client.replyMessage(Message(text=f"❌ Lỗi: {str(e)}"), message_object, thread_id, thread_type)

def PTA():
    return {'ghepdoi': handle_ghepdoi_command}