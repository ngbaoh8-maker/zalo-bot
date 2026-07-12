import json
import time
from zlapi.models import Message, MultiMsgStyle, MessageStyle, ThreadType
from config import PREFIX, ADMIN

des = {
    'version': "1.0.2",
    'credits': "ngbao",
    'description': "Gửi lời mời kết bạn cá nhân hoặc hàng loạt trong nhóm.",
    'power': "Admin"
}

ADMIN_ID = ADMIN


def is_admin(author_id):
    return str(author_id) == ADMIN_ID


# ======= Hàm gửi tin nhắn có tên đỏ đậm =======
def send_styled_reply(client, text, name, message_object, thread_id, thread_type, ttl=6000):
    styles = MultiMsgStyle([
        MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
        MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
    ])
    msg = f"{name}\n➜{text}"
    client.replyMessage(
        Message(text=msg, style=styles),
        message_object, thread_id, thread_type, ttl=ttl
    )


# ==================== GỬI KẾT BẠN MỘT NGƯỜI ====================
def handle_addfri(message, message_object, thread_id, thread_type, author_id, client):
    user_info = client.fetchUserInfo(author_id)
    author_info = user_info.changed_profiles.get(str(author_id), {}) if user_info and user_info.changed_profiles else {}
    name = author_info.get('zaloName', 'Không xác định')

    if not is_admin(author_id):
        send_styled_reply(client, "Bạn không đủ quyền hạn để sử dụng lệnh này! 😠",
                          name, message_object, thread_id, thread_type, ttl=5000)
        return

    # Xác định user_id mục tiêu
    user_id = None
    if thread_type == ThreadType.USER:
        user_id = thread_id
    elif message_object.mentions:
        user_id = message_object.mentions[0]['uid']

    if not user_id:
        send_styled_reply(client, "Vui lòng tag người dùng để kết bạn hoặc dùng trong cPTA riêng.",
                          name, message_object, thread_id, thread_type)
        return

    try:
        client.sendFriendRequest(user_id, "Xin chào, mình muốn kết bạn!")
        send_styled_reply(client, "Đã gửi lời mời kết bạn 🤝",
                          name, message_object, thread_id, thread_type)
    except Exception as e:
        send_styled_reply(client, f"Không thể gửi lời mời kết bạn. Lỗi: {str(e)}",
                          name, message_object, thread_id, thread_type)


# ==================== GỬI KẾT BẠN HÀNG LOẠT ====================
def handle_addallfri(message, message_object, thread_id, thread_type, author_id, client):
    user_info = client.fetchUserInfo(author_id)
    author_info = user_info.changed_profiles.get(str(author_id), {}) if user_info and user_info.changed_profiles else {}
    name = author_info.get('zaloName', 'Không xác định')

    if not is_admin(author_id):
        send_styled_reply(client, "Bạn không đủ quyền hạn để sử dụng lệnh này! 😠",
                          name, message_object, thread_id, thread_type, ttl=5000)
        return

    try:
        _, content = message.split(' ', 1)
    except ValueError:
        send_styled_reply(client, f"Sai cú pháp. Dùng: {PREFIX}addallfri \"Nội dung kết bạn\"",
                          name, message_object, thread_id, thread_type)
        return

    if not (content.startswith('"') and content.endswith('"')):
        send_styled_reply(client, f"Vui lòng đặt nội dung trong dấu ngoặc kép. Ví dụ: {PREFIX}addallfri \"Xin chào, mình muốn kết bạn!\"",
                          name, message_object, thread_id, thread_type)
        return

    content = content.strip('"')

    try:
        group_info = client.fetchGroupInfo(thread_id).gridInfoMap[thread_id]
        members = group_info.get('memVerList', [])
        total_members = len(members)
        success = 0

        for mem in members:
            user_id = mem.split('_')[0]
            try:
                client.sendFriendRequest(user_id, content)
                success += 1
            except Exception as e:
                print(f"Lỗi gửi kết bạn cho {user_id}: {str(e)}")
            time.sleep(0.5)

        send_styled_reply(client,
                          f"Đã gửi lời mời kết bạn đến {success}/{total_members} thành viên.\n📩 Nội dung: {content}",
                          name, message_object, thread_id, thread_type, ttl=8000)
    except Exception as e:
        send_styled_reply(client, f"Lỗi khi gửi lời mời hàng loạt: {str(e)}",
                          name, message_object, thread_id, thread_type, ttl=8000)


# ==================== KHAI BÁO LỆNH ====================
def PTA():
    return {
        'kb': handle_addfri,
        'kball': handle_addallfri
    }