import os
import json
import random
import time
import requests
import urllib.parse
from datetime import datetime
from zlapi.models import Message, MultiMsgStyle, MessageStyle

des = {
    'version': "6.0.0",
    'credits': "ngbao",
    'description': "Hệ thống thú cưng ảo nâng cao: quay, shop, chơi, nạp xu, set ảnh theo loại hoặc tên, auto fix dữ liệu.",
    'power': "Thành Viên"
}

ADMIN = ["700542342650452398"]
DATA_DIR = "modules/data/pet"
PET_FILE = os.path.join(DATA_DIR, "pet_data.json")
SHOP_FILE = os.path.join(DATA_DIR, "shop_data.json")

RARITY = {
    "common": "🐣",
    "rare": "🐶",
    "epic": "🐉",
    "legendary": "🔥"
}

IMG_DIR = os.path.join(DATA_DIR, "img")

# ====== AUTO TẠO FILE & THƯ MỤC ======
def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def ensure_file(path, default_data=None):
    ensure_dir(os.path.dirname(path))
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default_data or {}, f, ensure_ascii=False, indent=2)

def ensure_image_dirs():
    for rarity in RARITY.keys():
        ensure_dir(os.path.join(IMG_DIR, rarity))

def load_json_safe(path):
    ensure_file(path, {})
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError
            return data
    except Exception:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
        return {}

def save_json_safe(path, data):
    ensure_file(path, {})
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ====== TIỆN ÍCH ======
def _is_admin(author_id): return str(author_id) in ADMIN

def _reply(client, msg, message_object, thread_id, thread_type, author_id):
    try:
        user_info = client.fetchUserInfo(author_id)
        name = user_info.changed_profiles.get(str(author_id), {}).get('zaloName', 'Không xác định') if user_info and user_info.changed_profiles else 'Không xác định'
    except Exception:
        name = "Không xác định"
    style = MultiMsgStyle([
        MessageStyle(offset=0, length=len(name), style="color", color="#f4b342", auto_format=False),
        MessageStyle(offset=0, length=len(name), style="bold", auto_format=False)
    ])
    client.replyMessage(Message(text=f"{name}\n➜ {msg}", style=style),
                        message_object, thread_id=thread_id, thread_type=thread_type, ttl=15000)

def _init_user(uid): return {"coin": 0, "pets": {}, "equipped": None}

def _init_pet(pid, name, rarity):
    return {"id": pid, "name": name, "rarity": rarity, "level": 1, "exp": 0, "hunger": 100, "happy": 100, "skin": "default"}

def _get_random_pet():
    roll = random.randint(1, 100)
    rarity = "common" if roll <= 50 else "rare" if roll <= 80 else "epic" if roll <= 95 else "legendary"
    pool = {
        "common": ["Mèo Con", "Chim Non", "Cá Nhỏ"],
        "rare": ["Thỏ Trắng", "Cún Cưng", "Sóc Nâu"],
        "epic": ["Rồng Bé", "Hổ Mini", "Kỳ Lân Con"],
        "legendary": ["Rồng Lửa", "Phượng Hoàng", "Cáo Chín Đuôi"]
    }
    name = random.choice(pool[rarity])
    return _init_pet(f"{int(time.time())}_{random.randint(100,999)}", name, rarity)

# ====== LẤY ẢNH PET ======
def _get_pet_image_by_name(pet_name, rarity):
    folder = os.path.join(IMG_DIR, rarity)
    ensure_dir(folder)
    imgs = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.png'))]

    # Ưu tiên ảnh trùng tên (ví dụ meo.jpg cho "Mèo Con")
    for img in imgs:
        if pet_name.lower().split()[0] in os.path.basename(img).lower():
            return img

    # Ảnh default_<rarity>.jpg nếu có
    default_path = os.path.join(folder, f"default_{rarity}.jpg")
    if os.path.exists(default_path):
        return default_path

    # fallback: ảnh ngẫu nhiên
    return random.choice(imgs) if imgs else None

# ====== LỆNH CHÍNH ======
def handle_pet_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        ensure_dir(DATA_DIR)
        ensure_image_dirs()
        users = load_json_safe(PET_FILE)
        shop = load_json_safe(SHOP_FILE)
        uid = str(author_id)

        if uid not in users or not isinstance(users[uid], dict):
            users[uid] = _init_user(uid)
        for k, v in _init_user(uid).items():
            users[uid].setdefault(k, v)
        user = users[uid]

        parts = message.strip().split(maxsplit=2)
        sub = parts[1].lower() if len(parts) > 1 else None
        arg = parts[2] if len(parts) > 2 else None

        # ===== MENU =====
        if sub == "menu":
            menu_text = (
                "🐾 pet → xem pet hiện tại\n"
                "🎰 pet roll → quay pet mới\n"
                "🎮 pet play → chơi với pet để tăng level\n"
                "🍗 pet feed → cho ăn hồi no, tăng exp\n"
                "🏪 pet shop / buy / equip\n"
                "💰 pet nap <xu> (admin)\n"
                "🖼️ pet set <common|rare|epic|legendary> [tên_pet] (reply ảnh)\n"
                "🧹 pet reset (admin)\n"
                "🎒 pet bag\n"
                "🏦 pet shopitem (shop phụ kiện) lỗi Đang sửa\n"
  
            )
            _reply(client, menu_text, message_object, thread_id, thread_type, author_id)
            return
        # ===== SHOP PHỤ KIỆN (ITEMS) =====
        if sub == "shopitem":
            msg = "🏪 SHOP PHỤ KIỆN TĂNG SỨC MẠNH 🏪\n──────────────────────\n"
            for iid, info in items_data.items():
                msg += f"🆔 {iid} • {info['name']}\n"
                msg += f"📜 {info['desc']}\n"
                msg += f"⚡ +{info['power']}% sức mạnh\n"
                msg += f"💰 Giá: {info['price']} xu\n──────────────────────\n"
            msg += "💡 Dùng lệnh: pet buyitem <id> để mua!"
            _reply(client, msg.strip(), message_object, thread_id, thread_type, author_id)
            return
         # ===== MUA PHỤ KIỆN =====
        if sub == "buyitem":
            if not arg:
                _reply(client, "⚠️ Dùng: pet buyitem <id_item>", message_object, thread_id, thread_type, author_id)
                return

            item_id = arg.strip()
            items_data = load_json_safe(ITEMS_FILE, {})
            if item_id not in items_data:
                _reply(client, "❌ ID phụ kiện không tồn tại!", message_object, thread_id, thread_type, author_id)
                return

            user = users.get(str(author_id), _init_user(author_id))
            item_info = items_data[item_id]
            price = item_info["price"]

            if user.get("coin", 0) < price:
                _reply(client, f"💸 Bạn không đủ xu để mua {item_info['name']} ({price} xu).", message_object, thread_id, thread_type, author_id)
                return

            # Trừ xu và thêm item vào túi
            user["coin"] -= price
            bag = user.get("bag", [])
            bag.append(item_id)
            user["bag"] = bag
            users[str(author_id)] = user
            save_json_safe(PET_FILE, users)

            _reply(client, f"✅ Bạn đã mua {item_info['name']}! (-{price} xu)", message_object, thread_id, thread_type, author_id)
            return

        # ===== XEM PET =====
        if sub is None:
            eq = user.get("equipped")
            if eq and eq in user["pets"]:
                p = user["pets"][eq]
                msg = (f"🐾 {p['name']} ({RARITY[p['rarity']]})\n"
                       f"⭐ Level: {p['level']}\n"
                       f"💖 HP: {p['happy']} | 🍗 No: {p['hunger']}\n"
                       f"💰 Xu: {user['coin']}")
                img = _get_pet_image_by_name(p["name"], p["rarity"])
                if img:
                    client.sendLocalImage(imagePath=img, message=Message(text=msg),
                                          thread_id=thread_id, thread_type=thread_type, ttl=20000)
                else:
                    _reply(client, msg, message_object, thread_id, thread_type, author_id)
            else:
                _reply(client, "🐾 Bạn chưa có pet nào! Dùng `pet roll` để quay pet đầu tiên 💫", message_object, thread_id, thread_type, author_id)
            save_json_safe(PET_FILE, users)
            return

        # ===== ROLL =====
        if sub == "roll":
            new_pet = _get_random_pet()
            user["pets"][new_pet["id"]] = new_pet
            user["equipped"] = new_pet["id"]
            save_json_safe(PET_FILE, users)
            img = _get_pet_image_by_name(new_pet["name"], new_pet["rarity"])
            text = f"🎰 Bạn vừa quay ra {RARITY[new_pet['rarity']]} **{new_pet['name']}**! (đã chọn làm pet chính)"
            if img:
                client.sendLocalImage(imagePath=img, message=Message(text=text),
                                      thread_id=thread_id, thread_type=thread_type, ttl=25000)
            else:
                _reply(client, text, message_object, thread_id, thread_type, author_id)
            return

        # ===== PLAY =====
        if sub == "play":
            eq = user.get("equipped")
            if not eq or eq not in user["pets"]:
                _reply(client, "🐾 Bạn chưa có pet để chơi cùng! Dùng `pet roll` để quay pet.", message_object, thread_id, thread_type, author_id)
                return
            p = user["pets"][eq]
            p["happy"] = min(100, p["happy"] + random.randint(10, 25))
            p["exp"] += random.randint(15, 30)
            if p["exp"] >= 100:
                p["exp"] -= 100
                p["level"] += 1
                text = f"🎮 Bạn chơi với {p['name']}! 💖 Vui lên {p['happy']}%\n⭐ Pet đã lên cấp {p['level']}!"
            else:
                text = f"🎮 Bạn chơi với {p['name']}! 💖 Vui lên {p['happy']}% (EXP: {p['exp']}/100)"
            img = _get_pet_image_by_name(p["name"], p["rarity"])
            save_json_safe(PET_FILE, users)
            if img:
                client.sendLocalImage(imagePath=img, message=Message(text=text),
                                      thread_id=thread_id, thread_type=thread_type, ttl=20000)
            else:
                _reply(client, text, message_object, thread_id, thread_type, author_id)
            return

        # ===== FEED =====
        if sub == "feed":
            eq = user.get("equipped")
            if not eq or eq not in user["pets"]:
                _reply(client, "🐾 Bạn chưa có pet để cho ăn!", message_object, thread_id, thread_type, author_id)
                return
            p = user["pets"][eq]
            p["hunger"] = min(100, p["hunger"] + random.randint(20, 35))
            p["exp"] += random.randint(10, 20)
            if p["exp"] >= 100:
                p["exp"] -= 100
                p["level"] += 1
                text = f"🍗 Bạn cho {p['name']} ăn! No {p['hunger']}%\n⭐ Pet đã lên cấp {p['level']}!"
            else:
                text = f"🍗 {p['name']} đã ăn! No {p['hunger']}% (EXP: {p['exp']}/100)"
            img = _get_pet_image_by_name(p["name"], p["rarity"])
            save_json_safe(PET_FILE, users)
            if img:
                client.sendLocalImage(imagePath=img, message=Message(text=text),
                                      thread_id=thread_id, thread_type=thread_type, ttl=20000)
            else:
                _reply(client, text, message_object, thread_id, thread_type, author_id)
            return
       
               # ===== DANH SÁCH PET =====
        if sub == "list":
            pets = user.get("pets", {})
            if not pets:
                _reply(client, "🐾 Bạn chưa có pet nào!", message_object, thread_id, thread_type, author_id)
                return

            msg_total = f"📜 DANH SÁCH PET CỦA BẠN ({len(pets)}):\n"
            for pid, p in pets.items():
                is_eq = "⭐" if user.get("equipped") == pid else ""
                msg = (f"{is_eq} [{pid}]\n"
                       f"• {RARITY[p['rarity']]} {p['name']}\n"
                       f"⭐ Level: {p['level']} | 💖 {p['happy']}% | 🍗 {p['hunger']}%\n")
                img = _get_pet_image_by_name(p["name"], p["rarity"])
                if img:
                    client.sendLocalImage(imagePath=img, message=Message(text=msg),
                                          thread_id=thread_id, thread_type=thread_type, ttl=25000)
                else:
                    _reply(client, msg, message_object, thread_id, thread_type, author_id)
            return

                                                   
       
        # ===== SET ẢNH PET =====
        if sub == "set":
            if len(parts) < 3:
                _reply(client, "⚠️ Dùng: pet set <common|rare|epic|legendary> [tên_pet]", message_object, thread_id, thread_type, author_id)
                return

            args = parts[2].split(maxsplit=1)
            pet_type = args[0].lower()
            pet_name = args[1].lower() if len(args) > 1 else None

            if pet_type not in RARITY:
                _reply(client, "⚠️ Loại pet không hợp lệ! (common, rare, epic, legendary)", message_object, thread_id, thread_type, author_id)
                return

            if not message_object.quote or not message_object.quote.attach:
                _reply(client, f"📸 Hãy reply vào ảnh bạn muốn đặt cho pet '{pet_type}'{f' ({pet_name})' if pet_name else ''}.", message_object, thread_id, thread_type, author_id)
                return

            try:
                attach_data = json.loads(message_object.quote.attach)
                media_url = attach_data.get('hdUrl') or attach_data.get('href') or attach_data.get('oriUrl')
                if not media_url:
                    _reply(client, "❌ Không tìm thấy URL ảnh.", message_object, thread_id, thread_type, author_id)
                    return
                media_url = urllib.parse.unquote(media_url.replace("\\/", "/"))
                folder = os.path.join(IMG_DIR, pet_type)
                ensure_dir(folder)
                filename = f"{pet_name}.jpg" if pet_name else f"default_{pet_type}.jpg"
                save_path = os.path.join(folder, filename)
                response = requests.get(media_url, stream=True, timeout=10)
                response.raise_for_status()
                with open(save_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                msg = f"✅ Đã đặt ảnh {'riêng cho ' + pet_name if pet_name else 'mặc định cho ' + pet_type}!"
                _reply(client, msg, message_object, thread_id, thread_type, author_id)
            except Exception as e:
                _reply(client, f"⚠️ Lỗi khi tải ảnh: {e}", message_object, thread_id, thread_type, author_id)
            return
            
        # ===== XEM TÚI PHỤ KIỆN =====
        if sub == "bag":
            user = users.get(str(author_id), _init_user(author_id))
            bag = user.get("bag", [])
            if not bag:
                _reply(client, "🎒 Túi của bạn trống trơn!", message_object, thread_id, thread_type, author_id)
                return

            items_data = load_json_safe(ITEMS_FILE, {})
            msg = "🎒 TÚI PHỤ KIỆN CỦA BẠN 🎒\n──────────────────────\n"
            for iid in bag:
                if iid in items_data:
                    info = items_data[iid]
                    msg += f"🆔 {iid} • {info['name']} (+{info['power']}%)\n"
                else:
                    msg += f"🆔 {iid} • (Không rõ thông tin)\n"
            _reply(client, msg.strip(), message_object, thread_id, thread_type, author_id)
            return
            
        # ===== SHOP, EQUIP, ADMIN =====
        if sub == "shop":
            if not shop:
                _reply(client, "🏪 Shop trống, admin dùng `pet addshop` để thêm pet.", message_object, thread_id, thread_type, author_id)
            else:
                msg = "🏪 SHOP PET 🐾\n"
                for sid, item in shop.items():
                    msg += f"• ID: {sid} | {RARITY[item['rarity']]} {item['name']} - 💰 {item['price']} xu\n"
                _reply(client, msg, message_object, thread_id, thread_type, author_id)
            return

        if sub == "buy":
            if not arg or arg not in shop:
                _reply(client, "⚠️ Dùng: pet buy <id>", message_object, thread_id, thread_type, author_id)
                return
            item = shop[arg]
            if user["coin"] < item["price"]:
                _reply(client, "💸 Không đủ xu để mua!", message_object, thread_id, thread_type, author_id)
                return
            user["coin"] -= item["price"]
            new_pet = _init_pet(item["id"], item["name"], item["rarity"])
            user["pets"][new_pet["id"]] = new_pet
            save_json_safe(PET_FILE, users)
            img = _get_pet_image_by_name(item["name"], item["rarity"])
            text = f"✅ Mua thành công {RARITY[item['rarity']]} {item['name']}!"
            if img:
                client.sendLocalImage(imagePath=img, message=Message(text=text),
                                      thread_id=thread_id, thread_type=thread_type, ttl=25000)
            else:
                _reply(client, text, message_object, thread_id, thread_type, author_id)
            return

        if sub == "equip":
            if not arg or arg not in user["pets"]:
                _reply(client, "⚠️ Dùng: pet equip <id>", message_object, thread_id, thread_type, author_id)
                return
            user["equipped"] = arg
            save_json_safe(PET_FILE, users)
            pet = user["pets"][arg]
            img = _get_pet_image_by_name(pet["name"], pet["rarity"])
            text = f"🐾 Đã chọn {pet['name']} làm pet chính!"
            if img:
                client.sendLocalImage(imagePath=img, message=Message(text=text),
                                      thread_id=thread_id, thread_type=thread_type, ttl=20000)
            else:
                _reply(client, text, message_object, thread_id, thread_type, author_id)
            return

        if sub == "nap":
            if not _is_admin(author_id):
                _reply(client, "🚫 Chỉ admin mới được phép nạp xu cho người khác.", message_object, thread_id, thread_type, author_id)
                return

            if not message_object.mentions or not arg:
                _reply(client, "⚠️ Dùng: pet nap @user <số_xu>", message_object, thread_id, thread_type, author_id)
                return

        if sub == "addshop":
            if not _is_admin(author_id):
                _reply(client, "🚫 Chỉ admin được thêm pet.", message_object, thread_id, thread_type, author_id)
                return
            new_id = f"shop_{int(time.time())}"
            rarity = random.choice(list(RARITY.keys()))
            name = f"Pet Đặc Biệt {random.randint(1,999)}"
            price = random.randint(100, 500)
            shop[new_id] = {"id": new_id, "name": name, "price": price, "rarity": rarity}
            save_json_safe(SHOP_FILE, shop)
            _reply(client, f"🛒 Đã thêm {RARITY[rarity]} {name} vào shop ({price} xu).", message_object, thread_id, thread_type, author_id)
            return

        if sub == "reset":
            if not _is_admin(author_id):
                _reply(client, "🚫 Chỉ admin được reset.", message_object, message_object, thread_id, thread_type, author_id)
                return
            save_json_safe(PET_FILE, {})
            _reply(client, "✅ Đã reset toàn bộ dữ liệu PET!", message_object, thread_id, thread_type, author_id)
            return

        _reply(client, "⚠️ Sai cú pháp. Gõ `pet menu` để xem danh sách lệnh.", message_object, thread_id, thread_type, author_id)

    except Exception as e:
        _reply(client, f"⚠️ Lỗi trong pet system: {e}", message_object, thread_id, thread_type, author_id)

def PTA():
    return {"pet": handle_pet_command}