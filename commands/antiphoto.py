import json
import os
import time
from zlapi.models import Message, ThreadType, MultiMsgStyle, MessageStyle, Mention
from config import PREFIX

class AntiPhotoHandler:
    def __init__(self, client):
        self.client = client
        self.settings_file = "data/antiphoto_settings.json"
        self.enabled_groups = self.load_settings()
        self.photo_violations = {}
        self.violation_window = 15
        self.kick_threshold = 8
        self.warn_threshold = 5
        self.cleanup_interval = 120
        
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

    def get_user_name(self, uid):
        try:
            user_info = self.client.fetchUserInfo(uid)
            return user_info.changed_profiles.get(str(uid), {}).get('zaloName', str(uid))
        except Exception as e:
            self.client.logger.error(f"[AntiPhoto] Lỗi khi lấy tên người dùng {uid}: {e}")
            return str(uid)

    def handle_antiphoto_command(self, message_text, message_object, thread_id, thread_type, author_id):
        name = self.get_user_name(author_id)
        
        if str(author_id) not in self.client.ADMIN:
            rest_text = "⚠️ Chỉ admin bot hoặc QTV nhóm mới có quyền sử dụng lệnh này."
            msg = f"{name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False)
            ])
            self.client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=60000)
            for r_icon in ["❌", "🚫", "🔐"]:
                self.client.sendReaction(message_object, r_icon, thread_id, thread_type, reactionType=75)
            return

        parts = message_text.lower().split()
        if len(parts) < 2 or parts[1] not in ["on", "off"]:
            current_status = "Bật ✅" if self.is_enabled(thread_id) else "Tắt ❌"
            rest_text = f"🚦Hướng dẫn: {PREFIX}antiphoto <on/off>\n➜Trạng thái hiện tại: {current_status}"
            msg = f"{name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False)
            ])
            self.client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=60000)
            for r_icon in ["👉", "📜", "ℹ️"]:
                self.client.sendReaction(message_object, r_icon, thread_id, thread_type, reactionType=75)
            return

        action = parts[1]
        thread_id_str = str(thread_id)
        
        if action == "on":
            if self.is_enabled(thread_id_str):
                rest_text = "Chế độ Anti-Photo đã được bật trước đó. 🔄"
                reactions = ["⚠️", "🛡️", "📸"]
            else:
                self.enabled_groups[thread_id_str] = True
                self.save_settings()
                rest_text = f"Đã bật Anti-Photo. Cảnh báo lần 1 & {self.warn_threshold}, kick ở lần {self.kick_threshold}. 🛡️"
                reactions = ["✅", "🛡️", "📸"]
        else:
            if not self.is_enabled(thread_id_str):
                rest_text = "Chế độ Anti-Photo đã được tắt trước đó. 🔄"
                reactions = ["⚠️", "📸", "🔓"]
            else:
                if thread_id_str in self.enabled_groups:
                    del self.enabled_groups[thread_id_str]
                self.save_settings()
                rest_text = "Đã tắt chế độ Anti-Photo. 🔓"
                reactions = ["🚫", "📸", "🔓"]
        
        msg = f"{name}\n➜{rest_text}"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(name), style="bold", auto_format=False)
        ])
        self.client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=60000)
        for r_icon in reactions:
            self.client.sendReaction(message_object, r_icon, thread_id, thread_type, reactionType=75)

    def cleanup_old_violations(self, thread_id, current_time):
        """Xóa dữ liệu vi phạm cũ để tránh bộ nhớ đầy"""
        if thread_id not in self.photo_violations:
            return
        for user_id, violations in list(self.photo_violations[thread_id].items()):
            if current_time - violations['first_violation_time'] > self.cleanup_interval:
                del self.photo_violations[thread_id][user_id]

    def check_antiphoto(self, message_object, thread_id, thread_type, author_id):
        if not self.is_enabled(thread_id) or \
           not message_object.get('msgType', '').startswith('chat.photo') or \
           self.client.is_group_admin(thread_id, author_id) or \
           (str(thread_id) in self.client.whitelist and str(author_id) in self.client.whitelist.get(str(thread_id), [])):
            return False

        msg_id, cli_msg_id = message_object.get('msgId'), message_object.get('cliMsgId')
        delete_success = False
        try:
            if msg_id:
                self.client.deleteGroupMsg(msg_id, author_id, cli_msg_id, thread_id)
                delete_success = True
            else:
                self.client.logger.error(f"[AntiPhoto] Không tìm thấy msgId trong message_object: {message_object}")
                return False
        except Exception as e:
            self.client.logger.error(f"[AntiPhoto] Lỗi khi xóa ảnh (msgId: {msg_id}, user: {author_id}): {e}")
            return False

        if not delete_success:
            return False

        now = time.time()
        self.cleanup_old_violations(thread_id, now)

        if thread_id not in self.photo_violations:
            self.photo_violations[thread_id] = {}
        
        user_violations = self.photo_violations[thread_id].get(author_id, {'count': 0, 'first_violation_time': now})
        
        if now - user_violations['first_violation_time'] > self.violation_window:
            user_violations = {'count': 1, 'first_violation_time': now}
        else:
            user_violations['count'] += 1
            
        self.photo_violations[thread_id][author_id] = user_violations
        count = user_violations['count']
        
        name = self.get_user_name(author_id)
        tag_author = f"{name}"
        msg = ""
        
        # =======================================
        #  GỬI TIN NHẮN RIÊNG (DM) – PHONG CÁCH HẺO DẢK
        # =======================================
        try:
            dm_text = (
                f"👑 ANTIPHOTO 👑\n"
                f"🔧 Gì vậy người đẹp ai cho mà gửi ảnh??\n"
                f"➜ Ng dùng : @{author_id}\n"
                f"💢 Djt con mẹ mày </> Tân Xuân Hoàng đã k cho gửi ảnh r!\n"
            )

            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(dm_text) + 30, style="color", color="#DB342E", auto_format=False),
                MessageStyle(offset=0, length=len(dm_text) + 30, style="bold", size="15", auto_format=False),
            ])

            self.client.send(
                Message(text=dm_text, style=styles),
                thread_id=author_id,
                thread_type=ThreadType.USER,
                ttl=7200000
            )

        except Exception as e:
            print(f"[BOT] Lỗi gửi DM: {e}")

        if count >= self.kick_threshold:
            try:
                self.client.blockUsersInGroup(author_id, thread_id)
                rest_text = f"📣{tag_author} đã bị chặn khỏi nhóm do spam ảnh liên tục ({count}/{self.kick_threshold} ảnh)."
                del self.photo_violations[thread_id][author_id]
            except Exception as e:
                rest_text = f"Đã cố gắng chặn {tag_author} nhưng thất bại. Lỗi: {e}"
            msg = f"➜ [ANTI-PHOTO]\n{tag_author}\n➜ {rest_text}"
        elif count == self.warn_threshold:
            rest_text = f"😡 CẢNH BÁO CUỐI CÙNG! Bạn đã vi phạm {count} lần. Thêm {self.kick_threshold - count} lần nữa sẽ bị chặn."
            msg = f"➜ [ANTI-PHOTO]\n{tag_author}\n➜ {rest_text}"
        elif count == 1:
            rest_text = f"🚦 Nhóm chúng tôi có quy định không được gửi ảnh. Đây là lần nhắc nhở đầu tiên."
            msg = f"➜ [ANTI-PHOTO]\n{tag_author}\n➜ {rest_text}"

        if msg:
            tag_offset = msg.find(tag_author)
            styles = MultiMsgStyle([
                MessageStyle(offset=len("➜ "), length=len("[ANTI-PHOTO]"), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=len("➜ "), length=len("[ANTI-PHOTO]"), style="bold", auto_format=False)
            ])
            self.client.replyMessage(
                Message(
                    text=msg,
                    mention=Mention(author_id, offset=tag_offset, length=len(tag_author)),
                    style=styles
                ),
                message_object,
                thread_id,
                thread_type,
                ttl=120000
            )
        return True