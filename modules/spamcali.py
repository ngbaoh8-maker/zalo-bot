import os
import time
import threading
import random
from zlapi.models import Message, MultiMsgStyle, MessageStyle, Mention
from config import ADMIN, PREFIX

des = {
    'version': "2.4.0",
    'credits': "ngbao",
    'description': "Nhay Cali",
    'power': "Quản trị viên Bot"
}

is_nhaycali_running = False
COLORS = ['#15A85F', '#DB342E', '#F27806', '#F7B503', '#0000FF']
TTL_NHAY = 120000  # 2 phút

def colored_style(full_text):
    color = random.choice(COLORS)
    styles = MultiMsgStyle([
        MessageStyle(offset=0, length=len(full_text), style="color", color=color, auto_format=False),
        MessageStyle(offset=0, length=len(full_text), style="bold", auto_format=False)
    ])
    return styles

def handle_nhaycali_command(message, message_object, thread_id, thread_type, author_id, client):
    global is_nhaycali_running

    if str(author_id) not in ADMIN:
        return

    parts = message.split()
    if len(parts) < 2:
        return

    action = parts[1].lower()

    if action == "stop":
        is_nhaycali_running = False
        return

    if action != "on":
        return

    if not message_object.mentions:
        return

    tagged_user = message_object.mentions[0]['uid']
    try:
        user_info = client.fetchUserInfo(tagged_user)
        tagged_name = user_info.changed_profiles.get(str(tagged_user), {}).get("zaloName", "Người bị nhay")
    except:
        tagged_name = "Người bị nhay"

    try:
        with open("nhay.txt", "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return

    if not lines:
        return

    is_nhaycali_running = True

    def nhay_loop():
        global is_nhaycali_running
        while is_nhaycali_running:
            for text in lines:
                if not is_nhaycali_running:
                    break
                try:
                    tag_text = f"@{tagged_name}"
                    full_text = f"{tag_text} {text}"
                    mention = Mention(uid=tagged_user, offset=0, length=len(tag_text))
                    styles = colored_style(full_text)
                    client.send(Message(text=full_text, mention=mention, style=styles), thread_id, thread_type, ttl=TTL_NHAY)
                    time.sleep(0.3)
                except:
                    is_nhaycali_running = False
                    break
        is_nhaycali_running = False

    threading.Thread(target=nhay_loop).start()

def PTA():
    return {"nhaycali": handle_nhaycali_command}