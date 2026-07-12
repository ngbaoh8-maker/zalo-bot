import json
import os
import time
import threading
from zlapi.models import Message, ThreadType, ZaloAPIException, Mention, MultiMention
from config import PREFIX, ADMIN

des = {
    'version': "1.8.0",
    'credits': "ngbao",
    'description': "Spam JL.",
    'power': "Admin"
}

STICKER_LIST = [
    {"sticker_type": 3, "sticker_id": "23311", "category_id": "10425"},
    {"sticker_type": 3, "sticker_id": "27598", "category_id": "10746"},
]
spam_tasks = {}
current_sticker_index = 0
current_lag_index = 0
index_lock = threading.Lock()


def _load_lag_messages():
    try:
        with open("spam/lag.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError: return None

def _create_hidden_all_mention(client, group_id, text_message):
    try:
        group_info = client.fetchGroupInfo(group_id).gridInfoMap.get(str(group_id), {})
        members_list = group_info.get('memVerList', [])
        if not members_list: return Message(text=text_message)
        text_to_send, mentions, offset = text_message, [], len(text_message)
        for member_str in members_list:
            parts = member_str.split('_', 1)
            if len(parts) != 2: continue
            user_id, user_name = parts
            mentions.append(Mention(uid=user_id, offset=offset, length=len(user_name) + 1, auto_format=False))
            offset += len(user_name) + 2
        return Message(text=text_to_send, mention=MultiMention(mentions)) if mentions else Message(text=text_to_send)
    except Exception as e:
        print(f"[SpamVIP-All] Lỗi tạo mention: {e}")
        return Message(text=text_message)

def _spam_loop(client, group_link, sticker_list, lag_list, stop_event, admin_thread_id, admin_thread_type):
    global current_sticker_index, current_lag_index

    def notify_admin_and_stop(error_message):
        full_message = f"🔴 [SpamVIP] Tác vụ đã dừng!\n➜ Nhóm: {group_link}\n➜ Lý do: {error_message}"
        client.send(Message(text=full_message), admin_thread_id, admin_thread_type, ttl=220000)
        stop_event.set()
        if group_link in spam_tasks:
            del spam_tasks[group_link]

    while not stop_event.is_set():
        group_id = None
        try:
            try:
                print(f"[SpamVIP] Đang tham gia nhóm: {group_link}")
                data_join = client.joinGroup(group_link)
                
                if data_join and 'error_code' in data_join:
                    error_code = data_join['error_code']
                    if error_code not in [0, 240, 178, 1022]:
                        error_messages = {
                            175: "Bot đã bị chặn khỏi nhóm.",
                            227: "Link nhóm không tồn tại.",
                            1003: "Nhóm đã đầy thành viên.",
                            1004: "Nhóm đạt giới hạn thành viên."
                        }
                        error_msg = error_messages.get(error_code, f"Lỗi không xác định khi join (code: {error_code})")
                        notify_admin_and_stop(error_msg)
                        return

                print("[SpamVIP] Yêu cầu tham gia đã được gửi. Chờ để lấy ID...")
                time.sleep(0)
                group_info_data = client.getIDsGroup(group_link)
                if not group_info_data or 'groupId' not in group_info_data:
                    raise ZaloAPIException("Không thể lấy ID nhóm sau khi join.")
                group_id = group_info_data['groupId']
                print(f"[SpamVIP] Đã vào/xác định được nhóm: {group_id}")
                time.sleep(0)
            except ZaloAPIException as e:
                notify_admin_and_stop(f"Lỗi API khi tham gia nhóm ({e.message}).")
                return

            if stop_event.is_set(): break

            with index_lock:
                try:
                    if sticker_list:
                        sticker = sticker_list[current_sticker_index]
                        client.sendSticker(sticker['sticker_type'], sticker['sticker_id'], sticker['category_id'], group_id, ThreadType.GROUP)
                        current_sticker_index = (current_sticker_index + 1) % len(sticker_list)
                        time.sleep(0.3)

                    if lag_list:
                        for _ in range(2):
                            if stop_event.is_set(): break
                            text = lag_list[current_lag_index]
                            msg_obj = _create_hidden_all_mention(client, group_id, text)
                            client.send(msg_obj, thread_id=group_id, thread_type=ThreadType.GROUP)
                            current_lag_index = (current_lag_index + 1) % len(lag_list)
                            time.sleep(0.3)
                
                except ZaloAPIException as e:
                    notify_admin_and_stop(f"Bot đã bị chặn khi đang gửi tin ({e.message}).")
                    return

        except Exception as e:
            print(f"[SpamVIP] Lỗi không xác định trong vòng lặp chính: {e}")
        
        finally:
            if group_id:
                try:
                    print(f"[SpamVIP] Rời nhóm {group_id}")
                    client.leaveGroup(group_id, imei=client._imei)
                except: pass
            
            if not stop_event.is_set():
                print("[SpamVIP] Chờ 5 giây trước khi lặp lại...")
                time.sleep(0)

    print(f"[SpamVIP] Đã dừng tác vụ cho: {group_link}")


def handle_spamvip_command(message, message_object, thread_id, thread_type, author_id, client):
    if str(author_id) not in ADMIN:
        client.replyMessage(Message(text="➜ Bạn không có quyền sử dụng lệnh này."), message_object, thread_id, thread_type, ttl=60000)
        return

    parts = message.split()
    if len(parts) < 3:
        client.replyMessage(Message(text=f"➜ Sai cú pháp. Dùng: {PREFIX}spamvip <link nhóm> <on/off>"), message_object, thread_id, thread_type, ttl=60000)
        return

    group_link = parts[1]
    action = parts[2].lower()

    if not group_link.startswith("https://zalo.me/g/"):
        client.replyMessage(Message(text="➜ Link nhóm Zalo không hợp lệ."), message_object, thread_id, thread_type, ttl=60000)
        return

    if action == "on":
        if group_link in spam_tasks:
            client.replyMessage(Message(text="➜ Tác vụ spam cho link này đã được bật trước đó."), message_object, thread_id, thread_type, ttl=60000)
            return

        lag_list = _load_lag_messages()
        if lag_list is None:
            client.replyMessage(Message(text="➜ Lỗi: Không tìm thấy file spam/lag.txt"), message_object, thread_id, thread_type, ttl=60000)
            return
        if not STICKER_LIST and not lag_list:
            client.replyMessage(Message(text="➜ Lỗi: Cả danh sách sticker và file lag.txt đều rỗng."), message_object, thread_id, thread_type, ttl=60000)
            return

        stop_event = threading.Event()
        spam_tasks[group_link] = stop_event

        admin_thread_id = thread_id
        admin_thread_type = thread_type

        spam_thread = threading.Thread(
            target=_spam_loop,
            args=(client, group_link, STICKER_LIST, lag_list, stop_event, admin_thread_id, admin_thread_type),
            daemon=True
        )
        spam_thread.start()
        client.replyMessage(Message(text=f"➜ ✅ Đã bắt đầu tác vụ spam VIP vào nhóm:\n{group_link}"), message_object, thread_id, thread_type, ttl=60000)

    elif action == "off":
        if group_link not in spam_tasks:
            client.replyMessage(Message(text="➜ Không có spam nào đang chạy cho link này."), message_object, thread_id, thread_type, ttl=60000)
            return

        stop_event = spam_tasks[group_link]
        stop_event.set()
        del spam_tasks[group_link]
        client.replyMessage(Message(text=f"➜ 🚫 Đã gửi yêu cầu dừng spam VIP cho nhóm:\n{group_link}"), message_object, thread_id, thread_type, ttl=60000)
    else:
        client.replyMessage(Message(text=f"➜ Sai hành động. Dùng 'on' hoặc 'off'."), message_object, thread_id, thread_type, ttl=60000)

def PTA():
    return {'spamvip': handle_spamvip_command}