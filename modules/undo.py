from zlapi.models import Message, MultiMsgStyle, MessageStyle
from config import PREFIX, ADMIN
ADMIN_ID = ADMIN

des = {
    'version': "1.0.3",
    'credits': "ngbao",
    'description': "Thu hồi tin nhắn người dùng",
    'power': "Thành viên"
}

def handle_undo_command(message, message_object, thread_id, thread_type, author_id, client):
    if author_id not in ADMIN:
        msg = "• Bạn không có quyền sử dụng lệnh này."
        client.replyMessage(Message(text=msg), message_object, thread_id, thread_type, ttl=60000)
        return

    if message_object.quote:
        msg2undo = message_object.quote
        msg_id = msg2undo.globalMsgId
        cli_msg_id = msg2undo.cliMsgId
    else:
        msg = f"• Reply tin nhắn cần thu hồi."
        client.replyMessage(Message(text=msg), message_object, thread_id, thread_type, ttl=12000)
        return
    try:
        client.undoMessage(msg_id, cli_msg_id, thread_id, thread_type)
    except Exception as e:
        error_message = f"• Lỗi khi thu hồi tin nhắn: {str(e)}"
        print(error_message)

def PTA():
    return {
        'undo': handle_undo_command
    }
