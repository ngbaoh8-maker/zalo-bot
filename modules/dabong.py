import json
import random
import time
from zlapi.models import *
from config import PREFIX

des = {
    'version': "1.0.0",
    'credits': "ngbao",
    'description': "Game Đá Bóng (Trái / Giữa / Phải)",
    'power': "Thành viên"
}

# ================= MONEY =================
def load_money():
    try:
        with open('modules/cache/money.json', 'r') as f:
            return json.load(f)
    except:
        return {}

def save_money(data):
    with open('modules/cache/money.json', 'w') as f:
        json.dump(data, f, indent=4)

def format_money(n):
    n = int(n)
    if abs(n) >= 1_000_000_000_000:
        return f"{n//1_000_000_000_000}BB"
    if abs(n) >= 1_000_000_000:
        return f"{n//1_000_000_000}B"
    if abs(n) >= 1_000_000:
        return f"{n//1_000_000}M"
    if abs(n) >= 1_000:
        return f"{n//1_000}K"
    return str(n)

def parse_bet(text, balance):
    text = text.lower()

    if text == "all":
        if balance <= 0:
            return 0, "Số dư không đủ"
        return balance, None

    if text.endswith('%'):
        try:
            p = float(text[:-1])
            money = int(balance * p / 100)
            if money <= 0:
                return 0, "Tiền cược phải > 0"
            return money, None
        except:
            return 0, "Phần trăm không hợp lệ"

    mul = 1
    if text.endswith('bb'):
        mul = 1_000_000_000_000
        text = text[:-2]
    elif text.endswith('b'):
        mul = 1_000_000_000
        text = text[:-1]
    elif text.endswith('m'):
        mul = 1_000_000
        text = text[:-1]
    elif text.endswith('k'):
        mul = 1_000
        text = text[:-1]

    try:
        money = int(float(text) * mul)
        if money <= 0:
            return 0, "Tiền cược phải > 0"
        return money, None
    except:
        return 0, "Sai định dạng tiền"

# ================= CONFIG =================
CHOICES = ["trái", "giữa", "phải"]
COOLDOWN = 6
last_play = {}

# ================= HELP =================
def help_text():
    return (
        "⚽ GAME ĐÁ BÓNG ⚽\n"
        "━━━━━━━━━━━━━━━\n"
        f"📌 Lệnh:\n"
        f"➜ {PREFIX}dabong <trái/giữa/phải> <tiền>\n\n"
        "💰 Ví dụ:\n"
        f"➜ {PREFIX}dabong trái 100K\n"
        f"➜ {PREFIX}dabong giữa 50%\n"
        f"➜ {PREFIX}dabong phải all\n\n"
        "🎯 Luật chơi:\n"
        "➜ Bot giấu bóng ở 1 vị trí\n"
        "➜ Đoán đúng: x2 tiền\n"
        "➜ Đoán sai: mất tiền\n\n"
        "⏳ Chống spam: vài giây / lượt"
    )

# ================= MAIN =================
def handle_dabong(message, message_object, thread_id, thread_type, author_id, client):
    args = message.split()
    money = load_money()

    if len(args) == 1 or args[1].lower() in ["help", "hd"]:
        client.replyMessage(Message(text=help_text()), message_object, thread_id, thread_type)
        return

    if len(args) != 3 or args[1].lower() not in CHOICES:
        client.replyMessage(
            Message(text=f"❌ Sai lệnh\n➜ {PREFIX}dabong <trái/giữa/phải> <tiền>"),
            message_object, thread_id, thread_type
        )
        return

    now = time.time()
    if author_id in last_play and now - last_play[author_id] < COOLDOWN:
        client.replyMessage(
            Message(text=f"⏳ Chờ {int(COOLDOWN - (now - last_play[author_id]))}s nữa"),
            message_object, thread_id, thread_type
        )
        return

    choice = args[1].lower()
    balance = money.get(str(author_id), 0)
    bet, err = parse_bet(args[2], balance)

    if err:
        client.replyMessage(Message(text=f"❌ {err}"), message_object, thread_id, thread_type)
        return

    if bet > balance:
        client.replyMessage(Message(text="❌ Không đủ tiền"), message_object, thread_id, thread_type)
        return

    ball = random.choice(CHOICES)
    win = choice == ball
    change = bet * 2 if win else -bet

    money[str(author_id)] = balance + change
    save_money(money)
    last_play[author_id] = now

    result = (
        "⚽ ĐÁ BÓNG ⚽\n"
        f"🥅 Bóng ở: {ball.upper()}\n"
        f"👉 Bạn chọn: {choice.upper()}\n\n"
        f"{'🟢 GHI BÀN!' if win else '🔴 TRƯỢT!'}\n"
        f"{'➜ Nhận ' + format_money(bet*2) if win else '➜ Mất ' + format_money(bet)}"
    )

    client.replyMessage(Message(text=result), message_object, thread_id, thread_type)

# ================= REGISTER =================
def PTA():
    return {
        'dabong': handle_dabong,
        'db': handle_dabong
    }
