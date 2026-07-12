import subprocess
import time
import psutil
import pytz
import platform
import random
from datetime import datetime
from io import BytesIO
import requests
import os
import warnings
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from zlapi.models import Message, ThreadType

des = {
    'version': "1.1.0",
    'credits': "DucDuydzai cuto",
    'description': "Xem Thông Tin máy chủ",
    'power': "Quản trị viên Bot"
}


warnings.filterwarnings("ignore", category=RuntimeWarning)

WIDTH, HEIGHT = 1024, 800
AVATAR_SIZE = (110, 110)
FONT_PATH = "font/BeVietnamPro-Bold.ttf"
session = requests.Session()

def wrap_text_to_lines(text, font, max_width):
    if not text:
        return [""]
    
    words = text.split(' ')
    lines = []
    current_line = []
    
    if hasattr(font, 'getlength'):
        get_width = lambda t: font.getlength(t)
    else:
        get_width = lambda t: font.getsize(t)[0]

    for word in words:
        test_line = ' '.join(current_line + [word])
        text_width = get_width(test_line)
        
        if text_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            
            current_line = [word]
            if get_width(current_line[0]) > max_width and len(current_line[0]) > 10:
                 pass
            
    if current_line:
        lines.append(' '.join(current_line))
        
    return lines

def get_current_time_vn():
    return datetime.now(pytz.timezone("Asia/Ho_Chi_Minh")).strftime("%d-%m-%Y %H:%M:%S")

def get_cpu_info():
    try:
        logical = psutil.cpu_count(logical=True)
        physical = psutil.cpu_count(logical=False)
        arch = platform.machine()
        brand = "Không rõ"
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "Hardware" in line or "model name" in line:
                        brand = line.split(":")[-1].strip()
                        break
        except:
            brand = platform.processor() or "Không rõ"
            
        return (
            f"🧠 Bộ Vi Xử Lý (CPU)\n"
            f"- Tên: {brand}\n"
            f"- Kiến trúc: {arch}\n"
            f"- Lõi: {physical} (Thực) / {logical} (Logic)"
        )
    except Exception as e:
        return f" CPU - Lỗi: {str(e)}"

def get_ram_info():
    try:
        ram = psutil.virtual_memory()
        ram_used = ram.used / (1024 ** 3)
        ram_total = ram.total / (1024 ** 3)
        
        return (
            f"💾 Bộ Nhớ Chính (RAM)\n"
            f"- Sử Dụng: {ram_used:.2f} GB / {ram_total:.2f} GB\n"
            f"- Tỉ lệ: {ram.percent}%"
        )
    except Exception as e:
        return f" RAM - Lỗi: {str(e)}"

def get_swap_info():
    try:
        swap = psutil.swap_memory()
        swap_used = swap.used / (1024 ** 3)
        swap_total = swap.total / (1024 ** 3)
        
        return (
            f"📃 Bộ Nhớ Đệm (SWAP)\n"
            f"- Sử Dụng: {swap_used:.2f} GB / {swap_total:.2f} GB\n"
            f"- Tỉ lệ: {swap.percent}%"
        )
    except Exception as e:
        return f" SWAP - Lỗi: {str(e)}"

def get_disk_info():
    try:
        disk = psutil.disk_usage('/')
        disk_used = disk.used / (1024 ** 3)
        disk_total = disk.total / (1024 ** 3)
        disk_free = disk.free / (1024 ** 3)
        
        return (
            f"🗄️ Dung Lượng Ổ Đĩa\n"
            f"- Tổng: {disk_total:.2f} GB\n"
            f"- Đã Dùng: {disk_used:.2f} GB (Trống: {disk_free:.2f} GB)"
        )
    except Exception as e:
        return f" Ổ Đĩa - Lỗi: {str(e)}"

def get_os_info():
    try:
        if platform.system() != "Windows" and subprocess.run("uname", shell=True, capture_output=True).returncode == 0:
            os_info = subprocess.run("uname -a", shell=True, capture_output=True, text=True)
            info_text = os_info.stdout.strip()
        else:
            info_text = platform.platform()
            
        return f"💻 Hệ Điều Hành (OS)\n- Thông tin Kernel: {info_text}"
    except Exception as e:
        return f" OS - Lỗi: {str(e)}"

def get_ping_status():
    try:
        ping_cmd = "ping -c 1 8.8.8.8" if platform.system() != "Windows" else "ping -n 1 8.8.8.8"
        result = subprocess.run(ping_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0 and "time=" in result.stdout:
            time_ms = result.stdout.split("time=")[-1].split(" ")[0]
            
            return f"🌐 Độ Trễ Mạng (Ping)\n- Thời gian phản hồi: {time_ms}"
        return "🌐 Độ Trễ Mạng (Ping)\n- Không thể đo lường"
    except Exception as e:
        return f" Ping - Lỗi: {str(e)}"

def get_uptime():
    try:
        result = subprocess.run("uptime -p", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            uptime_text = result.stdout.strip()
        else:
            boot_time = datetime.fromtimestamp(psutil.boot_time(), pytz.timezone("Asia/Ho_Chi_Minh"))
            now = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh"))
            delta = now - boot_time
            seconds = delta.total_seconds()
            
            days = int(seconds // (24 * 3600))
            hours = int((seconds % (24 * 3600)) // 3600)
            minutes = int((seconds % 3600) // 60)
            
            parts = []
            if days > 0: parts.append(f"{days} ngày")
            if hours > 0: parts.append(f"{hours} giờ")
            if minutes > 0: parts.append(f"{minutes} phút")
            
            uptime_text = ", ".join(parts) if parts else "Vài giây"

        return f"⏱️ Thời Gian Hoạt Động (Uptime)\n- Thời gian: {uptime_text}"
    except Exception as e:
        return f" Uptime - Lỗi: {str(e)}"

def get_avatar(url):
    try:
        res = session.get(url, timeout=10)
        avatar = Image.open(BytesIO(res.content)).convert("RGBA").resize(AVATAR_SIZE)
    except:
        avatar = Image.new("RGBA", AVATAR_SIZE, (180, 180, 180, 255))

    mask = Image.new("L", AVATAR_SIZE, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, *AVATAR_SIZE), fill=255)
    avatar.putalpha(mask)

    glow = Image.new("RGBA", (AVATAR_SIZE[0]+30, AVATAR_SIZE[1]+30), (0, 0, 0, 0))
    for i in range(15, 0, -1):
        alpha = int(255 * (i / 15) * 0.4)
        ImageDraw.Draw(glow).ellipse(
            (15 - i, 15 - i, AVATAR_SIZE[0]+i+15, AVATAR_SIZE[1]+i+15),
            fill=(100, 200, 255, alpha)
        )
    glow.paste(avatar, (15, 15), avatar)
    return glow

def create_system_image(name, avatar_url, elapsed, data):
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)

    COLOR_START = (10, 20, 30)
    COLOR_END = (40, 20, 60)
    r1, g1, b1 = COLOR_START
    r2, g2, b2 = COLOR_END
    for i in range(HEIGHT):
        r = int(r1 + (r2 - r1) * i / HEIGHT)
        g = int(g1 + (g2 - g1) * i / HEIGHT)
        b = int(b1 + (b2 - b1) * i / HEIGHT)
        draw.line([(0, i), (WIDTH, i)], fill=(r, g, b, 255))
    
    try:
        font_title = ImageFont.truetype(FONT_PATH, 48)
        font_text_header = ImageFont.truetype(FONT_PATH, 28)
        font_text_body = ImageFont.truetype(FONT_PATH, 24)
        font_small = ImageFont.truetype(FONT_PATH, 22)
    except IOError:
        font_title = ImageFont.load_default()
        font_text_header = ImageFont.load_default()
        font_text_body = ImageFont.load_default()
        font_small = ImageFont.load_default()

    avatar = get_avatar(avatar_url)
    img.paste(avatar, (60, 40), avatar)

    TITLE_Y = 50
    draw.text((210, TITLE_Y), "🛡️ BÁO CÁO HỆ THỐNG 🛡️", font=font_title, fill="#4dd0e1")

    META_X = 210
    draw.text((META_X, TITLE_Y + 70), f"👤 Yêu Cầu Từ: {name}", font=font_small, fill="#cfd8dc")
    draw.text((META_X, TITLE_Y + 100), f"🕒 Cập Nhật Lúc: {get_current_time_vn()}", font=font_small, fill="#cfd8dc")
    draw.text((META_X, TITLE_Y + 130), f"⚙️ Tốc Độ Xử Lý: {elapsed:.2f}s", font=font_small, fill="#ffb74d")

    COL_1_DATA = data[0:3]
    COL_2_DATA = data[3:7]

    COL_1_X = 60
    COL_2_X = 530
    COL_WIDTH = 420
    START_Y = 280

    COLOR_HEADER = "#ffb74d"
    COLOR_BODY = "#ffffff"
    BODY_LINE_HEIGHT = 30

    y1 = START_Y
    for section in COL_1_DATA:
        raw_lines = section.splitlines()
        if not raw_lines: continue
        
        draw.text((COL_1_X, y1), raw_lines[0], font=font_text_header, fill=COLOR_HEADER)
        current_y = y1 + 35
        
        for line_detail in raw_lines[1:]:
            prefix = ""
            content = line_detail
            if ':' in line_detail:
                prefix, content = line_detail.split(':', 1)
            
            wrapped_content_lines = wrap_text_to_lines(content.strip(), font_text_body, COL_WIDTH - 20 - (70 if ':' in line_detail else 0)) 
            
            full_line_text = prefix + (": " if ':' in line_detail else "") + wrapped_content_lines[0]
            draw.text((COL_1_X + 20, current_y), full_line_text, font=font_text_body, fill=COLOR_BODY)
            current_y += BODY_LINE_HEIGHT
            
            for subsequent_line in wrapped_content_lines[1:]:
                draw.text((COL_1_X + 20 + 70, current_y), subsequent_line, font=font_text_body, fill=COLOR_BODY)
                current_y += BODY_LINE_HEIGHT
        
        y1 = current_y + 35 

    y2 = START_Y
    for section in COL_2_DATA:
        raw_lines = section.splitlines()
        if not raw_lines: continue
        
        draw.text((COL_2_X, y2), raw_lines[0], font=font_text_header, fill=COLOR_HEADER)
        current_y = y2 + 35
        
        for line_detail in raw_lines[1:]:
            prefix = ""
            content = line_detail
            if ':' in line_detail:
                prefix, content = line_detail.split(':', 1)
            
            wrapped_content_lines = wrap_text_to_lines(content.strip(), font_text_body, COL_WIDTH - 20 - (70 if ':' in line_detail else 0)) 
            
            full_line_text = prefix + (": " if ':' in line_detail else "") + wrapped_content_lines[0]
            draw.text((COL_2_X + 20, current_y), full_line_text, font=font_text_body, fill=COLOR_BODY)
            current_y += BODY_LINE_HEIGHT
            
            for subsequent_line in wrapped_content_lines[1:]:
                draw.text((COL_2_X + 20 + 70, current_y), subsequent_line, font=font_text_body, fill=COLOR_BODY)
                current_y += BODY_LINE_HEIGHT
        
        y2 = current_y + 35 


    path = f"system_{random.randint(1000,9999)}.png"
    img.convert("RGB").save(path)
    return path

def system_info_command(message, message_object, thread_id, thread_type, author_id, client):
    start = time.time()
    path = None
    try:
        user_info = client.fetchUserInfo(author_id).changed_profiles.get(author_id)
        name = user_info.displayName if user_info else "Người dùng ẩn danh"
        avatar = user_info.avatar if user_info and user_info.avatar else ""

        info = [
            get_cpu_info(),
            get_ram_info(),
            get_swap_info(),
            get_disk_info(),
            get_os_info(),
            get_ping_status(),
            get_uptime()
        ]

        elapsed = time.time() - start
        path = create_system_image(name, avatar, elapsed, info)

        client.sendLocalImage(
            path,
            thread_id=thread_id,
            thread_type=thread_type,
            width=WIDTH,
            height=HEIGHT,
            message=Message(text=""),
            ttl=300000
        )
    except Exception as e:
        err = f" Không lấy được thông tin hệ thống\nLỗi: {e}"
        client.replyMessage(Message(text=err), message_object, thread_id, thread_type)
    finally:
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except:
            pass

def PTA():
    return {
        "system": system_info_command
    }
