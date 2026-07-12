from zlapi.models import Message, ZaloAPIException
from config import ADMIN, IMEI
import time

des = {
    'version': "1.0.1",
    'credits': "ngbao",
    'description': "Lệnh rời nhóm",
    'power': "Admin"
}

def handle_leave_command(message, message_object, thread_id, thread_type, author_id, client):
    if author_id not in ADMIN:
        msg = "Quyền lồn biên giới⁉️"
        styles = MultiMsgStyle([
                MessageStyle(offset=0, length=10000, style="font", size="10", auto_format=False),
            ])
        client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=60000)
        return
    try:
        client.leaveGroup(thread_id, imei=IMEI)
        
    except ZaloAPIException as e:
        msg = f"err: {e}"
        styles = MultiMsgStyle([
                MessageStyle(offset=0, length=10000, style="font", size="10", auto_format=False),
            ])
        client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=60000)
    except Exception as e:
        msg = f"error: {e}"
        styles = MultiMsgStyle([
                MessageStyle(offset=0, length=10000, style="font", size="10", auto_format=False),
            ])
        client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=60000)

def PTA():
    return {
        'leave': handle_leave_command
    }
