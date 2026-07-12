import json
from zlapi.models import *
from config import ADMIN
import os
import time
from zlapi.models import MultiMsgStyle, MessageStyle

des = {
    'version': '1.0.7',
    'credits': "ngbao",
    'description': 'List group',
    'power': "Admin"
}

def is_admin(author_id):
    return author_id == ADMIN

def load_duyetbox_data():
    file_path = 'modules/cache/duyetboxdata.json'
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r') as f:
        try:
            data = json.load(f)
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []

def handle_lgr_command(message, message_object, thread_id, thread_type, author_id, client):

    styles = MultiMsgStyle([
        MessageStyle(offset=0, length=10000, style="font", size="10", auto_format=False),
    ])
    
    # Check admin
    if not is_admin(author_id):
        response_message = "❌ Bạn không có quyền sử dụng lệnh này."
        client.replyMessage(
            Message(text=response_message, style=styles),
            message_object, thread_id, thread_type
        )
        return

    # Load group list
    try:
        all_groups = client.fetchAllGroups().gridVerMap.keys()
    except Exception as e:
        client.replyMessage(
            Message(text=f"⚠️ Lỗi khi lấy danh sách nhóm: {e}", style=styles),
            message_object, thread_id, thread_type
        )
        return

    group_links = []
    excluded_group_id = "4009464343109121790"

    for group_id in all_groups:
        if group_id == excluded_group_id:
            continue

        # Get group name
        try:
            group_info = client.fetchGroupInfo(group_id).gridInfoMap.get(group_id, {})
            group_name = group_info.get("name", "Không xác định")
        except:
            group_name = "Không xác định"

        # Try create NEW link
        invite_link = None
        try:
            invite_link = client.createGroupInviteLink(group_id)
            time.sleep(0.2)
        except:
            invite_link = None

        # If cannot create → try get old link
        if not invite_link:
            try:
                invite_link = client.fetchGroupInviteLink(group_id)
            except:
                invite_link = None

        # If group disables share link → still no link
        if not invite_link:
            invite_link = "❌ Nhóm này không bật chia sẻ link."

        group_links.append(
            f"📍 {group_name}\n🔗 {invite_link}"
        )

    # Build response
    if not group_links:
        success_message = "• Bạn không có nhóm nào để hiển thị."
    else:
        success_message = "[ DANH SÁCH LINK NHÓM ]\n\n" + "\n\n".join(group_links)

    # Send chunked messages
    max_len = 3000
    if len(success_message) <= max_len:
        client.replyMessage(Message(text=success_message, style=styles),
                            message_object, thread_id, thread_type)
    else:
        parts = [success_message[i:i+max_len] for i in range(0, len(success_message), max_len)]
        for part in parts:
            client.replyMessage(Message(text=part, style=styles),
                                message_object, thread_id, thread_type)


def PTA():
    return {
        'lgr': handle_lgr_command
    }
