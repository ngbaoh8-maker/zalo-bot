import os
import time
import threading
import random
import json
from zlapi.models import Message
from config import PREFIX, ADMIN

des = {
    'version': "1.7.0",
    'credits': "ngbao",
    'description': "Treo Ngôn 5 Màu",
    'power': "Quản trị viên Bot"
}

COLORS = ['DB342E', '15A85F', 'F27806', 'F7B503', '0000FF']
treo_threads = {}
treo_flags = {}
TTL_CMD = 60000
TTL_TREO = 1800000

def multiline_styles(full_text):
    lines = full_text.split("\n")
    styles = []
    offset = 0
    for i, line in enumerate(lines):
        color = COLORS[i % len(COLORS)]
        styles.append({
            "start": offset,
            "len": len(line),
            "st": f"b,c_{color},f_100"
        })
        offset += len(line) + 1
    return json.dumps({"styles": styles, "ver": 0})

def style_name_only(full_text, name):
    start = full_text.find(name)
    if start == -1:
        return None
    styles = [{
        "start": start,
        "len": len(name),
        "st": "b,c_DB342E"
    }]
    return json.dumps({"styles": styles, "ver": 0})

def handle_treo_command(message, message_object, thread_id, thread_type, author_id, client):
    global treo_threads, treo_flags
    user_info = client.fetchUserInfo(author_id)
    author_info = user_info.changed_profiles.get(str(author_id), {}) if user_info and user_info.changed_profiles else {}
    name = author_info.get('zaloName', 'Không xác định')
    if str(author_id) != str(ADMIN):
        return
    parts = message.split()
    if len(parts) < 2:
        help_text = (
            f"{name}\n"
            f"➜ • {PREFIX}treo on – Bắt đầu gửi nội dung từ treo.txt\n"
            f"   • {PREFIX}treo stop – Dừng gửi"
        )
        style = style_name_only(help_text, name)
        client.replyMessage(
            Message(text=help_text, style=style),
            message_object, thread_id, thread_type, ttl=TTL_CMD
        )
        return
    action = parts[1].lower()
    if action == "stop":
        if thread_id in treo_flags and treo_flags[thread_id]:
            treo_flags[thread_id] = False
            client.send(Message(text="✅ Treo đã dừng."), thread_id, thread_type, ttl=TTL_CMD)
        else:
            client.send(Message(text="⚠️ Hiện không có tiến trình treo nào đang chạy."),
                        thread_id, thread_type, ttl=TTL_CMD)
        return
    if action == "on":
        try:
            with open("ngon.txt", "r", encoding="utf-8") as f:
                content = f.read().strip()
        except FileNotFoundError:
            client.send(Message(text="❌ Không tìm thấy file ngon.txt!"),
                        thread_id, thread_type, ttl=TTL_CMD)
            return
        if not content:
            client.send(Message(text="⚠️ File ngon.txt trống, không có nội dung để gửi."),
                        thread_id, thread_type, ttl=TTL_CMD)
            return
        if thread_id in treo_flags and treo_flags[thread_id]:
            client.send(Message(text="⚠️ Treo đang chạy rồi!"), thread_id, thread_type, ttl=TTL_CMD)
            return
        treo_flags[thread_id] = True
        client.send(Message(text="🚀 Treo đang chạy..."), thread_id, thread_type, ttl=TTL_CMD)
        def loop_send():
            while treo_flags.get(thread_id, False):
                try:
                    style = multiline_styles(content)
                    client.send(
                        Message(text=content, style=style),
                        thread_id, thread_type, ttl=TTL_TREO
                    )
                except Exception as e:
                    print(f"Lỗi khi gửi ngon: {e}")
                time.sleep(30)
        t = threading.Thread(target=loop_send, daemon=True)
        treo_threads[thread_id] = t
        t.start()
        return

def PTA():
    return {}