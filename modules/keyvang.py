from zlapi.models import Message
from config import PREFIX, ADMIN

des = {
    'version': "1.0.2",
    'credits': "ngbao",
    'description': "Chuyển chủ nhóm",
    'power': "Admin & Chủ nhóm"
}

def _get_mentioned_uid(message_object):
    mentions = getattr(message_object, "mentions", None)
    if not mentions:
        return None

    if isinstance(mentions, list):
        return getattr(mentions[0], "uid", None)

    if isinstance(mentions, dict):
        return next(iter(mentions.keys()), None)

    return None


def handle_owner_command(message_text, message_object, thread_id, thread_type, author_id, client):
    try:
        g = client.fetchGroupInfo(thread_id).gridInfoMap.get(str(thread_id))
        if not g:
            return

        if str(author_id) != str(ADMIN):
            client.replyMessage(
                Message(text="Chỉ Admin Bot mới được sử dụng lệnh này."),
                message_object, thread_id, thread_type, ttl=60000
            )
            return

        if str(client.uid) != str(g.creatorId):
            client.replyMessage(
                Message(text="❌ Bot hiện không phải là chủ nhóm nên không thể chuyển quyền cho người khác."),
                message_object, thread_id, thread_type, ttl=60000
            )
            return

        if message_text.lower().strip() == f"{PREFIX}keyvang me":
            target_id = author_id
        else:
            target_id = _get_mentioned_uid(message_object)

        if not target_id:
            client.replyMessage(
                Message(text=f"Dùng: {PREFIX}keyvang @user hoặc {PREFIX}keyvang me để chuyển trưởng nhóm"),
                message_object, thread_id, thread_type, ttl=60000
            )
            return

        admin_ids = getattr(g, "adminIds", [])
        if str(target_id) not in [str(a) for a in admin_ids]:
            client.replyMessage(
                Message(text="Người dùng phải là admin trước khi lên chủ."),
                message_object, thread_id, thread_type, ttl=60000
            )
            return

        client.changeGroupOwner(str(target_id), str(thread_id))

        client.replyMessage(
            Message(text="👑 Đã chuyển quyền chủ nhóm thành công."),
            message_object, thread_id, thread_type, ttl=60000
        )

    except Exception as e:
        client.replyMessage(
            Message(text=f"❌ Lỗi: {e}"),
            message_object, thread_id, thread_type, ttl=60000
        )


def PTA():
    return {
        'keyvang': handle_owner_command
    }
