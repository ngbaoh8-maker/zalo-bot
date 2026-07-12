import os
import uuid
import mimetypes
import requests
from urllib.parse import urlparse
from threading import Thread, Lock
from zlapi.models import Message
from zlapi import ThreadType
import time

try:
    from flask import Flask, send_from_directory
    app = Flask(__name__)
    
    @app.route('/<filename>')
    def serve_file(filename):
        return send_from_directory(SHARED_FOLDER, filename)
except ImportError:
    app = None
    print("[SHARE] Flask không được cài đặt, file server sẽ không hoạt động")

des = {
    'version': "6.2.0",
    'credits': "ngbao",
    'description': "Share file VIP bộc phá - cooldown 15s, auto resend, tối ưu 6.2.0",
    'power': "Thành viên"
}

# --- Cấu hình ---
SHARED_FOLDER = os.path.abspath("modules/shared_files")
FILE_SERVER_PORT = 5000
FILE_SERVER_HOST = "0.0.0.0"
FILE_SERVER_URL = f"http://127.0.0.1:{FILE_SERVER_PORT}"
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB
COOLDOWN_SECONDS = 15  # cooldown 15s/user

if not os.path.exists(SHARED_FOLDER):
    os.makedirs(SHARED_FOLDER)

# Lock & queue
sending_lock = Lock()
sending_users = set()
upload_times = [3]
last_request_time = {}  # lưu thời gian request gần nhất của mỗi user


def run_file_server():
    if app:
        app.run(host=FILE_SERVER_HOST, port=FILE_SERVER_PORT, debug=False, use_reloader=False)
    else:
        print("[SHARE] File server không thể khởi động vì Flask chưa được cài đặt")

if app:
    Thread(target=run_file_server, daemon=True).start()

# --- Lấy tên user ---
def get_username_by_id(client, uid):
    try:
        user_info = client.getUserInfo(uid)
        return getattr(user_info, "name", str(uid))
    except:
        return str(uid)

# --- Download file từ URL ---
def download_file_from_url(url: str, save_name: str = None) -> str:
    r = requests.get(url, stream=True, timeout=60)
    r.raise_for_status()

    if save_name:
        filename = save_name
    else:
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)
        if not filename or "." not in filename:
            ext = mimetypes.guess_extension(r.headers.get("content-type", "").split(";")[0].strip()) or ".dat"
            filename = f"share_{uuid.uuid4().hex[:8]}{ext}"

    base, ext = os.path.splitext(filename)
    final_path = os.path.join(SHARED_FOLDER, filename)
    if os.path.exists(final_path):
        filename = f"{base}_{uuid.uuid4().hex[:6]}{ext}"

    file_path = os.path.join(SHARED_FOLDER, filename)

    with open(file_path, "wb") as f:
        total_size = 0
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                total_size += len(chunk)
                if total_size > MAX_FILE_SIZE:
                    f.close()
                    os.remove(file_path)
                    raise Exception("File quá lớn (>200MB)")
                f.write(chunk)

    return filename

# --- Lưu file từ reply ---
def save_reply_file(message_object) -> str:
    if not message_object or not getattr(message_object, "attachments", None):
        raise Exception("Tin nhắn không có file đính kèm.")
    attachment = message_object.attachments[0]
    url = attachment.url
    filename = getattr(attachment, "filename", None) or os.path.basename(urlparse(url).path)
    if not filename or "." not in filename:
        ext = mimetypes.guess_extension(getattr(attachment, "content_type", None)) or ".dat"
        filename = f"share_{uuid.uuid4().hex[:8]}{ext}"

    base, ext = os.path.splitext(filename)
    final_path = os.path.join(SHARED_FOLDER, filename)
    if os.path.exists(final_path):
        filename = f"{base}_{uuid.uuid4().hex[:6]}{ext}"
    file_path = os.path.join(SHARED_FOLDER, filename)

    r = requests.get(url, stream=True, timeout=60)
    r.raise_for_status()
    with open(file_path, "wb") as f:
        total_size = 0
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                total_size += len(chunk)
                if total_size > MAX_FILE_SIZE:
                    f.close()
                    os.remove(file_path)
                    raise Exception("File quá lớn (>200MB)")
                f.write(chunk)
    return filename

# --- Gửi file VIP bộc phá ---
def send_file_vip(client, author_id, filename):
    file_url = f"{FILE_SERVER_URL}/{filename.replace(' ', '%20')}"
    with sending_lock:
        if author_id in sending_users:
            client.sendMessage(Message(text="⚠️ File đang được gửi, vui lòng chờ."), author_id, ThreadType.USER)
            return
        sending_users.add(author_id)

    sent_success = False
    attempt = 0
    start_time = time.time()

    def warn_after(delay, msg, action=None):
        nonlocal sent_success
        time.sleep(delay)
        with sending_lock:
            if author_id in sending_users and not sent_success:
                try:
                    client.sendMessage(Message(text=msg), author_id, ThreadType.USER)
                    if action: action()
                except: pass

    # 5s cảnh báo chậm
    Thread(target=warn_after, args=(5, "⚠️ Tiến trình gửi file có thể đang chậm, vui lòng kiên nhẫn chờ..."), daemon=True).start()

    # 10s dự phòng
    def fallback_action():
        nonlocal sent_success
        try:
            client.sendMessage(Message(text=f"📄 (Dự phòng) File của bạn: {filename}"), author_id, ThreadType.USER)
            client.sendRemoteFile(file_url, author_id, ThreadType.USER, fileName=filename)
            sent_success = True
        except: pass
    Thread(target=warn_after, args=(10, "⚠️ Hệ thống có thể bị trục trặc, thử phương thức dự phòng...", fallback_action), daemon=True).start()

    # 15s báo lỗi cuối
    Thread(target=warn_after, args=(15, "❌ Hệ thống bị lỗi, vui lòng thử lại sau"), daemon=True).start()

    try:
        while attempt < 3 and not sent_success:
            try:
                client.sendMessage(Message(text=f"📄 Đây là file bạn chọn: {filename}"), author_id, ThreadType.USER)
                client.sendRemoteFile(file_url, author_id, ThreadType.USER, fileName=filename)
                sent_success = True
            except:
                attempt += 1
                if attempt < 3:
                    time.sleep(5)
                    try:
                        client.sendMessage(Message(text=f"♻️ Gửi file chưa thành công, thử lại lần {attempt + 1}..."), author_id, ThreadType.USER)
                    except: pass
                else:
                    try:
                        client.sendMessage(Message(text="❌ Gửi thất bại sau nhiều lần thử."), author_id, ThreadType.USER)
                    except: pass
    finally:
        with sending_lock:
            sending_users.discard(author_id)

    end_time = time.time()
    upload_times.append(end_time - start_time)

# --- Lệnh .share fix VIP ---
def share_fix_system(client, thread_id, thread_type):
    client.sendMessage(Message(text="⏳ Bắt đầu kiểm tra hệ thống share, vui lòng chờ ít nhất 5 giây..."), thread_id, thread_type)
    time.sleep(5)

    report = "📊 Kết quả toàn diện hệ thống share:\n\n"
    files = os.listdir(SHARED_FOLDER)
    total_size = sum([os.path.getsize(os.path.join(SHARED_FOLDER,f)) for f in files])
    total_size_mb = total_size / (1024*1024)

    report += f"1️⃣ Người dùng đang upload/tải file: {len(sending_users)}\n"
    if sending_users:
        report += f"   Danh sách user: {', '.join([str(u) for u in sending_users])}\n"
    report += f"2️⃣ Tổng số file hiện có: {len(files)}\n"

    file_types = {}
    for f in files:
        ext = os.path.splitext(f)[1].lower() or "khác"
        file_types[ext] = file_types.get(ext, 0) + 1
    report += "3️⃣ Phân loại file:\n"
    for ext,count in file_types.items():
        report += f"   - {ext}: {count} file\n"

    report += f"4️⃣ Tổng dung lượng: {total_size_mb:.2f} MB\n"
    if upload_times:
        avg_time = sum(upload_times)/len(upload_times)
        report += f"5️⃣ Tốc độ trung bình: {avg_time:.2f}s/file\n"
    else:
        report += "5️⃣ Chưa có dữ liệu tốc độ gửi file\n"

    # Top 5 file lớn nhất
    if files:
        biggest = sorted(files, key=lambda f: os.path.getsize(os.path.join(SHARED_FOLDER, f)), reverse=True)[:5]
        report += "6️⃣ Top 5 file lớn nhất:\n"
        for f in biggest:
            size_mb = os.path.getsize(os.path.join(SHARED_FOLDER, f)) / (1024*1024)
            report += f"   - {f} ({size_mb:.2f} MB)\n"

    evaluation = "✅ Hệ thống ổn định"
    if len(sending_users) > 5:
        evaluation = "⚠️ Nhiều người dùng upload, có thể chậm"
    if total_size_mb > 500:
        evaluation += " | ⚠️ Dung lượng lớn, có thể gây chậm"
    report += f"7️⃣ Đánh giá tổng thể: {evaluation}\n"

    client.sendMessage(Message(text=report), thread_id, thread_type)

# --- Lệnh .share VIP ---
def handle_share_command(message, message_object, thread_id, thread_type, author_id, client):
    args = message.split()[1:] if len(message.split()) > 1 else []
    user_name = get_username_by_id(client, author_id)
    files = os.listdir(SHARED_FOLDER)

    if not args:
        if not files:
            client.sendMessage(Message(text="⚠️ Hiện chưa có file nào được chia sẻ."), thread_id, thread_type)
            return
        reply = "📂 Danh sách file:\n"
        for i, file in enumerate(files, start=1):
            reply += f"{i}. {file}\n"
        reply += "\n👉 Lấy file: .share <tên file | số thứ tự>"
        client.sendMessage(Message(text=reply), thread_id, thread_type)
        return

    if args[0].lower() == "fix":
        share_fix_system(client, thread_id, thread_type)
        return

    # Upload
    if args[0].lower() == "upload":
        try:
            if len(args) >= 3:
                url = args[1]
                custom_name = args[2]
                filename = download_file_from_url(url, save_name=custom_name)
            elif len(args) == 2:
                url = args[1]
                filename = download_file_from_url(url)
            else:
                filename = save_reply_file(message_object)
            client.sendMessage(Message(text=f"✅ Đã lưu file {filename} vào danh sách share."), thread_id, thread_type)
        except Exception as e:
            client.sendMessage(Message(text=f"❌ Lỗi khi lưu file: {str(e)}"), thread_id, thread_type)
            return
    else:
        query = " ".join(args).strip()
        filename = None
        if query.isdigit():
            index = int(query)-1
            if 0<=index<len(files):
                filename = files[index]
        else:
            for f in files:
                if f.lower() == query.lower():
                    filename = f
                    break
        if not filename:
            client.sendMessage(Message(text="❌ Không tìm thấy file bạn yêu cầu."), thread_id, thread_type)
            return

        # --- Check cooldown ---
        now = time.time()
        last_time = last_request_time.get(author_id, 0)
        if now - last_time < COOLDOWN_SECONDS:
            remaining = int(COOLDOWN_SECONDS - (now - last_time))
            client.sendMessage(Message(text=f"⚠️ Bạn vừa yêu cầu file, vui lòng thử lại sau {remaining} giây."), thread_id, thread_type)
            return
        last_request_time[author_id] = now

        client.sendMessage(Message(text=f"📦 bạn đã chọn file {filename}, bot sẽ gửi file riêng cho bạn."), thread_id, thread_type)
        send_file_vip(client, author_id, filename)

def PTA():
    return {
        'share': handle_share_command
    }
