import os
import json
import time
import random
import requests
from datetime import datetime
from zlapi.models import Message, MultiMsgStyle, MessageStyle
from config import ADMIN, PREFIX

des = {
    'version': "1.0.1",
    'credits': "ngbao",
    'description': "Chia sẻ bài viết ảo Facebook",
    'power': "Thành Viên"
}

TOKEN_FILE = 'modules/cache/token.json'
HEADERS = {
    'authority': 'graph.facebook.com',
    'accept': 'application/json',
    'user-agent': 'Mozilla/5.0',
}

ADMIN_ID = ADMIN

def is_admin(author_id):
    return str(author_id) == ADMIN_ID

def load_tokens():
    """Tải danh sách token từ file"""
    if not os.path.exists(TOKEN_FILE):
        return []
    with open(TOKEN_FILE, 'r') as f:
        return json.load(f)

def share_post(id_post, quantity, delay, privacy, client, thread_id, thread_type):
    tokens = load_tokens()
    if not tokens:
        client.sendMessage(Message(text="Không tìm thấy token. Vui lòng kiểm tra file token."), thread_id, thread_type)
        return
    
    success_count = 0
    failed_count = 0

    for _ in range(quantity):
        token = random.choice(tokens)
        try:
            url = "https://graph.facebook.com/me/feed"
            payload = {
                "link": f"https://m.facebook.com/{id_post}",
                "published": 0,
                "privacy": json.dumps({"value": "EVERYONE" if privacy == 1 else "SELF"}),
                "access_token": token
            }
            response = requests.post(url, headers=HEADERS, data=payload)
            response.raise_for_status()

            success_count += 1
            print(f"[SUCCESS] {success_count}/{quantity} - Token: {token} - Time: {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            failed_count += 1
            print(f"[FAILED] Token: {token} - Error: {str(e)} - Time: {datetime.now().strftime('%H:%M:%S')}")
        
        time.sleep(delay / 1000)

    client.sendMessage(
        Message(text=f"✅ Hoàn thành chia sẻ!\nThành công: {success_count}\nThất bại: {failed_count}"),
        thread_id, thread_type
    )

def handle_shareao_command(message, message_object, thread_id, thread_type, author_id, client):
    user_info = client.fetchUserInfo(author_id)
    author_info = user_info.changed_profiles.get(str(author_id), {}) if user_info and user_info.changed_profiles else {}
    name = author_info.get('zaloName', 'Không xác định')

    params = message.split()
    if len(params) != 2:
        rest_text = (
            f"Hướng dẫn sử dụng lệnh {PREFIX}shareao:\n"
            f"• {PREFIX}shareao <id bài viết>|<số lần>|<thời gian ms>|<quyền riêng tư>\n"
            f"Ví dụ: {PREFIX}shareao 123456|5|2000|1\n\n"
            f"Quyền riêng tư:\n"
            f"1 = Công khai 🌐\n"
            f"2 = Riêng tư 🔒"
        )
        msg = f"{name}\n➜ {rest_text}"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
        ])
        client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=20000)
        return

    try:
        id_post, quantity, delay, privacy = params[1].split('|')
        quantity = int(quantity)
        delay = int(delay)
        privacy = int(privacy)

        if privacy not in [1, 2]:
            raise ValueError("Quyền riêng tư không hợp lệ.")

        rest_text = (
            f"Đang thực hiện chia sẻ bài viết 📢 {id_post}\n"
            f"Số lần: {quantity}\n"
            f"Thời gian chờ: {delay}ms\n"
            f"Chế độ: {'Công khai 🌐' if privacy == 1 else 'Riêng tư 🔒'}"
        )
        msg = f"{name}\n➜ {rest_text}"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
        ])
        client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=10000)

        share_post(id_post, quantity, delay, privacy, client, thread_id, thread_type)

    except ValueError as ve:
        msg = f"{name}\n➜ Lỗi: {str(ve)}"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
        ])
        client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=8000)
    except Exception as e:
        msg = f"{name}\n➜ Có lỗi xảy ra: {str(e)}"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
        ])
        client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=8000)

def PTA():
    return {
        'shareao': handle_shareao_command
    }