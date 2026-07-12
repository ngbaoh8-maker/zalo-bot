import json
import time
from zlapi.models import Message, MultiMsgStyle, MessageStyle
from config import ADMIN

des = {
    "version": "1.0.3",
    "credits": "ngbao",
    "description": "Chấp nhận toàn bộ lời mời kết bạn",
    "power": "Quản trị viên Bot"
}


# ==========================
# ⚙️ HÀM CHÍNH
# ==========================

def do_acceptfriend(message, message_object, thread_id, thread_type, author_id, client):
    """Chỉ ADMIN mới được phép dùng lệnh này"""
    # Lấy tên người dùng
    try:
        user_info = client.fetchUserInfo(author_id)
        author_info = user_info.changed_profiles.get(str(author_id), {}) if user_info and user_info.changed_profiles else {}
        name = author_info.get('zaloName', 'Không xác định')
    except Exception:
        name = "Không xác định"

    # Kiểm tra quyền (dùng trực tiếp ADMIN từ config)
    if str(author_id) != str(ADMIN):
        rest_text = "Bạn không đủ quyền hạn để sử dụng lệnh này! 😠"
        msg = f"{name}\n➜ {rest_text}"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
        ])
        client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=5000)
        return

    # Gửi thông báo bắt đầu
    client.sendMessage(Message(text="🔍 Đang kiểm tra danh sách lời mời kết bạn..."), thread_id, thread_type)

    friend_requests = fetch_friend_requests_safe(client)

    # 📨 Không có lời mời -> thoát luôn
    if not friend_requests:
        client.sendMessage(Message(text="📭 Không có lời mời kết bạn nào cần xử lý."), thread_id, thread_type)
        return

    # ✅ Có lời mời thì bắt đầu xử lý
    total_requests = len(friend_requests)
    client.sendMessage(
        Message(text=f"🤝 Tìm thấy {total_requests} lời mời kết bạn, đang tiến hành chấp nhận..."),
        thread_id,
        thread_type
    )

    success_count = 0
    fail_count = 0

    for friend in friend_requests:
        uid = friend.get("uid") or friend.get("userId")
        if uid:
            if try_accept_friend(client, uid):
                success_count += 1
            else:
                fail_count += 1
        time.sleep(0.3)

    # ✅ Hoàn tất xử lý
    result_text = (
        f"✅ **Đã xử lý xong lời mời kết bạn!**\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"💚 Thành công: {success_count}\n"
        f"💔 Thất bại: {fail_count}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"✨ Tổng số yêu cầu đã kiểm tra: {total_requests}"
    )

    client.sendMessage(Message(text=result_text), thread_id, thread_type)


# ==========================
# 🔧 HÀM HỖ TRỢ
# ==========================

def fetch_friend_requests_safe(client):
    """Lấy danh sách lời mời kết bạn"""
    try:
        friend_data = client.getFriendRequests()
        return friend_data if friend_data else []
    except Exception as e:
        print(f"⚠️ Lỗi khi lấy danh sách lời mời kết bạn: {e}")
        return []


def try_accept_friend(client, uid):
    """Thử chấp nhận kết bạn từng UID"""
    try:
        client.acceptFriend(uid)
        return True
    except Exception as e:
        print(f"❌ Lỗi khi chấp nhận UID {uid}: {e}")
        return False


# ==========================
# 📦 HÀM QUẢN LÝ LỆNH
# ==========================

def PTA():
    return {"acceptfriend": do_acceptfriend}