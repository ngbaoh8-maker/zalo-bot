import json
import random
import time
import os
import emoji
import requests
from io import BytesIO
from zlapi.models import Message
from PIL import Image, ImageDraw, ImageFont

from config import ADMIN, PREFIX

FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
EMOJI_FONT_PATH = "modules/cache/font/NotoEmoji-Bold.ttf"
CACHE_DIR = "modules/cache/money_menu_temp"
os.makedirs(CACHE_DIR, exist_ok=True)

des = {
    'version': "1.2.0",
    'credits': "ngbao",
    'description': "Quản lý tiền tài khoản.",
    'power': "Quản trị viên Bot"
}

user_cooldowns = {}

def get_font(size):
    return ImageFont.truetype(FONT_PATH, size)

def get_emoji_font(size):
    return ImageFont.truetype(EMOJI_FONT_PATH, size)

def is_admin(author_id):
    return author_id == ADMIN

def load_money_data():
    try:
        with open('modules/cache/money.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_money_data(data):
    with open('modules/cache/money.json', 'w') as f:
        json.dump(data, f, indent=4)

def format_money(amount):
    if amount == 0:
        return "0"  # Explicitly handle zero case
    abs_amt = abs(amount)
    if abs_amt >= 1_000_000_000_000:
        return f"{int(amount/1_000_000_000_000)}BB"
    elif abs_amt >= 1_000_000_000:
        return f"{int(amount/1_000_000_000)}B"
    elif abs_amt >= 1_000_000:
        return f"{int(amount/1_000_000)}M"
    elif abs_amt >= 1_000:
        return f"{int(amount/1_000)}K"
    else:
        return f"{amount}"

def parse_money(amount_str):
    try:
        amount_str = amount_str.lower().strip()
        multiplier = 1
        if amount_str.endswith('k'):
            multiplier = 1_000
            amount_str = amount_str[:-1]
        elif amount_str.endswith('m'):
            multiplier = 1_000_000
            amount_str = amount_str[:-1]
        elif amount_str.endswith('b'):
            multiplier = 1_000_000_000
            amount_str = amount_str[:-1]
        elif amount_str.endswith('bb'):
            multiplier = 1_000_000_000_000
            amount_str = amount_str[:-2]
        
        # Chuyển đổi phần số thành số nguyên
        amount = int(float(amount_str) * multiplier)
        return amount
    except (ValueError, TypeError):
        return None

def get_user_name(client, user_id):
    try:
        user_info = client.fetchUserInfo(user_id)
        profile = user_info.changed_profiles.get(user_id, {})
        return profile.get('zaloName', 'Không xác định')
    except AttributeError:
        return 'Không xác định'

def text_wrap(text, font, emoji_font, max_width):
    lines = []
    line = ""
    for word in text.split():
        test_line = f"{line} {word}".strip()
        w = sum(emoji_font.getlength(ch) if emoji.emoji_count(ch) else font.getlength(ch) for ch in test_line)
        if w > max_width and line:
            lines.append(line)
            line = word
        else:
            line = test_line
    if line:
        lines.append(line)
    return lines

def draw_center_text(draw, text, y, font, emoji_font, img_w, color, shadow=False, x_offset=0):
    lines = text_wrap(text, font, emoji_font, img_w - 60)
    line_height = font.getbbox("Ay")[3] - font.getbbox("Ay")[1]
    for line in lines:
        width = sum(emoji_font.getlength(c) if emoji.emoji_count(c) else font.getlength(c) for c in line)
        x = (img_w - width) // 2 + x_offset
        if shadow:
            draw.text((x+2, y+2), line, font=font, fill=(0,0,0,180))
        draw.text((x, y), line, font=font, fill=color)
        y += line_height + 6

def draw_card_box(draw, x, y, w, h, radius, fill, outline, outline_width):
    draw.rounded_rectangle([x, y, x+w, y+h], radius=radius, fill=fill, outline=outline, width=outline_width)

def calc_card_height(lines, font, emoji_font, w):
    title_h = font.getbbox("Ay")[3] - font.getbbox("Ay")[1] + 30
    line_height = font.getbbox("Ay")[3] - font.getbbox("Ay")[1] + 4
    content_h = 0
    for line in lines:
        wrapped = text_wrap(line, font, emoji_font, w - 38)
        content_h += len(wrapped) * line_height
    y_bot = 28
    return title_h + content_h + y_bot

def draw_menu_card(draw, x, y, w, title, lines, font, emoji_font, color):
    title = title.strip()
    if title and (title[0] in emoji.EMOJI_DATA or ord(title[0]) > 10000):
        emoji_part = title[0]
        text_part = title[1:].strip()
    else:
        emoji_part = ""
        text_part = title

    card_h = calc_card_height(lines, font, emoji_font, w)
    draw_card_box(draw, x, y, w, card_h, 22, (36,60,120,230), color, 4)
    if emoji_part:
        draw.text((x+24, y+18), emoji_part, font=emoji_font, fill=(255,240,90))
        draw.text((x+68, y+18), text_part, font=font, fill=(255,240,90))
    else:
        draw.text((x+24, y+18), title, font=font, fill=(255,240,90))

    content_x = x+38
    y_text = y + font.getbbox("Ay")[3] - font.getbbox("Ay")[1] + 38
    line_height = font.getbbox("Ay")[3] - font.getbbox("Ay")[1] + 4
    for line in lines:
        line_lines = text_wrap(line, font, emoji_font, w-38)
        for l in line_lines:
            draw.text((content_x, y_text), l, font=font, fill=(210,255,255))
            y_text += line_height
    draw.line((x+20, y+card_h-14, x+w-20, y+card_h-14), fill=(130,210,255), width=2)
    return card_h

def fetch_avatar(url, size):
    try:
        response = requests.get(url, timeout=3)
        img = Image.open(BytesIO(response.content)).convert("RGBA").resize((size, size))
        mask = Image.new('L', (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        img.putalpha(mask)
        return img
    except Exception:
        img = Image.new("RGBA", (size, size), (120, 130, 150, 255))
        mask = Image.new('L', (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        img.putalpha(mask)
        return img

def draw_avatar_row(bg, draw, x, y, avatar_url, name, amount, rank, font, emoji_font, avatar_size=80, row_h=110, box_w=960):
    av = fetch_avatar(avatar_url, avatar_size)
    bg.alpha_composite(av, (x, y + (row_h - avatar_size)//2))
    if rank == 1:
        draw.ellipse([x-5, y + (row_h-avatar_size)//2 - 5, x + avatar_size + 5, y + (row_h-avatar_size)//2 + avatar_size + 5], outline=(255,210,20), width=4)
    medal_x = x + avatar_size + 24
    medal_y = y + row_h//2 - 47
    if rank == 1:
        medal = "🥇"
    elif rank == 2:
        medal = "🥈"
    elif rank == 3:
        medal = "🥉"
    else:
        medal = f"#{rank}"
    draw.text((medal_x, medal_y), str(medal), font=emoji_font, fill=(255,230,120))
    name_show = name if len(name) <= 17 else name[:16] + "…"
    name_x = medal_x + 58
    name_y = y + row_h//2 - 16
    draw.text((name_x, name_y), name_show, font=font, fill=(220,255,255))
    amt = f"{format_money(amount)}"
    amt_font = get_font(30)
    amt_w = amt_font.getlength(amt)
    amt_x = x + box_w - amt_w - 32
    amt_y = y + row_h//2 - 20
    amt_fill = (255,255,180) if rank == 1 else (180,255,180)
    draw.text((amt_x, amt_y), amt, font=amt_font, fill=amt_fill)
    draw.line((x, y+row_h-10, x+box_w, y+row_h-10), fill=(90,170,255), width=2)

def draw_money_top_menu(client, thread_id, thread_type, message_object, money_data):
    # Include users with zero balance if fewer than 10 users
    top_users = sorted(money_data.items(), key=lambda x: x[1], reverse=True)
    if not top_users:
        client.replyMessage(Message(text="⚠️ Chưa có ai trong bảng xếp hạng cả!"), message_object, thread_id, thread_type)
        return
    users = []
    for idx, (uid, amount) in enumerate(top_users, 1):
        uinfo = client.fetchUserInfo(uid) or {}
        ud = uinfo.get('changed_profiles', {}).get(uid, {})
        av = ud.get('avatar', None)
        name = ud.get('zaloName', 'Không xác định')
        users.append((av, name, amount, idx))
        if idx >= 10:
            break
    # If fewer than 10 users, pad with placeholder entries
    while len(users) < 10:
        users.append((None, "Không có", 0, len(users) + 1))
    row_h = 110
    box_w = 960
    margin_top = 90
    margin_left = 80
    image_width, image_height = 1150, margin_top + row_h * len(users) + 90
    bg = Image.new("RGBA", (image_width, image_height), (32, 40, 60, 255))
    draw = ImageDraw.Draw(bg)
    font = get_font(28)
    emoji_font = get_emoji_font(38)
    draw_center_text(draw, "🏆 TOP 10 ĐẠI GIA GIÀU NHẤT 🏆", 32, get_font(38), emoji_font, image_width, (255,235,80), True, x_offset=0)
    for i, (av_url, name, amount, rank) in enumerate(users):
        y = margin_top + i * row_h
        draw_avatar_row(bg, draw, margin_left, y, av_url, name, amount, rank, font, emoji_font, avatar_size=80, row_h=row_h, box_w=box_w)
    draw_center_text(draw, "📢 Muốn lên top? Chơi lớn đi nào! 😎", image_height-52, get_font(26), emoji_font, image_width, (180,255,210), True, x_offset=0)
    outname = os.path.join(CACHE_DIR, f"money_top_{time.time()}_{random.randint(1000,9999)}.jpg")
    bg = bg.convert("RGB")
    bg.save(outname, "JPEG", quality=100, optimize=True)
    with Image.open(outname) as img:
        width, height = img.size
    client.sendLocalImage(
        outname,
        thread_id=thread_id,
        thread_type=thread_type,
        width=width,
        height=height,
        ttl=120000
    )
    if os.path.exists(outname): os.remove(outname)

def show_menu_image():
    image_width, image_height = 1100, 880
    margin_x = 55
    bg = Image.new("RGBA", (image_width, image_height), (24, 36, 58, 255))
    draw = ImageDraw.Draw(bg)
    font = get_font(25)
    emoji_font = get_emoji_font(28)
    draw.rounded_rectangle([margin_x, 22, image_width-margin_x, 100], radius=30, fill=(110,180,255,110))
    header_text = "💰 MENU QUẢN LÝ TIỀN BOT 💰"
    draw_center_text(draw, header_text, 40, get_font(36), emoji_font, image_width, (255,255,255), True, x_offset=20)
    color = (100,255,220)
    y = 120
    card_w = image_width-2*margin_x-6

    user_lines = [
        f"💵 {PREFIX}money daily                 • Nhận tiền miễn phí mỗi 3 phút",
        f"💸 {PREFIX}money pay <số tiền> @user   • Chuyển tiền cho người khác",
        f"👀 {PREFIX}money check                 • Xem số dư bản thân",
        f"👀 {PREFIX}money check @user           • Xem số dư người được tag",
        f"🏆 {PREFIX}money top                   • Xem top 10 đại gia giàu nhất"
    ]
    admin_lines = [
        f"➕ {PREFIX}money set <tiền> @user       • Cộng tiền cho người khác",
        f"➕ {PREFIX}money add <tiền>             • Cộng tiền cho bản thân",
        f"➖ {PREFIX}money remove <tiền/all> [@user] • Trừ tiền bản thân hoặc người được tag",
        f"🧹 {PREFIX}money reset                  • Xóa sạch toàn bộ số dư hệ thống"
    ]
    sys_lines = [
        f"🌐 Phiên bản: {des['version']}",
        f"👤 Tác giả: {des['credits']}",
        f"🔑 Quyền: {des['power']}"
    ]

    card_h = draw_menu_card(
        draw, margin_x+3, y, card_w,
        "👤 LỆNH DÀNH CHO NGƯỜI DÙNG", user_lines, font, emoji_font, color
    )
    y += card_h + 10
    card_h = draw_menu_card(
        draw, margin_x+3, y, card_w,
        "👑 LỆNH DÀNH CHO ADMIN", admin_lines, font, emoji_font, (255,195,85)
    )
    y += card_h + 10
    card_h = draw_menu_card(
        draw, margin_x+3, y, card_w,
        "🔎 THÔNG TIN", sys_lines, font, emoji_font, (80,210,255)
    )

    draw_center_text(
        draw,
        "⚠️ Nhập đúng số tiền và @user để tránh lỗi!",
        image_height-44,
        font, emoji_font, image_width, (255,225,160), True
    )
    outname = os.path.join(CACHE_DIR, f"money_menu_{time.time()}_{random.randint(1000,9999)}.jpg")
    bg = bg.convert("RGB")
    bg.save(outname, "JPEG", quality=100, optimize=True)
    return outname

def handle_money_command(message, message_object, thread_id, thread_type, author_id, client):
    text = message.split()
    money_data = load_money_data()
    action = text[1].lower() if len(text) > 1 else ""
    
    if len(text) < 2 or action in ["help", "menu"]:
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
        client.sendReaction(message_object, "ℹ️", thread_id, thread_type)
        return
    
    if action == "top":
        draw_money_top_menu(client, thread_id, thread_type, message_object, money_data)
        return
    
    response_message = ""
    if action == "set" and is_admin(author_id):
        if len(text) < 3 or len(message_object.mentions) < 1:
            response_message = "❌ Admin ơi, nhập số tiền hợp lệ và tag @user nha!"
        else:
            amount = parse_money(text[2])
            if amount is None:
                response_message = "❌ Admin ơi, số tiền không hợp lệ! Vd: 500K, 1M, 1B, 1BB"
            else:
                target_id = message_object.mentions[0]['uid']
                target_name = get_user_name(client, target_id)
                money_data[target_id] = money_data.get(target_id, 0) + amount
                save_money_data(money_data)
                response_message = f"✅ Đã cộng {format_money(amount)} cho {target_name}."
    
    elif action == "add" and is_admin(author_id):
        if len(text) < 3:
            response_message = "❌ Admin ơi, nhập số tiền hợp lệ nha!"
        else:
            amount = parse_money(text[2])
            if amount is None:
                response_message = "❌ Admin ơi, số tiền không hợp lệ! Vd: 500K, 1M, 1B, 1BB"
            else:
                money_data[author_id] = money_data.get(author_id, 0) + amount
                save_money_data(money_data)
                response_message = f"✅ Admin đã cộng {format_money(amount)} cho bản thân!"
    
    elif action == "reset" and is_admin(author_id):
        try:
            os.remove('modules/cache/money.json')
            response_message = "✅ Đã reset toàn bộ số dư hệ thống!"
        except FileNotFoundError:
            response_message = "✅ Hệ thống đã sạch tiền!"
    
    elif action == "remove" and is_admin(author_id):
        if len(text) < 3:
            response_message = "❌ Admin ơi, nhập số tiền hoặc all, có thể tag @user!"
        else:
            target_id = message_object.mentions[0]['uid'] if len(message_object.mentions) > 0 else author_id
            target_name = get_user_name(client, target_id)
            if text[2].lower() == "all":
                money_data[target_id] = 0
                response_message = f"✅ Đã xóa sạch tiền của {target_name}!"
            else:
                amount = parse_money(text[2])
                if amount is None:
                    response_message = "❌ Admin ơi, số tiền không hợp lệ! Vd: 500K, 1M, 1B, 1BB"
                else:
                    money_data[target_id] = max(0, money_data.get(target_id, 0) - amount)
                    response_message = f"✅ Đã trừ {format_money(amount)} của {target_name}."
            save_money_data(money_data)
    
    elif action == "daily":
        current_time = time.time()
        cooldown_time = 180
        if author_id in user_cooldowns:
            time_since_last_use = current_time - user_cooldowns[author_id]
            if time_since_last_use < cooldown_time:
                remaining_time = cooldown_time - time_since_last_use
                response_message = f"⏳ Vui lòng đợi {int(remaining_time // 60)} phút {int(remaining_time % 60)} giây nữa để nhận tiền free nhé!"
                client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=60000)
                return
        amount = random.randint(10000, 500000)
        money_data[author_id] = money_data.get(author_id, 0) + amount
        user_cooldowns[author_id] = current_time
        save_money_data(money_data)
        response_message = f"🎉 Bạn nhận được {format_money(amount)} miễn phí!"
    
    elif action == "pay":
        if len(text) < 3 or len(message_object.mentions) < 1:
            response_message = "❌ Vui lòng nhập số tiền hợp lệ và tag @user nha!"
        else:
            amount = parse_money(text[2])
            if amount is None:
                response_message = "❌ Số tiền không hợp lệ! Vd: 500K, 1M, 1B, 1BB"
            elif amount <= 0:
                response_message = "❌ Không thể chuyển số tiền âm hoặc bằng 0!"
            else:
                target_id = message_object.mentions[0]['uid']
                target_name = get_user_name(client, target_id)
                if money_data.get(author_id, 0) >= amount:
                    money_data[author_id] -= amount
                    money_data[target_id] = money_data.get(target_id, 0) + amount
                    save_money_data(money_data)
                    response_message = f"✅ Chuyển {format_money(amount)} cho {target_name} thành công!"
                else:
                    response_message = "❌ Số dư không đủ để chuyển!"
    
    elif action == "check":
        if message_object.mentions:
            target_id = message_object.mentions[0]['uid']
            target_name = get_user_name(client, target_id)
            balance = money_data.get(target_id, 0)
            response_message = f"💸 {target_name} hiện có: {format_money(balance)}"
        else:
            balance = money_data.get(author_id, 0)
            response_message = f"💸 Bạn hiện có: {format_money(balance)}"
    
    else:
        response_message = "❌ Lệnh không hợp lệ hoặc bạn không có quyền dùng lệnh này!"
    
    client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=60000)
    client.sendReaction(message_object, "💰", thread_id, thread_type)

def PTA():
    return {
        'money': handle_money_command
    }