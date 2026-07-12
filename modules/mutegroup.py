import json
import os
import threading
import time
import logging
from zlapi.models import Message, ThreadType, MultiMsgStyle, MessageStyle
from config import ADMIN, PREFIX

logger = logging.getLogger(__name__)

des = {
    'version': "1.3.1",
    'credits': "ngbao",
    'description': "Tắt thông báo tất cả các nhóm hoặc tự động tắt thông báo các nhóm mới.",
    'power': "Quản trị viên Bot"
}

BASE_DIR = "modules/cache/mutegroup_configs"
STATUS_PATH = os.path.join(BASE_DIR, "automute_status.json")
DATA_PATH = os.path.join(BASE_DIR, "automute_data.json")

os.makedirs(BASE_DIR, exist_ok=True)
json_lock_mute = threading.Lock()


def load_json_mute(key):
    path = STATUS_PATH if key == "status" else DATA_PATH
    with json_lock_mute:
        if not os.path.exists(path):
            return {"enabled": False} if key == "status" else []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"enabled": False} if key == "status" else []


def save_json_mute(key, data):
    path = STATUS_PATH if key == "status" else DATA_PATH
    with json_lock_mute:
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[AutoMute] Lỗi ghi JSON {path}: {e}")


def get_user_name(client, user_id):
    try:
        user_info = client.fetchUserInfo(str(user_id))
        return user_info.changed_profiles.get(str(user_id), {}).get('zaloName', str(user_id))
    except Exception:
        return str(user_id)


def auto_mute_task(client):
    status = load_json_mute("status")
    if not status.get("enabled", False):
        return

    try:
        muted_groups = load_json_mute("data")
        all_groups = client.fetchAllGroups()
        if not hasattr(all_groups, 'gridVerMap'):
            logger.info(
                f"[AutoMute]  Không tìm thấy nhóm nào.")
            return

        current_group_ids = [str(gid) for gid in all_groups.gridVerMap.keys()]
        new_groups_to_mute = [
            gid for gid in current_group_ids if gid not in muted_groups]

        if new_groups_to_mute:
            for group_id in new_groups_to_mute:
                try:
                    client.setMute(group_id, ThreadType.GROUP,
                                   duration=-1, is_mute=True)
                    muted_groups.append(group_id)
                    time.sleep(0)
                except Exception as e:
                    logger.error(
                        f"[AutoMute]  Lỗi khi tắt thông báo nhóm {group_id}: {e}")
            save_json_mute("data", muted_groups)
        else:
            logger.info(
                f"[AutoMute]  Không có nhóm mới nào để tắt thông báo.")

    except Exception as e:
        logger.error(
            f"[AutoMute]  Lỗi trong luồng tự động: {e}")
    finally:
        reschedule_mute_task(client)


def reschedule_mute_task(client):
    status = load_json_mute("status")
    if status.get("enabled", False):
        interval = int(status.get("interval", 120))
        if hasattr(client, '_mutegroup_timer') and client._mutegroup_timer.is_alive():
            client._mutegroup_timer.cancel()
        client._mutegroup_timer = threading.Timer(
            interval, auto_mute_task, args=(client,))
        client._mutegroup_timer.daemon = True
        client._mutegroup_timer.start()


def start_mutegroup_scheduler(client):
    if not hasattr(client, '_mutegroup_scheduler_started') or not client._mutegroup_scheduler_started:
        reschedule_mute_task(client)
        client._mutegroup_scheduler_started = True


def handle_auto_mute(parts, client, message_object, thread_id, thread_type, author_id):
    name = get_user_name(client, author_id)
    if len(parts) < 3 or parts[2].lower() not in ['on', 'off']:
        rest_text = f"📖 Sai cú pháp. Dùng: {PREFIX}mtgroup auto on/off"
        msg = f"{name}\n➜{rest_text}"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(name), style="color",
                         color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(name),
                         style="bold", auto_format=False)
        ])
        client.replyMessage(Message(text=msg, style=styles),
                            message_object, thread_id, thread_type, ttl=120000)
        return

    action = parts[2].lower()
    status = load_json_mute("status")

    if action == 'on':
        if status.get("enabled", False):
            rest_text = "✨ Chế độ tự động tắt thông báo đã được bật từ trước."
        else:
            status['enabled'] = True
            save_json_mute("status", status)
            reschedule_mute_task(client)
            rest_text = "✅ Đã bật chế độ tự động tắt thông báo cho các nhóm mới."
    else:  # action == 'off'
        if not status.get("enabled", False):
            rest_text = "✨ Chế độ tự động tắt thông báo đã được tắt từ trước."
        else:
            status['enabled'] = False
            save_json_mute("status", status)
            if hasattr(client, '_mutegroup_timer') and client._mutegroup_timer.is_alive():
                client._mutegroup_timer.cancel()
            rest_text = "❌ Đã tắt chế độ tự động tắt thông báo."

    msg = f"{name}\n➜{rest_text}"
    styles = MultiMsgStyle([
        MessageStyle(offset=0, length=len(name), style="color",
                     color="#db342e", auto_format=False),
        MessageStyle(offset=0, length=len(name),
                     style="bold", auto_format=False)
    ])
    client.replyMessage(Message(text=msg, style=styles),
                        message_object, thread_id, thread_type, ttl=120000)


def handle_mute_all(client, message_object, thread_id, thread_type, author_id):
    name = get_user_name(client, author_id)
    rest_text = "⏳ Đang bắt đầu quá trình tắt thông báo tất cả các nhóm..."
    msg = f"{name}\n➜{rest_text}"
    styles = MultiMsgStyle([
        MessageStyle(offset=0, length=len(name), style="color",
                     color="#db342e", auto_format=False),
        MessageStyle(offset=0, length=len(name),
                     style="bold", auto_format=False)
    ])
    client.replyMessage(Message(text=msg, style=styles),
                        message_object, thread_id, thread_type, ttl=120000)

    try:
        all_groups = client.fetchAllGroups()
        if not hasattr(all_groups, 'gridVerMap'):
            rest_text = "🚫 Không tìm thấy nhóm nào để tắt thông báo."
        else:
            group_ids = [str(gid) for gid in all_groups.gridVerMap.keys()]
            success_count, failed_count = 0, 0
            for group_id in group_ids:
                try:
                    client.setMute(group_id, ThreadType.GROUP,
                                   duration=-1, is_mute=True)
                    success_count += 1
                    time.sleep(0)
                except Exception as e:
                    failed_count += 1
                    logger.error(
                        f"[MuteAll]  Lỗi khi tắt thông báo nhóm {group_id}: {e}")

            muted_groups = load_json_mute("data")
            updated_muted_list = list(set(muted_groups + group_ids))
            save_json_mute("data", updated_muted_list)
            rest_text = f"✅ Hoàn tất!\n➜Đã tắt thông báo thành công: {success_count} nhóm.\n➜Thất bại: {failed_count} nhóm."
    except Exception as e:
        logger.error(
            f"[MuteAll]  Lỗi nghiêm trọng khi lấy danh sách nhóm: {e}")
        rest_text = f"❌ Đã xảy ra lỗi: {e}"

    msg = f"{name}\n➜{rest_text}"
    styles = MultiMsgStyle([
        MessageStyle(offset=0, length=len(name), style="color",
                     color="#db342e", auto_format=False),
        MessageStyle(offset=0, length=len(name),
                     style="bold", auto_format=False)
    ])
    client.replyMessage(Message(text=msg, style=styles),
                        message_object, thread_id, thread_type, ttl=120000)


def handle_mutegroup_command(message_text, message_object, thread_id, thread_type, author_id, client):
    name = get_user_name(client, author_id)
    
    if str(author_id) not in ADMIN:
        rest_text = "🚫 Chỉ admin bot mới có quyền sử dụng lệnh này."
        msg = f"{name}\n➜{rest_text}"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(name), style="color",
                         color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(name),
                         style="bold", auto_format=False)
        ])
        client.replyMessage(Message(text=msg, style=styles),
                            message_object, thread_id, thread_type, ttl=120000)
        return

    parts = message_text.lower().split()
    sub_command = parts[1] if len(parts) > 1 else None

    if sub_command == "all":
        handle_mute_all(client, message_object,
                        thread_id, thread_type, author_id)
    elif sub_command == "auto":
        handle_auto_mute(parts, client, message_object,
                         thread_id, thread_type, author_id)
    else:
        rest_text = (
            f"📖 Hướng dẫn sử dụng lệnh MuteGroup:\n"
            f"  ➜{PREFIX}mtgroup all: Tắt thông báo tất cả các nhóm bot đang tham gia.\n"
            f"  ➜{PREFIX}mtgroup auto on/off: Bật/tắt chế độ tự động tắt thông báo cho các nhóm mới."
        )
        msg = f"{name}\n➜{rest_text}"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(name), style="color",
                         color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(name),
                         style="bold", auto_format=False)
        ])
        client.replyMessage(Message(text=msg, style=styles),
                            message_object, thread_id, thread_type, ttl=120000)


def PTA():
    return {
        'mtgroup': handle_mutegroup_command
    }
