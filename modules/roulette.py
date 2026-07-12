import json
import random
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from zlapi.models import *
from config import PREFIX

des = {
    'version': "1.4.0",
    'credits': "ngbao",
    'description': "Chơi game Roulette",
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
                return 0, "• Phần trăm phải từ 1% đến 100%."
        except ValueError:
            return 0, "• Phần trăm không hợp lệ."
    
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
            return 0, "• Số tiền cược phải lớn hơn 0."
        return amount, None
    except (ValueError, TypeError):
        return 0, "• Số tiền không hợp lệ. Ví dụ: 100K, 1M, 1B, 1BB"

def get_user_name(client, user_id):
    try:
        user_info = client.fetchUserInfo(user_id)
        profile = user_info.changed_profiles.get(user_id, {})
        user_name = profile.get('zaloName', 'Không xác định')
    except AttributeError:
        user_name = 'Không xác định'
    return user_name

class RouletteBet:
    VALID_NUMBERS = set(range(0, 37))
    RED_NUMBERS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
    BLACK_NUMBERS = {2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35}
    COLUMNS = {
        'col1': {1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34},
        'col2': {2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35},
        'col3': {3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36}
    }
    DOZENS = {
        '1st12': set(range(1, 13)),
        '2nd12': set(range(13, 25)),
        '3rd12': set(range(25, 37))
    }

    @staticmethod
    def validate_choice(choice):
        choice = choice.lower()
        valid_simple = ['đỏ', 'đen', 'chẵn', 'lẻ', '1-18', '19-36', '1st12', '2nd12', '3rd12', 'col1', 'col2', 'col3']
        if choice in valid_simple:
            return True
        if choice.isdigit() and int(choice) in RouletteBet.VALID_NUMBERS:
            return True
        if '-' in choice:
            try:
                nums = [int(n) for n in choice.split('-')]
                return all(n in RouletteBet.VALID_NUMBERS for n in nums) and len(nums) in [2, 3]
            except ValueError:
                return False
        return False

    @staticmethod
    def calculate_payout(choice, bet_amount, result_number):
        choice = choice.lower()
        if choice.isdigit() and int(choice) == result_number:
            return bet_amount * 36  # x35 + vốn
        elif choice == 'đỏ' and result_number in RouletteBet.RED_NUMBERS:
            return bet_amount * 2
        elif choice == 'đen' and result_number in RouletteBet.BLACK_NUMBERS:
            return bet_amount * 2
        elif choice == 'chẵn' and result_number % 2 == 0 and result_number != 0:
            return bet_amount * 2
        elif choice == 'lẻ' and result_number % 2 == 1:
            return bet_amount * 2
        elif choice == '1-18' and 1 <= result_number <= 18:
            return bet_amount * 2
        elif choice == '19-36' and 19 <= result_number <= 36:
            return bet_amount * 2
        elif choice in RouletteBet.DOZENS and result_number in RouletteBet.DOZENS[choice]:
            return bet_amount * 3
        elif choice in RouletteBet.COLUMNS and result_number in RouletteBet.COLUMNS[choice]:
            return bet_amount * 3
        elif '-' in choice:
            nums = [int(n) for n in choice.split('-')]
            if result_number in nums:
                return bet_amount * (18 if len(nums) == 2 else 12)  # x17 + vốn hoặc x11 + vốn
        return 0

def draw_roulette_result(number, color, choice, bet_amount, outcome, total_received, current_balance, author_name):
    width, height = 1280, 720
    img = Image.new('RGB', (width, height), color='#0f0f1a')
    draw = ImageDraw.Draw(img)
    try:
        title_font = ImageFont.truetype("modules/cache/font/BeVietnamPro-Bold.ttf", 60)
        number_font = ImageFont.truetype("modules/cache/font/BeVietnamPro-Bold.ttf", 120)
        info_font = ImageFont.truetype("modules/cache/font/BeVietnamPro-Bold.ttf", 36)
        result_font = ImageFont.truetype("modules/cache/font/BeVietnamPro-Bold.ttf", 45)
        footer_font = ImageFont.truetype("modules/cache/font/BeVietnamPro-Bold.ttf", 25)
    except:
        title_font = ImageFont.load_default()
        number_font = ImageFont.load_default()
        info_font = ImageFont.load_default()
        result_font = ImageFont.load_default()
        footer_font = ImageFont.load_default()

    # Vẽ tiêu đề
    title_text = "KẾT QUẢ ROULETTE"
    draw.text((width // 2, 80), title_text, fill="#FFD700", font=title_font, anchor="mm")

    # Vẽ vòng tròn và số kết quả
    circle_radius = height // 5
    draw.ellipse(
        (width//2 - circle_radius, height//2 - circle_radius - 90,
         width//2 + circle_radius, height//2 + circle_radius - 90),
        outline="#FFD700", width=4
    )
    box_size = circle_radius // 1.7
    color_map = {'xanh': (0, 200, 0), 'đỏ': (200, 30, 30), 'đen': (10, 10, 10)}
    draw.rounded_rectangle(
        (width//2 - box_size, height//2 - box_size - 90,
         width//2 + box_size, height//2 + box_size - 90),
        radius=30,
        fill=color_map[color],
        outline="#FFD700",
        width=5
    )
    draw.text(
        (width//2, height//2 - 90),
        str(number),
        fill="white",
        font=number_font,
        anchor="mm"
    )

    # Vẽ hộp thông tin
    info_box_height = height // 2.4
    info_box_width = width * 3 // 4
    info_box_x = width//2 - info_box_width//2
    info_box_y = height - info_box_height - 72
    draw.rounded_rectangle(
        (info_box_x, info_box_y,
         info_box_x + info_box_width, info_box_y + info_box_height),
        radius=20,
        fill="#000000",
        outline="#FFD700",
        width=3
    )

    # Thông tin người chơi
    player_info = [
        f"Người chơi: {author_name}",
        f"Cược: {format_money(bet_amount)} vào {choice.capitalize()}",
        f"Kết quả: Số {number} ({color.capitalize()})",
        f"Kết luận: {outcome}",
        f"Số dư: {format_money(current_balance)}"
    ]
    for i, text in enumerate(player_info):
        text_color = "#00FF00" if i == 3 and 'THẮNG' in outcome else "#FF0000" if i == 3 else "white"
        draw.text(
            (info_box_x + 40, info_box_y + 30 + i * 50),
            text,
            fill=text_color,
            font=info_font
        )

    # Chân trang
    footer_text = f"© 2025 Roulette Game | Tran Manh Quan"
    draw.text(
        (width//2, height - 30),
        footer_text,
        fill="#888888",
        font=footer_font,
        anchor="mm"
    )

    output_image_path = 'modules/roulette/result.png'
    img.save(output_image_path)
    return output_image_path

def get_roulette_result():
    number = random.randint(0, 36)
    color = 'xanh' if number == 0 else 'đỏ' if number in RouletteBet.RED_NUMBERS else 'đen'
    return number, color

def handle_roulette_command(message, message_object, thread_id, thread_type, author_id, client, ttl=120000):
    text = message.split()
    money_data = load_money_data()
    response_message = ""

    if len(text) < 3 or not RouletteBet.validate_choice(text[1]):
        response_message = (
            "🎰 NT DZ MỪNG ĐẾN VỚI ROULETTE SÒNG BẠC 🎰\n"
            "─────────────────────\n"
            "🌟 HƯỚNG DẪN CHƠI ROULETTE\n"
            "─────────────────────\n"
            "🔹 Chọn loại cược và đặt tiền:\n"
            "  • Số cụ thể (0-36): Thưởng x35\n"
            "  • Màu (đỏ/đen): Thưởng x2\n"
            "  • Chẵn/Lẻ: Thưởng x2\n"
            "  • Nửa bàn (1-18/19-36): Thưởng x2\n"
            "  • Tá (1st12/2nd12/3rd12): Thưởng x3\n"
            "  • Cột (col1/col2/col3): Thưởng x3\n"
            "  • Split (2 số, vd: 1-2): Thưởng x17\n"
            "  • Street (3 số, vd: 1-2-3): Thưởng x11\n\n"
            "🔹 Cách đặt cược:\n"
            "  • Dùng số tiền cụ thể, % số dư, hoặc 'all'.\n"
            "  • Ví dụ: 100K, 1M, 50%, all.\n\n"
            "📜 CÚ PHÁP:\n"
            f"{PREFIX}roulette <lựa chọn> <số tiền>\n\n"
            "🔸 VÍ DỤ:\n"
            f"  • {PREFIX}roulette 7 100K\n"
            f"  • {PREFIX}roulette đỏ 1M\n"
            f"  • {PREFIX}roulette 1-2 500K\n"
            f"  • {PREFIX}roulette col1 2M\n"
            f"  • {PREFIX}roulette 1st12 all\n\n"
            "💡 LƯU Ý:\n"
            "  • Số tiền cược > 0 và ≤ số dư.\n"
            "  • Nhập đúng lựa chọn cược.\n"
            "  • Số 0 là màu xanh, không tính chẵn/lẻ.\n\n"
            "📩 Hãy đặt cược và thử vận may của bạn! 🎲"
        )
    else:
        choice = text[1].lower()
        current_balance = money_data.get(str(author_id), 0)
        if len(text) >= 3:
            bet_amount, error = parse_bet_amount(text[2], current_balance)
            if error:
                response_message = error
            else:
                if bet_amount > current_balance:
                    response_message = f"• Số dư của bạn không đủ để đặt cược {format_money(bet_amount)}."
                elif bet_amount <= 0:
                    response_message = "• Số tiền cược phải lớn hơn 0."
                else:
                    result_number, result_color = get_roulette_result()
                    total_received = RouletteBet.calculate_payout(choice, bet_amount, result_number)
                    author_name = get_user_name(client, author_id)

                    if total_received > 0:
                        outcome = "THẮNG 🎉"
                        result_message = (
                            f"🎮 KẾT QUẢ ROULETTE\n\n"
                            f"🎲 Số ra: {result_number} ({result_color.capitalize()})\n"
                            f"💰 Nhận: {format_money(total_received)}\n"
                            f"💵 Đã cộng {format_money(total_received)} vào tài khoản."
                        )
                    else:
                        outcome = "THUA 😔"
                        result_message = (
                            f"🎮 KẾT QUẢ ROULETTE\n\n"
                            f"🎲 Số ra: {result_number} ({result_color.capitalize()})\n"
                            f"❌ Mất: {format_money(bet_amount)}\n"
                            f"💵 Đã trừ {format_money(bet_amount)} khỏi tài khoản."
                        )

                    money_data[str(author_id)] = current_balance + total_received - bet_amount
                    save_money_data(money_data)

                    image_path = draw_roulette_result(
                        result_number, result_color, choice, bet_amount, 
                        outcome, total_received, money_data.get(str(author_id), 0), author_name
                    )
                    client.sendLocalImage(
                        imagePath=image_path,
                        message=Message(text=result_message),
                        thread_id=thread_id,
                        thread_type=thread_type,
                        width=921,
                        height=518,
                        ttl=120000
                    )
                    try:
                        os.remove(image_path)
                    except:
                        pass
                    return
        else:
            response_message = (
                "🎰 LỖI NHẬP LỆNH 🎰\n"
                "─────────────────────────────────\n"
                "❌ Lệnh không đúng định dạng!\n"
                f"👉 CÚ PHÁP: {PREFIX}roulette <lựa chọn> <số tiền>\n\n"
                "🔸 VÍ DỤ:\n"
                f"  • {PREFIX}roulette 7 100K\n"
                f"  • {PREFIX}roulette đỏ 1M\n"
                f"  • {PREFIX}roulette 1-2 500K\n"
                f"  • {PREFIX}roulette col1 2M\n\n"
                "💡 LƯU Ý:\n"
                "  • Nhập đúng lựa chọn cược.\n"
                "  • Số tiền cược phải hợp lệ.\n\n"
                "📩 Vui lòng nhập lại lệnh chính xác!"
            )

    if response_message:
        client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=120000)

def PTA():
    return {
        'rlt': handle_roulette_command,
        'roulette': handle_roulette_command
    }