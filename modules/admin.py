import json
import os
import time
import requests
from io import BytesIO
from zlapi.models import Message
from PIL import Image, ImageDraw, ImageFont
from config import PREFIX
from config import ADMIN

FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
EMOJI_FONT_PATH = "modules/cache/font/NotoEmoji-Bold.ttf"
CACHE_DIR = "modules/cache/admin_menu_temp"
os.makedirs(CACHE_DIR, exist_ok=True)

des = {
    'version': "1.1.6 (Admin VIP)", # Cập nhật version
    'credits': "ngbao",
    'description': "Quản lý danh sách admin",
    'power': "Quản trị viên Bot"
}

def get_font(size):
    return ImageFont.truetype(FONT_PATH, size)

def get_emoji_font(size):
    return ImageFont.truetype(EMOJI_FONT_PATH, size)

def is_main_admin_only(author_id):
    """Kiểm tra admin (bao gồm admin chính, admin VIP và admin phụ)."""
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'seting.json')
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    admin_main = str(data.get('admin'))
    vip = [str(x) for x in data.get('vip_adm', [])]
    adm_list = [str(x) for x in data.get('adm', [])]
    return str(author_id) in [admin_main] + vip + adm_list

def is_primary_admin(author_id):
    """Admin chính bao gồm: Admin chính thật sự, Admin VIP, và Admin phụ (tất cả đều có quyền như admin chính)"""
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'seting.json')
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Admin chính là: ID chính thức HOẶC ID nằm trong danh sách vip_adm HOẶC admin phụ
    return author_id == data.get('admin') or author_id in data.get('vip_adm', []) or author_id in data.get('adm', [])

def is_secondary_admin(author_id):
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'seting.json')
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return author_id in data.get('adm', [])

def is_admin(author_id):
    return is_primary_admin(author_id) or is_secondary_admin(author_id)

def fetch_avatar(url, size):
    try:
        if url:
            response = requests.get(url, timeout=3)
            img = Image.open(BytesIO(response.content)).convert("RGBA").resize((size, size))
        else:
            raise Exception("No avatar url")
        mask = Image.new('L', (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        img.putalpha(mask)
        return img
    except Exception:
        img = Image.new("RGBA", (size, size), (180, 150, 180, 255))
        mask = Image.new('L', (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        img.putalpha(mask)
        return img

def draw_center_text(draw, text, y, font, emoji_font, img_w, color, shadow=False, x_offset=0):
    import emoji as emoji_mod
    lines = text_wrap(text, font, emoji_font, img_w - 60)
    line_height = font.getbbox("Ay")[3] - font.getbbox("Ay")[1]
    for line in lines:
        width = 0
        for c in line:
            if emoji_mod.emoji_count(c):
                width += emoji_font.getlength(c)
            else:
                width += font.getlength(c)
        x = (img_w - width) // 2 + x_offset
        cur_x = x
        for c in line:
            if emoji_mod.emoji_count(c):
                if shadow:
                    draw.text((cur_x+2, y+2), c, font=emoji_font, fill=(0,0,0,180))
                draw.text((cur_x, y), c, font=emoji_font, fill=color)
                cur_x += emoji_font.getlength(c)
            else:
                if shadow:
                    draw.text((cur_x+2, y+2), c, font=font, fill=(0,0,0,180))
                draw.text((cur_x, y), c, font=font, fill=color)
                cur_x += font.getlength(c)
        y += line_height + 6

def text_wrap(text, font, emoji_font, max_width):
    import emoji as emoji_mod
    lines = []
    line = ""
    for word in text.split():
        test_line = f"{line} {word}".strip()
        w = sum(emoji_font.getlength(ch) if emoji_mod.emoji_count(ch) else font.getlength(ch) for ch in test_line)
        if w > max_width and line:
            lines.append(line)
            line = word
        else:
            line = test_line
    if line:
        lines.append(line)
    return lines

def draw_card_box(draw, x, y, w, h, radius, fill, outline, outline_width):
    draw.rounded_rectangle([x, y, x+w, y+h], radius=radius, fill=fill, outline=outline, width=outline_width)

def calc_card_height(lines, font, emoji_font, w):
    title_h = font.getbbox("Ay")[3] - font.getbbox("Ay")[1] + 32
    line_height = font.getbbox("Ay")[3] - font.getbbox("Ay")[1] + 6
    content_h = 0
    for line in lines:
        wrapped = text_wrap(line, font, emoji_font, w - 38)
        content_h += len(wrapped) * line_height
    y_bot = 28
    return title_h + content_h + y_bot

def draw_menu_card(draw, x, y, w, title, lines, font, emoji_font, color):
    import emoji as emoji_mod
    title = title.strip()
    if title and (emoji_mod.emoji_count(title[0]) or ord(title[0]) > 10000):
        emoji_part = title[0]
        text_part = title[1:].strip()
    else:
        emoji_part = ""
        text_part = title

    card_h = calc_card_height(lines, font, emoji_font, w)
    # Vẽ shadow cho card
    for i in range(6, 0, -1):
        alpha = int(40 * (i / 6))
        draw.rounded_rectangle([x-i, y-i, x+w+i, y+card_h+i], radius=25+i, fill=(0,0,0,alpha), outline=None)
    draw_card_box(draw, x, y, w, card_h, 25, (60,70,120,240), color, 5)
    ty = y+18
    if emoji_part:
        draw.text((x+24, ty), emoji_part, font=emoji_font, fill=(255,230,120))
        draw.text((x+74, ty+5), text_part, font=font, fill=(255,240,180))
    else:
        draw.text((x+24, ty+5), text_part, font=font, fill=(255,240,180))
    content_x = x+38
    y_text = y + font.getbbox("Ay")[3] - font.getbbox("Ay")[1] + 42
    line_height = font.getbbox("Ay")[3] - font.getbbox("Ay")[1] + 6
    for line in lines:
        line_lines = text_wrap(line, font, emoji_font, w-38)
        for l in line_lines:
            cur_x = content_x
            for ch in l:
                if emoji_mod.emoji_count(ch):
                    draw.text((cur_x, y_text), ch, font=emoji_font, fill=(210,255,255))
                    cur_x += emoji_font.getlength(ch)
                else:
                    draw.text((cur_x, y_text), ch, font=font, fill=(210,255,255))
                    cur_x += font.getlength(ch)
            y_text += line_height
    draw.line((x+22, y+card_h-17, x+w-22, y+card_h-17), fill=(130,210,255), width=2)
    return card_h

def draw_admin_list_image(client):
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'seting.json')
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    qtv_bot = data.get('admin')
    qtv_c2 = data.get('adm', [])
    qtv_vip = data.get('vip_adm', []) # Lấy danh sách admin VIP

    admin_users = []
    # Gộp tất cả admin (owner/vip/phụ) và chuẩn hóa nhãn hiển thị
    all_admins = []
    if qtv_bot:
        all_admins.append((qtv_bot, 'owner'))
    for uid in qtv_vip:
        if uid != qtv_bot:
            all_admins.append((uid, 'admin'))
    for uid in qtv_c2:
        if uid != qtv_bot and uid not in qtv_vip:
            all_admins.append((uid, 'admin'))

    for idx, (uid, role_type) in enumerate(all_admins, 1):
        try:
            user_info = client.fetchUserInfo(uid)
            author_info = user_info.changed_profiles.get(uid, {}) if user_info and user_info.changed_profiles else {}
            name = author_info.get('zaloName', 'Không xác định')
            avatar = author_info.get('avatar', None)
        except Exception:
            name = "Không xác định"
            avatar = None
        label = "👑 Admin"
        typ = "admin"
        if role_type == 'owner':
            label = "👑 Admin (Owner)"
            typ = "main"
        admin_users.append((label, name, avatar, uid, typ))

    row_h = 130
    box_w = 980
    margin_top = 100
    margin_left = 85
    extra = 160 if len(admin_users) else 250
    image_width = 1200
    image_height = margin_top + row_h * max(1, len(admin_users)) + extra
    # Gradient background đẹp hơn
    bg = Image.new("RGBA", (image_width, image_height), (25, 20, 50, 255))
    draw = ImageDraw.Draw(bg)
    # Vẽ gradient background
    for i in range(image_height):
        alpha = int(255 * (1 - i / image_height * 0.3))
        color = (25 + int(i * 0.1), 20 + int(i * 0.08), 50 + int(i * 0.15), alpha)
        draw.line([(0, i), (image_width, i)], fill=color, width=1)
    # Vẽ overlay với độ trong suốt
    overlay = Image.new("RGBA", (image_width, image_height), (38, 30, 75, 200))
    bg = Image.alpha_composite(bg, overlay)
    draw = ImageDraw.Draw(bg)
    font = get_font(30)
    emoji_font = get_emoji_font(42)
    id_font = get_font(24)
    # Tiêu đề với hiệu ứng đẹp hơn
    title_y = 35
    draw_center_text(draw, "✨💎 DANH SÁCH ADMIN BOT 💎✨", title_y, get_font(42), emoji_font, image_width, (255,240,200), True, x_offset=0)
    if not admin_users:
        draw_center_text(draw, "Chưa có admin nào cả!", 200, font, emoji_font, image_width, (255,180,180), True)
    for i, (role, name, avatar_url, uid, typ) in enumerate(admin_users):
        y = margin_top + i * row_h
        av = fetch_avatar(avatar_url, 80)
        bg.alpha_composite(av, (margin_left, y + (row_h - 80)//2))
        
        # Vòng viền avatar
        if typ == "main":
            draw.ellipse([margin_left-5, y + (row_h-80)//2 - 5, margin_left + 80 + 5, y + (row_h-80)//2 + 80 + 5], outline=(250,220,90), width=5) # Vàng cho Admin Chính
        elif typ == "vip":
            draw.ellipse([margin_left-5, y + (row_h-80)//2 - 5, margin_left + 80 + 5, y + (row_h-80)//2 + 80 + 5], outline=(255,100,255), width=5) # Tím/Hồng cho VIP
            
        import emoji as emoji_mod
        role_x = margin_left + 100
        role_y = y + 14
        if role and (emoji_mod.emoji_count(role[0]) or ord(role[0]) > 10000):
            draw.text((role_x, role_y), role[0], font=emoji_font, fill=(240,245,180))
            draw.text((role_x + 48, role_y + 5), role[1:], font=font, fill=(240,245,180))
        else:
            draw.text((role_x, role_y + 5), role, font=font, fill=(240,245,180))
        name_show = name if len(name) <= 18 else name[:17] + "…"
        name_y = role_y + 43
        draw.text((role_x, name_y), f"Tên: {name_show}", font=font, fill=(200,255,255))
        id_y = name_y + 34
        draw.text((role_x, id_y), f"ID: {uid}", font=id_font, fill=(180,220,255))
        divider_y = y + row_h - 3
        # Đường kẻ với gradient
        for i in range(3):
            alpha = 200 - i * 50
            draw.line((margin_left+2, divider_y+i, margin_left+box_w-2, divider_y+i), fill=(159,108,255,alpha), width=1)
    # Footer đẹp hơn
    footer_y = image_height - 60
    draw_center_text(draw, "🌟 Muốn vào Admin? Chỉ Admin hiện tại mới có thể chỉ định. 🌟", footer_y, get_font(30), emoji_font, image_width, (255,220,180), True, x_offset=0)
    outname = os.path.join(CACHE_DIR, f"admin_list_{os.getpid()}_{int(time.time())}_{len(admin_users)}.jpg")
    bg = bg.convert("RGB")
    bg.save(outname, "JPEG", quality=100, optimize=True)
    return outname, image_width, image_height

def search_admin_commands(search_term):
    """Tìm kiếm subcommand admin dựa trên chuỗi nhập vào."""
    search_term = search_term.lower()
    commands = [
        ('vip', f'👑 {PREFIX}admin vip @user • Cấp quyền {PREFIX}admin VIP'),
        ('add', f'📋 {PREFIX}admin add @user • Thêm {PREFIX}admin chính'),
        ('remove', f'❌ {PREFIX}admin remove @user • Xóa {PREFIX}admin chính/VIP'),
        ('list', f'✅ {PREFIX}admin list • Xem danh sách {PREFIX}admin bot'),
        ('reset', f'🧹 {PREFIX}admin reset • Reset toàn bộ danh sách {PREFIX}admin (Chỉ Admin)')
    ]
    matched_commands = []
    for cmd, desc in commands:
        if search_term in cmd.lower():
            matched_commands.append((cmd, desc))
    return matched_commands

def show_menu_image(matched_commands=None):
    image_width, image_height = 1200, 950
    margin_x = 60
    # Background gradient đẹp hơn
    bg = Image.new("RGBA", (image_width, image_height), (25, 20, 50, 255))
    draw = ImageDraw.Draw(bg)
    # Vẽ gradient background
    for i in range(image_height):
        alpha = int(255 * (1 - i / image_height * 0.25))
        color = (25 + int(i * 0.12), 20 + int(i * 0.1), 50 + int(i * 0.18), alpha)
        draw.line([(0, i), (image_width, i)], fill=color, width=1)
    # Overlay
    overlay = Image.new("RGBA", (image_width, image_height), (38, 30, 75, 180))
    bg = Image.alpha_composite(bg, overlay)
    draw = ImageDraw.Draw(bg)
    font = get_font(27)
    emoji_font = get_emoji_font(32)
    # Header với hiệu ứng đẹp hơn
    header_y = 25
    header_h = 110
    # Vẽ header với gradient và shadow
    for i in range(8, 0, -2):
        alpha = int(120 * (i / 8))
        draw.rounded_rectangle([margin_x-i, header_y-i, image_width-margin_x+i, header_y+header_h+i], radius=35+i, fill=(159,108,255,alpha), outline=(200,150,255,alpha), width=2)
    draw.rounded_rectangle([margin_x, header_y, image_width-margin_x, header_y+header_h], radius=35, fill=(159,108,255,180), outline=(255,200,255,255), width=3)
    header_text = "✨💎 QUẢN LÝ ADMIN BOT 💎✨"
    draw_center_text(draw, header_text, header_y+35, get_font(40), emoji_font, image_width, (255,240,200), True, x_offset=0)
    color = (159,108,255)
    y = 150
    card_w = image_width-2*margin_x-8

    if matched_commands is None:
        user_lines = [
            f"📋 {PREFIX}admin list • Xem danh sách {PREFIX}admin bot",
            f"👑 {PREFIX}admin vip @user • Cấp quyền {PREFIX}admin VIP",
            f"✅ {PREFIX}admin add @user • Thêm {PREFIX}admin chính",
            f"❌ {PREFIX}admin remove @user • Xóa {PREFIX}admin chính/VIP",
            f"🧹 {PREFIX}admin reset • Reset toàn bộ danh sách {PREFIX}admin (Chỉ Admin)"
        ]
    else:
        user_lines = [desc for _, desc in matched_commands]

    rule_lines = [
        "👑 Tất cả Admin đều có quyền sử dụng toàn bộ lệnh.",
        "⚠️ Tag đúng @user khi thêm/xóa nhé!",
        "🔐 Lệnh reset: Chỉ Admin mới có thể dùng.",
        "🌟 Admin và Admin phụ có quyền như nhau."
    ]
    sys_lines = [
        f"🌐 Phiên bản: {des['version']}",
        f"👤 Tác giả: {des['credits']}",
        f"🔑 Quyền: {des['power']}"
    ]

    # Card với shadow đẹp hơn
    card_spacing = 15
    card_h = draw_menu_card(
        draw, margin_x+3, y, card_w,
        "💠 CÁC LỆNH QUẢN LÝ", user_lines, font, emoji_font, color
    )
    y += card_h + card_spacing
    card_h = draw_menu_card(
        draw, margin_x+3, y, card_w,
        "📜 LƯU Ý / QUY TẮC", rule_lines, font, emoji_font, (255,195,85)
    )
    y += card_h + card_spacing
    card_h = draw_menu_card(
        draw, margin_x+3, y, card_w,
        "🔎 THÔNG TIN", sys_lines, font, emoji_font, (80,210,255)
    )

    # Footer đẹp hơn
    footer_y = image_height - 55
    footer_text = f"🌈 Xem danh sách {PREFIX}admin: {PREFIX}admin list  •  ⚡ Menu: {PREFIX}admin help" if matched_commands is None else f"⚡ Menu: {PREFIX}admin help"
    draw_center_text(
        draw, footer_text, footer_y, font, emoji_font, image_width, (255,235,200), True
    )
    outname = os.path.join(CACHE_DIR, f"admin_menu_{os.getpid()}_{int(time.time())}.jpg")
    bg = bg.convert("RGB")
    bg.save(outname, "JPEG", quality=100, optimize=True)
    return outname

def add_admin(uids, client):
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'seting.json')
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    added_users = []
    
    # Đảm bảo admin chính và admin vip không bị thêm vào admin phụ
    main_admin = data.get('admin')
    vip_adm_list = data.get('vip_adm', [])
    
    for idx, uid in enumerate(uids, 1):
        if uid != main_admin and uid not in vip_adm_list and uid not in data.get('adm', []):
            data.setdefault('adm', []).append(uid)
            try:
                user_info = client.fetchUserInfo(uid)
                author_info = user_info.changed_profiles.get(uid, {}) if user_info and user_info.changed_profiles else {}
                name = author_info.get('zaloName', 'Không xác định')
                added_users.append(f"✅ {idx}. {name} (ID: {uid})")
            except (AttributeError, Exception):
                added_users.append(f"⚠️ {idx}. UID {uid} (Lỗi: Không lấy được thông tin)")
        else:
            if uid == main_admin:
                added_users.append(f"⚠️ {idx}. UID {uid} đã là Admin")
            elif uid in vip_adm_list:
                added_users.append(f"⚠️ {idx}. UID {uid} đã là Admin VIP")
            elif uid in data.get('adm', []):
                added_users.append(f"⚠️ {idx}. UID {uid} đã là ADMIN CHÍNH")
                
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'seting.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    if added_users:
        return (
            "🎯 ĐÃ THÊM ADMIN CHÍNH 🎯\n"
            "━━━━━━━━━━━━━━━\n"
            + "\n".join(added_users) +
            "\n━━━━━━━━━━━━━━━"
        )
    else:
        return (
            "⚠️ Không có admin mới nào được thêm.\n"
            "Hãy kiểm tra lại danh sách @user hoặc thử lại!"
        )

def add_vip_admin(uids, client):
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'seting.json')
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    added_users = []
    
    if 'vip_adm' not in data:
        data['vip_adm'] = []

    # Danh sách để kiểm tra
    main_admin = data.get('admin')
    secondary_adm_list = data.get('adm', [])
    vip_adm_list = data['vip_adm']

    for idx, uid in enumerate(uids, 1):
        if uid != main_admin and uid not in vip_adm_list:
            vip_adm_list.append(uid)
            
            # Xóa khỏi admin phụ nếu họ đang ở đó
            if uid in secondary_adm_list:
                secondary_adm_list.remove(uid)
            
            try:
                user_info = client.fetchUserInfo(uid)
                author_info = user_info.changed_profiles.get(uid, {}) if user_info and user_info.changed_profiles else {}
                name = author_info.get('zaloName', 'Không xác định')
                added_users.append(f"👑 {idx}. {name} (ID: {uid})")
            except (AttributeError, Exception):
                added_users.append(f"⚠️ {idx}. UID {uid} (Lỗi: Không lấy được thông tin)")
        else:
            if uid == main_admin:
                 added_users.append(f"⚠️ {idx}. UID {uid} đã là Admin")
            elif uid in vip_adm_list:
                 added_users.append(f"⚠️ {idx}. UID {uid} đã là ADMIN VIP")

    data['vip_adm'] = vip_adm_list
    data['adm'] = secondary_adm_list # Cập nhật lại list adm
    
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'seting.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
        
    if added_users:
        return (
            "👑 ĐÃ CẤP QUYỀN ADMIN VIP 👑\n"
            "━━━━━━━━━━━━━━━\n"
            + "\n".join(added_users) +
            "\n━━━━━━━━━━━━━━━"
        )
    else:
        return (
            "⚠️ Không có admin VIP mới nào được thêm.\n"
            "Hãy kiểm tra lại danh sách @user hoặc thử lại!"
        )

def remove_admin(uids, client):
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'seting.json')
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    removed_users = []
    
    adm_list = data.get('adm', [])
    vip_adm_list = data.get('vip_adm', [])
    main_admin = data.get('admin')
    
    for idx, uid in enumerate(uids, 1):
        if uid == main_admin:
            removed_users.append(f"🚫 {idx}. KHÔNG THỂ XÓA Admin chính (ID: {uid})")
            continue
            
        was_removed = False
        role_type = ""
        
        # Check VIP list
        if uid in vip_adm_list:
            vip_adm_list.remove(uid)
            role_type = "ADMIN VIP"
            was_removed = True
            
        # Check secondary list
        elif uid in adm_list:
            adm_list.remove(uid)
            role_type = "ADMIN CHÍNH"
            was_removed = True

        if was_removed:
            try:
                user_info = client.fetchUserInfo(uid)
                author_info = user_info.changed_profiles.get(uid, {}) if user_info and user_info.changed_profiles else {}
                name = author_info.get('zaloName', 'Không xác định')
                removed_users.append(f"❌ {idx}. {name} (ID: {uid}) - Đã xóa {role_type}")
            except (AttributeError, Exception):
                removed_users.append(f"⚠️ {idx}. UID {uid} (Lỗi: Không lấy được thông tin) - Đã xóa {role_type}")

    data['adm'] = adm_list
    data['vip_adm'] = vip_adm_list
    
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'seting.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
        
    if removed_users:
        return (
            "🧹 ĐÃ XÓA ADMIN 🧹\n"
            "━━━━━━━━━━━━━━━\n"
            + "\n".join(removed_users) +
            "\n━━━━━━━━━━━━━━━"
        )
    else:
        return (
            "⚠️ Không có admin nào bị xóa.\n"
            "Hãy kiểm tra lại danh sách @user hoặc thử lại!"
        )

def handle_admin_command(message, message_object, thread_id, thread_type, author_id, client):
    if not is_admin(author_id):
        response_message = (
            "🚫 Lệnh này chỉ dành cho Admin! 😤\n"
            "Hãy liên hệ Admin hiện tại để được cấp quyền."
        )
        message_to_send = Message(text=response_message)
        client.replyMessage(message_to_send, message_object, thread_id, thread_type, ttl=60000)
        return

    try:
        if hasattr(message_object, 'text') and isinstance(message_object.text, str):
            message_text = message_object.text
        else:
            message_text = str(message) if message else ""
    except Exception as e:
        print(f"Error extracting message text: {e}")
        response_message = (
            "⚠️ Lỗi khi xử lý lệnh! 😓\n"
            "Hãy thử lại hoặc kiểm tra cú pháp."
        )
        client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=60000)
        return

    text = message_text.split()
    if len(text) < 2 or text[1].lower() in ["help", "menu"]:
        img_path = show_menu_image()
        with Image.open(img_path) as img:
            width, height = img.size
        client.sendLocalImage(
            img_path,
            thread_id=thread_id,
            thread_type=thread_type,
            width=width,
            height=height,
            ttl=120000
        )
        if os.path.exists(img_path):
            os.remove(img_path)
        return

    subcommand = text[1].lower()
    
    # Lệnh ADD admin phụ
    if subcommand == "add" and message_object.mentions:
        # Tất cả admin chính (bao gồm admin phụ) đều có quyền add/remove
        if not is_primary_admin(author_id):
            response_message = (
                "🚫 Chỉ admin chính mới có thể thêm/xóa admin! 😤"
            )
            client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=60000)
            return
            
        uids = [mention['uid'] for mention in message_object.mentions]
        response_message = add_admin(uids, client)
        client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=60000)
    
    # Lệnh VIP admin (bằng admin chính)
    elif subcommand == "vip" and message_object.mentions: 
        if not is_primary_admin(author_id):
            response_message = (
                "🚫 Chỉ admin chính mới có thể cấp quyền Admin VIP! 😤"
            )
            client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=60000)
            return

        uids = [mention['uid'] for mention in message_object.mentions]
        response_message = add_vip_admin(uids, client) # DÙNG HÀM MỚI
        client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=60000)
        
    # Lệnh REMOVE admin phụ/VIP
    elif subcommand == "remove" and message_object.mentions:
        if not is_primary_admin(author_id):
            response_message = (
                "🚫 Chỉ admin chính mới có thể thêm/xóa admin! 😤"
            )
            client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=60000)
            return
            
        uids = [mention['uid'] for mention in message_object.mentions]
        response_message = remove_admin(uids, client)
        client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=60000)
    
    # Lệnh LIST
    elif subcommand == "list":
        img_path, width, height = draw_admin_list_image(client)
        client.sendLocalImage(
            img_path,
            thread_id=thread_id,
            thread_type=thread_type,
            width=width,
            height=height,
            ttl=120000
        )
        if os.path.exists(img_path):
            os.remove(img_path)
            
    # Lệnh RESET
    elif subcommand == "reset":
        # Chỉ admin chính thật sự mới có quyền reset
        if not is_main_admin_only(author_id):
            response_message = (
                "🚫 Chỉ Admin mới có thể reset danh sách admin! 😤"
            )
            client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=60000)
            return

        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'seting.json')
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        data['adm'] = []
        data['vip_adm'] = [] # Xóa cả admin VIP
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

        response_message = (
            "🧹 ĐÃ RESET DANH SÁCH ADMIN 🧹\n"
            "➜   ✅ Tất cả admin chính và admin VIP đã bị xóa.\n"
            "➜   Danh sách admin chính và admin VIP giờ đây rỗng!"
        )
        client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=60000)
        
    # Lệnh không hợp lệ
    else:
        matched_commands = search_admin_commands(subcommand)
        if not matched_commands:
            response_message = (
                f"❌ Không tìm thấy lệnh nào khớp với '{subcommand}'! 😓\n"
                f"Hãy dùng đúng cú pháp: {PREFIX}admin [vip|add|remove|list|reset]\n"
                f"Xem hướng dẫn: {PREFIX}admin help"
            )
            client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=60000)
        else:
            img_path = show_menu_image(matched_commands)
            with Image.open(img_path) as img:
                width, height = img.size
            client.sendLocalImage(
                img_path,
                thread_id=thread_id,
                thread_type=thread_type,
                width=width,
                height=height,
                ttl=120000
            )
            if os.path.exists(img_path):
                os.remove(img_path)

def PTA():
    return {
        'admin': handle_admin_command
    }
