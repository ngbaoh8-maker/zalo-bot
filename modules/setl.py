import json
import os
import threading
import time
from datetime import datetime
from zlapi.models import Message

LOVE_FILE = "modules/cache/love.json"
TTL_SECONDS = 300  # 5 phút

def load_love_data():
    if not os.path.exists(LOVE_FILE):
        return {}
    try:
        with open(LOVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_love_data(data):
    os.makedirs(os.path.dirname(LOVE_FILE), exist_ok=True)
    with open(LOVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_zalo_name(client, user_id, default="Không rõ"):
    try:
        info = client.fetchUserInfo(user_id)
        if info and hasattr(info, "changed_profiles"):
            return info.changed_profiles.get(str(user_id), {}).get("zaloName", default)
        return default
    except Exception:
        return default

# Hàm gửi tin nhắn + thu hồi sau TTL
def send_ttl_message(client, message_text, message_object, thread_id, thread_type):
    msg = client.replyMessage(
        Message(text=message_text),
        message_object, thread_id=thread_id, thread_type=thread_type
    )

    # Chạy luồng tự động thu hồi
    def delete_after_ttl(msg_id):
        time.sleep(TTL_SECONDS)
        try:
            client.unsendMessage(msg_id)
        except Exception:
            pass

    threading.Thread(target=delete_after_ttl, args=(msg.message_id,), daemon=True).start()

def setlove_cmd(message, message_object, thread_id, thread_type, author_id, client):
    text = message.strip().split()
    love_data = load_love_data()
    author_id = str(author_id)

    def get_target_id():
        if hasattr(message_object, "mentions") and message_object.mentions:
            return str(message_object.mentions[0])
        return None

    # 1️⃣ SET LOVE
    if len(text) >= 2 and text[1].startswith("@"):
        target_id = get_target_id()
        if not target_id:
            send_ttl_message(client, "❌ Không tìm thấy người được tag. Hãy dùng @Tên người nha 💞",
                             message_object, thread_id, thread_type)
            return

        today = datetime.now().strftime("%Y-%m-%d")
        love_data[author_id] = {"partner_id": target_id, "start_date": today}
        save_love_data(love_data)

        author_name = get_zalo_name(client, author_id, "Bạn")
        partner_name = get_zalo_name(client, target_id, "Người được tag")

        send_ttl_message(client, f"💞 {author_name} đã set love với {partner_name} rồi nha 💖",
                         message_object, thread_id, thread_type)
        return

    # 2️⃣ CHECK LOVE
    if len(text) >= 2 and text[1].lower() == "check":
        if len(text) == 3 and text[2].startswith("@"):
            target_id = get_target_id()
            if not target_id:
                send_ttl_message(client, "❌ Không tìm thấy người được tag để check.",
                                 message_object, thread_id, thread_type)
                return

            if author_id not in love_data or love_data[author_id]["partner_id"] != target_id:
                send_ttl_message(client, "💔 Bạn chưa set love với người này.",
                                 message_object, thread_id, thread_type)
                return

            info = love_data[author_id]
            start = datetime.strptime(info["start_date"], "%Y-%m-%d")
            days = (datetime.now() - start).days
            partner_name = get_zalo_name(client, target_id, "Người ấy")

            send_ttl_message(client, f"💘 Bạn và {partner_name} đã yêu nhau được {days} ngày rồi 💞",
                             message_object, thread_id, thread_type)
            return

        if author_id not in love_data:
            send_ttl_message(client, "❌ Bạn chưa có người yêu để check 🥲",
                             message_object, thread_id, thread_type)
            return

        info = love_data[author_id]
        start = datetime.strptime(info["start_date"], "%Y-%m-%d")
        days = (datetime.now() - start).days
        partner_id = info["partner_id"]
        partner_name = get_zalo_name(client, partner_id, "Người yêu của bạn")

        send_ttl_message(client, f"💘 Bạn đã set love với {partner_name} được {days} ngày rồi 💞",
                         message_object, thread_id, thread_type)
        return

    # 3️⃣ DANH SÁCH LOVE
    if len(text) >= 2 and text[1].lower() == "list":
        if not love_data:
            send_ttl_message(client, "📭 Chưa có ai set love hết 😅",
                             message_object, thread_id, thread_type)
            return

        lines = ["💖 Danh sách các set love:"]
        for uid, info in love_data.items():
            if uid == author_id:
                partner_name = get_zalo_name(client, info["partner_id"], "Người yêu của bạn")
                lines.append(f"• Bạn đang set love với {partner_name} từ {info['start_date']}")
        if len(lines) == 1:
            lines.append("❌ Bạn chưa set love với ai hết.")
        send_ttl_message(client, "\n".join(lines), message_object, thread_id, thread_type)
        return

    # 4️⃣ XOÁ LOVE
    if len(text) >= 2 and text[1].lower() == "remove":
        target_id = get_target_id()
        if not target_id:
            send_ttl_message(client, "❌ Hãy tag người cần xoá set love 💔",
                             message_object, thread_id, thread_type)
            return

        target_id = str(target_id)
        if author_id in love_data and love_data[author_id]["partner_id"] == target_id:
            del love_data[author_id]
            save_love_data(love_data)
            send_ttl_message(client, f"💔 Bạn đã xoá set love với {get_zalo_name(client, target_id, 'người đó')}",
                             message_object, thread_id, thread_type)
            return

        send_ttl_message(client, "❌ Bạn chưa set love với người này để xoá.",
                         message_object, thread_id, thread_type)
        return

    # 5️⃣ SỬA NGÀY
    if len(text) >= 3 and text[1].lower() == "suangay":
        new_date = text[2]
        try:
            datetime.strptime(new_date, "%Y-%m-%d")
        except ValueError:
            send_ttl_message(client, "❌ Định dạng ngày không hợp lệ! Dùng: YYYY-MM-DD",
                             message_object, thread_id, thread_type)
            return

        if author_id not in love_data:
            send_ttl_message(client, "❌ Bạn chưa có người yêu để sửa ngày 🥲",
                             message_object, thread_id, thread_type)
            return

        love_data[author_id]["start_date"] = new_date
        save_love_data(love_data)
        send_ttl_message(client, f"🗓 Đã cập nhật ngày yêu thành: {new_date} 💕",
                         message_object, thread_id, thread_type)
        return

    # 6️⃣ HƯỚNG DẪN
    send_ttl_message(client, (
        " ➜ 🍧 Lệnh setlove:\n"
        "• !setl @user ➜ Setlove Với Người Được Tag\n"
        " ━━━━━━━━━━━━━━━━━━━━━\n"
        "• !setl check ➜ Xem Xem Người Yêu Hiện Tại\n"
        " ━━━━━━━━━━━━━━━━━━━━━\n"
        "• !setl check @user ➜ Kiểm Tra Cụ Thể Với Ai Đó\n"
        " ━━━━━━━━━━━━━━━━━━━━━\n"
        "• !setl list ➜ Xem Danh Sách Bạn Đã Set Love\n"
        " ━━━━━━━━━━━━━━━━━━━━━\n"
        "• !setl remove @user ➜ Xoá Set Love Với Người Người Được Tag\n"
        " ━━━━━━━━━━━━━━━━━━━━━\n"
        "• !setl suangay YYYY-MM-DD ➜ Sửa Ngày Yêu\n"
        " ━━━━━━━━━━━━━━━━━━━━━\n"
    ), message_object, thread_id, thread_type)

def PTA():
    return {"setl": setlove_cmd}

des = {
    "version": "2.0",
    "credits": "ngbao",
    "description": "Setlove Với Người Được Tag",
    "power": "Admin"
}