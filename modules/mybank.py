import os
import random
import json
import requests
import urllib.parse
from zlapi.models import Message, MultiMsgStyle, MessageStyle
from logging_utils import Logging
from config import ADMIN, PREFIX 
logger = Logging()

des = {
    'version': "2.0.0",
    'credits': "ngbao",
    'description': "Quản lý thông tin tài khoản ngân hàng và QR Code cho bot.",
    'power': "Thành Viên"
}

BANK_DATA_FILE_NAME = "bank_data.json"
QR_IMAGE_FILE_PATH = "modules/data/bank/ảnh.jpg"

def is_admin(author_id):
    return str(author_id) in ADMIN
    
def _load_bank_data():
    file_path = os.path.join("modules/data/bank", BANK_DATA_FILE_NAME)
    default_data = {
        "stats_message": """
========================
💎: Số Tài Khoản   
✨ 0961557419 🪪
‼️ Qr Được Gửi Đi Kèm
========================
🏦: Ngân Hàng Thụ Hưởng
         ZaloPay / BV Bank
========================
📩: Nội Dung Giao Dịch
         Tên Zalo Bạn
========================
""",
        "qr_image_local_path": QR_IMAGE_FILE_PATH
    }
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for key, value in default_data.items():
                    if key not in data:
                        data[key] = value
                return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Tệp ngân hàng {file_path} không tìm thấy hoặc lỗi JSON: {e}. Tạo dữ liệu mặc định.")
    return default_data

def _save_bank_data(data):
    file_path = os.path.join("modules/data/bank", BANK_DATA_FILE_NAME)
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Lỗi khi lưu dữ liệu ngân hàng vào {file_path}: {e}")

def _download_image(url, save_path):
    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        logger.error(f"Lỗi khi tải ảnh từ URL {url}: {e}")
        return False

def _reply_styled_message(client, message_content, message_object, thread_id, thread_type, author_id):
    user_info = client.fetchUserInfo(author_id)
    author_name = user_info.changed_profiles.get(str(author_id), {}).get('zaloName', 'Không xác định') if user_info and user_info.changed_profiles else 'Không xác định'
    msg = f"{author_name}\n➜{message_content}"
    styles = MultiMsgStyle([
        MessageStyle(offset=0, length=len(author_name), style="color", color="#db342e", auto_format=False),
        MessageStyle(offset=0, length=len(author_name), style="bold", auto_format=False)
    ])
    client.replyMessage(
        Message(text=msg, style=styles),
        message_object, thread_id=thread_id, thread_type=thread_type, ttl=12000
    )

def handle_mybank_command(message, message_object, thread_id, thread_type, author_id, client):
    # giữ nguyên nội dung người dùng nhập
    cmd_parts = message.strip().split(maxsplit=2)
    main_command = cmd_parts[0].lower() if len(cmd_parts) > 0 else None
    sub_command = cmd_parts[1].lower() if len(cmd_parts) > 1 else None

    if sub_command == "set":
        if not is_admin(author_id):
            _reply_styled_message(client, "🚫 Bạn không có quyền thiết lập ảnh QR ngân hàng.", message_object, thread_id, thread_type, author_id)
            return
        if not message_object.quote or not message_object.quote.attach:
            _reply_styled_message(client, "⚠️ Vui lòng reply vào ảnh để thiết lập ảnh QR ngân hàng.", message_object, thread_id, thread_type, author_id)
            return
        try:
            attach_data = json.loads(message_object.quote.attach)
        except (json.JSONDecodeError, TypeError):
            _reply_styled_message(client, "❌ Dữ liệu đính kèm không hợp lệ.", message_object, thread_id, thread_type, author_id)
            return
        media_url = attach_data.get('hdUrl') or attach_data.get('href') or attach_data.get('oriUrl')
        if not media_url:
            _reply_styled_message(client, "❌ Không tìm thấy URL của ảnh từ tin nhắn reply.", message_object, thread_id, thread_type, author_id)
            return
        media_url = urllib.parse.unquote(media_url.replace("\\/", "/"))
        os.makedirs(os.path.dirname(QR_IMAGE_FILE_PATH), exist_ok=True)
        if _download_image(media_url, QR_IMAGE_FILE_PATH):
            bank_data = _load_bank_data()
            bank_data["qr_image_local_path"] = QR_IMAGE_FILE_PATH
            _save_bank_data(bank_data)
            _reply_styled_message(client, "✅ Đã thiết lập ảnh QR ngân hàng thành công!", message_object, thread_id, thread_type, author_id)
        else:
            _reply_styled_message(client, "❌ Lỗi khi tải ảnh QR. Vui lòng thử lại.", message_object, thread_id, thread_type, author_id)
        return
    elif sub_command == "setnd":
        if not client.is_allowed_author(author_id):
            _reply_styled_message(client, "🚫 Bạn không có quyền thiết lập nội dung tin nhắn ngân hàng.", message_object, thread_id, thread_type, author_id)
            return
        if len(cmd_parts) < 3:
            _reply_styled_message(client, "⚠️ Vui lòng cung cấp nội dung tin nhắn ngân hàng.\nVí dụ: mybank setnd <Nội dung>", message_object, thread_id, thread_type, author_id)
            return
        new_stats_message = cmd_parts[2]  # giữ nguyên in hoa/in thường
        bank_data = _load_bank_data()
        bank_data["stats_message"] = new_stats_message
        _save_bank_data(bank_data)
        _reply_styled_message(client, "✅ Đã thiết lập nội dung tin nhắn ngân hàng thành công!", message_object, thread_id, thread_type, author_id)
        return
    elif sub_command is None:
        bank_data = _load_bank_data()
        stats_message_to_send = bank_data.get("stats_message")
        qr_image_path = bank_data.get("qr_image_local_path")
        if qr_image_path and os.path.exists(qr_image_path):
            try:
                client.sendLocalImage(
                    imagePath=qr_image_path,
                    message=Message(text=stats_message_to_send),
                    thread_id=thread_id,
                    thread_type=thread_type,
                    width=1080,
                    height=1080,
                    ttl=500000
                )
            except Exception as e:
                logger.error(f"Lỗi khi gửi ảnh QR: {e}")
                client.sendMessage(
                    Message(text=stats_message_to_send),
                    thread_id, thread_type, ttl=60000
                )
        else:
            client.sendMessage(
                Message(text=stats_message_to_send),
                thread_id, thread_type, ttl=60000
            )
        icon_list = ["💵", "💴", "💶", "💳", "💵", "💴", "💶", "💳"]
        random_emojis = random.sample(icon_list, min(4, len(icon_list)))
        for emoji_icon in random_emojis:
            try:
                client.sendReaction(
                    message_object, emoji_icon, thread_id, thread_type
                )
            except Exception as e:
                logger.error(f"Lỗi khi gửi phản ứng {emoji_icon}: {e}")
        return
    else:
        _reply_styled_message(client, "⚠️ Cú pháp không hợp lệ. Vui lòng sử dụng:\n"
                                     "  - mybank: Xem thông tin ngân hàng.\n"
                                     "  - mybank set <reply ảnh>: Thiết lập ảnh QR.\n"
                                     "  - mybank setnd <nội dung>: Thiết lập nội dung text.",
                               message_object, thread_id, thread_type, author_id)
        return

def PTA():
    return {
        'mybank': handle_mybank_command
    }
