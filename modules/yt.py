import os
import logging
import requests
import re
import json
import time
import tempfile
import threading
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from bs4 import BeautifulSoup
from pydub import AudioSegment
import yt_dlp
from config import PREFIX
from zlapi.models import Message, ThreadType, MultiMsgStyle, MessageStyle

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
EMOJI_FONT_PATH = "modules/cache/font/NotoEmoji-Bold.ttf"
SEARCH_TIMEOUT = 120
PLATFORM = "youtube"

des = {
    'version': "1.0.4",
    'credits': "ngbao",
    'description': "Tải video hoặc nghe nhạc từ YouTube.",
    'power': "Thành Viên"
}

AUDIO_FORMAT = "bestaudio[ext=m4a]/bestaudio"
VIDEO_FORMAT_360 = "bestvideo[height<=360][vcodec^=avc1]+bestaudio/best[height<=360][vcodec^=avc1]"
VIDEO_FORMAT_720 = "bestvideo[height<=720][fps<=60][vcodec^=avc1]+bestaudio/best[height<=720][fps<=60][vcodec^=avc1]"
VIDEO_FORMAT_1080 = "bestvideo[height<=1080][fps<=60][vcodec^=avc1]+bestaudio/best[height<=1080][fps<=60][vcodec^=avc1]"
VIDEO_FORMAT_MAX = "bestvideo[vcodec^=avc1]+bestaudio/best[vcodec^=avc1]"

def get_user_name(client, uid):
    try:
        user_info = client.fetchUserInfo(uid)
        author_info = user_info.changed_profiles.get(str(uid), {}) if user_info and user_info.changed_profiles else {}
        name = author_info.get('zaloName', 'Không xác định')
        return name
    except Exception as e:
        logging.error(f"[get_user_name] Failed to fetch name for user {uid}: {e}")
        return 'Không xác định'

def get_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    }

def get_font(size):
    try: return ImageFont.truetype(FONT_PATH, size)
    except Exception: return ImageFont.load_default()

def get_emoji_font(size):
    try: return ImageFont.truetype(EMOJI_FONT_PATH, size)
    except Exception: return ImageFont.load_default()

def delete_file(file_path):
    if file_path and os.path.exists(file_path):
        try: os.remove(file_path)
        except Exception as e: logging.error(f"Could not delete file {file_path}: {e}")

def autosave(img, quality=97):
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tf:
        img.convert("RGB").save(tf, "JPEG", quality=quality, dpi=(100, 100), optimize=True, progressive=True, subsampling=0)
        return tf.name

def extract_youtube_url(text):
    youtube_regex = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:watch\?v=|shorts\/)|youtu\.be\/)([a-zA-Z0-9_-]+)(?:\S+)?'
    match = re.search(youtube_regex, text)
    return match.group(0) if match else None

def convert_published_time_to_vietnamese(published_time):
    if not published_time: return "Không xác định"
    time_map = { "second ago": "giây trước", "seconds ago": "giây trước", "minute ago": "phút trước", "minutes ago": "phút trước", "hour ago": "giờ trước", "hours ago": "giờ trước", "day ago": "ngày trước", "days ago": "ngày trước", "week ago": "tuần trước", "weeks ago": "tuần trước", "month ago": "tháng trước", "months ago": "tháng trước", "year ago": "năm trước", "years ago": "năm trước" }
    vietnamese_time = published_time
    for eng, viet in time_map.items():
        vietnamese_time = vietnamese_time.replace(eng, viet)
    return vietnamese_time

def convert_duration_to_ms(duration_str):
    parts = list(map(int, duration_str.split(':')))
    ms = 0
    if len(parts) == 3: ms = (parts[0] * 3600 + parts[1] * 60 + parts[2]) * 1000
    elif len(parts) == 2: ms = (parts[0] * 60 + parts[1]) * 1000
    elif len(parts) == 1: ms = parts[0] * 1000
    return ms

def get_video_format(quality_param):
    if quality_param is None: quality_param = "default"
    quality_param = quality_param.lower()
    if quality_param in ["audio", "mp3"]: return {"format": AUDIO_FORMAT, "qualityText": "audio", "ext": "m4a"}
    if quality_param in ["low", "360", "360p"]: return {"format": VIDEO_FORMAT_360, "qualityText": "360p", "ext": "mp4"}
    if quality_param in ["high", "1080", "1080p"]: return {"format": VIDEO_FORMAT_1080, "qualityText": "1080p", "ext": "mp4"}
    if quality_param == "max": return {"format": VIDEO_FORMAT_MAX, "qualityText": "Cao nhất", "ext": "mp4"}
    return {"format": VIDEO_FORMAT_720, "qualityText": "720p", "ext": "mp4"}
    
def search_youtube(query, max_results=10):
    try:
        search_url = f"https://www.youtube.com/results?search_query={requests.utils.quote(query)}"
        response = requests.get(search_url, headers=get_headers(), timeout=10)
        response.raise_for_status()
        match = re.search(r'var ytInitialData = ({.*?});</script>', response.text)
        if not match:
            logging.error("Could not find ytInitialData in YouTube search response.")
            return []
        data = json.loads(match.group(1))
        video_items = data['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']
        videos = []
        for item in video_items:
            if 'videoRenderer' in item:
                video_data = item['videoRenderer']
                if not all(k in video_data for k in ['videoId', 'title']) or 'lengthText' not in video_data: continue
                videos.append({
                    'videoId': video_data.get('videoId'),
                    'title': video_data.get('title', {}).get('runs', [{}])[0].get('text', ''),
                    'thumbnail': video_data.get('thumbnail', {}).get('thumbnails', [{}])[0].get('url', ''),
                    'duration': video_data.get('lengthText', {}).get('simpleText', '0:00'),
                    'viewCount': video_data.get('viewCountText', {}).get('simpleText', '0 views').replace("views", "").strip(),
                    'publishedTime': video_data.get('publishedTimeText', {}).get('simpleText', ''),
                    'channelName': video_data.get('ownerText', {}).get('runs', [{}])[0].get('text', ''),
                    'url': f"https://www.youtube.com/watch?v={video_data.get('videoId')}"
                })
            if len(videos) >= max_results: break
        return videos
    except Exception as e:
        logging.error(f"Error searching YouTube: {e}")
        return []

def get_youtube_video_info(video_url):
    try:
        ydl_opts = {'quiet': True, 'no_warnings': True, 'skip_download': True, 'force_generic_extractor': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return {
                'videoId': info.get('id'), 'title': info.get('title'), 'thumbnail': info.get('thumbnail'),
                'duration': info.get('duration', 0), 'viewCount': str(info.get('view_count', 0)),
                'channelName': info.get('uploader', 'Unknown'), 'publishedTime': info.get('upload_date'),
                'url': info.get('webpage_url')
            }
    except Exception as e:
        logging.error(f"Error getting video info with yt-dlp: {e}")
        return None

def download_youtube_video(video_url, video_id, format_opts):
    try:
        cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
        os.makedirs(cache_dir, exist_ok=True)
        video_path_template = os.path.join(cache_dir, f"yt_{video_id}_{int(time.time())}")
        ydl_opts = {
    'format': format_opts['format'],
    'outtmpl': f'{video_path_template}.%(ext)s',
    'quiet': True,
    'no_warnings': True,
    'merge_output_format': 'mp4' if format_opts['ext'] == 'mp4' else None,
    'ffmpeg_location': r'C:\Users\Administrator\Downloads\ffmpeg-2025-10-30-git-00c23bafb0-full_build (1)\ffmpeg-2025-10-30-git-00c23bafb0-full_build\bin',
    'prefer_ffmpeg': True,
    'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'm4a'}] if format_opts['ext'] == 'm4a' else [],
    'concurrent_fragments': 60,
    'fragment_retries': 5,
    'retries': 10,

        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            downloaded_path = ydl.prepare_filename(info)
            if format_opts['ext'] == 'm4a' and not downloaded_path.endswith('.m4a'):
                final_path_from_info = info.get('filepath')
                if final_path_from_info and os.path.exists(final_path_from_info):
                    return final_path_from_info
                
                possible_paths = [f for f in os.listdir(cache_dir) if f.startswith(f"yt_{video_id}_") and f.endswith('.m4a')]
                if possible_paths:
                    return os.path.join(cache_dir, max(possible_paths, key=lambda p: os.path.getmtime(os.path.join(cache_dir, p))))

                logging.warning(f"Could not find final .m4a path for {video_id}, returning downloaded_path: {downloaded_path}")
            return downloaded_path
    except Exception as e:
        logging.error(f"Error downloading with yt-dlp: {e}")
        return None

def convert_to_aac(m4a_path, aac_path):
    try:
        audio = AudioSegment.from_file(m4a_path, format="m4a")
        audio.export(aac_path, format="adts")
        return aac_path
    except Exception as e:
        logging.error(f"[convert_to_aac] Error converting M4A to AAC: {e}")
        return None

def upload_to_uguu(file_path):
    try:
        with open(file_path, 'rb') as file:
            response = requests.post("https://uguu.se/upload", files={'files[]': file})
            response.raise_for_status()
            return response.json().get('files')[0].get('url')
    except Exception as e:
        logging.error(f"[upload_to_uguu] Error: {e}")
        return None
        
def draw_search_result_image(videos):
    CARD_W, CARD_H = 800, 120; PADDING = 25; CARD_GAP = 15; COLS = 1; ROWS = len(videos)
    WIDTH = CARD_W + 2 * PADDING
    HEIGHT = (CARD_H * ROWS) + (CARD_GAP * (ROWS - 1)) + (2 * PADDING) + 80
    bg_color = (28, 28, 28); card_color = (44, 44, 44); font_title = get_font(24)
    font_small = get_font(18); font_index = get_font(26); text_color = (255, 255, 255); sub_text_color = (170, 170, 170)
    img = Image.new("RGBA", (WIDTH, HEIGHT), bg_color)
    draw = ImageDraw.Draw(img)
    header_font = get_font(32); header_text = "KẾT QUẢ TÌM KIẾM YOUTUBE"
    header_w = header_font.getlength(header_text)
    draw.text(((WIDTH - header_w) / 2, PADDING), header_text, font=header_font, fill=text_color)
    current_y = PADDING + 60
    for idx, video in enumerate(videos):
        cx = PADDING; cy = current_y
        draw.rounded_rectangle([cx, cy, cx + CARD_W, cy + CARD_H], radius=12, fill=card_color)
        if video.get('thumbnail'):
            try:
                thumb_url = video['thumbnail'].split('?')[0]
                cover_data = requests.get(thumb_url, headers=get_headers(), timeout=5).content
                with Image.open(BytesIO(cover_data)).convert("RGBA") as thumb_img:
                    thumb_img = thumb_img.resize((168, 94), Image.LANCZOS)
                    img.paste(thumb_img, (cx + 13, cy + 13), thumb_img)
            except Exception as e:
                logging.warning(f"Failed to load thumbnail for {video['title']}: {e}")
                draw.rectangle([cx + 13, cy + 13, cx + 13 + 168, cy + 13 + 94], fill=(60,60,60))
        text_x = cx + 168 + 26
        title = video['title']
        max_title_width = CARD_W - (text_x - cx) - 20
        if font_title.getlength(title) > max_title_width:
            title_lines = []; words = title.split(); current_line = ""
            for word in words:
                if font_title.getlength(current_line + " " + word) <= max_title_width: current_line += " " + word
                else: title_lines.append(current_line.strip()); current_line = word
            title_lines.append(current_line.strip())
            title = "\n".join(title_lines[:2])
            if len(title_lines) > 2 or (len(title_lines) == 2 and font_title.getlength(title_lines[1]) > max_title_width):
                last_line = title_lines[1]
                while font_title.getlength(last_line + "...") > max_title_width: last_line = last_line[:-1]
                title = title_lines[0] + "\n" + last_line + "..."
        draw.text((text_x, cy + 15), title, font=font_title, fill=text_color)
        channel_text = f"📺 {video['channelName']}"
        draw.text((text_x, cy + 70), channel_text, font=font_small, fill=sub_text_color)
        stats_text = f"👀 {video['viewCount']} • 📅 {convert_published_time_to_vietnamese(video['publishedTime'])}"
        draw.text((text_x, cy + 90), stats_text, font=font_small, fill=sub_text_color)
        duration_bg_x = cx + 13 + 168 - 55; duration_bg_y = cy + 13 + 94 - 24
        draw.rounded_rectangle([duration_bg_x, duration_bg_y, duration_bg_x + 50, duration_bg_y + 20], radius=5, fill=(0,0,0,180))
        duration_w = get_font(16).getlength(video['duration'])
        draw.text((duration_bg_x + (50 - duration_w)/2, duration_bg_y + 2), video['duration'], font=get_font(16), fill=text_color)
        idx_text = str(idx + 1); idx_w = font_index.getlength(idx_text)
        draw.text((cx - PADDING/2 - idx_w/2, cy + CARD_H/2 - font_index.size/2 + 5), idx_text, font=font_index, fill=sub_text_color)
        current_y += CARD_H + CARD_GAP
    footer_font = get_font(18); footer_text = f"➜ Trả lời tin nhắn này với số thứ tự để tải. Ví dụ: 1 hoặc 1 audio. Hết hạn sau {SEARCH_TIMEOUT}s."
    footer_w = footer_font.getlength(footer_text)
    draw.text(((WIDTH - footer_w) / 2, HEIGHT - PADDING - 10), footer_text, font=footer_font, fill=sub_text_color)
    return autosave(img, quality=92)

def handle_yt_command(message_text, message_object, thread_id, thread_type, author_id, client):
    user_states = client.yt_user_states
    name = get_user_name(client, author_id)
    parts = message_text.strip().split(maxsplit=1)
    
    if len(parts) < 2:
        client.replyMessage(Message(text=f"➜ {name}, vui lòng nhập từ khóa tìm kiếm hoặc link.\nVí dụ: {PREFIX}yt Sơn Tùng MTP"), message_object, thread_id, thread_type, ttl=30000)
        return

    query_full = parts[1]
    
    if query_full.strip().split()[0].isdigit() and author_id in user_states:
        state = user_states[author_id]
        if time.time() - state['time_of_search'] > SEARCH_TIMEOUT:
            del user_states[author_id]
            client.replyMessage(Message(text=f"➜ {name}, kết quả đã hết hạn, vui lòng tìm lại."), message_object, thread_id, thread_type, ttl=30000)
            return

        choice_parts = query_full.strip().split(); index_str = choice_parts[0]
        quality = choice_parts[1] if len(choice_parts) > 1 else "default"
        
        if not index_str.isdigit():
             client.replyMessage(Message(text=f"➜ {name}, lựa chọn không hợp lệ. Vui lòng trả lời bằng số."), message_object, thread_id, thread_type, ttl=30000)
             return
        
        index = int(index_str) - 1
        videos = state['videos']
        
        if not (0 <= index < len(videos)):
            client.replyMessage(Message(text=f"➜ {name}, lựa chọn không hợp lệ."), message_object, thread_id, thread_type, ttl=30000)
            return
        
        selected_video = videos[index]
        del user_states[author_id]
        
        threading.Thread(target=send_media_youtube, args=(client, message_object, thread_id, thread_type, selected_video, quality, name)).start()
        return

    url = extract_youtube_url(query_full)
    if url:
        client.replyMessage(Message(text=f"➜ {name}, đang xử lý dữ liệu từ link..."), message_object, thread_id, thread_type, ttl=120000)
        quality_parts = query_full.split()
        quality = quality_parts[-1] if len(quality_parts) > 1 and quality_parts[-1].lower() in ["low", "high", "max", "audio", "mp3", "360p", "720p", "1080p", "360", "720", "1080"] else "default"
        video_info = get_youtube_video_info(url)
        if not video_info:
            client.replyMessage(Message(text=f"➜ {name}, không thể lấy thông tin từ link này."), message_object, thread_id, thread_type, ttl=30000)
            return
        threading.Thread(target=send_media_youtube, args=(client, message_object, thread_id, thread_type, video_info, quality, name)).start()
        return

    client.replyMessage(Message(text=f"➜ {name}, đang tìm kiếm, vui lòng chờ..."), message_object, thread_id, thread_type, ttl=120000)
    videos = search_youtube(query_full)
    if not videos:
        client.replyMessage(Message(text=f"➜ {name}, không tìm thấy kết quả cho '{query_full}'."), message_object, thread_id, thread_type, ttl=30000)
        return

    user_states[author_id] = {'videos': videos, 'time_of_search': time.time()}
    img_path = None
    try:
        img_path = draw_search_result_image(videos)
        with Image.open(img_path) as im: width, height = im.size
        client.sendLocalImage(img_path, thread_id=thread_id, thread_type=thread_type, width=width, height=height, message=Message(text=f"➜ {name}, đây là kết quả cho '{query_full}'.\n➜ Vui lòng trả lời tin nhắn này với số thứ tự để tải. Ví dụ: 1 hoặc 1 audio. Hết hạn sau {SEARCH_TIMEOUT}s."), ttl=SEARCH_TIMEOUT * 1000)
    except Exception as e:
        logging.error(f"Error sending search result image: {e}")
        client.replyMessage(Message(text="Lỗi khi tạo ảnh kết quả."), message_object, thread_id, thread_type, ttl=30000)
    finally:
        delete_file(img_path)

def send_media_youtube(client, message_object, thread_id, thread_type, video_info, quality_param, user_name):
    duration = video_info.get('duration', 0)
    
    if not isinstance(duration, (int, float)): 
        duration = convert_duration_to_ms(duration) / 1000
    
    is_admin_or_bot_admin = client.is_allowed_author(message_object.uidFrom) or client.is_group_admin(thread_id, message_object.uidFrom)

    if not is_admin_or_bot_admin and duration > 60 * 60:
        client.replyMessage(Message(text=f"➜ {user_name}, vì tài nguyên có hạn, không thể tải video dài hơn 60 phút."), message_object, thread_id, thread_type, ttl=30000)
        return

    format_opts = get_video_format(quality_param)
    client.replyMessage(Message(text=f"➜ Đang tải video với {format_opts['qualityText']} cho:\n'{video_info['title']}'\nChờ chút nhé..."), message_object, thread_id, thread_type, ttl=120000)
    
    downloaded_path = None; aac_path = None
    try:
        downloaded_path = download_youtube_video(video_info['url'], video_info['videoId'], format_opts)
        if not downloaded_path or not os.path.exists(downloaded_path): raise Exception("Tải file thất bại.")
        
        if format_opts['qualityText'] == 'audio':
            aac_path = os.path.splitext(downloaded_path)[0] + '.aac'
            if not convert_to_aac(downloaded_path, aac_path): raise Exception("Chuyển đổi audio thất bại.")
            
            file_size = os.path.getsize(aac_path)
            if file_size == 0: raise Exception("File audio sau khi chuyển đổi có kích thước 0 byte.")
            
            upload_url = upload_to_uguu(aac_path)
            if not upload_url: raise Exception("Tải file lên server thất bại.")
            
            client.sendRemoteVoice(upload_url, thread_id, thread_type, fileSize=file_size, ttl=360000)
            client.sendMessage(Message(text=f"🎵 From Youtube 🎵\nTiêu đề: {video_info['title']}\nKênh: {video_info['channelName']}"), thread_id, thread_type, ttl=120000)
        else:
            video_url = upload_to_uguu(downloaded_path)
            if not video_url: raise Exception("Tải video lên server thất bại.")
            
            duration_ms = int(duration * 1000)
            msg_text = (f"▶️ From Youtube\n"
                        f"🎵 Tiêu đề: {video_info['title']}\n"
                        f"📺 Kênh: {video_info['channelName']}\n"
                        f"📊 Chất lượng: {format_opts['qualityText']}")
            client.sendRemoteVideo(videoUrl=video_url, thumbnailUrl=video_info['thumbnail'], duration=duration_ms, thread_id=thread_id, thread_type=thread_type, message=Message(text=msg_text), ttl=3600000)
    except Exception as e:
        logging.error(f"Error in send_media_youtube for '{video_info['title']}': {e}")
        client.replyMessage(Message(text=f"➜ {user_name}, đã xảy ra lỗi khi xử lý: {video_info['title']}."), message_object, thread_id, thread_type, ttl=30000)
    finally:
        delete_file(downloaded_path)
        delete_file(aac_path)

def PTA():
    return { 'yt': handle_yt_command }
