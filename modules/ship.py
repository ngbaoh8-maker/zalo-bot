import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import requests
import random
import time
import concurrent.futures
from zlapi.models import Message, Mention

# --- PHẦN KHAI BÁO THEO MẪU CŨ ---
from config import PREFIX

des = {
    'version': "4.5.0",
    'credits': "ngbao",
    'description': "Ghép đôi tình yêu (Premium V4 - Fix Font & Config)",
    'power': "Thành viên"
}

# --- CẤU HÌNH ĐƯỜNG DẪN ---
CACHE_PATH = "modules/cache"
FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
EMOJI_PATH = "modules/cache/font/NotoEmoji-Bold.ttf"

# Tự tạo thư mục nếu chưa có
if not os.path.exists(CACHE_PATH):
    os.makedirs(CACHE_PATH)

# ================= HÀM HỖ TRỢ (Font & Ảnh) =================

def get_font(size):
    """Tự động fallback font nếu không tìm thấy file"""
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except:
        try:
            return ImageFont.truetype("arial.ttf", size) # Fallback Windows
        except:
            return ImageFont.load_default()

def get_emoji_font(size):
    try:
        return ImageFont.truetype(EMOJI_PATH, size)
    except:
        return ImageFont.load_default()

def fetch_image(url):
    """Tải ảnh an toàn"""
    if not url: return None
    try:
        headers = {'User-Agent': 'Mozilla/5.0'} # Giả lập trình duyệt để tránh bị chặn
        response = requests.get(url, headers=headers, stream=True, timeout=5)
        response.raise_for_status()
        return Image.open(BytesIO(response.content)).convert("RGBA")
    except:
        return None

def circle_crop(img, size):
    """Cắt ảnh tròn"""
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    output = Image.new("RGBA", (size, size), (0,0,0,0))
    output.paste(img, (0,0), mask)
    return output

def draw_centered_text(draw, text, font, x, y, color, shadow=True):
    """Vẽ chữ căn giữa"""
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except:
        w = font.getlength(text)
        h = font.size
    
    if shadow:
        draw.text((x - w/2 + 2, y - h/2 + 2), text, font=font, fill=(0,0,0,160))
    
    draw.text((x - w/2, y - h/2), text, font=font, fill=color)

def get_love_comment(percent):
    if percent < 15: return "💀 Âm dương cách biệt, bỏ đi em ơi!"
    if percent < 35: return "💔 Friendzone cứng ngắc, chia buồn."
    if percent < 55: return "⚖️ 50/50, cái này hên xui à nha."
    if percent < 75: return "🔥 Rất hợp nhau, triển ngay cho nóng!"
    if percent < 90: return "🥰 Trời sinh một cặp, cưới đi chờ chi!"
    return "💍 Bách niên giai lão, định mệnh đời nhau rồi!"

# ================= CORE VẼ ẢNH =================

def draw_ship_card(u1, u2, percent):
    # Kích thước ảnh nền
    W, H = 1200, 600
    bg = Image.new("RGB", (W, H), (45, 20, 60))
    
    # Hiệu ứng nền (Gradient giả & Tim bay)
    overlay = Image.new("RGBA", (W, H), (0,0,0,0))
    draw_ov = ImageDraw.Draw(overlay)
    
    # Glow tròn ở giữa
    draw_ov.ellipse((W//2-250, H//2-250, W//2+250, H//2+250), fill=(255, 100, 150, 40))
    
    # Random tim bay
    for _ in range(20):
        x = random.randint(0, W)
        y = random.randint(0, H)
        size = random.randint(20, 50)
        draw_ov.text((x, y), "❤", font=get_emoji_font(size), fill=(255, 255, 255, 30))
        
    bg.paste(overlay, (0,0), overlay)
    draw = ImageDraw.Draw(bg)

    # --- Xử lý Avatar ---
    AVATAR_SIZE = 220
    Y_CENTER = 230
    OFFSET = 300
    
    def paste_avatar(url, cx):
        raw = fetch_image(url)
        if not raw: raw = Image.new("RGBA", (AVATAR_SIZE, AVATAR_SIZE), (128,128,128))
        
        avatar = circle_crop(raw, AVATAR_SIZE)
        
        # Shadow cho avatar
        shadow = Image.new("RGBA", (AVATAR_SIZE+20, AVATAR_SIZE+20), (0,0,0,0))
        ImageDraw.Draw(shadow).ellipse((10, 10, AVATAR_SIZE+10, AVATAR_SIZE+10), fill=(0,0,0,100))
        shadow = shadow.filter(ImageFilter.GaussianBlur(8))
        
        bg.paste(shadow, (cx - AVATAR_SIZE//2 - 10, Y_CENTER - AVATAR_SIZE//2 - 10), shadow)
        bg.paste(avatar, (cx - AVATAR_SIZE//2, Y_CENTER - AVATAR_SIZE//2), avatar)

    paste_avatar(u1['avatar'], W//2 - OFFSET)
    paste_avatar(u2['avatar'], W//2 + OFFSET)

    # --- Thông tin ---
    heart = "❤️" if percent >= 50 else "💔"
    draw_centered_text(draw, heart, get_emoji_font(120), W//2, Y_CENTER - 20, (255,0,0), shadow=False)
    draw_centered_text(draw, f"{percent}%", get_font(50), W//2, Y_CENTER + 15, (255, 223, 0))

    # Tên
    name_y = Y_CENTER + AVATAR_SIZE//2 + 40
    f_name = get_font(35)
    draw_centered_text(draw, u1['name'], f_name, W//2 - OFFSET, name_y, (255, 255, 255))
    draw_centered_text(draw, u2['name'], f_name, W//2 + OFFSET, name_y, (255, 255, 255))

    # Thanh %
    bar_w, bar_h = 600, 26
    bar_x, bar_y = (W - bar_w)//2, name_y + 50
    draw.rounded_rectangle((bar_x, bar_y, bar_x+bar_w, bar_y+bar_h), radius=13, fill=(0,0,0,150), outline=(255,255,255), width=2)
    
    fill_w = int((bar_w-4) * (percent/100))
    if fill_w > 0:
        col = (255, 60, 60) if percent < 50 else (60, 255, 100)
        draw.rounded_rectangle((bar_x+2, bar_y+2, bar_x+2+fill_w, bar_y+bar_h-2), radius=10, fill=col)

    # Lời bình
    comment = get_love_comment(percent)
    draw_centered_text(draw, comment, get_font(28), W//2, bar_y + 50, (220, 220, 255))
    
    return bg

# ================= HÀM XỬ LÝ LỆNH =================

def handle_ship_command(message, message_object, thread_id, thread_type, author_id, client):
    mentions = message_object.mentions
    uid1 = author_id
    uid2 = None
    
    # Logic xác định 2 người
    if len(mentions) == 1:
        uid2 = mentions[0]['uid']
    elif len(mentions) >= 2:
        uid1 = mentions[0]['uid']
        uid2 = mentions[1]['uid']
    else:
        if message_object.quote:
            uid2 = message_object.quote.ownerId
        else:
            # Sử dụng PREFIX từ config
            client.replyMessage(Message(text=f"⚠️ Vui lòng tag người muốn ghép đôi!\nVí dụ: {PREFIX}ship @Crush"), message_object, thread_id, thread_type)
            return

    client.sendReaction(message_object, "💘", thread_id, thread_type)

    def get_info(uid):
        try:
            data = client.fetchUserInfo(uid)
            # Check cấu trúc data trả về tùy phiên bản zlapi
            name = "Unknown"
            avatar = ""
            
            if hasattr(data, 'changed_profiles') and str(uid) in data.changed_profiles:
                prof = data.changed_profiles[str(uid)]
                name = prof.get('zaloName', name)
                avatar = prof.get('avatar', avatar)
            elif hasattr(data, 'name'):
                name = data.name
                avatar = data.avatar
                
            return {'name': name, 'avatar': avatar}
        except:
            return {'name': "Ẩn danh", 'avatar': ""}

    try:
        u1 = get_info(uid1)
        u2 = get_info(uid2)
        percent = random.randint(0, 100)

        # Chạy vẽ ảnh trong thread riêng
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(draw_ship_card, u1, u2, percent)
            img = future.result()

        timestamp = int(time.time())
        img_path = f"{CACHE_PATH}/ship_v4_{timestamp}.jpg"
        img.save(img_path, quality=95)
        
        caption = f"💘 Kết quả: {percent}% - {u1['name']} ❤️ {u2['name']}\n💬 {get_love_comment(percent)}"
        
        client.sendLocalImage(
            img_path,
            thread_id=thread_id,
            thread_type=thread_type,
            width=1200,
            height=600,
            message=Message(text=caption),
            ttl=120000
        )
        
        client.sendReaction(message_object, "✅", thread_id, thread_type)
        try: os.remove(img_path)
        except: pass

    except Exception as e:
        client.replyMessage(Message(text=f"❌ Lỗi: {str(e)}"), message_object, thread_id, thread_type)

def PTA():
    return {
        'ship': handle_ship_command,
        'ghepdoi': handle_ship_command,
        'love': handle_ship_command
    }