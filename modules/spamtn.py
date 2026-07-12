from zlapi.models import *
import os
import time
import threading
from config import ADMIN

is_war_running = False

des = {
    'version': "1.0.2",
    'credits': "ngbao",
    'description': "Spam nội dung từ file .txt",
    'power': "Admin"
}

def handle_war_command(message, message_object, thread_id, thread_type, author_id, client):
    global is_war_running
    
    if str(author_id) not in [str(a) for a in ADMIN]:
        client.replyMessage(
            Message(text="Bạn không có quyền dùng lệnh này."),
            message_object, thread_id, thread_type
        )
        return

    command_parts = str(message).split()
    if len(command_parts) < 2:
        client.replyMessage(Message(text="Vui lòng dùng: spam on hoặc spam stop."), message_object, thread_id, thread_type)
        return

    action = command_parts[1].lower()

    if action == "stop":
        if not is_war_running:
            client.replyMessage(Message(text="⚠️ Spam hiện không chạy."), message_object, thread_id, thread_type)
        else:
            is_war_running = False
            client.replyMessage(Message(text="✅ Đã dừng spam."), message_object, thread_id, thread_type)
        return

    if action == "on":
        if is_war_running:
            client.replyMessage(Message(text="⚠️ Spam đang chạy rồi."), message_object, thread_id, thread_type)
            return

        try:
            # Kiểm tra file nội dung
            file_path = "spam/ngonwar2.txt"
            if not os.path.exists(file_path):
                # Thử tìm ở các vị trí khác nếu cần, hoặc báo lỗi
                client.replyMessage(Message(text=f"❌ Không tìm thấy file {file_path}"), message_object, thread_id, thread_type)
                return

            with open(file_path, "r", encoding="utf-8") as file:
                Ngon = [line.strip() for line in file.readlines() if line.strip()]

            if not Ngon:
                client.replyMessage(Message(text="❌ File nội dung trống."), message_object, thread_id, thread_type)
                return

            is_war_running = True
            client.replyMessage(Message(text="🚀 Bắt đầu spam..."), message_object, thread_id, thread_type)

            def war_loop():
                while is_war_running:
                    for noidung in Ngon:
                        if not is_war_running:
                            break
                        try:
                            client.send(Message(text=noidung), thread_id, thread_type)
                        except:
                            pass
                        time.sleep(0.5) # Delay để tránh bị ban nhanh

            threading.Thread(target=war_loop, daemon=True).start()

        except Exception as e:
            client.replyMessage(Message(text=f"❌ Lỗi: {e}"), message_object, thread_id, thread_type)
        return

    client.replyMessage(Message(text="❌ Lệnh không hợp lệ. Dùng 'on' hoặc 'stop'."), message_object, thread_id, thread_type)

def PTA():
    return {
        'spam': handle_war_command
    }