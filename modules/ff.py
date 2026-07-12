from zlapi.models import Message, ThreadType, MessageStyle, MultiMsgStyle
import requests
from datetime import datetime

des = {
    'version': "1.0.0",
    'credits': "ngbao",
    'description': "Lấy thông tin tài khoản Free Fire từ UID",
    'power': "Thành viên"
}

def handle_ff_command(message, message_object, thread_id, thread_type, author_id, client):

    # ✅ Thêm phần lấy tên người gửi
    try:
        user_info = client.fetchUserInfo(author_id)
        user_name = user_info.name if user_info else "Người dùng"
    except:
        user_name = "Người dùng"

    parts = message.strip().split()

    if len(parts) < 2:
        client.sendMessage(
            Message(text=f"❌ Thiếu UID!\n\n📌 **Cách dùng:**\n`/ff <uid>`\n\nVí dụ: `/ff 12345678`\n\n[Ask by: {user_name}]"),
            thread_id, thread_type
        )
        return

    uid = parts[1]
    region = "SG"

    try:
        url = f"https://accinfo.vercel.app/player-info?region={region}&uid={uid}"
        res = requests.get(url)

        if res.status_code != 200 or not res.json().get("basicInfo"):
            client.sendMessage(
                Message(text=f"❌ Không tìm thấy tài khoản hoặc UID sai.\n\n[Ask by: {user_name}]"),
                thread_id, thread_type
            )
            return

        data = res.json()
        basic = data["basicInfo"]
        clan = data.get("clanBasicInfo", {})
        pet = data.get("petInfo", {})
        social = data.get("socialInfo", {})

        nickname = basic.get("nickname", "Không rõ")
        level = basic.get("level", 0)
        rank = basic.get("rank", 0)
        cs_rank = basic.get("csRank", 0)
        liked = basic.get("liked", 0)
        clan_name = clan.get("clanName", "Không có")
        pet_name = pet.get("name", "Không có")
        pet_lv = pet.get("level", 0)
        signature = social.get("signature", "Chưa có")
        created_at = datetime.fromtimestamp(int(basic.get("createAt", 0))).strftime("%d/%m/%Y")

        msg_lines = [
            f"💎 [Thông Tin Free Fire]",
            "━━━━━━━━━━━━━━━━━━━",
            f"👤 Nickname: {nickname}",
            f"🆔 UID: {uid} ({region})",
            f"📈 Cấp độ: {level}",
            f"🏆 Rank BR: {rank} | CS: {cs_rank}",
            f"❤️ Lượt thích: {liked:,}",
            f"👑 Clan: {clan_name}",
            f"🐾 Pet chính: {pet_name} (Lv.{pet_lv})",
            f"📅 Ngày tạo tài khoản: {created_at}",
            f"📝 Tiểu sử: {signature if signature else 'Không có'}",
            "━━━━━━━━━━━━━━━━━━━",
            f"[Ask by: {user_name}]"
        ]
        msg = "\n".join(msg_lines)

        offsets = []
        current_offset = 0
        for line in msg_lines:
            offsets.append(current_offset)
            current_offset += len(line) + 1

        style_list = [
            MessageStyle(offset=offsets[0], length=len(msg_lines[0]), style="bold"),
            MessageStyle(offset=offsets[0], length=len(msg_lines[0]), style="color", color="#15A85F"),
            MessageStyle(offset=offsets[2] + 13, length=len(nickname), style="color", color="#3498DB"),
            MessageStyle(offset=offsets[3] + 9, length=len(uid), style="color", color="#E67E22"),
            MessageStyle(offset=offsets[4] + 13, length=len(str(level)), style="color", color="#2ECC71"),
            MessageStyle(offset=offsets[5] + 13, length=len(str(rank)), style="color", color="#9B59B6"),
            MessageStyle(offset=offsets[5] + 24, length=len(str(cs_rank)), style="color", color="#8E44AD"),
            MessageStyle(offset=offsets[6] + 15, length=len(f"{liked:,}"), style="color", color="#E74C3C"),
            MessageStyle(offset=offsets[7] + 9, length=len(clan_name), style="color", color="#F1C40F"),
            MessageStyle(offset=offsets[8] + 14, length=len(pet_name), style="color", color="#1ABC9C"),
            MessageStyle(offset=offsets[9] + 23, length=len(created_at), style="color", color="#95A5A6"),
        ]

        if signature:
            style_list.append(
                MessageStyle(offset=offsets[10] + 13, length=len(signature), style="color", color="#7F8C8D")
            )

        styles = MultiMsgStyle(style_list)
        client.sendMessage(Message(text=msg, style=styles), thread_id, thread_type)

    except Exception as e:
        client.sendMessage(
            Message(text=f"⚠️ Có lỗi xảy ra khi xử lý: {e}\n\n[Ask by: {user_name}]"),
            thread_id, thread_type
        )

def PTA():
    return {
        'ff': handle_ff_command
    }
