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
    'description': "Ảnh Messenger",
    'power': "Thành viên"
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

def draw_rounded_rect(draw, box, radius, fill):
    draw.rounded_rectangle(box, radius=radius, fill=fill)

# ================= LOGIC VẼ iMESSAGE =================

def create_imessage(user_name, avatar_url, message_text):
    # 1. Cấu hình
    W, H = 800, 1000
    bg_color = (255, 255, 255)
    bg = Image.new("RGB", (W, H), bg_color)
    draw = ImageDraw.Draw(bg)

    # 2. Header (Thanh trạng thái & Info người gửi)
    # Giờ
    draw.text((40, 20), "9:41", font=get_font(30), fill=(0,0,0))
    # Icon pin, sóng (Vẽ giả lập)
    draw.rectangle((W-70, 25, W-30, 45), outline=(150,150,150), width=2)
    draw.rectangle((W-68, 27, W-40, 43), fill=(0,0,0)) # Pin đầy
    
    # Avatar người gửi (Ở giữa trên cùng)
    AVATAR_SIZE = 120
    raw_ava = fetch_image(avatar_url)
    if not raw_ava: raw_ava = Image.new("RGBA", (100, 100), (200, 200, 200))
    
    raw_ava = raw_ava.resize((AVATAR_SIZE, AVATAR_SIZE), Image.Resampling.LANCZOS)
    mask = Image.new("L", (AVATAR_SIZE, AVATAR_SIZE), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, AVATAR_SIZE, AVATAR_SIZE), fill=255)
    
    ava_x = (W - AVATAR_SIZE) // 2
    ava_y = 100
    bg.paste(raw_ava, (ava_x, ava_y), mask)
    
    # Tên người gửi
    name_font = get_font(35)
    try:
        bbox = draw.textbbox((0, 0), user_name, font=name_font)
        name_w = bbox[2] - bbox[0]
    except:
        name_w = name_font.getlength(user_name)
    
    draw.text(((W - name_w) / 2, ava_y + AVATAR_SIZE + 15), user_name, font=name_font, fill=(0,0,0))
    
    # Chữ "iMessage" mờ mờ
    draw.text(((W - 120) / 2, ava_y + AVATAR_SIZE + 60), "Messenger", font=get_font(25), fill=(150,150,150))

    # 3. Bong bóng tin nhắn (Bubble) - Tin nhắn đến (Màu xám)
    # Xử lý text wrap
    msg_font = get_font(40)
    emoji_font = get_emoji_font(40)
    
    # Tính toán độ rộng tối đa của bong bóng
    max_bubble_width = 550
    lines = textwrap.wrap(message_text, width=30) # Ước lượng
    
    # Tính chiều cao bong bóng
    line_height = 50
    padding_v = 30
    padding_h = 40
    
    bubble_h = len(lines) * line_height + padding_v * 2
    
    # Tính độ rộng thực tế của dòng dài nhất
    max_line_w = 0
    for line in lines:
        w = msg_font.getlength(line)
        if w > max_line_w: max_line_w = w
    
    bubble_w = max_line_w + padding_h * 2
    
    # Vị trí bong bóng (Bên trái vì là người khác nhắn đến)
    bubble_x = 40
    bubble_y = 450
    
    # Vẽ cái đuôi bong bóng (Tail)
    draw.polygon([(bubble_x - 10, bubble_y + bubble_h - 20), (bubble_x + 20, bubble_y + bubble_h - 20), (bubble_x + 20, bubble_y + bubble_h + 10)], fill=(233, 233, 235))

    # Vẽ thân bong bóng (Bo tròn)
    draw_rounded_rect(draw, (bubble_x, bubble_y, bubble_x + bubble_w, bubble_y + bubble_h), 35, (233, 233, 235))

    # Viết nội dung
    text_y = bubble_y + padding_v
    for line in lines:
        draw.text((bubble_x + padding_h, text_y), line, font=msg_font, fill=(0,0,0))
        text_y += line_height

    # 4. Trạng thái "Đã đọc" (Optional)
    draw.text((bubble_x + 10, bubble_y + bubble_h + 15), "Đã đọc 10:30", font=get_font(25), fill=(150,150,150))

    # 5. Thanh nhập liệu (Footer)
    footer_y = H - 120
    # Icon Camera (Giả lập)
    draw.rectangle((30, footer_y + 20, 80, footer_y + 60), fill=(150, 150, 150))
    
    # Ô nhập liệu
    draw_rounded_rect(draw, (110, footer_y, W - 110, footer_y + 80), 40, (240, 240, 240))
    draw.text((140, footer_y + 25), "iMessage", font=get_font(30), fill=(180, 180, 180))
    
    # Icon Micro
    draw.ellipse((W - 80, footer_y + 10, W - 30, footer_y + 60), fill=(150, 150, 150))

    return bg

# ================= XỬ LÝ LỆNH =================

def handle_imessage_command(message, message_object, thread_id, thread_type, author_id, client):
    # Cú pháp: /ib @tag [Nội dung]
    content = message.strip().split()
    target_id = author_id
    msg_content = ""
    
    if message_object.mentions:
        target_id = message_object.mentions[0]['uid']
        full_text = message_object.content
        parts = full_text.split()
        if len(parts) > 2:
            msg_content = " ".join(parts[2:])
    elif message_object.quote:
        target_id = message_object.quote.ownerId
        if len(content) > 1:
            msg_content = " ".join(content[1:])
    else:
        if len(content) > 1:
            msg_content = " ".join(content[1:])

    # Tin nhắn mẫu troll
    funny_msgs = [
        "Anh oii,em dới anh dí nhau nhá",
        "Thay quần lót cho em đi",
        "Chúng ta chia tay đi, em chán anh rồi.",
        "Anh cho em bú cu anh nhó:3",
        "bé iuu anh nhiều lắm",
        "đm m trả t 100triệu nhanh",
        "Chúc mừng m được 1 quả lọ từ ngbao.",
        "anh ơi em sắp raa ><",
        "em em sướng quá sắp ra rùi",
        "cu anh sắp ra rùii hẻ",
        "em dớii anh cưới nhauu di",
        "em qlai dớii nyc nha..",
        "anh qua nhà em đi em cho anh đụ e",
        "peter anh rỉ ròii kìa>.<",
        "chemchep em ngứa quá anh gãi dùm được không?"
    ]

    if not msg_content:
        msg_content = random.choice(funny_msgs)

    client.sendReaction(message_object, "📱", thread_id, thread_type)

    try:
        user_info = client.fetchUserInfo(target_id)
        user_name = "Người yêu cũ"
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
            future = executor.submit(create_imessage, user_name, avatar_url, msg_content)
            image = future.result()

        timestamp = int(time.time())
        img_path = f"modules/cache/ib_{timestamp}.jpg"
        
        if not os.path.exists("modules/cache"):
            os.makedirs("modules/cache")

        image.save(img_path, quality=95)
        
        client.sendLocalImage(
            img_path,
            thread_id=thread_id,
            thread_type=thread_type,
            width=800,
            height=1000,
            message=Message(text=f"📱 Tin nhắn từ: {user_name}"),
            ttl=120000
        )
        
        client.sendReaction(message_object, "✅", thread_id, thread_type)
        os.remove(img_path)

    except Exception as e:
        client.replyMessage(Message(text=f"❌ Lỗi: {str(e)}"), message_object, thread_id, thread_type)

def PTA():
    return {
        'mess': handle_imessage_command,
        'mes': handle_imessage_command,
        'messenger': handle_imessage_command
    }