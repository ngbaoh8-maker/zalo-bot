from zlapi.models import Message, MultiMsgStyle, MessageStyle
from logging_utils import Logging
from config import PREFIX 
logger = Logging()

class AntiSpamHandler:
    def __init__(self, client):
        self.client = client

    def handle_antispam_command(self, message, message_object, thread_id, thread_type, author_id):
        command = message.lower().split()
        user_info = self.client.fetchUserInfo(author_id)
        author_info = user_info.changed_profiles.get(str(author_id), {}) if user_info and user_info.changed_profiles else {}
        name = author_info.get('zaloName', 'Không xác định')

        if len(command) != 2:
            rest_text = f"Ê cu! Dùng đúng cú pháp {PREFIX}antisp on/off hộ cái nhá! 🙄"
            msg = f"{name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
            ])
            self.client.replyMessage(
                Message(text=msg, style=styles),
                message_object, thread_id, thread_type, ttl=30000
            )
            self.client.sendReaction(message_object, "👉", thread_id, thread_type, reactionType=75)
            return

        if str(author_id) not in self.client.ADMIN:
            rest_text = "Xin lỗi bạn iu nha, lệnh này chỉ admin mới được dùng thôi 🥲"
            msg = f"{name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
            ])
            self.client.replyMessage(
                Message(text=msg, style=styles),
                message_object, thread_id, thread_type, ttl=30000
            )
            self.client.sendReaction(message_object, "🔒", thread_id, thread_type, reactionType=75)
            return

        action = command[1]
        current_state = self.client.spam_enabled.get(thread_id, False)

        if action == 'on':
            if current_state:
                rest_text = "Chế độ chống spam đã bật sẵn rồi mà, cần bật lại đâu! 😎"
                msg = f"{name}\n➜{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                    MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object, thread_id, thread_type, ttl=30000
                )
                self.client.sendReaction(message_object, "🔄", thread_id, thread_type, reactionType=75)
            else:
                self.client.spam_enabled[thread_id] = True
                rest_text = " đã bật chế độ chống spam rồi đó, căng đét! 💪"
                msg = f"{name}\n➜{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                    MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object, thread_id, thread_type, ttl=30000
                )
                self.client.sendReaction(message_object, "✅", thread_id, thread_type, reactionType=75)
        elif action == 'off':
            if not current_state:
                rest_text = "Chế độ chống spam đã tắt sẵn rồi, tắt thêm chi nữa! 😜"
                msg = f"{name}\n➜{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                    MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object, thread_id, thread_type, ttl=30000
                )
                self.client.sendReaction(message_object, "🔄", thread_id, thread_type, reactionType=75)
            else:
                self.client.spam_enabled[thread_id] = False
                rest_text = " đã tắt chống spam rồi, ae quẩy thoải mái đi! 🎉"
                msg = f"{name}\n➜{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                    MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object, thread_id, thread_type, ttl=30000
                )
                self.client.sendReaction(message_object, "💨", thread_id, thread_type, reactionType=75)
        else:
            rest_text = f"Lệnh sai be bét rồi! Phải là {PREFIX}antisp on/off cơ mà 🤔"
            msg = f"{name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
            ])
            self.client.replyMessage(
                Message(text=msg, style=styles),
                message_object, thread_id, thread_type, ttl=30000
            )
            self.client.sendReaction(message_object, "❌", thread_id, thread_type, reactionType=75)

        self.client.save_spam_settings()