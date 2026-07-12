from zlapi.models import Message
from config import ADMIN

des = {
    'version': "1.6.1",
    'credits': "ngbao",
    'description': "Thêm key / Gỡ key",
    'power': "Quản Trị Viên Bot"
}

BOT_OWNER = "1262618053229730684"


def handle_add_admin_command(message, message_object, thread_id, thread_type, author_id, client):
    if str(author_id) != BOT_OWNER:
        client.sendMessage(Message(text="🚫Tuổi lồn đòi lấy key!"), thread_id, thread_type, ttl=30000)
        return

    text = message.split()
    group_info = client.fetchGroupInfo(thread_id)
    if not group_info:
        client.sendMessage(Message(text="⚠️ Không thể lấy thông tin nhóm."), thread_id, thread_type, ttl=30000)
        return

    group_data = group_info.gridInfoMap.get(thread_id)
    if not group_data:
        client.sendMessage(Message(text="⚠️ Không tìm thấy thông tin nhóm."), thread_id, thread_type, ttl=30000)
        return

    user_ids = []
    if message_object.mentions:
        user_ids = [mention['uid'] for mention in message_object.mentions]
        try:
            client.sendReaction(message_object, "🗝️", thread_id, thread_type)
        except:
            pass
    elif message_object.quote:
        user_ids = [str(message_object.quote.ownerId)]
        try:
            client.sendReaction(message_object, "🗝️", thread_id, thread_type)
        except:
            pass
    else:
        if len(text) < 2:
            try:
                client.sendReaction(message_object, "🔑", thread_id, thread_type)
            except:
                pass
            client.sendMessage(Message(text="⚠️ Vui lòng tag, reply hoặc nhập UID người cần làm phó nhóm."), thread_id, thread_type, ttl=30000)
            return
        user_ids = text[1:]
        try:
            client.sendReaction(message_object, "🔑", thread_id, thread_type)
        except:
            pass

    user_names = []
    for uid in user_ids:
        try:
            user_info = client.fetchUserInfo(uid)
            if isinstance(user_info, dict) and 'changed_profiles' in user_info:
                user_data = user_info['changed_profiles'].get(uid, {})
                user_names.append(user_data.get('zaloName', 'Không xác định'))
            else:
                user_names.append("Người dùng không xác định")
        except:
            user_names.append("Người dùng không xác định")

    try:
        if hasattr(client, 'addGroupAdmins'):
            client.addGroupAdmins(user_ids, thread_id)
            client.sendMessage(Message(text=f"Đã thêm {', '.join(user_names)} làm phó nhóm ✅"), thread_id, thread_type, ttl=30000)
        else:
            client.sendMessage(Message(text="⚠️ API không hỗ trợ hành động này."), thread_id, thread_type, ttl=30000)
    except Exception as e:
        client.sendMessage(Message(text=f"❌ Lỗi khi thêm phó nhóm: {str(e)}"), thread_id, thread_type, ttl=30000)


def handle_remove_admin_command(message, message_object, thread_id, thread_type, author_id, client):
    if str(author_id) != BOT_OWNER:
        client.sendMessage(Message(text="🚫 Chỉ chủ bot mới được dùng lệnh này!"), thread_id, thread_type, ttl=30000)
        return

    text = message.split()
    group_info = client.fetchGroupInfo(thread_id)
    if not group_info:
        client.sendMessage(Message(text="⚠️ Không thể lấy thông tin nhóm."), thread_id, thread_type, ttl=30000)
        return

    group_data = group_info.gridInfoMap.get(thread_id)
    if not group_data:
        client.sendMessage(Message(text="⚠️ Không tìm thấy thông tin nhóm."), thread_id, thread_type, ttl=30000)
        return

    user_ids = []
    if message_object.mentions:
        user_ids = [mention['uid'] for mention in message_object.mentions]
        try:
            client.sendReaction(message_object, "🧹", thread_id, thread_type)
        except:
            pass
    elif message_object.quote:
        user_ids = [str(message_object.quote.ownerId)]
        try:
            client.sendReaction(message_object, "🧹", thread_id, thread_type)
        except:
            pass
    else:
        if len(text) < 2:
            try:
                client.sendReaction(message_object, "🧹", thread_id, thread_type)
            except:
                pass
            client.sendMessage(Message(text="⚠️ Vui lòng tag, reply hoặc nhập UID người cần gỡ phó nhóm."), thread_id, thread_type, ttl=30000)
            return
        user_ids = text[1:]
        try:
            client.sendReaction(message_object, "🧹", thread_id, thread_type)
        except:
            pass

    user_names = []
    for uid in user_ids:
        try:
            user_info = client.fetchUserInfo(uid)
            if isinstance(user_info, dict) and 'changed_profiles' in user_info:
                user_data = user_info['changed_profiles'].get(uid, {})
                user_names.append(user_data.get('zaloName', 'Không xác định'))
            else:
                user_names.append("Người dùng không xác định")
        except:
            user_names.append("Người dùng không xác định")

    try:
        if hasattr(client, 'removeGroupAdmins'):
            client.removeGroupAdmins(user_ids, thread_id)
            client.sendMessage(Message(text=f"Đã gỡ quyền phó nhóm của {', '.join(user_names)} ✅."), thread_id, thread_type, ttl=30000)
        else:
            client.sendMessage(Message(text="⚠️ API không hỗ trợ hành động này."), thread_id, thread_type, ttl=30000)
    except Exception as e:
        client.sendMessage(Message(text=f"❌ Lỗi khi gỡ phó nhóm: {str(e)}"), thread_id, thread_type, ttl=30000)


def PTA():
    return {
        'addkey': handle_add_admin_command,
        'unkey': handle_remove_admin_command
    }