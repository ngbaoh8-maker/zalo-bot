import time
import threading
import logging
from zlapi.models import Message, Mention
from config import ADMIN

# Trạng thái chạy của lệnh troll theo từng nhóm
troll_status = {}
logger = logging.getLogger(__name__)

des = {
    'version': "1.1.0",
    'credits': "ngbao",
    'description': "Tag liên tục một người dùng",
    'power': "Admin"
}

def handle_onetag_command(message, message_object, thread_id, thread_type, author_id, client):
    global troll_status

    if author_id not in ADMIN:
        return client.replyMessage(Message(text="⚠️ Quyền Lồn Biên Giới!."), message_object, thread_id, thread_type)

    args = message.split()
    if len(args) < 2:
        return client.replyMessage(Message(text="👉 Dùng: .troll on @tag hoặc .troll stop"), message_object, thread_id, thread_type)

    action = args[1].lower()

    if action == "stop":
        troll_status[thread_id] = False
        return client.replyMessage(Message(text="🛑 Đã dừng tiến trình troll."), message_object, thread_id, thread_type)

    if action == "on":
        if not message_object.mentions:
            return client.replyMessage(Message(text="❗ Hãy tag người bạn muốn troll."), message_object, thread_id, thread_type)
        
        target_uid = message_object.mentions[0]['uid']
        troll_status[thread_id] = True

        def start_troll():
            try:
                # Đọc nội dung chửi 1 lần để tối ưu
                with open("trollv2.txt", "r", encoding="utf-8") as f:
                    sentences = [line.strip() for line in f if line.strip()]
                
                if not sentences:
                    client.sendMessage(Message(text="❌ File trollv2.txt trống!"), thread_id, thread_type)
                    return

                while troll_status.get(thread_id):
                    for text in sentences:
                        if not troll_status.get(thread_id): break
                        
                        # Gửi tin nhắn kèm tag
                        mention = Mention(target_uid, length=len(text), offset=1)
                        client.send(Message(text=f" {text}", mention=mention), thread_id, thread_type)
                        
                        # Thời gian nghỉ để tránh bị ban (2-3 giây)
                        time.sleep(1)
            except Exception as e:
                logger.error(f"Lỗi troll: {e}")

        threading.Thread(target=start_troll, daemon=True).start()
        client.replyMessage(Message(text="✅ Bắt đầu tiến trình..."), message_object, thread_id, thread_type)

def PTA():
    return {'troll': handle_onetag_command, 'nhayvip': handle_onetag_command}