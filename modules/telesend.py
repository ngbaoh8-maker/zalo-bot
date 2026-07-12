# telegram_sender.py - Module gửi Telegram
import requests
import json
import os
from datetime import datetime
try:
    from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, ENABLE_TELEGRAM
except ImportError:
    TELEGRAM_BOT_TOKEN = None
    TELEGRAM_CHAT_ID = None
    ENABLE_TELEGRAM = False

def send_telegram_message(text, parse_mode="HTML"):
    """Gửi tin nhắn đến Telegram"""
    
    # Kiểm tra bật/tắt
    if not ENABLE_TELEGRAM:
        return {"success": False, "error": "Telegram đang tắt"}
    
    # Kiểm tra token
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN.startswith("123456"):
        print("⚠️ Chưa cấu hình Telegram Bot Token!")
        return {"success": False, "error": "Chưa cấu hình bot token"}
    
    # Kiểm tra chat ID
    if not TELEGRAM_CHAT_ID or TELEGRAM_CHAT_ID.startswith("-100123"):
        print("⚠️ Chưa cấu hình Telegram Chat ID!")
        return {"success": False, "error": "Chưa cấu hình chat ID"}
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": parse_mode
        }
        
        response = requests.post(url, json=payload, timeout=10)
        result = response.json()
        
        if result.get("ok"):
            return {"success": True, "message_id": result.get("result", {}).get("message_id")}
        else:
            error_msg = result.get("description", "Unknown error")
            print(f"❌ Telegram error: {error_msg}")
            return {"success": False, "error": error_msg}
            
    except Exception as e:
        print(f"❌ Lỗi gửi Telegram: {e}")
        return {"success": False, "error": str(e)}

def format_add_notification(item_id, content, category, author_name):
    """Định dạng thông báo thêm dữ liệu"""
    current_time = datetime.now().strftime("%H:%M %d/%m/%Y")
    
    message = f"""🆕 <b>THÊM DỮ LIỆU MỚI</b>

⏰ <i>{current_time}</i>
🔢 <b>STT:</b> #{item_id}
🏷️ <b>Category:</b> {category}
👤 <b>Người thêm:</b> {author_name}

📝 <b>Nội dung:</b>
<code>{content}</code>

📊 <i>Thông báo từ Zalo Bot</i>"""
    
    return message

def format_delete_notification(item_id, content, author_name):
    """Định dạng thông báo xóa dữ liệu"""
    current_time = datetime.now().strftime("%H:%M %d/%m/%Y")
    
    message = f"""🗑️ <b>XÓA DỮ LIỆU</b>

⏰ <i>{current_time}</i>
🔢 <b>STT đã xóa:</b> #{item_id}
👤 <b>Người xóa:</b> {author_name}

📝 <b>Nội dung đã xóa:</b>
<code>{content[:100]}{'...' if len(content) > 100 else ''}</code>

⚠️ <i>Dữ liệu đã bị xóa vĩnh viễn</i>"""
    
    return message

def format_get_notification(item_id, content, author_name):
    """Định dạng thông báo lấy dữ liệu"""
    current_time = datetime.now().strftime("%H:%M %d/%m/%Y")
    
    message = f"""👀 <b>AI ĐÓ ĐANG XEM DỮ LIỆU</b>

⏰ <i>{current_time}</i>
🔢 <b>STT đang xem:</b> #{item_id}
👤 <b>Người xem:</b> {author_name}

📝 <b>Nội dung được xem:</b>
<code>{content[:100]}{'...' if len(content) > 100 else ''}</code>

🔍 <i>Ai đó đang check dữ liệu của bạn</i>"""
    
    return message