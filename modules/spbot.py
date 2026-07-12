import time
import threading
import json
from zlapi.models import Message, MultiMsgStyle, MessageStyle
from config import ADMIN, PREFIX

des = {
    'version': "1.0.7",
    'credits': "ngbao",
    'description': "Spam nội dung tùy chọn",
    'power': "Quản trị viên Bot"
}

MAX_SPAM = 1000
DEFAULT_DELAY = 0.3
SPAM_TTL = 1000
ADMIN_ID = ADMIN


def is_admin(author_id):
    return str(author_id) == str(ADMIN_ID)


def handle_spbot(message, message_object, thread_id, thread_type, author_id, client):
    user_info = client.fetchUserInfo(author_id)
    author_info = user_info.changed_profiles.get(str(author_id), {}) if user_info and user_info.changed_profiles else {}
    name = author_info.get('zaloName', 'Không xác định')

    if hasattr(message_object, "message_id"):
        try:
            client.unsendMessage(message_object.message_id, delay=3)
        except:
            pass

    if not is_admin(author_id):
        msg = f"{name}\n➜Bạn không đủ quyền hạn để sử dụng lệnh này! 😠"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
        ])
        client.replyMessage(
            Message(text=msg, style=styles),
            message_object,
            thread_id,
            thread_type,
            ttl=3000
        )
        return

    parts = message.strip().split()
    prefix_command = f"{PREFIX}spbot"

    if len(parts) != 3 or not message.lower().startswith(prefix_command):
        msg = f"{name}\n➜Hướng dẫn:\n{PREFIX}spbot <nội_dung> <số_lần>\nVD: {PREFIX}spbot ! 10"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
        ])
        client.replyMessage(
            Message(text=msg, style=styles),
            message_object,
            thread_id,
            thread_type,
            ttl=15000
        )
        return

    text = parts[1]
    try:
        count = int(parts[2])
    except:
        return

    if count <= 0 or count > MAX_SPAM:
        msg = f"{name}\n➜Số lần phải trong khoảng 1–{MAX_SPAM}!"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
        ])
        client.replyMessage(
            Message(text=msg, style=styles),
            message_object,
            thread_id,
            thread_type,
            ttl=3000
        )
        return

    for _ in range(count):
        try:
            client.sendMessage(
                Message(text=text),
                thread_id,
                thread_type,
                ttl=SPAM_TTL
            )
        except:
            pass
        time.sleep(DEFAULT_DELAY)


def PTA():
    return {'spbot': handle_spbot}