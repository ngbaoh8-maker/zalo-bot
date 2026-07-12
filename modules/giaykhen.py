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

# Import Prefix từ config
from config import PREFIX

des = {
    'version': "2.0.0",
    'credits': "ngbao",
    'description': "Tạo giấy khen",
    'power': "Thành viên"
}

FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"

# ================= HÀM HỖ TRỢ =================

def get_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
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
    """Thu nhỏ font cho đến khi vừa khung"""
    size = initial_size
    font = get_font(size)
    while font.getlength(text) > max_width and size > 20:
        size -= 2
        font = get_font(size)
    return font

# ================= LOGIC VẼ GIẤY KHEN =================

def create_certificate(user_name, avatar_url, reason):
    # 1. Tạo nền
    W, H = 1200, 850
    bg_color = (255, 253, 240)
    bg = Image.new("RGB", (W, H), bg_color)
    draw = ImageDraw.Draw(bg)

    # Khung viền
    draw.rectangle((20, 20, W-20, H-20), outline=(218, 165, 32), width=15)
    draw.rectangle((40, 40, W-40, H-40), outline=(180, 50, 50), width=3)
    
    # Góc trang trí
    corner = 50
    gold = (218, 165, 32)
    draw.ellipse((15, 15, 15+corner, 15+corner), fill=gold)
    draw.ellipse((W-15-corner, 15, W-15, 15+corner), fill=gold)
    draw.ellipse((15, H-15-corner, 15+corner, H-15), fill=gold)
    draw.ellipse((W-15-corner, H-15-corner, W-15, H-15), fill=gold)

    # 2. Header (Quốc hiệu & Tiêu đề) -> Đẩy lên cao để tiết kiệm chỗ
    draw_centered_text(draw, "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", get_font(28), W/2, 60, (0,0,0))
    draw_centered_text(draw, "Độc lập - Tự do - Hạnh phúc", get_font(22), W/2, 95, (0,0,0))
    draw.line((W/2 - 100, 125, W/2 + 100, 125), fill=(0,0,0), width=1)

    # Chữ GIẤY KHEN (Màu đỏ tươi)
    draw_centered_text(draw, "GIẤY KHEN", get_font(90), W/2, 140, (220, 30, 30))

    # 3. Avatar và Tên (Đặt ngang hàng nhau ở giữa)
    CONTENT_Y = 280
    
    # Xử lý Avatar
    raw_ava = fetch_image(avatar_url)
    if not raw_ava: raw_ava = Image.new("RGBA", (150, 150), (200, 200, 200))
    
    AVA_SIZE = 160
    raw_ava = raw_ava.resize((AVA_SIZE, AVA_SIZE), Image.Resampling.LANCZOS)
    mask = Image.new("L", (AVA_SIZE, AVA_SIZE), 0)
    ImageDraw.Draw(mask).ellipse((0,0,AVA_SIZE,AVA_SIZE), fill=255)
    
    # Vị trí Avatar: Lệch trái một chút
    ava_x = 300
    bg.paste(raw_ava, (ava_x, CONTENT_Y), mask)
    draw.ellipse((ava_x, CONTENT_Y, ava_x+AVA_SIZE, CONTENT_Y+AVA_SIZE), outline=gold, width=4)

    # Vị trí Tên: Nằm bên phải Avatar
    text_x = ava_x + AVA_SIZE + 40
    text_y_start = CONTENT_Y + 20
    
    draw.text((text_x, text_y_start), "Tặng cho:", font=get_font(35), fill=(80, 80, 80))
    
    # Tên người nhận (Tự co nhỏ nếu tên dài quá 500px)
    name_font = fit_text(user_name.upper(), 500, 65)
    draw.text((text_x, text_y_start + 45), user_name.upper(), font=name_font, fill=(0, 0, 0))

    # 4. Lý do (Nằm dưới Avatar + Tên)
    REASON_Y = CONTENT_Y + AVA_SIZE + 40 # Cách avatar 40px
    
    draw_centered_text(draw, "Đã có thành tích xuất sắc:", get_font(30), W/2, REASON_Y, (80, 80, 80))
    
    # Wrap text lý do (Tối đa 2 dòng để không đè footer)
    reason_font = get_font(45)
    lines = textwrap.wrap(reason, width=40) 
    
    current_y = REASON_Y + 50
    # Chỉ in tối đa 3 dòng
    for line in lines[:3]:
        draw_centered_text(draw, line, reason_font, W/2, current_y, (0, 0, 150))
        current_y += 55

    # 5. Footer (Chữ ký & Ngày tháng) -> Đẩy xuống đáy
    FOOTER_Y = 680
    SIGN_X = W - 300
    
    date_str = f"Ngày {time.strftime('%d')} tháng {time.strftime('%m')} năm {time.strftime('%Y')}"
    draw_centered_text(draw, date_str, get_font(24), SIGN_X, FOOTER_Y, (0, 0, 0))
    
    draw_centered_text(draw, "TM. BAN QUẢN TRỊ", get_font(28), SIGN_X, FOOTER_Y + 30, (220, 30, 30))
    draw_centered_text(draw, "(Đã Ký)", get_font(28), SIGN_X, FOOTER_Y + 70, (0, 0, 0))
    
    # Con dấu
    draw.ellipse((SIGN_X-70, FOOTER_Y+40, SIGN_X+70, FOOTER_Y+140), outline=(255, 0, 0), width=4)
    # Xoay chữ DUYỆT một chút cho nghệ
    txt_layer = Image.new("RGBA", (200, 100), (0,0,0,0))
    txt_draw = ImageDraw.Draw(txt_layer)
    txt_draw.text((50, 20), "DUYỆT", font=get_font(35), fill=(255, 0, 0))
    txt_layer = txt_layer.rotate(15, expand=1)
    bg.paste(txt_layer, (SIGN_X-90, FOOTER_Y+50), txt_layer)

    return bg

# ================= XỬ LÝ LỆNH =================

def handle_certificate_command(message, message_object, thread_id, thread_type, author_id, client):
    content = message.strip().split()
    target_id = author_id
    reason = ""
    
    # Xác định người nhận & lý do
    if message_object.mentions:
        target_id = message_object.mentions[0]['uid']
        # Lấy text sau khi tag
        full_text = message_object.content
        # Tách đơn giản: lấy phần sau dấu cách thứ 2 (prefix + lệnh + tag)
        parts = full_text.split()
        if len(parts) > 2:
            reason = " ".join(parts[2:])
    elif message_object.quote:
        target_id = message_object.quote.ownerId
        if len(content) > 1:
            reason = " ".join(content[1:])
    else:
        # Tự khen
        if len(content) > 1:
            reason = " ".join(content[1:])

    # Random lý do nếu để trống
    funny_reasons = [
        "Danh hiệu 'Chúa Tể Bom Hàng' năm nay",
        "Có công gánh team còng cả lưng",
        "Thức khuya dậy trễ, ngủ nướng đệ nhất",
        "Nói đạo lý hay nhất Vịnh Bắc Bộ",
        "Đã cai nghiện trà sữa thành công (1 tiếng)",
        "Thành tích: Ế bền vững 20 năm",
        "Luôn có mặt lúc ăn, vắng mặt lúc làm"
    ]

    if not reason:
        reason = random.choice(funny_reasons)
        
    # Giới hạn độ dài lý do để không vỡ khung
    if len(reason) > 80:
        reason = reason[:77] + "..."

    client.sendReaction(message_object, "🏆", thread_id, thread_type)

    try:
        user_info = client.fetchUserInfo(target_id)
        user_name = "Người Bí Ẩn"
        avatar_url = ""

        if hasattr(user_info, 'changed_profiles') and str(target_id) in user_info.changed_profiles:
            p = user_info.changed_profiles[str(target_id)]
            user_name = p.get('zaloName', user_name)
            avatar_url = p.get('avatar', avatar_url)
        elif hasattr(user_info, 'name'):
            user_name = user_info.name
            avatar_url = user_info.avatar

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(create_certificate, user_name, avatar_url, reason)
            image = future.result()

        timestamp = int(time.time())
        img_path = f"modules/cache/cert_{timestamp}.jpg"
        
        if not os.path.exists("modules/cache"):
            os.makedirs("modules/cache")

        image.save(img_path, quality=95)
        
        client.sendLocalImage(
            img_path,
            thread_id=thread_id,
            thread_type=thread_type,
            width=1200,
            height=850,
            message=Message(text=f"📜 Giấy khen trao tặng: {user_name}"),
            ttl=120000
        )
        
        client.sendReaction(message_object, "✅", thread_id, thread_type)
        os.remove(img_path)

    except Exception as e:
        client.replyMessage(Message(text=f"❌ Lỗi: {str(e)}"), message_object, thread_id, thread_type)

def PTA():
    return {
        'khen': handle_certificate_command,
        'bangkhen': handle_certificate_command
    }