import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import requests
import base64
import emoji
import concurrent.futures
import time
from zlapi.models import Message
from datetime import datetime
import pytz
import random

des = {
    'version': "1.2.5",
    'credits': "ngbao",
    'description': "Xem thời tiết khu vực chỉ định với ảnh nền neon",
    'power': "Thành Viên"
}

apikey = "d7e795ae6a0d44aaa8abb1a0a7ac19e4"
vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')

FONT_PATH = "modules/cache/font/NotoSans-Bold.ttf"
EMOJI_FONT_PATH = "modules/cache/font/NotoEmoji-Bold.ttf"


# ================= FONT =================
def get_font(size):
    return ImageFont.truetype(FONT_PATH, size)

def get_emoji_font(size):
    return ImageFont.truetype(EMOJI_FONT_PATH, size)


# ================= TEXT UTILS =================
def calculate_text_width(text, font, emoji_font):
    return sum(emoji_font.getlength(c) if emoji.emoji_count(c) else font.getlength(c) for c in text)

def split_text_into_lines(text, font, emoji_font, max_width):
    lines, current_line = [], []
    for word in text.split():
        temp_line = " ".join(current_line + [word])
        if calculate_text_width(temp_line, font, emoji_font) <= max_width:
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
    return lines + [" ".join(current_line)]

def calculate_text_height(content, font, emoji_font, image_width):
    line_height = int(font.size * 1.4)
    lines = []
    for line in content.splitlines():
        lines.extend(split_text_into_lines(line, font, emoji_font, image_width * 0.9))
    return len(lines) * line_height


# ================= IMAGE UTILS =================
def fetch_image(url):
    if not url:
        return None
    try:
        if url.startswith('data:image'):
            return Image.open(BytesIO(base64.b64decode(url.split(',', 1)[1]))).convert("RGBA")
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        return Image.open(BytesIO(response.content)).convert("RGBA")
    except:
        return None


# ================= WEATHER API =================
def fetch_weather(area, retries=3):
    try:
        response = requests.get(
            f"https://api.accuweather.com/locations/v1/cities/search.json?q={requests.utils.quote(area)}&apikey={apikey}&language=vi-vn"
        )
        response.raise_for_status()
        data = response.json()
        if not data:
            return "Không tìm thấy địa điểm này!"
        areaKey = data[0].get("Key")
    except:
        return "Lỗi khi tìm địa điểm!"

    try:
        dataWeather = requests.get(
            f"http://api.accuweather.com/forecasts/v1/daily/10day/{areaKey}?apikey={apikey}&details=true&language=vi"
        ).json()
    except:
        return "Lỗi khi lấy dữ liệu thời tiết!"

    def F_to_C(F):
        return round((F - 32) / 1.8)

    today = dataWeather["DailyForecasts"][0]
    msg = (
        f"{area}\n"
        f"📆 Hôm nay:\n{dataWeather.get('Headline', {}).get('Text', '')}\n"
        f"🌡 Nhiệt độ: {F_to_C(today['Temperature']['Minimum']['Value'])}°C - {F_to_C(today['Temperature']['Maximum']['Value'])}°C\n"
        f"🌡 Cảm nhận: {F_to_C(today['RealFeelTemperature']['Minimum']['Value'])}°C - {F_to_C(today['RealFeelTemperature']['Maximum']['Value'])}°C\n"
        f"🌧 Lượng mưa: {today['Day'].get('Rain', {}).get('Value', '?')} mm\n"
        f"☔ Xác suất mưa: {today['Day'].get('PrecipitationProbability', '?')}%\n"
        f"🌞 Ban ngày: {today['Day'].get('LongPhrase', '')}\n"
        f"🌙 Ban đêm: {today['Night'].get('LongPhrase', '')}"
    )
    return msg

# =============== MAIN RENDER (NỀN SÁNG + NEON GIẢM CHÓI) ===============
def process_weather_image(avatar_url, content, author_name):

    # ====== FONT NHỎ, GỌN ======
    base_font_size = 55
    normal_font = get_font(base_font_size)
    emoji_font = get_emoji_font(base_font_size)
    author_font = get_font(base_font_size + 20)

    combined_text = f"{author_name}\n\n{content}"

    # ====== RANDOM BACKGROUND GIỐNG menu.py ======
    BG_URLS = [
        "https://files.catbox.moe/y5fg9j.jpg",
        "https://files.catbox.moe/t31gfd.jpg",
        "https://files.catbox.moe/77c4by.jpg",
        "https://files.catbox.moe/d7p28q.jpg"
    ]

    bg = fetch_image(random.choice(BG_URLS))
    if bg is None:
        bg = Image.new("RGBA", (2000, 2000), (60, 65, 80))

    # ====== TÍNH SIZE ẢNH ======
    text_h = calculate_text_height(combined_text, normal_font, emoji_font, 1600)
    width, height = 2000, max(1700, text_h + 400)

    bg = bg.resize((width, height), Image.LANCZOS)

    # ====== Blur nền nhẹ, không làm tối quá ======
    bg = bg.filter(ImageFilter.GaussianBlur(5))

    # ====== Glass overlay sáng hơn ======
    glass = Image.new("RGBA", (width, height), (50, 60, 80, 95))  # ít tối → nền sáng hơn
    bg = Image.alpha_composite(bg.convert("RGBA"), glass)

    draw = ImageDraw.Draw(bg, "RGBA")

    # ========== NEON TEXT GIẢM CHÓI ==========
    def neon(text, x, y, font, color=(0, 255, 255)):
        for radius in (5, 3, 2):   # glow nhẹ
            draw.text(
                (x, y),
                text,
                font=font,
                fill=(color[0], color[1], color[2], 110),   # giảm sáng
                stroke_width=radius,
                stroke_fill=(color[0], color[1], color[2], 85)  # neon mượt
            )

        # Main text
        draw.text((x, y), text, font=font, fill=(240, 240, 255))

    # ====== RENDER TEXT ======
    lines = combined_text.split("\n")
    line_h = int(base_font_size * 1.6)

    y = (height - len(lines) * line_h) // 2

    for i, line in enumerate(lines):
        font_used = author_font if i == 0 else normal_font  # tên user to hơn

        neon(
            line,
            width // 2 - calculate_text_width(line, normal_font, emoji_font) // 2,
            y,
            font_used
        )
        y += line_h

    return bg.convert("RGB")

# =============== COMMAND HANDLER ===============
def handle_weather_command(message_text, message_object, thread_id, thread_type, author_id, client):
    text = message_text.split(maxsplit=1)
    if len(text) < 2:
        client.sendMessage(
            Message(text="• Vui lòng nhập khu vực cần xem thời tiết."),
            thread_id, thread_type
        )
        return

    area = text[1].strip()
    weather_info = fetch_weather(area)

    try:
        # Load avatar + tên người dùng
        user_data = client.fetchUserInfo(author_id)
        profile = user_data.get("changed_profiles", {}).get(str(author_id), {})

        avatar = profile.get("avatar", None)
        name = profile.get("displayName", "Người dùng")

        # Tạo ảnh trong thread
        with concurrent.futures.ThreadPoolExecutor() as exe:
            img = exe.submit(process_weather_image, avatar, weather_info, name).result()

        # Lưu file tạm
        out = f"modules/cache/weather_{int(time.time())}.jpg"
        img.save(out, "JPEG", quality=95)

        # Gửi ảnh
        client.sendLocalImage(
            out, thread_id=thread_id, thread_type=thread_type,
            width=img.width, height=img.height, ttl=120000
        )

        # Xóa file tạm
        if os.path.exists(out):
            os.remove(out)

    except Exception as e:
        client.sendMessage(
            Message(text=f"⚠️ Đã xảy ra lỗi khi tạo ảnh thời tiết.\nChi tiết: {e}"),
            thread_id, thread_type
        )


# =============== EXPORT PTA ===============
def PTA():
    return {"weatherneon": handle_weather_command}
