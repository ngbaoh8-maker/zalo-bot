import json
import os
import time
import threading
from zlapi.models import Message, ThreadType, MultiMsgStyle, MessageStyle, Mention
from config import PREFIX
import logging

logger = logging.getLogger(__name__)

def get_user_name(client, uid):
    try:
        user_info = client.fetchUserInfo(uid)
        author_info = user_info.changed_profiles.get(str(uid), {}) if user_info and user_info.changed_profiles else {}
        name = author_info.get('zaloName', 'Không xác định')
        return name
    except Exception as e:
        logger.error(f"[get_user_name] Failed to fetch name for user {uid}: {e}")
        return 'Không xác định'

class AntiRiconHandler:
    def __init__(self, client):
        self.client = client
        self.settings_file = "data/antiricon_settings.json"
        self.antiricon_enabled = self.load_settings()
        self.user_reaction_times = {}
        self.warned_reaction_users = {}
        self.reaction_spam_threshold = 20
        self.reaction_kick_threshold = 30
        self.reaction_spam_window = 10

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
            json.dump(self.antiricon_enabled, f, indent=4)

    def handle_antiricon_command(self, message_text, message_object, thread_id, thread_type, author_id):
        name = get_user_name(self.client, author_id)

        if str(author_id) not in self.client.ADMIN:
            rest_text = "⚠️ Bạn không có quyền sử dụng lệnh này."
            msg = f"{name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
            ])
            self.client.replyMessage(
                Message(text=msg, style=styles),
                message_object, thread_id, thread_type, ttl=60000
            )
            self.client.sendReaction(message_object, "❌", thread_id, thread_type, reactionType=75)
            self.client.sendReaction(message_object, "🚫", thread_id, thread_type, reactionType=75)
            self.client.sendReaction(message_object, "🔐", thread_id, thread_type, reactionType=75)
            return

        parts = message_text.split()
        if len(parts) < 2 or parts[1].lower() not in ["on", "off"]:
            current_status = "Bật" if self.antiricon_enabled.get(thread_id, False) else "Tắt"
            rest_text = f"Hướng dẫn: {PREFIX}antiricon <on/off>\nTrạng thái hiện tại: {current_status}"
            msg = f"{name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
            ])
            self.client.replyMessage(
                Message(text=msg, style=styles),
                message_object, thread_id, thread_type, ttl=60000
            )
            self.client.sendReaction(message_object, "👉", thread_id, thread_type, reactionType=75)
            self.client.sendReaction(message_object, "📜", thread_id, thread_type, reactionType=75)
            self.client.sendReaction(message_object, "ℹ️", thread_id, thread_type, reactionType=75)
            return

        action = parts[1].lower()
        if action == "on":
            self.antiricon_enabled[thread_id] = True
            self.save_settings()
            rest_text = "✅ Đã bật chế độ chống spam thả icon trong nhóm này."
            msg = f"{name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
            ])
            self.client.replyMessage(
                Message(text=msg, style=styles),
                message_object, thread_id, thread_type, ttl=60000
            )
            self.client.sendReaction(message_object, "✅", thread_id, thread_type, reactionType=75)
            self.client.sendReaction(message_object, "🛡️", thread_id, thread_type, reactionType=75)
            self.client.sendReaction(message_object, "😊", thread_id, thread_type, reactionType=75)
        elif action == "off":
            if thread_id in self.antiricon_enabled:
                self.antiricon_enabled[thread_id] = False
                self.save_settings()
            rest_text = "🚫 Đã tắt chế độ chống spam thả icon trong nhóm này."
            msg = f"{name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
            ])
            self.client.replyMessage(
                Message(text=msg, style=styles),
                message_object, thread_id, thread_type, ttl=60000
            )
            self.client.sendReaction(message_object, "🚫", thread_id, thread_type, reactionType=75)
            self.client.sendReaction(message_object, "😊", thread_id, thread_type, reactionType=75)
            self.client.sendReaction(message_object, "🔓", thread_id, thread_type, reactionType=75)

    def check_spam_reaction(self, author_id, message_object, thread_id, thread_type):
        if not self.antiricon_enabled.get(thread_id, False):
            return
            
        if self.client.is_group_admin(thread_id, author_id) or \
           (str(thread_id) in self.client.whitelist and str(author_id) in self.client.whitelist.get(str(thread_id), [])):
            return

        now = time.time()
        if thread_id not in self.user_reaction_times:
            self.user_reaction_times[thread_id] = {}
        if author_id not in self.user_reaction_times[thread_id]:
            self.user_reaction_times[thread_id][author_id] = []
        
        user_reactions = self.user_reaction_times[thread_id][author_id]
        user_reactions.append(now)
        user_reactions = [timestamp for timestamp in user_reactions if now - timestamp <= self.reaction_spam_window]
        self.user_reaction_times[thread_id][author_id] = user_reactions

        reaction_count = len(user_reactions)

        if reaction_count == self.reaction_spam_threshold:
            self.handle_spam_reaction_warn(author_id, message_object, thread_id, thread_type)
        elif reaction_count >= self.reaction_kick_threshold:
            self.handle_spam_reaction_violation(author_id, message_object, thread_id, thread_type)
            del self.user_reaction_times[thread_id][author_id]

    def handle_spam_reaction_warn(self, user_id, message_object, thread_id, thread_type):
        user_info = self.client.fetchUserInfo(user_id)
        display_name = str(user_id)
        if user_info and getattr(user_info, "changed_profiles", None):
            fetched_name = user_info.changed_profiles.get(user_id, {}).get('zaloName')
            if fetched_name and fetched_name != 'không xác định':
                display_name = fetched_name

        tag = f"{display_name}"
        msg = f"➜ [ANTI-REACTION]\n{tag}\n➜ Bạn đang thả biểu tượng cảm xúc quá nhanh.\n➜ Vui lòng dừng lại để tránh bị chặn khỏi nhóm!"
        styles = MultiMsgStyle([
            MessageStyle(offset=len("➜ "), length=len("[ANTI-REACTION]"), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=len("➜ "), length=len("[ANTI-REACTION]"), style="bold", auto_format=False),
        ])
        self.client.replyMessage(
            Message(text=msg, mention=Mention(user_id, length=len(tag), offset=msg.find(tag)), style=styles),
            message_object, thread_id, thread_type, ttl=30000
        )

    def handle_spam_reaction_violation(self, user_id, message_object, thread_id, thread_type):
        if self.client.is_group_admin(thread_id, user_id):
            return

        user_info = self.client.fetchUserInfo(user_id)
        display_name = str(user_id)
        if user_info and getattr(user_info, "changed_profiles", None):
            fetched_name = user_info.changed_profiles.get(user_id, {}).get('zaloName')
            if fetched_name and fetched_name != 'không xác định':
                display_name = fetched_name
        
        if self.client.group_lock_status.get(thread_id):
            try:
                self.client.blockUsersInGroup(user_id, thread_id)
                self.client._send_kick_notification(user_id, thread_id, display_name, message_object, is_secondary_kick=True, reason="thả icon")
            except:
                pass 
            return

        threading.Thread(
            target=self.client._lock_kick_and_unlock,
            args=(user_id, thread_id, display_name, message_object, "thả icon")
        ).start()