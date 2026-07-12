import json
import os
import time
from zlapi.models import Message, ThreadType, MultiMsgStyle, MessageStyle, Mention
from config import PREFIX, ADMIN


class AntiTagHandler:
    def __init__(self, client):
        self.client = client
        self.settings_file = "data/antitag_settings.json"
        self.enabled_groups = self.load_settings()
        self.tag_violations = {}
        self.violation_window = 60      # khoảng 60s để tính vi phạm
        self.warn_threshold = 2         # cảnh báo sau 2 lần tag
        self.kick_threshold = 3         # chặn sau 3 lần tag

    # ====== Load / Save cài đặt ======
    def load_settings(self):
        if not os.path.exists("data"):
            os.makedirs("data")
        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_settings(self):
        with open(self.settings_file, "w", encoding="utf-8") as f:
            json.dump(self.enabled_groups, f, indent=4)

    # ====== Kiểm tra nhóm có bật antitag không ======
    def is_enabled(self, thread_id):
        return self.enabled_groups.get(str(thread_id), False)

    # ====== Lấy tên user ======
    def get_user_name(self, uid):
        try:
            info = self.client.fetchUserInfo(uid)
            return info.changed_profiles.get(str(uid), {}).get("zaloName", str(uid))
        except Exception:
            return str(uid)

    # ====== Lệnh antitag on/off ======
    def handle_antitag_command(self, message_text, message_object, thread_id, thread_type, author_id):
        name = self.get_user_name(author_id)
        thread_id_str = str(thread_id)

        # Kiểm tra quyền
        if str(author_id) not in ADMIN:
            msg = f"{name}\n⚠️ Bạn không có quyền dùng lệnh này."
            style = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#db342e"),
                MessageStyle(offset=0, length=len(name), style="bold")
            ])
            self.client.replyMessage(Message(text=msg, style=style),
                                     message_object, thread_id, thread_type, ttl=60000)
            for icon in ["🚫", "🔒", "❌"]:
                self.client.sendReaction(message_object, icon, thread_id, thread_type, reactionType=75)
            return

        args = message_text.lower().split()
        action = args[1] if len(args) > 1 else ""

        if action not in ["on", "off"]:
            current = "Bật ✅" if self.is_enabled(thread_id) else "Tắt ❌"
            msg = f"{name}\n⚙️ Dùng lệnh: {PREFIX}antitag <on/off>\n➜ Trạng thái hiện tại: {current}"
            style = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#db342e"),
                MessageStyle(offset=0, length=len(name), style="bold")
            ])
            self.client.replyMessage(Message(text=msg, style=style),
                                     message_object, thread_id, thread_type, ttl=60000)
            for icon in ["ℹ️", "⚙️", "🧩"]:
                self.client.sendReaction(message_object, icon, thread_id, thread_type, reactionType=75)
            return

        if action == "on":
            self.enabled_groups[thread_id_str] = True
            rest_text = "✅ Đã bật chế độ AntiTag. Tin có tag sẽ bị xóa và cảnh báo."
            reactions = ["✅", "🛡️", "🔔"]
        else:
            self.enabled_groups.pop(thread_id_str, None)
            rest_text = "🚫 Đã tắt chế độ AntiTag."
            reactions = ["🚫", "🔒", "🧩"]

        self.save_settings()

        msg = f"{name}\n➜ {rest_text}"
        style = MultiMsgStyle([
            MessageStyle(offset=0, length=len(name), style="color", color="#db342e"),
            MessageStyle(offset=0, length=len(name), style="bold")
        ])
        self.client.replyMessage(Message(text=msg, style=style),
                                 message_object, thread_id, thread_type, ttl=60000)
        for r in reactions:
            self.client.sendReaction(message_object, r, thread_id, thread_type, reactionType=75)

    # ====== Kiểm tra & xử lý tin có tag ======
    def check_and_handle_tag(self, message_object, thread_id, thread_type, author_id):
        if not self.is_enabled(thread_id):
            return False

        if str(author_id) in ADMIN:
            return False

        mentions = getattr(message_object, "mentions", [])
        if not mentions or len(mentions) == 0:
            return False

        mention_count = len(mentions)
        name = self.get_user_name(author_id)

        # Xóa tin nhắn có tag
        try:
            msg_id = getattr(message_object, "msgId", None)
            cli_msg_id = getattr(message_object, "cliMsgId", None)
            if msg_id:
                self.client.deleteGroupMsg(msg_id, author_id, cli_msg_id, thread_id)
        except Exception as e:
            print(f"[AntiTag] Lỗi xóa tin tag: {e}")

        # Tính số lần vi phạm
        now = time.time()
        if thread_id not in self.tag_violations:
            self.tag_violations[thread_id] = {}

        user_data = self.tag_violations[thread_id].get(author_id, {'count': 0, 'first_time': now})
        if now - user_data['first_time'] > self.violation_window:
            user_data = {'count': 1, 'first_time': now}
        else:
            user_data['count'] += 1

        self.tag_violations[thread_id][author_id] = user_data
        count = user_data['count']

        # Xử lý theo mức vi phạm
        if mention_count > 10 or count >= self.kick_threshold:
            self.block_user(author_id, thread_id, name, message_object)
            return True
        elif count >= self.warn_threshold:
            self.send_warning(thread_id, thread_type, message_object, author_id, name, mention_count, warn=True)
        else:
            self.send_warning(thread_id, thread_type, message_object, author_id, name, mention_count, warn=False)

        print(f"[AntiTag] {author_id} tag {mention_count} người - vi phạm {count} lần")
        return True

    # ====== Cảnh báo người dùng ======
    def send_warning(self, thread_id, thread_type, message_object, uid, name, mention_count, warn=False):
        if warn:
            text = f"⚠️ Cảnh báo {name}!\nBạn đã tag {mention_count} người. Cẩn thận kẻo bị chặn!"
        else:
            text = f"📢 {name}, vui lòng không tag nhiều người cùng lúc!"

        style = MultiMsgStyle([
            MessageStyle(offset=0, length=len(name), style="color", color="#db342e"),
            MessageStyle(offset=0, length=len(name), style="bold")
        ])
        self.client.replyMessage(
            Message(
                text=text,
                mention=Mention(uid=uid, offset=text.find(name), length=len(name)),
                style=style
            ),
            message_object, thread_id, thread_type, ttl=90000
        )

    # ====== Chặn người vi phạm ======
    def block_user(self, uid, thread_id, name, message_object):
        try:
            self.client.blockUsersInGroup(uid, thread_id)
            msg = f"🚨 {name} đã bị chặn do tag quá nhiều người hoặc spam tag!"
        except Exception as e:
            msg = f"❌ Không thể chặn {name}. Lỗi: {e}"

        style = MultiMsgStyle([
            MessageStyle(offset=2, length=len(name), style="color", color="#db342e"),
            MessageStyle(offset=2, length=len(name), style="bold")
        ])
        self.client.replyMessage(
            Message(text=msg, style=style),
            message_object, thread_id, ThreadType.Group, ttl=90000
        )