# -*- coding: UTF-8 -*-
import json
import os
import time
import re
from datetime import datetime
from zlapi.models import Message, ThreadType

REMINDERS_FILE = "modules/cache/reminders.json"

des = {
    'version': "1.0.0",
    'credits': "Bot DCM",
    'description': "Đặt nhắc nhở thông minh cho người dùng",
    'power': "Thành Viên"
}

def load_reminders():
    if os.path.exists(REMINDERS_FILE):
        try:
            with open(REMINDERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_reminders(data):
    os.makedirs(os.path.dirname(REMINDERS_FILE), exist_ok=True)
    try:
        with open(REMINDERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Lỗi khi lưu nhắc nhở: {e}")

def parse_time_duration(time_str):
    if not time_str:
        return None
    unit = time_str[-1].lower()
    try:
        if unit == 's':
            value = int(time_str[:-1])
            return value
        elif unit == 'm':
            value = int(time_str[:-1])
            return value * 60
        elif unit == 'h':
            value = int(time_str[:-1])
            return value * 3600
        elif unit == 'd':
            value = int(time_str[:-1])
            return value * 86400
        else:
            return int(time_str)
    except ValueError:
        return None

def format_duration(seconds):
    if seconds < 60:
        return f"{seconds} giây"
    elif seconds < 3600:
        return f"{seconds // 60} phút"
    elif seconds < 86400:
        return f"{seconds // 3600} giờ"
    else:
        return f"{seconds // 86400} ngày"

def get_user_display_name(client, user_id):
    try:
        user_info = client.fetchUserInfo(user_id)
        if user_info and hasattr(user_info, 'changed_profiles'):
            fetched_name = user_info.changed_profiles.get(str(user_id), {}).get('zaloName')
            if fetched_name and fetched_name != 'không xác định':
                return fetched_name
            else:
                return user_info.changed_profiles.get(str(user_id), {}).get('displayName', str(user_id))
    except Exception:
        pass
    return str(user_id)

def handle_reminder_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        text = message.strip()
        match = re.search(r'(reminder|remind)\s+(.*)', text, re.IGNORECASE)
        if not match:
            # Gửi hướng dẫn
            guide = (
                "⏰ HƯỚNG DẪN DÙNG LỆNH NHẮC NHỞ (REMINDER)\n\n"
                "📌 1. Tạo nhắc nhở mới:\n"
                "👉 Cú pháp: !reminder <thời gian> <nội dung>\n"
                "📍 Đơn vị thời gian: s (giây), m (phút), h (giờ), d (ngày)\n"
                "📍 Ví dụ: !reminder 10m mua sữa, !reminder 1h học bài\n\n"
                "📌 2. Các lệnh quản lý:\n"
                "👉 Xem danh sách nhắc nhở: !reminder list\n"
                "👉 Xóa nhắc nhở: !reminder delete <mã_nhắc_nhở>\n"
                "📍 Ví dụ: !reminder delete 3"
            )
            client.replyMessage(Message(text=guide), message_object, thread_id, thread_type, ttl=45000)
            return
            
        arg_content = match.group(2).strip()
        parts = arg_content.split(None, 1)
        
        # 1. Hiển thị danh sách nhắc nhở
        if arg_content.lower() == "list":
            reminders = load_reminders()
            thread_reminders = [r for r in reminders if str(r.get("thread_id")) == str(thread_id)]
            
            if not thread_reminders:
                client.replyMessage(Message(text="📭 Hiện tại cuộc trò chuyện này không có nhắc nhở nào đang chờ!"), message_object, thread_id, thread_type, ttl=30000)
                return
                
            msg = "📋 DANH SÁCH NHẮC NHỞ ĐANG CHỜ:\n\n"
            for r in thread_reminders:
                remind_time = datetime.fromtimestamp(r.get("remind_at")).strftime("%H:%M:%S %d/%m/%Y")
                user_name = get_user_display_name(client, r.get("user_id"))
                msg += (
                    f"🔹 Mã: #{r.get('id')}\n"
                    f"👤 Đặt bởi: {user_name}\n"
                    f"📝 Nội dung: {r.get('content')}\n"
                    f"⏰ Nhắc lúc: {remind_time}\n"
                    f"─────────────────\n"
                )
            client.replyMessage(Message(text=msg), message_object, thread_id, thread_type, ttl=120000)
            return
            
        # 2. Xóa nhắc nhở
        if parts[0].lower() in ["delete", "del", "remove", "xoa"]:
            if len(parts) < 2:
                client.replyMessage(Message(text="⚠️ Vui lòng nhập mã nhắc nhở cần xóa!\nVí dụ: !reminder delete 3"), message_object, thread_id, thread_type, ttl=20000)
                return
            try:
                remind_id = int(parts[1].strip())
            except ValueError:
                client.replyMessage(Message(text="⚠️ Mã nhắc nhở phải là số nguyên!"), message_object, thread_id, thread_type, ttl=20000)
                return
                
            reminders = load_reminders()
            found = False
            for r in reminders:
                if r.get("id") == remind_id:
                    from config import ADMIN
                    is_admin = str(author_id) == str(ADMIN)
                    is_creator = str(r.get("user_id")) == str(author_id)
                    
                    if not (is_admin or is_creator):
                        client.replyMessage(Message(text="❌ Bạn không có quyền xóa nhắc nhở của người khác!"), message_object, thread_id, thread_type, ttl=20000)
                        return
                        
                    reminders.remove(r)
                    save_reminders(reminders)
                    found = True
                    break
            
            if found:
                client.replyMessage(Message(text=f"✅ Đã xóa thành công nhắc nhở #{remind_id}!"), message_object, thread_id, thread_type, ttl=20000)
            else:
                client.replyMessage(Message(text=f"❌ Không tìm thấy nhắc nhở với mã #{remind_id}!"), message_object, thread_id, thread_type, ttl=20000)
            return

        # 3. Tạo nhắc nhở mới
        time_str = parts[0]
        if len(parts) < 2:
            client.replyMessage(Message(text="⚠️ Thiếu nội dung nhắc nhở!\nVí dụ: !reminder 10m mua sữa"), message_object, thread_id, thread_type, ttl=20000)
            return
            
        content = parts[1].strip()
        duration_secs = parse_time_duration(time_str)
        
        if duration_secs is None or duration_secs <= 0:
            client.replyMessage(Message(text="⚠️ Định dạng thời gian không hợp lệ!\nVí dụ: 10s, 5m, 2h, 1d"), message_object, thread_id, thread_type, ttl=20000)
            return
            
        current_time = time.time()
        remind_at = current_time + duration_secs
        
        reminders = load_reminders()
        new_id = 1
        if reminders:
            new_id = max(r.get("id", 0) for r in reminders) + 1
            
        new_reminder = {
            "id": new_id,
            "user_id": str(author_id),
            "thread_id": str(thread_id),
            "thread_type": int(thread_type),
            "message_id": str(message_object.msgId),
            "created_at": current_time,
            "remind_at": remind_at,
            "content": content
        }
        
        reminders.append(new_reminder)
        save_reminders(reminders)
        
        user_name = get_user_display_name(client, author_id)
        remind_time_str = datetime.fromtimestamp(remind_at).strftime("%H:%M:%S %d/%m/%Y")
        
        success_msg = (
            f"⏰ ĐÃ ĐẶT NHẮC NHỞ THÀNH CÔNG!\n\n"
            f"👤 Thành viên: {user_name}\n"
            f"📝 Nội dung: {content}\n"
            f"🕒 Nhắc lúc: {remind_time_str} (sau {format_duration(duration_secs)})\n"
            f"🆔 Mã số: #{new_id}"
        )
        client.replyMessage(Message(text=success_msg), message_object, thread_id, thread_type, ttl=60000)

    except Exception as e:
        client.replyMessage(Message(text=f"❌ Lỗi hệ thống: {e}"), message_object, thread_id, thread_type, ttl=20000)

def PTA():
    return {
        'reminder': handle_reminder_command,
        'remind': handle_reminder_command
    }
