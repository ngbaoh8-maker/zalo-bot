import time
import random
import pytz
from datetime import datetime
from zlapi.models import Message, MultiMsgStyle, MessageStyle, ThreadType

des = {
    "version": "4.1.0",
    "credits": "ngbao",
    "description": "Lệnh /sendall: gửi tin nhắn cho toàn bộ bạn bè.",
    "power": "Admin"
}

def handle_sendall_command(message, message_object, thread_id, thread_type, author_id, bot):
    """
    /sendall <nội dung>
    Gửi tin nhắn đến toàn bộ bạn bè
    """
    try:
        args = message.split(" ", 1)
        if len(args) < 2:
            bot.sendMessage("⚠️ Dùng đúng: /sendall <nội dung>", thread_id)
            return

        send_text = args[1].strip()
        if not send_text:
            bot.sendMessage("⚠️ Nội dung tin nhắn không được rỗng!", thread_id)
            return

        # 🕓 Thời gian
        vn_tz = pytz.timezone("Asia/Ho_Chi_Minh")
        now_str = datetime.now(vn_tz).strftime("%H:%M:%S - %d/%m/%Y")

        # 👤 Tên người gọi lệnh
        try:
            info = bot.fetchUserInfo(author_id)
            author_name = (
                info.changed_profiles.get(str(author_id), {}).get("zaloName", "Không xác định")
                if info and info.changed_profiles else "Không xác định"
            )
        except:
            author_name = "Không xác định"

        # 💅 Style
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(author_name), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(author_name), style="bold", auto_format=False)
        ])

        # 🔍 Báo bắt đầu
        start_text = (
            f"{author_name}\n"
            f"🔍 Đang quét danh sách bạn bè…\n"
            f"🕓 {now_str}\n"
            f"💬 Nội dung: {send_text}"
        )
        bot.sendMessage(Message(text=start_text, style=styles), thread_id, thread_type)

        # 👥 Lấy bạn bè
        try:
            friends = bot.fetchAllFriends()
            total = len(friends)
        except:
            friends = []
            total = 0

        if total == 0:
            bot.sendMessage(
                Message(text=f"{author_name}\n⚠️ Không có bạn bè nào để gửi!", style=styles),
                thread_id, thread_type
            )
            return

        bot.sendMessage(
            Message(text=f"📌 Tìm thấy {total} bạn bè.\n🚀 Đang gửi tin nhắn…", style=styles),
            thread_id, thread_type
        )

        # 🚀 Gửi tin nhắn
        sent, failed = 0, 0

        for fr in friends:
            uid = str(fr.get("uid"))
            name = fr.get("name", "Không tên")

            try:
                bot.sendMessage(send_text, uid, ThreadType.USER)
                sent += 1
                print(f"[SENDALL] ✔ Sent to {uid}")
                time.sleep(0.4)
            except Exception as e:
                failed += 1
                print(f"[SENDALL] ✖ Failed {uid}: {e}")

        # 🧾 Kết quả
        done_str = datetime.now(vn_tz).strftime("%H:%M:%S - %d/%m/%Y")

        result = (
            f"{author_name}\n"
            f"✅ Hoàn tất gửi tin nhắn!\n"
            f"📨 Thành công: {sent}\n"
            f"⚠️ Thất bại: {failed}\n"
            f"🕓 {done_str}"
        )
        bot.sendMessage(Message(text=result, style=styles), thread_id, thread_type)

        # 🎉 Reaction
        for emo in random.sample(["🔥", "💫", "🤖", "🚀", "🎉"], 3):
            try:
                bot.sendReaction(message_object, emo, thread_id, thread_type)
            except:
                pass

    except Exception as e:
        bot.sendMessage(
            Message(text=f"❌ Lỗi sendall: {e}"),
            thread_id, thread_type
        )

def PTA():
    return {"sendall": handle_sendall_command}
