import os
import requests
from zlapi.models import Message
from datetime import datetime

des = {
    'version': "1.2.2",
    'credits': "ngbao",
    'description': "Xem avatar + thông tin TikTok (gửi kèm caption ảnh)",
    'power': "Thành viên"
}

def safe_get(data, key, default="Không có"):
    return data.get(key, default) if data and data.get(key) not in [None, ""] else default

def tiktok_command(message, message_object, thread_id, thread_type, author_id, client):
    parts = message.strip().split()
    if len(parts) < 2:
        client.sendMessage(
            Message(text="⚠️ Vui lòng nhập username TikTok.\nVí dụ: ,i4tt <UID>"),
            thread_id, thread_type
        )
        return

    username = parts[1]
    api_url = f"https://api.zeidteam.xyz/tiktok/user-info?username={username}"

    try:
        res = requests.get(api_url, timeout=10)
        data = res.json()

        if not data.get("status"):
            client.sendMessage(
                Message(text="❌ Không tìm thấy tài khoản TikTok!"),
                thread_id, thread_type
            )
            return

        user = data.get("data", {}).get("user", {})
        stats = data.get("data", {}).get("stats", {})

        create_time_raw = safe_get(user, "createTime", None)
        if create_time_raw and str(create_time_raw).isdigit():
            create_time = datetime.fromtimestamp(int(create_time_raw)).strftime("%d/%m/%Y")
        else:
            create_time = "Không rõ"

        is_live = "Có" if user.get("liveStatus") else "Không"
        is_online = "Có" if user.get("isActive") else "Không"

        caption = f"""✨ Thông tin TikTok ✨

👤 Nickname : {safe_get(user, 'nickname')}
🔗 Username : {safe_get(user, 'uniqueId')}
🆔 ID       : {safe_get(user, 'id')}
🆔 SecUid   : {safe_get(user, 'secUid')}
✅ Verified : {"Có" if user.get('verified') else "Không"}
🔒 Private  : {"Có" if user.get('privateAccount') else "Không"}
🟢 Online   : {is_online}
📺 Live     : {is_live}
📝 Bio      : {safe_get(user, 'signature')}

📊 Thống kê:
👥 Đang follow : {safe_get(stats, 'followingCount', 0)}
👥 Follower    : {safe_get(stats, 'followerCount', 0)}
👥 Bạn bè      : {safe_get(stats, 'friendCount', "Không có")}
❤️ Tổng like   : {safe_get(stats, 'heartCount', 0)}
👍 Đã like     : {safe_get(stats, 'diggCount', 0)}
🎥 Số video    : {safe_get(stats, 'videoCount', 0)}

🌍 Khác:
🇦🇺 Region    : {safe_get(user, 'region')}
🌐 Ngôn ngữ   : {safe_get(user, 'language')}
🕑 Tạo lúc    : {create_time}
🏠 Room ID    : {safe_get(user, 'roomId')}

🔗 Link Profile : https://www.tiktok.com/@{safe_get(user, 'uniqueId')}"""

        avatar_url = user.get('avatarLarger') or user.get('avatarMedium') or user.get('avatarThumb')
        if avatar_url:
            output_path = "modules/cache/tiktok_avatar.png"
            r = requests.get(avatar_url, stream=True, timeout=10)
            if r.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(r.content)

                # ✅ Gửi ảnh TRƯỚC
                client.sendLocalImage(
                    output_path,
                    thread_id=thread_id,
                    thread_type=thread_type
                )

                # ✅ Sau đó gửi caption
                client.sendMessage(
                    Message(text=caption),
                    thread_id, thread_type
                )

                os.remove(output_path)
            else:
                client.sendMessage(Message(text=caption), thread_id, thread_type)
        else:
            client.sendMessage(Message(text=caption), thread_id, thread_type)

    except Exception as e:
        client.sendMessage(
            Message(text=f"❌ Lỗi khi gọi API TikTok!\nChi tiết: {e}"),
            thread_id, thread_type
        )


def PTA():
    return {
        'i4tt': tiktok_command
    }
