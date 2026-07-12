import os
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from zlapi.models import Message, ThreadType

# ================================
# MODULE META
# ================================
des = {
    "version": "1.0.0",
    "author": "ngbao",
    "description": "Lấy thông tin nhóm và trả về dưới dạng ảnh UI đẹp.",
    "power": "Quản trị viên Bot"
}

# ================================
# CONFIG
# ================================
CACHE = "modules/cache/groupinfo"
os.makedirs(CACHE, exist_ok=True)

FONT = "modules/cache/font/BeVietnamPro-Bold.ttf"
WIDTH = 1440

def load_font(size):
    return ImageFont.truetype(FONT, size)


# ================================
# AVATAR BO TRÒN
# ================================
def circle_avatar(url, size=330):
    try:
        img = Image.open(BytesIO(requests.get(url, timeout=5).content)).convert("RGBA")
    except:
        img = Image.new("RGBA", (size, size), (100, 100, 100, 255))

    img = img.resize((size, size))
    
    mask = Image.new("L", (size, size))
    d = ImageDraw.Draw(mask)
    d.ellipse((0, 0, size, size), fill=255)
    img.putalpha(mask)

    return img


# ================================
# RENDER ẢNH THÔNG TIN NHÓM
# ================================
def make_groupinfo_image(group):

    HEIGHT = 950
    img = Image.new("RGBA", (WIDTH, HEIGHT), (15, 18, 28))
    d = ImageDraw.Draw(img)

    # FONT
    f_title = load_font(90)
    f_text = load_font(60)
    f_small = load_font(48)

    # Header đẹp
    d.text((WIDTH // 2 - 330, 60), "THÔNG TIN NHÓM", fill=(0, 200, 255), font=f_title)

    # CARD
    CARD_W, CARD_H = WIDTH - 200, 700
    card = Image.new("RGBA", (CARD_W, CARD_H), (25, 25, 35, 240))
    dc = ImageDraw.Draw(card)
    dc.rounded_rectangle((0, 0, CARD_W, CARD_H), radius=40, outline=(0, 200, 255), width=6)

    # Avatar group
    avatar_url = getattr(group, "avatar", None)
    if avatar_url:
        av = circle_avatar(avatar_url, 300)
        card.alpha_composite(av, (50, 50))

    # Lấy thông tin
    name = getattr(group, "name", "Không tên")
    desc = getattr(group, "desc", "Không có mô tả")
    total = getattr(group, "numberOfMembers", "Không rõ")
    admins = getattr(group, "adminIds", [])
    admin_txt = ", ".join(admins) if admins else "Không rõ"

    # Text
    dc.text((400, 60), f"Tên nhóm: {name}", fill="white", font=f_text)
    dc.text((400, 160), f"Mô tả: {desc}", fill=(220, 220, 220), font=f_small)
    dc.text((400, 270), f"Thành viên: {total}", fill=(0, 200, 255), font=f_text)
    dc.text((400, 380), "Admin:", fill=(255, 200, 0), font=f_text)
    dc.text((400, 470), admin_txt, fill="white", font=f_small)

    img.alpha_composite(card, (100, 200))

    # PATH
    path = os.path.join(CACHE, f"groupinfo_{os.urandom(6).hex()}.png")
    img.convert("RGB").save(path, quality=95)
    return path, WIDTH, HEIGHT


# ================================
# COMMAND HANDLER
# ================================
def handle_grifo(message, msg_obj, thread_id, thread_type, author_id, client):

    if thread_type == ThreadType.USER:
        client.replyMessage(
            Message(text="❌ Lệnh này chỉ dùng trong nhóm!"),
            msg_obj, thread_id, thread_type
        )
        return

    try:
        group = client.getGroupInfo(thread_id)

        if not group:
            client.replyMessage(
                Message(text="❌ Không lấy được thông tin nhóm!"),
                msg_obj, thread_id, thread_type
            )
            return

        img_path, W, H = make_groupinfo_image(group)
        client.sendLocalImage(img_path, thread_id, thread_type, width=W, height=H)

        os.remove(img_path)

    except Exception as e:
        client.replyMessage(
            Message(text=f"❌ Lỗi groupinfo: {e}"),
            msg_obj, thread_id, thread_type
        )


# ================================
# REGISTER COMMAND
# ================================
def PTA():
    return {
        "grifo": handle_grifo
    }
