from zlapi.models import Message, ZaloAPIException, ThreadType, Mention, MultiMention
import time

des = {
    'version': "1.0.1",
    'credits': "ngbao",
    'description': "Lệnh tham gia nhóm",
    'power': "Admin"
}

def handle_join_command(message, message_object, thread_id, thread_type, author_id, client):
    print(f"[DEBUG] Nhận lệnh từ: {author_id}, Nội dung: {message}")

    try:
        parts = message.split(" ", 1)
        if len(parts) < 2:
            print("[DEBUG] Không có link nhóm trong lệnh.")
            client.replyMessage(Message(text="Link đâu? Đùa bố à"), message_object, thread_id, thread_type, ttl=86400000)
            return

        group_link = parts[1].strip()
        print(f"[DEBUG] Link nhóm nhận được: {group_link}")

        if not group_link.startswith("https://zalo.me/"):
            print("[DEBUG] Link nhóm không hợp lệ.")
            client.replyMessage(Message(text="Link nhóm không hợp lệ."), message_object, thread_id, thread_type, ttl=86400000)
            return

        print("[DEBUG] Đang gửi yêu cầu tham gia nhóm...")
        data_join = client.joinGroup(group_link)
        print(f"[DEBUG] Phản hồi từ joinGroup: {data_join}")

        if data_join:
            if 'error_code' in data_join:
                error_code = data_join['error_code']
                msg_err = {
                    0: "Đã gửi yêu cầu tham gia nhóm thành công!",
                    240: "Cần được duyệt để tham gia nhóm.",
                    178: "Bạn đã là thành viên của nhóm này rồi.",
                    227: "Nhóm không tồn tại.",
                    175: "Không thể tham gia nhóm (bị chặn hoặc lỗi).",
                    1003: "Nhóm đã đầy thành viên.",
                    1004: "Nhóm đạt giới hạn thành viên.",
                    1022: "Đã gửi yêu cầu trước đó."
                }
                msg = msg_err.get(error_code, f"Lỗi: {data_join}")
            else:
                msg = f"{data_join}"
        else:
            msg = "Lỗi không xác định khi tham gia nhóm."

        print(f"[DEBUG] Tin nhắn phản hồi khi tham gia nhóm: {msg}")
        client.replyMessage(Message(text=msg), message_object, thread_id, thread_type, ttl=86400000)

        print("[DEBUG] Đang lấy ID và thông tin nhóm từ link...")
        group_info_response = client.getIDsGroup(group_link)
        print(f"[DEBUG] Phản hồi từ getIDsGroup: {group_info_response}")

        if not group_info_response or not isinstance(group_info_response, dict):
            print("[ERROR] API không trả về dữ liệu hợp lệ.")
            return

        group_id = group_info_response.get('groupId')
        print(f"[DEBUG] ID nhóm lấy được: {group_id}")

        if not group_id:
            print("[ERROR] Không tìm thấy 'groupId' trong phản hồi.")
            return

        print("[DEBUG] Lấy danh sách quản trị viên nhóm...")
        admins = group_info_response.get('adminIds', [])
        creator_id = group_info_response.get('creatorId')
        if creator_id and creator_id not in admins:
            admins.append(creator_id)

        admins = list(set(admins))
        print(f"[DEBUG] Danh sách admin: {admins}")

        if not admins:
            print("[WARNING] Không tìm thấy admin nào trong nhóm.")
            return

        text = "Xin Chào Mấy ní t là ngbao Dz Cte nè :-))"
        mentions = []
        offset = len(text)

        for admin_id in admins:
            mention = Mention(uid=admin_id, offset=offset, length=1, auto_format=False)
            mentions.append(mention)
            text += "@ "
            offset += 2

        multi_mention = MultiMention(mentions)

        print(f"[DEBUG] Tin nhắn sẽ gửi vào nhóm {group_id}: {text}")
        client.send(
            Message(text=text, mention=multi_mention),
            thread_id=group_id,
            thread_type=ThreadType.GROUP
        )
        print(f"[DEBUG] Đã gửi tin nhắn thành công tới nhóm {group_id}.")

    except ZaloAPIException as e:
        print(f"[ERROR] Zalo API Exception: {e}")
    except Exception as e:
        print(f"[ERROR] Lỗi không xác định: {e}")

def PTA():
    return {
        'join': handle_join_command
    }
