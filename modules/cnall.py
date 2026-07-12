# -*- coding: utf-8 -*-
import requests
import logging
import datetime
import time
from zlapi.models import Message, Mention, ZaloAPIException

des = {
    'version': "1.1.2",
    'credits': "ngbao",
    'description': "Quản lý lời mời kết bạn (Full Info + Index + Limit Name + Accept theo số)",
    'power': "Admin"
}

def safe_text(txt, limit=22):
    """Giới hạn độ dài tên hiển thị."""
    if not txt:
        return "Không tên"
    return txt if len(txt) <= limit else txt[:limit] + "..."

def get_friend_requests(client):
    try:
        data = client.getAddFriendsList()
        if not data:
            return []

        if "recommItems" in data:
            items = []
            for item in data["recommItems"]:
                info = item.get("dataInfo", {})
                items.append({
                    "uid": info.get("userId"),
                    "name": safe_text(info.get("displayName") or info.get("zaloName")),
                    "avatar": info.get("avatar"),
                    "message": info.get("recommInfo", {}).get("message", "")
                })
            return items

        return []

    except Exception as e:
        logging.error(f"Lỗi khi lấy danh sách lời mời: {e}")
        return []

def accept_single(client, uid, delay=0.15):
    """Chấp nhận 1 lời mời."""
    if not uid:
        return False, "UID trống"

    try:
        client.acceptFriendRequest(uid)
        time.sleep(delay)
        return True, None
    except Exception as e:
        logging.exception("Lỗi khi accept friend")
        return False, str(e)

def handle_cnall_command(message, message_object, thread_id, thread_type, author_id, client):
    args = message.strip().split()

    # MENU
    if len(args) == 1:
        menu = (
            "📌 Lệnh quản lý lời mời kết bạn\n"
            "──────────────────\n"
            "👉 ,cnall st — Kiểm tra số lời mời (Kèm danh sách)\n"
            "👉 ,cnall ac — Chấp nhận toàn bộ lời mời\n"
            "👉 ,cnall acp <số thứ tự> — Chấp nhận 1 lời mời cụ thể\n"
            "──────────────────"
        )
        client.replyMessage(
            Message(text=menu),
            message_object, thread_id, thread_type, ttl=200000
        )
        return

    # STATUS
    if args[1] == "st":
        client.replyMessage(
            Message(text="⏳ Đang kiểm tra lời mời kết bạn..."),
            message_object, thread_id, thread_type
        )
        lst = get_friend_requests(client)
        total = len(lst)

        if total == 0:
            client.replyMessage(
                Message(text="📨 Hiện không có lời mời kết bạn nào."),
                message_object, thread_id, thread_type
            )
            return

        lines = ["📋 Danh sách lời mời:\n──────────────────"]
        for i, item in enumerate(lst, 1):
            lines.append(
                f"{i}. 👤 {item['name']}\n"
                f"   🔹 UID: {item['uid']}\n"
                f"   💬 Lời nhắn: {item['message'] or 'Không có'}\n"
            )
        report = f"📨 Tổng lời mời: {total}\n" + "\n".join(lines)
        client.replyMessage(Message(text=report), message_object, thread_id, thread_type, ttl=200000)
        return

    # ACCEPT ALL
    if args[1] == "ac":
        client.replyMessage(
            Message(text="⚙️ Đang xử lý tất cả lời mời..."),
            message_object, thread_id, thread_type
        )
        lst = get_friend_requests(client)
        total = len(lst)
        if total == 0:
            client.replyMessage(
                Message(text="📨 Không có lời mời nào để xử lý."),
                message_object, thread_id, thread_type
            )
            return

        success = 0
        fail = 0
        logs = []
        for item in lst:
            ok, err = accept_single(client, item["uid"])
            if ok:
                success += 1
                logs.append(f"✔️ {item['name']} ({item['uid']}) — Thành công")
            else:
                fail += 1
                logs.append(f"❌ {item['name']} ({item['uid']}) — Thất bại: {err}")
        report = (
            "🎉 Đã xử lý tất cả lời mời!\n"
            "───────────────────\n"
            f"📨 Tổng số: {total}\n"
            f"✔️ Thành công: {success}\n"
            f"❌ Thất bại: {fail}\n"
            "───────────────────\n"
            "📋 Chi tiết:\n" + "\n".join(logs)
        )
        client.replyMessage(Message(text=report), message_object, thread_id, thread_type, ttl=200000)
        return

    # ACCEPT 1 theo số thứ tự
    if args[1] == "acp":
        if len(args) < 3 or not args[2].isdigit():
            client.replyMessage(
                Message(text="⚠️ Cú pháp: ,cnall acp <số thứ tự>"),
                message_object, thread_id, thread_type
            )
            return
        index = int(args[2]) - 1
        lst = get_friend_requests(client)
        if index < 0 or index >= len(lst):
            client.replyMessage(
                Message(text="⚠️ Số thứ tự không hợp lệ."),
                message_object, thread_id, thread_type
            )
            return
        item = lst[index]
        ok, err = accept_single(client, item["uid"])
        if ok:
            client.replyMessage(
                Message(text=f"✔️ Đã chấp nhận lời mời kb của: 👤Name: {item['name']}\n🔹UID: ({item['uid']})"),
                message_object, thread_id, thread_type
            )
        else:
            client.replyMessage(
                Message(text=f"❌ Không thể chấp nhận: {item['name']} ({item['uid']}) — {err}"),
                message_object, thread_id, thread_type
            )
        return

def PTA():
    return {
        'cnall': handle_cnall_command
    }
