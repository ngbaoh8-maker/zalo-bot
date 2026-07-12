# -*- coding: utf-8 -*-
import os
import random
import json
from zlapi.models import *
from PIL import Image
from config import PREFIX

des = {
    'version': "2.3.0",
    'credits': "ngbao",
    'description': "Game quay số Shoppe",
    'power': "Thành viên"
}

# 🪙 Dùng chung hệ thống tiền từ tài xỉu
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

# 🧭 Hướng dẫn
def shoppehelp(message, message_object, thread_id, thread_type, author_id, client):
    try:
       client.sendReaction(message_object, "🛍️" , thread_id, thread_type)
    except:
        pass
    help_path = "Image/shoppe/help.jpg"
    if os.path.exists(help_path):
        msg = Message(text="🛍️ Hướng dẫn chơi Shoppe:")
        img = Image.open(help_path)
        # đảm bảo mode RGB
        if img.mode != "RGB":
            img = img.convert("RGB")
        client.sendLocalImage(
            imagePath=help_path,
            message=msg,
            thread_id=thread_id,
            thread_type=thread_type,
            width=img.width,
            height=img.height,
            ttl=60000
        )
    else:
        client.replyMessage(
            Message(text="❌ Không tìm thấy ảnh hướng dẫn (Image/shoppe/help.jpg)!"),
            message_object, thread_id, thread_type
        )

# 🧩 Ghép 3 ảnh ngang (fix lỗi bị ô đen / cut)
def merge_images(image_paths, output_path):
    """
    - Chuẩn hoá tất cả ảnh về cùng chiều cao (max height) giữ tỉ lệ
    - Chuyển sang RGB nếu cần
    - Ghép ngang sát nhau, lưu ra output_path
    """
    imgs = []
    # load và convert
    for p in image_paths:
        im = Image.open(p)
        if im.mode != "RGB":
            im = im.convert("RGB")
        imgs.append(im)

    # tìm chiều cao lớn nhất
    max_h = max(im.height for im in imgs)

    # resize giữ tỉ lệ theo chiều cao = max_h
    resized = []
    for im in imgs:
        if im.height != max_h:
            # tỉ lệ
            ratio = max_h / im.height
            new_w = int(im.width * ratio)
            im_resized = im.resize((new_w, max_h), Image.LANCZOS)
        else:
            im_resized = im
        resized.append(im_resized)

    total_width = sum(im.width for im in resized)
    # tạo nền trắng (RGB) cùng kích thước
    new_im = Image.new('RGB', (total_width, max_h), (255, 255, 255))

    x_offset = 0
    for im in resized:
        new_im.paste(im, (x_offset, 0))
        x_offset += im.width

    # lưu file
    new_im.save(output_path, quality=95)

# 🎰 Shoppe chính
def handle_shoppe_command(message, message_object, thread_id, thread_type, author_id, client):
    args = message.split()
    money_data = load_money_data()
    user_money = money_data.get(str(author_id), 0)
    folder = "Image/shoppe"

    if len(args) == 1 or args[1].lower() == "help":
        return shoppehelp(message, message_object, thread_id, thread_type, author_id, client)

    # lấy tên người chơi zalo
    try:
        user_info = client.fetchUserInfo(author_id)
        profile = user_info.changed_profiles.get(author_id, {})
        author_name = profile.get('zaloName', 'Người chơi')
    except:
        author_name = "Người chơi"

    # cược
    try:
        bet = int(args[1])
    except:
        client.replyMessage(Message(
            text=f"❌ Sai cú pháp!\n➜ Dùng: {PREFIX}shoppe <số tiền>\nHoặc {PREFIX}shoppe help"),
            message_object, thread_id, thread_type)
        return

    if bet <= 0:
        client.replyMessage(Message(text="❌ Số tiền phải lớn hơn 0!"), message_object, thread_id, thread_type)
        return
    if bet > user_money:
        client.replyMessage(Message(text=f"❌ Bạn không đủ tiền! Số dư: {format_money(user_money)}"),
                            message_object, thread_id, thread_type)
        return

    # ảnh hợp lệ (loại help.jpg)
    images = [os.path.join(folder, img) for img in os.listdir(folder)
              if img.lower().endswith(('.jpg', '.png')) and img.lower() != "help.jpg"]
    if len(images) < 3:
        client.replyMessage(Message(text="❌ Cần ít nhất 3 ảnh trong Image/shoppe/ để quay!"),
                            message_object, thread_id, thread_type)
        return

    # random 3 ảnh
    result_imgs = [random.choice(images) for _ in range(3)]
    result_names = [os.path.splitext(os.path.basename(i))[0] for i in result_imgs]

    # tính kết quả
    if result_names[0] == result_names[1] == result_names[2]:
        reward = bet * 10
        result_text = f"🎉 3 hình giống nhau! Bạn THẮNG {format_money(reward)} 🎉"
    elif (result_names[0] == result_names[1]) or (result_names[1] == result_names[2]) or (result_names[0] == result_names[2]):
        reward = bet * 3
        result_text = f"✨ 2 hình giống nhau! Bạn thắng {format_money(reward)} ✨"
    else:
        reward = -bet
        result_text = f"🔴 Thua rồi! Mất {format_money(bet)}."

    # cập nhật tiền
    money_data[str(author_id)] = user_money + reward
    save_money_data(money_data)

    # ghép ảnh
    merged_path = "modules/shoppe_temp.jpg"
    try:
        merge_images(result_imgs, merged_path)
    except Exception as e:
        # fallback: nếu lỗi merge thì gửi 1 ảnh duy nhất (không chết)
        merged_path = random.choice(result_imgs)

    # tạo khung tin nhắn đẹp
    msg_text = (
        f"🎰 KẾT QUẢ SHOPPE 🎰\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 Người chơi: {author_name}\n"
        f"💸 Cược: {format_money(bet)}\n"
        f"🖼️ Kết quả quay:\n"
        f"   ▫️ {result_names[0]} | {result_names[1]} | {result_names[2]}\n"
        f"🏆 Kết quả: {result_text}\n"
        f"💰 Số dư hiện tại: {format_money(money_data[str(author_id)])}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🔄 Chơi tiếp? Nhập: {PREFIX}shoppe <số tiền>"
    )

    msg = Message(text=msg_text)

    # gửi ảnh với kích thước gốc của merged
    try:
        img = Image.open(merged_path)
        if img.mode != "RGB":
            img = img.convert("RGB")
        client.sendLocalImage(
            imagePath=merged_path,
            message=msg,
            thread_id=thread_id,
            thread_type=thread_type,
            width=img.width,
            height=img.height,
            ttl=60000
        )
    except Exception:
        # nếu gửi có lỗi, gửi message text thay thế
        client.replyMessage(msg, message_object, thread_id, thread_type)

    # xóa file tạm nếu có
    if os.path.exists(merged_path) and merged_path.endswith("_temp.jpg"):
        try:
            os.remove(merged_path)
        except:
            pass

def PTA():
    return {
        'shoppe': handle_shoppe_command,
        'shoppehelp': shoppehelp
    }