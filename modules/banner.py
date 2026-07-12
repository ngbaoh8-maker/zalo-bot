import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import requests
import time
import concurrent.futures
from datetime import datetime
from zlapi.models import Message, Mention

# --- CONFIG ---
from config import PREFIX

des = {
    'version': "2.7.0",
    'credits': "ngbao",
    'description': "Tạo Banner Profile",
    'power': "Thành viên"
}

# Đường dẫn cache
CACHE_PATH = "modules/cache"
FONT_DIR = os.path.join(CACHE_PATH, "font")
FONT_PATH = os.path.join(FONT_DIR, "BeVietnamPro-Bold.ttf")
EMOJI_FONT_PATH = os.path.join(FONT_DIR, "NotoEmoji-Bold.ttf")

if not os.path.exists(FONT_DIR):
    os.makedirs(FONT_DIR)

# ================= HÀM HỖ TRỢ =================

def get_font(size):
    try: return ImageFont.truetype(FONT_PATH, size)
    except:
        try: return ImageFont.truetype("arial.ttf", size)
        except: return ImageFont.load_default()

def get_emoji_font(size):
    try: return ImageFont.truetype(EMOJI_FONT_PATH, size)
    except: return ImageFont.load_default()

def fetch_image(url):
    if not url: return None
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, stream=True, timeout=10)
        response.raise_for_status()
        return Image.open(BytesIO(response.content)).convert("RGBA")
    except: return None

def convert_ts(ts):
    try:
        if not ts: return None
        ts = int(ts)
        if ts <= 0: return None
        if ts > 100000000000: return ts / 1000
        return ts
    except: return None

def format_date_only(ts):
    ts = convert_ts(ts)
    if not ts: return "Đã ẩn"
    try: return datetime.fromtimestamp(ts).strftime("%d/%m/%Y")
    except: return "Lỗi"

def format_full_time(ts):
    ts = convert_ts(ts)
    if not ts: return "Không xác định"
    try: return datetime.fromtimestamp(ts).strftime("%H:%M %d/%m/%Y")
    except: return "Lỗi"

def fit_text_font(text, max_width, initial_size, min_size=15):
    current_size = initial_size
    font = get_font(current_size)
    text_str = str(text)
    while font.getlength(text_str) > max_width and current_size > min_size:
        current_size -= 2
        font = get_font(current_size)
    if font.getlength(text_str) > max_width:
        while font.getlength(text_str + "...") > max_width and len(text_str) > 0:
            text_str = text_str[:-1]
        text_str += "..."
    return font, text_str

def draw_info_row(draw, x, y, icon, label, value, initial_font_size, emoji_font):
    draw.text((x, y), icon, font=emoji_font, fill=(255, 255, 255))
    draw.text((x + 50, y + 5), label, font=get_font(22), fill=(180, 180, 180))
    max_value_width = 280
    end_x = x + 480
    value_font, value_text = fit_text_font(value, max_value_width, initial_font_size)
    value_w = value_font.getlength(value_text)
    y_offset = (32 - value_font.size) // 2 
    draw.text((end_x - value_w, y + y_offset), value_text, font=value_font, fill=(255, 255, 255))

def create_glass_rect(draw, x, y, w, h, radius=15):
    draw.rounded_rectangle((x, y, x+w, y+h), radius=radius, fill=(30, 30, 30, 180), outline=(255, 255, 255, 40), width=1)

# === HÀM FIX LỖI TAG TÊN (QUAN TRỌNG) ===
def get_zalo_len(text):
    """Tính độ dài chuỗi theo chuẩn UTF-16 mà Zalo sử dụng"""
    return len(text.encode('utf-16-le')) // 2

# ================= LOGIC VẼ BANNER =================

def draw_pro_banner(user_data):
    width, height = 1200, 750
    bg = Image.new("RGBA", (width, height), (20, 20, 30))
    
    cover_url = user_data.get('cover')
    avatar_url = user_data.get('avatar')
    bg_img = fetch_image(cover_url) if cover_url else fetch_image(avatar_url)
    if bg_img:
        bg_layer = bg_img.convert("RGBA").resize((width, height), Image.Resampling.LANCZOS)
        bg_layer = bg_layer.filter(ImageFilter.GaussianBlur(radius=15))
        enhancer = ImageEnhance.Brightness(bg_layer)
        bg_layer = enhancer.enhance(0.5)
        bg.paste(bg_layer, (0,0))
    
    draw = ImageDraw.Draw(bg)

    # Avatar
    avt_size = 220
    avt_x, avt_y = 80, 80
    avatar_img_raw = fetch_image(avatar_url)
    if not avatar_img_raw:
        avatar_img_raw = Image.new("RGBA", (avt_size, avt_size), (100, 100, 100))
    mask = Image.new("L", (avt_size, avt_size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, avt_size, avt_size), fill=255)
    avatar_resized = avatar_img_raw.resize((avt_size, avt_size), Image.Resampling.LANCZOS)
    border_color = (0, 200, 255) if user_data.get('is_business') else (255, 255, 255)
    draw.ellipse((avt_x-5, avt_y-5, avt_x+avt_size+5, avt_y+avt_size+5), outline=border_color, width=5)
    bg.paste(avatar_resized, (avt_x, avt_y), mask)

    # Text Info
    text_x, text_y = 340, 100
    name_font, name_text = fit_text_font(user_data.get('name'), 800, 60, min_size=30)
    draw.text((text_x, text_y), name_text, font=name_font, fill=(255, 255, 255))
    draw.text((text_x, text_y + name_font.size + 15), f"UID: {user_data.get('id')}", font=get_font(30), fill=(200, 200, 200))
    
    if user_data.get('is_business'):
        badge_y = text_y + name_font.size + 65
        draw.rounded_rectangle((text_x, badge_y, text_x + 160, badge_y + 35), radius=8, fill=(0, 150, 255))
        draw.text((text_x + 25, badge_y + 5), "BUSINESS", font=get_font(20), fill=(255, 255, 255))

    # Info Box
    info_box_x, info_box_y = 60, 350
    create_glass_rect(draw, info_box_x, info_box_y, 1080, 350, radius=30)
    col_1_x, col_2_x = info_box_x + 40, info_box_x + 560
    row_h = 75
    emoji_font = get_emoji_font(32)
    base_info_size = 28

    draw_info_row(draw, col_1_x, info_box_y + 40, "🚻", "Giới tính", user_data.get('gender_txt'), base_info_size, emoji_font)
    draw_info_row(draw, col_1_x, info_box_y + 40 + row_h, "🎂", "Sinh nhật", user_data.get('dob_txt'), base_info_size, emoji_font)
    draw_info_row(draw, col_1_x, info_box_y + 40 + row_h*2, "🌐", "Global ID", user_data.get('global_id'), base_info_size, emoji_font)
    draw_info_row(draw, col_1_x, info_box_y + 40 + row_h*3, "📱", "SĐT", "Đã ẩn", base_info_size, emoji_font)

    draw_info_row(draw, col_2_x, info_box_y + 40, "📅", "Ngày tạo", user_data.get('created_time'), base_info_size, emoji_font)
    draw_info_row(draw, col_2_x, info_box_y + 40 + row_h, "⏱️", "Hoạt động", user_data.get('last_online'), base_info_size, emoji_font)
    
    status_text = "Online 🟢" if user_data.get('is_active') else "Offline 🔴"
    status_color = (0, 255, 100) if user_data.get('is_active') else (255, 100, 100)
    status_y = info_box_y + 40 + row_h*2
    draw.text((col_2_x, status_y + 5), "⚡", font=emoji_font, fill=(255,255,255))
    draw.text((col_2_x + 50, status_y + 10), "Trạng thái", font=get_font(22), fill=(180,180,180))
    st_font = get_font(28)
    st_w = st_font.getlength(status_text)
    draw.text((col_2_x + 480 - st_w, status_y + 5), status_text, font=st_font, fill=status_color)
    
    draw.text((width - 200, height - 30), "ZaloBot v2.7", font=get_font(18), fill=(100, 100, 100))
    return bg.convert("RGB")

# ================= XỬ LÝ LỆNH =================

def handle_banner_command(message, message_object, thread_id, thread_type, author_id, client):
    target_id = author_id
    if message_object.mentions:
        target_id = message_object.mentions[0]['uid']
    elif message_object.quote:
        target_id = message_object.quote.ownerId

    client.sendReaction(message_object, "🎨", thread_id, thread_type)

    try:
        user_info = client.fetchUserInfo(target_id)
        if not user_info or not hasattr(user_info, 'changed_profiles'):
             client.replyMessage(Message(text="❌ Lỗi lấy thông tin."), message_object, thread_id, thread_type)
             return

        profile = user_info.changed_profiles.get(str(target_id), {})
        
        gender_map = {0: "Nam", 1: "Nữ"}
        gender_txt = gender_map.get(profile.get('gender'), "Khác")
        is_business = True if profile.get('bizPkg', {}).get('label') else False
        
        dob = profile.get('dob', 0)
        dob_txt = str(profile['sdob']) if dob == 0 and 'sdob' in profile else format_date_only(dob)
        
        user_data = {
            'id': target_id,
            'name': profile.get('zaloName', 'Unknown'),
            'avatar': profile.get('avatar', ''),
            'cover': profile.get('cover', ''),
            'gender_txt': gender_txt,
            'dob_txt': dob_txt,
            'created_time': format_date_only(profile.get('createdTs', 0)),
            'last_online': format_full_time(profile.get('lastActionTime', 0)),
            'is_business': is_business,
            'global_id': profile.get('globalId') or "Chưa có",
            'is_active': (int(time.time() * 1000) - int(profile.get('lastActionTime', 0))) < 600000
        }

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(draw_pro_banner, user_data)
            image = future.result()

        timestamp = int(time.time())
        img_path = os.path.join(CACHE_PATH, f"banner_pro_{timestamp}.jpg")
        image.save(img_path, quality=95)
        
        # --- LOGIC FIX TAG CHÍNH XÁC ---
        # 1. Tạo các phần của tin nhắn
        prefix_msg = "👤 Profile: "
        user_name = user_data['name']
        suffix_msg = f"\n📅 Ngày tạo: {user_data['created_time']}"
        
        full_msg = f"{prefix_msg}{user_name}{suffix_msg}"
        
        # 2. Tính offset dựa trên hàm get_zalo_len (tính theo UTF-16)
        # Biểu tượng 👤 (emoji) có len() python = 1, nhưng Zalo tính là 2
        # Hàm get_zalo_len sẽ trả về 2 cho emoji đó, giúp offset chính xác
        mention_offset = get_zalo_len(prefix_msg)
        
        # 3. Tính độ dài tên
        mention_length = get_zalo_len(user_name)

        client.sendLocalImage(
            img_path,
            thread_id=thread_id,
            thread_type=thread_type,
            width=1200,
            height=750,
            message=Message(
                text=full_msg,
                mention=Mention(target_id, length=mention_length, offset=mention_offset)
            ),
            ttl=120000
        )
        
        client.sendReaction(message_object, "✅", thread_id, thread_type)
        try: os.remove(img_path)
        except: pass

    except Exception as e:
        client.replyMessage(Message(text=f"❌ Lỗi: {str(e)}"), message_object, thread_id, thread_type)

def PTA():
    return {
        'banner': handle_banner_command,
        'profile': handle_banner_command,
        'info': handle_banner_command
    }