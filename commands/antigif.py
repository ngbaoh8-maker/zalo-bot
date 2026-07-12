import json
import os
import time
from zlapi.models import Message, MultiMsgStyle, MessageStyle, Mention
from config import PREFIX


class AntiGifHandler:
    def __init__(self, client):
        self.client = client
        self.settings_path = "data/antigif_settings.json"
        self.enabled_groups = self.load_settings()
        self.violations = {}
        self.violation_window = 60
        self.kick_threshold = 3

    # ================= SETTINGS =================
    def load_settings(self):
        if not os.path.exists("data"):
            os.makedirs("data")
        try:
            with open(self.settings_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_settings(self):
        with open(self.settings_path, "w", encoding="utf-8") as f:
            json.dump(self.enabled_groups, f, indent=4, ensure_ascii=False)

    def is_enabled(self, thread_id):
        return self.enabled_groups.get(str(thread_id), False)

    # ================= UTIL =================
    def get_user_name(self, uid):
        try:
            info = self.client.fetchUserInfo(uid)
            return info.changed_profiles.get(
                str(uid), {}
            ).get("zaloName", str(uid))
        except Exception:
            return str(uid)

    # ================= COMMAND =================
    def handle_antigif_command(
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
                message_object,
                thread_id,
                thread_type,
                ttl=60000
            )
            return

        parts = message_text.lower().split()
        action = parts[1] if len(parts) > 1 else ""

        if action not in ("on", "off"):
            status = "Bật ✅" if self.is_enabled(thread_id) else "Tắt ❌"
            msg = (
                f"{name}\n➜ 🚦Hướng dẫn: {PREFIX}antigif <on/off>\n"
                f"➜ Trạng thái hiện tại: {status}"
            )
            self.client.replyMessage(
                Message(text=msg),
                message_object,
                thread_id,
                thread_type,
                ttl=60000
            )
            return

        tid = str(thread_id)
        if action == "on":
            self.enabled_groups[tid] = True
            text = "Đã bật Anti-GIF (cấm gửi ảnh GIF)."
        else:
            self.enabled_groups.pop(tid, None)
            text = "Đã tắt Anti-GIF."

        self.save_settings()
        self.client.replyMessage(
            Message(text=f"{name}\n➜ {text}"),
            message_object,
            thread_id,
            thread_type,
            ttl=60000
        )

    # ================= DETECT =================
    def is_gif_message(self, message_object):
        content = message_object.get("content", {})

        if not isinstance(content, dict):
            return False

        # Zalo GIF thực tế
        if content.get("mediaType") == "gif":
            return True

        # Một số client gửi gif dưới dạng image/gif
        if content.get("mimeType") == "image/gif":
            return True

        # GIF từ kho sticker/gif
        if content.get("type") in ("gif", "sticker_gif"):
            return True

        return False

    # ================= HANDLE =================
    def check_and_delete_gif(
        self,
        message_object,
        thread_id,
        thread_type,
        author_id
    ):
        if not self.is_enabled(thread_id):
            return False

        if not self.is_gif_message(message_object):
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
        except Exception:
            return False

        now = time.time()
        self.violations.setdefault(thread_id, {})
        user = self.violations[thread_id].get(
            author_id, {"count": 0, "time": now}
        )

        if now - user["time"] > self.violation_window:
            user = {"count": 1, "time": now}
        else:
            user["count"] += 1

        self.violations[thread_id][author_id] = user
        count = user["count"]
        name = self.get_user_name(author_id)

        if count >= self.kick_threshold:
            try:
                self.client.blockUsersInGroup(author_id, thread_id)
                text = f"🚫 {name} đã bị kick do gửi GIF nhiều lần."
            except Exception:
                text = f"⚠️ Không thể kick {name}."
        else:
            text = (
                f"⛔ Nhóm cấm gửi GIF!\n"
                f"➜ Cảnh báo {count}/{self.kick_threshold}"
            )

        self.client.replyMessage(
            Message(text=text, mention=Mention(author_id, 0, len(name))),
            message_object,
            thread_id,
            thread_type,
            ttl=120000
        )
        return True
