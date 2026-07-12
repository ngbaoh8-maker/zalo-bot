from zlapi.models import *
import os
import requests
from config import ADMIN
from zlapi.models import MessageStyle, MultiMsgStyle


des = {
    'version': "1.0.2",
    'credits': "ngbao",
    'description': "Thay avatar tài khoản bot",
    'power': "Quản trị viên Bot"
}


def send_msg(text, client, message_object, thread_id, thread_type):
    msg = Message(
        text=text,
        style=MultiMsgStyle([
            MessageStyle(offset=0, length=len(text), style="bold", size=13, auto_format=False),
            MessageStyle(offset=0, length=len(text), style="font", size=13, auto_format=False)
        ])
    )
    client.replyMessage(msg, message_object, thread_id, thread_type)


def download_image(url, save_path):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return False
        with open(save_path, "wb") as f:
            f.write(r.content)
        return True
    except:
        return False


def handle_change_avatar(message, message_object, thread_id, thread_type, author_id, client):

    # check admin
    if author_id not in ADMIN:
        return send_msg("b k d q.", client, message_object, thread_id, thread_type)

    img_path = "avatar_temp.jpg"

    # ===== TH1: ảnh đính kèm =====
    if hasattr(message_object, "attachments") and message_object.attachments:
        att = message_object.attachments[0]
        if att.type == "photo":
            if not download_image(att.url, img_path):
                return send_msg("Tải ảnh thất bại.", client, message_object, thread_id, thread_type)

            try:
                client.changeAccountAvatar(img_path)
                return send_msg("Đã đổi avatar từ ảnh đính kèm.", client, message_object, thread_id, thread_type)
            except Exception as e:
                return send_msg(f"Lỗi đổi avatar: {str(e)}", client, message_object, thread_id, thread_type)

    # ===== TH2: link ảnh =====
    parts = message.split(maxsplit=1)
    if len(parts) < 2:
        return send_msg("Gửi ảnh hoặc link ảnh để đổi avatar.", client, message_object, thread_id, thread_type)

    link = parts[1]

    if not download_image(link, img_path):
        return send_msg("Không tải được ảnh từ link.", client, message_object, thread_id, thread_type)

    try:
        client.changeAccountAvatar(img_path)
        return send_msg("Đã đổi avatar từ link ảnh.", client, message_object, thread_id, thread_type)
    except Exception as e:
        return send_msg(f"Lỗi đổi avatar: {str(e)}", client, message_object, thread_id, thread_type)


def PTA():
    return {
        "upava": handle_change_avatar
    }
