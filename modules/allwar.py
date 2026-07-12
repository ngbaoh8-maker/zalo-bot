from zlapi.models import *
import time
import random
import threading
import os
from config import PREFIX, ADMIN

is_war_running = False
WAR_SETTINGS = {}
DEFAULT_DELAY = 0.5

des = {
    'version': "2.0.0",
    'credits': "ngbao",
    'description': "War liên tục cho đến khi tắt ⚔️",
    'power': "Admin"
}

WAR_MENU = (
    f"╔════════════════════════╗\n"
    f"⚔️  MENU WAR BOT </> ngbao ⚔️\n"
    f"╚════════════════════════╝\n\n"
    f"➤ 🎯 Bắt đầu war: {PREFIX}war [reo/spam/poll/todo/random] @tag\n"
    f"➤ ⚙️ Cài delay: {PREFIX}war [reo/spam/poll/todo] delay [số]\n"
    f"➤ 📝 Đặt file: {PREFIX}war [reo/spam/poll/todo] set [file]\n"
    f"➤ ⭕️ Tắt war: {PREFIX}war off\n\n"
    f"💡 Ví dụ:\n"
    f"  • {PREFIX}war spam @Duy\n"
    f"  • {PREFIX}war spam delay 1\n"
    f"  • {PREFIX}war spam set data/war.txt\n"
    f"  • {PREFIX}war off"
)

DEFAULT_MESSAGES = [
    "🔥 thg cha m ngbao ba ro🔥",
    "💥 trum san war ngbao💣",
    "⚔️ vao day ma an ngbao ne",
    "🗿 so ank ngbao r ha e",
    "👻 bt ro cha ngbao ba san war ch ha con",
    "😈 con cac ba may ngbao war chet me may😈",
    "thg lon so ngbao ch ne",
    "trum san war ngbao ",
    "🚀 cha ngbao ba ro r",
    "🧨 BÙM!"
]


# ==================== HÀM HỖ TRỢ ====================
def load_messages_from_file(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    except:
        return None


def stop_war(client, message_object, thread_id, thread_type):
    global is_war_running
    if not is_war_running:
        client.replyMessage(Message(text="❌ Không có war nào đang chạy."), message_object, thread_id, thread_type, ttl=6000)
        return
    is_war_running = False
    client.replyMessage(Message(text="⛔️ Đã dừng WAR thành công!"), message_object, thread_id, thread_type, ttl=6000)


def start_war(client, message_object, thread_id, thread_type, mode, delay, messages, tagged_user):
    global is_war_running
    is_war_running = True

    def war_loop():
        global is_war_running
        while is_war_running:
            msg = random.choice(messages)
            try:
                if tagged_user:
                    mention = Mention(tagged_user, length=0, offset=0)
                    client.send(Message(text=msg, mention=mention), thread_id, thread_type, ttl=6000)
                else:
                    client.send(Message(text=msg), thread_id, thread_type, ttl=6000)
            except Exception as e:
                client.replyMessage(Message(text=f"Lỗi gửi tin: {e}"), message_object, thread_id, thread_type, ttl=6000)
            time.sleep(delay)
        is_war_running = False

    t = threading.Thread(target=war_loop)
    t.start()
    client.replyMessage(Message(text=f"🚀 Bắt đầu WAR mode `{mode}` (liên tục đến khi off)\nDelay: {delay}s"), message_object, thread_id, thread_type, ttl=6000)


# ==================== LỆNH CHÍNH ====================
def war(message, message_object, thread_id, thread_type, author_id, client):
    global is_war_running, WAR_SETTINGS

    # Chỉ admin mới được war
    if author_id not in ADMIN:
        client.replyMessage(Message(text="🚫 Bạn không có quyền dùng lệnh WAR."), message_object, thread_id, thread_type, ttl=6000)
        return

    parts = message.split()
    if len(parts) == 1 or (len(parts) > 1 and parts[1].lower() in ["help", "?", "menu"]):
        client.replyMessage(Message(text=WAR_MENU), message_object, thread_id, thread_type, ttl=6000)
        return

    if "off" in parts:
        stop_war(client, message_object, thread_id, thread_type)
        return

    mode = parts[1].lower()
    if mode not in ["reo", "spam", "poll", "todo", "random"]:
        client.replyMessage(Message(text=f"❌ Mode không hợp lệ.\n\n{WAR_MENU}"), message_object, thread_id, thread_type, ttl=6000)
        return

    if "delay" in parts:
        try:
            idx = parts.index("delay")
            val = float(parts[idx + 1])
            WAR_SETTINGS["delay"] = val
            client.replyMessage(Message(text=f"✅ Delay cho mode `{mode}` đặt thành {val}s"), message_object, thread_id, thread_type, ttl=6000)
        except:
            client.replyMessage(Message(text="⚠️ Sai cú pháp. Ví dụ: war spam delay 1"), message_object, thread_id, thread_type, ttl=6000)
        return

    if "set" in parts:
        try:
            idx = parts.index("set")
            path = parts[idx + 1]
            msgs = load_messages_from_file(path)
            if not msgs:
                client.replyMessage(Message(text="❌ Không đọc được file hoặc file trống."), message_object, thread_id, thread_type, ttl=6000)
                return
            WAR_SETTINGS["messages"] = msgs
            client.replyMessage(Message(text=f"✅ Đã nạp file `{path}` ({len(msgs)} dòng)."), message_object, thread_id, thread_type, ttl=6000)
        except:
            client.replyMessage(Message(text="⚠️ Sai cú pháp. Ví dụ: war spam set data/spam.txt"), message_object, thread_id, thread_type, ttl=6000)
        return

    delay = WAR_SETTINGS.get("delay", DEFAULT_DELAY)
    messages = WAR_SETTINGS.get("messages", DEFAULT_MESSAGES)
    tagged_user = message_object.mentions[0]["uid"] if message_object.mentions else None

    start_war(client, message_object, thread_id, thread_type, mode, delay, messages, tagged_user)


def PTA():
    return {
        'war': war
    }
