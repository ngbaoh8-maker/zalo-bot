# -*- coding: utf-8 -*-
import os
from datetime import datetime, timedelta, timezone
from zlapi.models import Message
from PIL import Image, ImageDraw, ImageFont
from modules.menu import get_font, get_bg_image, autosave

des = {
    "version": "3.9.6",
    "credits": "ngbao",
    "description": "Time Viet, Han, Anh, My, Nhat",
    "power": "Thành Viên"
}

def draw_time_card(timezones):
    WIDTH, HEIGHT = 1000, 1000
    bg = get_bg_image((WIDTH, HEIGHT)).convert("RGBA")
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0,0,0,120))
    bg.alpha_composite(overlay)
    draw = ImageDraw.Draw(bg)

    font_title = get_font(48)
    font_mid = get_font(36)
    font_small = get_font(28)

    # Tiêu đề
    title = "🌎 Thời gian hiện tại"
    tw, th = draw.textbbox((0,0), title, font=font_title)[2:]
    draw.text(((WIDTH - tw)/2, 30), title, font=font_title, fill=(255,255,255,255))

    # Tính chiều cao khung nhỏ của từng múi giờ
    gap = 40
    khung_heights = []
    khung_infos = []
    x_center = WIDTH // 2

    for tz in timezones:
        label_text = f"{tz['label']} ({tz['tz']})"
        time_text = tz['dt'].strftime("%H:%M:%S | %d/%m/%Y")

        bbox_label = draw.textbbox((0,0), label_text, font=font_mid)
        bbox_time = draw.textbbox((0,0), time_text, font=font_small)
        text_w = max(bbox_label[2]-bbox_label[0], bbox_time[2]-bbox_time[0]) + 40
        text_h = (bbox_label[3]-bbox_label[1]) + (bbox_time[3]-bbox_time[1]) + 40

        khung_heights.append(text_h)
        khung_infos.append((label_text, time_text, text_w, text_h))

    # Tính start_y để căn giữa và nhích lên 50px
    total_height = sum(khung_heights) + gap*(len(timezones)-1)
    start_y = (HEIGHT - total_height) // 2 + 100 - 50  # nhích lên trên 50px

    # Vẽ khung
    for info, kh_h in zip(khung_infos, khung_heights):
        label_text, time_text, text_w, text_h = info
        x0 = x_center - text_w//2
        y0 = start_y
        x1 = x_center + text_w//2
        y1 = start_y + text_h

        # Khung nhỏ
        color_outline = (255, 255, 255, 200)
        draw.rounded_rectangle([x0, y0, x1, y1], radius=20, outline=color_outline, width=3)

        # Viết chữ ở giữa
        label_bbox = draw.textbbox((0,0), label_text, font=font_mid)
        label_x = x_center - (label_bbox[2]-label_bbox[0])//2
        label_y = y0 + 10
        draw.text((label_x, label_y), label_text, font=font_mid, fill=(255,255,200,255))

        time_bbox = draw.textbbox((0,0), time_text, font=font_small)
        time_x = x_center - (time_bbox[2]-time_bbox[0])//2
        time_y = label_y + (label_bbox[3]-label_bbox[1]) + 10
        draw.text((time_x, time_y), time_text, font=font_small, fill=(220,255,220,255))

        start_y = y1 + gap

    # Footer
    footer = "Bot Time By Kim Thanhh"
    fbbox = draw.textbbox((0,0), footer, font=font_small)
    fw = fbbox[2]-fbbox[0]
    draw.text(((WIDTH-fw)/2, HEIGHT-50), footer, font=font_small, fill=(200,200,200,180))

    path = autosave(bg)
    return path

def do_tm(message, message_object, thread_id, thread_type, author_id, client):
    try:
        msg = message.lower().strip()
        args = msg.split()

        vn_tz = timezone(timedelta(hours=7))
        us_tz = timezone(timedelta(hours=-4))
        jp_tz = timezone(timedelta(hours=9))
        uk_tz = timezone(timedelta(hours=0))
        kr_tz = timezone(timedelta(hours=9))

        now_vn = datetime.now(vn_tz)
        now_us = datetime.now(us_tz)
        now_jp = datetime.now(jp_tz)
        now_uk = datetime.now(uk_tz)
        now_kr = datetime.now(kr_tz)

        timezone_map = {
            "việt": {"label":"🇻🇳 Việt Nam", "dt": now_vn, "tz":"UTC+7"},
            "mỹ":   {"label":"🇺🇸 Mỹ (New York)", "dt": now_us, "tz":"UTC-4"},
            "nhật": {"label":"🇯🇵 Nhật Bản (Tokyo)", "dt": now_jp, "tz":"UTC+9"},
            "anh":  {"label":"🇬🇧 Anh (London)", "dt": now_uk, "tz":"UTC+0"},
            "hàn":  {"label":"🇰🇷 Hàn Quốc (Seoul)", "dt": now_kr, "tz":"UTC+9"},
        }

        if len(args) == 1:
            tz_list = [timezone_map["việt"]]
        else:
            key = args[1]
            if key == "all":
                tz_list = list(timezone_map.values())
            else:
                tz = timezone_map.get(key)
                if not tz:
                    client.sendMessage(Message(text="❌ Không nhận diện được múi giờ. Thử: việt, mỹ, nhật, anh, hàn, all"), thread_id, thread_type)
                    return
                tz_list = [tz]

        img_path = draw_time_card(tz_list)
        client.sendLocalImage(img_path, thread_id=thread_id, thread_type=thread_type, ttl=60000)
        try: os.remove(img_path)
        except: pass

    except Exception as e:
        client.sendMessage(Message(text=f"❌ Lỗi khi lấy thời gian: {e}"), thread_id, thread_type)

def PTA():
    return {"tm": do_tm}