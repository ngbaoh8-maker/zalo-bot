# -*- coding: UTF-8 -*-
import time
import threading
from zlapi.models import Message, MultiMsgStyle, MessageStyle
from config import ADMIN, PREFIX

# ====== MÔ TẢ MODULE ======
des = {
    'version': "1.1.2",
    'credits': "ngbao",
    'description': "Spam sticker",
    'power': "Quản trị viên Bot"
}

# ====== BIẾN TRẠNG THÁI ======
is_spamstk_running = False


# ====== HÀM GỬI TIN NHẮN CÓ STYLE (TAG ĐỎ ĐẬM) ======
def styled_reply(client, name, rest_text, message_object, thread_id, thread_type, ttl=180000):
    """Gửi tin nhắn với dòng đầu là tag đỏ đậm, dòng sau là nội dung"""
    msg = f"{name}\n➜ {rest_text}"
    styled_msg = Message(
        text=msg,
        style=MultiMsgStyle([
            MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(name), style="bold", auto_format=False)
        ])
    )
    client.replyMessage(styled_msg, message_object, thread_id, thread_type, ttl=ttl)


# ====== HÀM DỪNG SPAM ======
def stop_spamstk(client, message_object, thread_id, thread_type, name):
    global is_spamstk_running
    is_spamstk_running = False
    styled_reply(client, name, "🛑 Đã dừng spam sticker.", message_object, thread_id, thread_type)


# ====== HÀM CHÍNH XỬ LÝ LỆNH ======
def handle_spamstk_command(message, message_object, thread_id, thread_type, author_id, client):
    global is_spamstk_running

    # 🧩 Lấy tên người gọi lệnh
    try:
        user_info = client.fetchUserInfo(author_id)
        author_info = user_info.changed_profiles.get(str(author_id), {}) if user_info and user_info.changed_profiles else {}
        name = author_info.get('zaloName', 'Không xác định')
    except Exception:
        name = "Không xác định"

    # 🛑 Kiểm tra quyền admin
    if str(author_id) not in ADMIN:
        styled_reply(client, name, "🚫 Bạn không có quyền sử dụng lệnh này!", message_object, thread_id, thread_type)
        return

    # 🧩 Xử lý cú pháp
    parts = message.split()
    if len(parts) < 2:
        styled_reply(client, name, f"⚙️ Cách dùng:\n{PREFIX}spamstk on\n{PREFIX}spamstk off",
                     message_object, thread_id, thread_type)
        return

    action = parts[1].lower()

    # 🛑 Dừng spam
    if action == "off":
        if not is_spamstk_running:
            styled_reply(client, name, "⚠️ Spam sticker đã dừng trước đó.", message_object, thread_id, thread_type)
        else:
            stop_spamstk(client, message_object, thread_id, thread_type, name)
        return

    # ✅ Bắt đầu spam
    if action == "on":
        is_spamstk_running = True
        styled_reply(client, name, "✅ Bắt đầu spam sticker...", message_object, thread_id, thread_type)

        def spamstk_loop():
            while is_spamstk_running:
                try:
                    client.sendSticker(
                        stickerType=7,
                        stickerId=23339,
                        cateId=10425,
                        thread_id=thread_id,
                        thread_type=thread_type
                    )
                    time.sleep(0.2)
                except Exception:
                    pass

        threading.Thread(target=spamstk_loop, daemon=True).start()
        return

    # ⚠️ Nếu không hợp lệ
    styled_reply(client, name, f"⚠️ Lệnh không hợp lệ, dùng:\n{PREFIX}spamstk on/off",
                 message_object, thread_id, thread_type)


# ====== ĐĂNG KÝ MODULE ======
def PTA():
    return {
        'spamstk': handle_spamstk_command
    }