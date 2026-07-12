# -*- coding: UTF-8 -*-
import os
import time
import threading
import json
from zlapi.models import Message, Mention, MessageStyle, MultiMsgStyle
from config import ADMIN, PREFIX

# ==============================
# THÔNG TIN MODULE
# ==============================
des = {
    'version': "1.1.0",
    'credits': "ngbao",
    'description': "Nhây Tag với cấu hình delay tùy chọn",
    'power': "Quản trị viên Bot"
}

is_nhaytag_running = False
CONFIG_PATH = "nhaytag_config.json"

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"delay": 0.3}

def save_config(config):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Lỗi lưu cấu hình nhaytag: {e}")

# ==============================
# HÀM GỬI TIN NHẮN ĐẸP (tên đỏ + in đậm)
# ==============================
def send_styled_message(author_id, text, message_object, thread_id, thread_type, client):
    try:
        user_info = client.fetchUserInfo(author_id)
        user_name = user_info.changed_profiles.get(str(author_id), {}).get("zaloName", "Người dùng")

        msg = f"{user_name}\n➜ {text}"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(user_name), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(user_name), style="bold", auto_format=False)
        ])
        message_to_send = Message(text=msg, style=styles)
        client.replyMessage(message_to_send, message_object, thread_id, thread_type, ttl=8000)
    except Exception as e:
        print(f"Lỗi khi gửi styled message: {e}")


# ==============================
# DỪNG NHẢY TAG
# ==============================
def stop_nhaytag(client, message_object, thread_id, thread_type, author_id):
    global is_nhaytag_running
    is_nhaytag_running = False
    send_styled_message(author_id, "✅ Đã dừng nhaytag", message_object, thread_id, thread_type, client)


def is_admin(author_id):
    try:
        import os
        import json
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'seting.json')
        if not os.path.exists(path):
            path = 'seting.json'
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        admin_main = str(data.get('admin', ''))
        vip = [str(x) for x in data.get('vip_adm', [])]
        adm_list = [str(x) for x in data.get('adm', [])]
        
        author_str = str(author_id)
        
        try:
            from config import ADMIN
            config_admin = str(ADMIN)
        except:
            config_admin = ""
            
        admins = set([admin_main, config_admin] + vip + adm_list)
        if "" in admins:
            admins.remove("")
            
        return author_str in admins
    except Exception as e:
        print(f"Error checking admin in nhaytag: {e}")
        return str(author_id) == str(ADMIN)

# ==============================
# HÀM CHÍNH NHẢY TAG
# ==============================
def handle_nhaytag_command(message, message_object, thread_id, thread_type, author_id, client):
    global is_nhaytag_running

    # Kiểm tra quyền admin
    if not is_admin(author_id):
        send_styled_message(author_id, "⛔ Bạn không có quyền sử dụng lệnh này", message_object, thread_id, thread_type, client)
        return

    command_parts = message.split()
    if len(command_parts) < 2:
        send_styled_message(author_id, f"❗ Dùng đúng cú pháp:\n👉 {PREFIX}nhaytag on\n👉 {PREFIX}nhaytag stop\n👉 {PREFIX}nhaytag delay [số giây]", message_object, thread_id, thread_type, client)
        return

    action = command_parts[1].lower()

    # Cài đặt delay
    if action == "delay":
        if len(command_parts) < 3:
            config = load_config()
            send_styled_message(author_id, f"🚨 Delay hiện tại của nhaytag: {config.get('delay', 0.3)} giây.\nCú pháp đặt: {PREFIX}nhaytag delay [giây]", message_object, thread_id, thread_type, client)
            return
        
        try:
            delay_val = float(command_parts[2].strip())
            if delay_val <= 0:
                raise ValueError()
        except ValueError:
            send_styled_message(author_id, "❌ Số giây delay phải là một số lớn hơn 0!", message_object, thread_id, thread_type, client)
            return
        
        config = load_config()
        config["delay"] = delay_val
        save_config(config)
        send_styled_message(author_id, f"✅ Đã đặt delay nhaytag thành: {delay_val} giây", message_object, thread_id, thread_type, client)
        return

    # Nếu stop
    if action == "stop":
        if not is_nhaytag_running:
            send_styled_message(author_id, "⚠️ Không có tiến trình nhaytag nào đang chạy", message_object, thread_id, thread_type, client)
        else:
            stop_nhaytag(client, message_object, thread_id, thread_type, author_id)
        return

    if action != "on":
        send_styled_message(author_id, f"❗ Lệnh không hợp lệ. Dùng:\n👉 {PREFIX}nhaytag on / stop / delay [giây]", message_object, thread_id, thread_type, client)
        return

    # Kiểm tra tag
    if not message_object.mentions:
        send_styled_message(author_id, "⚠️ Vui lòng tag người cần nhaytag", message_object, thread_id, thread_type, client)
        return

    tagged_user = message_object.mentions[0]['uid']

    # Lấy tên người được tag
    try:
        tag_info = client.fetchUserInfo(tagged_user)
        tag_name = tag_info.changed_profiles.get(str(tagged_user), {}).get("zaloName", "Người được tag")
    except Exception:
        tag_name = "Người được tag"

    # Đọc nội dung từ file
    try:
        with open("noidung.txt", "r", encoding="utf-8") as file:
            lines = [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        send_styled_message(author_id, "❌ Không tìm thấy file noidung.txt", message_object, thread_id, thread_type, client)
        return

    if not lines:
        send_styled_message(author_id, "⚠️ File noidung.txt trống, không có gì để gửi", message_object, thread_id, thread_type, client)
        return

    is_nhaytag_running = True
    config = load_config()
    delay_val = config.get("delay", 0.3)
    send_styled_message(author_id, f"🚀 Bắt đầu nhaytag {tag_name} với delay {delay_val}s ({len(lines)} dòng, lặp vô hạn cho đến khi stop)", message_object, thread_id, thread_type, client)

    # ==============================
    # VÒNG LẶP NHẢY TAG
    # ==============================
    def nhaytag_loop():
        global is_nhaytag_running
        while is_nhaytag_running:
            for noidung in lines:
                if not is_nhaytag_running:
                    break
                try:
                    mention_text = f"@{tag_name} "
                    mention = Mention(uid=tagged_user, length=len(mention_text.strip()), offset=0)
                    msg = Message(text=f"{mention_text}{noidung}", mention=mention)
                    client.send(msg, thread_id, thread_type, ttl=4000)
                    time.sleep(delay_val)
                except Exception as e:
                    print(f"Lỗi khi gửi nhaytag: {e}")
                    send_styled_message(author_id, f"⚠️ Lỗi khi gửi: {e}", message_object, thread_id, thread_type, client)
                    break

    threading.Thread(target=nhaytag_loop).start()


# ==============================
# ĐĂNG KÝ LỆNH
# ==============================
def PTA():
    return {
        "nhaytag": handle_nhaytag_command
    }