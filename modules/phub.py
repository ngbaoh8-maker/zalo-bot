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

# --- IMPORT PREFIX ---
from config import PREFIX

des = {
    'version': "1.0.0",
    'credits': "ngbao",
    'description': "Chế ảnh bình luận phong cách P-Hub",
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

# ================= LOGIC VẼ PHUB COMMENT =================

def create_phub_comment(user_name, avatar_url, comment_text):
    # 1. Cấu hình màu sắc đặc trưng
    BG_COLOR = (30, 30, 30)       # Màu nền xám đen
    TEXT_COLOR = (220, 220, 220)  # Màu chữ trắng xám
    NAME_COLOR = (255, 153, 0)    # Màu cam huyền thoại
    SUB_COLOR = (120, 120, 120)   # Màu chữ phụ
    
    W = 800
    PADDING = 30
    AVATAR_SIZE = 80
    
    # 2. Tính toán chiều cao ảnh dựa trên nội dung
    font_content = get_font(30)
    lines = textwrap.wrap(comment_text, width=45)
    
    # Chiều cao cơ bản + chiều cao text
    text_height = len(lines) * 40
    H = 180 + text_height
    
    bg = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(bg)

    # 3. Avatar (Tròn)
    raw_ava = fetch_image(avatar_url)
    if not raw_ava: raw_ava = Image.new("RGBA", (100, 100), (100, 100, 100))
    
    raw_ava = raw_ava.resize((AVATAR_SIZE, AVATAR_SIZE), Image.Resampling.LANCZOS)
    mask = Image.new("L", (AVATAR_SIZE, AVATAR_SIZE), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, AVATAR_SIZE, AVATAR_SIZE), fill=255)
    
    bg.paste(raw_ava, (PADDING, PADDING), mask)

    # 4. Header: Tên + Badge + Thời gian
    info_x = PADDING + AVATAR_SIZE + 20
    info_y = PADDING + 5
    
    # Vẽ tên (Màu cam)
    font_name = get_font(32)
    draw.text((info_x, info_y), user_name, font=font_name, fill=NAME_COLOR)
    
    # Vẽ Badge PREMIUM (Hình chữ nhật cam nhỏ)
    name_w = font_name.getlength(user_name)
    badge_x = info_x + name_w + 15
    badge_w = 110
    badge_h = 30
    
    draw.rounded_rectangle((badge_x, info_y + 2, badge_x + badge_w, info_y + 2 + badge_h), radius=5, fill=NAME_COLOR)
    
    # Chữ trong Badge
    font_badge = get_font(18)
    draw.text((badge_x + 12, info_y + 5), "PREMIUM", font=font_badge, fill=(255, 255, 255))
    
    # Thời gian (Ví dụ: 69 minutes ago)
    time_ago = f"{random.randint(1, 12)} hours ago"
    draw.text((info_x, info_y + 40), time_ago, font=get_font(22), fill=SUB_COLOR)

    # 5. Nội dung Comment
    content_y = info_y + 80
    emoji_font = get_emoji_font(30)
    
    for line in lines:
        draw.text((info_x, content_y), line, font=font_content, fill=TEXT_COLOR)
        content_y += 40

    # 6. Action Bar (Like, Dislike, Reply)
    action_y = content_y + 15
    
    # Nút Like (Tay cầm lên)
    draw.text((info_x, action_y), "👍", font=emoji_font, fill=SUB_COLOR)
    draw.text((info_x + 40, action_y + 5), "69", font=get_font(24), fill=SUB_COLOR)
    
    # Nút Dislike (Tay cầm xuống)
    draw.text((info_x + 100, action_y), "👎", font=emoji_font, fill=SUB_COLOR)
    
    # Nút Reply & Report
    draw.text((info_x + 160, action_y + 5), "Reply", font=get_font(26), fill=TEXT_COLOR)
    draw.text((info_x + 250, action_y + 5), "Spam", font=get_font(26), fill=SUB_COLOR)
    
    # Kẻ đường line mờ dưới cùng
    draw.line((0, H-2, W, H-2), fill=(50, 50, 50), width=2)

    return bg

# ================= XỬ LÝ LỆNH =================

def handle_phub_command(message, message_object, thread_id, thread_type, author_id, client):
    # Cú pháp: /phub @tag [Nội dung]
    content = message.strip().split()
    target_id = author_id
    comment_text = ""
    
    if message_object.mentions:
        target_id = message_object.mentions[0]['uid']
        full_text = message_object.content
        parts = full_text.split()
        if len(parts) > 2:
            comment_text = " ".join(parts[2:])
    elif message_object.quote:
        target_id = message_object.quote.ownerId
        if len(content) > 1:
            comment_text = " ".join(content[1:])
    else:
        if len(content) > 1:
            comment_text = " ".join(content[1:])

    # Các câu comment bựa
    funny_comments = [
        "Video này hay quá, tôi xem bằng một tay.",
        "Diễn xuất quá đỉnh, Oscar năm nay thuộc về anh.",
        "Tại sao anh thợ sửa ống nước lại không mặc áo?",
        "Tôi đến đây để học toán nhưng lại lạc vào đây.",
        "Cảm ơn vì đã giúp tôi giải trí sau giờ làm việc.",
        "Link full HD không che ở dưới phần mô tả nhé anh em.",
        "Nữ chính xinh quá, xin info với ạ!"
    ]

    if not comment_text:
        comment_text = random.choice(funny_comments)

    client.sendReaction(message_object, "😏", thread_id, thread_type)

    try:
        user_info = client.fetchUserInfo(target_id)
        user_name = "User69"
        avatar_url = ""

        if hasattr(user_info, 'changed_profiles') and str(target_id) in user_info.changed_profiles:
            p = user_info.changed_profiles[str(target_id)]
            user_name = p.get('zaloName', user_name)
            avatar_url = p.get('avatar', avatar_url)
        elif hasattr(user_info, 'name'):
            user_name = user_info.name
            avatar_url = user_info.avatar

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(create_phub_comment, user_name, avatar_url, comment_text)
            image = future.result()

        timestamp = int(time.time())
        img_path = f"modules/cache/phub_{timestamp}.jpg"
        
        if not os.path.exists("modules/cache"):
            os.makedirs("modules/cache")

        image.save(img_path, quality=95)
        
        client.sendLocalImage(
            img_path,
            thread_id=thread_id,
            thread_type=thread_type,
            width=800,
            height=image.height,
            message=Message(text=f"⚫🟠 Bình luận nổi bật từ {user_name}"),
            ttl=120000
        )
        
        client.sendReaction(message_object, "✅", thread_id, thread_type)
        os.remove(img_path)

    except Exception as e:
        client.replyMessage(Message(text=f"❌ Lỗi: {str(e)}"), message_object, thread_id, thread_type)

def PTA():
    return {
        'phub': handle_phub_command,
        'hub': handle_phub_command
    }