import os
import time
import threading
from zlapi.models import Message, MultiMsgStyle, MessageStyle, Mention
from config import ADMIN, PREFIX

des = {
    'version': "1.2.0",
    'credits': "ngbao",
    'description': "Reo chửi và tag thành viên",
    'power': "Quản trị viên Bot"
}

is_reo_running = False

def send_styled_message(author_id, text, message_object, thread_id, thread_type, client):
    try:
        user_info = client.fetchUserInfo(author_id)
        user_name = user_info.changed_profiles.get(str(author_id), {}).get("zaloName", "người dùng")
        msg = f"{user_name}\n➜ {text}"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(user_name), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(user_name), style="bold", auto_format=False)
        ])
        client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=8000)
    except Exception as e:
        print(f"Lỗi khi gửi styled message: {e}")

def stop_reo(client, message_object, thread_id, thread_type, author_id):
    global is_reo_running
    is_reo_running = False
    send_styled_message(author_id, "Đã dừng réo tên.", message_object, thread_id, thread_type, client)

def handle_reo_command(message, message_object, thread_id, thread_type, author_id, client):
    global is_reo_running

    if str(author_id) not in ADMIN:
        send_styled_message(author_id, "Bạn không có quyền sử dụng lệnh này.", message_object, thread_id, thread_type, client)
        return

    parts = message.split()
    if len(parts) < 2:
        send_styled_message(author_id, f"Dùng cú pháp:\n{PREFIX}reo on hoặc {PREFIX}reo stop", message_object, thread_id, thread_type, client)
        return

    action = parts[1].lower()

    if action == "stop":
        if not is_reo_running:
            send_styled_message(author_id, "Không có tiến trình reo nào đang chạy.", message_object, thread_id, thread_type, client)
        else:
            stop_reo(client, message_object, thread_id, thread_type, author_id)
        return

    if action != "on":
        send_styled_message(author_id, f"Lệnh không hợp lệ.\nDùng:\n{PREFIX}reo on hoặc {PREFIX}reo stop", message_object, thread_id, thread_type, client)
        return

    if not message_object.mentions:
        send_styled_message(author_id, "Hãy tag người cần bị réo", message_object, thread_id, thread_type, client)
        return

    tagged_user = message_object.mentions[0]['uid']

    try:
        user_info = client.fetchUserInfo(tagged_user)
        tagged_name = user_info.changed_profiles.get(str(tagged_user), {}).get("zaloName", "người bị réo")
    except:
        tagged_name = "người bị réo"

    try:
        with open("nhay.txt", "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        send_styled_message(author_id, "Không tìm thấy file nhay.txt", message_object, thread_id, thread_type, client)
        return

    if not lines:
        send_styled_message(author_id, "File nhay.txt rỗng", message_object, thread_id, thread_type, client)
        return

    is_reo_running = True
    send_styled_message(author_id, f"Bắt đầu réo", message_object, thread_id, thread_type, client)

    def reo_loop():
        global is_reo_running
        while is_reo_running:
            for text in lines:
                if not is_reo_running:
                    break
                try:
                    tag_text = f"@{tagged_name}"
                    full_text = f"{tag_text} {text}"
                    mention = Mention(uid=tagged_user, offset=0, length=len(tag_text))
                    client.send(Message(text=full_text, mention=mention), thread_id, thread_type)
                    time.sleep(0.5)
                except Exception as e:
                    print(f"Lỗi khi gửi: {e}")
                    is_reo_running = False
                    break
        is_reo_running = False

    threading.Thread(target=reo_loop).start()

def PTA():
    return {
        "reo": handle_reo_command
    }