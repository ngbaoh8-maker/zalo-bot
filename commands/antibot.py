import json
import os
import re
import time
from zlapi.models import Message, ThreadType, MultiMsgStyle, MessageStyle, Mention
from config import PREFIX

class AntiBotHandler:
    def __init__(self, client):
        self.client = client
        self.settings_file = "data/antibot_settings.json"
        self.enabled_groups = self.load_settings()
        self.bot_keywords = [
            "prefix", "bot", "menu", "help", "token", "autojoin",
            "add bot", "cài bot", "mybot", "/ff", ".help", ".bot", "!ai"
        ]
        self.violations = {}
        self.kick_threshold = 2
        self.detect_window = 60  # giây
        self.reaction_icons = {
            'antibot off': ['🚫', '🥀', '‼️', '🛑'],
            'antibot on': ['✅', '🗿', '❄️', '💎'],
            'antibot': ['⚠️', '🥀', '🐧', '🦧'],
        }


    # --- SETTINGS ---
    def load_settings(self):
        if not os.path.exists("data"):
            os.makedirs("data")
        try:
            with open(self.settings_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_settings(self):
        with open(self.settings_file, "w") as f:
            json.dump(self.enabled_groups, f, indent=4)

    def is_enabled(self, thread_id):
        return self.enabled_groups.get(str(thread_id), False)

    # --- HELPER ---
    def get_user_name(self, uid):
        try:
            user_info = self.client.fetchUserInfo(uid)
            return user_info.changed_profiles.get(str(uid), {}).get("zaloName", str(uid))
        except:
            return str(uid)

    # --- COMMAND: on/off ---
    def handle_antibot_command(self, message_text, message_object, thread_id, thread_type, author_id):
        name = self.get_user_name(author_id)
        if str(author_id) not in self.client.ADMIN and str(author_id) not in getattr(self.client, "ADM", []):
            msg = f"{name}\n➜⚠️ Bạn không có quyền sử dụng lệnh này."
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#db342e"),
                MessageStyle(offset=0, length=len(name), style="bold")
            ])
            self.client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type)
            for icon in ["🚫", "🔐"]:
                self.client.sendReaction(message_object, icon, thread_id, thread_type, reactionType=75)
            return

        parts = message_text.lower().split()
        action = parts[1] if len(parts) > 1 else ""
        thread_str = str(thread_id)

        if action not in ["on", "off"]:
            status = "Bật ✅" if self.is_enabled(thread_id) else "Tắt ❌"
            msg = f"{name}\n➜🚦Hướng dẫn: {PREFIX}antibot <on/off>\n➜Trạng thái hiện tại: {status}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#db342e"),
                MessageStyle(offset=0, length=len(name), style="bold")
            ])
            self.client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type)
            for icon in ["📜", "ℹ️"]:
                self.client.sendReaction(message_object, icon, thread_id, thread_type, reactionType=75)
            return

        if action == "on":
            if self.is_enabled(thread_str):
                msg = f"{name}\n➜⚠️ AntiBot đã bật từ trước."
                icons = ["⚠️", "🤖"]
            else:
                self.enabled_groups[thread_str] = True
                self.save_settings()
                msg = f"{name}\n➜✅ Đã bật AntiBot.\nBot sẽ tự động cảnh báo hoặc kick người nghi là bot khác."
                icons = ["✅", "🛡️"]
        else:
            if not self.is_enabled(thread_str):
                msg = f"{name}\n➜⚠️ AntiBot đã tắt từ trước."
                icons = ["⚠️", "🔓"]
            else:
                del self.enabled_groups[thread_str]
                self.save_settings()
                msg = f"{name}\n➜❌ Đã tắt AntiBot."
                icons = ["🚫", "🔓"]

        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(name), style="color", color="#db342e"),
            MessageStyle(offset=0, length=len(name), style="bold")
        ])
        self.client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type)
        for icon in icons:
            try:
                self.client.sendReaction(message_object, icon, thread_id, thread_type, reactionType=75)
            except:
                pass

    # --- KIỂM TRA & XỬ LÝ BOT KHÁC ---
    def check_and_handle_message(self, message_text, message_object, thread_id, thread_type, author_id):
        if not self.is_enabled(thread_id) or thread_type != ThreadType.GROUP:
            return False

        text = str(message_text).lower()
        if str(author_id) in self.client.ADMIN or str(author_id) in getattr(self.client, "ADM", []):
            return False

        if not any(k in text for k in self.bot_keywords):
            return False

        now = time.time()
        thread_str = str(thread_id)
        if thread_str not in self.violations:
            self.violations[thread_str] = {}
        data = self.violations[thread_str].get(author_id, {"count": 0, "time": now})

        if now - data["time"] > self.detect_window:
            data = {"count": 1, "time": now}
        else:
            data["count"] += 1
        self.violations[thread_str][author_id] = data

        name = self.get_user_name(author_id)
        count = data["count"]

        if count >= self.kick_threshold:
            try:
                self.client.kick_member_safe(thread_id, author_id)
                msg = (
    f"⚠️ [ANTI-BOT]\n➜ Phát hiện {name} gửi tin nghi là bot.\n"
    f"⚙️ Hệ thống không có quyền kick, vui lòng admin kiểm tra thủ công."
)

                del self.violations[thread_str][author_id]
            except Exception as e:
                msg = f"⚠️ Không thể kick {name}. Lỗi: {e}"
        else:
            msg = f"⚠️ [ANTI-BOT]\n➜ Cảnh báo {name} ({count}/{self.kick_threshold}).\nKhông gửi lệnh bot trong nhóm!"

        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len("[ANTI-BOT]"), style="color", color="#db342e"),
            MessageStyle(offset=0, length=len("[ANTI-BOT]"), style="bold")
        ])
        self.client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type)
        return True
