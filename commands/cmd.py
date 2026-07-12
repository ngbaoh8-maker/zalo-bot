import os
import requests
import io
import tempfile
import random
import regex
from zlapi.models import Message, ThreadType
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from config import PREFIX
from io import BytesIO

FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
EMOJI_FONT_PATH = "modules/cache/font/NotoEmoji-Bold.ttf"
CACHE_DIR = "modules/cache/menu_temp"
os.makedirs(CACHE_DIR, exist_ok=True)

# ==============================
# LOAD ẢNH TỪ URL
# ==============================
def load_image_from_url(url):
    resp = requests.get(url, timeout=10)
    return Image.open(BytesIO(resp.content)).convert("RGBA")

# ==============================
# FONT
# ==============================
def get_font(size, is_emoji=False):
    font_file = EMOJI_FONT_PATH if is_emoji else FONT_PATH
    try:
        return ImageFont.truetype(font_file, size)
    except:
        return ImageFont.load_default()

# ==============================
# WRAP TEXT
# ==============================
def wrap_text(text, font, max_width):
    lines = []
    if not text:
        return lines
    for line in text.split("\n"):
        words = line.split(" ")
        current = ""
        for w in words:
            if font.getlength(current + w + " ") <= max_width:
                current += w + " "
            else:
                if current:
                    lines.append(current.strip())
                current = w + " "
        if current:
            lines.append(current.strip())
    return lines

# ==============================
# RANDOM BACKGROUND (LINK)
# ==============================
def get_random_background(width, height):
    bg_urls = [
        "https://files.catbox.moe/y5fg9j.jpg",
        "https://files.catbox.moe/t31gfd.jpg",
        "https://files.catbox.moe/77c4by.jpg",
        "https://files.catbox.moe/d7p28q.jpg"
    ]
    try:
        url = random.choice(bg_urls)
        img = load_image_from_url(url).convert("RGBA")
        img = img.resize((width, height), Image.LANCZOS)
        return img
    except:
        return Image.new("RGBA", (width, height), (235, 240, 250))
# ==============================
# ICON LIST ẢNH (XOAY VÒNG)
# ==============================
icon_urls = [
    "https://files.catbox.moe/ijpxb5.jpg",
    "https://files.catbox.moe/1fd4ad.jpg",
    "https://files.catbox.moe/uy8o28.jpg",
    "https://files.catbox.moe/6pvn60.jpg",
    "https://files.catbox.moe/tiwpfk.jpg",
    "https://files.catbox.moe/e99aaq.jpg",
    "https://files.catbox.moe/br526z.jpg",
    "https://files.catbox.moe/pagrpt.jpg"
]

# ==============================
# VẼ MENU
# ==============================
def draw_menu_image(commands_list, page=1):
    WIDTH, HEIGHT = 1080, 1440

    COLS = 2
    PADDING = 50
    HEADER_HEIGHT = 220
    FOOTER_HEIGHT = 100
    CARD_PADDING = 30
    COL_SPACING = 40
    CARD_SPACING = 30

    ICON_SIZE = 58
    CARD_WIDTH = (WIDTH - PADDING * 2 - COL_SPACING) // COLS

    font_header = get_font(72)
    font_cmd = get_font(30)
    font_desc = get_font(24)
    font_footer = get_font(22)

    # Tính chiều cao card trước
    all_card_heights = []
    for _, cmd, desc in commands_list:
        desc_lines = wrap_text(desc, font_desc, CARD_WIDTH - CARD_PADDING * 2)
        card_height = CARD_PADDING * 2 + ICON_SIZE + 10 + len(desc_lines) * 30
        all_card_heights.append(card_height)

    available_height = HEIGHT - HEADER_HEIGHT - FOOTER_HEIGHT

    # Tính số card mỗi trang
    temp_col_heights = [0] * COLS
    items_per_page = 0

    for h in all_card_heights:
        idx = temp_col_heights.index(min(temp_col_heights))
        if temp_col_heights[idx] + h <= available_height:
            temp_col_heights[idx] += h + CARD_SPACING
            items_per_page += 1
        else:
            break

    if items_per_page == 0:
        items_per_page = 1

    total_pages = (len(commands_list) + items_per_page - 1) // items_per_page
    start = (page - 1) * items_per_page
    end = min(len(commands_list), start + items_per_page)

    if start >= len(commands_list):
        return None

    # Load nền random
    bg_image = get_random_background(WIDTH, HEIGHT)
    canvas = bg_image.filter(ImageFilter.GaussianBlur(6))
    draw = ImageDraw.Draw(canvas, "RGBA")

    # Header
    header_text = "MENU LỆNH ADMIN"
    hx = (WIDTH - font_header.getlength(header_text)) // 2
    draw.text(
        (hx, 80),
        header_text,
        font=font_header,
        fill=(255, 255, 255),
        stroke_width=3,
        stroke_fill=(0, 0, 0, 120)
    )

    # Chuẩn bị vẽ card
    col_heights = [HEADER_HEIGHT] * COLS
    col_cards = [[] for _ in range(COLS)]

    for i in range(start, end):
        h = all_card_heights[i]
        idx = col_heights.index(min(col_heights))
        col_cards[idx].append(i)
        col_heights[idx] += h + CARD_SPACING
    # ======================================================
    # RENDER CÁC THẺ LỆNH (CARD)
    # ======================================================
    # ======================================================
    # RENDER CÁC THẺ LỆNH (CARD)
    # ======================================================
    for col_idx in range(COLS):
        current_y = HEADER_HEIGHT

        for card_idx in col_cards[col_idx]:

            icon, cmd, desc = commands_list[card_idx]
            card_h = all_card_heights[card_idx]
            card_x = PADDING + col_idx * (CARD_WIDTH + COL_SPACING)

            # Glass blur background
            glass = bg_image.crop((card_x, current_y, card_x + CARD_WIDTH, current_y + card_h))
            glass = glass.filter(ImageFilter.GaussianBlur(18))
            canvas.paste(glass, (card_x, current_y))

            # Draw card box
            draw.rounded_rectangle(
                (card_x, current_y, card_x + CARD_WIDTH, card_y := current_y + card_h),
                radius=22,
                fill=(255, 255, 255, 55),
                outline=(255, 255, 255, 100),
                width=2
            )

            # ===========================================
            # ICON ẢNH BO TRÒN – KHÔNG VIỀN ĐEN
            # ===========================================
            icon_url = icon_urls[card_idx % len(icon_urls)]
            try:
                icon_img = load_image_from_url(icon_url)
            except:
                icon_img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (200, 200, 200))

            icon_img = icon_img.resize((ICON_SIZE, ICON_SIZE), Image.LANCZOS)

            # Mask bo tròn icon
            mask = Image.new("L", (ICON_SIZE, ICON_SIZE), 0)
            mdraw = ImageDraw.Draw(mask)
            mdraw.ellipse((0, 0, ICON_SIZE, ICON_SIZE), fill=255)

            rounded_icon = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0,0,0,0))
            rounded_icon.paste(icon_img, (0,0), mask)

            canvas.paste(
                rounded_icon,
                (card_x + CARD_PADDING, current_y + CARD_PADDING),
                rounded_icon
            )

            # ===========================================
            # TÊN LỆNH
            # ===========================================
            draw.text(
                (card_x + CARD_PADDING + ICON_SIZE + 16, current_y + CARD_PADDING + 8),
                cmd,
                font=font_cmd,
                fill=(0, 110, 230)
            )

            # ===========================================
            # MÔ TẢ
            # ===========================================
            desc_y = current_y + CARD_PADDING + ICON_SIZE + 10
            desc_lines = wrap_text(desc, font_desc, CARD_WIDTH - CARD_PADDING * 2)

            for line in desc_lines:
                draw.text(
                    (card_x + CARD_PADDING, desc_y),
                    line,
                    font=font_desc,
                    fill=(20, 30, 50)
                )
                desc_y += 30

            current_y += card_h + CARD_SPACING
    # ======================================================
    # FOOTER
    # ======================================================
    footer_text = f"Trang {page}/{total_pages} • Bot by Txh Dz Cte"
    fx = (WIDTH - font_footer.getlength(footer_text)) // 2

    draw.text(
        (fx, HEIGHT - FOOTER_HEIGHT + 30),
        footer_text,
        font=font_footer,
        fill=(200, 210, 230),
        stroke_width=1,
        stroke_fill=(0, 0, 0, 120)
    )

    # ======================================================
    # XUẤT ẢNH
    # ======================================================
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tf:
        final = canvas.convert("RGB")
        final.save(tf.name, "JPEG", quality=95, optimize=True, subsampling=0, dpi=(150,150))
        return tf.name, final.width, final.height



# ===================================================================
# COMMAND HANDLER
# ===================================================================
class CmdHandler:
    def __init__(self, client):
        self.client = client

    def handle_menu_command(self, message_text, message_object, thread_id, thread_type, author_id):

        # Check quyền admin
        if not self.client.is_admin(author_id, thread_id):
            self.client.replyMessage(
                Message(text="Bạn không có quyền sử dụng lệnh này."),
                message_object, thread_id, thread_type
            )
            return

        parts = message_text.split()
        page = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1

        # ==========================
        # DANH SÁCH LỆNH
        # ==========================
        commands_list = [
            ("icon", f"{PREFIX}bot", "Quản lý trạng thái bot (on/off/list/all)."),
            ("icon", f"{PREFIX}aibot", "Chế độ AI tự động trả lời."),
            ("icon", f"{PREFIX}antisp", "Chống spam tin nhắn."),
            ("icon", f"{PREFIX}antigif", "Chống gửi gif."),
            ("icon", f"{PREFIX}antiricon", "Chống spam reaction."),
            ("icon", f"{PREFIX}antiall", "Chống tag @all."),
            ("icon", f"{PREFIX}antitag", "Chống tag member."),
            ("icon", f"{PREFIX}antinude", "Chống gửi ảnh nóng 18+."),
            ("icon", f"{PREFIX}anticard", "Chống gửi card (danh thiếp)."),
            ("icon", f"{PREFIX}antiforward", "Chống chuyển tiếp tin nhắn."),
            ("icon", f"{PREFIX}antilink", "Chống gửi link lạ."),
            ("icon", f"{PREFIX}antiphoto", "Chống gửi ảnh."),
            ("icon", f"{PREFIX}antivideo", "Chống gửi video."),
            ("icon", f"{PREFIX}antifile", "Chống gửi file."),
            ("icon", f"{PREFIX}antistk", "Chống gửi sticker."),
            ("icon", f"{PREFIX}cam", "Bộ lọc ngôn từ thô tục."),
            ("icon", f"{PREFIX}antiundo", "Chống thu hồi tin nhắn."),
            ("icon", f"{PREFIX}antivoice", "Chống gửi voice."),
            ("icon", f"{PREFIX}antireply", "Chống trả lời tin nhắn."),
            ("icon", f"{PREFIX}antiforward", "Chống chuyển tiếp tin nhắn."),
            ("icon", f"{PREFIX}antiqr", "Chống gửi qr."),
            ("icon", f"{PREFIX}whitelist", "Danh sách miễn trừ."),
            ("icon", f"{PREFIX}autoapprv", "Tự động duyệt thành viên."),
            ("icon", f"{PREFIX}lbot", "Khoá bot chỉ cho admin."),
            ("icon", f"{PREFIX}unlbot", "Mở khoá bot."),
            ("icon", f"{PREFIX}bcmd", "Danh sách lệnh bị cấm."),
            ("icon", f"{PREFIX}svc",  "Quản lý voice.")
        ]

        output_path = None

        try:
            self.client.sendReaction(message_object, "⏳", thread_id, thread_type, reactionType=75)

            render = draw_menu_image(commands_list, page)

            if not render:
                self.client.replyMessage(
                    Message(text=f"❌ Trang {page} không có dữ liệu."),
                    message_object, thread_id, thread_type
                )
                return

            output_path, w, h = render

            self.client.sendLocalImage(
                output_path,
                thread_id=thread_id,
                thread_type=thread_type,
                width=w,
                height=h,
                ttl=120000
            )
            self.client.sendReaction(message_object, "✅", thread_id, thread_type, reactionType=75)

        except Exception as e:
            print("Error:", e)
            self.client.replyMessage(
                Message(text="⚠️ Đã xảy ra lỗi khi tạo menu."),
                message_object, thread_id, thread_type
            )
            self.client.sendReaction(message_object, "⚠️", thread_id, thread_type, reactionType=75)

        finally:
            if output_path and os.path.exists(output_path):
                os.remove(output_path)



# ===================================================================
# EXPORT PTA
# ===================================================================
def PTA():
    return {"cmd": CmdHandler}
