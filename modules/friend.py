
# -*- coding: utf-8 -*-
import os
import random
from PIL import Image, ImageDraw, ImageFont
from zlapi.models import Message

des = {
    'version': "1.0.3",
    'credits': "ngbao",
    'description': "Hiển thị danh sách bạn bè",
    'power': "Thành viên"
}

# ================= CẤU HÌNH =================
FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
BG_DIR = "modules/cache/backgrounds"
CACHE_DIR = "modules/cache/friends_temp"
os.makedirs(CACHE_DIR, exist_ok=True)

def get_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()

def get_bg_image(size):
    try:
        imgs = [f for f in os.listdir(BG_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if imgs:
            path = os.path.join(BG_DIR, random.choice(imgs))
            return Image.open(path).convert("RGBA").resize(size, Image.LANCZOS)
    except Exception as e:
        print("Lỗi nền:", e)
    return Image.new("RGBA", size, (25, 25, 45, 255))

def autosave(img, quality=95):
    path = os.path.join(CACHE_DIR, f"friends_{random.randint(1000,9999)}.jpg")
    img.convert("RGB").save(path, "JPEG", quality=quality)
    return path

def draw_friend_page(friends, page, total_pages, total_friends):
    WIDTH, HEIGHT = 1000, 1000
    bg = get_bg_image((WIDTH, HEIGHT))
    draw = ImageDraw.Draw(bg)

    font_title = get_font(60)
    font_name = get_font(36)
    font_footer = get_font(30)

    # Tiêu đề
    title = "Danh sách bạn bè"
    draw.text((WIDTH//2 - font_title.getlength(title)//2, 40),
              title, font=font_title, fill=(255,255,255))

    # Bố cục khung
    margin_x, margin_y = 75, 150
    box_w, box_h = 400, 120
    gap_x, gap_y = 50, 25

    for i, friend in enumerate(friends):
        row, col = divmod(i, 2)
        x = margin_x + col*(box_w+gap_x)
        y = margin_y + row*(box_h+gap_y)

        draw.rounded_rectangle(
            (x, y, x+box_w, y+box_h),
            radius=25,
            outline=(255, 255, 255, 180),
            width=3,
            fill=None
        )

        # Tên Zalo
        name = getattr(friend, "name", None) or getattr(friend, "displayName", None) or "Ẩn danh"
        name = str(name).strip()

        draw.text((x + 25, y + 35),
                  f"{i+1}. {name}",
                  fill="white", font=font_name)

    # Footer
    footer = f"Trang {page}/{total_pages}  •  Tổng {total_friends} bạn  •  by Hoàng Anh Tuấn"
    draw.text((WIDTH//2 - font_footer.getlength(footer)//2, 930),
              footer, fill="white", font=font_footer)

    return autosave(bg)

def friend(message, message_object, thread_id, thread_type, author_id, client):
        try:
            friends = client.fetchAllFriends()
            if not friends or len(friends) == 0:
                client.replyMessage(Message(text="⚠️ Không tìm thấy bạn bè nào!"),
                                    message_object, thread_id, thread_type)
                return

            parts = message.split()
            per_page = 10
            total_pages = (len(friends) + per_page - 1) // per_page
            total_friends = len(friends)

            # Xác định trang
            if len(parts) > 1 and parts[1].isdigit():
                page = int(parts[1])
            else:
                page = 1

            if page < 1 or page > total_pages:
                client.replyMessage(
                    Message(text=f"⚠️ Trang {page} không hợp lệ! (1 - {total_pages})"),
                    message_object, thread_id, thread_type
                )
                return

            start = (page - 1) * per_page
            end = start + per_page
            page_friends = friends[start:end]

            img_path = draw_friend_page(page_friends, page, total_pages, total_friends)
            if os.path.exists(img_path):
                client.sendLocalImage(
                    img_path,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    ttl=60000
                )
                os.remove(img_path)

        except Exception as e:
            print("Lỗi danh sách bạn bè:", e)
            client.replyMessage(Message(text=f"⚠️ Lỗi khi xử lý: {e}"),
                                message_object, thread_id, thread_type)

def PTA():
    return {'friend': friend}