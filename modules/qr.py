# -*- coding: UTF-8 -*-
import os
import time
import random
import threading
import requests
from zlapi.models import Message, MessageStyle, MultiMsgStyle

# ==============================
# THÔNG TIN MODULE
# ==============================
des = {
    'version': "1.0.0",
    'credits': "Antigravity",
    'description': "Gửi QR thanh toán với tin nhắn màu sắc ngẫu nhiên",
    'power': "Quản trị viên Bot"
}

QR_IMAGE_URL = "https://files.catbox.moe/ijuucq.jpeg"

ALL_COLORS = [
    "#DB342E",  # Đỏ
    "#15A85F",  # Xanh lá
    "#F27806",  # Cam
    "#F7B503"   # Vàng
]

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_PATH = os.path.join(ROOT_DIR, "modules/cache")
if not os.path.exists(CACHE_PATH):
    os.makedirs(CACHE_PATH)


def is_admin(author_id):
    try:
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
        except Exception:
            config_admin = ""

        admins = set([admin_main, config_admin] + vip + adm_list)
        admins.discard("")

        return author_str in admins
    except Exception:
        try:
            from config import ADMIN
            return str(author_id) == str(ADMIN)
        except Exception:
            return False


def handle_qr_command(message, message_object, thread_id, thread_type, author_id, client):
    def process():
        file_path = None
        try:
            # Lấy tên người dùng
            try:
                user_info = client.fetchUserInfo(author_id)
                user_name = user_info.changed_profiles.get(str(author_id), {}).get("zaloName", "Chủ nhân")
            except Exception:
                user_name = "Chủ nhân"

            # Random màu sắc
            color = random.choice(ALL_COLORS)

            # Gửi tin nhắn chờ với tên đẹp + màu random
            wait_text = f"{user_name}\n➜ Chủ nhân xin chờ ạ 💎"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(user_name), style="color", color=color, auto_format=False),
                MessageStyle(offset=0, length=len(user_name), style="bold", auto_format=False)
            ])
            client.replyMessage(
                Message(text=wait_text, style=styles),
                message_object, thread_id, thread_type, ttl=10000
            )

            # Tải ảnh QR từ link
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            r = requests.get(QR_IMAGE_URL, headers=headers, timeout=15)
            r.raise_for_status()

            file_name = f"qr_{author_id}_{int(time.time())}.jpeg"
            file_path = os.path.join(CACHE_PATH, file_name)
            with open(file_path, 'wb') as f:
                f.write(r.content)

            # Gửi ảnh QR lên nhóm
            color2 = random.choice(ALL_COLORS)
            qr_text = "📌 QR Thanh Toán"
            qr_styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(qr_text), style="color", color=color2, auto_format=False),
                MessageStyle(offset=0, length=len(qr_text), style="bold", auto_format=False)
            ])

            client.sendLocalImage(
                file_path,
                thread_id,
                thread_type,
                message=Message(text=qr_text, style=qr_styles)
            )

        except requests.exceptions.RequestException as e:
            client.replyMessage(
                Message(text=f"❌ Lỗi khi tải ảnh QR: {e}"),
                message_object, thread_id, thread_type
            )
        except Exception as e:
            client.replyMessage(
                Message(text=f"❌ Đã xảy ra lỗi: {e}"),
                message_object, thread_id, thread_type
            )
        finally:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass

    threading.Thread(target=process, daemon=True).start()


# ==============================
# ĐĂNG KÝ LỆNH
# ==============================
def PTA():
    return {
        'qr': handle_qr_command
    }
