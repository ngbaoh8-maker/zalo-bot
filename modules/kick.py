from zlapi.models import Message, MultiMsgStyle, MessageStyle, Mention
from config import ADMIN

ADMIN_ID = ADMIN

des = {
    'version': "1.0.5",
    'credits': "Hoàng Anh Tuấn",
    'description': "Kick thành viên trong nhóm (toàn bộ thu hồi sau 6s)",
    'power': "Quản trị viên Bot"
}

def handle_kick_command(message, message_object, thread_id, thread_type, author_id, client):
    TTL = 6000  # 6 giây

    # Kiểm tra quyền admin bot
    if author_id not in ADMIN:
        msg = "🚫 Sếp ơi, có thèn đòi dùng lệnh sếp :33"
        client.replyMessage(Message(text=msg), message_object, thread_id, thread_type, ttl=TTL)
        return

    # Xác định danh sách người cần kick
    user_ids_to_kick = []
    if message_object.mentions:
        user_ids_to_kick.extend([mention.uid for mention in message_object.mentions])
    elif message_object.quote:
        user_ids_to_kick.append(str(message_object.quote.ownerId))

    if not user_ids_to_kick:
        msg = "Nhập như vầy nè Sếp :D\nkick [reply] hoặc @user1 @user2 ✅"
        client.replyMessage(Message(text=msg), message_object, thread_id, thread_type, ttl=TTL)
        return

    # Lấy thông tin nhóm
    group_data = client.fetchGroupInfo(thread_id).gridInfoMap[thread_id]
    admins = group_data.adminIds
    owners = group_data.creatorId

    if client.uid not in admins and client.uid != owners:
        msg = "Đưa Em Key Bạc 🗝️, Em Kick Cho Sếp Xem :D"
        client.replyMessage(Message(text=msg), message_object, thread_id, thread_type, ttl=TTL)
        return

    kicked_names = []
    for user_id in user_ids_to_kick:
        if user_id in admins or user_id == owners:
            if user_id in admins:
                msg = "Thưa Sếp, em không thể kick key bạc của nhóm! 🚫"
            elif user_id == owners:
                msg = "Thưa Sếp, em không thể kick key vàng của nhóm! 🚫"
            client.replyMessage(Message(text=msg), message_object, thread_id, thread_type, ttl=TTL)
            continue
        
        try:
            user_info = client.fetchUserInfo(user_id)
            user_name = user_info.changed_profiles[user_id].zaloName
        except Exception:
            user_name = "Người dùng ẩn danh"

        # Kick người đó
        client.kickUsersInGroup(user_id, thread_id)
        kicked_names.append(user_name)

        # Gửi thông báo riêng cho mỗi người bị kick (chữ đỏ + in đậm)
        msg = f"{user_name}\n➜ Đã bị Sếp đá khỏi nhóm 🚪"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(user_name), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(user_name), style="bold", auto_format=False),
        ])
        client.send(Message(text=msg, style=styles), thread_id, thread_type, ttl=TTL)

    # Sau khi kick xong gửi tổng kết có tag Sếp
    if kicked_names:
        list_names = ", ".join(kicked_names)
        try:
            s_name = client.fetchUserInfo(author_id).changed_profiles[author_id].zaloName
        except Exception:
            s_name = "Sếp"
        mention_text = f"@{s_name}"
        msg = f"{mention_text}\n🧹 Báo Sếp: Đã đá {list_names} khỏi nhóm ✅"
        
        # Tạo style + mention màu đỏ
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(mention_text), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(mention_text), style="bold", auto_format=False),
        ])
        mentions = [Mention(uid=author_id, offset=0, length=len(mention_text))]
        client.send(Message(text=msg, style=styles, mentions=mentions), thread_id, thread_type, ttl=TTL)


def PTA():
    return {
        'kick': handle_kick_command
    }