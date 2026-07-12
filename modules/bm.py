import os
import io
import uuid
import requests
import logging
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from zlapi.models import Message, ThreadType

# ==============================
# THÔNG TIN MODULE
# ==============================
des = {
    "version": "1.0.1",
    "credits": "ngbao",
    "description": "Tạo ảnh CCCD (mặt trước) từ thông tin người dùng.",
    "power": "admin",
    "update": "15-11-2025"
}

# ==============================
# CẤU HÌNH & ĐƯỜNG DẪN
# ==============================
ASSET_DIR = "assets"
CACHE_CCCD = "modules/cache/cccd"
CACHE_KEEP = "modules/cache/anhcccd"

os.makedirs(CACHE_CCCD, exist_ok=True)
os.makedirs(CACHE_KEEP, exist_ok=True)

TEMPLATE_FRONT = os.path.join(ASSET_DIR, "cccd_mat_truoc.png")
FONT_BOLD = os.path.join(ASSET_DIR, "Roboto-Bold.ttf")
FONT_REGULAR = os.path.join(ASSET_DIR, "Roboto-Regular.ttf")
DEFAULT_AVATAR = os.path.join(ASSET_DIR, "avatar.png")

TEXT_COLOR = (39, 39, 39)

FIELDS = {
    'socccd': {'pos': (906, 1233), 'font': FONT_BOLD, 'size': 61},
    'hovaten': {'pos': (753, 1363), 'font': FONT_REGULAR, 'size': 48},
    'ngaysinh': {'pos': (1187, 1427), 'font': FONT_REGULAR, 'size': 45},
    'gioitinh': {'pos': (1027, 1490), 'font': FONT_REGULAR, 'size': 40},
    'quoctich': {'pos': (1560, 1482), 'font': FONT_REGULAR, 'size': 44},
    'quequan': {'pos': (753, 1605), 'font': FONT_REGULAR, 'size': 44},
    'thuongtru': {'pos': (753, 1700), 'font': FONT_REGULAR, 'size': 44},
    'ngayhethan': {'pos': (523, 1697), 'font': FONT_REGULAR, 'size': 35},
}

AVATAR_POS = (327, 1161)
AVATAR_SIZE = (376, 512)
QR_POS = (1540, 890)
QR_SIZE = (222, 222)

logger = logging.getLogger(__name__)

# ==============================
# HỖ TRỢ: KIỂM TRA NGÀY
# ==============================
def is_valid_date(date_str):
    try:
        datetime.strptime(date_str, "%d/%m/%Y")
        return True
    except ValueError:
        return False

# ==============================
# TẠO ẢNH CCCD
# ==============================
def create_cccd_front(data):
    try:
        template = Image.open(TEMPLATE_FRONT).convert("RGBA")
        draw = ImageDraw.Draw(template)

        avatar_path = data.get("avatar")
        if avatar_path and os.path.exists(avatar_path):
            avatar = Image.open(avatar_path).convert("RGBA").resize(AVATAR_SIZE)
        elif os.path.exists(DEFAULT_AVATAR):
            avatar = Image.open(DEFAULT_AVATAR).convert("RGBA").resize(AVATAR_SIZE)
        else:
            avatar = None
        if avatar:
            template.paste(avatar, AVATAR_POS, avatar)

        # QR code
        qrcode_text = (
            f"{data['socccd']}|{str(uuid.uuid4().int)[:9]}|{data['hovaten']}|"
            f"{data['ngaysinh'].replace('/', '')}|{data['gioitinh']}|"
            f"{data['thuongtru']}|{data['ngayhethan'].replace('/', '')}"
        )
        qr_url = f"https://quickchart.io/qr?text={qrcode_text}&light=0000&ecLevel=H&format=png&size=700"
        qr_resp = requests.get(qr_url, timeout=10)
        qr_img = Image.open(io.BytesIO(qr_resp.content)).convert("RGBA").resize(QR_SIZE)
        template.paste(qr_img, QR_POS, qr_img)

        for key, cfg in FIELDS.items():
            txt = data.get(key, "")
            font = ImageFont.truetype(cfg["font"], cfg["size"])
            draw.text(cfg["pos"], txt, fill=TEXT_COLOR, font=font)

        output = io.BytesIO()
        template.save(output, format="PNG")
        output.seek(0)
        return output
    except Exception as e:
        logger.error(f"[CCCD] Lỗi tạo ảnh: {e}", exc_info=True)
        return None

# ==============================
# XỬ LÝ LỆNH CCCD
# ==============================
def handle_cccd_command(message_text, message_object, thread_id, thread_type, author_id, client):
    # Chỉ nhóm mới dùng được
    if thread_type != ThreadType.GROUP:
        client.replyMessage(Message(text="⚠️ Lệnh này chỉ dùng trong nhóm!"), message_object, thread_id, thread_type, ttl=60000)
        return

    content = message_object.text or ""
    parts = [p.strip() for p in content.split('|')]
    if len(parts) != 8:
        help_text = (
            "❌ Sai cú pháp!\n"
            "➜ Cú pháp: `cccd Họ tên | Ngày sinh | Giới tính | Quốc tịch | Quê quán | Thường trú | Số CCCD | Ngày hết hạn`\n"
            "➜ Ví dụ: cccd Nguyễn Văn A | 01/01/2000 | Nam | VN | Hà Nội | Hà Nội | 123456789 | 01/01/2030"
        )
        client.replyMessage(Message(text=help_text), message_object, thread_id, thread_type, ttl=60000)
        return

    data = {
        "hovaten": parts[0],
        "ngaysinh": parts[1],
        "gioitinh": parts[2],
        "quoctich": parts[3],
        "quequan": parts[4],
        "thuongtru": parts[5],
        "socccd": parts[6],
        "ngayhethan": parts[7],
    }

    # Check ảnh reply
    if not hasattr(message_object, "attachments") or not message_object.attachments:
        client.replyMessage(Message(text="⚠️ Vui lòng gửi kèm ảnh avatar hoặc reply ảnh!"), message_object, thread_id, thread_type, ttl=60000)
        return

    # Lấy ảnh đầu tiên
    file_url = message_object.attachments[0].url
    temp_avatar = os.path.join(CACHE_CCCD, f"avatar_{uuid.uuid4().hex}.png")
    try:
        r = requests.get(file_url, timeout=10)
        with open(temp_avatar, "wb") as f:
            f.write(r.content)
        data["avatar"] = temp_avatar
    except Exception as e:
        client.replyMessage(Message(text=f"❌ Lỗi tải ảnh: {e}"), message_object, thread_id, thread_type, ttl=60000)
        return

    # Tạo ảnh CCCD
    buf = create_cccd_front(data)
    if not buf:
        client.replyMessage(Message(text="❌ Lỗi khi tạo ảnh CCCD."), message_object, thread_id, thread_type, ttl=60000)
        if os.path.exists(temp_avatar):
            os.remove(temp_avatar)
        return

    # Lưu bản chính
    final_path = os.path.join(CACHE_KEEP, f"{data['hovaten'].upper()}.png")
    with open(final_path, "wb") as f:
        f.write(buf.getvalue())

    # Gửi ảnh lên nhóm
    try:
        client.sendFileMessage(thread_id, buf, filename="cccd.png", text=f"✅ CCCD của {data['hovaten']}")
    except Exception as e:
        client.replyMessage(Message(text=f"❌ Lỗi gửi ảnh: {e}"), message_object, thread_id, thread_type, ttl=60000)

    # Dọn tệp tạm
    if os.path.exists(temp_avatar):
        os.remove(temp_avatar)

# ==============================
# ĐĂNG KÝ LỆNH
# ==============================
def PTA():
    return {"cccd": handle_cccd_command}
