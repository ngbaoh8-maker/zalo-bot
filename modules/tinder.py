import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import requests
import textwrap
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
    'description': "Tinder Profile (Fix lỗi đè nút)",
    'power': "Thành Viên"
}

FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
EMOJI_PATH = "modules/cache/font/NotoEmoji-Bold.ttf"

# ================= HÀM HỖ TRỢ =================

def get_font(size):
    try: return ImageFont.truetype(FONT_PATH, size)
    except: return ImageFont.load_default()

def get_emoji_font(size):
    try: return ImageFont.truetype(EMOJI_PATH, size)
    except: return ImageFont.load_default()

def fetch_image(url):
    if not url: return None
    try:
        if url.startswith('data:image'):
            return Image.open(BytesIO(base64.b64decode(url.split(',', 1)[1]))).convert("RGBA")
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        return Image.open(BytesIO(response.content)).convert("RGBA")
    except: return None

# ================= LOGIC VẼ TINDER CARD =================

def create_tinder_profile(user_name, avatar_url, bio_text):
    W, H = 800, 1100
    
    # 1. Xử lý Avatar nền
    bg = fetch_image(avatar_url)
    if not bg: 
        bg = Image.new("RGB", (W, H), (50, 50, 50))
    else:
        bg = bg.convert("RGB")
        img_ratio = bg.width / bg.height
        target_ratio = W / H
        
        if img_ratio > target_ratio:
            new_height = H
            new_width = int(img_ratio * H)
            bg = bg.resize((new_width, new_height), Image.Resampling.LANCZOS)
            left = (new_width - W) // 2
            bg = bg.crop((left, 0, left + W, H))
        else:
            new_width = W
            new_height = int(W / img_ratio)
            bg = bg.resize((new_width, new_height), Image.Resampling.LANCZOS)
            top = (new_height - H) // 2
            bg = bg.crop((0, top, W, top + H))

    draw = ImageDraw.Draw(bg, "RGBA")

    # 2. Bóng mờ Gradient (Làm cao hơn để chữ rõ hơn)
    # Cao 600px thay vì 500px như cũ
    GRADIENT_H = 600
    gradient = Image.new('RGBA', (W, GRADIENT_H), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(gradient)
    for i in range(GRADIENT_H):
        alpha = int((i / GRADIENT_H) * 240) # Đậm hơn chút
        g_draw.line((0, i, W, i), fill=(0, 0, 0, alpha))
    
    bg.paste(gradient, (0, H - GRADIENT_H), gradient)

    # 3. Thông tin User (ĐẨY LÊN CAO)
    # Vị trí cũ là H - 380, giờ đẩy lên H - 480 để né nút
    INFO_X = 40
    NAME_Y = H - 480 
    
    # Tên & Tuổi
    age = random.randint(18, 25)
    name_text = f"{user_name}, {age}"
    
    name_font = get_font(70)
    draw.text((INFO_X, NAME_Y), name_text, font=name_font, fill=(255, 255, 255))
    
    # Tích xanh
    name_w = name_font.getlength(name_text)
    draw.ellipse((INFO_X + name_w + 15, NAME_Y + 15, INFO_X + name_w + 55, NAME_Y + 55), fill=(255, 255, 255))
    draw.ellipse((INFO_X + name_w + 18, NAME_Y + 18, INFO_X + name_w + 52, NAME_Y + 52), fill=(0, 150, 255))
    check_font = get_font(25)
    draw.text((INFO_X + name_w + 25, NAME_Y + 18), "✔", font=check_font, fill=(255, 255, 255))

    # 4. Thông tin phụ (Khoảng cách, Trường học)
    META_Y = NAME_Y + 80
    meta_font = get_font(30)
    emoji_icon_font = get_emoji_font(30)
    
    # Dòng 1: Nhà
    draw.text((INFO_X, META_Y), "🏠", font=emoji_icon_font, fill=(255, 255, 255))
    draw.text((INFO_X + 45, META_Y), "Sống tại Hồ Chí Minh", font=meta_font, fill=(255, 255, 255))
    
    # Dòng 2: Khoảng cách
    km = random.randint(1, 15)
    draw.text((INFO_X, META_Y + 45), "📍", font=emoji_icon_font, fill=(255, 255, 255))
    draw.text((INFO_X + 45, META_Y + 45), f"Cách bạn {km} km", font=meta_font, fill=(255, 255, 255))

    # 5. Phần Bio (ĐẨY LÊN VÀ CẮT NGẮN)
    BIO_Y = META_Y + 95
    bio_font = get_font(32)
    
    # Cắt chữ để đảm bảo không tràn xuống nút
    # Wrap text width 40 ký tự
    lines = textwrap.wrap(bio_text, width=42)
    # Chỉ lấy tối đa 2 dòng, nếu dài hơn thì thêm dấu ...
    if len(lines) > 2:
        display_bio = "\n".join(lines[:2]) + "..."
    else:
        display_bio = "\n".join(lines)
        
    draw.text((INFO_X, BIO_Y), display_bio, font=bio_font, fill=(220, 220, 220))

    # 6. Các nút điều khiển (GIỮ NGUYÊN VỊ TRÍ ĐÁY)
    BTN_Y = H - 140
    CENTER_X = W // 2
    
    def draw_circle_btn(x, y, radius, border_color, icon, icon_color, icon_size=50):
        # Vẽ vòng tròn nền trắng nhẹ (mờ) để nút nổi bật hơn
        draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=(0,0,0,100), outline=border_color, width=4)
        
        font = get_emoji_font(icon_size)
        try:
            bbox = draw.textbbox((0, 0), icon, font=font)
            iw, ih = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except:
            iw, ih = font.getlength(icon), font.size
            
        draw.text((x - iw/2, y - ih/2 - 5), icon, font=font, fill=icon_color)

    # Vẽ nút
    draw_circle_btn(CENTER_X - 240, BTN_Y + 15, 35, (255, 200, 0), "↺", (255, 200, 0), 35) # Rewind
    draw_circle_btn(CENTER_X - 120, BTN_Y, 50, (255, 50, 50), "❌", (255, 50, 50), 45) # Nope
    draw_circle_btn(CENTER_X, BTN_Y + 15, 35, (50, 150, 255), "⭐", (50, 150, 255), 35) # Super Like
    draw_circle_btn(CENTER_X + 120, BTN_Y, 50, (0, 255, 150), "💚", (0, 255, 150), 45) # Like
    draw_circle_btn(CENTER_X + 240, BTN_Y + 15, 35, (180, 50, 255), "⚡", (180, 50, 255), 35) # Boost

    # Huy hiệu NEW
    draw.rounded_rectangle((W - 140, 40, W - 40, 90), radius=10, fill=(220, 50, 50))
    draw.text((W - 120, 50), "MỚI", font=get_font(30), fill=(255, 255, 255))

    return bg

# ================= XỬ LÝ LỆNH =================

def handle_tinder_command(message, message_object, thread_id, thread_type, author_id, client):
    content = message.strip().split()
    target_id = author_id
    bio = ""
    
    if message_object.mentions:
        target_id = message_object.mentions[0]['uid']
        full_text = message_object.content
        parts = full_text.split()
        if len(parts) > 2:
            bio = " ".join(parts[2:])
    elif message_object.quote:
        target_id = message_object.quote.ownerId
        if len(content) > 1:
            bio = " ".join(content[1:])
    else:
        if len(content) > 1:
            bio = " ".join(content[1:])

    funny_bios = [
        "Thích màu hồng và ghét sự giả dối.",
        "Tìm người yêu biết nấu ăn, rửa bát, giặt đồ.",
        "Nhà mặt phố, bố làm to, chưa người yêu.",
        "Nghiêm túc tìm mối quan hệ (hoặc trà sữa).",
        "Nếu em là hình, anh sẽ là bóng.",
        "Chỉ tiếp người đẹp trai/xinh gái.",
        "Học giỏi, ngoan hiền, mỗi tội hay dỗi.",
        "Gấu chưa có mà gió đông đã về."
    ]

    if not bio:
        bio = random.choice(funny_bios)

    client.sendReaction(message_object, "🔥", thread_id, thread_type)

    try:
        user_info = client.fetchUserInfo(target_id)
        user_name = "Anonymous"
        avatar_url = ""

        if hasattr(user_info, 'changed_profiles') and str(target_id) in user_info.changed_profiles:
            p = user_info.changed_profiles[str(target_id)]
            user_name = p.get('zaloName', user_name)
            avatar_url = p.get('avatar', avatar_url)
        elif hasattr(user_info, 'name'):
            user_name = user_info.name
            avatar_url = user_info.avatar

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(create_tinder_profile, user_name, avatar_url, bio)
            image = future.result()

        timestamp = int(time.time())
        img_path = f"modules/cache/tinder_{timestamp}.jpg"
        
        if not os.path.exists("modules/cache"):
            os.makedirs("modules/cache")

        image.save(img_path, quality=95)
        
        client.sendLocalImage(
            img_path,
            thread_id=thread_id,
            thread_type=thread_type,
            width=800,
            height=1100,
            message=Message(text=f"🔥 Có ai muốn Match không?\nUser: {user_name}"),
            ttl=120000
        )
        
        client.sendReaction(message_object, "✅", thread_id, thread_type)
        os.remove(img_path)

    except Exception as e:
        client.replyMessage(Message(text=f"❌ Lỗi: {str(e)}"), message_object, thread_id, thread_type)

def PTA():
    return {
        'tinder': handle_tinder_command,
        'date': handle_tinder_command
    }