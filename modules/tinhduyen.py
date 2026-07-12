import json
import os
import random
from zlapi.models import Message, MultiMsgStyle, MessageStyle
from config import PREFIX, ADMIN

des = {
    'version': "1.0.8",
    'credits': "ngbao",
    'description': "Bói tình duyên bằng cách tag 2 người 💕",
    'power': "Thành Viên"
}

def boi_tinh_duyen(ten1, ten2):
    """Sinh ngẫu nhiên % hợp nhau"""
    return random.randint(0, 100)

def send_tag_error(client, message_object, thread_id, thread_type, text):
    """Gửi thông báo lỗi bình thường, không in đậm"""
    client.replyMessage(
        Message(text=text),
        message_object, thread_id, thread_type, ttl=8000
    )

def handle_boitinhduyen_command(message, message_object, thread_id, thread_type, author_id, client):
    mentions = message_object.mentions

    # 🧩 Kiểm tra tag hợp lệ
    if not mentions or len(mentions) == 0:
        send_tag_error(client, message_object, thread_id, thread_type, "⚠️ Vui lòng tag đúng 2 người để bói tình duyên!")
        return

    if len(mentions) < 2:
        send_tag_error(client, message_object, thread_id, thread_type, "⚠️ Bạn cần tag đủ 2 người để bói tình duyên!")
        return

    if len(mentions) > 2:
        send_tag_error(client, message_object, thread_id, thread_type, "⚠️ Chỉ được tag tối đa 2 người để bói tình duyên!")
        return

    try:
        # 🧍‍♂️🧍‍♀️ Lấy thông tin 2 người
        uid1 = mentions[0]['uid']
        uid2 = mentions[1]['uid']

        user1 = client.fetchUserInfo(uid1)
        user2 = client.fetchUserInfo(uid2)

        name1 = user1.changed_profiles.get(str(uid1), {}).get('zaloName', 'Người 1')
        name2 = user2.changed_profiles.get(str(uid2), {}).get('zaloName', 'Người 2')

        # 💖 Random độ hợp nhau
        percent = boi_tinh_duyen(name1, name2)

        # ✍️ Soạn nội dung
        msg_text = (
            "💘 𝔹𝕆́𝕀 𝕋𝕀̀ℕℍ 𝔻𝕌𝕐𝔼̂ℕ 💘\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            f"💑 Cặp đôi: {name1} ❤️ {name2}\n"
            f"💞 Mức độ hợp nhau: {percent}%\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "✨ Chúc hai bạn luôn hạnh phúc nhé ✨\n\n"
            "👑 Dương Văn Nam"
        )

        # 🎨 Làm chữ “Dương Văn Nam” đỏ đậm
        styles = MultiMsgStyle([
            MessageStyle(
                offset=msg_text.find("Dương Văn Nam"),
                length=len("Dương Văn Nam"),
                style="bold_color",
                color="#db342e",
                auto_format=False
            )
        ])

        # 💬 Gửi tin nhắn kết quả
        client.replyMessage(
            Message(text=msg_text, style=styles),
            message_object, thread_id, thread_type, ttl=15000
        )

    except Exception as e:
        client.replyMessage(
            Message(text=f"❌ Lỗi: {str(e)}"),
            message_object, thread_id, thread_type, ttl=8000
        )

def PTA():
    return {
        'boitinhduyen': handle_boitinhduyen_command
    }