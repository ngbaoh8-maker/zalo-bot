import colorsys
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import glob
import random
import pytz
from zlapi.models import Message, ThreadType, MultiMsgStyle, MessageStyle
import time
import os
import requests

# Đường dẫn thư mục
BACKGROUND_PATH = "background/"
CACHE_PATH = "modules/cache/"
OUTPUT_IMAGE_PATH = os.path.join(CACHE_PATH, "prefix_menu.png")

# Thông tin mô tả bot
des = {
    'version': "1.0.5",
    'credits': "ngbao",
    'description': "Check prefix and admin status",
    'power': "Thành Viên"
}

# ==========================
# HÀM TẠO ẢNH
# ==========================

def get_dominant_color(image_path):
    img = Image.open(image_path).convert("RGB").resize((150, 150), Image.Resampling.LANCZOS)
    pixels = img.getdata()
    r, g, b = 0, 0, 0
    total = len(pixels)
    for pixel in pixels:
        r += pixel[0]
        g += pixel[1]
        b += pixel[2]
    return (r // total, g // total, b // total) if total else (0, 0, 0)

def random_contrast_color(base_color):
    r, g, b, _ = base_color
    box_luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    if box_luminance > 0.5:
        r, g, b = random.randint(0, 50), random.randint(0, 50), random.randint(0, 50)
    else:
        r, g, b = random.randint(200, 255), random.randint(200, 255), random.randint(200, 255)
    
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    s, v = min(1.0, s + 0.9), min(1.0, v + 0.7)
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    
    text_luminance = (0.299 * r + 0.587 * g + 0.114 * b)
    if abs(text_luminance - box_luminance) < 0.3:
        v = v * 0.4 if box_luminance > 0.5 else v * 1.7
        r, g, b = colorsys.hsv_to_rgb(h, s, min(1.0, v))
    
    return (int(r * 255), int(g * 255), int(b * 255), 255)

def download_avatar(avatar_url, save_path=os.path.join(CACHE_PATH, "user_avatar.png")):
    if not avatar_url:
        return None
    resp = requests.get(avatar_url, stream=True, timeout=0.5)
    if resp.status_code == 200:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            for chunk in resp.iter_content(1024):
                f.write(chunk)
        return save_path
    return None

def generate_menu_image(client, author_id, thread_id, thread_type, username, prefix):
    images = glob.glob(os.path.join(BACKGROUND_PATH, "*.jpg")) + \
             glob.glob(os.path.join(BACKGROUND_PATH, "*.png")) + \
             glob.glob(os.path.join(BACKGROUND_PATH, "*.jpeg"))
    if not images:
        return None

    image_path = random.choice(images)
    size = (1920, 600)
    final_size = (1280, 380)
    bg_image = Image.open(image_path).convert("RGBA").resize(size, Image.Resampling.LANCZOS)
    bg_image = bg_image.filter(ImageFilter.GaussianBlur(radius=7))
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    dominant_color = get_dominant_color(image_path)
    box_color = random.choice([
        (255, 20, 147, 90), (128, 0, 128, 90), (0, 100, 0, 90),
        (0, 0, 139, 90), (184, 134, 11, 90), (138, 3, 3, 90), (0, 0, 0, 90)
    ])

    box_x1, box_y1 = 90, 60
    box_x2, box_y2 = size[0] - 90, size[1] - 60
    draw.rounded_rectangle([(box_x1, box_y1), (box_x2, box_y2)], radius=75, fill=box_color)

    font_arial_path = "arial unicode ms.otf"
    font_emoji_path = "emoji.ttf"
    try:
        font_text_large = ImageFont.truetype(font_arial_path, size=100)
        font_text_big = ImageFont.truetype(font_arial_path, size=90)
        font_text_small = ImageFont.truetype(font_arial_path, size=82)
        font_text_bot = ImageFont.truetype(font_arial_path, size=78)
        font_time = ImageFont.truetype(font_arial_path, size=75)
        font_icon = ImageFont.truetype(font_emoji_path, size=80)
        font_icon_large = ImageFont.truetype(font_emoji_path, size=200)

    except:
        font_text_large = ImageFont.load_default()
        font_text_big = ImageFont.load_default()
        font_text_small = ImageFont.load_default()
        font_text_bot = ImageFont.load_default()
        font_time = ImageFont.load_default()
        font_icon = ImageFont.load_default()
        font_icon_large = ImageFont.load_default()

    def draw_text_with_shadow(draw, position, text, font, fill, shadow_color=(0, 0, 0, 250), shadow_offset=(2, 2)):
        x, y = position
        draw.text((x + shadow_offset[0], y + shadow_offset[1]), text, font=font, fill=shadow_color)
        draw.text((x, y), text, font=font, fill=fill)

    vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    vietnam_now = datetime.now(vietnam_tz)
    hour = vietnam_now.hour
    formatted_time = vietnam_now.strftime("%H:%M")
    time_icon = "🌤️" if 6 <= hour < 18 else "🌙"
    time_text = f" {formatted_time}"
    time_x, time_y = box_x2 - 250, box_y1 + 10

    box_rgb = box_color[:3]
    box_luminance = (0.299 * box_rgb[0] + 0.587 * box_rgb[1] + 0.114 * box_rgb[2]) / 255
    last_lines_color = (255, 255, 255, 220) if box_luminance < 0.5 else (0, 0, 0, 220)

    draw_text_with_shadow(draw, (time_x - 75, time_y - 8), time_icon, font_icon, random_contrast_color(box_color))
    draw.text((time_x, time_y), time_text, font=font_time, fill=last_lines_color)

    user_info = client.fetchUserInfo(author_id) if author_id else None
    user_name = user_info.changed_profiles[author_id].name if user_info and author_id in user_info.changed_profiles else f"ID_{author_id}"

    text_lines = [
        f"🛸 Xin chào {user_name}",
        f"🚦 Bot ngbao cuto Check Prefix Cho Bot ✨",
        f"❄️ Bot By ngbao cuto 🧳",
        f"😁 Bot Sẵn Sàng Phục Vụ 🖤",
        f"🤖 Bot: ngbao Dzai Cte 💻Version: 5.0 📅08/02/26"
    ]

    text_colors = [
        random_contrast_color(box_color),
        random_contrast_color(box_color),
        last_lines_color,
        last_lines_color,
        last_lines_color
    ]
    text_fonts = [font_text_large, font_text_big, font_text_bot, font_text_bot, font_text_small]

    line_spacing = 85
    start_y = box_y1 + 10

    avatar_url = user_info.changed_profiles[author_id].avatar if user_info and author_id in user_info.changed_profiles else None
    avatar_path = download_avatar(avatar_url)
    if avatar_path and os.path.exists(avatar_path):
        avatar_size = 200
        avatar_img = Image.open(avatar_path).convert("RGBA").resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)
        mask = Image.new("L", (avatar_size, avatar_size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, avatar_size, avatar_size), fill=255)
        border_size = avatar_size + 10
        rainbow_border = Image.new("RGBA", (border_size, border_size), (0, 0, 0, 0))
        draw_border = ImageDraw.Draw(rainbow_border)
        for i in range(360):
            h = i / 360
            r, g, b = colorsys.hsv_to_rgb(h, 1.0, 1.0)
            draw_border.arc([(0, 0), (border_size-1, border_size-1)], start=i, end=i + 1, fill=(int(r * 255), int(g * 255), int(b * 255), 255), width=5)
        avatar_y = (box_y1 + box_y2 - avatar_size) // 2
        overlay.paste(rainbow_border, (box_x1 + 40, avatar_y), rainbow_border)
        overlay.paste(avatar_img, (box_x1 + 45, avatar_y + 5), mask)
    else:
        draw.text((box_x1 + 60, (box_y1 + box_y2) // 2 - 140), "🐳", font=font_icon, fill=(0, 139, 139, 255))

    current_line_idx = 0
    for i, line in enumerate(text_lines):
        if not line:
            current_line_idx += 1
            continue
        parts = []
        current_part = ""
        for char in line:
            if ord(char) > 0xFFFF:
                if current_part:
                    parts.append(current_part)
                    current_part = ""
                parts.append(char)
            else:
                current_part += char
        if current_part:
            parts.append(current_part)

        total_width = 0
        part_widths = []
        current_font = font_text_bot if i == 4 else text_fonts[i]
        for part in parts:
            font_to_use = font_icon if any(ord(c) > 0xFFFF for c in part) else current_font
            width = draw.textbbox((0, 0), part, font=font_to_use)[2]
            part_widths.append(width)
            total_width += width

        max_width = box_x2 - box_x1 - 300
        if total_width > max_width:
            font_size = int(current_font.getbbox("A")[3] * max_width / total_width * 0.9)
            font_size = max(font_size, 60)
            current_font = ImageFont.truetype(font_arial_path, size=font_size) if os.path.exists(font_arial_path) else ImageFont.load_default(size=font_size)
            total_width = 0
            part_widths = []
            for part in parts:
                font_to_use = font_icon if any(ord(c) > 0xFFFF for c in part) else current_font
                width = draw.textbbox((0, 0), part, font=font_to_use)[2]
                part_widths.append(width)
                total_width += width

        text_x = (box_x1 + box_x2 - total_width) // 2
        text_y = start_y + current_line_idx * line_spacing + (current_font.getbbox("A")[3] // 2)

        current_x = text_x
        for part, width in zip(parts, part_widths):
            if any(ord(c) > 0xFFFF for c in part):
                draw_text_with_shadow(draw, (current_x, text_y), part, font_icon, random_contrast_color(box_color))
            else:
                if i < 2:
                    draw_text_with_shadow(draw, (current_x, text_y), part, current_font, text_colors[i])
                else:
                    draw.text((current_x, text_y), part, font=current_font, fill=text_colors[i])
            current_x += width
        current_line_idx += 1

    draw_text_with_shadow(draw, (box_x2 - 225, (box_y1 + box_y2 - 180) // 2), "🛠️", font_icon_large, random_contrast_color(box_color))

    final_image = Image.alpha_composite(bg_image, overlay)
    final_image = final_image.resize(final_size, Image.Resampling.LANCZOS)
    os.makedirs(os.path.dirname(OUTPUT_IMAGE_PATH), exist_ok=True)
    final_image.save(OUTPUT_IMAGE_PATH, "PNG", quality=95)
    return OUTPUT_IMAGE_PATH

# ==========================
# HÀM XỬ LÝ PREFIX
# ==========================

def checkprefix(message, message_object, thread_id, thread_type, author_id, client):
    # Lấy prefix và username trực tiếp từ client
    prefix = client.prefix if hasattr(client, 'prefix') else "."
    username = client.me_name if hasattr(client, 'me_name') else "Bot Không Tên"

    # Hiển thị prefix và username cho mọi người dùng
    msg = f"🚦 BOT: ngbao Dzai\n🔧 Prefix bây giờ của bot là: {prefix}\n Liên hệ zalo 0911037051 đễ được hỗ trợ. "
    styles = MultiMsgStyle([
        MessageStyle(offset=0, length=2, style="color", color="#f38ba8", auto_format=False),
        MessageStyle(offset=2, length=len(username), style="color", color="#cdd6f4", auto_format=False),
        MessageStyle(offset=2 + len(username), length=len(msg) - len(username) - 2, style="color", color="#cdd6f4", auto_format=False)
    ])

    # Gửi reaction và ảnh cho mọi người
    for reaction in ["🚀", "🚦", "🚧"]:
        client.sendReaction(message_object, reaction, thread_id, thread_type)
        time.sleep(0.2)

    image_path = generate_menu_image(client, author_id, thread_id, thread_type, username, prefix)
    if image_path:
        client.sendLocalImage(
            imagePath=image_path,
            message=Message(text=msg, style=styles),
            thread_id=thread_id,
            thread_type=thread_type,
            width=1280,
            height=380,
            ttl=240000
        )
        if os.path.exists(image_path):
            os.remove(image_path)
    else:
        client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=60000)
  
      
def PTA():
    return {
        'xem': checkprefix  # Lệnh để gọi hàm bói bài Jocker
    }