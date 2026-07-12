import json
import os
import time
from zlapi.models import Message, ThreadType, MultiMsgStyle, MessageStyle, Mention
from config import PREFIX

class AntiFileHandler:
    def __init__(self, client):
        self.client = client
        self.settings_file = "data/antifile_settings.json"
        self.enabled_groups = self.load_settings()
        self.file_violations = {}
        self.violation_window = 60
        self.kick_threshold = 3

    def load_settings(self):
        if not os.path.exists("data"): os.makedirs("data")
        try:
            with open(self.settings_file, "r") as f: return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError): return {}

    def save_settings(self):
        with open(self.settings_file, "w") as f:
            json.dump(self.enabled_groups, f, indent=4)

    def is_enabled(self, thread_id):
        return self.enabled_groups.get(str(thread_id), False)

    def get_user_name(self, uid):
        try:
            user_info = self.client.fetchUserInfo(uid)
            return user_info.changed_profiles.get(str(uid), {}).get('zaloName', str(uid))
        except: return str(uid)

    def handle_antifile_command(self, message_text, message_object, thread_id, thread_type, author_id):
        name = self.get_user_name(author_id)
        
        if str(author_id) not in self.client.ADMIN:
            rest_text = "⚠️ Bạn không có quyền sử dụng lệnh này."
            msg = f"{name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False)
            ])
            self.client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=60000)
            for r_icon in ["❌", "🚫", "🔐"]: self.client.sendReaction(message_object, r_icon, thread_id, thread_type, reactionType=75)
            return

        parts = message_text.lower().split()
        action = parts[1] if len(parts) > 1 else ""

        if action not in ["on", "off"]:
            current_status = "Bật ✅" if self.is_enabled(thread_id) else "Tắt ❌"
            rest_text = f"🚦Hướng dẫn: {PREFIX}antifile <on/off>\n➜Trạng thái hiện tại: {current_status}"
            msg = f"{name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False)
            ])
            self.client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=60000)
            for r_icon in ["👉", "📜", "ℹ️"]: self.client.sendReaction(message_object, r_icon, thread_id, thread_type, reactionType=75)
            return

        thread_id_str = str(thread_id)
        if action == "on":
            if self.is_enabled(thread_id_str):
                rest_text = "Chế độ Anti-File đã được bật trước đó. 🔄"
                reactions = ["⚠️", "🛡️", "📁"]
            else:
                self.enabled_groups[thread_id_str] = True
                self.save_settings()
                rest_text = f"Đã bật chế độ Anti-File. Vi phạm {self.kick_threshold} lần/phút sẽ bị kick. 🛡️"
                reactions = ["✅", "🛡️", "📁"]
        else:
            if not self.is_enabled(thread_id_str):
                rest_text = "Chế độ Anti-File đã được tắt trước đó. 🔄"
                reactions = ["⚠️", "📁", "🔓"]
            else:
                if thread_id_str in self.enabled_groups: del self.enabled_groups[thread_id_str]
                self.save_settings()
                rest_text = "Đã tắt chế độ Anti-File. 🔓"
                reactions = ["🚫", "📁", "🔓"]
        
        msg = f"{name}\n➜{rest_text}"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(name), style="bold", auto_format=False)
        ])
        self.client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=60000)
        for r_icon in reactions:
            try: self.client.sendReaction(message_object, r_icon, thread_id, thread_type, reactionType=75)
            except: pass

    def check_and_delete_file(self, message_object, thread_id, thread_type, author_id):
        if not self.is_enabled(thread_id) or \
           message_object.get('msgType') != 'share.file' or \
           self.client.is_group_admin(thread_id, author_id) or \
           (str(thread_id) in self.client.whitelist and str(author_id) in self.client.whitelist.get(str(thread_id), [])):
            return False

        try:
            msg_id, cli_msg_id = message_object.get('msgId'), message_object.get('cliMsgId')
            file_name = message_object.get('content', {}).get('title', 'Không tên')
            if msg_id: self.client.deleteGroupMsg(msg_id, author_id, cli_msg_id, thread_id)
        except Exception as e:
            self.client.logger.error(f"[AntiFile] Lỗi khi xóa file: {e}")
            return False

        now = time.time()
        if thread_id not in self.file_violations: self.file_violations[thread_id] = {}
        
        user_violations = self.file_violations[thread_id].get(author_id, {'count': 0, 'first_violation_time': now})
        
        if now - user_violations['first_violation_time'] > self.violation_window:
            user_violations = {'count': 1, 'first_violation_time': now}
        else:
            user_violations['count'] += 1
            
        self.file_violations[thread_id][author_id] = user_violations
        current_violation_count = user_violations['count']
        user_name = self.get_user_name(author_id)
        tag_author = f"{user_name}"
        msg = ""
        
        # =======================================
        #  GỬI TIN NHẮN RIÊNG (DM) – PHONG CÁCH HẺO DẢK
        # =======================================
        try:
            dm_text = (
                f"👑 ANTIFILE 👑\n"
                f"🔧 Gì vậy người đẹp ai cho mà gửi file ⁉️\n"
                f"➜ Ng dùng : @{author_id}\n"
                f"💢 Djt con mẹ mày </> Tân Xuân Hoàng dz đã k cho gửi file r!\n"
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

        if current_violation_count >= self.kick_threshold:
            try:
                self.client.blockUsersInGroup(author_id, thread_id)
                rest_text = f"📣{tag_author} đã bị chặn khỏi nhóm do gửi file quá nhiều lần ({current_violation_count}/{self.kick_threshold})."
                del self.file_violations[thread_id][author_id]
            except Exception as e:
                rest_text = f"Đã cố gắng chặn {tag_author} nhưng thất bại. Lỗi: {e}"
            msg = f"➜ [ANTI-FILE]\n{tag_author}\n➜ {rest_text}"
        else:
            rest_text = f"🚦Nhóm có quy định không được phép gửi file!\n➜ Tệp đã xóa: {file_name}\n➜ Cảnh báo lần {current_violation_count}/{self.kick_threshold}. Vui lòng không tái phạm!"
            msg = f"➜ [ANTI-FILE]\n{tag_author}\n➜ {rest_text}"

        if msg:
            tag_offset = msg.find(tag_author)
            styles = MultiMsgStyle([
                MessageStyle(offset=len("➜ "), length=len("[ANTI-FILE]"), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=len("➜ "), length=len("[ANTI-FILE]"), style="bold", auto_format=False)
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