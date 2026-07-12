import json
import random
import os
from PIL import Image
from zlapi.models import *
from config import PREFIX

des = {
    'version': "1.0.9",
    'credits': "ngbao",
    'description': "Chơi game Tài Xỉu",
    'power': "Thành viên"
}

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

def parse_bet_amount(text, current_balance):
    text = text.lower().strip()
    if text == "all":
        return current_balance, None
    if text.endswith('%'):
        try:
            percent = float(text[:-1])
            if 1 <= percent <= 100:
                return int(current_balance * (percent / 100)), None
            else:
                return 0, "➜ Phần trăm phải từ 1% đến 100%."
        except ValueError:
            return 0, "➜ Phần trăm không hợp lệ."
    
    multiplier = 1
    if text.endswith('k'):
        multiplier = 1_000
        text = text[:-1]
    elif text.endswith('m'):
        multiplier = 1_000_000
        text = text[:-1]
    elif text.endswith('b'):
        multiplier = 1_000_000_000
        text = text[:-1]
    elif text.endswith('bb'):
        multiplier = 1_000_000_000_000
        text = text[:-2]
    
    try:
        amount = int(float(text) * multiplier)
        if amount <= 0:
            return 0, "➜ Số tiền cược phải lớn hơn 0."
        return amount, None
    except (ValueError, TypeError):
        return 0, "➜ Số tiền không hợp lệ. Ví dụ: 100K, 1M, 1B, 1BB"

def get_user_name(client, user_id):
    try:
        user_info = client.fetchUserInfo(user_id)
        profile = user_info.changed_profiles.get(user_id, {})
        user_name = profile.get('zaloName', 'Không xác định')
    except AttributeError:
        user_name = 'Không xác định'
    return user_name

def merge_images(image_paths, output_path):
    images = [Image.open(img) for img in image_paths]
    total_width = sum(img.width for img in images)
    max_height = max(img.height for img in images)

    new_image = Image.new('RGB', (total_width, max_height))
    x_offset = 0

    for img in images:
        new_image.paste(img, (x_offset, 0))
        x_offset += img.width

    new_image.save(output_path)

def show_menu():
    return (
        "🎲 TRÒ CHƠI TÀI XỈU 🎲\n"
        "━━━━━━━━━━━━━━━\n"
        "📜 Hướng dẫn sử dụng:\n"
        f"   ➜ Cú pháp: {PREFIX}taixiu <tài/xỉu> <số tiền>\n"
        f"   ➜ Ví dụ: {PREFIX}taixiu tài 100K, {PREFIX}taixiu xỉu 1M, {PREFIX}taixiu tài all\n"
        "━━━━━━━━━━━━━━━\n"
        "💰 Cách đặt cược:\n"
        "   ➜ Số tiền: Nhập số (VD: 100K, 1M, 1B, 1BB)\n"
        "   ➜ Phần trăm: Nhập % số dư (VD: 50%)\n"
        "   ➜ Tất cả: Nhập all để cược toàn bộ số dư\n"
        "━━━━━━━━━━━━━━━\n"
        "🎯 Luật chơi:\n"
        "   ➜ 3 xúc xắc, mỗi xúc xắc từ 1-6 điểm\n"
        "   ➜ Tổng điểm 3-10: Xỉu, 11-18: Tài\n"
        "   ➜ Thắng: Nhận x2 tiền cược (x10 nếu 3 xúc xắc giống nhau)\n"
        "   ➜ Thua: Mất tiền cược\n"
        "━━━━━━━━━━━━━━━\n"
        "⚠️ Lưu ý: Đảm bảo số dư đủ để đặt cược!"
    )

def handle_taixiu_command(message, message_object, thread_id, thread_type, author_id, client):
    text = message.split()
    money_data = load_money_data()
    response_message = ""
    data_trave = ""
    dice_values = []

    if len(text) == 1 or text[1].lower() == "help":
        response_message = show_menu()
    elif len(text) != 3 or text[1].lower() not in ["tài", "xỉu"]:
        response_message = (
            "❌ Lệnh không hợp lệ!\n"
            f"   ➜ Vui lòng sử dụng: {PREFIX}taixiu <tài/xỉu> <số tiền>\n"
            f"   ➜ Xem hướng dẫn: {PREFIX}taixiu help"
        )
    else:
        choice = text[1].lower()
        current_balance = money_data.get(str(author_id), 0)
        bet_amount, error = parse_bet_amount(text[2], current_balance)
        if error:
            response_message = f"❌ Lỗi: {error}"
        else:
            if bet_amount > current_balance:
                response_message = f"❌ Lỗi: Số dư của bạn không đủ để đặt cược {format_money(bet_amount)}."
            elif bet_amount <= 0:
                response_message = "❌ Lỗi: Số tiền cược phải lớn hơn 0."
            else:
                dice_values = [random.randint(1, 6) for _ in range(3)]
                total_points = sum(dice_values)
                result = "xỉu" if 3 <= total_points <= 10 else "tài"
                outcome = "thắng" if choice == result else "thua"
                
                total_received = 0
                if outcome == "thắng":
                    multiplier = 2
                    if dice_values.count(dice_values[0]) == 3:
                        multiplier = 10
                    total_received = bet_amount * multiplier
                    response = f"🟢 Nhận: {format_money(total_received)}\nĐã cộng {format_money(total_received)} vào tài khoản."
                else:
                    response = f"🔴 Mất: {format_money(bet_amount)}\nĐã trừ {format_money(bet_amount)} khỏi tài khoản."

                money_data[str(author_id)] = current_balance + total_received - bet_amount
                save_money_data(money_data)
                author_name = get_user_name(client, author_id)

                data_trave = (
                    f"   🎮 KẾT QUẢ TÀI XỈU 🎮\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"   👤 Người chơi: {author_name}\n"
                    f"   💸 Cược: {format_money(bet_amount)} vào {choice.capitalize()}\n"
                    f"   🎲 Kết quả xúc xắc:\n"
                    f"   🎲 Xúc xắc 1: {dice_values[0]}\n"
                    f"   🎲 Xúc xắc 2: {dice_values[1]}\n"
                    f"   🎲 Xúc xắc 3: {dice_values[2]}\n"
                    f"   📊 Tổng điểm: {total_points} ({'Xỉu' if result == 'xỉu' else 'Tài'})\n"
                    f"   🏆 Kết quả: Bạn đã {outcome}\n"
                    f"     ➜ {response}\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"    🔄 Chơi tiếp? Nhập: {PREFIX}taixiu <tài/xỉu> <số tiền>"
                )

                gui = Message(text=data_trave)

    client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=60000)
    
    if dice_values:
        image_paths = [f'modules/taixiu/{value}.jpg' for value in dice_values]
        merged_image_path = "modules/taixiu/merged_dice.jpg"

        if all(os.path.exists(path) for path in image_paths):
            merge_images(image_paths, merged_image_path)

            client.sendLocalImage(
                imagePath=merged_image_path,
                message=gui,
                thread_id=thread_id,
                thread_type=thread_type,
                width=921,
                height=308,
                ttl=240000
            )

            os.remove(merged_image_path)
        else:
            response_message += "\n➜ Không thể hiển thị hình ảnh kết quả do thiếu hình ảnh xúc xắc."
            client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=60000)

def PTA():
    return {
        'taixiu': handle_taixiu_command,
        'tx': handle_taixiu_command
    }