from zlapi.models import Message
from config import PREFIX, ADMIN
import json

ADMIN_ID = 637876082720685615

des = {
    'version': "1.0.0",
    'credits': "ngbao",
    'description': "Lấy thông tin của tin nhắn",
    'power': "Thành viên"
}

def attach(attach_string):
    try:
        return json.dumps(json.loads(attach_string), indent=4, ensure_ascii=False)
    except json.JSONDecodeError:
        return attach_string

def handle_object_command(message, message_object, thread_id, thread_type, author_id, client):
    if message_object.quote:
        quoted_message = message_object.quote
        if quoted_message.attach:
            try:
                quoted_message.attach = json.loads(quoted_message.attach)
            except json.JSONDecodeError:
                pass
        msg_info = json.dumps(quoted_message.__dict__, indent=4, ensure_ascii=False)
        client.replyMessage(Message(text=msg_info), message_object, thread_id, thread_type, ttl=86400000)
    else:
        client.replyMessage(Message(text="Reply tin nhắn cần lấy thông tin."), message_object, thread_id, thread_type, ttl=12000)

def PTA():
    return {
        'gc': handle_object_command
    }
