from zlapi.models import Message
import requests
import os
from PIL import Image
from io import BytesIO

des = {
    'version': "1.0.9",
    'credits': "ngbao",
    'description': "Chơi câu đố vui",
    'power': "Thành viên"
}

def handle_doff_command(message, message_object, thread_id, thread_type, author_id, client):
    # Loại bỏ việc gọi hàm get_user_name_by_id
    user_name = "Unknown User"  # Hoặc có thể là một tên tĩnh, hoặc bỏ qua hẳn nếu không cần thiết

    parts = message.strip().split()

    if len(parts) < 2:
        client.sendMessage(
            Message(text=f"Dịch Vụ Xem Đồ Free Fire, Hân Hạnh Phục Vụ Bạn\n📌 **Cách dùng:**\ndoff <uid>\n\nVí dụ: doff 12345678`\n\n[Yêu Cầu Bởi: {user_name}]"),
            thread_id, thread_type
        )
        return

    uid = parts[1]
    region = "sg"
    api_key = "AYAxAPI"

    try:
        outfit_url = f"https://aya-outfit-version1.vercel.app/outfit-image?uid={uid}&region={region}&key={api_key}"

        response = requests.get(outfit_url, stream=True)
        if response.status_code != 200:
            client.sendMessage(
                Message(text=f"❌ Không thể lấy ảnh outfit. UID sai hoặc server lỗi.\n\n[Yêu Cầu Bởi: {user_name}]"),
                thread_id, thread_type
            )
            return

        image = Image.open(BytesIO(response.content)).convert("RGB")
        temp_path = f"modules/cache/outfit_{uid}.jpg"
        image.save(temp_path, format='JPEG')

        client.sendLocalImage(
            temp_path,
            thread_id=thread_id,
            thread_type=thread_type,
            width=image.width,
            height=image.height
        )

        if os.path.exists(temp_path):
            os.remove(temp_path)

    except Exception as e:
        client.sendMessage(
            Message(text=f"⚠️ Có lỗi xảy ra khi xử lý: {e}\n\n[Ask by: {user_name}]"),
            thread_id, thread_type
        )


def PTA():
    return {
        'doff': handle_doff_command,
    }