import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import requests
import base64
import emoji
import concurrent.futures
import time
import psutil
import platform
import json
import sys
from zlapi.models import Message
from datetime import datetime, timedelta
import pytz

des = {
    'version': "1.2.5",
    'credits': "ngbao",
    'description': "Xem thời tiết khu vực chỉ định với ảnh avatar nền",
    'power': "Thành Viên"
}

apikey = "d7e795ae6a0d44aaa8abb1a0a7ac19e4"
vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
FONT_PATH = "modules/cache/font/NotoSans-Bold.ttf"
EMOJI_FONT_PATH = "modules/cache/font/NotoEmoji-Bold.ttf"

def get_font(size):
    return ImageFont.truetype(FONT_PATH, size)

def get_emoji_font(size):
    return ImageFont.truetype(EMOJI_FONT_PATH, size)

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

def draw_text(draw, text, position, font, emoji_font, image_width, text_color=(255, 255, 255), author_font=None):
    x, y = position
    line_height = int((font.getbbox("Ay")[3] - font.getbbox("Ay")[1]) * 1.4)
    max_width = image_width * 0.9
    all_lines = []
    for line in text.splitlines():
        all_lines.extend(split_text_into_lines(line, font, emoji_font, max_width))
    start_y = y - len(all_lines) * line_height // 2
    for i, line in enumerate(all_lines):
        current_x = x - calculate_text_width(line, author_font if i == 0 and author_font else font,
                                             emoji_font) // 2
        for char in line:
            f = emoji_font if emoji.emoji_count(char) else (author_font if i == 0 and author_font else font)
            draw.text((current_x, start_y), char, fill=text_color, font=f)
            current_x += f.getlength(char)
        start_y += line_height

def make_circle_mask(size):
    mask = Image.new('L', size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size[0], size[1]), fill=255)
    return mask

def draw_circular_avatar(image, avatar_image, position, size):
    if avatar_image:
        image.paste(avatar_image.resize(size), position, mask=make_circle_mask(size))

def calculate_text_height(content, font, emoji_font, image_width):
    dummy_image = Image.new("RGB", (image_width, 1))
    line_height = int(
        (ImageDraw.Draw(dummy_image).textbbox((0, 0), "A", font=font)[3] - ImageDraw.Draw(dummy_image).textbbox((0, 0),
                                                                                                             "A",
                                                                                                             font=font)[
            1]) * 1.4)
    max_width = image_width * 0.9
    all_lines = []
    for line in content.splitlines():
        all_lines.extend(split_text_into_lines(line, font, emoji_font, max_width))
    return len(all_lines) * line_height

def fetch_image(url):
    if not url:
        return None
    try:
        if url.startswith('data:image'):
            return Image.open(BytesIO(base64.b64decode(url.split(',', 1)[1]))).convert("RGB")
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        return Image.open(BytesIO(response.content)).convert("RGB")
    except:
        return None

def fetch_weather(area, retries=3):
    try:
        response = requests.get(
            f"https://api.accuweather.com/locations/v1/cities/search.json?q={requests.utils.quote(area)}&apikey={apikey}&language=vi-vn"
        )
        response.raise_for_status()
        data = response.json()
        if data:
            areaKey = data[0].get('Key')
        else:
            return "Không tìm thấy địa điểm này!"
    except requests.exceptions.RequestException:
        if retries > 0:
            time.sleep(1)
            return fetch_weather(area, retries - 1)
        return "Đã có lỗi xảy ra khi tìm địa điểm!"

    try:
        dataWeather = requests.get(
            f"http://api.accuweather.com/forecasts/v1/daily/10day/{areaKey}?apikey={apikey}&details=true&language=vi"
        )
        dataWeather.raise_for_status()
        dataWeather = dataWeather.json()
    except requests.exceptions.RequestException:
        if retries > 0:
            time.sleep(1)
            return fetch_weather(area, retries - 1)
        return "Đã có lỗi xảy ra khi lấy dữ liệu thời tiết!"

    def convert_F_to_C(F):
        return round((F - 32) / 1.8)

    dataWeatherDaily = dataWeather.get('DailyForecasts', [])
    if not dataWeatherDaily:
        return "Không có dữ liệu dự báo thời tiết!"

    dataWeatherToday = dataWeatherDaily[0]
    rainfall_amount = dataWeatherToday.get('Day', {}).get('Rain', {}).get('Value', 'Không có thông tin')
    rain_chance = dataWeatherToday.get('Day', {}).get('PrecipitationProbability', 'Không có thông tin')
    msg = (
        f"{area}\n"
        f"📆 Hôm nay:\n{dataWeather.get('Headline', {}).get('Text', 'Không có thông tin tiêu đề')}\n"
        f"🌡 Nhiệt độ thấp nhất đến cao nhất: {convert_F_to_C(dataWeatherToday.get('Temperature', {}).get('Minimum', {}).get('Value', 0))}°C - {convert_F_to_C(dataWeatherToday.get('Temperature', {}).get('Maximum', {}).get('Value', 0))}°C\n"
        f"🌡 Nhiệt độ cảm nhận được: {convert_F_to_C(dataWeatherToday.get('RealFeelTemperature', {}).get('Minimum', {}).get('Value', 0))}°C - {convert_F_to_C(dataWeatherToday.get('RealFeelTemperature', {}).get('Maximum', {}).get('Value', 0))}°C\n"
        f"🌧 Lượng mưa: {rainfall_amount} mm\n"
        f"☔ Xác suất mưa: {rain_chance}%\n"
        f"🌞 Ban ngày: {dataWeatherToday.get('Day', {}).get('LongPhrase', 'Không có thông tin')}\n"
        f"🌙 Ban đêm: {dataWeatherToday.get('Night', {}).get('LongPhrase', 'Không có thông tin')}"
    )
    return msg

def process_weather_image(avatar_url, content, author_name):
    base_font_size = 88
    normal_font = get_font(base_font_size)
    emoji_font = get_emoji_font(base_font_size)
    author_font = get_font(base_font_size + 30)
    combined_text = f"{author_name}\n\n{content}"
    text_height = calculate_text_height(combined_text, normal_font, emoji_font, 1600)
    image_width = 2000
    image_height = max(2000, text_height + 200)
    image = Image.new("RGB", (image_width, image_height), color=(50, 50, 50))
    avatar_image = fetch_image(avatar_url)
    if avatar_image:
        image.paste(avatar_image.resize((image_width, image_height)), (0, 0))
        image = ImageEnhance.Brightness(image).enhance(0.3)
    draw = ImageDraw.Draw(image)
    draw_text(draw, combined_text, (image_width // 2, image_height // 2), normal_font, emoji_font, image_width,
              text_color=(255, 255, 255), author_font=author_font)
    return image

def handle_weather_command(message, message_object, thread_id, thread_type, author_id, client):
    text = message.split()
    if len(text) < 2:
        error_message = Message(text="• Vui lòng nhập khu vực cần xem thời tiết.")
        client.sendMessage(error_message, thread_id, thread_type)
        return

    area = " ".join(text[1:])
    weather_info = fetch_weather(area)
    try:
        user_info = client.fetchUserInfo(author_id) or {}
        user_data = user_info.get('changed_profiles', {}).get(str(author_id), {})
        avatar_url = user_data.get("avatar", None)
        author_name = user_data.get("displayName", "Unknown")
        with concurrent.futures.ThreadPoolExecutor() as executor:
            image = executor.submit(process_weather_image, avatar_url, weather_info, author_name).result()
        output_path = "modules/cache/weather_temp.png"
        image.save(output_path, quality=70)
        if os.path.exists(output_path):
            client.sendLocalImage(output_path, thread_id=thread_id, thread_type=thread_type, width=image.width,
                                 height=image.height)
            os.remove(output_path)
    except Exception as e:
         client.sendMessage(Message(text=f"• Đã xảy ra lỗi: {str(e)}"), thread_id, thread_type)

def PTA():
    return {
        'weather': handle_weather_command
    }