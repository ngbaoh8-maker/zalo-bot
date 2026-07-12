import json
import os
from zlapi.models import Message

des = {
    'version': "1.0.2",
    'credits': "ngbao",
    'description': "Bật/tắt event cho nhóm",
    'power': "Quản trị viên Bot"
}

ALLOWED_GROUPS_FILE = "data/event_setting.json"

def load_allowed_groups():
    if os.path.exists(ALLOWED_GROUPS_FILE):
        with open(ALLOWED_GROUPS_FILE, "r") as f:
            return json.load(f)
    return {"groups": []}

def save_allowed_groups(allowed_groups):
    with open(ALLOWED_GROUPS_FILE, "w") as f:
        json.dump(allowed_groups, f, indent=4)

def handle_event(message, message_object, thread_id, thread_type, author_id, client):
    command_parts = message.split()

    if len(command_parts) != 2:
        response_message = "• Sử dụng: .event set/unset."
    else:
        action = command_parts[1].lower()
        allowed_groups_data = load_allowed_groups()
        allowed_groups = allowed_groups_data.get("groups", [])

        if action == "set":
            if thread_id not in allowed_groups:
                allowed_groups.append(thread_id)
                allowed_groups_data["groups"] = allowed_groups
                save_allowed_groups(allowed_groups_data)
                response_message = "• Đã bật thông báo sự kiện cho nhóm này."
            else:
                response_message = "• Nhóm này đã được bật thông báo sự kiện trước đó."
        elif action == "unset":
            if thread_id in allowed_groups:
                allowed_groups.remove(thread_id)
                allowed_groups_data["groups"] = allowed_groups
                save_allowed_groups(allowed_groups_data)
                response_message = "• Đã tắt thông báo sự kiện cho nhóm này."
            else:
                response_message = "• Nhóm này đã được tắt thông báo sự kiện trước đó rồi."
        else:
            response_message = "• Sử dụng: .event set/unset."

    message_to_send = Message(text=response_message)
    client.replyMessage(message_to_send, message_object, thread_id, thread_type)

def PTA():
    return {
        'event': handle_event
    }