import json
import os
import time
from zlapi.models import Message, MultiMsgStyle, MessageStyle, Mention
from config import PREFIX


class AntiVoiceHandler:
    def __init__(self, client):
        self.client = client
        self.settings_voice = "data/antivoice_settings.json"
        self.enabled_groups = self.load_settings()
        self.voice_violations = {}
        self.violation_window = 60   # giây
        self.kick_threshold = 3      # số lần vi phạm trước khi kick

    # ------------------------ QUẢN LÝ CÀI ĐẶT ------------------------
    def load_settings(self):
        if not os.path.exists("data"):
            os.makedirs("data")
        try:
            with open(self.settings_voice, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_settings(self):
        with open(self.settings_voice, "w") as f:
            json.dump(self.enabled_groups, f, indent=4)

    def is_enabled(self, thread_id):
        return self.enabled_groups.get(str(thread_id), False)

    # ------------------------ TIỆN ÍCH ------------------------
    def get_user_name(self, uid):
        try:
            user_info = self.client.fetchUserInfo(uid)
            return user_info.changed_profiles.get(
                str(uid), {}).get('zaloName', str(uid))
        except BaseException:
            return str(uid)

    # ------------------------ LỆNH ANTIVOICE ------------------------
    def handle_antivoice_command(
        self,
        message_text,
        message_object,
        thread_id,
        thread_type,
        author_id
    ):
        name = self.get_user_name(author_id)

        if str(author_id) not in self.client.ADMIN:
            rest_text = "⚠️ Bạn không có quyền sử dụng lệnh này."
            msg = f"{name}\n➜ {rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(
                    offset=0,
                    length=len(name),
                    style="color",
                    color="#db342e",
                    auto_format=False
                ),
                MessageStyle(
                    offset=0,
                    length=len(name),
                    style="bold",
                    auto_format=False
                )
            ])
            self.client.replyMessage(
                Message(text=msg, style=styles),
                message_object,
                thread_id,
                thread_type,
                ttl=60000
            )
            return

        parts = message_text.lower().split()
        action = parts[1] if len(parts) > 1 else ""

        if action not in ["on", "off"]:
            current_status = "Bật ✅" if self.is_enabled(thread_id) else "Tắt ❌"
            rest_text = (
                f"🚦Hướng dẫn: {PREFIX}antivoice <on/off>\n"
                f"➜ Trạng thái hiện tại: {current_status}"
            )
            msg = f"{name}\n➜ {rest_text}"
            self.client.replyMessage(
                Message(text=msg),
                message_object,
                thread_id,
                thread_type,
                ttl=60000
            )
            return

        thread_id_str = str(thread_id)
        if action == "on":
            self.enabled_groups[thread_id_str] = True
            self.save_settings()
            rest_text = (
                f"Đã bật Anti-Voice. Gửi voice "
                f"{self.kick_threshold} lần/phút sẽ bị kick. 🔇"
            )
        else:
            self.enabled_groups.pop(thread_id_str, None)
            self.save_settings()
            rest_text = "Đã tắt chế độ Anti-Voice. 🔊"

        msg = f"{name}\n➜ {rest_text}"
        self.client.replyMessage(
            Message(text=msg),
            message_object,
            thread_id,
            thread_type,
            ttl=60000
        )

    # ------------------------ PHÁT HIỆN VOICE ------------------------
    def is_voice_message(self, message_object):
        msg_type = message_object.get("msgType")
        if msg_type in ["chat.voice", "chat.audio"]:
            return True

        content = message_object.get("content", {})
        if isinstance(content, dict):
            if content.get("mediaType") == "voice":
                return True

        return False

    # ------------------------ XỬ LÝ VOICE ------------------------
    def check_and_delete_voice(
        self,
        message_object,
        thread_id,
        thread_type,
        author_id
    ):
        if not self.is_enabled(thread_id):
            return False

        if not self.is_voice_message(message_object):
            return False

        if self.client.is_group_admin(thread_id, author_id):
            return False

        try:
            msg_id = message_object.get("msgId")
            cli_msg_id = message_object.get("cliMsgId")
            if msg_id:
                self.client.deleteGroupMsg(
                    msg_id, author_id, cli_msg_id, thread_id
                )
        except Exception as e:
            self.client.logger.error(f"[AntiVoice] Lỗi xóa voice: {e}")
            return False

        now = time.time()
        if thread_id not in self.voice_violations:
            self.voice_violations[thread_id] = {}

        user_violations = self.voice_violations[thread_id].get(
            author_id,
            {'count': 0, 'first_violation_time': now}
        )

        if now - user_violations['first_violation_time'] > self.violation_window:
            user_violations = {'count': 1, 'first_violation_time': now}
        else:
            user_violations['count'] += 1

        self.voice_violations[thread_id][author_id] = user_violations
        count = user_violations['count']
        user_name = self.get_user_name(author_id)

        if count >= self.kick_threshold:
            try:
                self.client.blockUsersInGroup(author_id, thread_id)
                rest_text = (
                    f"📣 {user_name} đã bị chặn khỏi nhóm do gửi voice "
                    f"quá nhiều lần ({count}/{self.kick_threshold})."
                )
                del self.voice_violations[thread_id][author_id]
            except Exception as e:
                rest_text = f"Không thể chặn {user_name}. Lỗi: {e}"
        else:
            rest_text = (
                f"🔇 Nhóm không cho phép gửi voice!\n"
                f"➜ Cảnh báo lần {count}/{self.kick_threshold}."
            )

        msg = f"➜ [ANTI-VOICE]\n{user_name}\n➜ {rest_text}"

        self.client.replyMessage(
            Message(
                text=msg,
                mention=Mention(
                    author_id,
                    msg.find(user_name),
                    len(user_name)
                )
            ),
            message_object,
            thread_id,
            thread_type,
            ttl=120000
        )
        return True
