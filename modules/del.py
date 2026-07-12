from zlapi.models import Message, MultiMsgStyle, MessageStyle
from config import ADMIN

des = {
    'version': "1.0.4",
    'credits': "ngbao",
    'description': "Xoá tin nhắn người dùng bằng cách reply",
    'power': "Quản trị viên Bot"
}

def is_admin(author_id):
    return str(author_id) in [str(a) for a in ADMIN]

def handle_del_command(message, message_object, thread_id, thread_type, author_id, client):
    user_info = client.fetchUserInfo(author_id)
    author_info = user_info.changed_profiles.get(str(author_id), {}) if user_info and user_info.changed_profiles else {}
    name = author_info.get('zaloName', 'Không xác định')

    if not is_admin(author_id):
        rest_text = "Bạn không có quyền sử dụng lệnh này. 😠"
        msg = f"{name}\n➜{rest_text}"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(name), style="bold", auto_format=False)
        ])
        client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=8000)
        return

    if not message_object.quote:
        rest_text = "Hãy reply tin nhắn bạn muốn xóa. 📌"
        msg = f"{name}\n➜{rest_text}"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(name), style="bold", auto_format=False)
        ])
        client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=10000)
        return

    msg2del = message_object.quote
    try:
        client.deleteGroupMsg(msg2del.globalMsgId, msg2del.ownerId, msg2del.cliMsgId, thread_id)
        rest_text = "Tin nhắn đã được xóa thành công! ✅"
    except:
        rest_text = "Không thể xóa tin nhắn này. ⚠️"

    msg = f"{name}\n➜{rest_text}"
    styles = MultiMsgStyle([
        MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
        MessageStyle(offset=0, length=len(name), style="bold", auto_format=False)
    ])
    client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=8000)

def PTA():
    return {
        'del': handle_del_command
    }