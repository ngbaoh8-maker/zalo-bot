import json
import os
import time
from zlapi.models import Message, ThreadType, MultiMsgStyle, MessageStyle, Mention
from config import PREFIX

class AntiLinkHandler:
    def __init__(self, client):
        self.client = client
        self.settings_file = "data/antilink_settings.json"
        self.enabled_groups = self.load_settings()

        # Bộ đếm vi phạm
        self.link_violations = {}
        self.violation_window = 60       # thời gian reset (1 phút)
        self.kick_threshold = 3          # số lần vi phạm để kick
        self.warn_threshold = 2          # số lần cảnh cáo

    def load_settings(self):
        if not os.path.exists("data"):
            os.makedirs("data")
        try:
            with open(self.settings_file, "r") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except:
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
        except:
            return str(uid)

    # ===========================
    #  LỆNH BẬT / TẮT ANTILINK
    # ===========================
    def handle_antilink_command(self, message_text, message_object, thread_id, thread_type, author_id):
        name = self.get_user_name(author_id)

        if str(author_id) not in self.client.ADMIN:
            msg = f"{name}\n➜⚠️ Bạn không có quyền dùng lệnh này."
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False)
            ])
            self.client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type)
            return

        parts = message_text.lower().split()
        action = parts[1] if len(parts) > 1 else ""

        if action not in ["on", "off"]:
            current = "Bật ✅" if self.is_enabled(thread_id) else "Tắt ❌"
            msg = f"{name}\n➜Dùng: {PREFIX}antilink <on/off>\n➜Trạng thái: {current}"
            self.client.replyMessage(Message(text=msg), message_object, thread_id, thread_type)
            return

        if action == "on":
            self.enabled_groups[str(thread_id)] = True
            rest = "Đã bật AntiLink 🛡️"
        else:
            self.enabled_groups.pop(str(thread_id), None)
            rest = "Đã tắt AntiLink 🔕"

        self.save_settings()
        msg = f"{name}\n➜{rest}"
        self.client.replyMessage(Message(text=msg), message_object, thread_id, thread_type)

    # ====================================
    #  XỬ LÝ MỖI KHI USER GỬI LINK
    # ====================================
    def check_and_handle_link(self, message_object, thread_id, thread_type, author_id):
        if not self.is_enabled(thread_id):
            return False

        if not self.client.is_url_in_message(message_object):
            return False

        if self.client.is_group_admin(thread_id, author_id):
            return False

        # Xoá tin nhắn
        try:
            self.client.deleteGroupMsg(
                message_object.get("msgId"),
                author_id,
                message_object.get("cliMsgId"),
                thread_id
            )
        except:
            pass

        now = time.time()

        if thread_id not in self.link_violations:
            self.link_violations[thread_id] = {}

        user = self.link_violations[thread_id].get(author_id, {
            "count": 0,
            "first": now
        })

        if now - user["first"] > self.violation_window:
            user = {"count": 1, "first": now}
        else:
            user["count"] += 1

        self.link_violations[thread_id][author_id] = user
        count = user["count"]

        author_name = self.get_user_name(author_id)
        tag = f"{author_name}"

        # =======================================
        #  GỬI TIN NHẮN RIÊNG (DM) – PHONG CÁCH HẺO DẢK
        # =======================================
        try:
            dm_text = (
                f"👑 ANTILINK 👑\n"
                f"🔧 Gì vậy anh bạn ai cho mà rải??\n"
                f"➜ Ng dùng : @{author_id}\n"
                f"💢 Dcm m # > Tân Xuân Hoàng Dz đã k cho rải link r\n"
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

        # =======================================
        #  XỬ LÝ CẢNH CÁO / KICK TRONG NHÓM
        # =======================================
        if count >= self.kick_threshold:
            try:
                self.client.blockUsersInGroup(author_id, thread_id)
                rest = f"❌ {tag} đã bị chặn do gửi link {count} lần!"
            except Exception as e:
                rest = f"Không thể chặn {tag}. Lỗi: {e}"
        elif count >= self.warn_threshold:
            rest = f"⚠️ {tag} đã vi phạm {count} lần. Cẩn thận bị kick!"
        else:
            rest = f"🚦 {tag}, nhóm cấm gửi link nhé!"

        reply = f"[ANTI-LINK]\n{rest}"

        try:
            self.client.replyMessage(
                Message(
                    text=reply,
                    mention=Mention(uid=author_id, offset=reply.find(tag), length=len(tag))
                ),
                message_object,
                thread_id,
                thread_type
            )
        except:
            self.client.replyMessage(Message(text=reply), message_object, thread_id, thread_type)

        return True
