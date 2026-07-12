import os
import random
import json
from PIL import Image, ImageDraw, ImageFont
from zlapi.models import Message, MultiMsgStyle, MessageStyle

des = {
    'version': "1.1.0",
    'credits': "ngbao",
    'description': "Game thám hiểm nhà ma có ảnh minh họa cho từng phòng.",
    'power': "Thành Viên"
}

GAME_DATA_PATH = "modules/data/ghost_game/"
IMAGE_PATH = os.path.join(GAME_DATA_PATH, "room_images/")
os.makedirs(IMAGE_PATH, exist_ok=True)

# =================== DỮ LIỆU PHÒNG ===================
rooms = {
    "sảnh chính": {"desc": "Bạn đang ở sảnh chính lạnh lẽo của ngôi nhà ma...", "north": "phòng khách", "east": "phòng ăn"},
    "phòng khách": {"desc": "Chiếc đèn chập chờn... Có gì đó di chuyển trong bóng tối.", "south": "sảnh chính", "north": "phòng kho", "item": "đèn pin"},
    "phòng ăn": {"desc": "Bàn ăn phủ đầy bụi, tiếng thì thầm vang vọng...", "west": "sảnh chính", "north": "phòng ngủ"},
    "phòng ngủ": {"desc": "Giường cũ nát, có ánh sáng yếu lóe lên dưới gối...", "south": "phòng ăn", "item": "bùa hộ mệnh"},
    "phòng kho": {"desc": "Kho đầy mạng nhện, có tiếng bước chân sau lưng bạn...", "south": "phòng khách", "east": "phòng bí mật"},
    "phòng bí mật": {"desc": "Một căn phòng tối om... có cánh cửa sắt khóa chặt ở góc.", "west": "phòng kho", "item": "chìa khóa"},
    "cửa thoát hiểm": {"desc": "Ánh sáng chiếu vào! Đây là lối thoát cuối cùng!"}
}

ghost_rooms = ["phòng ăn", "phòng kho"]

# =================== TIỆN ÍCH ===================
def _reply_styled_message(client, message_content, message_object, thread_id, thread_type, author_id):
    try:
        user_info = client.fetchUserInfo(author_id)
        author_name = user_info.changed_profiles.get(str(author_id), {}).get('zaloName', 'Không xác định') if user_info and user_info.changed_profiles else 'Không xác định'
    except Exception:
        author_name = "Người chơi"
    msg = f"{author_name}\n➜ {message_content}"
    styles = MultiMsgStyle([
        MessageStyle(offset=0, length=len(author_name), style="color", color="#db342e", auto_format=False),
        MessageStyle(offset=0, length=len(author_name), style="bold", auto_format=False)
    ])
    client.replyMessage(Message(text=msg, style=styles), message_object, thread_id=thread_id, thread_type=thread_type, ttl=12000)

def _get_save_path(author_id):
    return os.path.join(GAME_DATA_PATH, f"{author_id}.json")

def _load_progress(author_id):
    path = _get_save_path(author_id)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"current_room": "sảnh chính", "inventory": []}

def _save_progress(author_id, data):
    with open(_get_save_path(author_id), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def _generate_room_image(room_name, desc):
    """Tự tạo ảnh minh họa cho phòng"""
    img = Image.new("RGB", (1080, 720), (15, 15, 15))
    draw = ImageDraw.Draw(img)
    try:
        font_path = "arial.ttf"
        font_big = ImageFont.truetype(font_path, 80)
        font_small = ImageFont.truetype(font_path, 36)
    except:
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()

    draw.text((100, 100), f"👻 {room_name.upper()} 👻", fill=(220, 20, 60), font=font_big)
    draw.text((100, 250), desc[:200] + "...", fill=(240, 240, 240), font=font_small)
    draw.text((100, 600), "© Ghost Adventure", fill=(100, 100, 100), font=font_small)

    save_path = os.path.join(IMAGE_PATH, f"{room_name.replace(' ', '_')}.jpg")
    img.save(save_path)
    return save_path

# =================== XỬ LÝ GAME ===================
def handle_ma_command(message, message_object, thread_id, thread_type, author_id, client):
    args = message.strip().split(maxsplit=1)
    sub_cmd = args[1].lower() if len(args) > 1 else "bắt đầu"

    progress = _load_progress(author_id)
    room = progress["current_room"]
    inventory = progress["inventory"]

    # BẮT ĐẦU
    if sub_cmd == "go":
        _reply_styled_message(client, "🎮 Bắt đầu trò chơi thám hiểm NGÔI NHÀ MA!\nDùng:\n- `ma đi <hướng>`\n- `ma xem`\n- `ma thoát`", message_object, thread_id, thread_type, author_id)
        _save_progress(author_id, progress)
        return

    # XEM TRẠNG THÁI
    elif sub_cmd.startswith("xem"):
        desc = rooms[room]["desc"]
        inv = ", ".join(inventory) if inventory else "Trống rỗng"
        img_path = _generate_room_image(room, desc)
        try:
            client.sendLocalImage(
                imagePath=img_path,
                message=Message(text=f"📍 {room.upper()}\n{desc}\n🎒 Túi đồ: {inv}"),
                thread_id=thread_id,
                thread_type=thread_type,
                width=1080, height=720, ttl=30000
            )
        except Exception as e:
            _reply_styled_message(client, f"Lỗi gửi ảnh: {e}", message_object, thread_id, thread_type, author_id)
        return

    # ĐI HƯỚNG
    elif sub_cmd.startswith("đi"):
        direction = sub_cmd.replace("đi", "").strip().lower()
        if direction not in rooms[room]:
            _reply_styled_message(client, "🚫 Không thể đi hướng đó!", message_object, thread_id, thread_type, author_id)
            return

        next_room = rooms[room][direction]
        progress["current_room"] = next_room
        _save_progress(author_id, progress)

        # Gặp ma
        if next_room in ghost_rooms:
            if "bùa hộ mệnh" in inventory:
                _reply_styled_message(client, f"😱 Bạn gặp MA ở {next_room}! Nhưng bùa hộ mệnh phát sáng, con ma biến mất!", message_object, thread_id, thread_type, author_id)
                ghost_rooms.remove(next_room)
            else:
                _reply_styled_message(client, f"👻 Ma trong {next_room} đã bắt bạn! Trò chơi kết thúc!", message_object, thread_id, thread_type, author_id)
                os.remove(_get_save_path(author_id))
                return

        # Cửa thoát
        if next_room == "cửa thoát hiểm":
            if "chìa khóa" in inventory:
                _reply_styled_message(client, "🌕 Bạn mở cửa và THOÁT KHỎI NGÔI NHÀ MA!", message_object, thread_id, thread_type, author_id)
                os.remove(_get_save_path(author_id))
                return
            else:
                _reply_styled_message(client, "🚪 Cửa bị khóa, bạn cần chìa khóa!", message_object, thread_id, thread_type, author_id)
                return

        # Nhặt đồ
        item = rooms[next_room].get("item")
        if item and item not in inventory:
            inventory.append(item)
            progress["inventory"] = inventory
            _save_progress(author_id, progress)
            msg = f"📦 Bạn đã tìm thấy {item} trong {next_room}!"
        else:
            msg = f"🚶 Bạn đi đến {next_room}."

        img_path = _generate_room_image(next_room, rooms[next_room]["desc"])
        try:
            client.sendLocalImage(
                imagePath=img_path,
                message=Message(text=msg + f"\n\n{rooms[next_room]['desc']}"),
                thread_id=thread_id,
                thread_type=thread_type,
                width=1080, height=720, ttl=40000
            )
        except Exception as e:
            _reply_styled_message(client, f"Lỗi gửi ảnh: {e}", message_object, thread_id, thread_type, author_id)
        return

    # THOÁT GAME
    elif sub_cmd == "thoát":
        if os.path.exists(_get_save_path(author_id)):
            os.remove(_get_save_path(author_id))
        _reply_styled_message(client, "👋 Bạn đã rời khỏi ngôi nhà ma.", message_object, thread_id, thread_type, author_id)
        return

    # HƯỚNG DẪN
    else:
        _reply_styled_message(client, "📖 Lệnh hợp lệ:\n- `ma bắt đầu`\n- `ma đi <north/south/east/west>`\n- `ma xem`\n- `ma thoát`", message_object, thread_id, thread_type, author_id)
        return

def PTA():
    return {'ma': handle_ma_command}
