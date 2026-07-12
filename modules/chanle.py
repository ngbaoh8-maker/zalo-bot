import json
import random
import os
from PIL import Image
from zlapi.models import *
from config import PREFIX

des = {
    'version': "1.0.2",
    'credits': "ngbao",
    'description': "Game Chẵn Lẻ",
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
                return 0, "Số tiền cược phải lớn hơn 0"
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
            return 0, "Số tiền cược phải lớn hơn 0"
        return money, None
    except:
        return 0, "Sai định dạng tiền"

# ================= IMAGE =================
def merge_images(paths, out):
    imgs = [Image.open(p) for p in paths]
    w = sum(i.width for i in imgs)
    h = max(i.height for i in imgs)
    new = Image.new("RGB", (w, h))
    x = 0
    for i in imgs:
        new.paste(i, (x, 0))
        x += i.width
    new.save(out)

def get_name(client, uid):
    try:
        info = client.fetchUserInfo(uid)
        return info.changed_profiles.get(uid, {}).get("zaloName", "Người chơi")
    except:
        return "Người chơi"

# ================= MENU =================
def menu():
    return (
        "🎯 GAME CHẴN LẺ 🎯\n"
        "━━━━━━━━━━━━━━━\n"
        f"📌 Lệnh:\n"
        f"➜ {PREFIX}chanle <chẵn/lẻ> <tiền>\n\n"
        "💰 Ví dụ:\n"
        f"➜ {PREFIX}chanle chẵn 100K\n"
        f"➜ {PREFIX}chanle lẻ 50%\n"
        f"➜ {PREFIX}chanle lẻ all\n\n"
        "🎲 Luật:\n"
        "➜ Tổng 3 xúc xắc là CHẴN hoặc LẺ\n"
        "➜ Thắng x2 | Bão (3 số giống nhau) x10"
    )

# ================= MAIN =================
def handle_chanle(message, message_object, thread_id, thread_type, author_id, client):
    args = message.split()
    money = load_money()

    if len(args) == 1 or args[1].lower() == "help":
        client.replyMessage(Message(text=menu()), message_object, thread_id, thread_type)
        return

    if len(args) != 3 or args[1].lower() not in ["chẵn", "lẻ"]:
        client.replyMessage(
            Message(text=f"❌ Sai lệnh\n➜ {PREFIX}chanle <chẵn/lẻ> <tiền>"),
            message_object, thread_id, thread_type
        )
        return

    choice = args[1].lower()
    balance = money.get(str(author_id), 0)
    bet, err = parse_bet(args[2], balance)

    if err:
        client.replyMessage(Message(text=f"❌ {err}"), message_object, thread_id, thread_type)
        return

    if bet <= 0:
        client.replyMessage(
            Message(text="❌ Số tiền cược phải lớn hơn 0"),
            message_object, thread_id, thread_type
        )
        return

    if bet > balance:
        client.replyMessage(Message(text="❌ Không đủ tiền"), message_object, thread_id, thread_type)
        return

    dice = [random.randint(1, 6) for _ in range(3)]
    total = sum(dice)
    result = "chẵn" if total % 2 == 0 else "lẻ"

    win = choice == result
    multi = 10 if dice.count(dice[0]) == 3 else 2
    change = bet * multi if win else -bet

    money[str(author_id)] = balance + change
    save_money(money)

    name = get_name(client, author_id)

    msg = (
        f"🎯 KẾT QUẢ CHẴN LẺ 🎯\n"
        f"👤 {name}\n"
        f"🎲 {dice[0]} - {dice[1]} - {dice[2]}\n"
        f"📊 Tổng: {total} ({result.upper()})\n"
        f"💸 Cược: {format_money(bet)} ({choice})\n"
        f"{'🟢 THẮNG' if win else '🔴 THUA'}\n"
        f"{'➜ Nhận ' + format_money(bet*multi) if win else '➜ Mất ' + format_money(bet)}"
    )

    gui = Message(text=msg)

    paths = [f"modules/taixiu/{i}.jpg" for i in dice]
    out = "modules/taixiu/chanle.jpg"

    if all(os.path.exists(p) for p in paths):
        merge_images(paths, out)
        client.sendLocalImage(
            imagePath=out,
            message=gui,
            thread_id=thread_id,
            thread_type=thread_type,
            width=900,
            height=300
        )
        os.remove(out)
    else:
        client.replyMessage(gui, message_object, thread_id, thread_type)

# ================= REGISTER =================
def PTA():
    return {
        'chanle': handle_chanle,
        'cl': handle_chanle
    }
