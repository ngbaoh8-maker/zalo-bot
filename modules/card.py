from zlapi.models import Message, MultiMsgStyle, MessageStyle, ThreadType

des = {
    'version': "1.0.8",
    'credits': "ngbao",
    'description': "Tạo card thông tin người dùng",
    'power': "Thành viên"
}

def handle_cardinfo_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        # --- Xử lý TTL ---
        parts = message.strip().split()
        ttl = 10000  # mặc định 10s
        if len(parts) > 1:
            try:
                ttl_candidate = int(parts[-1])
                if ttl_candidate > 0:
                    ttl = ttl_candidate
            except ValueError:
                pass

        # --- Nếu có tag thì lấy người được tag, không thì lấy bản thân ---
        if message_object.mentions and len(message_object.mentions) > 0:
            userId = message_object.mentions[0]['uid']
        else:
            userId = author_id

        user_info = client.fetchUserInfo(userId).changed_profiles.get(userId)

        if not user_info:
            msg = "• Không thể lấy thông tin người dùng."
            client.send(Message(text=msg), thread_id=thread_id, thread_type=thread_type, ttl=ttl)
            return

        avatarUrl = user_info.avatar
        zaloName = user_info.zaloName if hasattr(user_info, "zaloName") else "Không xác định"

        if not avatarUrl:
            msg = f"• Người dùng {zaloName} không có ảnh đại diện."
            client.send(Message(text=msg), thread_id=thread_id, thread_type=thread_type, ttl=ttl)
            return

        # --- Gửi card ---
        client.sendBusinessCard(
            userId=userId,
            qrCodeUrl=avatarUrl,
            thread_id=thread_id,
            thread_type=thread_type,
            phone=f"Zalo: {zaloName}",
            ttl=ttl
        )

        # --- Gửi thông báo chữ đỏ ---
        rest_text = f"Đã tạo card cho {zaloName} ✅"
        msg = f"{zaloName}\n➜ {rest_text}"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(zaloName), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(zaloName), style="bold", auto_format=False),
        ])
        client.send(Message(text=msg, style=styles), thread_id=thread_id, thread_type=thread_type, ttl=ttl)

    except Exception as e:
        error_message = f"• Lỗi khi thực hiện lệnh card: {str(e)}"
        client.send(Message(text=error_message), thread_id=thread_id, thread_type=thread_type, ttl=10000)


def PTA():
    return {
        'card': handle_cardinfo_command
    }