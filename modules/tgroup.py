from zlapi.models import Message, Mention
from zlapi.models import ThreadType
from config import PREFIX

des = {
    'version': "1.0.0",
    'credits': "ngbao",
    'description': "Tạo nhóm mới từ mentions",
    'power': "Admin"
}

def handle_create_group(message, message_object, thread_id, thread_type, author_id, client):
    # Tách lệnh
    parts = message.split(maxsplit=1)

    if len(parts) < 2 or not parts[1].strip():
        return client.sendMessage(
            Message(text=f"⚠️ Dùng đúng:\n{PREFIX}creategroup <Tên nhóm> @tag"),
            thread_id, thread_type
        )

    # Lấy phần còn lại sau lệnh
    content = parts[1].strip()

    # Lấy danh sách mention
    mentions = getattr(message_object, "mentions", None)

    if not mentions or len(mentions) == 0:
        return client.sendMessage(
            Message(text="⚠️ Bạn phải tag ít nhất 1 người để tạo nhóm!"),
            thread_id, thread_type
        )

    member_ids = [m.uid for m in mentions]

    # Tên nhóm sẽ là phần text không thuộc mention
    group_name = content.split("@")[0].strip()

    if not group_name:
        group_name = "Nhóm mới"

    # Thông báo tạo
    client.sendMessage(
        Message(text=f"⏳ Đang tạo nhóm **{group_name}**..."),
        thread_id, thread_type
    )

    try:
        # API Zalo tạo nhóm
        res = client.createGroup(
            name=group_name,
            participant_ids=member_ids
        )

        if not res or "group_id" not in res:
            return client.sendMessage(
                Message(text="❌ Tạo nhóm thất bại!"),
                thread_id, thread_type
            )

        group_id = res["group_id"]

        # Gửi vào nhóm mới tạo
        client.sendMessage(
            Message(text=f"🎉 Nhóm **{group_name}** đã được tạo!\nID: {group_id}"),
            thread_id=group_id,
            thread_type=ThreadType.GROUP
        )

    except Exception as e:
        client.sendMessage(
            Message(text=f"❌ Lỗi tạo nhóm: {str(e)}"),
            thread_id, thread_type
        )


def PTA():
    return {
        "creategroup": handle_create_group,
        "tgroup": handle_create_group
    }
