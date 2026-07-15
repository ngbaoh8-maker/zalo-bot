import sys
import os
import time
from zlapi.models import Message, Mention, ThreadType, MultiMsgStyle, MessageStyle
from config import ADMIN

ADMIN_ID = ADMIN

des = {
    'version': "1.2.0",
    'credits': "ngbao",
    'description': "Restart lại bot",
    'power': "Admin"
}

def is_admin(author_id):
    return author_id == ADMIN_ID

def handle_reset_command(message, message_object, thread_id, thread_type, author_id, client):
    if not is_admin(author_id):
        msg = "•🚦Quyền Lồn Biên Giới!"
        client.replyMessage(Message(text=msg), message_object, thread_id, thread_type)
        return
    try:
        restarting_styles = MultiMsgStyle([
            MessageStyle(offset=0, length=10000, style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=10000, style="bold", size="100000", auto_format=False)
        ])
        
        client.sendMessage(
            Message(
                text="🤖 Đang khởi đông lại hệ thống bot...",
                style=restarting_styles
            ),
            thread_id,
            thread_type,
            ttl=20000
        )

        with open("modules/cache/restart_info.txt", "w") as f:
            f.write(f"{thread_id}\n{thread_type.name}")

        time.sleep(0)
        python = sys.executable
        os.execl(python, python, *sys.argv)
    except Exception as e:
        client.replyMessage(Message(text=f"• Đã xảy ra lỗi khi restart bot: {str(e)}"), message_object, thread_id, thread_type)

def send_reset_success_message(client):
    try:
        if not os.path.exists("modules/cache/restart_info.txt"):
            return
        with open("modules/cache/restart_info.txt", "r") as f:
            lines = f.readlines()
            thread_id = lines[0].strip()
            thread_type = ThreadType[lines[1].strip()]
        
        success_styles = MultiMsgStyle([
            MessageStyle(offset=0, length=10000, style="color", color="#15a85f", auto_format=False),
            MessageStyle(offset=0, length=10000, style="bold", size="100000", auto_format=False)
        ])
        
        success_message = Message(
            text="🤖 Hệ thống đã được reset thành công! Bot đã hoạt động trở lại🚦.",
            style=success_styles
        )
        
        client.sendMessage(success_message, thread_id, thread_type, ttl=30000)
        os.remove("modules/cache/restart_info.txt")
    except Exception as e:
        print(f"Lỗi khi gửi tin nhắn xác nhận sau khi restart: {e}")

def PTA():
    return {
        'rs': handle_reset_command,
        'restart': handle_reset_command
    }