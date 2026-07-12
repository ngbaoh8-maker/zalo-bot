import json
from zlapi.models import Message, MultiMsgStyle, MessageStyle
from logging_utils import Logging
from config import PREFIX

logger = Logging()

class LockBotHandler:
    def __init__(self, client):
        self.client = client
        self.client.locked_users = self.load_locked_users()

    def load_locked_users(self):
        try:
            with open('locked_users.json', 'r') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading locked_users.json: {e}")
            return []

    def save_locked_users(self):
        try:
            with open('locked_users.json', 'w') as file:
                json.dump(self.client.locked_users, file, indent=4)
        except Exception as e:
            logger.error(f"Error saving locked_users.json: {e}")

    def handle_lockbot_command(self, message_text, message_object, thread_id, thread_type, author_id):
        user_info = self.client.fetchUserInfo(author_id)
        author_info = user_info.changed_profiles.get(str(author_id), {}) if user_info and user_info.changed_profiles else {}
        name = author_info.get('zaloName', 'Không xác định')

        if str(author_id) != self.client.ADMIN:
            rest_text = "Quyền lồn biên giới! 🙄"
            msg = f"{name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
            ])
            self.client.replyMessage(
                Message(text=msg, style=styles),
                message_object, thread_id, thread_type, ttl=10000
            )
            self.client.sendReaction(message_object, "🔒", thread_id, thread_type, reactionType=75)
            return

        user_ids_to_lock = []

        if message_object.mentions:
            user_ids_to_lock.extend([mention['uid'] for mention in message_object.mentions])
        else:
            try:
                potential_user_id = message_text.split()[-1]
                if potential_user_id.isdigit():
                    user_ids_to_lock.append(potential_user_id)
            except:
                rest_text = f"Cú pháp sai lè rồi! Dùng: {PREFIX}lbot @tag hoặc {PREFIX}lbot <user_id>"
                msg = f"{name}\n➜{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                    MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object, thread_id, thread_type, ttl=10000
                )
                self.client.sendReaction(message_object, "🤦‍♂️", thread_id, thread_type, reactionType=75)
                return

        if not user_ids_to_lock:
            rest_text = "Tag người hoặc nhập ID người cần lock đi chứ! 🤨"
            msg = f"{name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
            ])
            self.client.replyMessage(
                Message(text=msg, style=styles),
                message_object, thread_id, thread_type, ttl=10000
            )
            self.client.sendReaction(message_object, "🤦‍♂️", thread_id, thread_type, reactionType=75)
            return

        for user_id_to_lock in user_ids_to_lock:
            try:
                user_info = self.client.fetchUserInfo(user_id_to_lock).changed_profiles.get(str(user_id_to_lock), {})
                user_name = user_info.get('zaloName', 'Không xác định')
            except (IndexError, KeyError):
                rest_text = f"Ủa? Không tìm thấy user ID {user_id_to_lock} này luôn á! 🤷‍♂️"
                msg = f"{name}\n➜{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                    MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object, thread_id, thread_type, ttl=10000
                )
                self.client.sendReaction(message_object, "❓", thread_id, thread_type, reactionType=75)
                continue

            if user_id_to_lock == self.client.ADMIN:
                rest_text = "Ê nhóc! Định khóa mõm cả Admin hả? To gan! 😠"
                msg = f"{name}\n➜{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                    MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object, thread_id, thread_type, ttl=10000
                )
                self.client.sendReaction(message_object, "🤬", thread_id, thread_type, reactionType=75)
                continue

            if user_id_to_lock not in self.client.locked_users:
                self.client.locked_users.append(user_id_to_lock)
                self.save_locked_users()
                
                # Styled message with admin name, message, and user name at the bottom
                rest_text = f"Đã khóa thành công! 🔒"
                msg = f"{name}\n➜{rest_text}\n{user_name}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                    MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object, thread_id, thread_type, ttl=10000
                )
                self.client.sendReaction(message_object, "✅", thread_id, thread_type, reactionType=75)
                logger.warning(f"Đã lock {user_name} - {user_id_to_lock}")
            else:
                # Styled message for already locked user
                rest_text = f"User này đã bị khóa trước đó! 😴"
                msg = f"{name}\n➜{rest_text}\n{user_name}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                    MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object, thread_id, thread_type, ttl=10000
                )
                self.client.sendReaction(message_object, "🔄", thread_id, thread_type, reactionType=75)

    def handle_unlockbot_command(self, message_text, message_object, thread_id, thread_type, author_id):
        # Lấy tên user thực hiện lệnh
        user_info = self.client.fetchUserInfo(author_id)
        author_info = user_info.changed_profiles.get(str(author_id), {}) if user_info and user_info.changed_profiles else {}
        name = author_info.get('zaloName', 'Không xác định')

        if str(author_id) != self.client.ADMIN:
            rest_text = "No way! Không đủ trình unlock đâu! 🙄"
            msg = f"{name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
            ])
            self.client.replyMessage(
                Message(text=msg, style=styles),
                message_object, thread_id, thread_type, ttl=10000
            )
            self.client.sendReaction(message_object, "🔓", thread_id, thread_type, reactionType=75)
            return

        user_ids_to_unlock = []

        if message_object.mentions:
            user_ids_to_unlock.extend([mention['uid'] for mention in message_object.mentions])
        else:
            try:
                potential_user_id = message_text.split()[-1]
                if potential_user_id.isdigit():
                    user_ids_to_unlock.append(potential_user_id)
            except:
                rest_text = f"Sai cú pháp unlock rồi! Dùng: {PREFIX}unlbot @tag hoặc {PREFIX}unlbot <user_id>"
                msg = f"{name}\n➜{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                    MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object, thread_id, thread_type, ttl=10000
                )
                self.client.sendReaction(message_object, "🤦‍♂️", thread_id, thread_type, reactionType=75)
                return

        if not user_ids_to_unlock:
            rest_text = "Tag người hoặc nhập ID người cần thả ra đi chứ! 🤨"
            msg = f"{name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
            ])
            self.client.replyMessage(
                Message(text=msg, style=styles),
                message_object, thread_id, thread_type, ttl=10000
            )
            self.client.sendReaction(message_object, "🤦‍♂️", thread_id, thread_type, reactionType=75)
            return

        for user_id_to_unlock in user_ids_to_unlock:
            try:
                user_info = self.client.fetchUserInfo(user_id_to_unlock).changed_profiles.get(str(user_id_to_unlock), {})
                user_name = user_info.get('zaloName', 'Không xác định')
            except (IndexError, KeyError):
                rest_text = f"Hình như không thấy user ID {user_id_to_unlock} này á! 🤷‍♂️"
                msg = f"{name}\n➜{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                    MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object, thread_id, thread_type, ttl=10000
                )
                self.client.sendReaction(message_object, "❓", thread_id, thread_type, reactionType=75)
                continue

            if user_id_to_unlock in self.client.locked_users:
                self.client.locked_users.remove(user_id_to_unlock)
                self.save_locked_users()
                
                
                rest_text = f"Đã thả xích thành công! 🔓"
                msg = f"{name}\n➜{rest_text}\n{user_name}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                    MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object, thread_id, thread_type, ttl=10000
                )
                self.client.sendReaction(message_object, "✅", thread_id, thread_type, reactionType=75)
                logger.warning(f"Đã unlock {user_name} - {user_id_to_unlock}")
            else:
                rest_text = f"User này có bị nhốt đâu mà đòi thả hả Đại Ka? 🤔"
                msg = f"{name}\n➜{rest_text}\n{user_name}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                    MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object, thread_id, thread_type, ttl=10000
                )
                self.client.sendReaction(message_object, "🔄", thread_id, thread_type, reactionType=75)

    def handle_listlockbot_command(self, message_text, message_object, thread_id, thread_type, author_id):
        user_info = self.client.fetchUserInfo(author_id)
        author_info = user_info.changed_profiles.get(str(author_id), {}) if user_info and user_info.changed_profiles else {}
        name = author_info.get('zaloName', 'Không xác định')

        if str(author_id) != self.client.ADMIN:
            rest_text = "Em chưa đủ level để xem danh sách! 🙄"
            msg = f"{name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
            ])
            self.client.replyMessage(
                Message(text=msg, style=styles),
                message_object, thread_id, thread_type, ttl=10000
            )
            self.client.sendReaction(message_object, "🔒", thread_id, thread_type, reactionType=75)
            return

        if not self.client.locked_users:
            rest_text = "Danh sách trong sạch, chưa có ai bị giam cầm cả! 😎"
            msg = f"{name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
            ])
            self.client.replyMessage(
                Message(text=msg, style=styles),
                message_object, thread_id, thread_type, ttl=10000
            )
            self.client.sendReaction(message_object, "✅", thread_id, thread_type, reactionType=75)
            return

        locked_users_info = []
        for user_id in self.client.locked_users:
            try:
                user_info = self.client.fetchUserInfo(user_id).changed_profiles.get(str(user_id), {})
                user_name = user_info.get('zaloName', 'Không xác định')
                locked_users_info.append(f"• {user_name} ({user_id})")
            except (IndexError, KeyError):
                locked_users_info.append(f"• Không xác định ({user_id})")
                logger.warning(f"Failed to fetch user info for ID {user_id}")

        list_message = "\n".join(locked_users_info) if locked_users_info else "Danh sách rỗng! 😎"
        rest_text = f"Danh sách con sen đang bị xích nè:\n\n{list_message}"
        msg = f"{name}\n➜{rest_text}"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
        ])
        self.client.replyMessage(
            Message(text=msg, style=styles),
            message_object, thread_id, thread_type, ttl=10000
        )
        self.client.sendReaction(message_object, "📜", thread_id, thread_type, reactionType=75)
        logger.info(f"Displayed locked users list: {list_message}")