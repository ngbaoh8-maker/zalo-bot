import time
import json
import os
from zlapi.models import Message, MultiMsgStyle, MessageStyle
from config import ADMIN, PREFIX

des = {
    'version': '1.3.0',
    'credits': "ngbao",
    'description': 'Quét và thoát các nhóm không cho chat.',
    'power': "Admin"
}

WHITELIST_FILE_PATH = 'modules/cache/outgrp_whitelist.json'
GROUPS_PER_PAGE = 30

def is_admin(author_id):
    return author_id == ADMIN

def load_whitelist():
    if not os.path.exists(WHITELIST_FILE_PATH):
        return []
    try:
        with open(WHITELIST_FILE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_whitelist(data):
    os.makedirs(os.path.dirname(WHITELIST_FILE_PATH), exist_ok=True)
    with open(WHITELIST_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def send_paginated_message(client, text, style, message_object, thread_id, thread_type):
    max_length = 3000
    if len(text) <= max_length:
        client.replyMessage(Message(text=text, style=style), message_object, thread_id, thread_type, ttl=320000)
    else:
        parts = [text[i:i+max_length] for i in range(0, len(text), max_length)]
        for i, part in enumerate(parts):
            if i > 0: part = f"[Tiếp theo...]\n{part}"
            client.replyMessage(Message(text=part, style=style), message_object, thread_id, thread_type, ttl=320000)
            time.sleep(1)

def send_group_list(client, groups, style, message_object, thread_id, thread_type, title):
    if not groups:
        return

    total_groups = len(groups)
    for page_idx in range(0, total_groups, GROUPS_PER_PAGE):
        page_groups = groups[page_idx:page_idx + GROUPS_PER_PAGE]
        page_num = page_idx // GROUPS_PER_PAGE + 1
        total_pages = (total_groups + GROUPS_PER_PAGE - 1) // GROUPS_PER_PAGE

        header = f"➜ {title.upper()} (Trang {page_num}/{total_pages}, Tổng: {total_groups} nhóm)\n\n"
        lines = [f"{page_idx + i + 1}. {g.get('name', 'N/A')}\n(🆔: {g.get('id', 'N/A')})" for i, g in enumerate(page_groups)]
        report_text = header + "\n".join(lines)
        send_paginated_message(client, report_text, style, message_object, thread_id, thread_type)
        time.sleep(1)
        
def handle_outgrp_command(message, message_object, thread_id, thread_type, author_id, client):
    styles = MultiMsgStyle([MessageStyle(offset=0, length=10000, style="font", size="10", auto_format=False)])

    if not is_admin(author_id):
        client.replyMessage(Message(text="Bạn không có quyền sử dụng lệnh này.", style=styles), message_object, thread_id, thread_type, ttl=60000)
        return

    command_parts = message.strip().split()
    sub_command = command_parts[1] if len(command_parts) > 1 else "scan"
    
    whitelist = load_whitelist()

    if sub_command == "list":
        if not whitelist: reply_text = "📝 Danh sách whitelist hiện đang trống."
        else:
            list_str = "\n".join(f"{i+1}. {group_id}" for i, group_id in enumerate(whitelist))
            reply_text = f"📝 DANH SÁCH WHITELIST ({len(whitelist)} NHÓM):\n\n{list_str}"
        client.replyMessage(Message(text=reply_text, style=styles), message_object, thread_id, thread_type, ttl=120000)
        return

    elif sub_command == "add":
        if len(command_parts) < 3:
            client.replyMessage(Message(text=f"⚠️ Vui lòng cung cấp ID nhóm để thêm. Ví dụ:\n{PREFIX}outgrp add 123456", style=styles), message_object, thread_id, thread_type, ttl=60000)
            return
        group_id_to_add = command_parts[2]
        if group_id_to_add in whitelist: reply_text = f"❌ Nhóm ID {group_id_to_add} đã có trong whitelist."
        else:
            whitelist.append(group_id_to_add)
            save_whitelist(whitelist)
            reply_text = f"✅ Đã thêm nhóm ID {group_id_to_add} vào whitelist."
        client.replyMessage(Message(text=reply_text, style=styles), message_object, thread_id, thread_type, ttl=60000)
        return

    elif sub_command == "remove":
        if len(command_parts) < 3:
            client.replyMessage(Message(text=f"⚠️ Vui lòng cung cấp ID nhóm để xóa. Ví dụ:\n{PREFIX}outgrp remove 123456", style=styles), message_object, thread_id, thread_type, ttl=60000)
            return
        group_id_to_remove = command_parts[2]
        if group_id_to_remove not in whitelist: reply_text = f"❌ Không tìm thấy nhóm ID {group_id_to_remove} trong whitelist."
        else:
            whitelist.remove(group_id_to_remove)
            save_whitelist(whitelist)
            reply_text = f"✅ Đã xóa nhóm ID {group_id_to_remove} khỏi whitelist."
        client.replyMessage(Message(text=reply_text, style=styles), message_object, thread_id, thread_type, ttl=60000)
        return

    elif sub_command == "help":
        help_text = (
            "📖 HƯỚNG DẪN LỆNH OUTGRP\n\n"
            f"➜ {PREFIX}outgrp: Quét thử (dry run) các nhóm không cho chat.\n"
            f"➜ {PREFIX}outgrp --force: Quét và thoát thật các nhóm tìm thấy.\n"
            f"➜ {PREFIX}outgrp list: Xem danh sách whitelist.\n"
            f"➜ {PREFIX}outgrp add [id]: Thêm nhóm vào whitelist.\n"
            f"➜ {PREFIX}outgrp remove [id]: Xóa nhóm khỏi whitelist.\n"
            f"➜ {PREFIX}outgrp help: Xem hướng dẫn này."
        )
        client.replyMessage(Message(text=help_text, style=styles), message_object, thread_id, thread_type, ttl=60000)
        return

    elif sub_command == "scan" or "--force" in command_parts:
        is_dry_run = '--force' not in command_parts
        
        initial_reply = "🔍 Bắt đầu quét các nhóm...\n"
        if is_dry_run: initial_reply += f"» Chế độ: Quét thử (dry run). Sẽ không thoát nhóm.\n» Dùng {PREFIX}outgrp --force để thực thi thoát nhóm."
        else: initial_reply += "» Chế độ: Quét và thoát thật (live run)."
        if whitelist: initial_reply += f"\n» Whitelist: Sẽ bỏ qua {len(whitelist)} nhóm đã lưu."
        client.replyMessage(Message(text=initial_reply, style=styles), message_object, thread_id, thread_type, ttl=60000)
        time.sleep(2)

        try:
            results = client.leaveReadOnlyGroups(dry_run=is_dry_run, whitelist_ids=whitelist)
            
            groups_to_leave = results.get('left_groups', [])
            bot_admin_groups = results.get('bot_is_admin_groups', [])

            action_word = "quét" if is_dry_run else "thoát"

            if not groups_to_leave and not bot_admin_groups:
                final_summary = "✅ Quá trình hoàn tất. Không tìm thấy nhóm nào phù hợp để xử lý."
                client.replyMessage(Message(text=final_summary, style=styles), message_object, thread_id, thread_type, ttl=120000)
                return

            send_group_list(client, groups_to_leave, styles, message_object, thread_id, thread_type, f"NHÓM {action_word}")
            
            send_group_list(client, bot_admin_groups, styles, message_object, thread_id, thread_type, "NHÓM ĐƯỢC GIỮ LẠI BOT LÀ ADMIN GROUP")

            final_summary = f"✅ Quá trình hoàn tất. {action_word.capitalize()} thành công tổng cộng {len(groups_to_leave)} nhóm."
            client.replyMessage(Message(text=final_summary, style=styles), message_object, thread_id, thread_type, ttl=120000)

        except Exception as e:
            error_message = f"❌ Đã xảy ra lỗi khi thực thi lệnh: {str(e)}"
            client.replyMessage(Message(text=error_message, style=styles), message_object, thread_id, thread_type, ttl=60000)
    else:
        client.replyMessage(Message(text=f"Lệnh không hợp lệ. Dùng {PREFIX}outgrp help để xem hướng dẫn.", style=styles), message_object, thread_id, thread_type, ttl=60000)

def PTA():
    return {
        'outgrp': handle_outgrp_command
    }