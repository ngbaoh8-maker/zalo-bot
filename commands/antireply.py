import json
import os
import time
from zlapi.models import Message, MultiMsgStyle, MessageStyle, Mention
from config import PREFIX


class AntiReplyHandler:
    def __init__(self, client):
        self.client = client
        self.settings_reply = "data/antireply_settings.json"
        self.enabled_groups = self.load_settings()
        self.reply_violations = {}
        self.violation_window = 60
        self.kick_threshold = 3

    # ---------------- SETTINGS ----------------
    def load_settings(self):
        if not os.path.exists("data"):
            os.makedirs("data")
        try:
            with open(self.settings_reply, "r") as f:
                return json.load(f)
        except:
            return {}

    def save_settings(self):
        with open(self.settings_reply, "w") as f:
            json.dump(self.enabled_groups, f, indent=4)

    def is_enabled(self, thread_id):
        return self.enabled_groups.get(str(thread_id), False)

    # ---------------- UTIL ----------------
    def get_user_name(self, uid):
        try:
            info = self.client.fetchUserInfo(uid)
            return info.changed_profiles.get(
                str(uid), {}).get("zaloName", str(uid))
        except:
            return str(uid)

    # ---------------- COMMAND ----------------
    def handle_antireply_command(
        self,
        message_text,
        message_object,
        thread_id,
        thread_type,
        author_id
    ):
        name = self.get_user_name(author_id)

        if str(author_id) not in self.client.ADMIN:
            msg = f"{name}\n➜ ⚠️ Bạn không có quyền sử dụng lệnh này."
            styles = MultiMsgStyle([
                MessageStyle(0, len(name), "color", "#db342e", False),
                MessageStyle(0, len(name), "bold", auto_format=False)
            ])
            self.client.replyMessage(
                Message(text=msg, style=styles),
                message_object, thread_id, thread_type, ttl=60000
            )
            return

        parts = message_text.lower().split()
        action = parts[1] if len(parts) > 1 else ""

        if action not in ["on", "off"]:
            status = "Bật ✅" if self.is_enabled(thread_id) else "Tắt ❌"
            msg = (
                f"{name}\n➜ 🚦Hướng dẫn: {PREFIX}antireply <on/off>\n"
                f"➜ Trạng thái hiện tại: {status}"
            )
            self.client.replyMessage(
                Message(text=msg),
                message_object, thread_id, thread_type, ttl=60000
            )
            return

        tid = str(thread_id)
        if action == "on":
            self.enabled_groups[tid] = True
            rest = "Đã bật Anti-Reply."
        else:
            self.enabled_groups.pop(tid, None)
            rest = "Đã tắt Anti-Reply."

        self.save_settings()
        self.client.replyMessage(
            Message(text=f"{name}\n➜ {rest}"),
            message_object, thread_id, thread_type, ttl=60000
        )

    # ---------------- DETECT REPLY ----------------
    def is_reply_message(self, message_object):
        return bool(getattr(message_object, "quote", None))

    # ---------------- HANDLE REPLY ----------------
    def check_and_delete_reply(
        self,
        message_object,
        thread_id,
        thread_type,
        author_id
    ):
        if not self.is_enabled(thread_id):
            return False

        if not self.is_reply_message(message_object):
            return False

        if self.client.is_group_admin(thread_id, author_id):
            return False

        try:
            self.client.deleteGroupMsg(
                message_object.get("msgId"),
                author_id,
                message_object.get("cliMsgId"),
                thread_id
            )
        except:
            return False

        now = time.time()
        self.reply_violations.setdefault(thread_id, {})
        user = self.reply_violations[thread_id].get(
            author_id, {"count": 0, "time": now}
        )

        if now - user["time"] > self.violation_window:
            user = {"count": 1, "time": now}
        else:
            user["count"] += 1

        self.reply_violations[thread_id][author_id] = user
        count = user["count"]
        name = self.get_user_name(author_id)

        if count >= self.kick_threshold:
            self.client.blockUsersInGroup(author_id, thread_id)
            text = f"🚫 {name} đã bị kick do spam reply."
        else:
            text = f"⛔ Cấm reply tin nhắn!\n➜ Cảnh báo {count}/{self.kick_threshold}"

        self.client.replyMessage(
            Message(text=text, mention=Mention(author_id, 0, len(name))),
            message_object, thread_id, thread_type, ttl=120000
        )
        return True
