import datetime
import os
import subprocess
import logging
from zlapi.models import Message, MultiMsgStyle, MessageStyle
from config import ADMIN

# --- Cấu hình ---
des = {
    'version': "1.1.0",
    'credits': "ngbao",
    'description': "Spam SMS/Call (Bản nâng cấp an toàn)",
    'power': "Thành viên"
}

# Danh sách số điện thoại được bảo vệ
BLACKLIST = ['113', '911', '114', '115', '0789305260']
DEFAULT_COOLDOWN = 120 # giây

def handle_sms_command(message, message_object, thread_id, thread_type, author_id, client):
    # Khởi tạo dict lưu cooldown trên client nếu chưa có
    if not hasattr(client, "last_sms_times"):
        client.last_sms_times = {}

    parts = message.split()
    if len(parts) < 2:
        msg = "🚫 [ HDSD SMS ] 🚫\n" + "━" * 15 + "\n👉 Cú pháp: .sms [SĐT]\n👉 Ví dụ: .sms 0987654321"
        return client.replyMessage(Message(text=msg), message_object, thread_id, thread_type)

    phone_number = parts[1].strip()

    # 1. Kiểm tra định dạng SĐT (10 số)
    if not phone_number.isdigit() or len(phone_number) != 10:
        return client.replyMessage(Message(text='❌ Số điện thoại phải là 10 chữ số!'), message_object, thread_id, thread_type)

    # 2. Kiểm tra danh sách đen
    if phone_number in BLACKLIST:
        return client.replyMessage(Message(text="⛔ Không thể tấn công số điện thoại công vụ hoặc VIP!"), message_object, thread_id, thread_type)

    # 3. Kiểm tra Cooldown (Bỏ qua nếu là Admin Bot)
    current_time = datetime.datetime.now()
    if str(author_id) not in ADMIN:
        last_sent = client.last_sms_times.get(author_id)
        if last_sent:
            elapsed = (current_time - last_sent).total_seconds()
            if elapsed < DEFAULT_COOLDOWN:
                wait = int(DEFAULT_COOLDOWN - elapsed)
                return client.replyMessage(Message(text=f"⏳ Chậm lại nào! Vui lòng đợi {wait} giây."), message_object, thread_id, thread_type)

    # 4. Thực thi file script spam
    script_path = os.path.join(os.getcwd(), "smsv2.py")
    if not os.path.exists(script_path):
        return client.replyMessage(Message(text="❌ Lỗi: Hệ thống thiếu file xử lý 'smsv2.py'."), message_object, thread_id, thread_type)

    try:
        # Lưu thời gian gửi
        client.last_sms_times[author_id] = current_time
        
        # Chạy script Python bên ngoài một cách an toàn
        # Shell=False ngăn chặn tấn công chèn lệnh hệ thống
        subprocess.Popen(["python", script_path, phone_number, "7"], shell=False)

        # 5. Phản hồi người dùng
        time_str = current_time.strftime("%H:%M:%S - %d/%m/%Y")
        masked_phone = f"{phone_number[:3]}***{phone_number[-3:]}"
        
        res_msg = (
            "🔥 [ KÍCH HOẠT SPAM ] 🔥\n"
            "━━━━━━━━━━━━━\n"
            f"📱 Mục tiêu: {masked_phone}\n"
            f"⏰ Lúc: {time_str}\n"
            f"⏳ Cooldown: {DEFAULT_COOLDOWN}s\n"
            f"👤 Người thực hiện: {author_id}\n"
            "━━━━━━━━━━━━━\n"
            "💬 Trạng thái: Đang gửi yêu cầu..."
        )
        
        client.replyMessage(Message(text=res_msg), message_object, thread_id, thread_type)

    except Exception as e:
        logging.error(f"Lỗi SMS: {str(e)}")
        client.replyMessage(Message(text="❌ Đã xảy ra lỗi khi khởi chạy script."), message_object, thread_id, thread_type)

def PTA():
    return {'spamsms': handle_sms_command}