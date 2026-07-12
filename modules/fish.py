# -*- coding: utf-8 -*-
import os
import json
import random
import time
from datetime import datetime
from zlapi.models import Message
from config import PREFIX

des = {
    'version': "1.0.0",
    'credits': "ngbao",
    'description': "Game câu cá",
    'power': "Thành viên"
}

MONEY_PATH = "modules/cache/money.json"      # dùng chung với taixiu
FISH_DATA_PATH = "modules/cache/fish.json"   # dữ liệu riêng cho câu cá
COOLDOWN_SECONDS = 5                         # chống spam cast (per-user)

# ================= utils tiền (dùng chung) =================
def load_money_data():
    try:
        with open(MONEY_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_money_data(data):
    os.makedirs(os.path.dirname(MONEY_PATH), exist_ok=True)
    with open(MONEY_PATH, 'w') as f:
        json.dump(data, f, indent=4)

def format_money(amount):
    try:
        amount = int(amount)
    except:
        amount = 0
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

# ================= storage câu cá =================
def load_fish_data():
    try:
        with open(FISH_DATA_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_fish_data(data):
    os.makedirs(os.path.dirname(FISH_DATA_PATH), exist_ok=True)
    with open(FISH_DATA_PATH, 'w') as f:
        json.dump(data, f, indent=4)

# ================= người dùng =================
def get_user_name(client, user_id):
    try:
        info = client.fetchUserInfo(user_id)
        if isinstance(info, dict):
            p = info.get(str(user_id)) or info.get(user_id) or {}
            if isinstance(p, dict):
                return p.get("zaloName") or p.get("name") or "Người chơi"
    except:
        pass
    return "Người chơi"

# ================= cấu hình cá =================
# danh sách loài cá mẫu (id, tên, rarity, base_value)
FISH_POOL = [
    {"id": "f_shr", "name": "Cá tạp", "rarity": "common", "value": 50},
    {"id": "f_carp", "name": "Cá chép", "rarity": "common", "value": 80},
    {"id": "f_trout", "name": "Cá hồi nhỏ", "rarity": "uncommon", "value": 200},
    {"id": "f_bass", "name": "Cá rô", "rarity": "uncommon", "value": 250},
    {"id": "f_salmon", "name": "Cá hồi lớn", "rarity": "rare", "value": 800},
    {"id": "f_snake", "name": "Cá rắn kỳ lạ", "rarity": "rare", "value": 1200},
    {"id": "f_treasure", "name": "Cá kho báu (hiếm)", "rarity": "legend", "value": 5000},
]

# xác suất cơ bản (phải cộng lên 100)
RARITY_WEIGHTS = {
    "common": 60,
    "uncommon": 25,
    "rare": 12,
    "legend": 3
}

# mồi: mỗi lần cast tiêu 1 bait
STARTER_BAIT = 3
BAIT_PRICE = 100  # 1 bait = 100 tiền

# ================= helper =================
def ensure_player_record(data, user_id):
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "bait": STARTER_BAIT,
            "inventory": [],    # list of fish items: {id,name,rarity,size,value,time}
            "last_cast": 0
        }

def weighted_choice_by_rarity():
    # pick rarity first by weights
    total = sum(RARITY_WEIGHTS.values())
    rnd = random.randint(1, total)
    acc = 0
    chosen = "common"
    for r, w in RARITY_WEIGHTS.items():
        acc += w
        if rnd <= acc:
            chosen = r
            break
    # from pool, pick a fish of tPTA rarity
    candidates = [f for f in FISH_POOL if f["rarity"] == chosen]
    if not candidates:
        candidates = [f for f in FISH_POOL if f["rarity"] == "common"]
    return random.choice(candidates)

def generate_fish():
    fish_def = weighted_choice_by_rarity()
    # size influences value: random factor: 0.8 - 1.8 times base
    size_cm = random.randint(10, 100)
    size_factor = 0.8 + (size_cm / 100)  # 10cm -> 0.9, 100cm -> 1.8
    value = max(1, int(fish_def["value"] * size_factor))
    # add small random bonus for rare/legend
    if fish_def["rarity"] == "rare":
        value += random.randint(50, 300)
    if fish_def["rarity"] == "legend":
        value += random.randint(300, 1500)
    return {
        "id": fish_def["id"],
        "name": fish_def["name"],
        "rarity": fish_def["rarity"],
        "size_cm": size_cm,
        "value": value,
        "caught_at": int(time.time())
    }

# ================= game commands =================
def help_text():
    return (
        "🎣 GAME CÂU CÁ 🎣\n"
        "━━━━━━━━━━━━━━━\n"
        f"• {PREFIX}fish help  — Xem hướng dẫn\n"
        f"• {PREFIX}fish cast  — Câu 1 lần (tiêu 1 mồi)\n"
        f"• {PREFIX}fish bait  — Xem số mồi / mua mồi (cú pháp: {PREFIX}fish bait buy <số>)\n"
        f"• {PREFIX}fish inventory  — Xem kho cá của bạn\n"
        f"• {PREFIX}fish sell <index|all>  — Bán cá (index từ `inventory`)\n"
        "━━━━━━━━━━━━━━━\n"
        "Lưu ý: Mỗi người mới được tặng 3 mồi starter. Chúc bạn câu được cá to!"
    )

def handle_fish_command(message, message_object, thread_id, thread_type, author_id, client):
    parts = message.strip().split()
    cmd = parts[1].lower() if len(parts) >= 2 else "help"

    # load data
    money = load_money_data()
    fish_data = load_fish_data()
    ensure_player_record(fish_data, author_id)
    uid = str(author_id)
    player = fish_data[uid]

    # ensure money record exists
    if str(author_id) not in money:
        money[str(author_id)] = 0

    # HELP
    if cmd == "help":
        client.replyMessage(Message(help_text()), message_object, thread_id, thread_type)
        save_fish_data(fish_data)
        save_money_data(money)
        return

    # BAIT: show or buy
    if cmd == "bait":
        if len(parts) >= 3 and parts[2].lower() == "buy":
            # buy amount
            if len(parts) < 4:
                client.replyMessage(Message(f"❌ Cú pháp: {PREFIX}fish bait buy <số>"), message_object, thread_id, thread_type)
                return
            try:
                amt = int(parts[3])
                if amt <= 0:
                    raise ValueError()
            except:
                client.replyMessage(Message("❌ Nhập số mồi hợp lệ (>0)."), message_object, thread_id, thread_type)
                return
            cost = amt * BAIT_PRICE
            bal = money.get(uid, 0)
            if bal < cost:
                client.replyMessage(Message(f"❌ Bạn không đủ tiền. Giá {amt} mồi = {format_money(cost)}. Số dư: {format_money(bal)}"), message_object, thread_id, thread_type)
                return
            money[uid] = bal - cost
            player["bait"] = player.get("bait", 0) + amt
            save_money_data(money)
            save_fish_data(fish_data)
            client.replyMessage(Message(f"✅ Mua thành công {amt} mồi. Đã trừ {format_money(cost)}. Mồi hiện có: {player['bait']}"), message_object, thread_id, thread_type)
            return
        else:
            client.replyMessage(Message(f"🎣 Bạn có {player.get('bait', 0)} mồi.\nMua bằng: {PREFIX}fish bait buy <số> (1 mồi = {format_money(BAIT_PRICE)})"), message_object, thread_id, thread_type)
            save_fish_data(fish_data)
            save_money_data(money)
            return

    # INVENTORY
    if cmd == "inventory":
        inv = player.get("inventory", [])
        if not inv:
            client.replyMessage(Message("📦 Kho bạn đang rỗng. Hãy câu cá bằng lệnh `!fish cast`!"), message_object, thread_id, thread_type)
            save_fish_data(fish_data)
            return
        lines = ["📦 KHO CÁ CỦA BẠN:", "━━━━━━━━━━━━━━━"]
        for i, item in enumerate(inv, start=1):
            t = datetime.fromtimestamp(item.get("caught_at", time.time())).strftime("%d/%m %H:%M")
            lines.append(f"{i}. {item['name']} ({item['rarity']}) — {item['size_cm']}cm — {format_money(item['value'])} — {t}")
        lines.append("━━━━━━━━━━━━━━━\nDùng: !fish sell <số>  hoặc  !fish sell all")
        client.replyMessage(Message("\n".join(lines)), message_object, thread_id, thread_type)
        save_fish_data(fish_data)
        return

    # SELL
    if cmd == "sell":
        inv = player.get("inventory", [])
        if len(parts) < 3:
            client.replyMessage(Message("❌ Cú pháp: !fish sell <index|all>"), message_object, thread_id, thread_type)
            return
        arg = parts[2].lower()
        if arg == "all":
            if not inv:
                client.replyMessage(Message("❌ Kho trống, không có gì để bán."), message_object, thread_id, thread_type)
                return
            total = sum(item["value"] for item in inv)
            money[uid] = money.get(uid, 0) + total
            player["inventory"] = []
            save_money_data(money)
            save_fish_data(fish_data)
            client.replyMessage(Message(f"✅ Đã bán tất cả cá, nhận {format_money(total)}. Số dư hiện tại: {format_money(money[uid])}"), message_object, thread_id, thread_type)
            return
        else:
            try:
                idx = int(arg) - 1
                if idx < 0 or idx >= len(inv):
                    raise IndexError()
            except:
                client.replyMessage(Message("❌ Chỉ số không hợp lệ."), message_object, thread_id, thread_type)
                return
            item = inv.pop(idx)
            money[uid] = money.get(uid, 0) + item["value"]
            save_money_data(money)
            save_fish_data(fish_data)
            client.replyMessage(Message(f"✅ Đã bán {item['name']} ({item['size_cm']}cm) lấy {format_money(item['value'])}. Số dư: {format_money(money[uid])}"), message_object, thread_id, thread_type)
            return

    # CAST / câu cá
    if cmd == "cast":
        now = int(time.time())
        last = player.get("last_cast", 0)
        if now - last < COOLDOWN_SECONDS:
            client.replyMessage(Message(f"⏳ Hãy chờ {COOLDOWN_SECONDS} giây giữa 2 lần câu."), message_object, thread_id, thread_type)
            return
        bait = player.get("bait", 0)
        if bait <= 0:
            client.replyMessage(Message(f"❌ Bạn không có mồi! Mua bằng: {PREFIX}fish bait buy <số> hoặc nhận mồi starter (nếu mới)."), message_object, thread_id, thread_type)
            return

        # tiêu 1 mồi
        player["bait"] = bait - 1
        player["last_cast"] = now

        # chance miss (small)
        miss_roll = random.randint(1, 100)
        miss_threshold = 8  # 8% miss
        # mồi có thể ảnh hưởng (not implemented complexly now)
        if miss_roll <= miss_threshold:
            save_fish_data(fish_data)
            client.replyMessage(Message("😓 Rũ lưới... hôm nay xui, không bắt được gì."), message_object, thread_id, thread_type)
            return

        # bắt được 1 con
        caught = generate_fish()
        # small chance to get a surprise: golden bait (bonus money)
        bonus_roll = random.randint(1, 1000)
        if bonus_roll <= 5:  # 0.5% chance
            bonus = 2000
            money[uid] = money.get(uid, 0) + bonus
            save_money_data(money)
            client.replyMessage(Message(f"🎉 Wow! Khi kéo lưới bạn tìm thấy 1 kho báu nhỏ và nhận {format_money(bonus)}!"), message_object, thread_id, thread_type)

        # thêm vào inventory
        inv = player.get("inventory", [])
        inv.append(caught)
        player["inventory"] = inv
        save_fish_data(fish_data)
        save_money_data(money)

        # thông báo chi tiết
        user_name = get_user_name(client, author_id)
        msg_lines = [
            f"🎣 KẾT QUẢ CÂU CÁ — {user_name}",
            "━━━━━━━━━━━━━━━",
            f"Bạn đã câu được: {caught['name']} ({caught['rarity']})",
            f"Kích thước: {caught['size_cm']} cm",
            f"Giá trị (tạm): {format_money(caught['value'])}",
            f"Mồi còn lại: {player.get('bait',0)}",
            "━━━━━━━━━━━━━━━",
            f"Dùng {PREFIX}fish inventory để xem kho, {PREFIX}fish sell <số> để bán."
        ]
        client.replyMessage(Message("\n".join(msg_lines)), message_object, thread_id, thread_type)
        return

    # unknown
    client.replyMessage(Message("❌ Lệnh không hợp lệ. Dùng: !fish help"), message_object, thread_id, thread_type)
    save_fish_data(fish_data)
    save_money_data(money)

def PTA():
    return {
        'fish': handle_fish_command,
        'fishing': handle_fish_command
    }