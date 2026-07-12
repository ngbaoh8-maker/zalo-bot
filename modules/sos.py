from zlapi.models import Message
from config import ADMIN
import json
import random
import time
import threading

# Mô tả module
des = {
    'version': "1.0.1",
    'credits': "ngbao",
    'description': "Lệnh đóng/mở chat",
    'power': "Quản trị viên Bot"
}

group_chat_status = {}

# Danh sách emoji để thả reaction
EMOJI_LIST = ["😍", "🥀", "🦧", "💤", "😂", "🔥", "❄️", "🤡", "👥", "🗿"]

# Hàm tạo style chữ
def styled(text, b=True, i=True, color="15a85f", size=18):
    styles = [{
        "start": 0,
        "len": len(text),
        "st": ",".join(filter(None, [
            "b" if b else "",
            "i" if i else "",
            f"c_{color}",
            f"f_{size}"
        ]))
    }]
    return json.dumps({"styles": styles, "ver": 0})

# Kiểm tra admin
def is_admin(author_id):
    return str(author_id) in ADMIN

# Gửi 6 reaction ngẫu nhiên
def send_random_reactions(client, message_object, thread_id, thread_type):
    emojis = random.sample(EMOJI_LIST, 6)
    for emoji in emojis:
        try:
            client.sendReaction(message_object, emoji, thread_id, thread_type, reactionType=75)
        except Exception as e:
            print(f"Lỗi reaction {emoji}: {e}")

# Xử lý lệnh sos
def handle_bot_sos_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        if not is_admin(author_id):
            error_msg = "M tuổi lồn gì mà đòi xài lệnh admin =))"
            client.replyMessage(
                Message(text=error_msg),
                message_object, thread_id, thread_type, ttl=60000
            )
            return

        command_text = message.lower().strip()
        current_status = group_chat_status.get(thread_id, 0)

        if "-sos on" in command_text:
            # Kiểm tra nếu có thời gian tắt, ví dụ: -sos on 10s
            if 's' in command_text.split()[-1]:
                time_seconds = int(command_text.split()[-1][:-1])  # Lấy thời gian từ câu lệnh
                if current_status == 1:
                    return
                new_status = 1
                action_text = f"🚦 Đóng chat thành công! Tắt sau {time_seconds} giây!"
                action_style = styled(action_text, color="db342e")
                
                # Thực hiện tắt chat trong thời gian quy định
                threading.Timer(time_seconds, toggle_chat, [thread_id, 0, client]).start()
            else:
                if current_status == 1:
                    return
                new_status = 1
                action_text = "🚦 Đóng chat thành công!"
                action_style = styled(action_text, color="db342e")

        elif "-sos off" in command_text:
            if current_status == 0:
                return
            new_status = 0
            action_text = "🤖 Mở chat thành công!"
            action_style = styled(action_text, color="15a85f")

        else:
            new_status = 1 if current_status == 0 else 0
            if new_status == 1:
                action_text = "🚦 Đóng chat thành công!"
                action_style = styled(action_text, color="db342e")
            else:
                action_text = "🤖 Mở chat thành công!"
                action_style = styled(action_text, color="15a85f")

        group_chat_status[thread_id] = new_status
        client.changeGroupSetting(thread_id, lockSendMsg=new_status)

        client.replyMessage(
            Message(text=action_text, style=action_style),
            message_object,
            thread_id, thread_type, ttl=60000
        )

        # Thả 6 reaction
        send_random_reactions(client, message_object, thread_id, thread_type)

    except Exception as e:
        error_message = f"⚠ Lỗi khi thay đổi cài đặt nhóm: {str(e)}"
        client.replyMessage(
            Message(text=error_message),
            message_object, thread_id, thread_type, ttl=60000
        )

# Hàm tắt chat sau một thời gian
def toggle_chat(thread_id, status, client):
    group_chat_status[thread_id] = status
    client.changeGroupSetting(thread_id, lockSendMsg=status)

def PTA():
    return {
        'sos': handle_bot_sos_command
    }