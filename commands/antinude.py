import json
import os
import time
import requests
from io import BytesIO
from zlapi.models import Message, ThreadType, MultiMsgStyle, MessageStyle, Mention
from config import PREFIX

API_USER = '1620660599'
API_SECRET = '3QV8UF6nFMDfj3bKcCsM9yB24XoHEmHb'

class AntiNudeHandler:
    def __init__(self, client):
        self.client = client
        self.settings_file = "data/antinude_settings.json"
        self.enabled_groups = self.load_settings()
        self.nude_violations = {}
        self.violation_window = 60
        self.kick_threshold = 3
        self.warn_threshold = 2

    def load_settings(self):
        if not os.path.exists("data"): os.makedirs("data")
        try:
            with open(self.settings_file, "r", encoding="utf-8") as f: return json.load(f)
        except: return {}

    def save_settings(self):
        with open(self.settings_file, "w", encoding="utf-8") as f:
            json.dump(self.enabled_groups, f, indent=4, ensure_ascii=False)

    def is_enabled(self, thread_id):
        return self.enabled_groups.get(str(thread_id), False)

    def get_user_name(self, uid):
        try:
            user_info = self.client.fetchUserInfo(uid)
            return user_info.changed_profiles.get(str(uid), {}).get('zaloName', str(uid))
        except: return str(uid)

    def handle_antinude_command(self, message_text, message_object, thread_id, thread_type, author_id):
        name = self.get_user_name(author_id)

        if not self.client.is_allowed_author(author_id):
            rest_text = "⚠️ Bạn không có quyền sử dụng lệnh này."
            msg = f"{name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False)
            ])
            self.client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=60000)
            self.client.sendReaction(message_object, "👌", thread_id, thread_type)
            return

        parts = (message_text or "").lower().split()
        action = parts[1] if len(parts) > 1 else ""

        if action not in ["on", "off"]:
            current_status = "Bật" if self.is_enabled(thread_id) else "Tắt"
            rest_text = f" Dùng: {PREFIX}antinude <on/off> | Trạng thái hiện tại: {current_status}"
            msg = f"{name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False)
            ])
            self.client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=60000)
            return

        thread_id_str = str(thread_id)
        if action == "on":
            self.enabled_groups[thread_id_str] = True
            rest_text = f"Đã bật Anti-Nude. Gửi ảnh nóng {self.kick_threshold} lần sẽ cút🚦"
        else:
            if thread_id_str in self.enabled_groups: del self.enabled_groups[thread_id_str]
            rest_text = "Đã tắt chế độ Anti-Nude 🔓"

        self.save_settings()
        msg = f"{name}\n➜{rest_text}"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(name), style="bold", auto_format=False)
        ])
        self.client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=60000)
        self.client.sendReaction(message_object, "🔞", thread_id, thread_type)

    def _extract_image_url(self, mo):
        try:
            attach = mo.get('attach') if isinstance(mo, dict) else getattr(mo, 'attach', None)
            if isinstance(attach, str):
                try: attach = json.loads(attach)
                except: pass

            if isinstance(attach, dict):
                return attach.get('hdUrl') or attach.get('originUrl') or attach.get('url')

            content = mo.get('content') if isinstance(mo, dict) else getattr(mo, 'content', None)
            if isinstance(content, dict) and content.get('href'):
                return content.get('href')
        except: pass
        return None

    def check_and_handle_nude(self, message_object, thread_id, thread_type, author_id):
        if not self.is_enabled(thread_id): return False
        if self.client.is_allowed_author(author_id) or self.client.is_group_admin(thread_id, author_id): return False

        img_url = self._extract_image_url(message_object)
        if not img_url: return False

        try:
            img_data = requests.get(img_url, timeout=5).content
            files = {'media': ('image.jpg', img_data)}
            data = {
                'models': 'nudity-2.0',
                'api_user': API_USER,
                'api_secret': API_SECRET
            }

            r = requests.post('https://api.sightengine.com/1.0/check.json', files=files, data=data, timeout=10)
            output = r.json()

            if output.get('status') != 'success': return False

            nudity = output.get('nudity', {})
            is_unsafe = False
            reason = ""

            if nudity.get('sexual_activity', 0) > 0.5:
                is_unsafe = True; reason = "Hành vi tình dục"
            elif nudity.get('sexual_display', 0) > 0.5:
                is_unsafe = True; reason = "Lộ bộ phận nhạy cảm"
            elif nudity.get('erotica', 0) > 0.6:
                is_unsafe = True; reason = "Hình ảnh gợi dục"

            if is_unsafe:
                msg_id = message_object.get('msgId') if isinstance(message_object, dict) else getattr(message_object, 'msgId', None)
                cli_msg_id = message_object.get('cliMsgId') if isinstance(message_object, dict) else getattr(message_object, 'cliMsgId', None)
                if msg_id: self.client.deleteGroupMsg(msg_id, author_id, cli_msg_id, thread_id)

                self._handle_violation(author_id, thread_id, thread_type, reason, message_object)
                return True

        except Exception as e:
            self.client.logger.error(f"[AntiNude] Lỗi: {e}")
        return False

    def _handle_violation(self, author_id, thread_id, thread_type, reason, mo):
        now = time.time()
        if thread_id not in self.nude_violations: self.nude_violations[thread_id] = {}
        user_v = self.nude_violations[thread_id].get(author_id, {'count': 0, 'first': now})

        if now - user_v['first'] > self.violation_window:
            user_v = {'count': 1, 'first': now}
        else:
            user_v['count'] += 1

        self.nude_violations[thread_id][author_id] = user_v
        count = user_v['count']
        name = self.get_user_name(author_id)
        tag_author = f"{name}"
        
                # =======================================
        #  GỬI TIN NHẮN RIÊNG (DM) – PHONG CÁCH HẺO DẢK
        # =======================================
        try:
            dm_text = (
                f"👑 ANTINUDE 👑\n"
                f"🔧 Gì vậy người đẹp ai cho mà gửi ảnh nóg??\n"
                f"➜ Ng dùng : @{author_id}\n"
                f"💢 Djt con mẹ mày </> Tân Xuân Hoàng dz đã k cho gửi ảnh nóg 18+ r!\n"
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
                rest_text = f"📣Thằng óc {tag_author} đã bị chặn vì gửi ảnh nóng ({reason})."
                del self.nude_violations[thread_id][author_id]
            except: rest_text = f"Đã cố gắng chặn {tag_author} nhưng thất bại."
            msg = f"➜ [ANTI-NUDE]\n{tag_author}\n➜ {rest_text}"
        elif count >= self.warn_threshold:
            rest_text = f"mày rải ảnh nóng lần nữa cút con mẹ mày đi á"
            msg = f"➜ [ANTI-NUDE]\n{tag_author}\n➜ {rest_text}"
        else:
            rest_text = f"🚦Cảnh Báo: Đại ca tao bảo đéo cho mày rải ảnh nhạy cảm ở đây"
            msg = f"➜ [ANTI-NUDE]\n{tag_author}\n➜ {rest_text}"

        tag_offset = msg.find(tag_author)
        styles = MultiMsgStyle([
            MessageStyle(offset=len("➜ "), length=len("[ANTI-NUDE]"), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=len("➜ "), length=len("[ANTI-NUDE]"), style="bold", auto_format=False)
        ])

        self.client.replyMessage(
            Message(
                text=msg,
                mention=Mention(uid=author_id, offset=tag_offset, length=len(tag_author)),
                style=styles
            ),
            mo, thread_id, thread_type, ttl=120000
        )
