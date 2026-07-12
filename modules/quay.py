from zlapi.models import *
import time
import threading
import os
import sys
import io
import json
import random
from config import ADMIN

des = {
    'version': "5.0.0",
    'credits': "ngbao",
    'description': "Spam tên nhóm + poll + style đẹp + tag ẩn + sticker nấm đấm",
    'power': "Quản Trị Viên Bot"
}

is_spamming = False
spam_delay = 0.5
list_color = ['db342e', 'f27806', 'f7b503', '15a85f']

# Danh sách sticker
stickers = [
    {"sticker_type": 3, "sticker_id": "27616", "category_id": "10425"},
    {"sticker_type": 3, "sticker_id": "27621", "category_id": "10425"},
    {"sticker_type": 3, "sticker_id": "27614", "category_id": "10426"},
    {"sticker_type": 3, "sticker_id": "23999", "category_id": "10427"},
    {"sticker_type": 3, "sticker_id": "23339", "category_id": "10199"},
    {"sticker_type": 3, "sticker_id": "16988", "category_id": "10180"},
    {"sticker_type": 3, "sticker_id": "26954", "category_id": "10188"},
    {"sticker_type": 3, "sticker_id": "23763", "category_id": "10333"},
    {"sticker_type": 3, "sticker_id": "21010", "category_id": "10299"},
    {"sticker_type": 3, "sticker_id": "25001", "category_id": "10500"},
    {"sticker_type": 3, "sticker_id": "20331", "category_id": "10260"},
    {"sticker_type": 3, "sticker_id": "20113", "category_id": "10245"},
    {"sticker_type": 3, "sticker_id": "19999", "category_id": "10200"},
    {"sticker_type": 3, "sticker_id": "24000", "category_id": "10450"},
    {"sticker_type": 3, "sticker_id": "17000", "category_id": "10181"},
    {"sticker_type": 3, "sticker_id": "26000", "category_id": "10510"}
]

# Hàm tạo style chữ có hiệu ứng đẹp
def tstyles(text, full_text, b=True, i=True, u=False, s=False, color=None, size=18, fm=True):
    styles = [{
        "start": full_text.index(text),
        "len": len(text),
        "st": ",".join(filter(None, [
            "b" if b else "",
            "i" if i else "",
            "u" if u else "",
            "s" if s else "",
            f"c_{color}" if color else "",
            f"f_{size}" if size else ""
        ]))
    }]
    return json.dumps({"styles": styles, "ver": 0}) if fm else styles

def m_tstyles(list_styles):
    return json.dumps({"styles": list_styles, "ver": 0})

def hidden_tagall(client, thread_id, thread_type):
    group_info = client.fetchGroupInfo(thread_id).gridInfoMap[thread_id]
    members = group_info.get('memVerList', [])
    mentions = [Mention(userId.split('_')[0], length=3000, offset=0, auto_format=False) for userId in members]
    return MultiMention(mentions)

def stop_spam(client, message_object, thread_id, thread_type):
    global is_spamming
    is_spamming = False
    client.replyMessage(Message(text="⛔ Đã dừng toàn bộ quay."), message_object, thread_id, thread_type)

def handle_quay_command(message, message_object, thread_id, thread_type, author_id, client):
    global is_spamming, spam_delay

    if author_id not in ADMIN:
        return

    command_parts = message.split()
    if len(command_parts) < 2:
        return

    action = command_parts[1].lower()
    custom_thread_id = thread_id

    if action == "on" and len(command_parts) >= 3:
        custom_thread_id = command_parts[2]

    if action == "setdelay":
        if len(command_parts) < 3:
            client.replyMessage(Message(text="⏱️ Dùng đúng: ?quay setdelay <giây>"), message_object, thread_id, thread_type)
            return
        try:
            spam_delay = float(command_parts[2])
            client.replyMessage(Message(text=f"🚦 Delay của lệnh quay đã được đặt thành {spam_delay}s"), message_object, thread_id, thread_type)
        except ValueError:
            client.replyMessage(Message(text="❗ Giá trị delay không hợp lệ, vui lòng nhập số hợp lệ."), message_object, thread_id, thread_type)
        return

    if action == "off":
        stop_spam(client, message_object, thread_id, thread_type)
        return

    if action != "on":
        return

    try:
        with open("spamgop.txt", "r", encoding="utf-8") as file:
            content_lines = [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        client.replyMessage(Message(text="❌ Không tìm thấy file spamgop.txt"), message_object, thread_id, thread_type)
        return

    if not content_lines:
        client.replyMessage(Message(text="❌ File spamgop.txt trống."), message_object, thread_id, thread_type)
        return

    is_spamming = True

    def name_loop():
        while is_spamming:
            for name in content_lines:
                if not is_spamming: break
                client.changeGroupName(name, custom_thread_id)
                time.sleep(spam_delay)

    def poll_loop():
        index = 0
        while is_spamming:
            try:
                question = content_lines[index]
                client.createPoll(
                    question=question,
                    options=["Gbao w Vminh", "Gbao w Vminh"],
                    groupId=custom_thread_id
                )
                index = (index + 1) % len(content_lines)
                time.sleep(1)
            except Exception as e:
                client.replyMessage(Message(text=f"Lỗi khi tạo poll: {str(e)}"), message_object, thread_id, thread_type)
                break

    def styled_loop():
        counter = 0
        while is_spamming:
            for text in content_lines:
                if not is_spamming: break
                words = text.split()
                list_st = []
                offset = 0
                for word in words:
                    try:
                        start = text.index(word, offset)
                        list_st.append({
                            "start": start,
                            "len": len(word),
                            "st": ",".join(filter(None, [
                                "b", "i",
                                f"c_{random.choice(list_color)}",
                                f"f_{random.randint(17, 22)}"
                            ]))
                        })
                        offset = start + len(word)
                    except:
                        continue

                style_msg = m_tstyles(list_st)
                mention = hidden_tagall(client, custom_thread_id, thread_type)
                client.send(Message(text=text, mention=mention, style=style_msg), custom_thread_id, thread_type)

                counter += 1
                if counter % 3 == 0:
                    sticker = random.choice(stickers)
                    try:
                        client.sendSticker(sticker['sticker_type'], sticker['sticker_id'], sticker['category_id'], custom_thread_id, thread_type)
                    except Exception as e:
                        print(f"Sticker lỗi: {e}")

                time.sleep(spam_delay)

    threading.Thread(target=name_loop).start()
    threading.Thread(target=poll_loop).start()
    threading.Thread(target=styled_loop).start()

    client.replyMessage(Message(text=f"Bắt đầu quay vào nhóm {custom_thread_id} với delay {spam_delay}s"), message_object, thread_id, thread_type)

def PTA():
    return {
        'quay': handle_quay_command
    }