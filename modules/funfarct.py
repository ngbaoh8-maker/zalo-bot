# modules/fact.py
import random
from zlapi.models import Message

des = {
    "version": "1.0",
    "credits": "ngbao",
    "description": "Gửi một sự thật ngẫu nhiên",
    "power": "Thành Viên"
}

def do_fact(message, message_object, thread_id, thread_type, author_id, client):
    """
    Lệnh:
      !fact  hoặc  !funfact
    """
    facts = [
        "🧠 Não người tạo ra hơn 70.000 suy nghĩ mỗi ngày!",
        "☀️ Ánh sáng từ Mặt Trời mất 8 phút 20 giây để đến Trái Đất.",
        "🐶 Chó có thể hiểu được hơn 150 từ của con người.",
        "🐱 Mèo ngủ trung bình 16 tiếng một ngày.",
        "🚀 Trên vũ trụ, phi hành gia cao hơn khi ở Trái Đất 2–5 cm.",
        "🍯 Mật ong là thực phẩm không bao giờ bị hỏng.",
        "🍌 Chuối giúp cải thiện tâm trạng vì chứa serotonin tự nhiên.",
        "🌿 Cây trồng phát triển nhanh hơn nếu nghe nhạc nhẹ.",
        "💧 Uống nước ấm buổi sáng giúp tăng trao đổi chất.",
        "🔥 Cười giúp giảm đau tự nhiên vì kích thích endorphin."
        "😹 Mèo không thể nếm được vị ngọt!",
        "🧃 Nước dừa từng được dùng thay máu truyền trong chiến tranh thế giới!",
        "🍕 Ở Ý, pizza ban đầu dành cho người nghèo thôi đó!",
        "🦈 Cá mập tồn tại trước cả khủng long hàng trăm triệu năm!",
        "😴 Khi bạn mơ, não của bạn hoạt động gần giống lúc đang thức!",
    ]

    fact = random.choice(facts)
    text = f"✨ *Sự thật thú vị hôm nay:*\n\n{fact}"
    client.replyMessage(
        Message(text=text),
        message_object,
        thread_id=thread_id,
        thread_type=thread_type,
        ttl=60000
    )

def PTA():
    return {
        "fact": do_fact,
        "suthat": do_fact
    }