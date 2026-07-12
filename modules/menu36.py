# -*- coding: utf-8 -*-
import os, io, tempfile, random, requests, regex, math
from zlapi.models import Message, ThreadType
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from config import PREFIX

# =============== CẤU HÌNH ===============
FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
EMOJI_FONT_PATH = "modules/cache/font/NotoEmoji-Bold.ttf"
CACHE_DIR = "modules/cache/menu_temp"
BG_DIR = "modules/cache/backgrounds"

os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(BG_DIR, exist_ok=True)

# =============== CÀI ĐẶT PHÂN TRANG ===============
ITEMS_PER_PAGE = 10  # <-- số command hiển thị mỗi trang, đổi tuỳ ý

# =============== MÀU SẮC ===============
BG_FALLBACK_COLOR = (240, 245, 255)
TEXT_COLOR = (20, 25, 35, 255)
CMD_COLOR = (0, 140, 255, 255)
FOOTER_COLOR = (255, 255, 255, 220)
BORDER_COLOR = (0, 160, 255, 255)

# =============== FONT ===============
def get_font(size, is_emoji=False):
    try:
        font_file = EMOJI_FONT_PATH if is_emoji else FONT_PATH
        if not os.path.exists(font_file):
            raise IOError
        return ImageFont.truetype(font_file, size)
    except Exception:
        return ImageFont.load_default()

# =============== WRAP TEXT ===============
def wrap_text(text, font, max_width):
    lines = []
    if not text:
        return lines
    for line in text.split('\n'):
        words = line.split(' ')
        current_line = ""
        for word in words:
            # dùng font.getlength để đo chính xác chiều dài
            if font.getlength(current_line + word + " ") <= max_width:
                current_line += word + " "
            else:
                lines.append(current_line.strip())
                current_line = word + " "
        if current_line:
            lines.append(current_line.strip())
    return lines

# =============== TẢI NGẪU NHIÊN BACKGROUND ===============
def download_random_bg():
    sources = [
        "https://api.waifu.pics/sfw/waifu",
        "https://api.waifu.pics/sfw/neko",
        "https://api.waifu.pics/sfw/marin",
        "https://api.waifu.pics/sfw/shinobu",
        "https://api.waifu.pics/sfw/megumin",
        "https://api.waifu.pics/sfw/maid",
        "https://api.waifu.pics/sfw/smile"
    ]
    try:
        url = random.choice(sources)
        res = requests.get(url, timeout=8).json()
        img_url = res.get("url")
        if img_url:
            img_data = requests.get(img_url, timeout=10).content
            filename = os.path.join(BG_DIR, f"bg_{random.randint(1,99999)}.jpg")
            with open(filename, "wb") as f:
                f.write(img_data)
            return filename
    except Exception as e:
        print(f"⚠️ Không thể tải ảnh nền: {e}")
    return None

# =============== LẤY BACKGROUND ===============
def get_random_background(width, height):
    try:
        imgs = [f for f in os.listdir(BG_DIR) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
        if not imgs:
            path = download_random_bg()
            imgs = [os.path.basename(path)] if path else []
        if not imgs:
            raise FileNotFoundError("Không có ảnh nền khả dụng")

        img_path = os.path.join(BG_DIR, random.choice(imgs))
        bg = Image.open(img_path).convert("RGBA")

        w, h = bg.size
        scale = max(width / w, height / h)
        bg = bg.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        left, top = (bg.width - width) // 2, (bg.height - height) // 2
        return bg.crop((left, top, left + width, top + height))
    except Exception as e:
        print(f"Error background: {e}")
        return Image.new("RGBA", (width, height), BG_FALLBACK_COLOR)

# =============== VẼ MENU ẢNH ===============
def draw_menu_image(commands_list, page=1, total_pages=1):
    WIDTH, HEIGHT = 1080, 1440
    COLS, PADDING = 2, 60
    HEADER_HEIGHT, FOOTER_HEIGHT = 200, 120
    CARD_PADDING, CARD_SPACING, COL_SPACING = 30, 40, 50
    CARD_WIDTH = (WIDTH - PADDING * 2 - COL_SPACING) // COLS

    font_header = get_font(70)
    font_cmd = get_font(32)
    font_desc = get_font(26)
    font_footer = get_font(24)
    emoji_font = get_font(46, is_emoji=True)

    bg = get_random_background(WIDTH, HEIGHT)
    image = bg.copy()
    draw = ImageDraw.Draw(image, "RGBA")

    # Header
    header_text = "✨ MENU LỆNH BOT ✨"
    bbox = draw.textbbox((0, 0), header_text, font=font_header)
    draw.text(((WIDTH - (bbox[2]-bbox[0]))/2, 60), header_text,
              font=font_header, fill=(255,255,255,240),
              stroke_width=2, stroke_fill=(0,0,0,120))

    # Card layout: dùng số items hiện tại để tính rows
    num_cards = len(commands_list)
    rows = math.ceil(num_cards / COLS) if num_cards > 0 else 1
    # chuẩn hóa chiều cao card: tính trung bình rồi dùng cố định cho mọi card trên trang
    sample_heights = []
    for icon, cmd, desc in commands_list:
        lines = wrap_text(desc, font_desc, CARD_WIDTH - CARD_PADDING * 2)
        h = CARD_PADDING * 2 + 60 + len(lines) * 30
        sample_heights.append(h)
    avg_height = int(sum(sample_heights) / len(sample_heights)) if sample_heights else 200
    avg_height += 8  # thêm chút khoảng trống

    for i, (icon, cmd, desc) in enumerate(commands_list):
        row = i // COLS
        col = i % COLS
        x = PADDING + col * (CARD_WIDTH + COL_SPACING)
        y = HEADER_HEIGHT + row * (avg_height + CARD_SPACING)

        # Khung mờ
        glass = bg.crop((x, y, x+CARD_WIDTH, y+avg_height)).filter(ImageFilter.GaussianBlur(4))
        image.paste(glass, (x, y))
        overlay = Image.new("RGBA", (CARD_WIDTH, avg_height), (255,255,255,35))
        image.paste(overlay, (x,y), overlay)

        # Glow + viền
        glow = Image.new("RGBA", image.size, (0,0,0,0))
        gdraw = ImageDraw.Draw(glow)
        gdraw.rounded_rectangle((x, y, x+CARD_WIDTH, y+avg_height), radius=22, outline=(0,160,255,160), width=8)
        glow = glow.filter(ImageFilter.GaussianBlur(6))
        image.alpha_composite(glow)
        draw.rounded_rectangle((x, y, x+CARD_WIDTH, y+avg_height), radius=22, outline=BORDER_COLOR, width=3)

        # Icon + cmd
        draw.text((x + CARD_PADDING, y + CARD_PADDING - 4), icon, font=emoji_font, fill=TEXT_COLOR)
        draw.text((x + CARD_PADDING + 60, y + CARD_PADDING + 4), cmd, font=font_cmd, fill=CMD_COLOR)

        # Mô tả (wrap)
        text_lines = wrap_text(desc, font_desc, CARD_WIDTH - CARD_PADDING * 2)
        desc_y = y + CARD_PADDING + 60
        for line in text_lines:
            draw.text((x + CARD_PADDING, desc_y), line, font=font_desc, fill=(255,255,255,230))
            desc_y += 30

    # Footer: hiển thị trang hiện tại / tổng trang
    footer_text = f"Trang {page}/{total_pages} • Bot by Khánh Sang"
    bbox = draw.textbbox((0,0), footer_text, font=font_footer)
    draw.text(((WIDTH - (bbox[2]-bbox[0]))/2, HEIGHT - 100), footer_text,
              font=font_footer, fill=FOOTER_COLOR)

    # Lưu tạm và trả đường dẫn
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tf:
        final_img = image.convert("RGB")
        final_img.save(tf.name, "JPEG", quality=96)
        return tf.name, WIDTH, HEIGHT

# =============== LỚP XỬ LÝ ===============
class CmdHandler:
    def __init__(self, client):
        self.client = client

    def handle_menu_command(self, message_text, message_object, thread_id, thread_type, author_id):
        # quyền
        if not self.client.is_admin(author_id, thread_id):
            self.client.replyMessage(Message(text="⛔ Bạn không có quyền dùng lệnh này."),
                                     message_object, thread_id, thread_type)
            return

        # parse args
        parts = message_text.split()
        page = 1
        is_text_mode = False

        for p in parts:
            if p.lower() == "text":
                is_text_mode = True
            elif p.isdigit():
                page = max(1, int(p))

        # toàn bộ danh sách lệnh (ví dụ bạn có 15+)
        commands_list = [
            ("🤖", f"{PREFIX}bot", "Quản lý trạng thái bot (on/off/list/all)."),
            ("🧠", f"{PREFIX}aibot", "Chuyển sang chế độ AI tự động trả lời."),
            ("🛡️", f"{PREFIX}antisp", "Chống spam tin nhắn nhanh."),
            ("📢", f"{PREFIX}antiall", "Chống tag @all hoặc spam tag."),
            ("🔗", f"{PREFIX}antilink", "Chặn gửi link lạ."),
            ("📸", f"{PREFIX}antiphoto", "Chống gửi ảnh."),
            ("🎭", f"{PREFIX}antistk", "Chặn sticker."),
            ("🎙️", f"{PREFIX}voice", "Quản lý voice (lưu, gửi, xóa)."),
            ("💬", f"{PREFIX}chat", "Trò chuyện với bot."),
            ("🎨", f"{PREFIX}menu", "Xem danh sách lệnh."),
            # ví dụ thêm lệnh để kiểm tra: (11..15)
            ("🧾", f"{PREFIX}log", "Xem nhật ký hoạt động của bot."),
            ("🧹", f"{PREFIX}clear", "Xoá tin nhắn theo điều kiện."),
            ("🔒", f"{PREFIX}lock", "Khoá kênh / cuộc trò chuyện."),
            ("🔓", f"{PREFIX}unlock", "Mở khoá kênh / cuộc trò chuyện."),
            ("⚙️", f"{PREFIX}setting", "Cấu hình các tuỳ chọn bot.")
        ]

        total_items = len(commands_list)
        total_pages = math.ceil(total_items / ITEMS_PER_PAGE) if ITEMS_PER_PAGE > 0 else 1
        if page > total_pages:
            page = total_pages

        # slice theo trang
        start = (page - 1) * ITEMS_PER_PAGE
        end = start + ITEMS_PER_PAGE
        page_items = commands_list[start:end]

        # chế độ text (phân trang)
        if is_text_mode:
            text_lines = [f"✨ DANH SÁCH LỆNH BOT (Trang {page}/{total_pages}) ✨\n"]
            for icon, cmd, desc in page_items:
                text_lines.append(f"{icon} {cmd}\n  ➜ {desc}")
            text_lines.append(f"\nDùng: {PREFIX}menu <số_trang> hoặc {PREFIX}menu text <số_trang>")
            msg_text = "\n".join(text_lines)
            self.client.replyMessage(Message(text=msg_text), message_object, thread_id, thread_type)
            return

        # chế độ ảnh: vẽ page_items, truyền tổng trang để footer hiển thị
        try:
            self.client.sendReaction(message_object, "⌛", thread_id, thread_type)
            img_path, w, h = draw_menu_image(page_items, page=page, total_pages=total_pages)
            self.client.sendLocalImage(img_path, thread_id=thread_id, thread_type=thread_type, width=w, height=h)
            self.client.sendReaction(message_object, "✅", thread_id, thread_type)
        except Exception as e:
            print(f"Error creating menu: {e}")
            self.client.replyMessage(Message(text="⚠️ Lỗi khi tạo menu."),
                                     message_object, thread_id, thread_type)

# =============== ĐĂNG KÝ ===============
def PTA():
    return {'menu36': CmdHandler.handle_menu_command}
