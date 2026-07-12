from zlapi.models import *
import os
import time
import threading
from zlapi.models import MultiMsgStyle, MessageStyle
from config import ADMIN

is_war_running = False

des = {
    'version': "1.0.2",
    'credits': "ngbao",
    'description': "Chửi người ta",
    'power': "Admin"
}

def stop_war(client, message_object, thread_id, thread_type):
    global is_war_running
    is_war_running = False
    client.replyMessage(Message(text="Đã dừng gửi nội dung."), message_object, thread_id, thread_type)

def is_admin(author_id):
    try:
        import os
        import json
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'seting.json')
        if not os.path.exists(path):
            path = 'seting.json'
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        admin_main = str(data.get('admin', ''))
        vip = [str(x) for x in data.get('vip_adm', [])]
        adm_list = [str(x) for x in data.get('adm', [])]
        
        author_str = str(author_id)
        
        try:
            from config import ADMIN
            config_admin = str(ADMIN)
        except:
            config_admin = ""
            
        admins = set([admin_main, config_admin] + vip + adm_list)
        if "" in admins:
            admins.remove("")
            
        return author_str in admins
    except Exception as e:
        print(f"Error checking admin in chui: {e}")
        return str(author_id) == str(ADMIN)

def handle_war_command(message, message_object, thread_id, thread_type, author_id, client):
    global is_war_running

    if not is_admin(author_id):
        client.replyMessage(
            Message(text="Cha ngbao Cho Mày Sử Dụng À ??🤪🤣."),
            message_object, thread_id, thread_type
        )
        return

    command_parts = message.split()
    if len(command_parts) < 2:
        client.replyMessage(Message(text="Vui lòng chỉ định lệnh hợp lệ (vd: chui on hoặc chui stop)."), message_object, thread_id, thread_type)
        return

    action = command_parts[1].lower()

    if action == "stop":
        if not is_war_running:
            client.replyMessage(
                Message(text="⚠️ **Gửi nội dung đã dừng lại.**"),
                message_object, thread_id, thread_type
            )
        else:
            stop_war(client, message_object, thread_id, thread_type)
        return

    if action != "on":
        client.replyMessage(Message(text="Vui lòng chỉ định lệnh 'on' hoặc 'stop'."), message_object, thread_id, thread_type)
        return

    try:
        with open("ngonwar2.txt", "r", encoding="utf-8") as file:
            Ngon = file.readlines()
    except FileNotFoundError:
        client.replyMessage(
            Message(text="Không tìm thấy file ngonwar2.txt."),
            message_object,
            thread_id,
            thread_type
        )
        return

    if not Ngon:
        client.replyMessage(
            Message(text="File ngonwar2.txt không có nội dung nào để gửi."),
            message_object,
            thread_id,
            thread_type
        )
        return

    is_war_running = True

    def war_loop():
        while is_war_running:
            for noidung in Ngon:
                if not is_war_running:
                    break
                client.send(Message(text=noidung), thread_id, thread_type)
                time.sleep(10)

    war_thread = threading.Thread(target=war_loop)
    war_thread.start()

def PTA():
    return {
        'chui': handle_war_command
    }