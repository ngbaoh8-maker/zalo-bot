import os
import json
import random
import math
import requests
from io import BytesIO
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps
from zlapi.models import *

des = {
    'version': "1.2.0",
    'credits': "Bot System",
    'description': "Tra cứu SĐT Zalo - thiết bị, vị trí, nhà mạng",
    'power': "Thành Viên"
}

# ============ FONT & CACHE ============
FONT_DIR = "modules/cache/font/"
CACHE_DIR = "modules/cache/"

# ============ BẢNG ĐẦU SỐ NHÀ MẠNG VIỆT NAM ============
PHONE_PREFIXES = {
    # Viettel
    "032": ("Viettel", "🟢"), "033": ("Viettel", "🟢"), "034": ("Viettel", "🟢"),
    "035": ("Viettel", "🟢"), "036": ("Viettel", "🟢"), "037": ("Viettel", "🟢"),
    "038": ("Viettel", "🟢"), "039": ("Viettel", "🟢"),
    "086": ("Viettel", "🟢"), "096": ("Viettel", "🟢"), "097": ("Viettel", "🟢"),
    "098": ("Viettel", "🟢"),
    # Mobifone
    "070": ("Mobifone", "🔵"), "076": ("Mobifone", "🔵"), "077": ("Mobifone", "🔵"),
    "078": ("Mobifone", "🔵"), "079": ("Mobifone", "🔵"),
    "089": ("Mobifone", "🔵"), "090": ("Mobifone", "🔵"), "093": ("Mobifone", "🔵"),
    # Vinaphone
    "081": ("Vinaphone", "🟡"), "082": ("Vinaphone", "🟡"), "083": ("Vinaphone", "🟡"),
    "084": ("Vinaphone", "🟡"), "085": ("Vinaphone", "🟡"),
    "088": ("Vinaphone", "🟡"), "091": ("Vinaphone", "🟡"), "094": ("Vinaphone", "🟡"),
    # Vietnamobile
    "052": ("Vietnamobile", "🟠"), "056": ("Vietnamobile", "🟠"), "058": ("Vietnamobile", "🟠"),
    "092": ("Vietnamobile", "🟠"),
    # Gmobile
    "059": ("Gmobile", "⚪"), "099": ("Gmobile", "⚪"),
    # Reddi
    "055": ("Reddi", "🔴"),
    # Itelecom
    "087": ("Itelecom", "🟣"),
}

# ============ BẢNG VÙNG MIỀN THEO ĐẦU SỐ CỐ ĐỊNH (tham khảo) ============
REGION_MAP = {
    # Miền Bắc
    "024": "Hà Nội", "0220": "Hà Nam", "0221": "Hà Nam", "0225": "Hải Phòng",
    "0226": "Hưng Yên", "0228": "Hòa Bình", "0229": "Ninh Bình",
    "0203": "Quảng Ninh", "0204": "Bắc Kạn", "0205": "Sơn La",
    "0206": "Yên Bái", "0207": "Tuyên Quang", "0208": "Vĩnh Phúc",
    "0209": "Lạng Sơn", "0210": "Lào Cai", "0211": "Điện Biên",
    "0212": "Lai Châu", "0213": "Hà Giang", "0214": "Cao Bằng",
    "0215": "Phú Thọ", "0216": "Thái Nguyên", "0219": "Bắc Giang",
    "0220": "Hà Nam", "0221": "Nam Định", "0222": "Thái Bình",
    "0226": "Hưng Yên", "0227": "Hải Dương", "0228": "Hòa Bình",
    "0229": "Ninh Bình", "0230": "Thanh Hóa",
    # Miền Trung
    "0231": "Nghệ An", "0232": "Hà Tĩnh", "0233": "Quảng Bình",
    "0234": "Quảng Trị", "0235": "Huế", "0236": "Đà Nẵng",
    "0237": "Quảng Nam", "0238": "Nghệ An",
    "0255": "Quảng Ngãi", "0256": "Bình Định", "0257": "Phú Yên",
    "0258": "Khánh Hòa", "0259": "Ninh Thuận",
    "0260": "Kon Tum", "0261": "Gia Lai", "0262": "Đắk Lắk",
    "0263": "Đà Lạt/Lâm Đồng", "0269": "Đắk Nông",
    # Miền Nam
    "028": "TP. Hồ Chí Minh", "0270": "Tây Ninh", "0271": "Bình Dương",
    "0272": "Long An", "0273": "Tiền Giang", "0274": "Bình Dương",
    "0275": "Bến Tre", "0276": "Đồng Tháp", "0277": "Vĩnh Long",
    "0251": "Đồng Nai", "0252": "Bà Rịa-Vũng Tàu", "0254": "Bà Rịa-Vũng Tàu",
    "0280": "Sóc Trăng", "0281": "An Giang", "0282": "Kiên Giang",
    "0283": "Cần Thơ", "0284": "Trà Vinh", "0285": "Hậu Giang",
    "0286": "Bạc Liêu", "0290": "Cà Mau", "0291": "Bình Thuận",
    "0252": "Bà Rịa Vũng Tàu",
}


def get_safe_font(font_path, size):
    """Lấy font an toàn."""
    paths_to_try = [
        font_path,
        os.path.join(FONT_DIR, "BeVietnamPro-Bold.ttf"),
        "BeVietnamPro-Bold.ttf",
        "BeVietnamPro-SemiBold.ttf",
    ]
    for p in paths_to_try:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def fetch_image(url):
    if not url:
        return None
    try:
        r = requests.get(url, stream=True, timeout=8)
        r.raise_for_status()
        return Image.open(BytesIO(r.content)).convert("RGBA")
    except Exception:
        return None


def make_circle_avatar(img, size):
    img = img.resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    output.paste(img, (0, 0), mask)
    return output


def format_timestamp(ts, default="Không xác định"):
    if isinstance(ts, (int, float)):
        try:
            if ts > 4_102_444_800_000:
                ts /= 1000
            elif ts < 1_000_000_000 and ts != 0:
                return default
            if ts <= 0:
                return default
            return datetime.fromtimestamp(ts).strftime("%H:%M %d/%m/%Y")
        except (ValueError, OSError):
            return default
    return default


def get_gender_text(gender):
    if gender == 0:
        return "Nam 👨"
    elif gender == 1:
        return "Nữ 👩"
    return "Không xác định"


def get_carrier_info(phone_number):
    """Xác định nhà mạng từ đầu số."""
    clean = phone_number.replace("+84", "0").replace(" ", "").replace("-", "")
    if clean.startswith("84") and not clean.startswith("0"):
        clean = "0" + clean[2:]

    prefix3 = clean[:3]
    info = PHONE_PREFIXES.get(prefix3)
    if info:
        return info[0], info[1]
    return "Không xác định", "❓"


def get_region_from_phone(phone_number):
    """Xác định vùng miền dựa trên SĐT (chỉ áp dụng cho SĐT cố định)."""
    clean = phone_number.replace("+84", "0").replace(" ", "").replace("-", "")
    if clean.startswith("84") and not clean.startswith("0"):
        clean = "0" + clean[2:]

    # Thử match đầu số cố định (4 hoặc 3 ký tự)
    for length in [4, 3]:
        prefix = clean[:length]
        region = REGION_MAP.get(prefix)
        if region:
            return region

    return None


def get_device_status(user):
    """Lấy trạng thái thiết bị đăng nhập chi tiết."""
    devices = []

    is_active_mobile = getattr(user, 'isActive', None) or getattr(user, 'isActiveApp', None)
    is_active_pc = getattr(user, 'isActivePC', None)
    is_active_web = getattr(user, 'isActiveWeb', None)

    if is_active_mobile == 1:
        devices.append({
            "name": "Điện Thoại (Mobile)",
            "icon": "📱",
            "status": "🟢 Online",
            "color": (0, 255, 130, 255)
        })
    else:
        devices.append({
            "name": "Điện Thoại (Mobile)",
            "icon": "📱",
            "status": "⚫ Offline",
            "color": (120, 120, 120, 200)
        })

    if is_active_pc == 1:
        devices.append({
            "name": "Máy Tính (PC/Desktop)",
            "icon": "💻",
            "status": "🟢 Online",
            "color": (100, 180, 255, 255)
        })
    else:
        devices.append({
            "name": "Máy Tính (PC/Desktop)",
            "icon": "💻",
            "status": "⚫ Offline",
            "color": (120, 120, 120, 200)
        })

    if is_active_web == 1:
        devices.append({
            "name": "Trình Duyệt (Web)",
            "icon": "🌐",
            "status": "🟢 Online",
            "color": (255, 200, 50, 255)
        })
    else:
        devices.append({
            "name": "Trình Duyệt (Web)",
            "icon": "🌐",
            "status": "⚫ Offline",
            "color": (120, 120, 120, 200)
        })

    return devices


def get_online_status_text(user):
    is_active_mobile = getattr(user, 'isActive', None) or getattr(user, 'isActiveApp', None)
    is_active_pc = getattr(user, 'isActivePC', None)
    is_active_web = getattr(user, 'isActiveWeb', None)

    if is_active_mobile == 1 or is_active_pc == 1 or is_active_web == 1:
        return "🟢 Đang Online"
    return "🔴 Offline"


# ============ GRADIENT ============
GRADIENT_PALETTES = [
    [(138, 43, 226), (0, 191, 255)],
    [(255, 0, 128), (255, 165, 0)],
    [(0, 206, 209), (148, 0, 211)],
    [(255, 69, 0), (255, 215, 0)],
    [(0, 255, 127), (0, 100, 255)],
    [(255, 20, 147), (138, 43, 226)],
    [(0, 191, 255), (255, 105, 180)],
    [(75, 0, 130), (255, 0, 255)],
]


def create_gradient_bg(width, height, color1, color2):
    img = Image.new("RGBA", (width, height))
    for y in range(height):
        t = y / height
        r = int(color1[0] * (1 - t) + color2[0] * t)
        g = int(color1[1] * (1 - t) + color2[1] * t)
        b = int(color1[2] * (1 - t) + color2[2] * t)
        for x in range(width):
            img.putpixel((x, y), (r, g, b, 255))
    return img


def draw_circle_border(draw, cx, cy, radius, color1, color2, width=3):
    for i in range(360):
        t = i / 360.0
        r = int(color1[0] * (1 - t) + color2[0] * t)
        g = int(color1[1] * (1 - t) + color2[1] * t)
        b = int(color1[2] * (1 - t) + color2[2] * t)
        angle = math.radians(i)
        for w in range(width):
            x = cx + int((radius + w) * math.cos(angle))
            y = cy + int((radius + w) * math.sin(angle))
            try:
                draw.point((x, y), fill=(r, g, b, 255))
            except Exception:
                pass


def create_trasdt_image(user, phone_number, author_name):
    """Tạo ảnh kết quả tra SĐT đẹp mắt - bao gồm thiết bị & vị trí."""
    W, H = 900, 800
    palette = random.choice(GRADIENT_PALETTES)
    c1, c2 = palette

    # === Nền ===
    cover_url = getattr(user, 'cover', None)
    avatar_url = getattr(user, 'avatar', None)

    bg_img = fetch_image(cover_url) or fetch_image(avatar_url)
    if bg_img:
        bg_img = ImageOps.fit(bg_img.convert("RGBA"), (W, H), method=Image.LANCZOS, centering=(0.5, 0.42))
        bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=14))
        enhancer = ImageEnhance.Brightness(bg_img)
        bg_img = enhancer.enhance(0.25)
        bg = bg_img
    else:
        bg = create_gradient_bg(W, H, c1, c2)

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 130))
    bg = Image.alpha_composite(bg, overlay)
    draw = ImageDraw.Draw(bg)

    # === Khung viền ===
    draw.rounded_rectangle([3, 3, W - 3, H - 3], radius=20, outline=(*c1, 200), width=3)
    draw.rounded_rectangle([8, 8, W - 8, H - 8], radius=16, outline=(*c2, 100), width=2)

    # === Fonts ===
    font_title = get_safe_font(os.path.join(FONT_DIR, "BeVietnamPro-Bold.ttf"), 26)
    font_name = get_safe_font(os.path.join(FONT_DIR, "BeVietnamPro-Bold.ttf"), 30)
    font_label = get_safe_font(os.path.join(FONT_DIR, "BeVietnamPro-Bold.ttf"), 17)
    font_value = get_safe_font(os.path.join(FONT_DIR, "BeVietnamPro-Bold.ttf"), 16)
    font_small = get_safe_font(os.path.join(FONT_DIR, "BeVietnamPro-Bold.ttf"), 13)
    font_device = get_safe_font(os.path.join(FONT_DIR, "BeVietnamPro-Bold.ttf"), 15)
    font_section = get_safe_font(os.path.join(FONT_DIR, "BeVietnamPro-Bold.ttf"), 18)

    # ==================== PHẦN 1: HEADER ====================
    title = "🔍 TRA CỨU SỐ ĐIỆN THOẠI ZALO"
    title_bbox = draw.textbbox((0, 0), title, font=font_title)
    title_w = title_bbox[2] - title_bbox[0]
    title_x = (W - title_w) // 2

    draw.text((title_x + 2, 22), title, font=font_title, fill=(0, 0, 0, 150))
    draw.text((title_x, 20), title, font=font_title, fill=(0, 255, 180, 255))

    draw.line([(40, 58), (W - 40, 58)], fill=(*c1, 150), width=2)

    # ==================== PHẦN 2: AVATAR + TÊN ====================
    avatar_size = 100
    avatar_img = fetch_image(avatar_url)
    if avatar_img:
        avatar_circle = make_circle_avatar(avatar_img, avatar_size)
    else:
        avatar_circle = Image.new("RGBA", (avatar_size, avatar_size), (*c1, 255))
        mask = Image.new("L", (avatar_size, avatar_size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, avatar_size, avatar_size), fill=255)
        avatar_circle.putalpha(mask)

    avatar_x = 50
    avatar_y = 75
    bg.paste(avatar_circle, (avatar_x, avatar_y), avatar_circle)

    # Viền avatar
    cx = avatar_x + avatar_size // 2
    cy = avatar_y + avatar_size // 2
    draw_circle_border(draw, cx, cy, avatar_size // 2, c1, c2, width=3)

    # Tên + trạng thái bên phải avatar
    display_name = getattr(user, 'displayName', None) or getattr(user, 'zaloName', None) or "Không xác định"
    name_x = avatar_x + avatar_size + 25
    name_y = avatar_y + 15
    draw.text((name_x + 1, name_y + 1), display_name, font=font_name, fill=(0, 0, 0, 120))
    draw.text((name_x, name_y), display_name, font=font_name, fill=(255, 255, 255, 255))

    # Trạng thái online
    online_status = get_online_status_text(user)
    status_color = (0, 255, 100, 255) if "Online" in online_status else (255, 80, 80, 255)
    draw.text((name_x, name_y + 38), online_status, font=font_label, fill=status_color)

    # Nhà mạng
    carrier_name, carrier_icon = get_carrier_info(phone_number)
    carrier_text = f"{carrier_icon} Nhà mạng: {carrier_name}"
    draw.text((name_x, name_y + 62), carrier_text, font=font_value, fill=(200, 200, 255, 230))

    # ==================== PHẦN 3: THÔNG TIN CƠ BẢN ====================
    section_y = avatar_y + avatar_size + 25
    draw.line([(40, section_y), (W - 40, section_y)], fill=(*c2, 100), width=1)

    info_title = "📋 THÔNG TIN TÀI KHOẢN"
    it_bbox = draw.textbbox((0, 0), info_title, font=font_section)
    it_w = it_bbox[2] - it_bbox[0]
    draw.text(((W - it_w) // 2, section_y + 8), info_title, font=font_section, fill=(255, 220, 100, 255))

    info_start_y = section_y + 38
    left_x = 50
    right_x = W // 2 + 20
    line_h = 36

    user_id = getattr(user, 'userId', None) or getattr(user, 'uid', None) or "Không có"
    gender = getattr(user, 'gender', -1)
    dob = getattr(user, 'dob', None)
    created_ts = getattr(user, 'createdTs', None)
    last_action = getattr(user, 'lastActionTime', None)
    status_text = getattr(user, 'status', None) or "Chưa có tiểu sử"
    biz_pkg = getattr(user, 'bizPkg', None)
    has_business = "Có ✅" if biz_pkg and hasattr(biz_pkg, 'label') and biz_pkg.label else "Không"

    # Xác định vùng miền
    region = get_region_from_phone(phone_number)
    region_text = region if region else "Di động (toàn quốc)"

    info_items_left = [
        ("📞 SĐT:", phone_number),
        ("🆔 User ID:", str(user_id)),
        ("🚻 Giới tính:", get_gender_text(gender)),
        ("🎂 Sinh nhật:", format_timestamp(dob, "Ẩn")),
    ]

    info_items_right = [
        ("📍 Khu vực SĐT:", region_text),
        ("🗓️ Ngày tạo TK:", format_timestamp(created_ts, "Không rõ")),
        ("💡 Lần cuối online:", format_timestamp(last_action)),
        ("💼 Business:", has_business),
    ]

    for i, (label, value) in enumerate(info_items_left):
        y_pos = info_start_y + i * line_h
        draw.text((left_x, y_pos), label, font=font_label, fill=(180, 220, 255, 255))
        draw.text((left_x, y_pos + 17), str(value), font=font_value, fill=(255, 255, 255, 230))

    for i, (label, value) in enumerate(info_items_right):
        y_pos = info_start_y + i * line_h
        draw.text((right_x, y_pos), label, font=font_label, fill=(180, 220, 255, 255))
        draw.text((right_x, y_pos + 17), str(value), font=font_value, fill=(255, 255, 255, 230))

    # ==================== PHẦN 4: THIẾT BỊ ĐĂNG NHẬP ====================
    device_section_y = info_start_y + len(info_items_left) * line_h + 15
    draw.line([(40, device_section_y), (W - 40, device_section_y)], fill=(*c1, 100), width=1)

    device_title = "📡 THIẾT BỊ & VỊ TRÍ ĐĂNG NHẬP"
    dt_bbox = draw.textbbox((0, 0), device_title, font=font_section)
    dt_w = dt_bbox[2] - dt_bbox[0]
    draw.text(((W - dt_w) // 2, device_section_y + 8), device_title, font=font_section, fill=(255, 200, 50, 255))

    devices = get_device_status(user)
    device_start_y = device_section_y + 38

    for i, device in enumerate(devices):
        dy = device_start_y + i * 45

        # Nền card cho mỗi thiết bị
        card_left = 50
        card_right = W - 50
        card_top = dy - 5
        card_bottom = dy + 35

        if "Online" in device["status"]:
            card_bg_color = (0, 255, 100, 20)
            border_color = (*c1, 80)
        else:
            card_bg_color = (100, 100, 100, 15)
            border_color = (100, 100, 100, 40)

        draw.rounded_rectangle(
            [card_left, card_top, card_right, card_bottom],
            radius=10, fill=card_bg_color, outline=border_color, width=1
        )

        # Icon + tên thiết bị
        device_text = f"{device['icon']} {device['name']}"
        draw.text((card_left + 15, dy), device_text, font=font_device, fill=device["color"])

        # Trạng thái
        status_text_device = device["status"]
        st_bbox = draw.textbbox((0, 0), status_text_device, font=font_device)
        st_w = st_bbox[2] - st_bbox[0]
        draw.text((card_right - st_w - 15, dy), status_text_device, font=font_device, fill=device["color"])

        # Dòng phụ - vị trí ước tính
        if "Online" in device["status"]:
            if "Điện Thoại" in device["name"]:
                loc_hint = "📍 Đang hoạt động trên ứng dụng Zalo Mobile"
            elif "Máy Tính" in device["name"]:
                loc_hint = "📍 Đang hoạt động trên Zalo PC/Desktop"
            else:
                loc_hint = "📍 Đang hoạt động trên Zalo Web (trình duyệt)"
            draw.text((card_left + 35, dy + 18), loc_hint, font=font_small, fill=(150, 200, 255, 180))

    # ==================== PHẦN 5: TIỂU SỬ ====================
    bio_section_y = device_start_y + len(devices) * 45 + 10
    draw.line([(40, bio_section_y), (W - 40, bio_section_y)], fill=(*c2, 80), width=1)

    bio_title = "📝 TIỂU SỬ"
    bt_bbox = draw.textbbox((0, 0), bio_title, font=font_section)
    bt_w = bt_bbox[2] - bt_bbox[0]
    draw.text(((W - bt_w) // 2, bio_section_y + 5), bio_title, font=font_section, fill=(200, 255, 200, 255))

    bio_text_full = getattr(user, 'status', None) or "Chưa có tiểu sử"
    if len(bio_text_full) > 80:
        bio_text_full = bio_text_full[:80] + "..."

    bio_bbox = draw.textbbox((0, 0), bio_text_full, font=font_value)
    bio_w = bio_bbox[2] - bio_bbox[0]
    bio_x = (W - bio_w) // 2 if bio_w < (W - 100) else 50
    draw.text((bio_x, bio_section_y + 30), bio_text_full, font=font_value, fill=(220, 220, 240, 220))

    # ==================== FOOTER ====================
    footer_y = H - 30
    time_str = datetime.now().strftime("%H:%M %d/%m/%Y")
    footer_text = f"🕐 {time_str}  |  Tra cứu bởi: {author_name}"
    ft_bbox = draw.textbbox((0, 0), footer_text, font=font_small)
    ft_w = ft_bbox[2] - ft_bbox[0]
    draw.text(((W - ft_w) // 2, footer_y), footer_text, font=font_small, fill=(150, 150, 170, 180))

    # === Lưu ===
    os.makedirs(CACHE_DIR, exist_ok=True)
    out_path = os.path.join(CACHE_DIR, f"trasdt_{random.randint(1000, 9999)}.png")
    bg = bg.convert("RGB")
    bg.save(out_path, quality=95)
    return out_path


def trasdt(message, message_object, thread_id, thread_type, author_id, client):
    """
    Lệnh tra cứu SĐT Zalo.
    Cú pháp: !trasdt <số điện thoại>
    """
    try:
        # Lấy tên người gửi
        try:
            author_info = client.fetchUserInfo(author_id)
            if author_info and hasattr(author_info, "changed_profiles"):
                author_name = author_info.changed_profiles.get(str(author_id), {}).get('zaloName', 'Không xác định')
            else:
                author_name = str(author_id)
        except Exception:
            author_name = str(author_id)

        # Parse SĐT
        parts = message.split()
        if len(parts) < 2:
            client.sendReaction(message_object, "❓", thread_id, thread_type)
            msg = (
                f"➜ {author_name}\n"
                f"❌ Vui lòng nhập số điện thoại!\n"
                f"📌 Cú pháp: trasdt <SĐT>\n"
                f"📌 Ví dụ: trasdt 0912345678"
            )
            styles = MultiMsgStyle([
                MessageStyle(offset=2, length=len(author_name), style="color", color="#DB342E", auto_format=False),
                MessageStyle(offset=2, length=len(author_name), style="bold", size="15", auto_format=False),
            ])
            client.replyMessage(
                Message(text=msg, style=styles),
                message_object, thread_id=thread_id, thread_type=thread_type, ttl=60000
            )
            return

        phone_number = parts[1].strip()

        # Validate SĐT
        clean_phone = phone_number.replace("+84", "0").replace(" ", "").replace("-", "")
        if clean_phone.startswith("84") and not clean_phone.startswith("0"):
            clean_phone = "0" + clean_phone[2:]

        if not clean_phone.isdigit() or len(clean_phone) < 9 or len(clean_phone) > 12:
            client.sendReaction(message_object, "❌", thread_id, thread_type)
            msg = (
                f"➜ {author_name}\n"
                f"❌ Số điện thoại không hợp lệ!\n"
                f"📌 Vui lòng nhập SĐT đúng (VD: 0912345678)"
            )
            styles = MultiMsgStyle([
                MessageStyle(offset=2, length=len(author_name), style="color", color="#DB342E", auto_format=False),
                MessageStyle(offset=2, length=len(author_name), style="bold", size="15", auto_format=False),
            ])
            client.replyMessage(
                Message(text=msg, style=styles),
                message_object, thread_id=thread_id, thread_type=thread_type, ttl=60000
            )
            return

        # Reaction đang xử lý
        client.sendReaction(message_object, "🔍", thread_id, thread_type)

        # Gọi API
        try:
            user_data = client.fetchPhoneNumber(phone_number)
        except Exception as api_err:
            client.sendReaction(message_object, "⚠️", thread_id, thread_type)
            msg = (
                f"➜ {author_name}\n"
                f"⚠️ Không thể tra cứu SĐT này!\n"
                f"📌 SĐT có thể đã ẩn hoặc không tồn tại trên Zalo.\n"
                f"📌 Lỗi: {str(api_err)[:100]}"
            )
            styles = MultiMsgStyle([
                MessageStyle(offset=2, length=len(author_name), style="color", color="#DB342E", auto_format=False),
                MessageStyle(offset=2, length=len(author_name), style="bold", size="15", auto_format=False),
            ])
            client.replyMessage(
                Message(text=msg, style=styles),
                message_object, thread_id=thread_id, thread_type=thread_type, ttl=60000
            )
            return

        if not user_data:
            client.sendReaction(message_object, "❌", thread_id, thread_type)
            msg = (
                f"➜ {author_name}\n"
                f"❌ Không tìm thấy tài khoản Zalo với SĐT: {phone_number}\n"
                f"📌 SĐT có thể đã bị ẩn hoặc chưa đăng ký Zalo."
            )
            styles = MultiMsgStyle([
                MessageStyle(offset=2, length=len(author_name), style="color", color="#DB342E", auto_format=False),
                MessageStyle(offset=2, length=len(author_name), style="bold", size="15", auto_format=False),
            ])
            client.replyMessage(
                Message(text=msg, style=styles),
                message_object, thread_id=thread_id, thread_type=thread_type, ttl=60000
            )
            return

        # Lấy user_id
        user_id = None
        if hasattr(user_data, 'uid'):
            user_id = user_data.uid
        elif isinstance(user_data, dict):
            user_id = user_data.get('uid') or user_data.get('userId')
        if not user_id:
            if hasattr(user_data, 'userId'):
                user_id = user_data.userId
            elif hasattr(user_data, 'changed_profiles') and user_data.changed_profiles:
                user_id = list(user_data.changed_profiles.keys())[0]

        if not user_id:
            client.sendReaction(message_object, "❌", thread_id, thread_type)
            msg = (
                f"➜ {author_name}\n"
                f"❌ Không thể xác định User ID từ SĐT: {phone_number}\n"
                f"📌 SĐT có thể đã bị ẩn."
            )
            styles = MultiMsgStyle([
                MessageStyle(offset=2, length=len(author_name), style="color", color="#DB342E", auto_format=False),
                MessageStyle(offset=2, length=len(author_name), style="bold", size="15", auto_format=False),
            ])
            client.replyMessage(
                Message(text=msg, style=styles),
                message_object, thread_id=thread_id, thread_type=thread_type, ttl=60000
            )
            return

        # Fetch user info đầy đủ (có trạng thái online + thiết bị)
        try:
            user_info = client.fetchUserInfo(user_id)
            if hasattr(user_info, 'changed_profiles') and user_info.changed_profiles:
                user = user_info.changed_profiles.get(str(user_id))
                if not user:
                    first_key = list(user_info.changed_profiles.keys())[0]
                    user = user_info.changed_profiles.get(first_key)
            else:
                user = user_data
        except Exception:
            user = user_data

        if not user:
            user = user_data

        # Tạo ảnh
        image_path = create_trasdt_image(user, phone_number, author_name)

        # Lấy thông tin cho text
        devices = get_device_status(user)
        display_name = getattr(user, 'displayName', None) or getattr(user, 'zaloName', None) or "Không xác định"
        online_status = get_online_status_text(user)
        carrier_name, carrier_icon = get_carrier_info(phone_number)
        region = get_region_from_phone(phone_number)
        region_text = region if region else "Di động (toàn quốc)"

        # Tạo text thiết bị
        devices_text = ""
        for d in devices:
            devices_text += f"   {d['icon']} {d['name']}: {d['status']}\n"

        # Tạo text vị trí đăng nhập
        location_text = ""
        for d in devices:
            if "Online" in d["status"]:
                if "Điện Thoại" in d["name"]:
                    location_text += "   📍 Zalo Mobile App\n"
                elif "Máy Tính" in d["name"]:
                    location_text += "   📍 Zalo PC/Desktop\n"
                elif "Trình Duyệt" in d["name"]:
                    location_text += "   📍 Zalo Web Browser\n"

        if not location_text:
            location_text = "   ⚫ Không đang online trên thiết bị nào\n"

        msg = (
            f"🔍 KẾT QUẢ TRA CỨU SĐT\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📞 SĐT: {phone_number}\n"
            f"👤 Tên: {display_name}\n"
            f"🆔 ID: {getattr(user, 'userId', 'N/A') or getattr(user, 'uid', 'N/A')}\n"
            f"{carrier_icon} Nhà mạng: {carrier_name}\n"
            f"📍 Khu vực SĐT: {region_text}\n"
            f"{online_status}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📡 Thiết bị đăng nhập:\n{devices_text}"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🌐 Vị trí đăng nhập:\n{location_text}"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 Hoạt động cuối: {format_timestamp(getattr(user, 'lastActionTime', None))}\n"
            f"🕐 Tra cứu lúc: {datetime.now().strftime('%H:%M %d/%m/%Y')}\n"
            f"👤 Bởi: {author_name}"
        )

        # Gửi
        client.sendReaction(message_object, "✅", thread_id, thread_type)

        client.sendLocalImage(
            imagePath=image_path,
            thread_id=thread_id,
            thread_type=thread_type,
            message=Message(text=msg),
            width=900,
            height=800,
            ttl=300000
        )

        # Xóa ảnh tạm
        try:
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception:
            pass

    except Exception as e:
        print(f"[TRASDT] Lỗi: {e}")
        import traceback
        traceback.print_exc()
        client.sendReaction(message_object, "⚠️", thread_id, thread_type)
        try:
            msg = f"➜ {author_name}\n⚠️ Đã xảy ra lỗi khi tra cứu: {str(e)[:150]}"
        except Exception:
            msg = f"⚠️ Đã xảy ra lỗi khi tra cứu: {str(e)[:150]}"
        client.replyMessage(
            Message(text=msg),
            message_object, thread_id=thread_id, thread_type=thread_type, ttl=60000
        )


def PTA():
    return {
        'trasdt': trasdt
    }
