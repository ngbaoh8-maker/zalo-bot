from zlapi.models import Message
import random
import json
import ffmpeg
import os

des = {
    'version': "1.0.5",
    'credits': "ngbao",
    'description': "Gửi video gái",
    'power': "Thành Viên"
}

VIDEO_FILE = "modules/cache/data/vdgirl.json"
DURATION_DEFAULT = 240000  # 4 phút = 240000 ms

def get_video_info(video_url):
    try:
        probe = ffmpeg.probe(video_url)
        video_stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
        if not video_stream:
            raise ValueError("Không tìm thấy luồng video trong URL")

        duration = float(video_stream.get('duration', 240)) * 1000  # ms
        width = int(video_stream.get('width', 720))
        height = int(video_stream.get('height', 1280))
        return duration, width, height
    except Exception:
        # fallback nếu lỗi: giữ 4 phút, size mặc định
        return DURATION_DEFAULT, 720, 1280

def handle_vdgirl_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        if not os.path.exists(VIDEO_FILE):
            return  # Không có file danh sách video

        with open(VIDEO_FILE, "r") as f:
            video_urls = json.load(f)

        if not video_urls:
            return  # Danh sách trống

        video_url = random.choice(video_urls)
        image_url = "https://"  # ảnh thumbnail tạm
        duration, width, height = get_video_info(video_url)

        # Chỉ gửi video, không text, tự thu hồi sau 4 phút
        client.sendRemoteVideo(
            video_url,
            image_url,
            int(duration),
            message=None,
            thread_id=thread_id,
            thread_type=thread_type,
            width=width,
            height=height,
            ttl=DURATION_DEFAULT
        )

    except Exception:
        pass  # Không gửi bất kỳ thông báo lỗi nào

def PTA():
    return {
        'vdgirl': handle_vdgirl_command
    }