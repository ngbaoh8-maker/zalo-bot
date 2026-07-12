import re
import json
import threading
import time
import logging
import random
import requests
from requests.adapters import HTTPAdapter
from concurrent.futures import ThreadPoolExecutor, as_completed
from zlapi.models import ThreadType, Message
from zlapi import ZaloAPIException
from zlapi.models import Message, MultiMsgStyle, MessageStyle, ThreadType

des = {
    'version': "1.0.2",
    'credits': "ngbao",
    'description': "Tự động tham gia nhóm phát hiện link",
    'power': "Quản trị viên Bot"
}

# --- Logging config ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [AUTOJOIN] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
import logging
logging.disable(logging.CRITICAL)

file_handler = logging.FileHandler('autojoin.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - [AUTOJOIN] - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# --- Regex compile ---
ZALO_GROUP_LINK_REGEX = re.compile(r'https:\/\/(?:zalo\.me|chat\.zalo\.me)\/g\/[a-zA-Z0-9]+(?:\?[^ ]*)?')

# --- Shared vars ---
failed_links = set()
failed_lock = threading.Lock()

# --- Load failed_links ---
try:
    with open('failed_links.json', 'r') as f:
        content = f.read().strip()
        failed_links = set(json.loads(content)) if content else set()
    logger.info(f"Đã tải {len(failed_links)} link thất bại từ failed_links.json")
except Exception as e:
    logger.warning(f"Không thể load failed_links.json: {e}")
    failed_links = set()

# --- Save failed_links batch ---
def save_failed_links():
    with failed_lock:
        try:
            with open('failed_links.json', 'w') as f:
                json.dump(list(failed_links), f)
        except Exception as e:
            logger.error(f"Lỗi khi lưu failed_links.json: {e}")

# --- Shared requests session ---
_shared_session = requests.Session()
adapter = HTTPAdapter(pool_connections=50, pool_maxsize=50)
_shared_session.mount("http://", adapter)
_shared_session.mount("https://", adapter)
_shared_session.headers.update({'User-Agent': 'ZaloWeb/1.0'})
requests.get = _shared_session.get
requests.post = _shared_session.post
requests.put = _shared_session.put
requests.delete = _shared_session.delete

# --- Helpers ---
def extract_links_from_message(message_object, text):
    links = []
    if text:
        links.extend(ZALO_GROUP_LINK_REGEX.findall(text))

    attachments = getattr(message_object, 'attachments', None) or []
    for att in attachments:
        if isinstance(att, dict):
            att_text = str(att.get('content', '') or att.get('url', '') or att.get('link', '') or att.get('href', ''))
            links.extend(ZALO_GROUP_LINK_REGEX.findall(att_text))

    return list(dict.fromkeys(links))  # unique giữ nguyên thứ tự


def try_autojoin_from_link(client, link):
    if link in failed_links:
        return False, "Bỏ qua link thất bại trước đó", None, None

    if not ZALO_GROUP_LINK_REGEX.match(link):
        return False, "Link nhóm không hợp lệ", None, None

    group_code = link.split("/")[-1].split("?")[0].lower()

    try:
        join_response = client.joinGroup(link)
        time.sleep(0.01)
        return True, f"Yêu cầu join đã gửi ({group_code})", join_response, None

    except ZaloAPIException as e:
        if "404" in str(e):
            with failed_lock:
                failed_links.add(link)
            return False, "Link không hợp lệ (404)", None, None
        return False, f"API lỗi: {str(e)}", None, None
    except Exception as e:
        with failed_lock:
            failed_links.add(link)
        return False, f"Lỗi không mong muốn: {str(e)}", None, None


def process_message_for_autojoin(client, message_object, thread_id, thread_type, author_id, message_text, mid=None, logger_ext=None):
    log = logger_ext or logger
    try:
        links = extract_links_from_message(message_object, message_text)
        if not links:
            return

        settings = read_settings(client.uid) or {}
        if not settings.get("autojoin_enabled", False):
            return

        if not client.isLoggedIn():
            log.error("Session không hợp lệ (isLoggedIn = False)")
            return

        results = []
        new_failed_links = set()

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_to_link = {executor.submit(try_autojoin_from_link, client, link): link for link in links[:5]}
            for future in as_completed(future_to_link):
                link = future_to_link[future]
                try:
                    success, msg, response, group_info = future.result()
                    results.append((link, success, msg, group_info))
                    if not success and "404" in msg:
                        new_failed_links.add(link)
                    time.sleep(2)
                except Exception as e:
                    results.append((link, False, f"Lỗi xử lý: {e}", None))
                    new_failed_links.add(link)

        if new_failed_links:
            with failed_lock:
                failed_links.update(new_failed_links)
            save_failed_links()

        for link, success, msg, group_info in results:
            try:
                if success:
                    icon = random.choice(["🗿Bot ngbao bá sàn😗", "🐢tao join r đó duyệt đi🤨", "🤴cho thuê bot nhiều chức năng🐧", "💸Nhận Rãi Thuê", "🌟Cho Thuê Bót😹"])
                else:
                    icon = "Phải Chịu🐻"

                client.sendReaction(message_object, icon, thread_id, thread_type)
                time.sleep(0.05)
            except Exception as e:
                log.error(f"Lỗi khi gửi reaction cho {link}: {e}")

    except Exception as e:
        log.exception(f"Lỗi trong process_message_for_autojoin: {e}")


def handle_autojoin_command(self, message_object, thread_id, thread_type, author_id, message_text, mid=None, logger_ext=None):
    log = logger_ext or logger

    args = message_text.split()
    if len(args) < 2:
        self.sendReaction(message_object, "❓", thread_id, thread_type)
        author_name = get_user_name_by_id(self, author_id) or str(author_id)
        msg = f"➜{author_name}\n/-li Fen Ơi, dùng {self.prefix}autojoin on|off nha"
        name_offset = 0
        name_len = len(author_name)
        if any(ord(ch) > 127 for ch in author_name):
            name_len += 1
        styles = MultiMsgStyle([
            MessageStyle(offset=name_offset, length=name_len, style="color", color="#DB342E", auto_format=False),
            MessageStyle(offset=name_offset, length=name_len, style="bold", size="15", auto_format=False),
        ])
        self.send(Message(text=msg, style=styles), thread_id=thread_id, thread_type=thread_type, ttl=60000)
        return

    action = args[1].lower()
    settings = read_settings(self.uid) or {}
    author_name = get_user_name_by_id(self, author_id) or str(author_id)

    try:
        if action in ("on", "enable", "1", "true"):
            settings["autojoin_enabled"] = True
            write_settings(self.uid, settings)
            status_text = "on"
            icon = "💢"

        elif action in ("off", "disable", "0", "false"):
            settings["autojoin_enabled"] = False
            write_settings(self.uid, settings)
            status_text = "off"
            icon = "❌"

        else:
            self.sendReaction(message_object, "❓", thread_id, thread_type)
            msg = f"➜{author_name}\nFen Ơi, /-li dùng {self.prefix}autojoin on|off nha"
            name_offset = 0
            name_len = len(author_name)
            if any(ord(ch) > 127 for ch in author_name):
                name_len += 1
            styles = MultiMsgStyle([
                MessageStyle(offset=name_offset, length=name_len, style="color", color="#DB342E", auto_format=False),
                MessageStyle(offset=name_offset, length=name_len, style="bold", size="15", auto_format=False),
            ])
            self.send(Message(text=msg, style=styles), thread_id=thread_id, thread_type=thread_type, ttl=60000)
            return

        self.sendReaction(message_object, icon, thread_id, thread_type)
        msg = f"➜{author_name}\n/-li Fen Ơi, Autojoin {status_text} Gòi"
        name_offset = 0
        name_len = len(author_name)
        if any(ord(ch) > 127 for ch in author_name):
            name_len += 1

        styles = MultiMsgStyle([
            MessageStyle(offset=name_offset, length=name_len, style="color", color="#DB342E", auto_format=False),
            MessageStyle(offset=name_offset, length=name_len, style="bold", size="15", auto_format=False),
        ])

        self.send(
            Message(text=msg, style=styles),
            thread_id=thread_id,
            thread_type=thread_type,
            ttl=60000
        )

    except Exception as e:
        log.error(f"Lỗi không mong muốn khi xử lý lệnh /autojoin: {e}")
        self.sendReaction(message_object, "⚠️", thread_id, thread_type)
        msg = f"{author_name}\n⚠️ Lỗi không mong muốn khi xử lý lệnh"
        name_offset = 0
        name_len = len(author_name)
        if any(ord(ch) > 127 for ch in author_name):
            name_len += 1
        styles = MultiMsgStyle([
            MessageStyle(offset=name_offset, length=name_len, style="color", color="#DB342E", auto_format=False),
            MessageStyle(offset=name_offset, length=name_len, style="bold", size="15", auto_format=False),
        ])
        self.send(Message(text=msg, style=styles), thread_id=thread_id, thread_type=thread_type)

def PTA():
    return {
        'atj': handle_autojoin_command
    }
