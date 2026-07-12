import json
import random
import time
from zlapi.models import *
from config import PREFIX

des = {
    'version': "1.0.0",
    'credits': "ngbao",
    'description': "Game Quay Hũ (Slot)",
    'power': "Thành Viên"
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
                return 0, "Số tiền cược phải > 0"
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
            return 0, "Số tiền cược phải > 0"
        return money, None
    except:
        return 0, "Sai định dạng tiền"

# ================= SLOT CONFIG =================
SLOTS = ["🍒", "🍋", "🍉", "⭐", "💎"]
COOLDOWN = 8  # seconds
last_play = {}

# ================= MENU =================
def menu():
    return (
        "🎰 QUAY HŨ 🎰\n"
        "━━━━━━━━━━━━━━━\n"
        f"📌 Lệnh:\n"
        f"➜ {PREFIX}quayhu <tiền>\n\n"
        "💰 Ví dụ:\n"
        f"➜ {PREFIX}quayhu 100K\n"
        f"➜ {PREFIX}quayhu 50%\n"
        f"➜ {PREFIX}quayhu all\n\n"
        "🎯 Luật:\n"
        "➜ 3 biểu tượng giống nhau: x5\n"
        "➜ 2 biểu tượng giống nhau: x2\n"
        "➜ 3 💎: JACKPOT x10"
    )

# ================= MAIN =================
def handle_quayhu(message, message_object, thread_id, thread_type, author_id, client):
    args = message.split()
    money = load_money()

    if len(args) == 1 or args[1].lower() == "help":
        client.replyMessage(Message(text=menu()), message_object, thread_id, thread_type)
        return

    now = time.time()
    if author_id in last_play and now - last_play[author_id] < COOLDOWN:
        client.replyMessage(
            Message(text=f"⏳ Chờ {int(COOLDOWN - (now - last_play[author_id]))}s nữa mới quay tiếp"),
            message_object, thread_id, thread_type
        )
        return

    balance = money.get(str(author_id), 0)
    bet, err = parse_bet(args[1], balance)

    if err:
        client.replyMessage(Message(text=f"❌ {err}"), message_object, thread_id, thread_type)
        return

    if bet > balance:
        client.replyMessage(Message(text="❌ Không đủ tiền"), message_object, thread_id, thread_type)
        return

    slot = [random.choice(SLOTS) for _ in range(3)]

    win = False
    multi = 0

    if slot.count("💎") == 3:
        win = True
        multi = 10
    elif len(set(slot)) == 1:
        win = True
        multi = 5
    elif len(set(slot)) == 2:
        win = True
        multi = 2

    change = bet * multi if win else -bet
    money[str(author_id)] = balance + change
    save_money(money)

    last_play[author_id] = now

    result = (
        f"🎰 QUAY HŨ 🎰\n"
        f"{slot[0]} | {slot[1]} | {slot[2]}\n\n"
        f"💸 Cược: {format_money(bet)}\n"
    )

    if win:
        result += f"🟢 THẮNG x{multi}\n➜ Nhận {format_money(bet*multi)}"
    else:
        result += f"🔴 THUA\n➜ Mất {format_money(bet)}"

    client.replyMessage(Message(text=result), message_object, thread_id, thread_type)

# ================= REGISTER =================
def PTA():
    return {
        'quayhu': handle_quayhu,
        'slot': handle_quayhu
    }
