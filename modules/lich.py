# -*- coding: utf-8 -*-
import os
import tempfile
import datetime
from lunarcalendar import Converter, Solar
from PIL import Image, ImageDraw, ImageFont
from zlapi.models import Message, MultiMsgStyle, MessageStyle
from config import PREFIX

des = {
    'version': "3.0.2",
    'credits': "ngbao",
    'description': "Hiển thị lịch ngày hôm nay dạng ảnh đầy đủ 📅",
    'power': "Thành Viên"
}

FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
CACHE_DIR = "modules/cache/lich_temp"
os.makedirs(CACHE_DIR, exist_ok=True)

def get_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except:
        return ImageFont.load_default()

def save_temp(img):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        img.convert("RGB").save(tmp.name, "JPEG", quality=95)
        return tmp.name

def get_special_days(today):
    events = [
        ("Ngày Nhà giáo Việt Nam", datetime.date(today.year, 11, 20)),
        ("Ngày TLQĐND Việt Nam", datetime.date(today.year, 12, 22)),
        ("Tết Dương lịch", datetime.date(today.year + 1, 1, 1)),
        ("Giỗ Tổ Hùng Vương", datetime.date(today.year + 1, 4, 6))
    ]
    lines = []
    for name, date in events:
        diff = (date - today).days
        if diff >= 0:
            lines.append(f"{diff} ngày nữa - {name}")
    return lines

def draw_calendar_image(name):
    WIDTH, HEIGHT = 1080, 1080
    bg = Image.new("RGB", (WIDTH, HEIGHT), (245, 245, 255))
    draw = ImageDraw.Draw(bg)

    title_font = get_font(52)
    info_font = get_font(32)
    small_font = get_font(26)
    num_font = get_font(32)
    header_font = get_font(30)

    now = datetime.datetime.now()
    today = now.date()
    solar = Solar(today.year, today.month, today.day)
    lunar = Converter.Solar2Lunar(solar)

    weekdays = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
    weekday = weekdays[today.weekday()]
    lunar_text = f"{lunar.day:02d}/{lunar.month:02d}/{lunar.year}"

    title = f"{weekday}, Ngày {today.day} Tháng {today.month} Năm {today.year}"
    draw.text((80, 60), title, font=title_font, fill=(0, 0, 0))
    draw.text((80, 130), now.strftime("%H:%M"), font=info_font, fill=(60, 60, 80))
    draw.text((80, 180), f"Âm Lịch - {lunar_text}", font=info_font, fill=(50, 50, 80))

    special_lines = get_special_days(today)
    y = 240
    for line in special_lines:
        draw.text((80, y), line, font=small_font, fill=(40, 40, 60))
        y += 38

    y_offset = y + 30
    first_day = today.replace(day=1)
    next_month = today.replace(month=today.month % 12 + 1, day=1)
    days_in_month = (next_month - datetime.timedelta(days=1)).day
    start_weekday = (first_day.weekday() + 1) % 7

    days_header = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    x_start, y_start = 100, y_offset + 40
    cell_w, cell_h = 110, 85

    for i, d in enumerate(days_header):
        color = (200, 50, 50) if d == "CN" else (0, 0, 0)
        draw.text((x_start + i * cell_w + 30, y_start), d, font=header_font, fill=color)

    x = x_start
    y = y_start + 55
    day = 1

    for week in range(6):
        for wd in range(7):
            if (week == 0 and wd < start_weekday) or day > days_in_month:
                x += cell_w
                continue

            current_day = datetime.date(today.year, today.month, day)
            is_today = (current_day == today)
            color = (200, 50, 50) if wd == 6 or is_today else (0, 0, 0)

            draw.text((x + 38, y), str(day), font=num_font, fill=color)

            solar_d = Solar(today.year, today.month, day)
            lunar_d = Converter.Solar2Lunar(solar_d)
            lunar_day = f"{lunar_d.day:02d}/{lunar_d.month:02d}"
            draw.text((x + 20, y + 38), lunar_day, font=small_font, fill=(90, 90, 130))

            x += cell_w
            day += 1
        x = x_start
        y += cell_h

    footer = f"Bot by Hoàng Anh Tuấn"
    draw.text((WIDTH//2 - info_font.getlength(footer)//2, HEIGHT - 60),
              footer, font=small_font, fill=(50, 50, 70))

    return save_temp(bg)

def handle_lich_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        user_info = client.fetchUserInfo(author_id)
        author_info = user_info.changed_profiles.get(str(author_id), {}) if user_info and user_info.changed_profiles else {}
        name = author_info.get("zaloName", "Người dùng")
    except:
        name = "Người dùng"

    try:
        img_path = draw_calendar_image(name)
        client.sendLocalImage(img_path, thread_id=thread_id, thread_type=thread_type, ttl=120000)
    except Exception as e:
        msg = f"{name}\n⚠️ Gửi ảnh lịch thất bại.\nLỗi: {e}"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
        ])
        client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=10000)
    finally:
        if 'img_path' in locals() and os.path.exists(img_path):
            os.remove(img_path)

def PTA():
    return {
        "lich": handle_lich_command
    }