# -*- coding: utf-8 -*-
import os
import importlib
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from zlapi.models import Message
from modules.menu import get_font, get_bg_image, autosave, _smart_resize

des = {
    'version': "1.2.1",
    'credits': "ngbao",
    'description': "Liệt kê các lệnh dành cho Quản trị viên Bot.",
    'power': "Thành Viên"
}

def draw_admin_page(page_modules, page_num, total_pages, total_admin):
    WIDTH, HEIGHT = 1100, 1000
    bg = get_bg_image((WIDTH, HEIGHT)).convert("RGBA")
    # Vẽ gradient background đẹp hơn
    gradient_overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(gradient_overlay)
    for i in range(HEIGHT):
        alpha = int(180 * (1 - i / HEIGHT * 0.4))
        color = (25 + int(i * 0.12), 20 + int(i * 0.1), 50 + int(i * 0.18), alpha)
        gdraw.line([(0, i), (WIDTH, i)], fill=color, width=1)
    bg = Image.alpha_composite(bg, gradient_overlay)
    overlay = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font_title = get_font(48)
    font_text = get_font(40)
    font_small = get_font(32)

    # --- Tiêu đề với hiệu ứng đẹp hơn ---
    title = "✨💎 LỆNH DÀNH CHO QUẢN TRỊ VIÊN BOT 💎✨"
    title_y = 80
    # Vẽ shadow cho tiêu đề
    for offset in [(3, 3), (2, 2), (1, 1)]:
        draw.text(
            (WIDTH // 2 - font_title.getlength(title) // 2 + offset[0], title_y + offset[1]),
            title, font=font_title,
            fill=(0, 0, 0, 120),
            stroke_width=2, stroke_fill=(0, 0, 0, 100)
        )
    draw.text(
        (WIDTH // 2 - font_title.getlength(title) // 2, title_y),
        title, font=font_title,
        fill=(255, 240, 200, 255),
        stroke_width=3, stroke_fill=(159, 108, 255, 200)
    )

    # --- Số trang với style đẹp hơn ---
    page_text = f"📄 Trang {page_num}/{total_pages}"
    page_x = WIDTH - font_small.getlength(page_text) - 90
    page_y = 70
    # Vẽ background cho số trang
    page_bg_w = font_small.getlength(page_text) + 30
    page_bg_h = 45
    draw.rounded_rectangle(
        [page_x - 15, page_y - 8, page_x + page_bg_w - 15, page_y + page_bg_h - 8],
        radius=20, fill=(159, 108, 255, 180), outline=(255, 200, 255, 255), width=2
    )
    draw.text(
        (page_x, page_y),
        page_text, font=font_small,
        fill=(255, 240, 200, 255),
        stroke_width=2, stroke_fill=(0, 0, 0, 120)
    )

    # --- Card với shadow và gradient đẹp hơn ---
    card_x, card_y, card_w, card_h = 80, 240, 940, 620
    color_outline = (200, 180, 255, 255)

    # Vẽ shadow nhiều lớp
    shadow = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    for i in range(15, 0, -2):
        alpha = int(50 * (i / 15))
        c = (*color_outline[:3], alpha)
        sdraw.rounded_rectangle(
            [card_x - i, card_y - i, card_x + card_w + i, card_y + card_h + i],
            radius=50 + i, outline=c, width=4
        )
    shadow = shadow.filter(ImageFilter.GaussianBlur(6))
    bg.alpha_composite(shadow)
    
    # Vẽ card với gradient fill
    card_fill = Image.new("RGBA", (card_w, card_h), (60, 50, 100, 220))
    card_fill_draw = ImageDraw.Draw(card_fill)
    for i in range(card_h):
        alpha = int(220 * (1 - i / card_h * 0.2))
        color = (60 + int(i * 0.05), 50 + int(i * 0.04), 100 + int(i * 0.08), alpha)
        card_fill_draw.line([(0, i), (card_w, i)], fill=color, width=1)
    bg.alpha_composite(card_fill, (card_x, card_y))
    
    draw.rounded_rectangle(
        [card_x, card_y, card_x + card_w, card_y + card_h],
        radius=50, outline=color_outline, width=4, fill=None
    )

    # --- Vẽ text 2 cột với style đẹp hơn ---
    line_spacing = 46
    col_width = card_w // 2
    left_x = card_x + 70
    right_x = card_x + col_width + 50
    max_lines_per_col = int(card_h / line_spacing) - 1  # vừa khít khung

    left_list = page_modules[:max_lines_per_col]
    right_list = page_modules[max_lines_per_col:max_lines_per_col * 2]

    text_y = card_y + 50
    for idx, name in enumerate(left_list, 1):
        # Vẽ bullet point với màu gradient
        bullet_color = (255, 220, 150, 255) if idx % 2 == 0 else (200, 255, 255, 255)
        draw.text((left_x, text_y), f"✨ {name}", font=font_text,
                  fill=bullet_color,
                  stroke_width=2, stroke_fill=(0, 0, 0, 150))
        text_y += line_spacing

    text_y = card_y + 50
    for idx, name in enumerate(right_list, max_lines_per_col + 1):
        # Vẽ bullet point với màu gradient
        bullet_color = (255, 220, 150, 255) if idx % 2 == 0 else (200, 255, 255, 255)
        draw.text((right_x, text_y), f"✨ {name}", font=font_text,
                  fill=bullet_color,
                  stroke_width=2, stroke_fill=(0, 0, 0, 150))
        text_y += line_spacing

    # --- Footer + Tổng số lệnh với style đẹp hơn ---
    footer = f"🤖 Bot: Hoàng Anh Tuấn  •  Tác giả: Kim Thanh  •  v1.2.1"
    total_text = f"📊 Tổng số lệnh quản trị viên: {total_admin}"

    footer_y = HEIGHT - 90
    # Vẽ background cho footer
    footer_bg_h = 70
    footer_bg_y = footer_y - 15
    draw.rounded_rectangle(
        [50, footer_bg_y, WIDTH - 50, footer_bg_y + footer_bg_h],
        radius=25, fill=(159, 108, 255, 150), outline=(255, 200, 255, 255), width=2
    )
    
    # Vẽ shadow cho text
    for offset in [(2, 2), (1, 1)]:
        draw.text(
            (WIDTH // 2 - font_small.getlength(footer) // 2 + offset[0], footer_y + offset[1]),
            footer, font=font_small,
            fill=(0, 0, 0, 100),
            stroke_width=1, stroke_fill=(0, 0, 0, 80)
        )
    draw.text(
        (WIDTH // 2 - font_small.getlength(footer) // 2, footer_y),
        footer, font=font_small,
        fill=(255, 240, 200, 255),
        stroke_width=2, stroke_fill=(0, 0, 0, 120)
    )

    total_y = footer_y + 38
    # Vẽ shadow cho total text
    for offset in [(2, 2), (1, 1)]:
        draw.text(
            (WIDTH // 2 - font_small.getlength(total_text) // 2 + offset[0], total_y + offset[1]),
            total_text, font=font_small,
            fill=(0, 0, 0, 100),
            stroke_width=1, stroke_fill=(0, 0, 0, 80)
        )
    draw.text(
        (WIDTH // 2 - font_small.getlength(total_text) // 2, total_y),
        total_text, font=font_small,
        fill=(200, 255, 255, 255),
        stroke_width=2, stroke_fill=(0, 0, 0, 120)
    )

    bg.alpha_composite(overlay)
    path = autosave(_smart_resize(bg, WIDTH, HEIGHT))
    return path


def _lietke_admin(message, message_object, thread_id, thread_type, author_id, client):
    try:
        # --- Lấy danh sách module admin ---
        admin_modules = []
        for module_name in os.listdir('modules'):
            if module_name.endswith('.py') and module_name != '__init__.py':
                try:
                    module = importlib.import_module(f"modules.{module_name[:-3]}")
                    if hasattr(module, 'des'):
                        power = getattr(module, 'des', {}).get('power', 'Thành viên')
                        if "quản trị viên" in power.lower():
                            admin_modules.append(module_name[:-3])
                except Exception as e:
                    print(f"Lỗi load module {module_name}: {e}")

        if not admin_modules:
            client.replyMessage(Message(text="❌ Không có lệnh nào dành cho Quản trị viên Bot."),
                                message_object, thread_id, thread_type)
            return

        # --- Chia trang ---
        per_page = 26  # mỗi trang hiển thị tối đa 26 lệnh (13 trái + 13 phải)
        total_pages = (len(admin_modules) + per_page - 1) // per_page

        # --- Xác định trang cần xem ---
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
        page_modules = admin_modules[start:end]

        img_path = draw_admin_page(page_modules, page, total_pages, len(admin_modules))
        client.sendLocalImage(img_path, thread_id=thread_id, thread_type=thread_type, ttl=60000)
        os.remove(img_path)

    except Exception as e:
        print("Lỗi trong _lietke_admin:", e)
        client.replyMessage(Message(text="⚠️ Lỗi khi liệt kê lệnh quản trị viên."),
                            message_object, thread_id, thread_type)

def PTA():
    return {'lietkeadmin': _lietke_admin}