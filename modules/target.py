import json
import os
import time
from zlapi.models import Message, Mention, MultiMention, MessageStyle, MultiMsgStyle, ThreadType

# Đường dẫn lưu trữ dữ liệu các đối tượng bị target
TARGET_FILE = "data/target_users.json"

des = {
    'version': "1.0.0",
    'credits': "Antigravity",
    'description': "Thêm/Xóa/Xem danh sách người dùng tự động kick khi vào nhóm",
    'power': "Quản trị viên"
}

def load_targets():
    if not os.path.exists(TARGET_FILE):
        os.makedirs(os.path.dirname(TARGET_FILE), exist_ok=True)
        with open(TARGET_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
        return {}
    try:
        with open(TARGET_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_targets(targets):
    os.makedirs(os.path.dirname(TARGET_FILE), exist_ok=True)
    with open(TARGET_FILE, "w", encoding="utf-8") as f:
        json.dump(targets, f, indent=4, ensure_ascii=False)

def check_is_admin(client, author_id, thread_id):
    """Kiểm tra quyền hạn của người dùng sử dụng lệnh (Admin Bot hoặc Admin nhóm)"""
    try:
        if hasattr(client, 'is_admin'):
            return client.is_admin(author_id, thread_id)
    except Exception:
        pass

    # Fallback kiểm tra thủ công nếu hàm client.is_admin gặp lỗi
    try:
        if str(author_id) == str(client.ADMIN) or str(author_id) in [str(adm) for adm in client.ADM]:
            return True
            
        ginfo = client.fetchGroupInfo(thread_id).gridInfoMap[thread_id]
        admins = ginfo.adminIds
        creator = ginfo.creatorId
        return str(author_id) == str(creator) or str(author_id) in [str(a) for a in admins]
    except Exception:
        return False

def get_mention_arg(mentions):
    if not mentions:
        return None
    if len(mentions) == 1:
        return mentions[0]
    return MultiMention(mentions)

def handle_target_command(message, message_object, thread_id, thread_type, author_id, client):
    # Kiểm tra quyền hạn người dùng
    if not check_is_admin(client, author_id, thread_id):
        client.replyMessage(Message(text="⚠️ Bạn không có quyền sử dụng lệnh này!"), message_object, thread_id, thread_type)
        return

    # Chỉ hoạt động trong nhóm chat
    if thread_type != ThreadType.GROUP:
        client.replyMessage(Message(text="⚠️ Lệnh này chỉ hoạt động trong nhóm chat!"), message_object, thread_id, thread_type)
        return

    targets = load_targets()
    group_id_str = str(thread_id)
    command_parts = message.strip().split()

    # Kiểm tra xem có yêu cầu xem danh sách (list) không
    if len(command_parts) >= 2 and command_parts[1].lower() in ["list", "ds", "danhsach"]:
        group_targets = targets.get(group_id_str, {})
        if not group_targets:
            client.replyMessage(Message(text="📝 Danh sách target auto kick của nhóm này đang trống."), message_object, thread_id, thread_type)
            return

        msg_text = "📝 Danh sách đối tượng auto kick trong nhóm:\n"
        mentions = []
        count = 1
        for uid, info in group_targets.items():
            name = info.get("name", f"User {uid}")
            mention_tag = f"@{name}"
            offset = len(msg_text)
            msg_text += f"{count}. {mention_tag} (UID: {uid})\n"
            mentions.append(Mention(uid=uid, offset=offset + len(f"{count}. "), length=len(mention_tag)))
            count += 1

        client.replyMessage(Message(text=msg_text, mention=get_mention_arg(mentions)), message_object, thread_id, thread_type)
        return

    # Kiểm tra hành động xóa target
    is_remove = False
    if len(command_parts) >= 2 and command_parts[1].lower() in ["remove", "xoa", "untarget", "delete", "del"]:
        is_remove = True

    # Tìm UID của đối tượng cần xử lý (qua mention, qua quote, hoặc UID trực tiếp)
    user_ids = []
    if message_object.mentions:
        user_ids = [str(mention.uid) for mention in message_object.mentions]
    elif message_object.quote:
        user_ids = [str(message_object.quote.ownerId)]

    if not user_ids:
        # Tìm kiếm xem có truyền UID dạng số dài trực tiếp không
        for part in command_parts[1:]:
            if part.isdigit() and len(part) >= 10:
                user_ids.append(part)
                break

    # Nếu không tìm thấy đối tượng, hiển thị hướng dẫn
    if not user_ids:
        help_text = (
            "⚙️ Hướng dẫn lệnh TARGET (Auto Kick):\n"
            "1. Thêm target: `!target @mention` hoặc reply tin nhắn của người cần kick.\n"
            "2. Xóa target: `!target remove @mention` hoặc `!target remove [reply]`.\n"
            "3. Xem danh sách: `!target list`.\n"
            "⚠️ Bot cần có quyền Admin nhóm để đá thành viên!"
        )
        client.replyMessage(Message(text=help_text), message_object, thread_id, thread_type)
        return

    group_targets = targets.get(group_id_str, {})
    success_users = []
    already_users = []
    not_found_users = []

    for uid in user_ids:
        if is_remove:
            if uid in group_targets:
                name = group_targets[uid].get("name", "User")
                del group_targets[uid]
                success_users.append((uid, name))
            else:
                not_found_users.append(uid)
        else:
            try:
                user_info = client.fetchUserInfo(uid)
                user_name = user_info.changed_profiles[uid].zaloName
            except Exception:
                user_name = f"User {uid}"

            if uid in group_targets:
                already_users.append((uid, user_name))
            else:
                group_targets[uid] = {
                    "name": user_name,
                    "added_by": str(author_id),
                    "timestamp": time.time()
                }
                success_users.append((uid, user_name))

    targets[group_id_str] = group_targets
    save_targets(targets)

    # Gửi tin nhắn phản hồi kết quả
    reply_text = ""
    mentions = []

    if is_remove:
        if success_users:
            reply_text += "✅ Đã xóa khỏi danh sách target auto kick của nhóm:\n"
            for uid, name in success_users:
                tag = f"@{name}"
                offset = len(reply_text)
                reply_text += f"➜ {tag} (UID: {uid})\n"
                mentions.append(Mention(uid=uid, offset=offset + len("➜ "), length=len(tag)))
        if not_found_users:
            reply_text += f"⚠️ Không tìm thấy UID {', '.join(not_found_users)} trong danh sách target của nhóm."
    else:
        if success_users:
            reply_text += "📌 Đã ghim đối tượng vào danh sách auto kick của nhóm:\n"
            for uid, name in success_users:
                tag = f"@{name}"
                offset = len(reply_text)
                reply_text += f"➜ {tag} (UID: {uid})\n"
                mentions.append(Mention(uid=uid, offset=offset + len("➜ "), length=len(tag)))
            reply_text += "🚪 Khi người này vào nhóm, bot sẽ tự động kick."
        if already_users:
            if reply_text:
                reply_text += "\n"
            reply_text += "⚠️ Đối tượng đã có sẵn trong danh sách target:\n"
            for uid, name in already_users:
                tag = f"@{name}"
                offset = len(reply_text)
                reply_text += f"➜ {tag} (UID: {uid})\n"
                mentions.append(Mention(uid=uid, offset=offset + len("➜ "), length=len(tag)))

    client.replyMessage(Message(text=reply_text, mention=get_mention_arg(mentions)), message_object, thread_id, thread_type)

def PTA():
    return {
        'target': handle_target_command,
        'tager': handle_target_command
    }
