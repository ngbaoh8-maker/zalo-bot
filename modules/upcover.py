from zlapi.models import *
import os
import requests
from config import ADMIN
from zlapi.models import MessageStyle, MultiMsgStyle


des = {
    'version': "1.0.0",
    'credits': "ngbao",
    'description': "Thay avatar nhóm",
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


def set_group_avatar(client, gid, file_path):

    # 1. setGroupImage
    if hasattr(client, "setGroupImage"):
        client.setGroupImage(gid, file_path)
        return True

    # 2. changeGroupAvatar
    if hasattr(client, "changeGroupAvatar"):
        client.changeGroupAvatar(gid, file_path)
        return True

    return False


def handle_group_avatar(message, message_object, thread_id, thread_type, author_id, client):

    if author_id not in ADMIN:
        return send_msg("b k d q.", client, message_object, thread_id, thread_type)

    if thread_type != ThreadType.GROUP:
        return send_msg("Chỉ dùng được trong nhóm.", client, message_object, thread_id, thread_type)

    gid = thread_id
    img_path = "group_avatar_temp.jpg"

    # === gửi ảnh đính kèm ===
    if hasattr(message_object, "attachments") and message_object.attachments:
        att = message_object.attachments[0]
        if att.type == "photo":

            if not download_image(att.url, img_path):
                return send_msg("Không tải được ảnh.", client, message_object, thread_id, thread_type)

            if set_group_avatar(client, gid, img_path):
                return send_msg("Đã đổi avatar nhóm từ ảnh đính kèm.", client, message_object, thread_id, thread_type)
            else:
                return send_msg("API không hỗ trợ đổi avatar nhóm.", client, message_object, thread_id, thread_type)

    # === link ảnh ===
    parts = message.split(maxsplit=1)
    if len(parts) < 2:
        return send_msg("Gửi ảnh hoặc dán link ảnh để đổi avatar nhóm.", client, message_object, thread_id, thread_type)

    link = parts[1]

    if not download_image(link, img_path):
        return send_msg("Không tải được ảnh từ link.", client, message_object, thread_id, thread_type)

    if set_group_avatar(client, gid, img_path):
        return send_msg("Đã đổi avatar nhóm từ link ảnh.", client, message_object, thread_id, thread_type)
    else:
        return send_msg("API không hỗ trợ đổi avatar nhóm.", client, message_object, thread_id, thread_type)


def PTA():
    return {
        "upgava": handle_group_avatar
    }
