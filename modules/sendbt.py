import json
import random
import time
from zlapi.models import Message

des = {
    'version': "1.2.0",
    'credits': "ngbao",
    'description': "Send text và spam ẩn",
    'power': "Quản trị viên bot"
}

COLOR_LIST = [
    "DB342E", 
    "15A85F", 
    "F27806",  
    "F7B503", 
    "2E86C1", 
    "8E44AD",  
    "D35400"   
]


def multi_color_styles(full_text, size=1, bold=True):
    styles = []
    offset = 0
    for ch in full_text:
        if ch.strip() == "":
            offset += 1
            continue

        color = random.choice(COLOR_LIST)
        styles.append({
            "start": offset,
            "len": 1,
            "st": ",".join(filter(None, [
                "b" if bold else "",
                f"c_{color}",
                f"f_{size}"
            ]))
        })
        offset += 1

    return json.dumps({"styles": styles, "ver": 0})


def _get_reply_id(message_object):
    if not message_object:
        return None

    if isinstance(message_object, dict):
        for key in ("message_id", "msg_id", "id", "messageId", "mid"):
            if key in message_object and message_object[key]:
                return message_object[key]

    for attr in ("message_id", "msg_id", "id", "messageId", "mid"):
        if hasattr(message_object, attr):
            val = getattr(message_object, attr)
            if val:
                return val

    return None


def _run_send(content, count, delay, reply_id, thread_id, thread_type, client, ttl_value):

    for i in range(count):
        style = multi_color_styles(content)

        msg_obj = Message(
            text=content,
            style=style
        )

        if reply_id is not None:
            try:
                client.replyMessage(
                    reply_id,
                    msg_obj,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    ttl=ttl_value
                )
            except TypeError:
                client.sendMessage(
                    msg_obj,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    ttl=ttl_value
                )
        else:
            client.sendMessage(
                msg_obj,
                thread_id=thread_id,
                thread_type=thread_type,
                ttl=ttl_value
            )

        if i < count - 1:
            time.sleep(delay)



# ========== LỆNH SEND ==========

def handle_send_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        msg = message.strip()[5:].strip()
        if not msg:
            client.sendMessage(
                Message(text="⚠️ Cú pháp: ,send {text}_{số_lần}_delay{số_giây}\n📌 Có thể bỏ delay → tự dùng 0.2s"),
                thread_id=thread_id,
                thread_type=thread_type,
                ttl=3600
            )
            return

        # kiểm tra có delay không
        if "_delay" in msg:
            content_part, delay_str = msg.split("_delay", 1)
            delay = float(delay_str) if delay_str.strip() != "" else 0.2
        else:
            content_part = msg
            delay = 0.2   # mặc định

        if "_" not in content_part:
            raise ValueError

        content, count = content_part.rsplit("_", 1)
        count = int(count)

        if count <= 0:
            raise ValueError

        if count > 500:
            count = 20

        reply_id = _get_reply_id(message_object)

        _run_send(content, count, delay, reply_id, thread_id, thread_type, client, ttl_value=3600)

    except Exception:
        client.sendMessage(
            Message(
                text="🚦 Sai cú pháp!\n📌 ,send text_3_delay1\n📌 Hoặc: ,send text_3 (auto delay = 0.2)"
            ),
            thread_id=thread_id,
            thread_type=thread_type,
            ttl=3600
        )



# ========== LỆNH BT (ẩn) ==========

def handle_sendhide_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        msg = message[len("?bt"):].strip()

        if not msg:
            client.sendMessage(
                Message(text="⚠️ Cú pháp: ,bt {text}_{số_lần}_delay{số_giây}\n📌 Có thể bỏ delay → auto 0.2"),
                thread_id=thread_id,
                thread_type=thread_type,
                ttl=3600
            )
            return

        # kiểm tra có delay không
        if "_delay" in msg:
            content_part, delay_str = msg.split("_delay", 1)
            delay = float(delay_str) if delay_str.strip() != "" else 0.2
        else:
            content_part = msg
            delay = 0.2

        if "_" not in content_part:
            raise ValueError

        content, count = content_part.rsplit("_", 1)
        count = int(count)

        if count <= 0:
            raise ValueError

        if count > 500:
            count = 20

        reply_id = _get_reply_id(message_object)

        _run_send(content, count, delay, reply_id, thread_id, thread_type, client, ttl_value=1)

    except Exception:
        client.sendMessage(
            Message(
                text="🚦 Sai cú pháp!\n📌 ,bt text_3_delay1\n📌 Hoặc: ,bt text_3 (auto delay = 0.2)"
            ),
            thread_id=thread_id,
            thread_type=thread_type,
            ttl=3600
        )


def PTA():
    return {
        'send': handle_send_command,
        'bt': handle_sendhide_command
    }
