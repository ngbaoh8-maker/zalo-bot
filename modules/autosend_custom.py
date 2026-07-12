import time
import random
import json
import os
import requests
from zlapi.models import Message, ThreadType
from datetime import datetime, timedelta
import pytz
import threading
import re

# Tệp lưu trữ các bộ tin nhắn
MESSAGE_SETS_FILE = "message_sets.json"

des = {
    'version': "1.1.0",
    'credits': "ngbao",
    'description': "Quản lý và gửi sản phẩm Zalo.\n⚙️Các lệnh có sẵn:\n- product create [tên] [giá] (Reply vào ảnh)\n- product send [tên]\n- product list\n- product delete [tên].",
    'power': "Quản trị viên"
}



def load_message_sets():
    """Đọc message_sets từ tệp JSON, nếu không tồn tại thì trả về danh sách rỗng."""
    try:
        if os.path.exists(MESSAGE_SETS_FILE):
            with open(MESSAGE_SETS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for ms in data:
                    if 'time_slot' in ms:
                        ms['time_slot'] = set(ms['time_slot'])
                return data
        return []
    except Exception as e:
        print(f"Lỗi khi đọc tệp {MESSAGE_SETS_FILE}: {e}")
        return []

def save_message_sets(message_sets):
    """Ghi message_sets vào tệp JSON."""
    try:
        data = [
            {**ms, 'time_slot': list(ms['time_slot'])}
            for ms in message_sets
        ]
        with open(MESSAGE_SETS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Lỗi khi ghi tệp {MESSAGE_SETS_FILE}: {e}")

message_sets = load_message_sets()

VN_TZ = pytz.timezone('Asia/Ho_Chi_Minh')

def get_excluded_group_ids():
    try:
        with open("danhsachnhom.json", "r", encoding="utf-8") as f:
            groups = json.load(f)
            return {grp.get("group_id") for grp in groups}
    except Exception as e:
        print(f"Lỗi khi đọc file danhsachnhom.json: {e}")
        return set()

def get_allowed_groups(client, excluded_group_ids):
    all_groups = client.fetchAllGroups()
    return {gid for gid in all_groups.gridVerMap.keys() if gid not in excluded_group_ids}

# =================================================================
# ====================== HỖ TRỢ GỬI VIDEO =========================
# =================================================================

def send_video_to_group(client, thread_id, video_path, message_set):
    try:
        if not os.path.exists(video_path):
            print(f"Không tìm thấy video tại {video_path}")
            return
        
        msg = Message(text=message_set['message'])
        client.sendLocalVideo(
            video_path,
            thread_id=thread_id,
            thread_type=ThreadType.GROUP,
            message=msg,
            ttl=600000
        )
    except Exception as e:
        print(f"Lỗi gửi video đến {thread_id}: {e}")

# =================================================================
# ================ NÂNG CẤP GỬI ẢNH + VIDEO =======================
# =================================================================

def send_message_to_group(client, thread_id, current_time_str, message_set):
    file_path = message_set.get('file_path') or message_set.get('image_path')
    msg_type = message_set.get('type', 'image')

    if not os.path.exists(file_path):
        print(f"Không tìm thấy file tại {file_path} cho thread_id {thread_id}")
        return

    try:
        if msg_type == "video":
            send_video_to_group(client, thread_id, file_path, message_set)
        else:
            message = Message(text=message_set['message'])
            client.sendLocalImage(
                file_path,
                thread_id=thread_id,
                thread_type=ThreadType.GROUP,
                message=message,
                width=message_set['width'],
                height=message_set['height'],
                ttl=600000
            )
    except Exception as e:
        print(f"Lỗi khi gửi tin nhắn đến {thread_id}: {e}")

# =================================================================

def auto_send(client, allowed_thread_ids):
    if not message_sets:
        print("Không có bộ tin nhắn nào được định nghĩa.")
        return
    last_sent_time = None
    while True:
        now = datetime.now(VN_TZ)
        current_time_str = now.strftime("%H:%M")
        for message_set in message_sets:
            if current_time_str in message_set['time_slot'] and (last_sent_time is None or now - last_sent_time >= timedelta(minutes=1)):
                try:
                    for thread_id in allowed_thread_ids:
                        send_message_to_group(client, thread_id, current_time_str, message_set)
                        time.sleep(2)
                    last_sent_time = now
                except Exception as e:
                    print(f"Lỗi trong quá trình tự động gửi: {e}")
        time.sleep(30)

def start_auto(client):
    try:
        if not message_sets:
            print("Không có bộ tin nhắn nào được định nghĩa để gửi tự động.")
            return
        excluded_group_ids = get_excluded_group_ids()
        allowed_thread_ids = get_allowed_groups(client, excluded_group_ids)
        auto_send(client, allowed_thread_ids)
    except Exception as e:
        print(f"Lỗi khi khởi tạo tự động gửi: {e}")

def handle_autosend_start(message, message_object, thread_id, thread_type, author_id, client):
    if not message_sets:
        response_message = Message(text="Không có bộ tin nhắn nào được định nghĩa. Vui lòng thêm bộ bằng lệnh addset.")
        client.replyMessage(response_message, message_object, thread_id, thread_type)
        return
    threading.Thread(target=start_auto, args=(client,), daemon=True).start()
    response_message = Message(text="Đã bật tính năng tự động gửi quảng cáo theo thời gian đã định ✅🚀")
    client.replyMessage(response_message, message_object, thread_id, thread_type)

def handle_send_set(message, message_object, thread_id, thread_type, author_id, client):
    try:
        parts = message.split(" ", 1)
        if len(parts) != 2:
            response_message = Message(text="Cú pháp không hợp lệ. Sử dụng: sendset <tên_bộ>")
            client.replyMessage(response_message, message_object, thread_id, thread_type)
            return
        
        set_name = parts[1].strip()
        message_set = next((ms for ms in message_sets if ms['name'] == set_name), None)
        if not message_set:
            response_message = Message(text=f"Không tìm thấy bộ tin nhắn {set_name}.")
            client.replyMessage(response_message, message_object, thread_id, thread_type)
            return
        
        file_path = message_set.get("file_path")
        if not os.path.exists(file_path):
            response_message = Message(text=f"Lỗi: Không tìm thấy file tại {file_path} cho bộ {set_name}.")
            client.replyMessage(response_message, message_object, thread_id, thread_type)
            return
        
        start_message = Message(text=f"Bắt đầu gửi tin nhắn của bộ {set_name} đến tất cả nhóm... ⏳")
        client.replyMessage(start_message, message_object, thread_id, thread_type)
        
        excluded_group_ids = get_excluded_group_ids()
        allowed_thread_ids = get_allowed_groups(client, excluded_group_ids)
        current_time_str = datetime.now(VN_TZ).strftime("%H:%M")
        
        for tid in allowed_thread_ids:
            send_message_to_group(client, tid, current_time_str, message_set)
            time.sleep(2)
        
        response_message = Message(text=f"Đã gửi tin nhắn của bộ {set_name} thành công ✅🚀")
        client.replyMessage(response_message, message_object, thread_id, thread_type)
    except Exception as e:
        response_message = Message(text=f"Lỗi khi gửi tin nhắn của bộ {set_name}: {e}")
        client.replyMessage(response_message, message_object, thread_id, thread_type)

def validate_time_slot(time_str):
    time_pattern = re.compile(r"^\d{2}:\d{2}$")
    return bool(time_pattern.match(time_str))

# =================================================================
# ==================== ADDSET NÂNG CẤP VIDEO ======================
# =================================================================
def handle_add_set(message, message_object, thread_id, thread_type, author_id, client):
    action = "✅"
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)
    try:
        parts = message.split("|", 5)
        if len(parts) != 6:
            response_message = Message(text="Cú pháp không hợp lệ. Sử dụng:\naddset tên_bộ | giờ1,giờ2 | link_file | width | height | nội_dung")
            client.replyMessage(response_message, message_object, thread_id, thread_type)
            return
        
        set_name = parts[0].strip().split(" ", 1)[1].strip()
        time_slots_str = parts[1].strip()
        file_path_input = parts[2].strip()
        width_str = parts[3].strip()
        height_str = parts[4].strip()
        message_content = parts[5].strip()

        if any(ms['name'] == set_name for ms in message_sets):
            response_message = Message(text=f"Bộ {set_name} đã tồn tại.")
            client.replyMessage(response_message, message_object, thread_id, thread_type)
            return
        
        time_slots = set(time_slots_str.split(","))
        if not all(validate_time_slot(ts.strip()) for ts in time_slots):
            response_message = Message(text="Khung giờ không hợp lệ (HH:MM).")
            client.replyMessage(response_message, message_object, thread_id, thread_type)
            return

        # ========================
        # XỬ LÝ FILE ẢNH / VIDEO
        # ========================

        local_path = file_path_input
        msg_type = "image"

        # -------- TRƯỜNG HỢP VIDEO --------
        is_url = file_path_input.startswith(("http://", "https://"))
        is_video_ext = file_path_input.lower().endswith((".mp4", ".mov", ".mkv", ".avi"))

        if is_video_ext or is_url:

            # Nếu là URL → kiểm tra xem URL có phải video
            if is_url:
                ext_guess = file_path_input.split("?")[0].split(".")[-1].lower()
                if ext_guess in ["mp4", "mov", "mkv", "avi"]:
                    msg_type = "video"
                    local_path = f"{set_name}_video.{ext_guess}"

                    try:
                        r = requests.get(file_path_input, stream=True)
                        if r.status_code == 200:
                            with open(local_path, "wb") as f:
                                for chunk in r.iter_content(1024):
                                    f.write(chunk)
                        else:
                            response_message = Message(text="Không thể tải video từ URL.")
                            client.replyMessage(response_message, message_object, thread_id, thread_type)
                            return
                    except Exception as e:
                        response_message = Message(text=f"Lỗi khi tải video: {e}")
                        client.replyMessage(response_message, message_object, thread_id, thread_type)
                        return

                    width = 0
                    height = 0

                else:
                    # URL nhưng không phải video → coi như ảnh
                    msg_type = "image"
                    local_path = f"{set_name}.jpg"

                    try:
                        r = requests.get(file_path_input, stream=True)
                        if r.status_code == 200:
                            with open(local_path, "wb") as f:
                                for chunk in r.iter_content(1024):
                                    f.write(chunk)
                        else:
                            response_message = Message(text="Không tải được ảnh từ URL.")
                            client.replyMessage(response_message, message_object, thread_id, thread_type)
                            return
                    except Exception as e:
                        response_message = Message(text=f"Lỗi tải ảnh: {e}")
                        client.replyMessage(response_message, message_object, thread_id, thread_type)
                        return

                    width = int(width_str)
                    height = int(height_str)

            else:
                # File local video
                if os.path.exists(file_path_input):
                    msg_type = "video"
                    width = 0
                    height = 0
                else:
                    response_message = Message(text=f"Không tìm thấy file video tại {file_path_input}.")
                    client.replyMessage(response_message, message_object, thread_id, thread_type)
                    return

        # -------- TRƯỜNG HỢP ẢNH LOCAL --------
        else:
            if not os.path.exists(file_path_input):
                response_message = Message(text=f"Không tìm thấy file ảnh tại {file_path_input}.")
                client.replyMessage(response_message, message_object, thread_id, thread_type)
                return

            msg_type = "image"
            try:
                width = int(width_str)
                height = int(height_str)
            except:
                response_message = Message(text="Chiều rộng và chiều cao phải là số.")
                client.replyMessage(response_message, message_object, thread_id, thread_type)
                return

        # ============================
        # TẠO BỘ MỚI
        # ============================

        new_set = {
            'name': set_name,
            'time_slot': time_slots,
            'message': message_content,
            'file_path': local_path,
            'type': msg_type,
            'width': width,
            'height': height
        }

        message_sets.append(new_set)
        save_message_sets(message_sets)
        
        response_message = Message(text=f"Đã tạo bộ {set_name} thành công! ✅")
        client.replyMessage(response_message, message_object, thread_id, thread_type)
    
    except Exception as e:
        response_message = Message(text=f"Lỗi khi tạo bộ mới: {e}")
        client.replyMessage(response_message, message_object, thread_id, thread_type)

def send_video_to_group(client, thread_id, video_path, message_set):
    try:
        if not os.path.exists(video_path):
            print(f"Không tìm thấy video tại {video_path}")
            return
        
        msg = Message(text=message_set['message'])

        client.sendLocalVideo(
            video_path,
            thread_id=thread_id,
            thread_type=ThreadType.GROUP,
            message=msg
        )

        print(f"Đã gửi video tới nhóm {thread_id}")

    except Exception as e:
        print(f"Lỗi gửi video đến {thread_id}: {e}")

# =================================================================

def handle_list_sets(message, message_object, thread_id, thread_type, author_id, client):
    action = "✅"
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)
    try:
        if not message_sets:
            response_message = Message(text="Hiện tại không có bộ tin nhắn nào.")
        else:
            set_names = [ms['name'] for ms in message_sets]
            response_text = "Danh sách bộ tin nhắn:\n" + "\n".join(f"- {name}" for name in set_names)
            response_message = Message(text=response_text)
        client.replyMessage(response_message, message_object, thread_id, thread_type)
    except Exception as e:
        response_message = Message(text=f"Lỗi khi hiển thị danh sách bộ: {e}")
        client.replyMessage(response_message, message_object, thread_id, thread_type)

def handle_del_set(message, message_object, thread_id, thread_type, author_id, client):
    action = "✅"
    client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)
    try:
        parts = message.split(" ", 1)
        if len(parts) != 2:
            response_message = Message(text="Cú pháp: delset <tên_bộ>")
            client.replyMessage(response_message, message_object, thread_id, thread_type)
            return
        
        set_name = parts[1].strip()
        global message_sets
        message_set = next((ms for ms in message_sets if ms['name'] == set_name), None)
        if not message_set:
            response_message = Message(text=f"Không tìm thấy bộ {set_name}.")
            client.replyMessage(response_message, message_object, thread_id, thread_type)
            return
        
        message_sets = [ms for ms in message_sets if ms['name'] != set_name]
        save_message_sets(message_sets)
        
        response_message = Message(text=f"Đã xóa bộ {set_name} thành công! ✅")
        client.replyMessage(response_message, message_object, thread_id, thread_type)
    except Exception as e:
        response_message = Message(text=f"Lỗi khi xóa bộ: {e}")
        client.replyMessage(response_message, message_object, thread_id, thread_type)

def handle_set_video(message, message_object, thread_id, thread_type, author_id, client):
    try:
        parts = message.split(" ", 2)

        if len(parts) < 2:
            resp = Message(text="❌ Cú pháp sai!\nDùng:\n- setvideo <tên_bộ> (và reply video)\n- setvideo <tên_bộ> <link_video>")
            client.replyMessage(resp, message_object, thread_id, thread_type)
            return
        
        set_name = parts[1].strip()

        # Tìm bộ
        message_set = next((ms for ms in message_sets if ms['name'] == set_name), None)
        if not message_set:
            resp = Message(text=f"❌ Không tìm thấy bộ '{set_name}'.")
            client.replyMessage(resp, message_object, thread_id, thread_type)
            return

        # ========================================
        # 1) TRƯỜNG HỢP DÙNG LINK VIDEO
        # ========================================
        video_url = None

        if len(parts) == 3:
            # Người dùng nhập link video → dùng luôn
            maybe_link = parts[2].strip()
            if maybe_link.startswith("http"):
                video_url = maybe_link
            else:
                resp = Message(text="❌ Link video không hợp lệ!")
                client.replyMessage(resp, message_object, thread_id, thread_type)
                return

        # ========================================
        # 2) TRƯỜNG HỢP REPLY VIDEO
        # ========================================
        if not video_url:
            if not message_object.reply or "video" not in message_object.reply:
                resp = Message(text="❌ Bạn phải reply vào 1 video hoặc nhập link!\nVí dụ:\nsetvideo test https://abc/video.mp4")
                client.replyMessage(resp, message_object, thread_id, thread_type)
                return

            video_info = message_object.reply["video"]
            video_url = video_info.get("url")

        if not video_url:
            resp = Message(text="❌ Không lấy được URL video!")
            client.replyMessage(resp, message_object, thread_id, thread_type)
            return

        # ========================================
        # TẢI VIDEO VỀ
        # ========================================
        local_path = f"{set_name}_video.mp4"
        try:
            r = requests.get(video_url, stream=True)
            if r.status_code == 200:
                with open(local_path, "wb") as f:
                    for chunk in r.iter_content(1024):
                        f.write(chunk)
            else:
                resp = Message(text=f"❌ Không tải được video. Mã lỗi: {r.status_code}")
                client.replyMessage(resp, message_object, thread_id, thread_type)
                return
        except Exception as e:
            resp = Message(text=f"❌ Lỗi tải video: {e}")
            client.replyMessage(resp, message_object, thread_id, thread_type)
            return

        # ========================================
        # GHI VÀO BỘ
        # ========================================
        message_set["file_path"] = local_path
        message_set["type"] = "video"
        message_set["width"] = 0
        message_set["height"] = 0
        
        save_message_sets(message_sets)

        resp = Message(text=f"🎥 Đã cập nhật VIDEO cho bộ **{set_name}** thành công!")
        client.replyMessage(resp, message_object, thread_id, thread_type)

    except Exception as e:
        resp = Message(text=f"❌ Lỗi trong setvideo: {e}")
        client.replyMessage(resp, message_object, thread_id, thread_type)

def PTA():
    return {
        'quangcao': handle_autosend_start,
        'addset': handle_add_set,
        'sendset': handle_send_set,
        'listsets': handle_list_sets,
        'delset': handle_del_set,
        'setvideo': handle_set_video
    }
