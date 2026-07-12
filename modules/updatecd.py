import time
import logging
from zlapi.models import Message, ThreadType, MultiMsgStyle, MessageStyle
from config import ADMIN, PREFIX

des = {
    'version': "1.2.0",
    'credits': "ngbao",
    'description': "Nâng cấp nhóm hiện tại lên Cộng đồng - Phiên bản tối giản.",
    'power': "Quản trị viên Bot"
}

def get_user_name(client, user_id):
    try:
        user_info = client.fetchUserInfo(str(user_id))
        return user_info.changed_profiles.get(str(user_id), {}).get('zaloName', str(user_id))
    except Exception:
        return str(user_id)

def handle_updatecd_command(message_text, message_object, thread_id, thread_type, author_id, client):
    name = get_user_name(client, author_id)
    
    if str(author_id) not in ADMIN:
        rest_text = "🚫 Chỉ admin bot mới có quyền sử dụng lệnh này."
        msg = f"{name}\n➜{rest_text}"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(name), style="bold", auto_format=False)
        ])
        client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=120000)
        return

    if thread_type != ThreadType.GROUP:
        rest_text = "🚫 Lệnh này chỉ thực hiện được trong nhóm."
        msg = f"{name}\n➜{rest_text}"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(name), style="bold", auto_format=False)
        ])
        client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=120000)
        return

    rest_text = "⏳ Đang bắt đầu quá trình nâng cấp nhóm lên Cộng đồng..."
    msg = f"{name}\n➜{rest_text}"
    styles = MultiMsgStyle([
        MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
        MessageStyle(offset=0, length=len(name), style="bold", auto_format=False)
    ])
    client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=120000)

    group_info = client.fetchGroupInfo(thread_id)
    res = client.upgradeCommunity(thread_id)
    
    success = False
    if isinstance(res, dict) and (res.get('error_code') == 0 or res.get('status') == 0):
        success = True
    elif res is None: 
        success = True

    if success:
        rest_text = f"✅ Hoàn tất!\n➜Đã nâng cấp thành công: 1 nhóm.\n➜Thất bại: 0 nhóm."
    else:
        rest_text = f"❌ Thất bại!\n➜Nhóm không đủ điều kiện hoặc đã là cộng đồng.\n➜Thất bại: 1 nhóm."
        
    msg = f"{name}\n➜{rest_text}"
    styles = MultiMsgStyle([
        MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
        MessageStyle(offset=0, length=len(name), style="bold", auto_format=False)
    ])
    client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=120000)

def PTA():
    return {
        'upcd': handle_updatecd_command
    }
