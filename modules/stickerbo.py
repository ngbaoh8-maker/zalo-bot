import requests
import subprocess
import json
import urllib.parse
import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageSequence
from zlapi.models import Message
from zlapi._threads import ThreadType
import time
import random
import re

des = {
    'version': "2.4.8",
    'credits': "ngbao",
    'description': "Sticker với nhiều tùy chọn",
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
        if "image" in content_type:
            return "image"
        elif "video" in content_type:
            return "video"
        return "unknown"
    except requests.RequestException:
        return "unknown"

def upload_to_uguu(file_path):
    try:
        with open(file_path, 'rb') as file:
            response = requests.post("https://uguu.se/upload", files={'files[]': file})
            response.raise_for_status()
            return response.json().get('files')[0].get('url')
    except Exception as e:
        print(f"Lỗi khi upload lên uguu: {e}")
        return None

def crop_to_square(img):
    width, height = img.size
    if width == height:
        return img
    min_side = min(width, height)
    left = (width - min_side) // 2
    top = (height - min_side) // 2
    right = left + min_side
    bottom = top + min_side
    return img.crop((left, top, right, bottom))

def apply_circular_mask_and_border(img):
    BORDER_COLOR = (175, 238, 238, 255)
    BORDER_WIDTH = 6
    TARGET_SIZE = img.size[0]
    canvas_size = TARGET_SIZE + BORDER_WIDTH * 2

    canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    offset = BORDER_WIDTH
    img = img.convert("RGBA")

    mask = Image.new("L", (TARGET_SIZE, TARGET_SIZE), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, TARGET_SIZE, TARGET_SIZE), fill=255)
    img.putalpha(mask)

    canvas.paste(img, (offset, offset), img)

    border_draw = ImageDraw.Draw(canvas)
    border_draw.ellipse(
        (0, 0, canvas_size - 1, canvas_size - 1),
        outline=BORDER_COLOR,
        width=BORDER_WIDTH
    )

    return canvas

def apply_rounded_mask_and_border(img, roundness=100):
    BORDER_COLOR = (175, 238, 238, 255)
    BORDER_WIDTH = 6
    TARGET_SIZE = img.size[0]
    canvas_size = TARGET_SIZE + BORDER_WIDTH * 2

    canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    offset = BORDER_WIDTH
    img = img.convert("RGBA")

    radius = int((roundness / 100) * (TARGET_SIZE / 2))
    
    mask = Image.new("L", (TARGET_SIZE, TARGET_SIZE), 0)
    draw = ImageDraw.Draw(mask)
    
    if radius == TARGET_SIZE // 2:
        draw.ellipse((0, 0, TARGET_SIZE, TARGET_SIZE), fill=255)
    else:
        draw.rounded_rectangle((0, 0, TARGET_SIZE, TARGET_SIZE), radius=radius, fill=255)
    
    img.putalpha(mask)
    canvas.paste(img, (offset, offset), img)

    border_draw = ImageDraw.Draw(canvas)
    if radius == TARGET_SIZE // 2:
        border_draw.ellipse(
            (0, 0, canvas_size - 1, canvas_size - 1),
            outline=BORDER_COLOR,
            width=BORDER_WIDTH
        )
    else:
        border_draw.rounded_rectangle(
            (BORDER_WIDTH//2, BORDER_WIDTH//2, canvas_size - BORDER_WIDTH//2 - 1, canvas_size - BORDER_WIDTH//2 - 1),
            radius=radius + BORDER_WIDTH//2,
            outline=BORDER_COLOR,
            width=BORDER_WIDTH
        )

    return canvas

def apply_disc_rotation(img):
    TARGET_SIZE = img.size[0]
    canvas_size = int(TARGET_SIZE * 1.2)
    
    rounded_img = apply_circular_mask_and_border(img)
    
    frames = []
    for angle in range(0, 360, 15):
        frame = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
        
        rotated = rounded_img.rotate(angle, resample=Image.Resampling.BICUBIC, expand=False)
        
        x_offset = (canvas_size - TARGET_SIZE - 12) // 2
        y_offset = x_offset
        
        frame.paste(rotated, (x_offset, y_offset), rotated)
        frames.append(frame)
    
    return frames

def convert_media_and_upload(media_url, file_type, unique_id, options=None):
    if options is None:
        options = {}
    
    script_dir = os.path.dirname(__file__)
    temp_dir = os.path.join(script_dir, 'cache', 'temp')
    os.makedirs(temp_dir, exist_ok=True)

    temp_input = os.path.join(temp_dir, f"pro_input_{unique_id}")
    temp_webp = os.path.join(temp_dir, f"stk_{unique_id}.webp")
    files_to_cleanup = [temp_input, temp_webp]
    TARGET_SIZE = 512

    try:
        print(f"Tải media từ: {media_url}")
        response = requests.get(media_url, stream=True, timeout=20)
        response.raise_for_status()
        with open(temp_input, "wb") as f:
            for chunk in response.iter_content(8192):
                f.write(chunk)
        print("Tải media hoàn tất.")

        if file_type == "image":
            with Image.open(temp_input) as img:
                square_img = crop_to_square(img)
                square_img.thumbnail((TARGET_SIZE, TARGET_SIZE), Image.Resampling.LANCZOS)
                
                if options.get('mode') == 'disc':
                    frames = apply_disc_rotation(square_img)
                    duration = 60
                else:
                    roundness = options.get('roundness', 100)
                    
                    if options.get('mode') == 'rotate':
                        final_img = apply_rounded_mask_and_border(square_img, roundness=roundness)
                        frames = []
                        for angle in range(0, 360, 10):
                            frame = final_img.rotate(angle, resample=Image.Resampling.BICUBIC, expand=False)
                            frames.append(frame)
                        duration = 120
                    else:
                        final_img = apply_rounded_mask_and_border(square_img, roundness=roundness)
                        frames = [final_img]
                        duration = 100
                
                frames[0].save(
                    temp_webp,
                    format="WEBP",
                    save_all=True,
                    append_images=frames[1:],
                    loop=0,
                    duration=duration,
                    lossless=False,
                    quality=85
                )
                print("Tạo WEBP hoàn tất.")
        
        else:
            roundness = options.get('roundness', 100)
            radius = int((roundness / 100) * (TARGET_SIZE / 2))
            
            filter_chain = f"crop='min(iw,ih)':'min(iw,ih)',scale={TARGET_SIZE}:{TARGET_SIZE},format=rgba"
            
            if radius == TARGET_SIZE // 2:
                filter_chain += f",geq=lum='p(X,Y)',alpha='if(lt(sqrt(pow(X-{TARGET_SIZE/2},2)+pow(Y-{TARGET_SIZE/2},2)),{TARGET_SIZE/2}),255,0)'"
            else:
                filter_chain += f",geq=r={radius}:alpha='if(gt(abs(X-{TARGET_SIZE/2}),{TARGET_SIZE/2}-{radius})*gt(abs(Y-{TARGET_SIZE/2}),{TARGET_SIZE/2}-{radius})*lt(sqrt(pow(abs(X-{TARGET_SIZE/2})-({TARGET_SIZE/2}-{radius}),2)+pow(abs(Y-{TARGET_SIZE/2})-({TARGET_SIZE/2}-{radius}),2)),{radius}),255,0)'"
            
            if options.get('mode') == 'disc':
                filter_chain += f",rotate=2*PI*t/6"
            elif options.get('mode') == 'rotate':
                filter_chain += f",rotate=2*PI*t/8"
            
            subprocess.run([
                "ffmpeg", "-y", "-i", temp_input,
                "-vf", filter_chain,
                "-c:v", "libwebp_anim",
                "-loop", "0",
                "-r", "15",
                "-an",
                "-lossless", "0",
                "-q:v", "80",
                "-loglevel", "error",
                temp_webp
            ], check=True, capture_output=True, text=True)
            print("Tạo WEBP video/GIF hoàn tất.")

        webp_url = upload_to_uguu(temp_webp)
        if not webp_url:
            raise Exception("Không thể tải lên sticker WEBP.")
        return webp_url

    except subprocess.CalledProcessError as e:
        print(f"Lỗi FFmpeg: {e.stderr}")
        raise Exception(f"Lỗi FFmpeg: {e.stderr}")
    except Exception as e:
        print(f"Lỗi khi chuyển đổi media: {e}")
        raise e
    finally:
        for f in files_to_cleanup:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except Exception as clean_e:
                print(f"Lỗi khi dọn dẹp file {f}: {clean_e}")

def parse_stk_command(message):
    options = {'mode': 'normal', 'roundness': 100}
    
    message_lower = message.lower().strip()
    
    if 'rotate' in message_lower:
        options['mode'] = 'rotate'
    
    r_match = re.search(r'-r\s+(\d+)', message)
    if r_match:
        roundness = int(r_match.group(1))
        options['roundness'] = max(0, min(100, roundness))
    
    return options

def handle_stk_command(message, message_object, thread_id, thread_type, author_id, client):
    if not check_ffmpeg_webp_support():
        client.replyMessage(
            Message(text="➜ Lỗi: FFmpeg không hỗ trợ codec libwebp/libwebp_anim."),
            message_object, thread_id, thread_type, ttl=60000
        )
        return

    if not message_object.quote or not message_object.quote.attach:
        help_text = """🎭 LỆNH STICKER - Hướng dẫn sử dụng:
Quote ảnh/video + gõ:
   • .stk → Tạo sticker bình thường
   • .stk -r <0-100> → Bo tròn góc (0=vuông, 100=tròn)
   • .stk rotate → Sticker xoay 360° như đĩa nhạc"""
        
        client.replyMessage(
            Message(text=help_text),
            message_object, thread_id, thread_type, ttl=60000
        )
        return

    try:
        attach_data = json.loads(message_object.quote.attach)
    except (json.JSONDecodeError, TypeError):
        client.replyMessage(Message(text="➜ Dữ liệu đính kèm không hợp lệ."), message_object, thread_id, thread_type, ttl=60000)
        return

    media_url = attach_data.get('hdUrl') or attach_data.get('href')
    if not media_url:
        client.replyMessage(Message(text="➜ Không tìm thấy URL của media."), message_object, thread_id, thread_type, ttl=60000)
        return

    media_url = urllib.parse.unquote(media_url.replace("\\/", "/"))
    if "jxl" in media_url:
        media_url = media_url.replace("jxl", "jpg")

    file_type = get_file_type(media_url)
    if file_type not in ["image", "video"]:
        client.replyMessage(Message(text="➜ Loại file không được hỗ trợ."), message_object, thread_id, thread_type, ttl=60000)
        return

    options = parse_stk_command(message)
    
    processing_text = "➜ ⏳ Đang xử lý"
    if options['roundness'] != 100:
        processing_text += f" (bo góc: {options['roundness']}%)"
    if options['mode'] == 'rotate':
        processing_text += " (xoay nội dung)"
    elif options['mode'] == 'disc':
        processing_text += " (xoay 360° đĩa nhạc)"
    processing_text += "..."
    
    processing_msg = Message(text=processing_text)
    client.replyMessage(processing_msg, message_object, thread_id, thread_type, ttl=120000)

    try:
        unique_id = f"{thread_id}_{int(time.time())}_{random.randint(1000,9999)}"
        webp_url = convert_media_and_upload(media_url, file_type, unique_id, options)

        if not webp_url:
            raise Exception("Không thể tạo hoặc tải lên sticker.")

        client.sendCustomSticker(
            animationImgUrl=webp_url,
            staticImgUrl=webp_url,
            thread_id=thread_id,
            thread_type=thread_type,
            width=524,
            height=524
        )
        print(f"Sticker URL: {webp_url}")

    except Exception as e:
        client.replyMessage(
            Message(text=f"➜ Lỗi khi tạo sticker: {e}"),
            message_object, thread_id, thread_type, ttl=30000
        )

def PTA():
    return {
        'stkbo': handle_stk_command
    }