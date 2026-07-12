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
    'description': "Chế ảnh bình luận Youtube (Dark Mode)",
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

# ================= LOGIC VẼ YOUTUBE COMMENT =================

def create_youtube_comment(user_name, avatar_url, comment_text):
    # 1. Cấu hình
    W = 1000
    # Chiều cao sẽ tính động dựa trên độ dài comment, nhưng tối thiểu là 300
    padding = 40
    avatar_size = 100
    
    # Tính toán chiều cao text trước
    font_content = get_font(38)
    lines = textwrap.wrap(comment_text, width=55)
    text_height = len(lines) * 50
    
    H = 250 + text_height # Chiều cao ảnh tùy biến
    
    # Màu Youtube Dark Mode
    bg_color = (15, 15, 15) 
    text_main = (241, 241, 241)
    text_sub = (170, 170, 170)
    
    bg = Image.new("RGB", (W, H), bg_color)
    draw = ImageDraw.Draw(bg)

    # 2. Avatar (Tròn)
    raw_ava = fetch_image(avatar_url)
    if not raw_ava: raw_ava = Image.new("RGBA", (150, 150), (100, 100, 100))
    
    raw_ava = raw_ava.resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)
    mask = Image.new("L", (avatar_size, avatar_size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, avatar_size, avatar_size), fill=255)
    
    bg.paste(raw_ava, (padding, padding), mask)

    # 3. Header: Tên + Thời gian
    name_x = padding + avatar_size + 30
    name_y = padding + 10
    
    # Vẽ tên
    # Xử lý tên user kiểu handle (vd: @User...)
    handle_name = f"@{user_name.replace(' ', '')}"
    font_name = get_font(32)
    draw.text((name_x, name_y), handle_name, font=font_name, fill=text_main)
    
    # Vẽ thời gian (Cách tên một đoạn)
    time_ago = f"{random.randint(1, 59)} phút trước"
    name_w = font_name.getlength(handle_name)
    draw.text((name_x + name_w + 20, name_y + 2), time_ago, font=get_font(28), fill=text_sub)

    # 4. Nội dung Comment
    content_y = name_y + 60
    
    for line in lines:
        draw.text((name_x, content_y), line, font=font_content, fill=text_main)
        content_y += 50

    # 5. Footer: Like, Dislike, Phản hồi
    footer_y = content_y + 20
    
    # Icon Like (👍)
    emoji_font = get_emoji_font(35)
    draw.text((name_x, footer_y), "👍", font=emoji_font, fill=text_main)
    
    # Số like (Random số to)
    likes = random.randint(100, 5000)
    if likes > 1000:
        like_str = f"{likes/1000:.1f} N"
    else:
        like_str = str(likes)
        
    draw.text((name_x + 50, footer_y + 5), like_str, font=get_font(28), fill=text_sub)
    
    # Icon Dislike (👎)
    like_w = get_font(28).getlength(like_str)
    dislike_x = name_x + 50 + like_w + 40
    draw.text((dislike_x, footer_y), "👎", font=emoji_font, fill=text_main)
    
    # Chữ "Phản hồi"
    reply_x = dislike_x + 80
    draw.text((reply_x, footer_y + 5), "Phản hồi", font=get_font(30), fill=text_main)

    # *Bonus*: Ghim bởi chủ kênh (Tạo cảm giác VIP)
    # Vẽ một dòng nhỏ phía trên Avatar
    pinned_y = 10
    # Kéo ảnh xuống chút nếu vẽ thêm cái này (Optional), ở đây mình vẽ đè lên khoảng trống trên cùng nếu H đủ lớn
    # Nhưng để đơn giản, mình vẽ icon trái tim nhỏ bên cạnh avatar chủ kênh
    
    # Vẽ trái tim nhỏ của chủ kênh thả tim (Góc avatar hoặc cạnh nút like)
    # Vẽ icon trái tim nhỏ cạnh nút like (chủ kênh đã thích)
    heart_x = dislike_x + 50
    # draw.text((heart_x, footer_y), "❤️", font=emoji_font, fill=(255, 0, 0)) # Bỏ qua cho đỡ rối

    return bg

# ================= XỬ LÝ LỆNH =================

def handle_youtube_command(message, message_object, thread_id, thread_type, author_id, client):
    # /youtube [Nội dung] hoặc /youtube @tag [Nội dung]
    content = message.strip().split()
    target_id = author_id
    comment_text = ""
    
    # Logic tách lệnh
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

    # Comment mặc định nếu không nhập
    funny_comments = [
        "Ai xem video này năm 2025 điểm danh 👇",
        "Nội dung hay quá, tôi đã xem 10 lần rồi!",
        "Chủ kênh này xứng đáng 1 triệu sub.",
        "Video quá cảm động, tôi đã khóc hết nước mắt 😭",
        "Có ai ở đây từ Facebook qua không?",
        "Xin chào các bạn, mình là fan cứng 20 năm.",
        "Hướng dẫn quá chi tiết, mình đã làm được và cháy nhà."
    ]

    if not comment_text:
        comment_text = random.choice(funny_comments)

    client.sendReaction(message_object, "🔴", thread_id, thread_type)

    try:
        user_info = client.fetchUserInfo(target_id)
        user_name = "User123"
        avatar_url = ""

        if hasattr(user_info, 'changed_profiles') and str(target_id) in user_info.changed_profiles:
            p = user_info.changed_profiles[str(target_id)]
            user_name = p.get('zaloName', user_name)
            avatar_url = p.get('avatar', avatar_url)
        elif hasattr(user_info, 'name'):
            user_name = user_info.name
            avatar_url = user_info.avatar

        # Vẽ ảnh
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(create_youtube_comment, user_name, avatar_url, comment_text)
            image = future.result()

        timestamp = int(time.time())
        img_path = f"modules/cache/yt_{timestamp}.jpg"
        
        if not os.path.exists("modules/cache"):
            os.makedirs("modules/cache")

        image.save(img_path, quality=95)
        
        client.sendLocalImage(
            img_path,
            thread_id=thread_id,
            thread_type=thread_type,
            width=1000,
            height=image.height, # Chiều cao tự động
            message=Message(text=f"🔴 Bình luận nổi bật của: {user_name}"),
            ttl=120000
        )
        
        client.sendReaction(message_object, "✅", thread_id, thread_type)
        os.remove(img_path)

    except Exception as e:
        client.replyMessage(Message(text=f"❌ Lỗi: {str(e)}"), message_object, thread_id, thread_type)

def PTA():
    return {
        'youtube': handle_youtube_command,
        'ytb': handle_youtube_command,
        'comment': handle_youtube_command
    }