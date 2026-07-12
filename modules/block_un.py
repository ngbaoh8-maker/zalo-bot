import json
from zlapi.models import Message, MultiMsgStyle, MessageStyle, ThreadType
from config import PREFIX, ADMIN

des = {
    'version': "1.0.2",
    'credits': "ngbao",
    'description': "Chặn và mở chặn người dùng.",
    'power': "Quản trị viên Bot"
}

ADMIN_ID = ADMIN


def is_admin(author_id):
    return str(author_id) == ADMIN_ID


# ======= Hàm gửi tin có tên đỏ đậm =======
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


# ==================== CHẶN NGƯỜI DÙNG ====================
def handle_block(message, message_object, thread_id, thread_type, author_id, client):
    user_info = client.fetchUserInfo(author_id)
    author_info = user_info.changed_profiles.get(str(author_id), {}) if user_info and user_info.changed_profiles else {}
    name = author_info.get('zaloName', 'Không xác định')

    if not is_admin(author_id):
        send_styled_reply(client, "Bạn không đủ quyền hạn để sử dụng lệnh này! 😠",
                          name, message_object, thread_id, thread_type, ttl=5000)
        return

    user_id = None
    if thread_type == ThreadType.USER:
        user_id = thread_id
    elif message_object.mentions:
        user_id = message_object.mentions[0]['uid']

    if not user_id:
        send_styled_reply(client, "Vui lòng tag người dùng để chặn hoặc sử dụng lệnh trong cuộc trò chuyện riêng.",
                          name, message_object, thread_id, thread_type, ttl=6000)
        return

    try:
        client.blockUser(user_id)
        send_styled_reply(client, "Đã chặn người dùng 🚫",
                          name, message_object, thread_id, thread_type, ttl=6000)
    except Exception as e:
        send_styled_reply(client, f"Không thể chặn người dùng. Lỗi: {str(e)}",
                          name, message_object, thread_id, thread_type, ttl=6000)


# ==================== MỞ CHẶN NGƯỜI DÙNG ====================
def handle_unblock(message, message_object, thread_id, thread_type, author_id, client):
    user_info = client.fetchUserInfo(author_id)
    author_info = user_info.changed_profiles.get(str(author_id), {}) if user_info and user_info.changed_profiles else {}
    name = author_info.get('zaloName', 'Không xác định')

    if not is_admin(author_id):
        send_styled_reply(client, "Bạn không đủ quyền hạn để sử dụng lệnh này! 😠",
                          name, message_object, thread_id, thread_type, ttl=5000)
        return

    user_id = None
    if thread_type == ThreadType.USER:
        user_id = thread_id
    elif message_object.mentions:
        user_id = message_object.mentions[0]['uid']

    if not user_id:
        send_styled_reply(client, "Vui lòng tag người dùng để mở chặn hoặc dùng trong chat riêng.",
                          name, message_object, thread_id, thread_type, ttl=6000)
        return

    try:
        client.unblockUser(user_id)
        send_styled_reply(client, "Đã mở chặn người dùng ✅",
                          name, message_object, thread_id, thread_type, ttl=6000)
    except Exception as e:
        send_styled_reply(client, f"Không thể mở chặn người dùng. Lỗi: {str(e)}",
                          name, message_object, thread_id, thread_type, ttl=6000)


# ==================== ĐĂNG KÝ LỆNH ====================
def PTA():
    return {
        'block': handle_block,
        'unblock': handle_unblock
    }