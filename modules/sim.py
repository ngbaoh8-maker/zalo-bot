from zlapi.models import Message, ThreadType, Mention
import time, random
from datetime import datetime
import logging

des = {
    'version': "1.1.6",
    'credits': "ngbao",
    'description': "Trả Lời tự động khi có ai nhắn tin",
    'power': "Quản trị viên Bot"
}

def handle_sim_command(message, message_object, thread_id, thread_type, author_id, client):
    text = message.strip().lower().split()

    # Nếu chỉ gõ "sim" hoặc gọi tên bot
    if len(text) < 2:
        replies = [
            "Em đây 💬", "Nghe nè 😎", "Ai gọi tui đó 🐸",
            "Có chuyện gì thế?", "Ờ?", "Nói lẹ coi 😆",
            "Bot đây, nói đi 🫡", "Ơ kìa, gọi chi đó~",
            "Gọi gì lắm zậy 😏"
        ]
        reply_text = random.choice(replies)
        client.replyMessage(
            Message(text=reply_text),
            message_object,
            thread_id,
            thread_type,
            ttl=10000
        )
        return

# === TỰ ĐỘNG TRẢ LỜI MỌI TIN NHẮN ===
def handle_auto_reply(message_object, thread_id, thread_type, author_id, message_text, client):
    try:
        # Bỏ qua nếu bot tự nhắn cho chính nó
        if str(author_id) == str(client.user_id):
            return

        # Một số câu trả lời ngẫu nhiên
        auto_replies = [
            "Ừ, tui nghe nè 😄",
            "Có gì hông á?",
            "Đang bận mà nhắn hoài 😤",
            "Ờ ok 😅",
            "Tui đây 🐧",
            "Cần gì đó?",
            "Sao đó 🧐",
            "Gì dị?",
            "Tui đang nghe nè 🎧"
        ]

        reply_text = random.choice(auto_replies)
        client.sendMessage(
            Message(text=reply_text),
            thread_id,
            thread_type
        )

    except Exception as e:
        logging.error(f"[AutoReply] Lỗi: {e}")

def PTA():
    return {
        'bot': handle_sim_command,
        'auto_reply': handle_auto_reply
    }
