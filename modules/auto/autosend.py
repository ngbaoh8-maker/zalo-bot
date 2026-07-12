import time
import random
import requests
from zlapi.models import Message, ThreadType
from datetime import datetime, timedelta
import pytz
import ffmpeg
import json
import os
import urllib.parse
from logging_utils import Logging

logger = Logging()
time_messages = {
    "05:05": ["Thức dậy để đón ngày mới tuyệt vời nào! ✨", "video chill"],
    "06:05": ["Chào ngày mới, bạn đã sẵn sàng chưa? 💪", "video chill"],
    "07:05": ["Bắt đầu ngày mới với một bữa sáng ngon lành nhé! 🍳", "vitamin girl"],
    "09:05": ["Làm gì đó cho vui lên bạn ơi! 🎉", "vitamin girl"],
    "11:05": ["Đến giờ nạp năng lượng rồi, ăn trưa thôi! 🍔", "vitamin girl"],
    "13:05": ["Nghỉ ngơi chút rồi tiếp tục nha! ☕", "video chill"],
    "15:05": ["Chiều đến rồi, làm gì đó thú vị nào! 🌇", "vitamin girl"],
    "17:05": ["Kết thúc một ngày rồi, thư giãn thôi! 🛀", "music"],
    "18:05": ["Ăn tối vui vẻ cùng người thân nhé! 👨‍👩‍👧‍👦", "music"],
    "20:18": ["Thời gian cho riêng mình, tận hưởng đi! 🧘", "music"],
    "21:05": ["Chuẩn bị cho giấc ngủ ngon nhé bạn! 🛌", "music"],
    "22:05": ["Ngủ ngon nha, mai có nhiều điều mới! 🌃", "music"],
    "23:05": ["Ngủ sớm để khỏe bạn nhé! 😴", "video chill"],
}
vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
API_URL = "https://bj-tiktok-search.ma-coder-x.workers.dev/?query={}"
video_captions = {
    "video chill": "Chill một chút!!! 😌",
    "vitamin girl": "Cung cấp vitamin gái cho anh em đây!!! 😍",
    "music": "Thưởng thức âm nhạc rất hot trên TikTok!!! 🎶"
}
USED_VIDEOS_FILE = "modules/cache/used_videos.json"

def load_used_videos():
    try:
        with open(USED_VIDEOS_FILE, "r") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_used_video(video_url):
    used_videos = load_used_videos()
    used_videos.add(video_url)
    os.makedirs(os.path.dirname(USED_VIDEOS_FILE), exist_ok=True)
    with open(USED_VIDEOS_FILE, "w") as f:
        json.dump(list(used_videos), f)

def get_video_info(video_url, max_retries=3):
    for attempt in range(max_retries):
        try:
            probe = ffmpeg.probe(video_url)
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            if not video_stream:
                raise ValueError("Không tìm thấy luồng video trong URL")
            duration = float(video_stream['duration']) * 1000
            width = int(video_stream['width'])
            height = int(video_stream['height'])
            return duration, width, height
        except Exception as e:
            logger.error(f"Lỗi lấy thông tin video (lần thử {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                logger.error(f"Không thể lấy thông tin video: {str(e)}")
                return None, None, None

def load_allowed_groups():
    try:
        with open("modules/cache/sendtask_autosend.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("Không tìm thấy sendtask_autosend.json. Tạo file rỗng.")
        return {"groups": []}
    except json.JSONDecodeError:
        logger.error("Lỗi giải mã sendtask_autosend.json.")
        return {"groups": []}

def fetch_tiktok_videos(keywords, max_retries=3):
    encoded_keywords = urllib.parse.quote(keywords)
    used_videos = load_used_videos()
    for attempt in range(max_retries):
        try:
            url = API_URL.format(encoded_keywords)
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("status") and data.get("data"):
                videos = [v for v in data["data"] if v.get("no_watermark") and v["no_watermark"] not in used_videos]
                if not videos:
                    logger.warning(f"Không còn video mới cho từ khóa: {keywords}")
                    return []
                return videos
            else:
                logger.warning(f"Không tìm thấy video cho từ khóa: {keywords}")
                return []
        except Exception as e:
            logger.error(f"Lỗi lấy video TikTok (lần thử {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                logger.error(f"Không thể lấy video TikTok sau nhiều lần thử: {str(e)}")
                return []

def start_auto(client):
    try:
        allowed_groups_data = load_allowed_groups()
        allowed_thread_ids = allowed_groups_data.get("groups", [])
        if not allowed_thread_ids:
            logger.error("Không có nhóm nào được cấu hình.")
            return
        last_sent_time = None
        while True:
            now = datetime.now(vn_tz)
            current_time_str = now.strftime("%H:%M")
            if current_time_str in time_messages and (last_sent_time is None or now - last_sent_time >= timedelta(minutes=1)):
                message_data = time_messages[current_time_str]
                message = message_data[0]
                keyword = message_data[1]
                videos = fetch_tiktok_videos(keyword)
                if not videos:
                    logger.warning(f"Không tìm thấy video mới cho từ khóa: {keyword}. Thử lại sau 30 giây.")
                    time.sleep(30)
                    continue
                video_item = random.choice(videos)
                play_url = video_item.get("no_watermark")
                cover_url = video_item.get("cover")
                duration = video_item.get("music", {}).get("duration", 15000)
                video_width = 1080
                video_height = 1920
                if not play_url:
                    logger.warning(f"Không có URL khả dụng cho video.")
                    time.sleep(30)
                    continue
                duration, width, height = get_video_info(play_url)
                if duration is None:
                    logger.warning(f"Không lấy được thông tin video {play_url}, sử dụng giá trị mặc định.")
                    width, height = video_width, video_height
                    duration = 15000
                info_text = f"{current_time_str} | {message}\n\n{video_captions.get(keyword, 'Video TikTok')}"
                for thread_id in allowed_thread_ids:
                    try:
                        client.sendRemoteVideo(
                            videoUrl=play_url,
                            thumbnailUrl=cover_url,
                            duration=duration,
                            message=Message(text=info_text),
                            thread_id=thread_id,
                            thread_type=ThreadType.GROUP,
                            width=width,
                            height=height,
                            ttl=1800000
                        )
                        logger.info(f"Đã gửi video đến nhóm {thread_id}")
                        save_used_video(play_url)
                        time.sleep(0.3)
                    except Exception as e:
                        logger.error(f"Lỗi gửi video đến nhóm {thread_id}: {e}")
                last_sent_time = now
                logger.info(f"Đã gửi video lúc {current_time_str} cho từ khóa: {keyword}")
            time_to_next_minute = 60 - now.second - (now.microsecond / 1000000)
            time.sleep(time_to_next_minute)
    except Exception as e:
        logger.error(f"Lỗi nghiêm trọng trong start_auto: {e}")
        raise e