import time
from zlapi.models import *
import requests
import urllib.parse
import os
from config import PREFIX

des = {
    'version': "1.0.2",
    'credits': "ngbao",
    'description': "Tìm ảnh Pin",
    'power': "Thành Viên"
}

def handle_pin_command(message, message_object, thread_id, thread_type, author_id, client):
    text = message.split()

    if len(text) < 3 or not text[1].strip():
        error_message = Message(text=f"Thưa Sếp, vui lòng nhập nội dung cần tìm ảnh và số lượng ảnh (ví dụ: {PREFIX}pin dog 5). ✅")
        client.replyMessage(error_message, message_object, thread_id, thread_type, ttl=30000)
        client.sendReaction(message_object, "🚫", thread_id, thread_type, reactionType=75)
        return

    try:
        num_images = int(text[-1])
        if num_images <= 0 or num_images > 15:
            error_message = Message(text="Số lượng ảnh phải từ 1 đến 15. 🚫")
            client.replyMessage(error_message, message_object, thread_id, thread_type, ttl=30000)
            client.sendReaction(message_object, "🚫", thread_id, thread_type, reactionType=75)
            return
    except ValueError:
        error_message = Message(text="Số lượng ảnh phải là một số hợp lệ (ví dụ: 5). 🚫")
        client.replyMessage(error_message, message_object, thread_id, thread_type, ttl=30000)
        client.sendReaction(message_object, "🚫", thread_id, thread_type, reactionType=75)
        return

    search_terms = " ".join(text[1:-1])
    if not search_terms.strip():
        error_message = Message(text="Vui lòng nhập nội dung cần tìm ảnh. 🚫")
        client.replyMessage(error_message, message_object, thread_id, thread_type, ttl=30000)
        client.sendReaction(message_object, "🚫", thread_id, thread_type, reactionType=75)
        return

    encoded_text = urllib.parse.quote(search_terms, safe='')

    try:
        api_url = f'https://api.sumiproject.net/pinterest?search={encoded_text}'

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }
        
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        
        if not data.get('data'):
            error_message = Message(text="Không tìm thấy ảnh nào. 🚫")
            client.sendMessage(error_message, thread_id, thread_type, ttl=30000)
            client.sendReaction(message_object, "🚫", thread_id, thread_type, reactionType=75)
            return

        unique_links = []
        seen = set()
        for url in data['data']:
            if url and url not in seen:
                unique_links.append(url)
                seen.add(url)
            if len(unique_links) >= num_images:
                break

        if not unique_links:
            error_message = Message(text="Không tìm thấy ảnh nào. 🚫")
            client.sendMessage(error_message, thread_id, thread_type, ttl=30000)
            client.sendReaction(message_object, "🚫", thread_id, thread_type, reactionType=75)
            return

        image_paths = []
        for idx, link in enumerate(unique_links):
            if link:
                image_response = requests.get(link, headers=headers, timeout=15)
                image_response.raise_for_status()
                image_path = f'modules/cache/temp_image_{idx}_{int(time.time())}.jpeg'
                with open(image_path, 'wb') as f:
                    f.write(image_response.content)
                image_paths.append(image_path)

        if all(os.path.exists(path) for path in image_paths):
            total_images = len(image_paths)
            gui = Message(text=f"Đã gửi {total_images} ảnh tìm kiếm từ Pinterest. ✅")
            client.sendMultiLocalImage(
                imagePathList=image_paths,
                message=gui,
                thread_id=thread_id,
                thread_type=thread_type,
                width=1600,
                height=1600,
                ttl=200000
            )
            client.sendReaction(message_object, "✅", thread_id, thread_type, reactionType=75)
            for path in image_paths:
                os.remove(path)

    except requests.exceptions.Timeout:
        error_message = Message(text="❌ Yêu cầu hết thời gian chờ (timeout). Vui lòng thử lại sau. 🚫")
        client.sendMessage(error_message, thread_id, thread_type, ttl=30000)
        client.sendReaction(message_object, "🚫", thread_id, thread_type, reactionType=75)
    except requests.exceptions.RequestException as e:
        error_message = Message(text=f"❌ Đã xảy ra lỗi khi gọi API: {str(e)}")
        client.sendMessage(error_message, thread_id, thread_type, ttl=30000)
        client.sendReaction(message_object, "🚫", thread_id, thread_type, reactionType=75)
    except KeyError as e:
        error_message = Message(text=f"❌ Dữ liệu từ API không đúng cấu trúc: {str(e)}")
        client.sendMessage(error_message, thread_id, thread_type, ttl=30000)
        client.sendReaction(message_object, "🚫", thread_id, thread_type, reactionType=75)
    except Exception as e:
        error_message = Message(text=f"❌ Đã xảy ra lỗi không xác định: {str(e)}")
        client.sendMessage(error_message, thread_id, thread_type, ttl=30000)
        client.sendReaction(message_object, "🚫", thread_id, thread_type, reactionType=75)

def PTA():
    return {
        'pin': handle_pin_command
    }