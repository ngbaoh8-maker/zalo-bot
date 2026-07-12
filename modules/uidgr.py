from zlapi.models import Message, ThreadType

des = {
    'version': "1.0.0",
    'credits': "ngbao",
    'description': "Lấy ID nhóm (box) hiện tại",
    'power': "Thành viên"
}

def handle_uidgr_command(message, message_object, thread_id, thread_type, author_id, client):
    if thread_type == ThreadType.USER:
        client.replyMessage(
            Message(text="❌ Lệnh này chỉ dùng trong nhóm!"),
            message_object, thread_id, thread_type
        )
        return

    response_message = f"📌 ID Box: {thread_id}"
    client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type)

def PTA():
    return {
        'uidgr': handle_uidgr_command
    }
