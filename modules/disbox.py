from zlapi.models import Message, ThreadType
from config import ADMIN
import json

des = {
    'version': "1.0.0",
    'credits': "ngbao",
    'description': "Giải tán nhóm Zalo mà lệnh được gửi tới",
    'power': "Chủ nhóm & Admin"
}

def check_admin(author_id):
    return str(author_id) in ADMIN

def handle_disbox_command(message, message_object, thread_id, thread_type, author_id, client):
    if not check_admin(author_id):
        error_message = Message(text="🚨 Chỉ admin có thể sử dụng lệnh này!")
        client.sendMessage(error_message, thread_id, thread_type, ttl=30000)
        return

    if thread_type != ThreadType.GROUP:
        error_message = Message(text="🚦 Lệnh này chỉ có thể được sử dụng trong nhóm!")
        client.sendMessage(error_message, thread_id, thread_type, ttl=30000)
        return

    try:
        result = client.disperseGroup(thread_id)
        if result is None:
            success_message = Message(text="✅ Nhóm đã được giải tán thành công!")
            client.sendMessage(success_message, thread_id, thread_type, ttl=30000)
        else:
            error_message = Message(text=f"🚨 Lỗi do: {result.get('error_message', 'Không thể giải tán nhóm.')}")
            client.sendMessage(error_message, thread_id, thread_type, ttl=30000)
    except Exception as e:
        error_message = Message(text=f"🚨 Đã xảy ra lỗi khi giải tán nhóm: {str(e)}")
        client.sendMessage(error_message, thread_id, thread_type, ttl=30000)

def PTA():
    return {
        'disbox': handle_disbox_command
    }