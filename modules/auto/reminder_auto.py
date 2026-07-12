# -*- coding: UTF-8 -*-
import json
import os
import time
from datetime import datetime
from zlapi.models import Message, ThreadType, Mention

REMINDERS_FILE = "modules/cache/reminders.json"

des = {
    'version': "1.0.0",
    'credits': "Bot DCM",
    'description': "Tự động gửi nhắc nhở cho người dùng"
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

def start_auto(client):
    def reminder_loop():
        print("[REMINDER_AUTO] Luồng nhắc nhở đã khởi động.")
        while True:
            try:
                reminders = load_reminders()
                current_time = time.time()
                triggered = []
                remaining = []
                
                for r in reminders:
                    if r.get("remind_at", 0) <= current_time:
                        triggered.append(r)
                    else:
                        remaining.append(r)
                        
                if triggered:
                    # Lưu lại danh sách còn lại trước khi gửi để tránh trùng lặp
                    save_reminders(remaining)
                    
                    for r in triggered:
                        user_id = r.get("user_id")
                        thread_id = r.get("thread_id")
                        thread_type = r.get("thread_type")
                        content = r.get("content")
                        created_at = r.get("created_at")
                        
                        user_name = get_user_display_name(client, user_id)
                        created_time_str = datetime.fromtimestamp(created_at).strftime("%H:%M:%S %d/%m/%Y")
                        
                        mention_name = f"@{user_name}"
                        msg_text = f"🔔 {mention_name} ➜ ĐẾN GIỜ NHẮC NHỞ!\n📝 Nội dung: {content}\n📅 Đặt lúc: {created_time_str}"
                        
                        mentions = [Mention(uid=str(user_id), length=len(mention_name), offset=2)]
                        
                        try:
                            client.sendMessage(
                                Message(text=msg_text, mention=mentions),
                                thread_id=thread_id,
                                thread_type=ThreadType(thread_type)
                            )
                        except Exception as send_err:
                            print(f"[REMINDER_AUTO] Lỗi khi gửi nhắc nhở đến {thread_id}: {send_err}")
                            
            except Exception as e:
                print(f"[REMINDER_AUTO] Lỗi trong loop: {e}")
                
            time.sleep(2)

    import threading
    t = threading.Thread(target=reminder_loop, daemon=True)
    t.start()
