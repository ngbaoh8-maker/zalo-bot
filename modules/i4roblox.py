from zlapi.models import Message, ThreadType
import requests
from datetime import datetime

des = {
    'version': "1.1.1",
    'credits': "ngbao",
    'description': "Thông tin acc Roblox (dynamic)",
    'power': "Thành Viên"
}

def handle_rb_command(message, message_object, thread_id, thread_type, author_id, client):

    parts = message.strip().split()
    if len(parts) < 2:
        client.sendMessage(
            Message(text="❌ Dùng: /rb <username | userid>"),
            thread_id, thread_type
        )
        return

    query = parts[1]

    try:
        if query.isdigit():
            user_id = query
        else:
            r = requests.post(
                "https://users.roblox.com/v1/usernames/users",
                json={"usernames": [query]}
            ).json()
            if not r.get("data"):
                raise Exception("Khong tim thay user")
            user_id = str(r["data"][0]["id"])

        info = requests.get(
            f"https://users.roblox.com/v1/users/{user_id}"
        ).json()

        username = info.get("name", "N/A")
        display = info.get("displayName", "N/A")
        desc = info.get("description") or "..."
        verified = "✅" if info.get("hasVerifiedBadge") else "❌"
        status = "❌ BỊ KHÓA" if info.get("isBanned") else "✅ HOẠT ĐỘNG"

        created = datetime.fromisoformat(
            info["created"].replace("Z", "")
        ).strftime("%d/%m/%Y %H:%M")

        premium = requests.get(
            f"https://premiumfeatures.roblox.com/v1/users/{user_id}/validate-membership"
        ).json()
        premium_txt = "✅ CÓ" if premium else "❌ KHÔNG"

        friends = requests.get(
            f"https://friends.roblox.com/v1/users/{user_id}/friends/count"
        ).json()["count"]

        followers = requests.get(
            f"https://friends.roblox.com/v1/users/{user_id}/followers/count"
        ).json()["count"]

        following = requests.get(
            f"https://friends.roblox.com/v1/users/{user_id}/followings/count"
        ).json()["count"]

        msg = (
            f"📊 THÔNG TIN ROBLOX: {username}\n"
            f"──────────────\n"
            f"👤 Tên hiển thị: {display}\n"
            f"🆔 ID: {user_id}\n"
            f"🛡️ Verified: {verified}\n"
            f"📅 Ngày tạo: {created}\n"
            f"📝 Mô tả: {desc}\n"
            f"──────────────\n"
            f"💰 Robux: N/A\n"
            f"🌟 Premium: {premium_txt}\n"
            f"👥 Bạn bè: {friends}\n"
            f"📡 Followers: {followers}\n"
            f"👀 Following: {following}\n"
            f"🔐 Trạng thái: {status}"
        )

        client.sendMessage(Message(text=msg), thread_id, thread_type)

    except Exception as e:
        client.sendMessage(
            Message(text=f"⚠️ Lỗi Roblox: {e}"),
            thread_id, thread_type
        )

def PTA():
    return {'i4rbl': handle_rb_command}
