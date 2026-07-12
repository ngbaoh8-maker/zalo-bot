import time
import threading
from zlapi.models import Message, MultiMsgStyle, MessageStyle
from config import ADMIN, PREFIX

des = {
    'version': "1.1.5",
    'credits': "ngbao",
    'description': "Ẩn kick + mời lại nhiều lần, tự động hiển thị tên người dùng lệnh.",
    'power': "Admin"
}

ADMIN_ID = ADMIN


def is_admin(author_id):
    return str(author_id) == ADMIN_ID


def handle_them_command(message, message_object, thread_id, thread_type, author_id, client):
    # --- Lấy tên người dùng lệnh ---
    user_info = client.fetchUserInfo(author_id)
    zalo_name = "Không xác định"
    if user_info and hasattr(user_info, "changed_profiles") and user_info.changed_profiles:
        zalo_name = user_info.changed_profiles.get(str(author_id), {}).get("zaloName", "Không xác định")

    # --- Nếu không phải admin ---
    if not is_admin(author_id):
        rest_text = "❌ Bạn không có quyền dùng lệnh này!"
        msg = f"{zalo_name}\n➜ {rest_text}"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(zalo_name), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(zalo_name), style="bold", auto_format=False),
        ])
        client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=6000)
        return

    # --- Phân tích lệnh ---
    args = message.strip().split()
    if len(args) < 2:
        rest_text = f"Dùng lệnh:\n{PREFIX}them <số_lần> [@tag / reply / UID]"
        msg = f"{zalo_name}\n➜ {rest_text}"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(zalo_name), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(zalo_name), style="bold", auto_format=False),
        ])
        client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=10000)
        return

    # --- Lấy số lần ---
    try:
        repeat_count = int(args[1])
        if repeat_count < 1:
            repeat_count = 1
        elif repeat_count > 30:
            repeat_count = 30
    except ValueError:
        rest_text = "⚠️ Vui lòng nhập số lần hợp lệ!"
        msg = f"{zalo_name}\n➜ {rest_text}"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(zalo_name), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(zalo_name), style="bold", auto_format=False),
        ])
        client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=7000)
        return

    # --- Xác định user bị kick ---
    user_id = None
    if getattr(message_object, "quote", None):
        user_id = str(message_object.quote.ownerId)
    elif getattr(message_object, "mentions", None) and message_object.mentions:
        user_id = str(message_object.mentions[0]["uid"])
    elif len(args) >= 3:
        user_id = args[2]

    if not user_id:
        rest_text = "⚠️ Hãy reply, tag hoặc nhập UID để chọn người!"
        msg = f"{zalo_name}\n➜ {rest_text}"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(zalo_name), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(zalo_name), style="bold", auto_format=False),
        ])
        client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=7000)
        return

    # --- Chạy ẩn (không gửi thông báo kick/mời) ---
    def run_them():
        for _ in range(repeat_count):
            try:
                client.kickUsersInGroup(user_id, thread_id)
                time.sleep(0.3)
                client.addUsersToGroup(user_id, thread_id)
                time.sleep(0.3)
            except Exception:
                pass

    threading.Thread(target=run_them, daemon=True).start()


# ================== CHUẨN CHO BOT PTA ==================
def PTA():
    return {
        'them': handle_them_command
    }
