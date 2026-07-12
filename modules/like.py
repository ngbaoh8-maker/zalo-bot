from zlapi.models import Message, MessageStyle, MultiMsgStyle
from datetime import datetime

import requests
import random
import time

des = {
    'version': "1.1.0",
    'credits': "ngbao",
    'description': "Buff like Free Fire kèm thông tin tài khoản (giả lập)",
    'power': "Thành Viên"
}

def handle_buffff_command(message, message_object, thread_id, thread_type, author_id, client):

    # ====== LẤY TÊN NGƯỜI DÙNG (TRÁNH LỖI user_name) ======
    try:
        # Ưu tiên lấy từ cache nếu có
        if hasattr(client, "dname_cache"):
            user_name = client.dname_cache.get(author_id, str(author_id))
        else:
            user_info = client.getUserInfo(author_id)
            user_name = user_info.display_name if hasattr(user_info, "display_name") else str(author_id)
    except Exception:
        user_name = str(author_id)

    # ====== XỬ LÝ LỆNH ======
    parts = message.strip().split()

    if len(parts) < 2:
        client.sendMessage(
            Message(text=f"❌ Thiếu UID!\n\n📌 Cách dùng:\n`like <uid>`\n\nVí dụ: `like 123456789`\n\n[Ask by: {user_name}]"),
            thread_id, thread_type
        )
        return

    uid = parts[1]
    region = "SG"

    try:
        # Lấy info từ API Free Fire (giống file pro_ff.py)
        url = f"https://accinfo.vercel.app/player-info?region={region}&uid={uid}"
        res = requests.get(url, timeout=8)

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

        # ====== PHẦN BUFF LIKE GIẢ LẬP ======
        buff_added = random.randint(200, 1000)
        total_likes = liked + buff_added
        speed = random.randint(100, 250)
        time.sleep(random.uniform(0.3, 1.0))
        now = datetime.now().strftime("%H:%M:%S - %d/%m/%Y")

        # ====== TẠO NỘI DUNG HIỂN THỊ ======
        msg_lines = [
            f"🔥 Buff like Free Fire thành công!",
            "━━━━━━━━━━━━━━━━━━━",
            f"💖 Tổng like: {total_likes:,} (+{buff_added:,} mới)",
            f"⚡ Tốc độ: {speed} like/giây",
            "━━━━━━━━━━━━━━━━━━━",
            "📦 [Thông Tin Free Fire]",
            "━━━━━━━━━━━━━━━━━━━",
            f"👤 Nickname: {nickname}",
            f"🆔 UID: {uid} ({region})",
            f"📈 Cấp độ: {level}",
            f"🏆 Rank BR: {rank} | CS: {cs_rank}",
            f"👑 Clan: {clan_name}",
            f"🐾 Pet chính: {pet_name} (Lv.{pet_lv})",
            f"📅 Ngày tạo tài khoản: {created_at}",
            f"📝 Tiểu sử: {signature if signature else 'Không có'}",
            "━━━━━━━━━━━━━━━━━━━",
            f"👤 Người thực hiện: {user_name}",
            f"🕓 Thời gian: {now}"
        ]
        msg = "\n".join(msg_lines)

        # ====== TÍNH OFFSET CHO STYLE ======
        offsets = []
        off = 0
        for line in msg_lines:
            offsets.append(off)
            off += len(line) + 1

        # ====== STYLE GIỐNG FILE pro_ff.py ======
        styles = [
            # tiêu đề buff
            MessageStyle(offset=offsets[0], length=len(msg_lines[0]), style="bold"),
            MessageStyle(offset=offsets[0], length=len(msg_lines[0]), style="color", color="#E67E22"),

            # tổng like
            MessageStyle(offset=offsets[2] + 12, length=len(f"{total_likes:,}"), style="color", color="#E74C3C"),
            MessageStyle(offset=offsets[2] + 14 + len(f"{total_likes:,}"), length=len(f"+{buff_added:,} mới"), style="color", color="#2ECC71"),

            # tốc độ
            MessageStyle(offset=offsets[3] + 10, length=len(str(speed)), style="color", color="#F1C40F"),

            # tiêu đề Info
            MessageStyle(offset=offsets[5], length=len(msg_lines[5]), style="bold"),
            MessageStyle(offset=offsets[5], length=len(msg_lines[5]), style="color", color="#15A85F"),

            # nickname
            MessageStyle(offset=offsets[7] + 13, length=len(nickname), style="color", color="#3498DB"),

            # UID
            MessageStyle(offset=offsets[8] + 9, length=len(uid), style="color", color="#E67E22"),

            # Level
            MessageStyle(offset=offsets[9] + 10, length=len(str(level)), style="color", color="#2ECC71"),

            # Rank
            MessageStyle(offset=offsets[10] + 12, length=len(str(rank)), style="color", color="#9B59B6"),
            MessageStyle(offset=offsets[10] + 23, length=len(str(cs_rank)), style="color", color="#8E44AD"),

            # Clan
            MessageStyle(offset=offsets[11] + 8, length=len(clan_name), style="color", color="#F1C40F"),

            # Pet
            MessageStyle(offset=offsets[12] + 14, length=len(pet_name), style="color", color="#1ABC9C"),

            # Ngày tạo
            MessageStyle(offset=offsets[13] + 24, length=len(created_at), style="color", color="#95A5A6"),

            # Người thực hiện
            MessageStyle(offset=offsets[-2] + 17, length=len(user_name), style="color", color="#2980B9"),

            # Thời gian
            MessageStyle(offset=offsets[-1] + 10, length=len(now), style="color", color="#9B59B6")
        ]

        if signature:
            styles.append(MessageStyle(offset=offsets[14] + 13, length=len(signature), style="color", color="#7F8C8D"))

        style_pack = MultiMsgStyle(styles)
        client.sendMessage(Message(text=msg, style=style_pack), thread_id, thread_type)

    except Exception as e:
        client.sendMessage(
            Message(text=f"⚠️ Lỗi khi xử lý: {e}\n\n[Ask by: {user_name}]"),
            thread_id, thread_type
        )

# ===============================
# ĐĂNG KÝ LỆNH
# ===============================
def PTA():
    return {
        'like': handle_buffff_command
    }
