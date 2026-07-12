import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageOps
import requests
import textwrap
import random
import concurrent.futures
import time
from zlapi.models import Message
from config import PREFIX

des = {
    'version': "1.3.0",
    'credits': "ngbao",
    'description': "Tạo ảnh bản tin thời sự cực nóng (Tối ưu hiệu suất)",
    'power': "Thành viên"
}

# --- CẤU HÌNH ĐƯỜNG DẪN ---
CACHE_PATH = "modules/cache"
FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
os.makedirs(CACHE_PATH, exist_ok=True)

def get_font(size):
    """Tìm font thông minh tránh lỗi hệ thống"""
    paths = [FONT_PATH, "C:/Windows/Fonts/Arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "arial.ttf"]
    for p in paths:
        if os.path.exists(p): return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def fetch_image(url):
    """Tải ảnh an toàn với timeout"""
    if not url: return None
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return Image.open(BytesIO(response.content)).convert("RGBA")
    except: return None

def create_breaking_news(avatar_url, headline):
    """Vẽ ảnh bản tin thời sự"""
    # Kích thước chuẩn HD
    width, height = 1280, 720
    
    # 1. Tạo nền đỏ thời sự hoặc dùng ảnh nền nếu bạn có file 'news_bg.jpg'
    canvas = Image.new('RGB', (width, height), (180, 0, 0))
    draw = ImageDraw.Draw(canvas)
    
    # 2. Xử lý Avatar người dùng (phóng to làm nền bên trái)
    user_img = fetch_image(avatar_url)
    if user_img:
        # Làm hiệu ứng nền mờ nhẹ đằng sau
        bg_user = user_img.resize((width, height), Image.LANCZOS)
        bg_user = bg_user.point(lambda p: p * 0.5) # Làm tối nền
        canvas.paste(bg_user, (0, 0))
        
        # Ảnh chính diện bên phải
        main_user = user_img.resize((500, 500), Image.LANCZOS)
        canvas.paste(main_user, (700, 50), main_user if main_user.mode == 'RGBA' else None)

    # 3. Vẽ khung bản tin (Overlay)
    # Khung đỏ dưới cùng
    draw.rectangle([0, 550, width, 720], fill=(200, 0, 0))
    # Khung vàng "TIN NÓNG"
    draw.rectangle([0, 500, 300, 550], fill=(255, 200, 0))
    
    font_header = get_font(35)
    font_main = get_font(55)
    
    draw.text((30, 505), "BẢN TIN NÓNG", font=font_header, fill=(0, 0, 0))
    
    # Tự động xuống dòng cho tiêu đề dài
    wrapped_text = textwrap.fill(headline.upper(), width=35)
    draw.text((50, 570), wrapped_text, font=font_main, fill=(255, 255, 255))
    
    # Thêm logo giả định hoặc thời gian
    now = time.strftime("%H:%M")
    draw.text((1150, 20), now, font=font_header, fill=(255, 255, 255))

    return canvas

def handle_news_command(message, message_object, thread_id, thread_type, author_id, client):
    args = message.split(maxsplit=1)
    headline = args[1] if len(args) > 1 else "PHÁT HIỆN ĐỐI TƯỢNG CÓ HÀNH VI QUÁ ĐẸP TRAI"
    
    target_id = author_id
    if message_object.messageReply:
        target_id = message_object.messageReply.senderId
    elif message_object.mentions:
        target_id = list(message_object.mentions.keys())[0]

    try:
        # Gửi reaction chờ
        client.sendReaction(message_object, "📺", thread_id, thread_type)
        
        # Lấy link avatar
        avatar_url = f"https://s120-ava-talk.zadn.vn/a/b/c/{target_id}.jpg"
        
        # Chạy trong ThreadPool để không treo bot
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(create_breaking_news, avatar_url, headline)
            image = future.result()

        img_path = os.path.join(CACHE_PATH, f"news_{thread_id}.jpg")
        image.save(img_path, quality=90)
        
        client.sendLocalImage(
            img_path,
            thread_id=thread_id,
            thread_type=thread_type,
            width=1280, height=720,
            message=Message(text=f"📺 Truyền hình Zalo đưa tin về đối tượng {target_id}!")
        )
        
        if os.path.exists(img_path): os.remove(img_path)

    except Exception as e:
        client.replyMessage(Message(text=f"❌ Lỗi: {str(e)}"), message_object, thread_id, thread_type)

def PTA():
    return {'truyhinh': handle_news_command,
    'fakenews': handle_news_command}