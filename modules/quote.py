import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import requests
import textwrap
import base64
import emoji
import concurrent.futures
import time
from zlapi.models import Message
from config import PREFIX

des = {
    'version': "1.0.0",
    'credits': "ngbao",
    'description': "Tạo ảnh trích dẫn (Quote) nghệ thuật",
    'power': "Thành viên"
}

FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
EMOJI_FONT_PATH = "modules/cache/font/NotoEmoji-Bold.ttf"

def get_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except:
        return ImageFont.load_default()

def get_emoji_font(size):
    try:
        return ImageFont.truetype(EMOJI_FONT_PATH, size)
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

def draw_quote_card(avatar_url, user_name, quote_text):
    # 1. Cấu hình
    width, height = 1200, 630 # Kích thước chuẩn hiển thị đẹp trên điện thoại
    bg_color = (20, 20, 20)
    text_color = (255, 255, 255)
    accent_color = (0, 255, 200) # Màu xanh ngọc

    # 2. Tạo nền
    bg = Image.new("RGBA", (width, height), bg_color)
    
    # Xử lý nền từ avatar (Làm mờ + Tối)
    avatar_img = fetch_image(avatar_url)
    if avatar_img:
        bg_layer = avatar_img.resize((width, height))
        bg_layer = bg_layer.filter(ImageFilter.GaussianBlur(radius=25)) # Mờ mạnh
        enhancer = ImageEnhance.Brightness(bg_layer)
        bg_layer = enhancer.enhance(0.4) # Tối đi để nổi bật chữ
        bg.paste(bg_layer, (0,0))
    
    draw = ImageDraw.Draw(bg)

    # 3. Vẽ Avatar tròn bên trái
    if avatar_img:
        avt_size = 180
        avt_x, avt_y = 80, (height - avt_size) // 2
        
        mask = Image.new("L", (avt_size, avt_size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, avt_size, avt_size), fill=255)
        
        avatar_resized = avatar_img.resize((avt_size, avt_size))
        
        # Viền avatar
        draw.ellipse((avt_x-5, avt_y-5, avt_x+avt_size+5, avt_y+avt_size+5), outline=accent_color, width=4)
        bg.paste(avatar_resized, (avt_x, avt_y), mask)

    # 4. Vẽ dấu ngoặc kép trang trí
    quote_symbol_font = get_font(150)
    draw.text((300, 50), "“", font=quote_symbol_font, fill=(255, 255, 255, 50))

    # 5. Xử lý văn bản (Tự xuống dòng)
    quote_font = get_font(50)
    emoji_font = get_emoji_font(50)
    
    # Tự động xuống dòng nếu văn bản dài
    wrapped_lines = textwrap.wrap(quote_text, width=25) 
    
    # Tính toán vị trí Y để căn giữa theo chiều dọc
    line_height = 70
    total_text_height = len(wrapped_lines) * line_height
    start_y = (height - total_text_height) // 2 - 30
    text_x = 320 # Cách lề trái (nơi đặt avatar)

    for line in wrapped_lines:
        current_x = text_x
        for char in line:
            # Xử lý emoji và text thường
            f = emoji_font if emoji.emoji_count(char) else quote_font
            draw.text((current_x, start_y), char, font=f, fill=text_color)
            current_x += f.getlength(char)
        start_y += line_height

    # 6. Vẽ tên tác giả
    author_font = get_font(35)
    draw.text((text_x, start_y + 40), f"— {user_name}", font=author_font, fill=accent_color)
    
    # 7. Watermark nhỏ
    wm_font = get_font(20)
    draw.text((width - 250, height - 40), "✨ Created by ZaloBot", font=wm_font, fill=(150, 150, 150))

    return bg.convert("RGB")

def handle_quote_command(message, message_object, thread_id, thread_type, author_id, client):
    content = " ".join(message.strip().split()[1:]).strip()
    
    # Nếu không nhập gì thì lấy tin nhắn được reply
    if not content and message_object.quote:
        content = message_object.quote.content

    if not content:
        client.replyMessage(
            Message(text=f"⚠️ Vui lòng nhập nội dung!\nVí dụ: {PREFIX}quote Hôm nay trời đẹp quá"),
            message_object, thread_id, thread_type
        )
        return

    client.sendReaction(message_object, "🎨", thread_id, thread_type)

    try:
        # Lấy thông tin người dùng (người gửi lệnh hoặc người bị reply)
        target_id = author_id
        if message_object.quote:
            target_id = message_object.quote.ownerId

        user_info = client.fetchUserInfo(target_id) or {}
        user_profile = user_info.get('changed_profiles', {}).get(str(target_id), {})
        
        user_name = user_profile.get('zaloName', 'Người dùng bí ẩn')
        avatar_url = user_profile.get('avatar', '')

        # Xử lý ảnh trong luồng riêng để không lag bot
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(draw_quote_card, avatar_url, user_name, content)
            image = future.result()

        # Lưu và gửi
        timestamp = int(time.time())
        img_path = f"modules/cache/quote_{timestamp}.jpg"
        
        if not os.path.exists("modules/cache"):
            os.makedirs("modules/cache")

        image.save(img_path, quality=95)
        
        client.sendLocalImage(
            img_path,
            thread_id=thread_id,
            thread_type=thread_type,
            width=1200,
            height=630,
            ttl=120000
        )
        
        client.sendReaction(message_object, "✅", thread_id, thread_type)
        os.remove(img_path)

    except Exception as e:
        client.replyMessage(Message(text=f"❌ Lỗi: {str(e)}"), message_object, thread_id, thread_type)

def PTA():
    return {
        'quote': handle_quote_command,
        'trichdan': handle_quote_command,
        'sodeep': handle_quote_command
    }