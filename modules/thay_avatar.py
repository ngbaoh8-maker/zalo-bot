from zlapi.models import Message, MultiMsgStyle, MessageStyle
import os
import json
import requests
from config import ADMIN

des = {
    'version': "1.0.2",
    'credits': "ngbao",
    'description': "Thay đổi avt của bot.",
    'power': "Admin"
}

def handle_change_avatar_command(message, message_object, thread_id, thread_type, author_id, client):
    # check quyền admin
    if str(author_id) not in ADMIN:
        send_styled_message(author_id, "• Tuổi cặc đòi đổi avt tao‼️.", message_object, thread_id, thread_type, client)
        return

    # Nếu người dùng chỉ gõ lệnh .avt mà không reply
    if not getattr(message_object, 'quote', None):
        guide_text = (
            "Hướng dẫn sử dụng lệnh Avatar:\n\n"
            "➜ avt set\n"
            "» Công dụng: Reply vào một tin nhắn có ảnh để đặt làm avatar cho bot."
        )
        send_styled_message(author_id, guide_text, message_object, thread_id, thread_type, client)
        return

    try:
        attach = getattr(message_object.quote, 'attach', None)
        if not attach:
            send_styled_message(author_id, "• Cái này không phải ảnh.", message_object, thread_id, thread_type, client)
            return
            
        try:
            attach_data = json.loads(attach)
        except json.JSONDecodeError:
            send_styled_message(author_id, "• Lỗi khi phân tích dữ liệu đính kèm.", message_object, thread_id, thread_type, client)
            return

        media_url = attach_data.get('hdUrl') or attach_data.get('href')
        if not media_url:
            send_styled_message(author_id, "• Không tìm thấy liên kết ảnh trong file đính kèm.", message_object, thread_id, thread_type, client)
            return

        image_path = "modules/cache/group_avatar.jpeg"
        download_image(media_url, image_path)
        if os.path.exists(image_path):
            client.changeAccountAvatar(image_path)
            send_styled_message(author_id, "✅ Thành công đổi avatar cho bot.", message_object, thread_id, thread_type, client)
            os.remove(image_path)
        else:
            send_styled_message(author_id, "❌ Lỗi khi tải ảnh về.", message_object, thread_id, thread_type, client)
    except Exception as e:
        print(f"Lỗi khi xử lý lệnh đổi avatar: {str(e)}")
        send_styled_message(author_id, "⚠️ Đã xảy ra lỗi khi đổi avatar.", message_object, thread_id, thread_type, client)

def download_image(url, save_path):
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
        else:
            print(f"Lỗi khi tải ảnh: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Lỗi khi tải ảnh: {str(e)}")

# Hàm gửi tin nhắn có chữ đỏ tên người gọi lệnh
def send_styled_message(author_id, text, message_object, thread_id, thread_type, client):
    try:
        user_info = client.fetchUserInfo(author_id)
        user_name = user_info.changed_profiles.get(str(author_id), {}).get("zaloName", "Người dùng")

        msg = f"{user_name}\n➜ {text}"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(user_name), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(user_name), style="bold", auto_format=False)
        ])
        message_to_send = Message(text=msg, style=styles)
        client.replyMessage(message_to_send, message_object, thread_id, thread_type, ttl=10000)
    except Exception as e:
        print(f"Lỗi khi gửi styled message: {str(e)}")

def PTA():
    return {
        'thayavt': handle_change_avatar_command
    }