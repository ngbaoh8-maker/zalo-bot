# -*- coding: utf-8 -*-
import os
import time
import threading
import requests
from zlapi.models import Message
from config import PREFIX, ADMIN

des = {
    'version': "3.0.1",
    'credits': "ngbao",
    'description': "Treo ảnh tự động — tất cả chức năng gói trong 1 lệnh, tin nhắn tự thu hồi 2 phút.",
    'power': "Quản trị viên Bot"
}

is_relay_running = False
relay_image_path = "relay_image.jpg"
relay_text = "🖼️ Ảnh treo đang hoạt động..."

def is_admin(author_id):
    return author_id in ADMIN

def safe_mkdir(path):
    folder = os.path.dirname(path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder)

def extract_reply_image_url(message_object):
    reply_candidates = [
        getattr(message_object, "replied_to", None),
        getattr(message_object, "messageReply", None),
    ]
    for reply in reply_candidates:
        if not reply:
            continue
        inner_msg = getattr(reply, "message", None)
        attachments = getattr(inner_msg, "attachments", None) or getattr(reply, "attachments", None)
        if not attachments:
            continue
        for a in attachments:
            if hasattr(a, "url") and a.url and a.url.lower().endswith((".jpg", ".jpeg", ".png")):
                return a.url
    return None

def process_image_pipeline(image_url, save_path="relay_image.jpg"):
    try:
        safe_mkdir(save_path)
        res = requests.get(image_url, timeout=10)
        if res.status_code != 200:
            return False, f"❌ Không tải được ảnh (mã {res.status_code})"
        with open(save_path, "wb") as f:
            f.write(res.content)
        if os.path.getsize(save_path) == 0:
            return False, "❌ Ảnh tải về rỗng hoặc link lỗi."
        return True, "✅ Ảnh đã được tải và lưu thành công!"
    except Exception as e:
        return False, f"❌ Lỗi khi tải ảnh: {e}"

def stop_relay(client, message_object, thread_id, thread_type, notify=True):
    global is_relay_running
    if not is_relay_running:
        if notify:
            client.replyMessage(Message(text="⚠️ Hiện không có ảnh nào đang treo."), message_object, thread_id, thread_type, ttl=120000)
        return
    is_relay_running = False
    if notify:
        client.replyMessage(Message(text="🛑 Đã **tạm dừng treo ảnh.**"), message_object, thread_id, thread_type, ttl=120000)

def start_relay(client, message_object, thread_id, thread_type):
    global is_relay_running, relay_image_path, relay_text
    if not os.path.exists(relay_image_path):
        client.replyMessage(Message(text="⚠️ Chưa đặt ảnh treo nào."), message_object, thread_id, thread_type, ttl=120000)
        return
    if is_relay_running:
        client.replyMessage(Message(text="⚠️ Ảnh treo đã bật rồi."), message_object, thread_id, thread_type, ttl=120000)
        return

    is_relay_running = True
    def loop():
        while is_relay_running:
            try:
                client.sendLocalImage(
                    relay_image_path,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    message=Message(text=relay_text)
                )
                time.sleep(3)
            except Exception as e:
                client.send(Message(text=f"❌ Lỗi gửi ảnh treo: {e}"), thread_id, thread_type)
                break
    threading.Thread(target=loop, daemon=True).start()
    client.replyMessage(Message(text=f"✅ Đã bật treo ảnh!\n🖼️ Nội dung: {relay_text}"),
                        message_object, thread_id, thread_type, ttl=120000)

def handle_treoanh_command(message, message_object, thread_id, thread_type, author_id, client):
    global relay_text, relay_image_path, is_relay_running

    if not is_admin(author_id):
        client.replyMessage(Message(text="❌ Bạn không có quyền dùng lệnh này."), message_object, thread_id, thread_type, ttl=120000)
        return

    parts = message.split(maxsplit=2)
    if len(parts) < 2:
        msg = (
            f"⚙️ Dùng: {PREFIX}treoanh on / stop / set / text / info / img [link hoặc reply ảnh]\n\n"
            "🖼️ Ví dụ:\n"
            f"• {PREFIX}treoanh set → Bật lại ảnh treo hiện tại\n"
            f"• {PREFIX}treoanh text Hello mọi người → Đổi chữ treo\n"
            f"• {PREFIX}treoanh img (reply ảnh) → Đặt ảnh mới\n"
            f"• {PREFIX}treoanh on → Bật treo lại\n"
            f"• {PREFIX}treoanh stop → Tạm dừng\n"
            f"• {PREFIX}treoanh info → Xem trạng thái hiện tại"
        )
        client.replyMessage(Message(text=msg), message_object, thread_id, thread_type, ttl=120000)
        return

    action = parts[1].lower()

    if action == "on":
        start_relay(client, message_object, thread_id, thread_type)
        return

    if action in ["off", "stop"]:
        stop_relay(client, message_object, thread_id, thread_type)
        return

    if action == "info":
        status = "✅ Đang treo" if is_relay_running else "⏸️ Đang dừng"
        has_img = "✅ Có" if os.path.exists(relay_image_path) else "❌ Không"
        msg = (
            f"📊 **Trạng thái ảnh treo:**\n"
            f"• Trạng thái: {status}\n"
            f"• Ảnh có sẵn: {has_img}\n"
            f"• Nội dung: {relay_text}"
        )
        client.replyMessage(Message(text=msg), message_object, thread_id, thread_type, ttl=120000)
        return

    if action == "text":
        if len(parts) < 3:
            client.replyMessage(Message(text="❌ Hãy nhập nội dung muốn hiển thị."), message_object, thread_id, thread_type, ttl=120000)
            return
        relay_text = f"🖼️ {parts[2]}"
        client.replyMessage(Message(text=f"✅ Đã đổi nội dung treo thành:\n{relay_text}"),
                            message_object, thread_id, thread_type, ttl=120000)
        return

    if action in ["img", "set"]:
        image_url = extract_reply_image_url(message_object)
        if not image_url and len(parts) >= 3:
            maybe_link = parts[2]
            if maybe_link.startswith("http") and any(x in maybe_link for x in [".jpg", ".jpeg", ".png"]):
                image_url = maybe_link
        if not image_url:
            client.replyMessage(Message(text="❌ Hãy reply 1 ảnh hoặc nhập link ảnh hợp lệ."),
                                message_object, thread_id, thread_type, ttl=120000)
            return
        ok, msg = process_image_pipeline(image_url, relay_image_path)
        client.replyMessage(Message(text=msg), message_object, thread_id, thread_type, ttl=120000)
        if ok:
            start_relay(client, message_object, thread_id, thread_type)
        return

def PTA():
    return {
        'treoanh': handle_treoanh_command
    }