# -*- coding: utf-8 -*-
import os
import json
import datetime
from PIL import Image, ImageDraw
from zlapi.models import Message
from modules.menu import get_font, autosave

des = {
    'version': "2.4.0",
    'credits': "ngbao",
    'description': "Nhận diện file (.py, .txt, ... trong cả modules/)",
    'power': "Thành viên"
}

HISTORY_FILE = "file_status_history.json"

# ===== Load / Save JSON =====
def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {}
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_history(history):
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

# ===== Đổi sang giờ Việt Nam =====
def vn_time(ts):
    return (datetime.datetime.fromtimestamp(ts) + datetime.timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")

def draw_file_info_image(user_id, info_text):
    WIDTH, HEIGHT = 1000, 1000
    bg = Image.new("RGBA", (WIDTH, HEIGHT), (240, 240, 240, 255))
    draw = ImageDraw.Draw(bg)
    
    font_title = get_font(60)
    font_text = get_font(40)
    
    title = "THÔNG TIN FILE"
    bbox_title = draw.textbbox((0, 0), title, font=font_title)
    draw.text(((WIDTH - (bbox_title[2] - bbox_title[0])) / 2, 50),
              title, font=font_title, fill=(0, 0, 0, 255))
    
    current_h = 150
    for line in info_text.split('\n'):
        bbox = draw.textbbox((0, 0), line, font=font_text)
        draw.text(((WIDTH - (bbox[2] - bbox[0])) / 2, current_h),
                  line, font=font_text, fill=(0, 102, 255, 255))
        current_h += bbox[3] - bbox[1] + 15
    
    return autosave(bg)

def find_file_path(path: str):
    if os.path.exists(path):
        return path
    if not os.path.splitext(path)[1]:
        path += ".py"
    alt = os.path.join("modules", path)
    return alt if os.path.exists(alt) else None

def handle_fileinfo(message, message_object, thread_id, thread_type, author_id, client):
    try:
        file_path = None
        if message_object.quote and message_object.quote.attach:
            try:
                data = json.loads(message_object.quote.attach)
                file_path = data.get("hdUrl") or data.get("href")
            except:
                file_path = None
        
        if not file_path:
            args = message.split(maxsplit=1)
            if len(args) < 2:
                client.sendMessage(Message("⚠️ Vui lòng gửi file hoặc nhập đường dẫn: .fileinfo <file>"),
                                   thread_id, thread_type, ttl=180000)
                return
            file_path = args[1].strip()

        file_path = find_file_path(file_path)
        if not file_path or not os.path.exists(file_path):
            client.sendMessage(Message(f"⚠️ Không tìm thấy file '{file_path}' (kể cả trong modules/)"),
                               thread_id, thread_type, ttl=180000)
            return

        # Thông tin file
        info = {
            "file_path": file_path,
            "size_bytes": os.path.getsize(file_path),
            "extension": os.path.splitext(file_path)[1].lower(),
            "created": vn_time(os.path.getmtime(file_path)),  # dùng mtime thay cho ctime
            "modified": vn_time(os.path.getmtime(file_path))
        }

        text_ext = [".py", ".txt", ".json", ".md"]
        if info["extension"] in text_ext:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                info["lines"] = content.count("\n") + 1
                info["characters"] = len(content)
                info["type"] = "text"
            except Exception as e:
                info.update({"lines": None, "characters": None, "type": f"text / unreadable ({e})"})
        else:
            info.update({"lines": None, "characters": None, "type": "binary / unreadable"})

        # Lưu lịch sử
        history = load_history()
        uid = str(author_id)
        timestamp = (datetime.datetime.utcnow() + datetime.timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
        history.setdefault(uid, []).append({"checked_at": timestamp, "file_info": info})
        save_history(history)

        # Tạo text kết quả
        info_text = "\n".join([
            f"📁 File: {info['file_path']}",
            f"📂 Loại: {info['type']}",
            f"📄 Kích thước: {info['size_bytes']} bytes",
            f"📝 Số dòng: {info['lines']}" if info["lines"] else "📝 Số dòng: không đọc được",
            f"🔤 Số ký tự: {info['characters']}" if info["characters"] else "🔤 Số ký tự: không đọc được",
            f"🕒 Ngày tạo: {info['created']}",
            f"🕒 Ngày sửa: {info['modified']}",
            f"💾 Đã lưu lịch sử check ✅"
        ])

        # Gửi cả text + ảnh, TTL = 3 phút
        client.sendMessage(Message(info_text), thread_id, thread_type, ttl=180000)
        img_path = draw_file_info_image(author_id, info_text)
        client.sendLocalImage(img_path, thread_id=thread_id, thread_type=thread_type, ttl=180000)
        os.remove(img_path)

    except Exception as e:
        client.sendMessage(Message(f"⚠️ Lỗi: {e}"), thread_id, thread_type, ttl=180000)

def handle_fileinfo_history(message, message_object, thread_id, thread_type, author_id, client):
    try:
        history = load_history()
        user_history = history.get(str(author_id), [])
        if not user_history:
            client.sendMessage(Message("📂 Lịch sử trống"), thread_id, thread_type, ttl=180000)
            return
        lines = ["📜 Lịch sử check file:"]
        for i, item in enumerate(user_history, 1):
            lines.append(f"{i}. {item['checked_at']} - {item['file_info']['file_path']}")
        client.sendMessage(Message("\n".join(lines)), thread_id, thread_type, ttl=180000)
    except Exception as e:
        client.sendMessage(Message(f"⚠️ Lỗi: {e}"), thread_id, thread_type, ttl=180000)

def PTA():
    return {
        "file": handle_fileinfo,
        "fileinfo_history": handle_fileinfo_history
    }