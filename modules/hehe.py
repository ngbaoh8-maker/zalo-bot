from zlapi.models import *
from zlapi.models import MessageStyle, MultiMsgStyle

des = {
    "version": "1.0.0",
    "credits": "ngbao",
    "description": "Auto gửi danh thiếp khi bị tag",
    "power": "Thành Viên"
}

# ID danh thiếp muốn gửi
CONTACT_UID = "637876082720685615"   # thay UID cần gửi danh thiếp
SEND_TEXT = "Bạn tag bot à? Đây là danh thiếp nè 🩷"

def sendStyled(text):
    return MultiMsgStyle([
        MessageStyle(offset=0, length=len(text), style="bold", size=13, auto_format=False),
        MessageStyle(offset=0, length=len(text), style="font", size=13, auto_format=False)
    ])


def handle_tag_event(message, message_object, thread_id, thread_type, author_id, client):

    # Chỉ hoạt động trong group
    if thread_type != ThreadType.GROUP:
        return

    # Nếu không có mention thì bỏ qua
    if not hasattr(message_object, "mentions") or not message_object.mentions:
        return

    # Check xem bot có bị tag không
    bot_uid = client.uid
    is_tagged = any(m.uid == bot_uid for m in message_object.mentions)

    if not is_tagged:
        return

    # Gửi tin nhắn kèm danh thiếp
    try:
        # Message text
        msg = Message(
            text=SEND_TEXT,
            style=sendStyled(SEND_TEXT)
        )

        # Tạo danh thiếp
        card = ContactCard(uid=CONTACT_UID)

        # Gửi message + contact card
        client.sendMessage(
            message=msg,
            thread_id=thread_id,
            thread_type=thread_type,
            attachments=[card]
        )

    except Exception as e:
        err = f"Lỗi auto gửi danh thiếp: {str(e)}"
        msg = Message(text=err, style=sendStyled(err))
        client.sendMessage(msg, thread_id, thread_type)


def PTA():
    return {
        "ai_tag": handle_tag_event
    }
