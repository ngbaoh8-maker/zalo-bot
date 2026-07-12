# -*- coding: utf-8 -*-
import json
import os
import time
from zlapi.models import Message, ThreadType, MultiMsgStyle, MessageStyle, Mention
from config import PREFIX


class AntiCardHandler:
    def __init__(self, client):
        self.client = client
        self.settings_card = "data/anticard_settings.json"
        self.enabled_groups = self.load_settings()
        self.card_violations = {}
        self.violation_window = 60  # thời gian tính vi phạm (giây)
        self.kick_threshold = 3     # số lần vi phạm trước khi kick

    # ------------------------ QUẢN LÝ CÀI ĐẶT ------------------------
    def load_settings(self):
        if not os.path.exists("data"):
            os.makedirs("data")
        try:
            with open(self.settings_card, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_settings(self):
        with open(self.settings_card, "w") as f:
            json.dump(self.enabled_groups, f, indent=4)

    def is_enabled(self, thread_id):
        return self.enabled_groups.get(str(thread_id), False)

    # ------------------------ HÀM TIỆN ÍCH ------------------------
    def get_user_name(self, uid):
        try:
            user_info = self.client.fetchUserInfo(uid)
            return user_info.changed_profiles.get(
                str(uid), {}).get(
                'zaloName', str(uid))
        except BaseException:
            return str(uid)

    # ------------------------ LỆNH ANTICARD ------------------------
    def handle_anticard_command(
            self,
            message_text,
            message_object,
            thread_id,
            thread_type,
            author_id):
        name = self.get_user_name(author_id)

        if str(author_id) not in self.client.ADMIN:
            rest_text = "⚠️ Bạn không có quyền sử dụng lệnh này."
            msg = f"{name}\n➜ {rest_text}"
            styles = MultiMsgStyle(
                [
                    MessageStyle(
                        offset=0,
                        length=len(name),
                        style="color",
                        color="#db342e",
                        auto_format=False),
                    MessageStyle(
                        offset=0,
                        length=len(name),
                        style="bold",
                        auto_format=False)])
            self.client.replyMessage(
                Message(
                    text=msg,
                    style=styles),
                message_object,
                thread_id,
                thread_type,
                ttl=60000)
            for r_icon in ["❌", "🚫", "🔐"]:
                self.client.sendReaction(
                    message_object,
                    r_icon,
                    thread_id,
                    thread_type,
                    reactionType=75)
            return

        parts = message_text.lower().split()
        action = parts[1] if len(parts) > 1 else ""

        if action not in ["on", "off"]:
            current_status = "Bật ✅" if self.is_enabled(thread_id) else "Tắt ❌"
            rest_text = f"🚦Hướng dẫn: {PREFIX}anticard <on/off>\n➜ Trạng thái hiện tại: {current_status}"
            msg = f"{name}\n➜ {rest_text}"
            styles = MultiMsgStyle(
                [
                    MessageStyle(
                        offset=0,
                        length=len(name),
                        style="color",
                        color="#db342e",
                        auto_format=False),
                    MessageStyle(
                        offset=0,
                        length=len(name),
                        style="bold",
                        auto_format=False)])
            self.client.replyMessage(
                Message(
                    text=msg,
                    style=styles),
                message_object,
                thread_id,
                thread_type,
                ttl=60000)
            for r_icon in ["👉", "📜", "ℹ️"]:
                self.client.sendReaction(
                    message_object,
                    r_icon,
                    thread_id,
                    thread_type,
                    reactionType=75)
            return

        thread_id_str = str(thread_id)
        if action == "on":
            if self.is_enabled(thread_id_str):
                rest_text = "Chế độ Anti-Card đã được bật trước đó. 🔄"
                reactions = ["⚠️", "🛡️", "🪪"]
            else:
                self.enabled_groups[thread_id_str] = True
                self.save_settings()
                rest_text = f"Đã bật chế độ Anti-Card. Gửi card {self.kick_threshold} lần/phút sẽ bị kick. 🛡️"
                reactions = ["✅", "🛡️", "🪪"]
        else:
            if not self.is_enabled(thread_id_str):
                rest_text = "Chế độ Anti-Card đã được tắt trước đó. 🔄"
                reactions = ["⚠️", "🪪", "🔓"]
            else:
                if thread_id_str in self.enabled_groups:
                    del self.enabled_groups[thread_id_str]
                self.save_settings()
                rest_text = "Đã tắt chế độ Anti-Card. 🔓"
                reactions = ["🚫", "🪪", "🔓"]

        msg = f"{name}\n➜ {rest_text}"
        styles = MultiMsgStyle([MessageStyle(offset=0,
                                             length=len(name),
                                             style="color",
                                             color="#db342e",
                                             auto_format=False),
                                MessageStyle(offset=0,
                                             length=len(name),
                                             style="bold",
                                             auto_format=False)])
        self.client.replyMessage(
            Message(
                text=msg,
                style=styles),
            message_object,
            thread_id,
            thread_type,
            ttl=60000)
        for r_icon in reactions:
            try:
                self.client.sendReaction(
                    message_object,
                    r_icon,
                    thread_id,
                    thread_type,
                    reactionType=75)
            except BaseException:
                pass

    # ------------------------ XỬ LÝ CARD ------------------------
    def check_and_delete_card(
            self,
            message_object,
            thread_id,
            thread_type,
            author_id):
        """
        Hàm phát hiện và xóa tin nhắn dạng 'card' (chat.carduser, chat.cardgroup, v.v.)
        """
        if not self.is_enabled(thread_id):
            return False

        msg_type = message_object.get('msgType')
        if msg_type not in ['chat.recommended']:  # kiểu card
            return False

        if self.client.is_group_admin(thread_id, author_id):
            return False
        if str(thread_id) in self.client.whitelist and str(
                author_id) in self.client.whitelist.get(str(thread_id), []):
            return False

        try:
            msg_id = message_object.get('msgId')
            cli_msg_id = message_object.get('cliMsgId')
            card_name = message_object.get(
                'content', {}).get(
                'displayName', 'Không rõ tên')
            if msg_id:
                self.client.deleteGroupMsg(
                    msg_id, author_id, cli_msg_id, thread_id)
        except Exception as e:
            self.client.logger.error(f"[AntiCard] Lỗi khi xóa card: {e}")
            return False

        now = time.time()
        if thread_id not in self.card_violations:
            self.card_violations[thread_id] = {}

        user_violations = self.card_violations[thread_id].get(
            author_id, {'count': 0, 'first_violation_time': now})

        if now - \
                user_violations['first_violation_time'] > self.violation_window:
            user_violations = {'count': 1, 'first_violation_time': now}
        else:
            user_violations['count'] += 1

        self.card_violations[thread_id][author_id] = user_violations
        current_violation_count = user_violations['count']
        user_name = self.get_user_name(author_id)
        tag_author = f"{user_name}"
        msg = ""

        if current_violation_count >= self.kick_threshold:
            try:
                self.client.blockUsersInGroup(author_id, thread_id)
                rest_text = f"📣 {tag_author} đã bị chặn khỏi nhóm do gửi card quá nhiều lần ({current_violation_count}/{self.kick_threshold})."
                del self.card_violations[thread_id][author_id]
            except Exception as e:
                rest_text = f"Đã cố gắng chặn {tag_author} nhưng thất bại. Lỗi: {e}"
            msg = f"➜ [ANTI-CARD]\n{tag_author}\n➜ {rest_text}"
        else:
            rest_text = (
                f"🚦Nhóm có quy định không được phép gửi card!\n"
                f"➜ Card đã xóa: {card_name}\n"
                f"➜ Cảnh báo lần {current_violation_count}/{self.kick_threshold}. Vui lòng không tái phạm!"
            )
            msg = f"➜ [ANTI-CARD]\n{tag_author}\n➜ {rest_text}"

        if msg:
            tag_offset = msg.find(tag_author)
            styles = MultiMsgStyle(
                [
                    MessageStyle(
                        offset=len("➜ "),
                        length=len("[ANTI-CARD]"),
                        style="color",
                        color="#db342e",
                        auto_format=False),
                    MessageStyle(
                        offset=len("➜ "),
                        length=len("[ANTI-CARD]"),
                        style="bold",
                        auto_format=False)])
            self.client.replyMessage(
                Message(
                    text=msg,
                    mention=Mention(
                        author_id,
                        offset=tag_offset,
                        length=len(tag_author)),
                    style=styles),
                message_object,
                thread_id,
                thread_type,
                ttl=120000)
        return True
        