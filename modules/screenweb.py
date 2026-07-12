import requests
import os
import time
import urllib.parse
import threading
from zlapi.models import Message
from config import PREFIX

des = {
    'version': "1.2.0",
    'credits': "ngbao",
    'description': "Chụp ảnh màn hình website (Tối ưu hóa tốc độ và xử lý ảnh chờ)",
    'power': "Thành viên"
}

# Thư mục tạm để lưu ảnh
CACHE_DIR = "modules/cache/screenweb"
os.makedirs(CACHE_DIR, exist_ok=True)

def handle_web_command(message, message_object, thread_id, thread_type, author_id, client):
    content = message.strip().split()
    
    if len(content) < 2:
        return client.replyMessage(
            Message(text=f"⚠️ Vui lòng nhập link website!\nVí dụ: {PREFIX}web google.com"),
            message_object, thread_id, thread_type
        )

    url = content[1].strip()
    if not url.startswith("http"):
        url = "https://" + url
        
    def process_screenshot():
        try:
            client.sendReaction(message_object, "📸", thread_id, thread_type)
            
            encoded_url = urllib.parse.quote(url)
            # Thêm tham số v= để tránh cache ảnh cũ/ảnh lỗi
            api_url = f"https://s0.wp.com/mshots/v1/{encoded_url}?w=1280&h=720&v={int(time.time())}"
            
            img_path = os.path.join(CACHE_DIR, f"web_{thread_id}.png")
            
            # Cơ chế Retry: mShots cần thời gian để render nếu trang web chưa được lưu
            max_retries = 3
            success = False
            
            for i in range(max_retries):
                response = requests.get(api_url, timeout=20)
                # Nếu mShots trả về status 200 và nội dung không phải là ảnh chờ của WordPress
                if response.status_code == 200 and len(response.content) > 5000:
                    with open(img_path, 'wb') as f:
                        f.write(response.content)
                    success = True
                    break
                else:
                    # Đợi 2 giây để API render trang web
                    time.sleep(2)

            if success:
                client.sendLocalImage(
                    img_path,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    message=Message(text=f"🌐 Snapshot: {url}"),
                    width=1280,
                    height=720
                )
                client.sendReaction(message_object, "✅", thread_id, thread_type)
            else:
                client.replyMessage(
                    Message(text="❌ Không thể chụp ảnh trang web này. Có thể trang web chặn bot hoặc tải quá lâu."),
                    message_object, thread_id, thread_type
                )
            
            if os.path.exists(img_path):
                os.remove(img_path)

        except Exception as e:
            client.replyMessage(Message(text=f"❌ Lỗi: {str(e)}"), message_object, thread_id, thread_type)

    # Chạy trong luồng riêng để tránh làm bot bị đứng khi chờ API phản hồi
    threading.Thread(target=process_screenshot, daemon=True).start()

def PTA():
    return {'web': handle_web_command}