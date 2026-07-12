import requests
import threading
import random
import os
import time
from zlapi.models import Message

# Cấu hình đường dẫn cache
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_PATH = os.path.join(ROOT_DIR, "modules/cache")

if not os.path.exists(CACHE_PATH):
    os.makedirs(CACHE_PATH)

des = {
    'version': "1.0.0",
    'credits': "ngbao",
    'description': "Tự động tìm kiếm ảnh chế (Meme) ngẫu nhiên",
    'power': "Thành Viên"
}

def handle_meme_command(message, message_object, thread_id, thread_type, author_id, client):
    def process():
        file_path = None
        try:
            client.sendReaction(message_object, "😆", thread_id, thread_type)

            # 1. Gọi API lấy danh sách meme phổ biến
            url = "https://api.imgflip.com/get_memes"
            response = requests.get(url, timeout=10)
            data = response.json()

            if not data.get("success"):
                client.replyMessage(Message(text="❌ Không thể kết nối kho Meme."), message_object, thread_id, thread_type)
                return

            memes = data['data']['memes']
            
            # 2. Lọc meme theo từ khóa nếu người dùng có nhập (VD: .meme cat)
            parts = message.split(" ", 1)
            if len(parts) > 1:
                query = parts[1].lower()
                filtered_memes = [m for m in memes if query in m['name'].lower()]
                if filtered_memes:
                    chosen_meme = random.choice(filtered_memes)
                else:
                    # Nếu không tìm thấy theo từ khóa, lấy đại 1 cái và báo lại
                    chosen_meme = random.choice(memes)
                    client.replyMessage(Message(text=f"😅 Không tìm thấy meme '{query}', tặng bạn cái này thay thế!"), message_object, thread_id, thread_type)
            else:
                # Nếu chỉ gõ .meme thì lấy ngẫu nhiên hoàn toàn
                chosen_meme = random.choice(memes)

            meme_url = chosen_meme['url']
            meme_name = chosen_meme['name']

            # 3. Tải và gửi ảnh
            file_name = f"meme_{author_id}_{int(time.time())}.jpg"
            file_path = os.path.join(CACHE_PATH, file_name)
            
            r = requests.get(meme_url)
            with open(file_path, 'wb') as f:
                f.write(r.content)

            client.sendLocalImage(
                file_path,
                thread_id,
                thread_type,
                message=Message(text=f"🤣 Meme: {meme_name}")
            )

        except Exception as e:
            print(f"Lỗi Meme: {e}")
            client.replyMessage(Message(text="⚠️ Lỗi khi tìm meme, thử lại sau nhé!"), message_object, thread_id, thread_type)
        finally:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)

    threading.Thread(target=process, daemon=True).start()

def PTA():
    return {'meme': handle_meme_command, 'che': handle_meme_command}