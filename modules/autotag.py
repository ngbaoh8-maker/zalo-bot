import json
import time
import threading
from zlapi.models import Message, Mention, MessageStyle, MultiMsgStyle
import logging
from config import PREFIX

logging.basicConfig(level=logging.DEBUG)

import os
path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'seting.json')
with open(path, 'r', encoding='utf-8') as f:
    settings = json.load(f)

ADMIN_ID = settings['admin']

des = {
    'version': "2.0.0",
    'credits': "ngbao",
    'description': "AutoTag spam liên tục (giống var)",
    'power': "Quản trị viên Bot"
}

is_autotag_running = False


def stop_autotag(client, message_object, thread_id, thread_type):
    """Dừng auto tag"""
    global is_autotag_running
    is_autotag_running = False
    if message_object:
        client.replyMessage(Message(text="🚨 Đã dừng AutoTag!"), message_object, thread_id, thread_type, ttl=30000)
    else:
        client.send(Message(text="🚨 Đã dừng AutoTag!"), thread_id, thread_type, ttl=30000)


def check_admin_permissions(author_id, creator_id, admin_ids):
    """Kiểm tra quyền admin"""
    all_admin_ids = set(admin_ids)
    all_admin_ids.add(str(creator_id))
    all_admin_ids.add(str(ADMIN_ID))
    return str(author_id) in all_admin_ids


def send_error_message(client, thread_id, thread_type, error_message):
    """Gửi tin lỗi"""
    client.send(Message(text=error_message), thread_id, thread_type, ttl=30000)


def handle_autotag_command(message, message_object, thread_id, thread_type, author_id, client):
    global is_autotag_running
    command_parts = message.split()
    if len(command_parts) < 3:
        msg = f"🚦 Sai cú pháp! Dùng {PREFIX}autotag @ on/off"
        if message_object:
            client.replyMessage(Message(text=msg), message_object, thread_id, thread_type, ttl=30000)
        else:
            client.send(Message(text=msg), thread_id, thread_type, ttl=30000)
        return

    if command_parts[1] != "@":
        send_error_message(client, thread_id, thread_type, f"🚦 Sai cú pháp! Dùng {PREFIX}autotag @ on/off")
        return

    action = command_parts[2].lower()

    # --- OFF ---
    if action == "off":
        if not is_autotag_running:
            client.send(Message(text="🚦 Không có AutoTag nào đang chạy!"), thread_id, thread_type, ttl=30000)
        else:
            stop_autotag(client, message_object, thread_id, thread_type)
        return

    # --- ON ---
    if action != "on":
        send_error_message(client, thread_id, thread_type, f"🚦 Sai cú pháp! Dùng {PREFIX}autotag @ on/off")
        return

    group_info = client.fetchGroupInfo(thread_id)
    if not group_info or thread_id not in group_info.gridInfoMap:
        send_error_message(client, thread_id, thread_type, "🚦 ❌ Không thể dùng trong tin nhắn riêng.")
        return

    group_data = group_info.gridInfoMap[thread_id]
    creator_id = group_data.get("creatorId")
    admin_ids = group_data.get("adminIds", [])

    if not check_admin_permissions(author_id, creator_id, admin_ids):
        send_error_message(client, thread_id, thread_type, "🚦 Chỉ admin mới có thể sử dụng lệnh này.")
        return

    member_ids = group_data.get("memberIds", [])
    if not member_ids:
        client.send(Message(text="❌ Không tìm thấy thành viên nào để tag!"), thread_id, thread_type)
        return

    # --- Bắt đầu spam autotag ---
    is_autotag_running = True
    client.send(Message(text="✅ Đã bật AutoTag spam liên tục!"), thread_id, thread_type, ttl=30000)

    def autotag_loop():
        while is_autotag_running:
            tag_text = ""
            mentions = []
            for uid in member_ids:
                try:
                    user_info = client.fetchUserInfo(uid)
                    name = user_info[uid].first_name or user_info[uid].name or "Người dùng"
                except Exception:
                    name = "Người dùng"
                start = len(tag_text)
                tag_text += f"@{name} "
                mentions.append(Mention(uid, offset=start, length=len(name) + 1))

            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(tag_text), style="bold", auto_format=False),
                MessageStyle(offset=0, length=len(tag_text), style="color", color="#db342e", auto_format=False)
            ])

            client.send(Message(text=tag_text.strip(), mentions=mentions, style=styles), thread_id, thread_type)
            time.sleep(0.5)  # chỉnh tốc độ spam (0.3–1.0 giây tuỳ bạn)

        client.send(Message(text="🚦 AutoTag đã dừng."), thread_id, thread_type)

    threading.Thread(target=autotag_loop, daemon=True).start()


def PTA():
    return {
        'autotag': handle_autotag_command
    }
