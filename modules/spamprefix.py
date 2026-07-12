import time
import threading
from zlapi.models import *
from config import ADMIN, PREFIX

des = {
    'version': '1.0.6',
    'credits': "ngbao",
    'description': 'Gửi tin nhắn tàng hình (Không hiện nội dung, tự thu hồi).',
    'power': 'Quản trị viên Bot'
}

def is_admin(author_id):
    return author_id == ADMIN

def handle_gui_command(message, message_object, thread_id, thread_type, author_id, client):
    """
    Cú pháp: {PREFIX}gui <số lần> [nội dung]
    Ví dụ: .gui 10 (Sẽ gửi 10 tin nhắn tàng hình và thu hồi ngay)
    """
    parts = message.strip().split()

    if not is_admin(author_id):
        return

    if len(parts) < 2:
        return

    try:
        # Lấy số lần gửi
        count = int(parts[1])
        
        # Nếu bạn không nhập nội dung, bot dùng ký tự tàng hình (\u200b)
        # Nếu có nhập nội dung, nó sẽ gửi nội dung đó rồi thu hồi.
        content = " ".join(parts[2:]) if len(parts) > 2 else "\u200b"
        
        # Giới hạn an toàn để tránh bị Zalo khóa tài khoản
        if count > 50: count = 50

        def start_ghost_spam():
            # Bước 1: Thử xóa tin nhắn lệnh của chính bạn cho "sạch" cuộc trò chuyện
            try:
                client.deleteMessage(message_object.msgId, thread_id, thread_type)
            except:
                pass

            for i in range(count):
                try:
                    # Bước 2: Gửi tin nhắn
                    sent_msg = client.send(Message(text=content), thread_id, thread_type)
                    
                    # Bước 3: Thu hồi ngay lập tức (Ghosting)
                    if sent_msg and hasattr(sent_msg, 'msgId'):
                        client.unsendMessage(sent_msg.msgId, thread_id, thread_type)
                    
                    # Khoảng nghỉ ngắn để lách bộ lọc của Zalo
                    time.sleep(0.7)
                except Exception as e:
                    print(f"[GUI] Lỗi tại lần {i+1}: {e}")
                    break

        # Chạy trong luồng riêng để Bot không bị khựng
        threading.Thread(target=start_ghost_spam, daemon=True).start()

    except ValueError:
        pass

def PTA():
    return {
        'gui': handle_gui_command,
    }
