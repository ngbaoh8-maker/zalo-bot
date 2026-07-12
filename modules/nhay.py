from zlapi.models import *
import os
import time
import threading
from zlapi.models import MultiMsgStyle, Mention, MessageStyle
from config import ADMIN
from config import PREFIX
is_nhaytag_running = False

des = {
    'version': "1.0.2",
    'credits': "ngbao",
    'description': "Nhây",
    'power': "Admin"
}

def nhaytagstop(client, message_object, thread_id, thread_type, ttl=6000):
    global is_nhaytag_running
    is_nhaytag_running = False
    client.replyMessage(Message(text="Đã dừng nhây tag."), message_object, thread_id, thread_type, ttl=6000)

def nhaytag(message, message_object, thread_id, thread_type, author_id, client):
    global is_nhaytag_running

    if author_id not in ADMIN:
        client.replyMessage(
            Message(text="Bạn Không có quyền dùng lệnh này"),
            message_object, thread_id, thread_type, ttl=6000
        )
        return

    command_parts = message.split()
    if len(command_parts) < 2:
        client.replyMessage(Message(text=f"Vui lòng chỉ định lệnh hợp lệ (vd: {PREFIX}nhaytag on hoặc {PREFIX}nhaytag stop)."), message_object, thread_id, thread_type, ttl=6000)
        return

    action = command_parts[1].lower()

    if action == "stop":
        if not is_nhaytag_running:
            client.replyMessage(
                Message(text="đã dừng lệnh nhây tag"),
                message_object, thread_id, thread_type, ttl=6000
            )
        else:
            nhaytagstop(client, message_object, thread_id, thread_type, ttl=6000)
        return

    if action != "on":
        client.replyMessage(Message(text="Vui lòng chỉ định lệnh 'on' hoặc 'stop'."), message_object, thread_id, thread_type)
        return

    if message_object.mentions:
        tagged_users = message_object.mentions[0]['uid']
    else:
        client.replyMessage(Message(text="Xin hãy tag user cần spam"), message_object, thread_id, thread_type, ttl=6000)
        return

    try:
        with open("noidung.txt", "r", encoding="utf-8") as file:
            Ngon = file.readlines()
    except FileNotFoundError:
        client.replyMessage(
            Message(text="Không tìm thấy file noidung.txt."),
            message_object,
            thread_id,
            thread_type, ttl=6000
        )
        return

    if not Ngon:
        client.replyMessage(
            Message(text="File noidung.txt không có nội dung nào để gửi."),
            message_object,
            thread_id,
            thread_type, ttl=6000,
        )
        return

    is_nhaytag_running = True
    def nhaytag_loop():
        while is_nhaytag_running:
            for noidung in Ngon:
                if not is_nhaytag_running:
                    break
                mention = Mention(tagged_users, length=0, offset=0)
                client.send(Message(text=f"  {noidung}", mention=mention), thread_id, thread_type, ttl=5000)
                time.sleep(0.3)

    nhaytag_thread = threading.Thread(target=nhaytag_loop)
    nhaytag_thread.start()

def PTA():
    return {
        'nhay': nhaytag
    }