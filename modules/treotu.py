import os
import time
import threading
from zlapi.models import Message
from config import PREFIX

des = {
    'version': "1.4.0",
    'credits': "ngbao",
    'description': "Treo Từ",
    'power': "Tất cả người dùng"
}

is_treongon_running = False
treongon_threads = {}
sent_messages = {}

def handle_treongon_command(message, message_object, thread_id, thread_type, author_id, client):
    global is_treongon_running, treongon_threads, sent_messages

    parts = message.split()
    if len(parts) < 2:
        return

    action = parts[1].lower()

    if action == "stop":
        is_treongon_running = False
        treongon_threads.pop(thread_id, None)
        sent_messages.pop(thread_id, None)
        return

    if action == "on":
        try:
            with open("ngon.txt", "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
        except FileNotFoundError:
            return

        if not lines:
            return

        is_treongon_running = True
        sent_messages[thread_id] = []

        def loop_send():
            start_time = time.time()
            while is_treongon_running:
                if time.time() - start_time >= 1800:
                    for msg_id in sent_messages.get(thread_id, []):
                        try:
                            client.unsendMessage(msg_id)
                        except Exception:
                            pass
                    sent_messages[thread_id] = []
                    start_time = time.time()

                full_text = "\n\n".join(lines)
                try:
                    msg = client.send(Message(text=full_text), thread_id, thread_type)
                    sent_messages[thread_id].append(msg.message_id)
                except Exception:
                    pass

                time.sleep(30)

        t = threading.Thread(target=loop_send, daemon=True)
        treongon_threads[thread_id] = t
        t.start()
        return

def PTA():
    return {
        'treotu': handle_treongon_command
    }