import logging
import random
import re
from typing import List, Tuple
from datetime import datetime, timedelta
import threading
import json
import os
import emoji
import pytz
from zlapi.models import *
import sys
from core.bot_sys import admin_cao, is_admin, read_settings

CONFIG_FILE = "config.json"
logging.basicConfig(level=logging.INFO, filename='bot_manager.log', encoding='utf-8')

des = {
    'version': "2.0.0",
    'credits': "ngbao",
    'description': "Quản lý hệ thống bot đa người dùng",
    'power': "Quản trị viên và thành viên"
}

def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        default_config = {"data": []}
        save_config(default_config)
        return default_config

def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Lỗi khi lưu config.json: {str(e)}")

def send_message(client, message_object, thread_id, thread_type, text):
    try:
        client.replyMessage(Message(text=text), message_object, thread_id, thread_type, ttl=120000)
    except Exception as e:
        logging.error(f"Lỗi khi gửi tin nhắn: {str(e)}")

def get_user_name_by_id(client, author_id):
    try:
        user_info = client.fetchUserInfo(author_id).changed_profiles[author_id]
        return user_info.zaloName or user_info.displayName
    except Exception:
        return "Người dùng không tồn tại"

def parse_time_duration(duration_str):
    if duration_str.lower() == "all":
        return "all"
    total_seconds = 0
    parts = duration_str.split()
    for part in parts:
        if not part:
            continue
        if part.endswith("d"):
            total_seconds += int(part[:-1]) * 86400
        elif part.endswith("h"):
            total_seconds += int(part[:-1]) * 3600
        elif part.endswith("m"):
            total_seconds += int(part[:-1]) * 60
        else:
            return None
    return total_seconds if total_seconds > 0 else None

def is_bot_active(author_id, client):
    config = load_config()
    vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    now = datetime.now(vietnam_tz)
    for bot in config.get("data", []):
        if str(bot.get("author_id")) == str(author_id):
            het_han = bot.get("het_han", None)
            if het_han:
                try:
                    expires_datetime = datetime.strptime(het_han, '%d/%m/%Y').replace(tzinfo=vietnam_tz)
                    if now > expires_datetime:
                        bot["status"] = False
                        save_config(config)
                        return False
                except ValueError:
                    pass
            return bot.get("status", False)
    return False

def deactivate_bot(target_author_id, config, client, message_object, thread_id, thread_type):
    try:
        target_name = get_user_name_by_id(client, target_author_id)
        target_bot = None
        for bot in config.get("data", []):
            if str(bot.get("author_id")) == str(target_author_id):
                target_bot = bot
                break
        if not target_bot:
            return send_message(client, message_object, thread_id, thread_type,
                               f"🚦 Bot của {target_name} không tồn tại!")
        target_bot["status"] = False
        save_config(config)
        send_message(client, message_object, thread_id, thread_type,
                     f"🚦• Bot của {target_name} đã hết thời gian hoạt động và đã bị tắt!")
    except Exception as e:
        logging.error(f"• Đã xảy ra lỗi khi tắt bot: {str(e)}")

def handle_rs_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        config = load_config()
        source_name = get_user_name_by_id(client, author_id)
        source_bot = None
        for bot in config.get("data", []):
            if str(bot.get("author_id")) == str(author_id):
                source_bot = bot
                break
        source_name = source_bot["username"] if source_bot else source_name
        if not source_bot:
            return send_message(client, message_object, thread_id, thread_type,
                               f"🚦 {source_name}, bạn không có bot!")
        if not source_bot.get("is_main_bot", False):
            return send_message(client, message_object, thread_id, thread_type,
                               f"❌ {source_name}, chỉ admin bot chính mới có thể sử dụng lệnh này!")
        
        vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        now = datetime.now(vietnam_tz)
        source_bot["last_reset"] = now.strftime('%H:%M:%S %d/%m/%Y')
        source_bot["status"] = True
        save_config(config)

        send_message(client, message_object, thread_id, thread_type,
                     f"🚦BOT {source_name} Tiến Hành Khởi Động Lại Toàn Bộ Hệ Thống")

        os.execl(sys.executable, sys.executable, *sys.argv)
    except Exception as e:
        source_name = get_user_name_by_id(client, author_id)
        send_message(client, message_object, thread_id, thread_type,
                     f"🚦 {source_name}, lỗi xảy ra khi reset hệ thống: {str(e)}")

def handle_create_command(message, message_object, thread_id, thread_type, author_id, client):
    def create_bot_entry():
        try:
            config = load_config()
            source_name = get_user_name_by_id(client, author_id)
            source_bot = None
            for bot in config.get("data", []):
                if str(bot.get("author_id")) == str(author_id):
                    source_bot = bot
                    break
            source_name = source_bot["username"] if source_bot else source_name
            if thread_type != ThreadType.USER:
                cookie = """{"_ga": "GA1.2.103..."}"""
                return send_message(client, message_object, thread_id, thread_type,
                    f"🚦 {source_name}, lệnh này chỉ hoạt động với USER cá nhân inbox riêng, không hoạt động trong GROUP 🤧\n"
                    f"🚦 Kết bạn với chủ Bot và gõ lệnh theo cú pháp {client.prefix}mybot create [prefix] [imei] [cookies] để tạo Bot \n")

            pattern = r"\[(.*?)\]\s*\[(.*?)\]\s*\[(.*?)\]"
            match = re.search(pattern, message)
            if not match or len(match.groups()) < 3:
                cookies = """{"_ga": "GA1.2.103..."}"""
                return send_message(client, message_object, thread_id, thread_type,
                    f"🚦 {source_name}, vui lòng cung cấp đủ thông số theo cú pháp {client.prefix}mybot create [prefix] [imei] [cookies] để tạo Bot 🤖\n"
                    f"🚦 Kí tự: Các thông số imei và cookies JSON phải để trong ngoặc [], nếu không dùng prefix thì nhập prefix là None 📌\n"
                    f"🚦 Ví dụ: {client.prefix}mybot create [{client.prefix}] [ff33af5c-fb...] [{cookies}] ✅\n")

            PREFIX, imei, raw_cookies = match.groups()
            if PREFIX.lower() == "none":
                PREFIX = ""
            raw_cookies = ''.join(c for c in raw_cookies if c.isprintable() and c not in '\n\r\t')
            cookies = None if not raw_cookies else json.loads(raw_cookies) if raw_cookies.startswith('{') and raw_cookies.endswith('}') else None
            if cookies is None and raw_cookies:
                return send_message(client, message_object, thread_id, thread_type,
                    f"🚦 {source_name}, cookies không hợp lệ! Phải là một đối tượng JSON hoàn chỉnh, ví dụ: {{\"_ga\": \"GA1.2.103...\"}}")
            if not isinstance(cookies, dict) and cookies is not None:
                return send_message(client, message_object, thread_id, thread_type,
                    f"🚦 {source_name}, cookies không hợp lệ! Phải là một đối tượng JSON (dạng từ điển). Ví dụ: {{\"key\": \"value\"}}")
            if not imei.strip():
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, IMEI không hợp lệ!")
            if config is None:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, không thể tải cấu hình!")
            if source_bot:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, bot của bạn đã tồn tại, không thể tạo thêm!")
            vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
            now = datetime.now(vietnam_tz)
            config["data"].append({
                "prefix": PREFIX,
                "session_cookies": cookies,
                "imei": imei,
                "is_main_bot": False,
                "username": source_name,
                "author_id": author_id,
                "status": False,
                "kich_hoat": now.strftime('%d/%m/%Y'),
                "het_han": (now + timedelta(days=1)).strftime('%d/%m/%Y')
            })
            save_config(config)
            send_message(client, message_object, thread_id, thread_type, f"🚦 Bot của {source_name} đã được tạo thành công và đang trong trạng thái chờ duyệt!")
        except Exception as e:
            source_name = get_user_name_by_id(client, author_id)
            send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, đã xảy ra lỗi: {str(e)}")

    threading.Thread(target=create_bot_entry, daemon=True).start()

def handle_lock_command(message, message_object, thread_id, thread_type, author_id, client):
    def lock_bot_entry():
        try:
            config = load_config()
            source_name = get_user_name_by_id(client, author_id)
            source_bot = None
            for bot in config.get("data", []):
                if str(bot.get("author_id")) == str(author_id):
                    source_bot = bot
                    break
            source_name = source_bot["username"] if source_bot else source_name
            if not source_bot:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, bạn không có bot!")
            if not source_bot.get("is_main_bot", False):
                return send_message(client, message_object, thread_id, thread_type,
                                   f"❌ {source_name}, chỉ admin bot chính mới có thể sử dụng lệnh này!")
            parts = message.split()
            if len(parts) < 3:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, cú pháp sai! Vui lòng nhập: {client.prefix}mybot lock [index]")
            try:
                index = int(parts[2]) - 1
                bots = [bot for bot in config.get("data", []) if not bot.get("is_main_bot", False)]
                if index < 0 or index >= len(bots):
                    return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, số thứ tự không hợp lệ!")
                target_bot = bots[index]
                target_name = target_bot["username"]
                target_bot["status"] = False
                save_config(config)
                send_message(client, message_object, thread_id, thread_type,
                             f"🚦Đã Khóa Bot ( {target_name})")
                os.execl(sys.executable, sys.executable, *sys.argv)
            except ValueError:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, số thứ tự không hợp lệ!")
        except Exception as e:
            source_name = get_user_name_by_id(client, author_id)
            send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, đã xảy ra lỗi: {str(e)}")

    threading.Thread(target=lock_bot_entry, daemon=True).start()

def handle_unlock_command(message, message_object, thread_id, thread_type, author_id, client):
    def unlock_bot_entry():
        try:
            config = load_config()
            source_name = get_user_name_by_id(client, author_id)
            source_bot = None
            for bot in config.get("data", []):
                if str(bot.get("author_id")) == str(author_id):
                    source_bot = bot
                    break
            source_name = source_bot["username"] if source_bot else source_name
            if not source_bot:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, bạn không có bot!")
            if not source_bot.get("is_main_bot", False):
                return send_message(client, message_object, thread_id, thread_type,
                                   f"❌ {source_name}, chỉ admin bot chính mới có thể sử dụng lệnh này!")
            parts = message.split()
            if len(parts) < 3:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, cú pháp sai! Vui lòng nhập: {client.prefix}mybot unlock [index]")
            try:
                index = int(parts[2]) - 1
                bots = [bot for bot in config.get("data", []) if not bot.get("is_main_bot", False)]
                if index < 0 or index >= len(bots):
                    return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, số thứ tự không hợp lệ!")
                target_bot = bots[index]
                target_name = target_bot["username"]
                vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
                now = datetime.now(vietnam_tz)
                het_han = datetime.strptime(target_bot.get("het_han", now.strftime("%d/%m/%Y")), "%d/%m/%Y").replace(tzinfo=vietnam_tz)
                if now > het_han:
                    return send_message(client, message_object, thread_id, thread_type, f"🚦 Bot của {target_name} đã hết hạn, liên hệ ngbao để gia hạn! 😎")
                target_bot["status"] = True
                save_config(config)
                send_message(client, message_object, thread_id, thread_type,
                             f"🚦Đã Mở Khóa Bot ( {target_name})")
                os.execl(sys.executable, sys.executable, *sys.argv)
            except ValueError:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, số thứ tự không hợp lệ!")
        except Exception as e:
            source_name = get_user_name_by_id(client, author_id)
            send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, đã xảy ra lỗi: {str(e)}")

    threading.Thread(target=unlock_bot_entry, daemon=True).start()

def handle_lockall_command(message, message_object, thread_id, thread_type, author_id, client):
    def lockall_bot_entry():
        try:
            config = load_config()
            source_name = get_user_name_by_id(client, author_id)
            source_bot = None
            for bot in config.get("data", []):
                if str(bot.get("author_id")) == str(author_id):
                    source_bot = bot
                    break
            source_name = source_bot["username"] if source_bot else source_name
            if not source_bot:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, bạn không có bot!")
            if not source_bot.get("is_main_bot", False):
                return send_message(client, message_object, thread_id, thread_type, f"❌ {source_name}, bạn không phải admin bot chính!")
            for bot in config.get("data", []):
                if not bot.get("is_main_bot", False):
                    bot["status"] = False
            save_config(config)
            send_message(client, message_object, thread_id, thread_type, "🚦Tiến Hành Khóa Toàn Bộ Bot")
            os.execl(sys.executable, sys.executable, *sys.argv)
        except Exception as e:
            source_name = get_user_name_by_id(client, author_id)
            send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, đã xảy ra lỗi: {str(e)}")

    threading.Thread(target=lockall_bot_entry, daemon=True).start()

def handle_unlockall_command(message, message_object, thread_id, thread_type, author_id, client):
    def unlockall_bot_entry():
        try:
            config = load_config()
            source_name = get_user_name_by_id(client, author_id)
            source_bot = None
            for bot in config.get("data", []):
                if str(bot.get("author_id")) == str(author_id):
                    source_bot = bot
                    break
            source_name = source_bot["username"] if source_bot else source_name
            if not source_bot:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, bạn không có bot!")
            if not source_bot.get("is_main_bot", False):
                return send_message(client, message_object, thread_id, thread_type, f"❌ {source_name}, bạn không phải admin bot chính!")
            vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
            now = datetime.now(vietnam_tz)
            for bot in config.get("data", []):
                if not bot.get("is_main_bot", False):
                    het_han = datetime.strptime(bot.get("het_han", now.strftime("%d/%m/%Y")), "%d/%m/%Y").replace(tzinfo=vietnam_tz)
                    if now <= het_han:
                        bot["status"] = True
            save_config(config)
            send_message(client, message_object, thread_id, thread_type, "🚦Tiến Hành Khởi Chạy Toàn Bộ Bot")
            os.execl(sys.executable, sys.executable, *sys.argv)
        except Exception as e:
            source_name = get_user_name_by_id(client, author_id)
            send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, đã xảy ra lỗi: {str(e)}")

    threading.Thread(target=unlockall_bot_entry, daemon=True).start()

def handle_list_bots_command(message, message_object, thread_id, thread_type, author_id, client):
    def list_bots():
        try:
            config = load_config()
            source_name = get_user_name_by_id(client, author_id)
            source_bot = None
            for bot in config.get("data", []):
                if str(bot.get("author_id")) == str(author_id):
                    source_bot = bot
                    break
            source_name = source_bot["username"] if source_bot else source_name
            if not source_bot:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, bạn không có bot!")
            if config is None:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, không thể tải cấu hình!")
            
            bots = [bot for bot in config.get("data", []) if not bot.get("is_main_bot", False)]
            message_text = f"📋 DANH SÁCH TẤT CẢ BOT ({len(bots)})\n\n"
            vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
            now = datetime.now(vietnam_tz)
            
            for idx, bot in enumerate(bots, start=1):
                bot_name = bot["username"]
                bot_id = bot["author_id"]
                kich_hoat = bot.get("kich_hoat", "N/A")
                het_han = bot.get("het_han", "N/A")
                status = "✅ running" if bot.get("status", False) else "⏹️ stopped"
                prefix = bot.get("prefix", "Không có prefix")
                
                try:
                    kich_hoat_date = datetime.strptime(kich_hoat, '%d/%m/%Y').replace(tzinfo=vietnam_tz).strftime('%d/%m/%Y') if kich_hoat != "N/A" else "N/A"
                except ValueError:
                    kich_hoat_date = "N/A"
                
                try:
                    het_han_date = datetime.strptime(het_han, '%d/%m/%Y').replace(tzinfo=vietnam_tz).strftime('%d/%m/%Y') if het_han != "N/A" else "N/A"
                except ValueError:
                    het_han_date = "N/A"
                
                try:
                    expires_datetime = datetime.strptime(het_han, '%d/%m/%Y').replace(tzinfo=vietnam_tz)
                    remaining = expires_datetime - now
                    if remaining.total_seconds() > 0:
                        days = remaining.days
                        hours = remaining.seconds // 3600
                        minutes = (remaining.seconds % 3600) // 60
                        remaining_time = f"{days} ngày {hours} giờ {minutes} phút"
                    else:
                        remaining_time = "Hết hạn"
                except ValueError:
                    remaining_time = "Không xác định"
                
                bot_entry = (
                    f"{idx}. 🤖 {bot_name}\n"
                    f"   👤 Người tạo: {bot_name}\n"
                    f"   🆔 Bot ID: {bot_id}\n"
                    f"   📅 Kích hoạt: {kich_hoat_date}\n"
                    f"   ⏰ Hết hạn: {het_han_date}\n"
                    f"   ⏳ Thời hạn: {remaining_time}\n"
                    f"   📊 Trạng thái: {status}\n"
                    f"   🚀 Prefix: {prefix}\n"
                )
                message_text += bot_entry + "\n"
            
            send_message(client, message_object, thread_id, thread_type, message_text.strip())
        except Exception as e:
            source_name = get_user_name_by_id(client, author_id)
            send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, đã xảy ra lỗi: {str(e)}")

    threading.Thread(target=list_bots, daemon=True).start()

def handle_del_command(message, message_object, thread_id, thread_type, author_id, client):
    def delete_user_data():
        try:
            config = load_config()
            source_name = get_user_name_by_id(client, author_id)
            source_bot = None
            for bot in config.get("data", []):
                if str(bot.get("author_id")) == str(author_id):
                    source_bot = bot
                    break
            source_name = source_bot["username"] if source_bot else source_name
            if not source_bot:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, bạn không có bot!")
            if not source_bot.get("is_main_bot", False):
                return send_message(client, message_object, thread_id, thread_type, f"❌ {source_name}, chỉ admin bot chính mới có thể sử dụng lệnh này!")
            parts = message.split()
            if len(parts) < 3:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, cú pháp sai! Vui lòng nhập: {client.prefix}mybot del [index]")
            try:
                index = int(parts[2]) - 1
                bots = [bot for bot in config.get("data", []) if not bot.get("is_main_bot", False)]
                if index < 0 or index >= len(bots):
                    return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, số thứ tự không hợp lệ!")
                target_bot = bots[index]
                target_name = target_bot["username"]
                config["data"] = [bot for bot in config.get("data", []) if str(bot["author_id"]) != str(target_bot["author_id"])]
                save_config(config)
                send_message(client, message_object, thread_id, thread_type, f"🚦Đã Xóa Bot ( {target_name})")
                os.execl(sys.executable, sys.executable, *sys.argv)
            except ValueError:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, số thứ tự không hợp lệ!")
        except Exception as e:
            source_name = get_user_name_by_id(client, author_id)
            send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, đã xảy ra lỗi: {str(e)}")

    threading.Thread(target=delete_user_data, daemon=True).start()

def handle_change_prefix_command(message, message_object, thread_id, thread_type, author_id, client):
    def change_prefix():
        try:
            config = load_config()
            source_name = get_user_name_by_id(client, author_id)
            source_bot = None
            for bot in config.get("data", []):
                if str(bot.get("author_id")) == str(author_id):
                    source_bot = bot
                    break
            source_name = source_bot["username"] if source_bot else source_name
            if not source_bot:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, bạn không có bot!")
            if not is_bot_active(author_id, client):
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, bot của bạn đang bị khóa, không thể thay đổi prefix!")
            parts = message.split(maxsplit=2)
            if len(parts) < 3:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, cú pháp sai! Vui lòng nhập đúng: {client.prefix}mybot prefix [new_prefix]")
            new_prefix = parts[2].strip()
            if new_prefix.lower() == "none":
                new_prefix = ""
            if config is None:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, không thể tải cấu hình!")
            source_bot["prefix"] = new_prefix
            save_config(config)
            send_message(client, message_object, thread_id, thread_type, f"🚦 Prefix của bot {source_name} đã được đổi thành: {new_prefix if new_prefix else 'Không có prefix'}")
        except Exception as e:
            source_name = get_user_name_by_id(client, author_id)
            send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, đã xảy ra lỗi: {str(e)}")

    threading.Thread(target=change_prefix, daemon=True).start()

def handle_active_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        config = load_config()
        source_name = get_user_name_by_id(client, author_id)
        source_bot = None
        for bot in config.get("data", []):
            if str(bot.get("author_id")) == str(author_id):
                source_bot = bot
                break
        source_name = source_bot["username"] if source_bot else source_name
        if not source_bot:
            return send_message(client, message_object, thread_id, thread_type,
                               f"🚦 {source_name}, bạn không có bot!")
        if not source_bot.get("is_main_bot", False):
            return send_message(client, message_object, thread_id, thread_type,
                               f"❌ {source_name}, bạn không phải admin bot chính!")
        parts = message.split()
        if len(parts) < 4:
            return send_message(client, message_object, thread_id, thread_type,
                               f"🚦 {source_name}, cú pháp sai! Vui lòng nhập đúng: {client.prefix}mybot active [index] [thời gian]\n"
                               f"📖 Định dạng: `1d`, `5h`, `30m`, `1d 5h 30m`\n"
                               f"💞 Ví dụ: {client.prefix}mybot active 1 1d")
        try:
            index = int(parts[2]) - 1
            bots = [bot for bot in config.get("data", []) if not bot.get("is_main_bot", False)]
            if index < 0 or index >= len(bots):
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, số thứ tự không hợp lệ!")
            duration_str = parts[3]
            duration_seconds = parse_time_duration(duration_str)
            if duration_seconds is None:
                return send_message(client, message_object, thread_id, thread_type,
                                   f"🚦 {source_name}, thời gian không hợp lệ! Định dạng: `1d`, `5h`, `30m`, `1d 5h 30m`")
            vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
            now = datetime.now(vietnam_tz)
            target_bot = bots[index]
            target_name = target_bot["username"]
            activation_date = now.strftime('%d/%m/%Y')
            expiration_timestamp = now + timedelta(seconds=duration_seconds)
            expiration_date = expiration_timestamp.strftime('%d/%m/%Y')
            target_bot["kich_hoat"] = activation_date
            target_bot["het_han"] = expiration_date
            target_bot["status"] = True
            save_config(config)
            remaining = expiration_timestamp - now
            days = remaining.days
            hours = remaining.seconds // 3600
            minutes = (remaining.seconds % 3600) // 60
            send_message(client, message_object, thread_id, thread_type,
                         f"🚦• Bot của {target_name} đang kích hoạt bởi {source_name}")
            send_message(client, message_object, thread_id, thread_type,
                         f"🚦• Bot của {target_name} đã được kích hoạt thành công bởi {source_name} vào ngày {activation_date} "
                         f"với thời gian còn lại: {days} ngày {hours} giờ {minutes} phút\n"
                         f"Bot sẽ tự động ngừng vào ngày {expiration_date}!")
            timer = threading.Timer(duration_seconds, deactivate_bot,
                                   args=(target_bot["author_id"], config, client, message_object, thread_id, thread_type))
            timer.start()
        except ValueError:
            return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, số thứ tự không hợp lệ!")
        except Exception as e:
            send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, đã xảy ra lỗi: {str(e)}")
    except Exception as e:
        source_name = get_user_name_by_id(client, author_id)
        send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, đã xảy ra lỗi: {str(e)}")

def handle_bot_info_command(message, message_object, thread_id, thread_type, author_id, client):
    def get_bot_info():
        try:
            config = load_config()
            source_name = get_user_name_by_id(client, author_id)
            source_bot = None
            for bot in config.get("data", []):
                if str(bot.get("author_id")) == str(author_id):
                    source_bot = bot
                    break
            source_name = source_bot["username"] if source_bot else source_name
            if not source_bot:
                return send_message(client, message_object, thread_id, thread_type,
                                   f"🚦 {source_name}, bạn không có bot!")
            if not is_bot_active(author_id, client):
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, bot của bạn đang bị khóa, không thể xem thông tin!")
            parts = message.split()
            target_bot = source_bot
            target_name = source_name
            if len(parts) >= 3:
                if not source_bot.get("is_main_bot", False):
                    return send_message(client, message_object, thread_id, thread_type,
                                       f"❌ {source_name}, chỉ admin bot chính mới có thể xem thông tin bot khác!")
                try:
                    index = int(parts[2]) - 1
                    bots = [bot for bot in config.get("data", []) if not bot.get("is_main_bot", False)]
                    if index < 0 or index >= len(bots):
                        return send_message(client, message_object, thread_id, thread_type,
                                           f"🚦 {source_name}, số thứ tự không hợp lệ!")
                    target_bot = bots[index]
                    target_name = target_bot["username"]
                except ValueError:
                    return send_message(client, message_object, thread_id, thread_type,
                                       f"🚦 {source_name}, số thứ tự không hợp lệ!")
            if target_bot.get("is_main_bot", False) and len(parts) < 3:
                bot_id = f"🆔 ID: {target_bot.get('author_id')}"
                bot_name = f"🤖 Bot: {target_name}"
                prefix = target_bot.get("prefix", "Không có prefix")
                status = "✅ Đang hoạt động" if target_bot.get("status", False) else "❌ Tạm Dừng"
                settings = read_settings(client.uid)
                allowed_thread_ids = settings.get("allowed_thread_ids", [])
                message_parts = [
                    f"{bot_name}",
                    f"{bot_id}",
                    f"📶 Tình trạng: {status}",
                    f"➡️ Prefix: {prefix}",
                    f"🌀 Nhóm setbox: {allowed_thread_ids if allowed_thread_ids else 'Chưa thiết lập'}"
                ]
                message_text = "\n".join(message_parts)
                send_message(client, message_object, thread_id, thread_type, message_text)
            else:
                bot_id = f"🆔 ID: {target_bot.get('author_id')}"
                bot_name = f"🤖 Bot {target_name}"
                prefix = target_bot.get("prefix", "Không có prefix")
                status = "✅ Đang hoạt động" if target_bot.get("status", False) else "❌ Tạm Dừng"
                kich_hoat = target_bot.get("kich_hoat", "N/A")
                het_han = target_bot.get("het_han", "N/A")
                vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
                now = datetime.now(vietnam_tz)
                try:
                    kich_hoat_date = datetime.strptime(kich_hoat, '%d/%m/%Y').replace(tzinfo=vietnam_tz).strftime('%d/%m/%Y') if kich_hoat != "N/A" else "N/A"
                except ValueError:
                    kich_hoat_date = "N/A"
                try:
                    het_han_date = datetime.strptime(het_han, '%d/%m/%Y').replace(tzinfo=vietnam_tz).strftime('%d/%m/%Y') if het_han != "N/A" else "N/A"
                except ValueError:
                    het_han_date = "N/A"
                try:
                    expires_datetime = datetime.strptime(het_han, '%d/%m/%Y').replace(tzinfo=vietnam_tz)
                    remaining = expires_datetime - now
                    if remaining.total_seconds() > 0:
                        days = remaining.days
                        hours = remaining.seconds // 3600
                        minutes = (remaining.seconds % 3600) // 60
                        remaining_time = f"{days} ngày {hours} giờ {minutes} phút"
                    else:
                        remaining_time = "Hết hạn"
                except ValueError:
                    remaining_time = "Không xác định"
                settings = read_settings(client.uid)
                allowed_thread_ids = settings.get("allowed_thread_ids", [])
                message_parts = [
                    f"{bot_name}",
                    f"{bot_id}",
                    f"📶 Tình trạng: {status}",
                    f"📅 Kích hoạt: {kich_hoat_date}",
                    f"⏰ Hết hạn: {het_han_date}",
                    f"⏳ Thời hạn: {remaining_time}",
                    f"➡️ Prefix: {prefix}",
                    f"🌀 Group quản lý: {allowed_thread_ids if allowed_thread_ids else 'Chưa thiết lập'}"
                ]
                message_text = "\n".join(message_parts)
                send_message(client, message_object, thread_id, thread_type, message_text)
        except Exception as e:
            source_name = get_user_name_by_id(client, author_id)
            send_message(client, message_object, thread_id, thread_type,
                         f"🚦 {source_name}, đã xảy ra lỗi: {str(e)}")
    threading.Thread(target=get_bot_info, daemon=True).start()

def handle_detail_command(message, message_object, thread_id, thread_type, author_id, client):
    def get_bot_detail():
        try:
            config = load_config()
            source_name = get_user_name_by_id(client, author_id)
            source_bot = None
            for bot in config.get("data", []):
                if str(bot.get("author_id")) == str(author_id):
                    source_bot = bot
                    break
            source_name = source_bot["username"] if source_bot else source_name
            if not source_bot:
                return send_message(client, message_object, thread_id, thread_type,
                                   f"🚦 {source_name}, bạn không có bot!")
            if not is_bot_active(author_id, client):
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, bot của bạn đang bị khóa, không thể xem chi tiết!")
            parts = message.split()
            target_bot = source_bot
            target_name = source_name
            if len(parts) >= 3:
                if not source_bot.get("is_main_bot", False):
                    return send_message(client, message_object, thread_id, thread_type,
                                       f"❌ {source_name}, chỉ admin bot chính mới có thể xem chi tiết bot khác!")
                try:
                    index = int(parts[2]) - 1
                    bots = [bot for bot in config.get("data", []) if not bot.get("is_main_bot", False)]
                    if index < 0 or index >= len(bots):
                        return send_message(client, message_object, thread_id, thread_type,
                                           f"🚦 {source_name}, số thứ tự không hợp lệ!")
                    target_bot = bots[index]
                    target_name = target_bot["username"]
                except ValueError:
                    return send_message(client, message_object, thread_id, thread_type,
                                       f"🚦 {source_name}, số thứ tự không hợp lệ!")
            if target_bot.get("is_main_bot", False) and len(parts) < 3:
                bot_id = f"🆔 {target_bot.get('author_id')}"
                bot_name = f"📱 {target_name}"
                prefix = target_bot.get("prefix", "Không có prefix")
                status = "✅ Đang hoạt động" if target_bot.get("status", False) else "❌ Tạm Dừng"
                settings = read_settings(client.uid)
                allowed_thread_ids = settings.get("allowed_thread_ids", [])
                current_time = datetime.now(pytz.timezone('Asia/Ho_Chi_Minh')).strftime('%H:%M:%S %d/%m/%Y')
                message_text = (
                    f"📌 THÔNG TIN CHI TIẾT BOT 📌\n\n"
                    f"{bot_id}\n"
                    f"{bot_name}\n"
                    f"🟢 Trạng thái: {status}\n"
                    f"➡️ Prefix: {prefix}\n"
                    f"🌀 Nhóm setbox: {allowed_thread_ids if allowed_thread_ids else 'Chưa thiết lập'}\n\n"
                    f"📊 THÔNG TIN ĐĂNG KÝ\n"
                    f"📅 Ngày tạo: {target_bot.get('kich_hoat', 'N/A')}\n"
                    f"👤 Người tạo: {target_name}\n"
                    f"✅ Thời gian xem xét gần nhất: {current_time}\n"
                    f"👮 Được phê duyệt bởi: ngbao\n\n"
                    f"• Cập nhật cuối: {current_time}"
                )
                send_message(client, message_object, thread_id, thread_type, message_text)
            else:
                bot_id = f"🆔 {target_bot.get('author_id')}"
                bot_name = f"📱{target_name}"
                status = "✅ Đang hoạt động" if target_bot.get("status", False) else "❌ Tạm Dừng"
                kich_hoat = target_bot.get("kich_hoat", "N/A")
                het_han = target_bot.get("het_han", "N/A")
                vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
                now = datetime.now(vietnam_tz)
                try:
                    kich_hoat_date = datetime.strptime(kich_hoat, '%d/%m/%Y').replace(tzinfo=vietnam_tz).strftime('%d/%m/%Y') if kich_hoat != "N/A" else "N/A"
                except ValueError:
                    kich_hoat_date = "N/A"
                try:
                    het_han_date = datetime.strptime(het_han, '%d/%m/%Y').replace(tzinfo=vietnam_tz).strftime('%d/%m/%Y') if het_han != "N/A" else "N/A"
                except ValueError:
                    het_han_date = "N/A"
                current_time = now.strftime('%H:%M:%S %d/%m/%Y')
                message_text = (
                    f"📌 THÔNG TIN CHI TIẾT BOT 📌\n\n"
                    f"{bot_id}\n"
                    f"{bot_name}\n"
                    f"🟢 Trạng thái: {status}\n"
                    f"🗄️ Database: {target_bot.get('author_id')}\n"
                    f"🔄 Đang chạy: {kich_hoat_date} - {het_han_date}\n"
                    f"📊 THÔNG TIN ĐĂNG KÝ\n"
                    f"📅 Ngày tạo: {kich_hoat_date}\n"
                    f"👤 Người tạo: {target_name}\n"
                    f"✅ Thời gian xem xét gần nhất: {current_time}\n"
                    f"👮 Được phê duyệt bởi: ngbao\n\n"
                    f"• Cập nhật cuối: {current_time}"
                )
                send_message(client, message_object, thread_id, thread_type, message_text)
        except Exception as e:
            source_name = get_user_name_by_id(client, author_id)
            send_message(client, message_object, thread_id, thread_type,
                         f"🚦 {source_name}, đã xảy ra lỗi: {str(e)}")
    threading.Thread(target=get_bot_detail, daemon=True).start()

def handle_manager_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        config = load_config()
        source_name = get_user_name_by_id(client, author_id)
        source_bot = None
        for bot in config.get("data", []):
            if str(bot.get("author_id")) == str(author_id):
                source_bot = bot
                break
        source_name = source_bot["username"] if source_bot else source_name
        if not source_bot:
            return send_message(client, message_object, thread_id, thread_type,
                               f"🚦 {source_name}, bạn không có bot!")
        if not source_bot.get("is_main_bot", False):
            return send_message(client, message_object, thread_id, thread_type,
                               f"❌ Chỉ Dành Cho Quản Trị Viên Bot")
        message_text = (
            f"👮 LỆNH QUẢN TRỊ BOT 👮\n\n"
            f"1️⃣ Quản lý danh sách (OA)\n"
            f"『{client.prefix}mybot list』 - Xem danh sách tất cả bot\n"
            f"『{client.prefix}mybot cmd』 - Load tất cả các lệnh có bao nhiêu lệnh\n\n"
            f"➤ Quản lý bot cụ thể:\n"
            f"『{client.prefix}mybot detail [index]』 - Xem thông tin chi tiết bot theo số thứ tự\n"
            f"『{client.prefix}mybot info [index]』 - Xem thông tin cơ bản bot theo số thứ tự\n"
            f"『{client.prefix}mybot active [index] [thời gian]』 - Kích hoạt bot theo số thứ tự\n"
            f"『{client.prefix}mybot lock [index]』 - Tắt bot theo số thứ tự\n"
            f"『{client.prefix}mybot unlock [index]』 - Mở khóa bot theo số thứ tự\n\n"
            f"2️⃣ Quản lí Mở/Khóa Bot (OA) \n"
            f"『{client.prefix}mybot unlockall』 - Khởi chạy tất cả bot\n"
            f"『{client.prefix}mybot lockall』 - Tắt tất cả bot\n\n"
            f"📝 Lưu ý về thời hạn:\n"
            f"• Định dạng: số + đơn vị\n"
            f"• Đơn vị: m (phút), h (giờ), d (ngày)\n"
            f"• Ví dụ: 15m, 24h, 7d, all (vô thời hạn)"
        )
        send_message(client, message_object, thread_id, thread_type, message_text)
    except Exception as e:
        source_name = get_user_name_by_id(client, author_id)
        send_message(client, message_object, thread_id, thread_type,
                     f"🚦 {source_name}, đã xảy ra lỗi: {str(e)}")

def handle_share_command(message, message_object, thread_id, thread_type, author_id, client):
    def share_time():
        try:
            config = load_config()
            source_name = get_user_name_by_id(client, author_id)
            source_bot = None
            for bot in config.get("data", []):
                if str(bot.get("author_id")) == str(author_id):
                    source_bot = bot
                    break
            source_name = source_bot["username"] if source_bot else source_name
            if not source_bot:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, bạn không có bot!")
            if not source_bot.get("is_main_bot", False):
                return send_message(client, message_object, thread_id, thread_type, f"❌ {source_name}, bạn không phải admin bot chính!")
            if thread_type != ThreadType.GROUP:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, lệnh này không thể sử dụng trong tin nhắn riêng!")
            parts = message.split()
            if len(parts) < 4:
                return send_message(client, message_object, thread_id, thread_type,
                                   f"🚦 {source_name}, vui lòng nhập đúng cú pháp: {client.prefix}mybot share [index] [thời gian]\n"
                                   f"📖 Định dạng: `1d`, `5h`, `30m`, `1d 5h 30m`, `all`\n"
                                   f"💞 Ví dụ: {client.prefix}mybot share 1 1d")
            try:
                index = int(parts[2]) - 1
                duration_str = parts[3]
                bots = [bot for bot in config.get("data", []) if not bot.get("is_main_bot", False)]
                if index < 0 or index >= len(bots):
                    return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, số thứ tự không hợp lệ!")
                duration_seconds = parse_time_duration(duration_str)
                if duration_seconds is None:
                    return send_message(client, message_object, thread_id, thread_type,
                                       f"🚦 {source_name}, thời gian không hợp lệ! Định dạng: `1d`, `5h`, `30m`, `1d 5h 30m`, hoặc `all`")
                vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
                now = datetime.now(vietnam_tz)
                target_bot = bots[index]
                target_name = target_bot["username"]
                source_expiration = datetime.strptime(source_bot.get("het_han", now.strftime("%d/%m/%Y")), "%d/%m/%Y").replace(tzinfo=vietnam_tz)
                remaining_seconds = (source_expiration - now).total_seconds()
                if remaining_seconds <= 0:
                    return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, bot của bạn đã hết hạn, không thể chia sẻ!")
                if duration_seconds == "all":
                    duration_seconds = remaining_seconds
                if duration_seconds > remaining_seconds:
                    return send_message(client, message_object, thread_id, thread_type,
                                       f"🚦 {source_name}, thời gian chia sẻ vượt quá thời gian còn lại của bot!")
                source_new_expiration = source_expiration - timedelta(seconds=duration_seconds)
                target_expiration = datetime.strptime(target_bot.get("het_han", now.strftime("%d/%m/%Y")), "%d/%m/%Y").replace(tzinfo=vietnam_tz)
                target_new_expiration = max(target_expiration, now) + timedelta(seconds=duration_seconds)
                source_bot["het_han"] = source_new_expiration.strftime("%d/%m/%Y")
                target_bot["het_han"] = target_new_expiration.strftime("%d/%m/%Y")
                target_bot["status"] = True
                save_config(config)
                source_remaining = source_new_expiration - now
                source_days = source_remaining.days
                source_hours = source_remaining.seconds // 3600
                source_minutes = (source_remaining.seconds % 3600) // 60
                target_remaining = target_new_expiration - now
                target_days = target_remaining.days
                target_hours = target_remaining.seconds // 3600
                target_minutes = (target_remaining.seconds % 3600) // 60
                send_message(client, message_object, thread_id, thread_type,
                             f"🔄 Giao dịch thành công ✅\n\n"
                             f"📤 {source_name}\n"
                             f"\t『Bot Name: {source_name}\n"
                             f"\t➜⌛ Còn lại: {source_days} ngày {source_hours} giờ {source_minutes} phút\n"
                             f"———————————————————\n"
                             f"📥 {target_name}\n"
                             f"\t『Bot Name: {target_name}\n"
                             f"\t➜⌛ Hiện tại: {target_days} ngày {target_hours} giờ {target_minutes} phút")
            except ValueError:
                return send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, số thứ tự không hợp lệ!")
            except Exception as e:
                send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, đã xảy ra lỗi: {str(e)}")
        except Exception as e:
            source_name = get_user_name_by_id(client, author_id)
            send_message(client, message_object, thread_id, thread_type, f"🚦 {source_name}, đã xảy ra lỗi: {str(e)}")

    threading.Thread(target=share_time, daemon=True).start()

def handle_update_command(message, message_object, thread_id, thread_type, author_id, client):
    def update_bot_entry():
        try:
            config = load_config()
            source_name = get_user_name_by_id(client, author_id)
            source_bot = None
            for bot in config.get("data", []):
                if str(bot.get("author_id")) == str(author_id):
                    source_bot = bot
                    break
            source_name = source_bot["username"] if source_bot else source_name
            if not source_bot:
                return send_message(client, message_object, thread_id, thread_type,
                                   f"🚦 {source_name}, bạn không có bot để cập nhật!")
            if thread_type != ThreadType.USER:
                return send_message(client, message_object, thread_id, thread_type,
                                   f"🚦 {source_name}, lệnh này chỉ hoạt động với USER cá nhân inbox riêng, không hoạt động trong GROUP 🤧\n"
                                   f"🚦 Gõ lệnh theo cú pháp {client.prefix}mybot update [imei] [cookies JSON] để cập nhật Bot 🤖\n")
            pattern = r"\[(.*?)\]\s*\[(.*?)\]"
            match = re.search(pattern, message)
            if not match or len(match.groups()) < 2:
                return send_message(client, message_object, thread_id, thread_type,
                                   f"🚦 {source_name}, vui lòng cung cấp đủ thông số theo cú pháp {client.prefix}mybot update [imei] [cookies JSON] để cập nhật Bot 🤖\n"
                                   f"🚦 Kí tự: Các thông số imei và cookies JSON phải để trong ngoặc [] 📌\n"
                                   f"🚦 Ví dụ: {client.prefix}mybot update [ff33af5c-fb...] [{{\"_ga\": \"GA1.2.103\"}}] ✅")
            imei, raw_cookies = match.groups()
            raw_cookies = ''.join(c for c in raw_cookies if c.isprintable() and c not in '\n\r\t')
            cookies = None if not raw_cookies else json.loads(raw_cookies) if raw_cookies.startswith('{') and raw_cookies.endswith('}') else None
            if cookies is None and raw_cookies:
                return send_message(client, message_object, thread_id, thread_type,
                                   f"🚦 {source_name}, cookies không hợp lệ! Phải là một đối tượng JSON hoàn chỉnh, ví dụ: {{\"_ga\": \"GA1.2.103\"}}")
            if not isinstance(cookies, dict) and cookies is not None:
                return send_message(client, message_object, thread_id, thread_type,
                                   f"🚦 {source_name}, cookies không hợp lệ! Phải là một đối tượng JSON (dạng từ điển). Ví dụ: {{\"key\": \"value\"}}")
            if not imei.strip():
                return send_message(client, message_object, thread_id, thread_type,
                                   f"🚦 {source_name}, IMEI không hợp lệ!")
            source_bot["imei"] = imei
            source_bot["session_cookies"] = cookies
            save_config(config)
            send_message(client, message_object, thread_id, thread_type,
                         f"🚦 Bot của {source_name} đã được cập nhật thành công!\n"
                         f"『IMEI mới: {imei}\n"
                         f"『Cookies mới: {json.dumps(cookies) if cookies else 'Không có cookies'}")
        except Exception as e:
            source_name = get_user_name_by_id(client, author_id)
            send_message(client, message_object, thread_id, thread_type,
                         f"🚦 {source_name}, đã xảy ra lỗi khi cập nhật bot: {str(e)}")

    threading.Thread(target=update_bot_entry, daemon=True).start()

def handle_setbox_command(message, message_object, thread_id, thread_type, author_id, client):
    def set_box_entry():
        try:
            config = load_config()
            source_name = get_user_name_by_id(client, author_id)
            source_bot = None
            for bot in config.get("data", []):
                if str(bot.get("author_id")) == str(author_id):
                    source_bot = bot
                    break
            source_name = source_bot["username"] if source_bot else source_name
            if not source_bot:
                return send_message(client, message_object, thread_id, thread_type,
                                   f"『{source_name}, bạn không có bot để thiết lập box quản lý!")
            if not source_bot.get("is_main_bot", False):
                return send_message(client, message_object, thread_id, thread_type,
                                   f"❌ {source_name}, bạn không phải admin bot chính để sử dụng lệnh này!")
            if thread_type != ThreadType.GROUP:
                return send_message(client, message_object, thread_id, thread_type,
                                   f"『{source_name}, lệnh này chỉ hoạt động trong GROUP, không hoạt động trong tin nhắn riêng!")
            box_id = thread_id
            source_bot["box_id"] = box_id
            save_config(config)
            send_message(client, message_object, thread_id, thread_type,
                         f"『Đã Thiết Lập!\n"
                         f"『ID Box: {box_id}\n"
                         f"『Người thiết lập: {source_name}")
        except Exception as e:
            source_name = get_user_name_by_id(client, author_id)
            send_message(client, message_object, thread_id, thread_type,
                         f"『{source_name}, đã xảy ra lỗi khi thiết lập box quản lý: {str(e)}")

    threading.Thread(target=set_box_entry, daemon=True).start()

def handle_help_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        source_name = get_user_name_by_id(client, author_id)
        msg = (
            f"《 HỆ THỐNG QUẢN LÝ BOT 》\n\n"
            f"1️⃣ Lệnh Thành Viên:\n"
            f"『{client.prefix}mybot info』 - Xem thông tin bot của bạn\n"
            f"『{client.prefix}mybot detail』 - Xem thông tin chi tiết bot của bạn\n"
            f"『{client.prefix}mybot prefix [prefix]』 - Đổi prefix cho bot của bạn\n"
            f"『{client.prefix}mybot update [imei] [cookies]』 - Cập nhật IMEI và cookies (inbox riêng)\n"
            f"『{client.prefix}mybot share [index] [thời gian]』 - Chia sẻ thời gian sử dụng bot (trong group)\n"
            f"『{client.prefix}mybot list』 - Xem danh sách tất cả bot\n\n"
            f"2️⃣ Quản Trị Viên Bot \n"
            f"『{client.prefix}mybot manager』 - Xem danh sách lệnh quản lý (dành cho admin)\n"
            f"『{client.prefix}mybot rs』 - Reset toàn bộ hệ thống (admin)\n"
            f"『{client.prefix}mybot list』 - Xem danh sách tất cả bot (admin)\n"
        )
        send_message(client, message_object, thread_id, thread_type, msg)
    except Exception as e:
        source_name = get_user_name_by_id(client, author_id)
        send_message(client, message_object, thread_id, thread_type,
                     f"🚦 {source_name}, đã xảy ra lỗi: {str(e)}")

def handle_cmd_command(message, message_object, thread_id, thread_type, author_id, client):
    def load_commands():
        try:
            config = load_config()
            source_name = get_user_name_by_id(client, author_id)
            source_bot = None
            for bot in config.get("data", []):
                if str(bot.get("author_id")) == str(author_id):
                    source_bot = bot
                    break
            source_name = source_bot["username"] if source_bot else source_name

            if not source_bot:
                return send_message(client, message_object, thread_id, thread_type,
                                   f"🚦 {source_name}, bạn không có bot! Hãy tạo bot bằng `{client.prefix}mybot create`.")

            if not source_bot.get("is_main_bot", False):
                return send_message(client, message_object, thread_id, thread_type,
                                   f"❌ {source_name}, chỉ admin bot chính mới có thể sử dụng lệnh này!")

            command_list = [
                {"name": "info", "description": "Xem thông tin cơ bản của bot"},
                {"name": "detail", "description": "Xem thông tin chi tiết của bot"},
                {"name": "prefix", "description": "Đổi prefix của bot"},
                {"name": "update", "description": "Cập nhật IMEI và cookies (inbox riêng)"},
                {"name": "share", "description": "Chia sẻ thời gian sử dụng bot (trong group)"},
                {"name": "list", "description": "Liệt kê tất cả bot"},
                {"name": "lock", "description": "Khóa bot theo số thứ tự (admin)"},
                {"name": "unlock", "description": "Mở khóa bot theo số thứ tự (admin)"},
                {"name": "lockall", "description": "Khóa tất cả bot (admin)"},
                {"name": "unlockall", "description": "Mở khóa tất cả bot chưa hết hạn (admin)"},
                {"name": "active", "description": "Kích hoạt bot với thời gian cụ thể (admin)"},
                {"name": "del", "description": "Xóa bot theo số thứ tự (admin)"},
                {"name": "rs", "description": "Reset toàn bộ hệ thống (admin)"},
                {"name": "setbox", "description": "Thiết lập group quản lý (admin, trong group)"},
                {"name": "cmd", "description": "Liệt kê tất cả lệnh (admin)"},
                {"name": "manager", "description": "Xem danh sách lệnh quản lý (admin)"},
                {"name": "help", "description": "Xem hướng dẫn sử dụng các lệnh"}
            ]

            message_text = f"📋 DANH SÁCH LỆNH ({len(command_list)}) 📋\n\n"
            for idx, cmd in enumerate(command_list, start=1):
                message_text += f"{idx}. `{client.prefix}mybot {cmd['name']}` - {cmd['description']}\n"
            message_text += f"\n📝 Tổng số lệnh: {len(command_list)}\n"
            message_text += f"📅 Cập nhật lúc: {datetime.now(pytz.timezone('Asia/Ho_Chi_Minh')).strftime('%H:%M:%S %d/%m/%Y')}"

            send_message(client, message_object, thread_id, thread_type, message_text)
        except Exception as e:
            logging.error(f"Lỗi khi xử lý lệnh cmd: {str(e)}")
            send_message(client, message_object, thread_id, thread_type,
                         f"🚦 {source_name}, lỗi khi liệt kê lệnh: {str(e)}")

    threading.Thread(target=load_commands, daemon=True).start()

def handle_mybot_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        config = load_config()
        source_bot = None
        for bot in config.get("data", []):
            if str(bot.get("author_id")) == str(author_id):
                source_bot = bot
                break
        source_name = source_bot["username"] if source_bot else get_user_name_by_id(client, author_id)

        parts = message.lower().split(maxsplit=2)
        if len(parts) < 2:
            cookies = """{"_ga": "GA1.2.103..."}"""
            return send_message(client, message_object, thread_id, thread_type,
                f"《 HỆ THỐNG QUẢN LÝ BOT 》\n\n"
                f"➤ Tạo/Sửa Bot:\n"
                f"『{client.prefix}mybot create』\n"
                f"• Cú pháp: {client.prefix}mybot create [prefix] [imei] [cookies]\n"
                f"• Chức năng: Đăng ký/sửa đổi thông tin vào hệ thống ngbao\n"
                f"• Lưu ý: \n"
                f"   - Cần nhập dấu []\n"
                f"   - Nếu không biết cách điền, chat '{client.prefix}mybot create' để xem hướng dẫn\n"
                f"   - Chỉ hoạt động trong tin nhắn riêng\n\n"
                f"➤ Trợ Giúp:\n"
                f"『{client.prefix}mybot help』\n"
                f"• Hiển thị hướng dẫn sử dụng các lệnh cơ bản\n")

        subcommand = parts[1].lower()

        if subcommand not in ["create", "help", "list", "manager", "info", "detail"]:
            if not source_bot:
                return send_message(client, message_object, thread_id, thread_type,
                                   f"🚦 {source_name}, bạn chưa có bot! Hãy tạo bot bằng lệnh `{client.prefix}mybot create`. 📌")
            if not is_bot_active(author_id, client):
                return send_message(client, message_object, thread_id, thread_type,
                                   f"🚦 {source_name}, bot của bạn đang bị khóa hoặc hết hạn! Liên hệ ngbao để gia hạn. 😎")

        if subcommand == "create":
            handle_create_command(message, message_object, thread_id, thread_type, author_id, client)
        elif subcommand == "lock":
            handle_lock_command(message, message_object, thread_id, thread_type, author_id, client)
        elif subcommand == "unlock":
            handle_unlock_command(message, message_object, thread_id, thread_type, author_id, client)
        elif subcommand == "lockall":
            handle_lockall_command(message, message_object, thread_id, thread_type, author_id, client)
        elif subcommand == "unlockall":
            handle_unlockall_command(message, message_object, thread_id, thread_type, author_id, client)
        elif subcommand == "list":
            handle_list_bots_command(message, message_object, thread_id, thread_type, author_id, client)
        elif subcommand == "del":
            handle_del_command(message, message_object, thread_id, thread_type, author_id, client)
        elif subcommand == "rs":
            handle_rs_command(message, message_object, thread_id, thread_type, author_id, client)
        elif subcommand == "prefix":
            handle_change_prefix_command(message, message_object, thread_id, thread_type, author_id, client)
        elif subcommand == "active":
            handle_active_command(message, message_object, thread_id, thread_type, author_id, client)
        elif subcommand == "info":
            handle_bot_info_command(message, message_object, thread_id, thread_type, author_id, client)
        elif subcommand == "detail":
            handle_detail_command(message, message_object, thread_id, thread_type, author_id, client)
        elif subcommand == "manager":
            handle_manager_command(message, message_object, thread_id, thread_type, author_id, client)
        elif subcommand == "share":
            handle_share_command(message, message_object, thread_id, thread_type, author_id, client)
        elif subcommand == "update":
            handle_update_command(message, message_object, thread_id, thread_type, author_id, client)
        elif subcommand == "setbox":
            handle_setbox_command(message, message_object, thread_id, thread_type, author_id, client)
        elif subcommand == "help":
            handle_help_command(message, message_object, thread_id, thread_type, author_id, client)
        elif subcommand == "cmd":
            handle_cmd_command(message, message_object, thread_id, thread_type, author_id, client)
        else:
            send_message(client, message_object, thread_id, thread_type,
                         f"『Lệnh {client.prefix}mybot {subcommand} không được hỗ trợ 🤧")
    except Exception as e:
        source_name = get_user_name_by_id(client, author_id)
        send_message(client, message_object, thread_id, thread_type,
                     f"🚦 {source_name}, đã xảy ra lỗi khi xử lý lệnh: {str(e)}")

def PTA():
    return {
        'mybot': handle_mybot_command
    }