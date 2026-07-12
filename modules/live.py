import random
from zlapi.models import Message, MultiMsgStyle, MessageStyle
from config import PREFIX

des = {
    'version': "1.0.6",
    'credits': "ngbao",
    'description': "Gửi video đá banh ngẫu nhiên (giống autosend)",
    'power': "Thành Viên"
}

# 🎥 Danh sách video highlight / bóng đá ngẫu nhiên (nguồn hợp pháp từ Pixabay)
FOOTBALL_VIDEOS = [
    "https://cdn.pixabay.com/video/2021/08/15/85379-594902559_large.mp4",
    "https://cdn.pixabay.com/video/2022/05/18/117982-715016806_large.mp4",
    "https://cdn.pixabay.com/video/2021/05/05/73916-550010089_large.mp4",
    "https://cdn.pixabay.com/video/2022/06/10/121227-726357771_large.mp4",
    "https://cdn.pixabay.com/video/2023/03/07/154839-808676227_large.mp4"
]

def handle_live_command(message, message_object, thread_id, thread_type, author_id, client):
    # 🔁 Chọn ngẫu nhiên 1 video
    video_url = random.choice(FOOTBALL_VIDEOS)

    # 🧾 Nội dung caption
    msg_title = "⚽ Live đá banh hôm nay 🎥"
    msg_body = "Gửi video highlight ngẫu nhiên cho vui 😎"

    # 💅 Style giống autosend
    styles = MultiMsgStyle([
        MessageStyle(offset=0, length=len(msg_title), style="bold", auto_format=False),
        MessageStyle(offset=0, length=len(msg_title), style="color", color="#1e90ff", auto_format=False)
    ])

    # 📨 Gửi video kiểu autosend
    client.sendMessage(
        Message(
            text=f"{msg_title}\n➜ {msg_body}",
            attachments=[video_url],   # ✅ y hệt autosend gửi video
            style=styles
        ),
        thread_id, thread_type
    )

def PTA():
    return {
        'live': handle_live_command
    }
