from zlapi.models import Message, MultiMsgStyle, MessageStyle
import requests
import os
import threading
import time

des = {
    'version': "1.0.4",
    'credits': "ngbao",
    'description': "Gửi ảnh hentai ngẫu nhiên",
    'power': "Thành Viên"
}

TEMP_DIR = "modules/cache/hentai_temp"
os.makedirs(TEMP_DIR, exist_ok=True)


# ====== HÀM TAG ĐỎ ĐẬM ======
def styled_reply(client, author_id, reply_text, message_object, thread_id, thread_type):
    """Gửi tin nhắn có tên người gọi lệnh màu đỏ đậm"""
    try:
        user_info = client.fetchUserInfo(author_id)
        user_name = user_info.changed_profiles.get(str(author_id), {}).get("zaloName", "Người dùng")

        msg = f"{user_name}\n➜ {reply_text}"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(user_name), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(user_name), style="bold", auto_format=False)
        ])
        client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type)
    except Exception as e:
        print(f"[HENTAI] Lỗi khi styled reply: {e}")


# ====== HÀM THU HỒI ======
def unsend_after_delay(client, message_id, delay=300):
    """Tự động thu hồi tin nhắn sau thời gian delay (giây)"""
    def _unsend():
        time.sleep(delay)
        try:
            client.unsendMessage(message_id)
        except Exception as e:
            print(f"[HENTAI] Lỗi khi thu hồi tin nhắn: {e}")
    threading.Thread(target=_unsend, daemon=True).start()


# ====== LỆNH CHÍNH ======
def handle_hentai(message, message_object, thread_id, thread_type, author_id, client):
    """Lệnh gửi ảnh hentai ngẫu nhiên"""
    try:
        api_url = "https://api-dowig.onrender.com/images/hentai"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()

        image_url = data.get("url") or data.get("data")
        if not image_url:
            styled_reply(client, author_id, "Không lấy được ảnh từ API 😥", message_object, thread_id, thread_type)
            return

        # Tải ảnh về tạm
        temp_path = os.path.join(TEMP_DIR, f"hentai_{author_id}.jpg")
        img_data = requests.get(image_url, headers=headers).content
        with open(temp_path, "wb") as f:
            f.write(img_data)

        # Gửi ảnh
        sent_msg = client.sendLocalImage(
            temp_path,
            thread_id=thread_id,
            thread_type=thread_type,
            width=1200,
            height=1600
        )

        # Xóa file sau khi gửi
        os.remove(temp_path)

        # Trả lời thông báo
        styled_reply(client, author_id, "Hoàng Anh Tuấn, ảnh về rồi, giữ kín nha 👀\n", message_object, thread_id, thread_type)

        # Thu hồi ảnh sau 5 phút (300 giây)
        if sent_msg and hasattr(sent_msg, "message_id"):
            unsend_after_delay(client, sent_msg.message_id, delay=300)

    except requests.exceptions.RequestException as e:
        styled_reply(client, author_id, f"Lỗi khi gọi API: {e}", message_object, thread_id, thread_type)
    except Exception as e:
        styled_reply(client, author_id, f"Lỗi không xác định: {e}", message_object, thread_id, thread_type)


# ====== ĐĂNG KÝ LỆNH ======
def PTA():
    return {
        "hentai": handle_hentai
    }