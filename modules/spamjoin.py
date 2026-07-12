import json
import os
import time
import threading
from zlapi.models import Message, ThreadType, ZaloAPIException
from config import PREFIX, ADMIN

des = {
    'version': "1.0.0",
    'credits': "ngbao",
    'description': "Join – Out liên tục không gửi gì.",
    'power': "Admin"
}

joinout_tasks = {}


def _joinout_loop(client, group_link, stop_event, admin_thread_id, admin_thread_type):

    def notify_admin_and_stop(error_message):
        full_message = f"🔴 [JoinOut] Đã dừng!\n➜ Nhóm: {group_link}\n➜ Lý do: {error_message}"
        client.send(Message(text=full_message), admin_thread_id, admin_thread_type)
        stop_event.set()
        if group_link in joinout_tasks:
            del joinout_tasks[group_link]

    while not stop_event.is_set():
        group_id = None
        try:
            # Tham gia nhóm
            print(f"[JoinOut] Đang tham gia nhóm: {group_link}")
            data_join = client.joinGroup(group_link)

            if data_join and 'error_code' in data_join:
                err = data_join['error_code']
                if err not in [0, 240, 178, 1022]:
                    notify_admin_and_stop(f"Lỗi join nhóm (code {err})")
                    return

            # Lấy group_id
            group_info_data = client.getIDsGroup(group_link)
            if not group_info_data or 'groupId' not in group_info_data:
                notify_admin_and_stop("Không lấy được ID nhóm.")
                return

            group_id = group_info_data['groupId']

        except ZaloAPIException as e:
            notify_admin_and_stop(f"Lỗi API khi join ({e.message})")
            return

        # Rời nhóm ngay lập tức
        try:
            if group_id:
                client.leaveGroup(group_id, imei=client._imei)
        except:
            pass

        time.sleep(0)  # auto loop

    print(f"[JoinOut] Đã dừng tác vụ cho: {group_link}")


def handle_joinout_command(message, message_object, thread_id, thread_type, author_id, client):
    if str(author_id) not in ADMIN:
        client.replyMessage(Message(text="Bạn không có quyền dùng lệnh này."), message_object, thread_id, thread_type)
        return

    parts = message.split()
    if len(parts) < 3:
        client.replyMessage(Message(text=f"➜ Dùng: {PREFIX}joinout <link> <on/off>"), message_object, thread_id, thread_type)
        return

    group_link = parts[1]
    action = parts[2].lower()

    if not group_link.startswith("https://zalo.me/g/"):
        client.replyMessage(Message(text="Link nhóm không hợp lệ."), message_object, thread_id, thread_type)
        return

    if action == "on":
        if group_link in joinout_tasks:
            client.replyMessage(Message(text="Tác vụ đã chạy trước đó."), message_object, thread_id, thread_type)
            return

        stop_event = threading.Event()
        joinout_tasks[group_link] = stop_event

        thread = threading.Thread(
            target=_joinout_loop,
            args=(client, group_link, stop_event, thread_id, thread_type),
            daemon=True
        )
        thread.start()

        client.replyMessage(Message(text=f"Đã bật JoinOut không gửi gì:\n{group_link}"), message_object, thread_id, thread_type)

    elif action == "off":
        if group_link not in joinout_tasks:
            client.replyMessage(Message(text="Không có tác vụ đang chạy."), message_object, thread_id, thread_type)
            return

        joinout_tasks[group_link].set()
        del joinout_tasks[group_link]

        client.replyMessage(Message(text=f"Đã tắt JoinOut:\n{group_link}"), message_object, thread_id, thread_type)

    else:
        client.replyMessage(Message(text="Hành động phải là on hoặc off."), message_object, thread_id, thread_type)


def PTA():
    return {
        'joinout': handle_joinout_command
    }