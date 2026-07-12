from zlapi.models import Message
from config import PREFIX

des = {
    'version': "1.0.0",
    'credits': "ngbao",
    'description': "Thêm, xoá key bạc trong nhóm",
    'power': "Quản trị viên Bot"
}

def _get_mentioned_uid(message_object):
    mentions = getattr(message_object, "mentions", None)
    if not mentions:
        return None

    if isinstance(mentions, list):
        m0 = mentions[0]
        return getattr(m0, "uid", None)

    if isinstance(mentions, dict):
        return next(iter(mentions.keys()), None)

    return None


def handle_key_command(message_text, message_object, thread_id, thread_type, author_id, client):
    try:
        if not client.is_allowed_author(author_id):
            return

        parts = message_text.strip().split()
        action = parts[1].lower() if len(parts) > 1 else ""

        if action not in ["add", "delete", "del", "remove"]:
            client.replyMessage(
                Message(text=f"Dùng: {PREFIX}key <add/delele> @user"),
                message_object, thread_id, thread_type, ttl=60000
            )
            return

        target_id = _get_mentioned_uid(message_object)
        if not target_id:
            client.replyMessage(
                Message(text="Tag người cần nâng/hạ key (@user)"),
                message_object, thread_id, thread_type, ttl=60000
            )
            return

        group_id = str(thread_id)

        if action == "add":
            client.addGroupAdmins([str(target_id)], group_id)
            client.replyMessage(
                Message(text=""),
                message_object, thread_id, thread_type, ttl=60000
            )
            return

        client.removeGroupAdmins([str(target_id)], group_id)
        client.replyMessage(
            Message(text=""),
            message_object, thread_id, thread_type, ttl=60000
        )

    except Exception as e:
        client.replyMessage(
            Message(text=f"Lỗi: {e}"),
            message_object, thread_id, thread_type, ttl=60000
        )


def PTA():
    return {
        'key': handle_key_command
    }
