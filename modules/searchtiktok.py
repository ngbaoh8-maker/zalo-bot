from zlapi.models import Message, Mention, ThreadType
import requests
import json
import os
import time
import logging
from io import BytesIO
from PIL import Image
import threading
from config import PREFIX

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

des = {
    'version': "2.1.0",
    'credits': "ngbao",
    'description': "Tìm kiếm video/ảnh từ TikTok theo từ khóa",
    'power': "Thành viên"
}

def handle_stiktok_command(message, message_object, thread_id, thread_type, author_id, client):
    text = message.split(maxsplit=1)
    if len(text) < 2 or not text[1].strip():
        client.sendMessage(
            Message(text=f"Vui lòng nhập từ khóa tìm kiếm! Ví dụ: {PREFIX}stiktok cosplay"),
            thread_id, thread_type, ttl=60000
        )
        return
    
    keywords = text[1].strip()
    api_url = f"https://bj-tiktok-search.ma-coder-x.workers.dev/?query={keywords}"
    
    try:
        client.sendMessage(
            Message(text=f"Đang tìm kiếm video/ảnh TikTok với từ khóa: '{keywords}'..."),
            thread_id, thread_type, ttl=60000
        )
        
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") and data.get("data") and len(data["data"]) > 0:
            process_result(client, thread_id, thread_type, author_id, data["data"][0], keywords)
        else:
            client.sendMessage(
                Message(text=f"Không tìm thấy kết quả cho từ khóa: '{keywords}'"),
                thread_id, thread_type, ttl=12000
            )
    
    except requests.exceptions.Timeout:
        client.sendMessage(
            Message(text="Yêu cầu API hết thời gian! Vui lòng thử lại sau."),
            thread_id, thread_type, ttl=12000
        )
    except requests.exceptions.HTTPError as e:
        client.sendMessage(
            Message(text=f"Lỗi API: {str(e)}"),
            thread_id, thread_type, ttl=12000
        )
    except Exception as e:
        logger.error(f"Lỗi trong handle_stiktok_command: {str(e)}")
        client.sendMessage(
            Message(text=f"Lỗi không xác định: {str(e)}"),
            thread_id, thread_type, ttl=12000
        )

def process_result(client, thread_id, thread_type, author_id, item, keywords):
    try:
        title = item.get("title", "Không có tiêu đề")
        play_url = item.get("no_watermark")
        cover_url = item.get("cover")
        has_video = play_url is not None and play_url != ""
        has_images = False

        views = item.get("views", 0)
        likes = item.get("likes", 0)
        comments = item.get("comments", 0)
        
        info_text = f"🔍 Kết quả tìm kiếm cho '{keywords}'\n\n{title}\n\n"
        info_text += f"👁️ {views:,} | ❤️ {likes:,} | 💬 {comments:,}"
        
        if has_video:
            try:
                client.sendMessage(
                    Message(text="Đang tải video, vui lòng đợi..."),
                    thread_id, thread_type, ttl=30000
                )
                
                duration = item.get("music", {}).get("duration", 15000)
                
                video_width = 1080
                video_height = 1920
                
                if cover_url:
                    try:
                        cover_response = requests.get(cover_url, timeout=5)
                        cover_response.raise_for_status()
                        
                        img = Image.open(BytesIO(cover_response.content))
                        video_width, video_height = img.size
                        logger.info(f"Lấy kích thước từ cover image: {video_width}x{video_height}")
                    except Exception as e:
                        logger.error(f"Không thể lấy kích thước từ cover: {str(e)}")
                
                logger.info(f"Gửi video với kích thước: {video_width}x{video_height}")
                
                client.sendRemoteVideo(
                    videoUrl=play_url,
                    thumbnailUrl=cover_url,
                    duration=duration,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    width=video_width,
                    height=video_height,
                    message=Message(text=info_text),
                    ttl=240000
                )
                
            except Exception as e:
                logger.error(f"Lỗi khi gửi video: {str(e)}")
                client.sendMessage(
                    Message(text="Không thể gửi video. Vui lòng thử lại sau."),
                    thread_id, thread_type, ttl=12000
                )
                
                if cover_url:
                    try:
                        cover_response = requests.get(cover_url, timeout=10)
                        cover_response.raise_for_status()
                        
                        img = Image.open(BytesIO(cover_response.content))
                        
                        os.makedirs("modules/cache", exist_ok=True)
                        
                        temp_path = f"modules/cache/tiktok_cover_{thread_id}_{int(time.time())}.jpg"
                        img.save(temp_path)
                        
                        img_width, img_height = img.size
                        
                        client.sendLocalImage(
                            temp_path,
                            thread_id=thread_id,
                            thread_type=thread_type,
                            width=img_width,
                            height=img_height,
                            message=Message(text=f"{info_text}\n\nKhông thể gửi video, đây là hình ảnh từ video."),
                            ttl=120000
                        )
                        
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                    except Exception as e:
                        logger.error(f"Lỗi khi gửi hình ảnh thay thế: {str(e)}")
        
        else:
            if cover_url:
                try:
                    cover_response = requests.get(cover_url, timeout=10)
                    cover_response.raise_for_status()
                    
                    img = Image.open(BytesIO(cover_response.content))
                    
                    os.makedirs("modules/cache", exist_ok=True)
                    
                    temp_path = f"modules/cache/tiktok_cover_{thread_id}_{int(time.time())}.jpg"
                    img.save(temp_path)
                    
                    img_width, img_height = img.size
                    
                    client.sendLocalImage(
                        temp_path,
                        thread_id=thread_id,
                        thread_type=thread_type,
                        width=img_width,
                        height=img_height,
                        message=Message(text=info_text),
                        ttl=120000
                    )
                    
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                        
                except Exception as e:
                    logger.error(f"Lỗi khi tải ảnh cover: {str(e)}")
                    client.sendMessage(
                        Message(text=info_text),
                        thread_id, thread_type, ttl=12000
                    )
            else:
                client.sendMessage(
                    Message(text=info_text),
                    thread_id, thread_type, ttl=12000
                )
                
    except Exception as e:
        logger.error(f"Lỗi trong process_result: {str(e)}")
        client.sendMessage(
            Message(text=f"Đã xảy ra lỗi khi xử lý kết quả: {str(e)}"),
            thread_id, thread_type, ttl=12000
        )

def PTA():
    return {
        'stiktok': handle_stiktok_command,
        'searchtiktok': handle_stiktok_command
    }