from zlapi.models import *
import os
import time
import threading
from zlapi.models import MessageStyle, MultiMsgStyle
from config import ADMIN

des = {
    'version': "1.0.3",
    'credits': "ngbao",
    'description': "Đổi tên nhóm",
    'power': "Quản trị viên Bot"
}

is_reo_running = False
current_group_name = None

def stop_reo(client, message_object, thread_id, thread_type):
    global is_reo_running
    is_reo_running = False
    message = Message(
        text="Quyền lồn biên giới.",
        style=MultiMsgStyle([
            MessageStyle(offset=0, length=len("Quyền lồn biên giới."), style="bold", size=13, auto_format=False),
            MessageStyle(offset=0, length=len("Quyền lồn biên giới."), style="font", size=13, auto_format=False)
        ])
    )
    client.replyMessage(message, message_object, thread_id, thread_type, ttl=60000)  # TTL 1 phút

def handle_setnamegr_command(message, message_object, thread_id, thread_type, author_id, client):
    global is_reo_running, current_group_name
    
    if author_id not in ADMIN:
        message = Message(
            text="Quyền đéo.",
            style=MultiMsgStyle([
                MessageStyle(offset=0, length=len("Quyền đéo."), style="bold", size=13, auto_format=False),
                MessageStyle(offset=0, length=len("Quyền đéo."), style="font", size=13, auto_format=False)
            ])
        )
        client.replyMessage(message, message_object, thread_id, thread_type, ttl=60000)
        return

    command_parts = message.split(maxsplit=1)
    if len(command_parts) < 2:
        message = Message(
            text="Vui lòng chỉ định tên mới cho nhóm.",
            style=MultiMsgStyle([
                MessageStyle(offset=0, length=len("Vui lòng chỉ định tên mới cho nhóm."), style="bold", size=13, auto_format=False),
                MessageStyle(offset=0, length=len("Vui lòng chỉ định tên mới cho nhóm."), style="font", size=13, auto_format=False)
            ])
        )
        client.replyMessage(message, message_object, thread_id, thread_type, ttl=60000)
        return

    new_group_name = command_parts[1]

    try:
        group_info = client.fetchGroupInfo(thread_id)
        group_name = group_info.gridInfoMap.get(thread_id, {}).get('name', 'None')
    except Exception as e:
        message = Message(
            text=f"Không thể lấy thông tin nhóm: {str(e)}",
            style=MultiMsgStyle([
                MessageStyle(offset=0, length=len(f"Không thể lấy thông tin nhóm: {str(e)}"), style="bold", size=13, auto_format=False),
                MessageStyle(offset=0, length=len(f"Không thể lấy thông tin nhóm: {str(e)}"), style="font", size=13, auto_format=False)
            ])
        )
        client.replyMessage(message, message_object, thread_id, thread_type, ttl=60000)
        return

    if new_group_name == group_name:
        message = Message(
            text="Tên nhóm chưa thay đổi.\nCó thể do vi phạm chính sách đặt tên của Zalo.",
            style=MultiMsgStyle([
                MessageStyle(offset=0, length=len("Tên nhóm chưa thay đổi.\nCó thể do vi phạm chính sách đặt tên của Zalo."), style="bold", size=13, auto_format=False),
                MessageStyle(offset=0, length=len("Tên nhóm chưa thay đổi.\nCó thể do vi phạm chính sách đặt tên của Zalo."), style="font", size=13, auto_format=False)
            ])
        )
        client.replyMessage(message, message_object, thread_id, thread_type, ttl=60000)
        return

    current_group_name = new_group_name
    
    try:
        client.changeGroupName(new_group_name, thread_id)
        message = Message(
            text=f"Đã đổi tên nhóm thành '{new_group_name}'.\nTên nhóm cũ: '{group_name}'",
            style=MultiMsgStyle([
                MessageStyle(offset=0, length=len(f"Đã đổi tên nhóm thành '{new_group_name}'.\nTên nhóm cũ: '{group_name}'"), style="bold", size=13, auto_format=False),
                MessageStyle(offset=0, length=len(f"Đã đổi tên nhóm thành '{new_group_name}'.\nTên nhóm cũ: '{group_name}'"), style="font", size=13, auto_format=False)
            ])
        )
        client.replyMessage(message, message_object, thread_id, thread_type, ttl=60000)
    except Exception as e:
        error_message = f"Đã xảy ra lỗi khi đổi tên nhóm: {str(e)}. Vui lòng thử lại sau."
        message = Message(
            text=error_message,
            style=MultiMsgStyle([
                MessageStyle(offset=0, length=len(error_message), style="bold", size=13, auto_format=False),
                MessageStyle(offset=0, length=len(error_message), style="font", size=13, auto_format=False)
            ])
        )
        client.replyMessage(message, message_object, thread_id, thread_type, ttl=60000)
        return

def PTA():
    return {
        'rngr': handle_setnamegr_command
    }