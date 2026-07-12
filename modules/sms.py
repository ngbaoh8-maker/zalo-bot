import datetime
import os
import subprocess
import threading
from zlapi.models import Message, MultiMsgStyle, MessageStyle
import logging

# --- Cấu hình ---
des = {
    'version': "2.0.0",
    'credits': "ngbao",
    'description': "Spam SMS/Call - Hệ thống quản lý cooldown an toàn",
    'power': "Thành viên"
}

# Danh sách số điện thoại không được phép tấn công (Admin/Cảnh sát)
BLACKLIST = ['113', '114', '115', '911', '0789305260']
COOLDOWN_TIME = 120 # giây

def handle_sms_command(message, message_object, thread_id, thread_type, author_id, client):
    parts = message.split()

    if len(parts) < 2:
        return client.replyMessage(
            Message(text='🚫 Vui lòng nhập số điện thoại!\nCú pháp: .sms [Số điện thoại]'),
            message_object, thread_id, thread_type
        )

    phone_number = parts[1].strip()

    # 1. Kiểm tra định dạng số điện thoại
    if not phone_number.isdigit() or len(phone_number) < 10 or len(phone_number) > 11:
        return client.replyMessage(
            Message(text='❌ Số điện thoại không hợp lệ!'),
            message_object, thread_id, thread_type
        )

    # 2. Kiểm tra danh sách đen
    if phone_number in BLACKLIST:
        return client.replyMessage(
            Message(text="⛔ Số điện thoại này nằm trong danh sách bảo vệ!"),
            message_object, thread_id, thread_type
        )

    # 3. Kiểm tra Cooldown (Thời gian chờ)
    if not hasattr(client, 'last_sms_times'):
        client.last_sms_times = {}

    current_time = datetime.datetime.now()
    if author_id in client.last_sms_times:
        last_sent = client.last_sms_times[author_id]
        elapsed = (current_time - last_sent).total_seconds()
        
        if elapsed < COOLDOWN_TIME:
            wait_time = int(COOLDOWN_TIME - elapsed)
            return client.replyMessage(
                Message(text=f"⏳ Cooldown: Vui lòng đợi {wait_time} giây để tiếp tục."),
                message_object, thread_id, thread_type
            )

    # 4. Thực thi lệnh Spam
    file_path = os.path.join(os.getcwd(), "smsv2.py")
    if not os.path.exists(file_path):
        return client.replyMessage(
            Message(text="❌ Không tìm thấy file thực thi smsv2.py trên hệ thống!"),
            message_object, thread_id, thread_type
        )

    try:
        # Cập nhật thời gian gửi cuối cùng
        client.last_sms_times[author_id] = current_time
        
        # Chạy script spam ngầm (không làm treo bot)
        # Sử dụng shell=False để bảo mật
        subprocess.Popen(["python", file_path, phone_number, "7"], shell=False)

        # 5. Thông báo kết quả
        masked_phone = f"{phone_number[:3]}***{phone_number[-3:]}"
        time_str = current_time.strftime("%H:%M:%S - %d/%m/%Y")
        
        response_text = (
            "🚀 [ TRẠNG THÁI ATTACK ] 🚀\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"📱 Mục tiêu: {masked_phone}\n"
            f"⏰ Bắt đầu: {time_str}\n"
            f"⏳ Chờ: {COOLDOWN_TIME}s\n"
            f"👤 Người dùng: {author_id}\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "⚠️ Lưu ý: Hành vi phá hoại có thể bị khóa tài khoản."
        )

        client.replyMessage(
            Message(text=response_text),
            message_object, thread_id, thread_type
        )

    except Exception as e:
        logging.error(f"Lỗi SMS: {e}")
        client.replyMessage(Message(text=f"❌ Lỗi hệ thống: {str(e)}"), message_object, thread_id, thread_type)

def PTA():
    return {'sms': handle_sms_command}