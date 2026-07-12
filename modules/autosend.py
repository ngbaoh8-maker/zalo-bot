import json
import os
from zlapi.models import Message, MultiMsgStyle, MessageStyle
from config import PREFIX, ADMIN

des = {
    'version': "1.0.2",
    'credits': "ngbao",
    'description': "Bật/tắt auto send tin nhắn cho nhóm",
    'power': "Quản trị viên Bot"
}

ALLOWED_GROUPS_FILE = "modules/cache/sendtask_autosend.json"
ADMIN_ID = ADMIN

def is_admin(author_id):
    return str(author_id) == ADMIN_ID

def load_allowed_groups():
    try:
        if os.path.exists(ALLOWED_GROUPS_FILE):
            with open(ALLOWED_GROUPS_FILE, "r") as f:
                return json.load(f)
    except json.JSONDecodeError:
        return {"groups": []}
    return {"groups": []}

def save_allowed_groups(allowed_groups):
    try:
        with open(ALLOWED_GROUPS_FILE, "w") as f:
            json.dump(allowed_groups, f, indent=4)
    except Exception as e:
        print(f"Error saving allowed groups: {e}")

def handle_autosend_command(message, message_object, thread_id, thread_type, author_id, client):
    user_info = client.fetchUserInfo(author_id)
    author_info = user_info.changed_profiles.get(str(author_id), {}) if user_info and user_info.changed_profiles else {}
    name = author_info.get('zaloName', 'Không xác định')

    if not is_admin(author_id):
        rest_text = "Bạn không đủ quyền hạn để sử dụng lệnh này! 😠"
        msg = f"{name}\n➜{rest_text}"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
        ])
        client.replyMessage(
            Message(text=msg, style=styles),
            message_object, thread_id, thread_type, ttl=5000
        )
        return

    command_parts = message.split()
    if len(command_parts) != 2:
        rest_text = (
            f"Hướng dẫn sử dụng lệnh {PREFIX}autosend:\n"
            f"• {PREFIX}autosend on: Bật AutoSend cho nhóm.\n"
            f"• {PREFIX}autosend off: Tắt AutoSend cho nhóm.\n"
            f"Lưu ý: Chỉ admin mới có quyền sử dụng lệnh này."
        )
        msg = f"{name}\n➜{rest_text}"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
        ])
        client.replyMessage(
            Message(text=msg, style=styles),
            message_object, thread_id, thread_type, ttl=30000
        )
        return

    action = command_parts[1].lower()
    allowed_groups_data = load_allowed_groups()
    allowed_groups = allowed_groups_data.get("groups", [])

    if action == "on":
        if thread_id not in allowed_groups:
            allowed_groups.append(thread_id)
            allowed_groups_data["groups"] = allowed_groups
            save_allowed_groups(allowed_groups_data)
            rest_text = "Đã bật AutoSend cho nhóm này! 🚦"
        else:
            rest_text = "Nhóm này đã được bật AutoSend trước đó! 🔄"
    elif action == "off":
        if thread_id in allowed_groups:
            allowed_groups.remove(thread_id)
            allowed_groups_data["groups"] = allowed_groups
            save_allowed_groups(allowed_groups_data)
            rest_text = "Đã tắt AutoSend cho nhóm này! 🚨"
        else:
            rest_text = "Nhóm này đã được tắt AutoSend trước đó rồi! 🔄"
    else:
        rest_text = f"Sử dụng: {PREFIX}autosend on/off"

    msg = f"{name}\n➜{rest_text}"
    styles = MultiMsgStyle([
        MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
        MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
    ])
    client.replyMessage(
        Message(text=msg, style=styles),
        message_object, thread_id, thread_type, ttl=5000
    )

def PTA():
    return {
        'autosend': handle_autosend_command
    }