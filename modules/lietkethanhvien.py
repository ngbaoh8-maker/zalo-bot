# -*- coding: utf-8 -*-
import os
import importlib
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from zlapi.models import Message
from modules.menu import get_font, get_bg_image, autosave, _smart_resize

des = {
    'version': "1.2.1",
    'credits': "ngbao",
    'description': "Liệt kê các lệnh dành cho Thành viên",
    'power': "Thành Viên"
}

def draw_member_page(page_modules, page_num, total_pages, total_member):
    WIDTH, HEIGHT = 1000, 900
    bg = get_bg_image((WIDTH, HEIGHT)).convert("RGBA")
    overlay = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font_title = get_font(48)
    font_text = get_font(38)
    font_small = get_font(30)

    # --- Tiêu đề ---
    title = "LỆNH DÀNH CHO THÀNH VIÊN"
    draw.text(
        (WIDTH // 2 - font_title.getlength(title) // 2, 100),
        title, font=font_title,
        fill=(255, 255, 255, 235),
        stroke_width=3, stroke_fill=(0, 0, 0, 160)
    )

    # --- Trang ---
    page_text = f"Trang {page_num}/{total_pages}"
    draw.text(
        (WIDTH - font_small.getlength(page_text) - 80, 60),
        page_text, font=font_small,
        fill=(255, 210, 240, 235),
        stroke_width=2, stroke_fill=(0, 0, 0, 160)
    )

    # --- Card ---
    card_x, card_y, card_w, card_h = 100, 220, 800, 560
    color_outline = (200, 220, 255, 255)  # xanh pastel nhẹ cho khác admin

    shadow = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    for i in range(12, 0, -3):
        alpha = int(30 * i / 10)
        c = (*color_outline[:3], alpha)
        sdraw.rounded_rectangle(
            [card_x - i, card_y - i, card_x + card_w + i, card_y + card_h + i],
            radius=45 + i, outline=c, width=5
        )
    shadow = shadow.filter(ImageFilter.GaussianBlur(4))
    bg.alpha_composite(shadow)
    draw.rounded_rectangle(
        [card_x, card_y, card_x + card_w, card_y + card_h],
        radius=50, outline=color_outline, width=3, fill=None
    )

    # --- Vẽ text 2 cột, chống tràn ---
    line_spacing = 42
    col_width = card_w // 2
    left_x = card_x + 60
    right_x = card_x + col_width + 40
    max_lines = int((card_h - 80) / line_spacing)

    mid = (len(page_modules) + 1) // 2
    left_list = page_modules[:mid][:max_lines]
    right_list = page_modules[mid:][:max_lines]

    # Cột trái
    text_y = card_y + 40
    for name in left_list:
        draw.text((left_x, text_y), f"• {name}", font=font_text,
                  fill=(255, 255, 255, 240),
                  stroke_width=2, stroke_fill=(0, 0, 0, 130))
        text_y += line_spacing

    # Cột phải
    text_y = card_y + 40
    for name in right_list:
        draw.text((right_x, text_y), f"• {name}", font=font_text,
                  fill=(255, 255, 255, 240),
                  stroke_width=2, stroke_fill=(0, 0, 0, 130))
        text_y += line_spacing

    # --- Footer + Tổng lệnh ---
    footer = f"🤖 Bot: Hoàng Anh Tuấn  •  Tác giả: Kim Thanh  •  v1.2.1"
    total_text = f"Tổng số lệnh thành viên: {total_member}"

    draw.text(
        (WIDTH // 2 - font_small.getlength(footer) // 2, HEIGHT - 80),
        footer, font=font_small,
        fill=(230, 230, 255, 230),
        stroke_width=2, stroke_fill=(0, 0, 0, 150)
    )

    draw.text(
        (WIDTH // 2 - font_small.getlength(total_text) // 2, HEIGHT - 45),
        total_text, font=font_small,
        fill=(255, 230, 255, 240),
        stroke_width=2, stroke_fill=(0, 0, 0, 150)
    )

    bg.alpha_composite(overlay)
    path = autosave(_smart_resize(bg, WIDTH, HEIGHT))
    return path


def _lietke_member(message, message_object, thread_id, thread_type, author_id, client):
    try:
        # --- Lấy danh sách module Thành viên ---
        member_modules = []
        for module_name in os.listdir('modules'):
            if module_name.endswith('.py') and module_name != '__init__.py':
                try:
                    module = importlib.import_module(f"modules.{module_name[:-3]}")
                    if hasattr(module, 'des'):
                        power = getattr(module, 'des', {}).get('power', 'Thành viên')
                        if "quản trị viên" not in power.lower():
                            member_modules.append(module_name[:-3])
                except Exception as e:
                    print(f"Lỗi load module {module_name}: {e}")

        if not member_modules:
            client.replyMessage(Message(text="❌ Không có lệnh nào dành cho Thành viên."),
                                message_object, thread_id, thread_type)
            return

        # --- Chia trang ---
        per_page = 26
        total_pages = (len(member_modules) + per_page - 1) // per_page

        # --- Xác định trang ---
        args = message.split()
        page = 1
        if len(args) > 1 and args[1].isdigit():
            page = int(args[1])
        if page < 1 or page > total_pages:
            client.replyMessage(Message(text=f"⚠️ Trang không hợp lệ! (1 - {total_pages})"),
                                message_object, thread_id, thread_type)
            return

        start = (page - 1) * per_page
        end = start + per_page
        page_modules = member_modules[start:end]

        img_path = draw_member_page(page_modules, page, total_pages, len(member_modules))
        client.sendLocalImage(img_path, thread_id=thread_id, thread_type=thread_type, ttl=60000)
        os.remove(img_path)

    except Exception as e:
        print("Lỗi trong _lietke_member:", e)
        client.replyMessage(Message(text="⚠️ Lỗi khi liệt kê lệnh thành viên."),
                            message_object, thread_id, thread_type)

def PTA():
    return {'lietkethanhvien': _lietke_member}