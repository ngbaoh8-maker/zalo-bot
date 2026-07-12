# -*- coding: utf-8 -*-
import os
import importlib
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from zlapi.models import Message
from modules.menu import get_font, get_bg_image, autosave, _smart_resize

des = {
    'version': "1.0.3",
    'credits': "ngbao",
    'description': "Thống kê lệnh quản trị và thành viên bằng hình ảnh.",
    'power': "Thành viên"
}

def draw_tonghop_img(admin_count, member_count, total_modules):
    WIDTH, HEIGHT = 1000, 900
    bg = get_bg_image((WIDTH, HEIGHT)).convert("RGBA")
    overlay = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font_title = get_font(48)
    font_text = get_font(44)
    font_small = get_font(32)

    title = "TỔNG HỢP LỆNH BOT Van Nam"
    draw.text(
        (WIDTH // 2 - font_title.getlength(title) // 2, 100),
        title,
        font=font_title,
        fill=(160, 210, 235, 220),
        stroke_width=3,
        stroke_fill=(0, 0, 0, 160)
    )

    def draw_transparent_card(x, y, w, h):
        # Viền trắng trong suốt mờ nhẹ, không fill
        shadow = Image.new("RGBA", bg.size, (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(shadow)
        for i in range(10, 0, -2):
            alpha = int(22 * i / 10)
            sdraw.rounded_rectangle(
                [x - i, y - i, x + w + i, y + h + i],
                radius=45 + i,
                outline=(255, 255, 255, alpha),
                width=3
            )
        shadow = shadow.filter(ImageFilter.GaussianBlur(3))
        bg.alpha_composite(shadow)

        # Card hoàn toàn trong suốt, chỉ còn viền
        draw.rounded_rectangle(
            [x, y, x + w, y + h],
            radius=50,
            outline=(160, 210, 235, 220),
            width=3,
            fill=None
        )

    infos = [
        ("👑 Quản trị viên Bot", admin_count),
        ("👥 Thành viên", member_count),
        ("🧩 Tổng module", total_modules)
    ]

    card_x = 130
    card_w = 740
    card_h = 150
    y = 250

    for label, val in infos:
        draw_transparent_card(card_x, y, card_w, card_h)
        label_x = card_x + card_w // 2 - font_text.getlength(label) // 2
        draw.text(
            (label_x, y + 20),
            label,
            font=font_text,
            fill=(255, 255, 255, 240),
            stroke_width=2,
            stroke_fill=(0, 0, 0, 150)
        )
        val_str = str(val)
        val_x = card_x + card_w // 2 - font_title.getlength(val_str) // 2
        draw.text(
            (val_x, y + 80),
            val_str,
            font=font_title,
            fill=(255, 255, 255, 255),
            stroke_width=2,
            stroke_fill=(0, 0, 0, 160)
        )
        y += 200

    footer = f"🤖 Bot: Van Nam  •  v1.0.3  •  Tác giả: Dương Văn Nam"
    draw.text(
        (WIDTH // 2 - font_small.getlength(footer) // 2, HEIGHT - 80),
        footer,
        font=font_small,
        fill=(160, 210, 235, 220),
        stroke_width=2,
        stroke_fill=(0, 0, 0, 150)
    )

    bg.alpha_composite(overlay)
    path = autosave(_smart_resize(bg, 960, 960))
    return path

def _tonghop(message, message_object, thread_id, thread_type, author_id, client):
    try:
        admin_count = 0
        member_count = 0
        total_modules = 0
        for module_name in os.listdir('modules'):
            if module_name.endswith('.py') and module_name != '__init__.py':
                try:
                    module = importlib.import_module(f"modules.{module_name[:-3]}")
                    if hasattr(module, 'des'):
                        total_modules += 1
                        power = getattr(module, 'des', {}).get('power', 'Thành viên')
                        if "quản trị viên" in power.lower():
                            admin_count += 1
                        else:
                            member_count += 1
                except Exception as e:
                    print(f"Lỗi load module {module_name}: {e}")
        img_path = draw_tonghop_img(admin_count, member_count, total_modules)
        client.sendLocalImage(img_path, thread_id=thread_id, thread_type=thread_type, ttl=60000)
        os.remove(img_path)
    except Exception as e:
        print("Lỗi trong _tonghop:", e)
        client.replyMessage(Message(text="⚠️ Lỗi khi tạo thống kê!"), message_object, thread_id, thread_type)

def PTA():
    return {'tonghop': _tonghop}