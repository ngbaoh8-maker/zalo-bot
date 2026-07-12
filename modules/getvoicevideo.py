import json
import re
import os
import tempfile
import logging
import requests
from zlapi.models import *
from pydub import AudioSegment

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

des = {
    'version': "1.0.0",
    'credits': "ngbao",
    'description': "Chuyển đổi video thành tin nhắn thoại",
    'power': "Thành viên"
}

def get_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Upgrade-Insecure-Requests": "1"
    }

def save_file_to_cache(url, filename):
    try:
        response = requests.get(url, headers=get_headers(), timeout=3)
        response.raise_for_status()
        cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
        os.makedirs(cache_dir, exist_ok=True)
        file_path = os.path.join(cache_dir, filename)
        with open(file_path, 'wb') as file:
            file.write(response.content)
        return file_path
    except Exception as e:
        logging.error(f"[save_file_to_cache] Error saving file: {e}")
        return None

def convert_to_aac(input_path, aac_path):
    try:
        audio = AudioSegment.from_file(input_path)
        audio.export(aac_path, format="adts")
        return aac_path
    except Exception as e:
        logging.error(f"[convert_to_aac] Error converting to AAC: {e}")
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

def delete_file(file_path):
    try:
        os.remove(file_path)
    except:
        pass

def handle_getvoice_command(message, message_object, thread_id, thread_type, author_id, self):
    video_url = None
    if message_object.quote:
        attach = message_object.quote.attach
        if attach:
            try:
                attach_data = json.loads(attach)
                video_url = attach_data.get('hdUrl') or attach_data.get('href')
            except json.JSONDecodeError as e:
                logging.error(f"[handle_getvoice_command] Error parsing JSON: {e}")
                send_error_message(thread_id, thread_type, self, "Lỗi khi phân tích dữ liệu video.", message_object)
                return
        else:
            send_error_message(thread_id, thread_type, self, "Vui lòng reply tin nhắn chứa video.", message_object)
            return
    else:
        video_url = extract_video_url(message)
        if not video_url:
            send_error_message(thread_id, thread_type, self, "Vui lòng gửi link video hợp lệ.", message_object)
            return

    if video_url:
        send_voice_from_video(video_url, thread_id, thread_type, self, message_object)
    else:
        send_error_message(thread_id, thread_type, self, "Không tìm thấy URL video.", message_object)

def extract_video_url(message):
    video_url_pattern = r"https?://[^\s]+(?:youtube\.com|vimeo\.com|dailymotion\.com|facebook\.com|tiktok\.com|vkontakte\.ru|vimeo\.com|twitch\.tv|soundcloud\.com|...)"
    match = re.search(video_url_pattern, message)
    if match:
        return match.group(0)
    return None

def send_voice_from_video(video_url, thread_id, thread_type, self, message_object):
    try:
        temp_filename = f"video_{int(os.times().elapsed * 1000)}.mp4"
        video_path = save_file_to_cache(video_url, temp_filename)
        if not video_path:
            send_error_message(thread_id, thread_type, self, "Lỗi khi tải video.", message_object)
            return

        aac_filename = f"hat_{int(os.times().elapsed * 1000)}.aac"
        aac_path = os.path.join(os.path.dirname(__file__), 'cache', aac_filename)
        aac_path = convert_to_aac(video_path, aac_path)
        delete_file(video_path)
        if not aac_path:
            send_error_message(thread_id, thread_type, self, "Lỗi khi chuyển đổi sang định dạng âm thanh.", message_object)
            return

        try:
            file_size = os.path.getsize(aac_path)
        except Exception as e:
            logging.error(f"[send_voice_from_video] Error getting file size: {e}")
            send_error_message(thread_id, thread_type, self, "Lỗi khi lấy kích thước file âm thanh.", message_object)
            delete_file(aac_path)
            return
            
        uploaded_url = upload_to_uguu(aac_path)
        delete_file(aac_path)
        if not uploaded_url:
            send_error_message(thread_id, thread_type, self, "Lỗi khi tải file âm thanh lên.", message_object)
            return

        self.sendRemoteVoice(uploaded_url, thread_id, thread_type, fileSize=file_size)
    except Exception as e:
        logging.error(f"[send_voice_from_video] Error: {e}")
        send_error_message(thread_id, thread_type, self, "Không thể gửi voice từ video này.", message_object)

def send_error_message(thread_id, thread_type, self, error_message="Lỗi không xác định.", message_object=None):
    if hasattr(self, 'send'):
        if message_object:
            self.send(Message(text=error_message), thread_id=thread_id, thread_type=thread_type, reply_to=message_object)
        else:
            self.send(Message(text=error_message), thread_id=thread_id, thread_type=thread_type)
    else:
        logging.error("Client không hỗ trợ gửi tin nhắn.")

def hat():
    return {
        'getvoice': handle_getvoice_command
    }