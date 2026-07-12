import os
import json
import logging
import time
from zlapi.models import Message, MultiMsgStyle, MessageStyle, ThreadType
from zlapi import ZaloAPIException
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import threading
from config import ADMIN, PREFIX 
logger = logging.getLogger(__name__)

MAX_INVITE_THREADS = 5
INVITE_DELAY_PER_BATCH = 0
WHITELIST_FILE = "database/keomem_whitelist.json"

des = {
    'version': "1.2.0",
    'credits': "ngbao",
    'description': "Mời toàn bộ bạn bè vào nhóm.",
    'power': "Admin"
}

def load_whitelist():
    os.makedirs(os.path.dirname(WHITELIST_FILE), exist_ok=True)
    try:
        if os.path.exists(WHITELIST_FILE):
            with open(WHITELIST_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_whitelist(whitelist_data):
    os.makedirs(os.path.dirname(WHITELIST_FILE), exist_ok=True)
    with open(WHITELIST_FILE, 'w', encoding='utf-8') as f:
        json.dump(whitelist_data, f, indent=4)

def get_user_name(client, user_id):
    try:
        user_info = client.fetchUserInfo(user_id)
        if user_info and hasattr(user_info, 'changed_profiles') and user_info.changed_profiles:
            profile = user_info.changed_profiles.get(str(user_id))
            if profile and profile.get('zaloName'):
                return profile['zaloName']
    except Exception as e:
        logger.error(f"[keomem] Lỗi lấy tên người dùng {user_id}: {e}")
    return f"UID: {user_id}"

def get_user_ids_from_message(message_object, message_text_parts):
    user_ids = []
    if message_object.mentions:
        user_ids.extend([str(m.uid) for m in message_object.mentions])
    elif message_object.quote:
        user_ids.append(str(message_object.quote.ownerId))
    
    if len(message_text_parts) > 2:
        for part in message_text_parts[2:]:
            if part.isdigit():
                user_ids.append(part)
                
    return list(set(user_ids))

class InviteManager:
    def __init__(self):
        self.success_count = 0
        self.failed_count = 0
        self.lock = threading.Lock()

    def reset(self):
        with self.lock:
            self.success_count = 0
            self.failed_count = 0

    def add_success(self, count=1):
        with self.lock:
            self.success_count += count

    def add_failed(self, count=1):
        with self.lock:
            self.failed_count += count

invite_manager = InviteManager()

def _send_invite_task(uid, thread_id, client):
    try:
        invite_result = client.addUsersToGroup([uid], thread_id)
        if invite_result and hasattr(invite_result, 'errorMembers'):
            if not invite_result.errorMembers:
                invite_manager.add_success()
            else:
                is_actual_failure = True
                if hasattr(invite_result, 'error_data') and isinstance(invite_result.error_data, dict):
                    if '166' in invite_result.error_data:
                        invite_manager.add_success()
                        is_actual_failure = False
                        logger.info(f"[AddAll] Mời UID {uid}: Đã có trong nhóm hoặc đã mời (Mã 166).")
                
                if is_actual_failure:
                    invite_manager.add_failed()
                    logger.warning(f"[AddAll] Mời UID {uid} thất bại: {invite_result.errorMembers}. Chi tiết: {getattr(invite_result, 'error_data', 'N/A')}")
        else:
            invite_manager.add_failed()
            logger.warning(f"[AddAll] Mời UID {uid} thất bại, cấu trúc phản hồi không rõ: {invite_result}")
    except ZaloAPIException as e:
        invite_manager.add_failed()
        logger.error(f"[AddAll] Lỗi Zalo API khi mời UID {uid}: {e}")
    except Exception as e:
        invite_manager.add_failed()
        logger.error(f"[AddAll] Lỗi không xác định khi mời UID {uid}: {e}")

def _execute_invite_all(message_object, thread_id, thread_type, author_id, client):
    invite_manager.reset()
    name = get_user_name(client, author_id)
    
    if thread_type != ThreadType.GROUP:
        msg = f"{name}\n➜ Lệnh này chỉ có thể sử dụng trong nhóm chat."
        client.replyMessage(Message(text=msg), message_object, thread_id, thread_type, ttl=60000)
        return

    client.replyMessage(Message(text=f"➜ {name}\nĐang lấy danh sách bạn bè và bắt đầu mời.. ⏳"), message_object, thread_id, thread_type, ttl=60000)
    
    try:
        all_friends_raw = client.fetchAllFriends()
        if not all_friends_raw:
            msg = f"{name}\n➜ Không tìm thấy bạn bè nào để mời (danh sách bạn bè trống hoặc lỗi API)."
            client.replyMessage(Message(text=msg), message_object, thread_id, thread_type, ttl=60000)
            return

        friend_uids = [friend.userId for friend in all_friends_raw if hasattr(friend, 'userId')]
        logger.info(f"[AddAll] Đã tìm thấy {len(friend_uids)} UIDs bạn bè.")

        if not friend_uids:
            msg = f"{name}\n➜ Không có bạn bè nào có UID hợp lệ để mời."
            client.replyMessage(Message(text=msg), message_object, thread_id, thread_type, ttl=60000)
            return

        whitelist = load_whitelist()
        friend_uids_to_invite = [uid for uid in friend_uids if str(uid) not in whitelist]
        
        skipped_count = len(friend_uids) - len(friend_uids_to_invite)
        if skipped_count > 0:
            logger.info(f"[AddAll] Đã bỏ qua {skipped_count} người dùng trong danh sách trắng.")

        if not friend_uids_to_invite:
            msg = f"{name}\n➜ Tất cả bạn bè của bạn đều nằm trong danh sách trắng hoặc đã có trong nhóm. Không có ai để mời."
            client.replyMessage(Message(text=msg), message_object, thread_id, thread_type, ttl=60000)
            return

        with ThreadPoolExecutor(max_workers=MAX_INVITE_THREADS) as executor:
            futures = [executor.submit(_send_invite_task, uid, thread_id, client) for uid in friend_uids_to_invite]
            for future in concurrent.futures.as_completed(futures):
                future.result()
            time.sleep(INVITE_DELAY_PER_BATCH)

        count = invite_manager.success_count + invite_manager.failed_count
        rest_text = f"Hoàn tất! ✅\nĐã mời {count}\nBỏ qua (whitelist): {skipped_count}"
        msg = f"{name}\n➜ {rest_text}"
        client.replyMessage(Message(text=msg), message_object, thread_id, thread_type, ttl=120000)

    except ZaloAPIException as e:
        msg = f"{name}\n➜ Đã xảy ra lỗi API: {e}"
        client.replyMessage(Message(text=msg), message_object, thread_id, thread_type, ttl=60000)
    except Exception as e:
        msg = f"{name}\n➜ Đã xảy ra lỗi không xác định: {e}"
        client.replyMessage(Message(text=msg), message_object, thread_id, thread_type, ttl=60000)

def _handle_whitelist_command(parts, message_object, thread_id, thread_type, author_id, client):
    sub_command = parts[1].lower()
    user_ids = get_user_ids_from_message(message_object, parts)

    if not user_ids:
        msg = f"➜ Vui lòng tag người dùng, trả lời tin nhắn của họ, hoặc cung cấp ID.\n➜ Ví dụ: {parts[0]} {sub_command} @user"
        client.replyMessage(Message(text=msg), message_object, thread_id, thread_type, ttl=60000)
        return

    whitelist = load_whitelist()
    added_users = []
    removed_users = []
    already_in_list = []
    not_in_list = []

    for uid in user_ids:
        user_name = get_user_name(client, uid)
        if sub_command == "addwl":
            if uid not in whitelist:
                whitelist.append(uid)
                added_users.append(user_name)
            else:
                already_in_list.append(user_name)
        elif sub_command == "remove":
            if uid in whitelist:
                whitelist.remove(uid)
                removed_users.append(user_name)
            else:
                not_in_list.append(user_name)

    save_whitelist(whitelist)
    
    response_parts = []
    if added_users:
        response_parts.append(f"✅ Đã thêm vào whitelist: {', '.join(added_users)}")
    if removed_users:
        response_parts.append(f"🗑️ Đã xóa khỏi whitelist: {', '.join(removed_users)}")
    if already_in_list:
        response_parts.append(f"ℹ️ Đã có trong whitelist: {', '.join(already_in_list)}")
    if not_in_list:
        response_parts.append(f"⚠️ Không tìm thấy trong whitelist: {', '.join(not_in_list)}")

    final_response = "➜ [Whitelist Manager]\n" + "\n".join(response_parts)
    client.replyMessage(Message(text=final_response), message_object, thread_id, thread_type, ttl=120000)

def handle_addall_command(message_text, message_object, thread_id, thread_type, author_id, client):
    if author_id not in ADMIN:
        client.replyMessage(Message(text="⚠️ Bạn không có quyền sử dụng lệnh này."), message_object, thread_id, thread_type, ttl=60000)
        return

    parts = message_text.split()
    sub_command = parts[1].lower() if len(parts) > 1 else None

    if sub_command in ["addwl", "remove"]:
        _handle_whitelist_command(parts, message_object, thread_id, thread_type, author_id, client)
    elif sub_command is None:
        _execute_invite_all(message_object, thread_id, thread_type, author_id, client)
    else:
        help_text = (
            f"➜ Lệnh không hợp lệ.\n"
            f"➜ Cách dùng:\n"
            f"- {parts[0]}: Mời tất cả bạn bè.\n"
            f"- {parts[0]} addwl <@tag/id>: Thêm người vào danh sách miễn mời.\n"
            f"- {parts[0]} remove <@tag/id>: Xóa người khỏi danh sách miễn mời."
        )
        client.replyMessage(Message(text=help_text), message_object, thread_id, thread_type, ttl=60000)

def PTA():
    return {'addall': handle_addall_command}