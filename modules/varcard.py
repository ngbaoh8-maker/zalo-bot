# -*- coding: UTF-8 -*-
import os
import time
import threading
from zlapi.models import Message, MultiMsgStyle, MessageStyle
from config import ADMIN

# ==============================
# THÔNG TIN MODULE
# ==============================
des = {
    'version': "1.0.3",
    'credits': "ngbao",
    'description': "Gửi danh thiếp với nội dung trong file noidung.txt + tag người dùng",
    'power': "Quản trị viên Bot"
}

is_reo_running = False


# ==============================
# HÀM GỬI TIN CÓ STYLE (tên đỏ)
# ==============================
def send_styled_message(author_id, text, message_object, thread_id, thread_type, client):
    try:
        user_info = client.fetchUserInfo(author_id)
        user_name = user_info.changed_profiles.get(str(author_id), {}).get("zaloName", "Người dùng")

        msg = f"{user_name}\n➜ {text}"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(user_name), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(user_name), style="bold", auto_format=False)
        ])
        message_to_send = Message(text=msg, style=styles)
        client.replyMessage(message_to_send, message_object, thread_id, thread_type, ttl=10000)
    except Exception as e:
        print(f"Lỗi khi gửi styled message: {e}")


# ==============================
# HÀM DỪNG GỬI
# ==============================
def stop_reo(client, message_object, thread_id, thread_type, author_id):
    global is_reo_running
    is_reo_running = False
    send_styled_message(author_id, "✅ Đã dừng gửi danh thiếp.", message_object, thread_id, thread_type, client)


# ==============================
# HÀM CHÍNH
# ==============================
def handle_cardinfo_command(message, message_object, thread_id, thread_type, author_id, client):
    global is_reo_running

    # Kiểm tra quyền admin
    if str(author_id) not in ADMIN:
        send_styled_message(author_id, "⛔ Bạn không có quyền sử dụng lệnh này", message_object, thread_id, thread_type, client)
        return

    command_parts = message.split()
    if len(command_parts) < 2:
        send_styled_message(author_id, "❗ Vui lòng dùng cú pháp:\n👉 varcard on hoặc varcard stop", message_object, thread_id, thread_type, client)
        return

    action = command_parts[1].lower()

    if action == "stop":
        if not is_reo_running:
            send_styled_message(author_id, "⚠️ Hiện không có tiến trình gửi danh thiếp nào đang chạy", message_object, thread_id, thread_type, client)
        else:
            stop_reo(client, message_object, thread_id, thread_type, author_id)
        return

    if action != "on":
        send_styled_message(author_id, "❗ Lệnh không hợp lệ, vui lòng dùng:\n👉 varcard on hoặc varcard stop", message_object, thread_id, thread_type, client)
        return

    # Lấy người được tag
    if message_object.mentions:
        tagged_user = message_object.mentions[0]['uid']
    else:
        send_styled_message(author_id, "❗ Vui lòng tag người cần gửi danh thiếp", message_object, thread_id, thread_type, client)
        return

    # Đọc nội dung từ file
    try:
        with open("noidung.txt", "r", encoding="utf-8") as file:
            contents = file.readlines()
    except FileNotFoundError:
        send_styled_message(author_id, "❌ Không tìm thấy file noidung.txt.", message_object, thread_id, thread_type, client)
        return

    if not contents:
        send_styled_message(author_id, "⚠️ File noidung.txt không có nội dung nào để gửi", message_object, thread_id, thread_type, client)
        return

    is_reo_running = True
    send_styled_message(author_id, f"🚀 Bắt đầu gửi danh thiếp cho người được tag", message_object, thread_id, thread_type, client)

    def card_loop():
        global is_reo_running
        for content in contents:
            if not is_reo_running:
                break
            try:
                user_info = client.fetchUserInfo(tagged_user).changed_profiles.get(tagged_user)
                avatarUrl = user_info.avatar if user_info else None

                if not avatarUrl:
                    send_styled_message(author_id, "⚠️ Không tìm thấy ảnh đại diện của người dùng", message_object, thread_id, thread_type, client)
                    continue

                client.sendBusinessCard(
                    userId=tagged_user,
                    phone=content.strip(),
                    qrCodeUrl=avatarUrl,
                    thread_id=thread_id,
                    thread_type=thread_type
                )
                time.sleep(0.1)

            except Exception as e:
                print(f"Lỗi khi gửi danh thiếp: {e}")
                send_styled_message(author_id, "⚠️ Đã xảy ra lỗi khi gửi danh thiếp", message_object, thread_id, thread_type, client)
                break

        send_styled_message(author_id, "✅ Hoàn thành gửi danh thiếp", message_object, thread_id, thread_type, client)

    threading.Thread(target=card_loop).start()


# ==============================
# ĐĂNG KÝ LỆNH
# ==============================
def PTA():
    return {
        "varcard": handle_cardinfo_command
    }