import requests
import subprocess
import json
import urllib.parse
import os
from io import BytesIO
from PIL import Image, ImageDraw
from zlapi.models import Message, MultiMsgStyle, MessageStyle
from zlapi._threads import ThreadType
import time
import random
import math

des = {
    'version': "2.0.0",
    'credits': "Nguyễn Hải Nam",
    'description': "Tạo sticker từ ảnh, GIF, video.",
    'power': "Thành viên"
}

def check_ffmpeg_webp_support():
    try:
        result = subprocess.run(["ffmpeg", "-codecs"], capture_output=True, text=True, check=True)
        return "libwebp_anim" in result.stdout or "libwebp" in result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def get_file_type(url):
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        content_type = response.headers.get("Content-Type", "").lower()
        if "gif" in content_type or url.lower().endswith(".gif"):
            return "video"
        elif "image" in content_type:
            return "image"
        elif "video" in content_type:
            return "video"
        return "unknown"
    except requests.RequestException:
        if url.lower().endswith((".mp4", ".gif", ".webm", ".avi", ".mov")):
            return "video"
        elif url.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".jxl")):
            return "image"
        return "unknown"

def upload_to_catbox(file_path):
    try:
        with open(file_path, "rb") as f:
            files = {'fileToUpload': ('sticker.webp', f, 'image/webp')}
            response = requests.post("https://catbox.moe/user/api.php", files=files, data={"reqtype": "fileupload"})
        return response.text.strip() if response.status_code == 200 else None
    except Exception as e:
        print(f"Lỗi khi upload lên Catbox: {e}")
        return None

def apply_sparkles(img, frame_idx, num_frames=8):
    canvas = img.copy()
    draw = ImageDraw.Draw(canvas)
    width, height = img.size
    
    # 3 stars at bottom right
    s1_cx, s1_cy = width - 50, height - 50
    s1_max_R, s1_max_r = 35, 10
    
    s2_cx, s2_cy = width - 15, height - 90
    s2_max_R, s2_max_r = 18, 5
    
    s3_cx, s3_cy = width - 95, height - 15
    s3_max_R, s3_max_r = 15, 4

    t = frame_idx / num_frames * 2 * math.pi
    
    scale1 = 0.6 + 0.4 * math.sin(t)
    scale2 = 0.6 + 0.4 * math.sin(t + 2)
    scale3 = 0.6 + 0.4 * math.sin(t + 4)
    
    def draw_star(cx, cy, R, r, scale):
        R_s = R * scale
        r_s = r * scale
        if R_s < 1: return
        points = [
            (cx, cy - R_s), (cx + r_s, cy - r_s),
            (cx + R_s, cy), (cx + r_s, cy + r_s),
            (cx, cy + R_s), (cx - r_s, cy + r_s),
            (cx - R_s, cy), (cx - r_s, cy - r_s)
        ]
        draw.polygon(points, fill=(230, 200, 255, 255))
        
        R_in = R_s * 0.5
        r_in = r_s * 0.5
        points_in = [
            (cx, cy - R_in), (cx + r_in, cy - r_in),
            (cx + R_in, cy), (cx + r_in, cy + r_in),
            (cx, cy + R_in), (cx - r_in, cy + r_in),
            (cx - R_in, cy), (cx - r_in, cy - r_in)
        ]
        draw.polygon(points_in, fill=(255, 255, 255, 255))

    draw_star(s1_cx, s1_cy, s1_max_R, s1_max_r, scale1)
    draw_star(s2_cx, s2_cy, s2_max_R, s2_max_r, scale2)
    draw_star(s3_cx, s3_cy, s3_max_R, s3_max_r, scale3)
    
    return canvas

def convert_media_and_upload(media_url, file_type, unique_id, client, options=None):
    if options is None: options = {}
    script_dir = os.path.dirname(__file__)
    temp_dir = os.path.join(script_dir, 'cache', 'temp')
    
    os.makedirs(temp_dir, exist_ok=True)

    temp_input = os.path.join(temp_dir, f"pro_input_{unique_id}")
    temp_webp = os.path.join(temp_dir, f"tranquan_{unique_id}.webp")
    
    files_to_cleanup = [temp_input, temp_webp]

    try:
        response = requests.get(media_url, stream=True, timeout=15)
        response.raise_for_status()
        
        with open(temp_input, "wb") as f:
            for chunk in response.iter_content(8192):
                if chunk:
                    f.write(chunk)

        if file_type == "image":
            with Image.open(temp_input).convert("RGBA") as img:
                img.thumbnail((512, 512), Image.Resampling.LANCZOS)
                
                width, height = img.size
                try:
                    mask = Image.new("L", (width, height), 0)
                    draw = ImageDraw.Draw(mask)
                    draw.rounded_rectangle((0, 0, width, height), radius=50, fill=255)
                    img.putalpha(mask)
                except AttributeError:
                    pass
                
                if options.get('sparkle'):
                    frames = []
                    for i in range(8):
                        frames.append(apply_sparkles(img, i, 8))
                    frames[0].save(
                        temp_webp, format="WEBP", save_all=True, append_images=frames[1:],
                        loop=0, duration=100, lossless=False, quality=80
                    )
                else:
                    img.save(temp_webp, format="WEBP", quality=80, lossless=False)
        else: # video
            ffmpeg_cmd = ["ffmpeg", "-y", "-i", temp_input]
            
            if options.get('sparkle'):
                sparkle_webp = os.path.join(temp_dir, f"sparkle_{unique_id}.webp")
                files_to_cleanup.append(sparkle_webp)
                sparkle_frames = []
                base_transparent = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
                for i in range(8):
                    sparkle_frames.append(apply_sparkles(base_transparent, i, 8))
                sparkle_frames[0].save(
                    sparkle_webp, format="WEBP", save_all=True, append_images=sparkle_frames[1:], loop=0, duration=100
                )
                
                filter_chain = "[0:v]scale=512:512[base];[base][1:v]overlay=0:0"
                ffmpeg_cmd.extend(["-i", sparkle_webp, "-filter_complex", filter_chain])
                
            ffmpeg_cmd.extend([
                "-c:v", "libwebp",
                "-loop", "0",
                "-r", "15",
                "-an",
                "-lossless", "0",
                "-q:v", "80",
                "-loglevel", "error",
                temp_webp
            ])
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)

        url = upload_to_catbox(temp_webp)
        if not url:
            raise Exception("Upload lên Catbox thất bại, không nhận được link.")
        return url

    except subprocess.CalledProcessError as e:
        err_out = e.stderr if e.stderr else "Lỗi không xác định"
        print(f"Lỗi FFmpeg: {err_out}")
        raise Exception(f"Lỗi FFmpeg: {err_out}")
    except Exception as e:
        print(f"Lỗi khi chuyển đổi media: {e}")
        raise e
    finally:
        for f in files_to_cleanup:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass

def handle_stk_command(message, message_object, thread_id, thread_type, author_id, client):
    if not message_object.quote or not message_object.quote.attach:
        client.replyMessage(
            Message(text="➜ Vui lòng reply vào ảnh, GIF hoặc video để tạo sticker."),
            message_object, thread_id, thread_type, ttl=60000
        )
        return

    try:
        attach_data = json.loads(message_object.quote.attach)
    except (json.JSONDecodeError, TypeError):
        client.replyMessage(Message(text="➜ Dữ liệu đính kèm không hợp lệ."), message_object, thread_id, thread_type, ttl=60000)
        return

    media_url = attach_data.get('hdUrl') or attach_data.get('href') or attach_data.get('url') or attach_data.get('link')
    if not media_url:
        client.replyMessage(Message(text="➜ Không tìm thấy URL của media."), message_object, thread_id, thread_type, ttl=60000)
        return
    media_url = urllib.parse.unquote(media_url.replace("\\/", "/"))

    if "jxl" in media_url:
        media_url = media_url.replace("jxl", "jpg")

    file_type = get_file_type(media_url)
    if file_type not in ["image", "video"]:
        client.replyMessage(Message(text="➜ Loại file không được hỗ trợ (chỉ nhận ảnh, GIF, video)."), message_object, thread_id, thread_type, ttl=60000)
        return

    options = {}
    message_lower = message.lower().strip() if message else ""
    if 'ai' in message_lower or 'sao' in message_lower or 'nhấp nháy' in message_lower:
        options['sparkle'] = True

    processing_text = "➜ ⏳ Đang xử lý, vui lòng chờ..."
    if options.get('sparkle'):
        processing_text = "➜ ⏳ Đang xử lý ✨(có sao lấp lánh)..."

    client.replyMessage(Message(text=processing_text), message_object, thread_id, thread_type, ttl=120000)

    try:
        unique_id = f"{thread_id}_{int(time.time())}_{random.randint(1000, 9999)}"
        webp_url = convert_media_and_upload(media_url, file_type, unique_id, client, options)
        
        if not webp_url:
            raise Exception("Không thể tạo hoặc tải lên sticker.")

        client.sendCustomSticker(
            animationImgUrl=webp_url,
            staticImgUrl=webp_url,
            thread_id=thread_id,
            thread_type=thread_type,
            width=512,
            height=512
        )
        
    except Exception as e:
        client.replyMessage(
            Message(text=f"➜ Lỗi khi tạo sticker: {e}"),
            message_object, thread_id, thread_type, ttl=30000
        )

def PTA():
    return {
        'stk': handle_stk_command
    }