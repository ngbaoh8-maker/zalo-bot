from zlapi.models import *
import os
import time
import threading
from zlapi.models import MessageStyle, MultiMsgStyle
from config import ADMIN

des = {
    'version': "1.0.3",
    'credits': "ngbao",
    'description': "Chỉnh sửa tên tài khoản bot",
    'power': "Admin"
}

current_account_name = None

def handle_change_account_name_command(message, message_object, thread_id, thread_type, author_id, client):
    global is_reo_running, current_account_name
    
    if author_id not in ADMIN:
        message = Message(
            text="b k d q.",
            style=MultiMsgStyle([
                MessageStyle(offset=0, length=len("b k d q."), style="bold", size=13, auto_format=False),
                MessageStyle(offset=0, length=len("b k d q."), style="font", size=13, auto_format=False)
            ])
        )
        client.replyMessage(message, message_object, thread_id, thread_type)
        return

    command_parts = message.split(maxsplit=1)
    if len(command_parts) < 2:
        message = Message(
            text="Vui lòng chỉ định tên mới cho tài khoản.",
            style=MultiMsgStyle([
                MessageStyle(offset=0, length=len("Vui lòng chỉ định tên mới cho tài khoản."), style="bold", size=13, auto_format=False),
                MessageStyle(offset=0, length=len("Vui lòng chỉ định tên mới cho tài khoản."), style="font", size=13, auto_format=False)
            ])
        )
        client.replyMessage(message, message_object, thread_id, thread_type)
        return

    new_account_name = command_parts[1]
    try:
        account_info = client.fetchAccountInfo()
        current_account_name = account_info.get("name", "None")
    except Exception as e:
        message = Message(
            text=f"Không thể lấy thông tin tài khoản: {str(e)}",
            style=MultiMsgStyle([
                MessageStyle(offset=0, length=len(f"Không thể lấy thông tin tài khoản: {str(e)}"), style="bold", size=13, auto_format=False),
                MessageStyle(offset=0, length=len(f"Không thể lấy thông tin tài khoản: {str(e)}"), style="font", size=13, auto_format=False)
            ])
        )
        client.replyMessage(message, message_object, thread_id, thread_type)
        return

    if new_account_name == current_account_name:
        message = Message(
            text="Tên tài khoản chưa thay đổi.",
            style=MultiMsgStyle([
                MessageStyle(offset=0, length=len("Tên tài khoản chưa thay đổi."), style="bold", size=13, auto_format=False),
                MessageStyle(offset=0, length=len("Tên tài khoản chưa thay đổi."), style="font", size=13, auto_format=False)
            ])
        )
        client.replyMessage(message, message_object, thread_id, thread_type)
        return

    try:
        default_dob = "2000-04-06"
        default_gender = 0

        client.changeAccountSetting(name=new_account_name, dob=default_dob, gender=default_gender)
        message = Message(
            text=f"Đã đổi tên tài khoản thành {new_account_name}.",
            style=MultiMsgStyle([
                MessageStyle(offset=0, length=len(f"Đã đổi tên tài khoản thành {new_account_name}."), style="bold", size=13, auto_format=False),
                MessageStyle(offset=0, length=len(f"Đã đổi tên tài khoản thành {new_account_name}."), style="font", size=13, auto_format=False)
            ])
        )
        client.replyMessage(message, message_object, thread_id, thread_type)
    except Exception as e:
        error_message = f"Đã xảy ra lỗi khi thay đổi tên tài khoản: {str(e)}. Vui lòng thử lại sau."
        message = Message(
            text=error_message,
            style=MultiMsgStyle([
                MessageStyle(offset=0, length=len(error_message), style="bold", size=13, auto_format=False),
                MessageStyle(offset=0, length=len(error_message), style="font", size=13, auto_format=False)
            ])
        )
        client.replyMessage(message, message_object, thread_id, thread_type)
        return

def PTA():
    return {
        'rename': handle_change_account_name_command
    }
