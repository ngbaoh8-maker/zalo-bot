import requests
import threading
import os
import time
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from zlapi.models import Message

# API Key của bạn
WEATHER_API_KEY = "b01eca52b7c0032efbb1c73c9c7e0bcc"

# Đường dẫn cache và font
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_PATH = os.path.join(ROOT_DIR, "modules/cache")
FONT_BOLD = os.path.join(CACHE_PATH, "font/BeVietnamPro-Bold.ttf")
FONT_REG = os.path.join(CACHE_PATH, "font/BeVietnamPro-Regular.ttf")

if not os.path.exists(CACHE_PATH):
    os.makedirs(CACHE_PATH)

des = {
    'version': "1.2.0",
    'credits': "ngbao",
    'description': "Thời tiết kèm ảnh (Sử dụng API Key cá nhân)",
    'power': "Thành Viên"
}

def get_font(path, size):
    if os.path.exists(path):
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def handle_weather_command(message, message_object, thread_id, thread_type, author_id, client):
    def process():
        image_file_path = None
        icon_path = None
        try:
            parts = message.split(" ", 1)
            if len(parts) < 2:
                client.replyMessage(Message(text="⚠️ Nhập tên thành phố! VD: {PREFIX}thoitiet Hanoi"), message_object, thread_id, thread_type)
                return
            
            city = parts[1]
            client.sendReaction(message_object, "⛅", thread_id, thread_type)

            # 1. Lấy dữ liệu từ OpenWeatherMap (lang=vi)
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=vi"
            response = requests.get(url, timeout=10)
            data = response.json()

            if data.get("cod") != 200:
                client.replyMessage(Message(text=f"❌ Không tìm thấy thông tin cho: {city}"), message_object, thread_id, thread_type)
                return

            # 2. Trích xuất thông tin
            name = data['name']
            country = data['sys']['country']
            temp = round(data['main']['temp'], 1)
            feels_like = round(data['main']['feels_like'], 1)
            desc = data['weather'][0]['description'].capitalize()
            humidity = data['main']['humidity']
            wind = data['wind']['speed']
            icon_code = data['weather'][0]['icon']

            # 3. Tạo ảnh nền (Gradient nhẹ)
            w, h = 800, 500
            img = Image.new('RGB', (w, h), color=(255, 255, 255))
            draw = ImageDraw.Draw(img)
            
            # Vẽ nền màu xanh trời
            for i in range(h):
                color = (100, 180, 255 - int(i/4))
                draw.line([(0, i), (w, i)], fill=color)

            # 4. Tải và dán Icon thời tiết
            icon_url = f"http://openweathermap.org/img/wn/{icon_code}@4x.png"
            icon_res = requests.get(icon_url)
            icon_path = os.path.join(CACHE_PATH, f"icon_{icon_code}.png")
            with open(icon_path, 'wb') as f:
                f.write(icon_res.content)
            
            icon_img = Image.open(icon_path).convert("RGBA")
            img.paste(icon_img, (50, 100), icon_img)

            # 5. Viết chữ lên ảnh
            f_title = get_font(FONT_BOLD, 45)
            f_temp = get_font(FONT_BOLD, 80)
            f_info = get_font(FONT_REG, 25)

            draw.text((w//2, 60), f"{name.upper()}, {country}", font=f_title, fill="white", anchor="mm")
            draw.text((250, 180), f"{temp}°C", font=f_temp, fill="white")
            
            info_text = (
                f"☁️ Trạng thái: {desc}\n"
                f"🌡️ Cảm giác như: {feels_like}°C\n"
                f"💧 Độ ẩm: {humidity}% | 🌬️ Gió: {wind}m/s"
            )
            draw.multiline_text((260, 280), info_text, font=f_info, fill="white", spacing=15)
            
            draw.text((w//2, 460), f"Cập nhật: {datetime.now().strftime('%H:%M - %d/%m/%Y')}", font=get_font(FONT_REG, 18), fill=(240, 240, 240), anchor="mm")

            # 6. Lưu và gửi
            image_file_path = os.path.join(CACHE_PATH, f"weather_final_{author_id}.png")
            img.save(image_file_path)
            
            client.sendLocalImage(image_file_path, thread_id, thread_type, message=Message(text=f"🌡️ Dự báo thời tiết {name}"))

        except Exception as e:
            print(f"Lỗi: {e}")
            client.replyMessage(Message(text=f"⚠️ Lỗi: {str(e)}"), message_object, thread_id, thread_type)
        finally:
            if image_file_path and os.path.exists(image_file_path): os.remove(image_file_path)
            if icon_path and os.path.exists(icon_path): os.remove(icon_path)

    threading.Thread(target=process, daemon=True).start()

def PTA():
    return {'tt': handle_weather_command, 'thoitiet': handle_weather_command}