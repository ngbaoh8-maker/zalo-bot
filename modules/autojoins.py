from zlapi.models import Message, ZaloAPIException, ThreadType, Mention, MultiMention, MultiMsgStyle, MessageStyle
from config import ADMIN, PREFIX
import json
import os
import re
import logging
import time
import requests
import threading
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

des = {
    'version': "1.1.1",
    'credits': "ngbao",
    'description': "Tự động tham gia nhóm Zalo",
    'power': "Quản trị viên Bot"
}

def get_user_name(client, uid):
    try:
        user_info = client.fetchUserInfo(uid)
        author_info = user_info.changed_profiles.get(str(uid), {}) if user_info and user_info.changed_profiles else {}
        name = author_info.get('zaloName', 'Không xác định')
        return name
    except Exception as e:
        logger.error(f"[get_user_name] Failed to fetch name for user {uid}: {e}")
        return 'Không xác định'

class AutoJoinHandler:
    def __init__(self, client):
        self.client = client
        self.settings_file = "data/autojoin_settings.json"
        self.autojoin_enabled = self.load_autojoin_settings()
        self.cleanup_invalid_groups()
        self.start_periodic_check()

    def load_autojoin_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, "r") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Lỗi tải autojoin: {e}")
            return {}

    def save_autojoin_settings(self):
        try:
            with open(self.settings_file, "w") as f:
                json.dump(self.autojoin_enabled, f, indent=4)
        except Exception as e:
            logger.error(f"Lỗi lưu autojoin: {e}")

    def cleanup_invalid_groups(self):
        try:
            all_groups = set(str(group_id) for group_id in self.client.fetchAllGroups().gridVerMap.keys())
            current_settings = self.autojoin_enabled.copy()
            for group_id in current_settings:
                if group_id not in all_groups:
                    del self.autojoin_enabled[group_id]
            self.save_autojoin_settings()
        except Exception as e:
            logger.error(f"Lỗi dọn nhóm không tồn tại: {e}")

    def check_new_groups(self):
        try:
            all_groups = self.client.fetchAllGroups().gridVerMap.keys()
            for group_id in all_groups:
                group_id = str(group_id)
                if group_id not in self.autojoin_enabled:
                    self.on_group_joined(group_id)
        except Exception as e:
            logger.error(f"Lỗi kiểm tra nhóm mới: {e}")

    def start_periodic_check(self):
        try:
            self.check_new_groups()
            threading.Timer(300, self.start_periodic_check).start()
        except Exception as e:
            logger.error(f"Lỗi periodic check: {e}")

    def on_group_joined(self, group_id):
        try:
            group_id = str(group_id)
            if group_id not in self.autojoin_enabled:
                all_off = all(not status for status in self.autojoin_enabled.values()) if self.autojoin_enabled else True
                self.autojoin_enabled[group_id] = not all_off
                self.save_autojoin_settings()
        except Exception as e:
            logger.error(f"Lỗi khi thêm nhóm {group_id}: {e}")

    def handle_autojoin_command(self, message_text, message_object, thread_id, thread_type, author_id):
        name = get_user_name(self.client, author_id)
        if author_id not in ADMIN:
            msg = f"{name}\n➜❌ Bạn không có quyền dùng lệnh này."
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
            ])
            self.client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=60000)
            self.client.sendReaction(message_object, "🚫", thread_id, thread_type, reactionType=75)
            return

        parts = message_text.split()
        if len(parts) < 2:
            msg = f"{name}\n➜🚦 Cách dùng: {PREFIX}autojoin <on/off>"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
            ])
            self.client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=60000)
            self.client.sendReaction(message_object, "👉", thread_id, thread_type, reactionType=75)
            return

        action = parts[1].lower()
        try:
            all_groups = self.client.fetchAllGroups().gridVerMap.keys()
            if action == "on":
                for group_id in all_groups:
                    self.autojoin_enabled[str(group_id)] = True
                self.save_autojoin_settings()
                rest_text = f"🚦 Đã bật autojoin cho {len(all_groups)} nhóm."
                icon = "✅"
            elif action == "off":
                for group_id in all_groups:
                    self.autojoin_enabled[str(group_id)] = False
                self.save_autojoin_settings()
                rest_text = f"🚦 Đã tắt autojoin cho {len(all_groups)} nhóm."
                icon = "💨"
            else:
                rest_text = "🤦‍♂️ Lệnh không hợp lệ."
                icon = "🤦‍♂️"

            msg = f"{name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
            ])
            self.client.replyMessage(Message(text=msg, style=styles), message_object, thread_id, thread_type, ttl=60000)
            self.client.sendReaction(message_object, icon, thread_id, thread_type, reactionType=75)
        except Exception as e:
            logger.error(f"Lỗi xử lý lệnh autojoin: {e}")

    def validate_group_link(self, group_link):
        zalo_link_pattern = r"https://zalo\.me/g/([^\s]+)"
        match = re.search(zalo_link_pattern, group_link)
        if not match:
            return None
        group_code = match.group(1).strip()
        return group_code, f"https://zalo.me/g/{group_code}"

    def check_group_status(self, group_link):
        try:
            response = requests.get(group_link, timeout=5)
            return response.status_code == 200
        except:
            return False

    def check_and_join_group(self, message_text, message_object, thread_id, thread_type, author_id):
        if str(thread_id) not in self.autojoin_enabled or not self.autojoin_enabled[str(thread_id)]:
            return

        zalo_link_pattern = r"https://zalo\.me/[^\s]+"
        match = re.search(zalo_link_pattern, message_text)
        if not match:
            return

        group_link = match.group(0).strip()
        result = self.validate_group_link(group_link)
        if not result:
            return
        group_code, standardized_link = result

        if not self.check_group_status(standardized_link):
            return

        try:
            data_join = self.client.joinGroup(standardized_link)
            error_code = data_join.get('error_code', -1)

            icon_success = ["🗿ngbao VIP😗", "🐢ngbao Bá Rõ🤨", "💸Thuê Bot 40k🐧", "💸Nhận Rãi Thuê", "🌟Cho Thuê Bót😹"]
            icon_fail = ["Phải Chịu🐻", "💀ThấtBại😿", "😭KhôngThểVào🐻"]

            if error_code in [0, 240, 178, 1022]:
                chosen_icon = random.choice(icon_success)
            else:
                chosen_icon = random.choice(icon_fail)

            self.client.sendReaction(message_object, chosen_icon, thread_id, thread_type)

            summary_title = "[𝐀𝐮𝐭𝐨𝐉𝐨𝐢𝐧 𝐂ủ𝐚 𝔻𝕦𝕔 𝔻𝕦𝕪]\n"
            summary_text = summary_title

            if error_code == 0:
                summary_text += "🤖 𝐓𝐚𝐨 𝐃𝐚𝐧𝐠 𝐕𝐚̀𝐨 𝐆𝐫, 𝐃𝐨̣𝐢 𝐓𝐢́...\n"
            elif error_code == 175:
                summary_text += "🚫 𝐂𝐨𝐧 𝐂𝐡𝐨́ 𝐍𝐚̀𝐨 𝐃𝐚́𝐦 𝐁𝐥𝐨𝐜𝐤 𝐁𝗼̂́!\n"
            elif error_code in [240, 1022]:
                summary_text += "📩 𝐃𝐚̃ 𝐆𝐮̛̉𝐢 𝐘𝐞̂𝐮 𝐂𝐚̂̀𝐮 𝐓𝐫𝐨𝐧𝐠 𝐃𝐨̛̣𝐢, 𝐂𝐡𝐨̛̀ 𝐃𝐮𝐲𝐞̣̂𝐭...\n"
            elif error_code == 178:
                summary_text += "😎 𝐓𝐚𝐨 𝐎̛̉ 𝐓𝐫𝐨𝐧𝐠 𝐑𝐨̂̀𝐢, 𝐇𝐨̂𝐧𝐠 𝐂𝐚̂̀𝐧 𝐉𝐨𝐢𝐧 𝐍𝐮̛̃𝐚!!\n"
            else:
                summary_text += f"❌ 𝐊𝐡𝐨̂𝐧𝐠 𝐓𝐡𝐞̂̉ 𝐉𝐨𝐢𝐧 (𝐌𝐚̃ {error_code})\n"

            try:
                total_groups = len(self.client.fetchAllGroups().gridVerMap.keys())
            except:
                total_groups = 0

            joined_today = sum(1 for g in self.autojoin_enabled.values() if g)
            summary_text += f"\n🌅 𝐉𝐨𝐢𝐧 𝐍𝐠𝐚̀𝐲 𝐍𝐚𝐲: {joined_today}/{total_groups}"

            length_true = len(summary_text.encode("utf-16-le")) // 2

            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=length_true, style="color", color="#F7B503", auto_format=False),
                MessageStyle(offset=0, length=length_true, style="bold", auto_format=False)
            ])

            self.client.replyMessage(Message(text=summary_text, style=styles), message_object, thread_id, thread_type, ttl=60000)

        except Exception as e:
            logger.error(f"Lỗi join nhóm: {e}")

def PTA():
    return {
        'autojoins': AutoJoinHandler
    }