import json
import random
import time
from zlapi.models import *
from config import PREFIX

des = {
    'version': "1.0.0",
    'credits': "ngbao",
    'description': "Game Sóc Lọ",
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
    if abs(n) >= 1_000_000:
        return f"{n//1_000_000}M"
    if abs(n) >= 1_000:
        return f"{n//1_000}K"
    return str(n)

def parse_bet(text, balance):
    text = text.lower()
    if text == "all":
        return balance, None

    mul = 1
    if text.endswith('m'):
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

# ================= MAIN =================
def handle_soclo(message, message_object, thread_id, thread_type, author_id, client):
    args = message.split()
    money = load_money()

    if len(args) != 2:
        client.replyMessage(
            Message(text=f"❌ Dùng: {PREFIX}soclo <tiền>\nVí dụ: {PREFIX}soclo 100K"),
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

    # ⏱ RANDOM THỜI GIAN BẮN: 0.1s -> 10 phút
    shoot_time = random.uniform(0.1, 600)

    client.replyMessage(
        Message(text=f"🎯 SOC LỌ 🎯\n⏳ Đang bắn...\n⏱ Thời gian: {shoot_time:.2f} giây"),
        message_object, thread_id, thread_type
    )

    time.sleep(shoot_time)

    # 🎲 4 đồng xu
    coins = [random.randint(0, 1) for _ in range(4)]
    total = sum(coins)
    result = "chẵn" if total % 2 == 0 else "lẻ"

    # Random win / thua 50-50
    win = random.choice([True, False])
    change = bet * 2 if win else -bet

    money[str(author_id)] = balance + change
    save_money(money)

    msg = (
        f"🎯 KẾT QUẢ SOC LỌ 🎯\n"
        f"🪙 Kết quả: {coins} (Tổng: {total} → {result.upper()})\n"
        f"💰 Cược: {format_money(bet)}\n"
        f"{'🟢 THẮNG' if win else '🔴 THUA'}\n"
        f"{'➜ Nhận ' + format_money(bet*2) if win else '➜ Mất ' + format_money(bet)}"
    )

    client.replyMessage(Message(text=msg), message_object, thread_id, thread_type)

# ================= REGISTER =================
def PTA():
    return {
        'soclo': handle_soclo,
        'sl': handle_soclo
    }