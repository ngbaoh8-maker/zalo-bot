# -*- coding: utf-8 -*-
# pro_replyai.py — DucDuydzai cuto ver 3.8.0
# Auto reply cố định + menu 1|2|3 (gửi QR/STK/link) + reaction + autoreply on/off + cooldown 1h + set ảnh QR

import json, os, random, logging, time, requests, urllib.parse
from datetime import datetime, timedelta
from zlapi.models import Message

ADMIN_IDS = ["700542342650452398" "9137606601091558912"]

des = {
    'version': "3.8.0",
    'credits': "DucDuydzai cuto",
    'description': "Bot DucDuydzai cuto — trả lời cố định, menu 1/2/3 gửi QR/STK/link, cooldown 1h, thả reaction, autoreply on/off, set ảnh QR.",
    'power': "admin"
}

# --- Cấu hình ---
QR_DIR = "modules/data/qr"
QR_FILE_PATH = os.path.join(QR_DIR, "qr.png")       # QR thuê bot
QR_FILE_PATH_BUY = os.path.join(QR_DIR, "qr_buy.png")  # QR mua file
GROUP_LINK = "https://zalo.me/g/uoctiu980"
STK_TEXT = "💳 STK: 7102165690 (BIDV)\n📞 Liên hệ: 0585519838 (DucDuydzai cuto)"

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [BII AUTOREPLY] - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- Reaction helper ---
def send_reactions_safe(bot, message_object, thread_id, thread_type, reactions):
    for r in reactions:
        try:
            bot.sendReaction(message_object, r, thread_id, thread_type)
            time.sleep(0.15)
        except Exception as e:
            logger.warning(f"[REACTION] Lỗi gửi {r}: {e}")

# --- Autoreply state ---
STATE_FILE = "autoreply_state.json"

if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        try:
            autoreply_groups = json.load(f)
        except:
            autoreply_groups = {}
else:
    autoreply_groups = {}
    logger.info("Khởi tạo trạng thái AutoReply rỗng.")

def save_state():
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(autoreply_groups, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Lỗi lưu trạng thái: {e}")

def handle_autoreply_on(bot, thread_id):
    autoreply_groups[str(thread_id)] = True
    save_state()

def handle_autoreply_off(bot, thread_id):
    autoreply_groups[str(thread_id)] = False
    save_state()

# --- Chống spam ---
user_spam_log = {}
blocked_users = {}
blocked_notified = set()
SPAM_THRESHOLD = 6
WINDOW_SECONDS = 10
BLOCK_DURATION = 20

# --- Cooldown 1 tiếng mỗi người ---
last_reply_time = {}  # {uid: datetime}
COOLDOWN_SECONDS = 3600  # 1 giờ

def get_user_name_by_id(bot, author_id):
    try:
        user_info = bot.fetchUserInfo(author_id).changed_profiles[author_id]
        return user_info.zaloName or user_info.displayName
    except Exception:
        return "bạn bí ẩn"

def check_spam(self, author_id, message_object, thread_id, thread_type):
    now = datetime.now()
    user_spam_log.setdefault(author_id, [])
    user_spam_log[author_id] = [t for t in user_spam_log[author_id] if (now - t).total_seconds() <= WINDOW_SECONDS]
    user_spam_log[author_id].append(now)

    if author_id in blocked_users:
        if now < blocked_users[author_id]:
            if author_id not in blocked_notified:
                name = get_user_name_by_id(self, author_id)
                try:
                    self.replyMessage(
                        Message(text=f"🚫 {name}, đừng spam nữa nha! (bị chặn 20s)"),
                        message_object, thread_id=thread_id, thread_type=thread_type, ttl=600000
                    )
                except:
                    logger.warning("Không thể gửi cảnh báo spam.")
                blocked_notified.add(author_id)
            return True
        else:
            del blocked_users[author_id]
            blocked_notified.discard(author_id)

    if len(user_spam_log[author_id]) > SPAM_THRESHOLD:
        blocked_users[author_id] = now + timedelta(seconds=BLOCK_DURATION)
        blocked_notified.discard(author_id)
        user_spam_log[author_id] = []
        return True

    return False

# --- Helper gửi file ---
def try_send_file(self, filepath, message_object, thread_id, thread_type, caption=None):
    """Thử gửi file ảnh theo nhiều cách (tùy framework). Có fallback gửi link hoặc base64."""
    import base64

    if not os.path.exists(filepath):
        logger.error(f"[QR SEND] Không tìm thấy file: {filepath}")
        return False

    sent = False

    # 1) sendFile
    try:
        if hasattr(self, "sendFile"):
            self.sendFile(filepath, thread_id, thread_type, message_object=message_object, caption=caption)
            sent = True
    except Exception as e:
        logger.warning(f"[QR SEND] sendFile lỗi: {e}")

    # 2) sendImage
    if not sent:
        try:
            if hasattr(self, "sendImage"):
                self.sendImage(filepath, thread_id=thread_id, thread_type=thread_type,
                               message_object=message_object, caption=caption)
                sent = True
        except Exception as e:
            logger.warning(f"[QR SEND] sendImage lỗi: {e}")

    # 3) replyMessage có file đính kèm
    if not sent:
        try:
            msg = Message(text=caption or "")
            if hasattr(msg, "attachments"):
                msg.attachments = [filepath]
            self.replyMessage(msg, message_object, thread_id=thread_id, thread_type=thread_type)
            sent = True
        except Exception as e:
            logger.warning(f"[QR SEND] replyMessage lỗi: {e}")

    # 4) Fallback gửi base64
    if not sent:
        try:
            with open(filepath, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")
            file_name = os.path.basename(filepath)
            txt = f"{caption or ''}\n\n⚠️ Không gửi được ảnh trực tiếp.\n📄 File: `{file_name}`\n🖼️ Base64: {img_b64[:200]}..."
            self.replyMessage(Message(text=txt), message_object, thread_id=thread_id, thread_type=thread_type)
            logger.warning("[QR SEND] fallback bằng text/base64 thành công.")
        except Exception as e:
            logger.error(f"[QR SEND] fallback lỗi: {e}")

    return sent

import threading
from datetime import datetime
# đảm bảo logger, COOLDOWN_SECONDS, last_reply_time, autoreply_groups, check_spam, send_reactions_safe, Message,.. tồn tại

def _safe_delete_message(self, thread_id, thread_type, message_id):
    """Hàm cố gắng gọi nhiều tên API xóa khác nhau tuỳ client."""
    try:
        if not message_id:
            return False
        # thử một vài tên hàm có thể có trên client
        if hasattr(self, "deleteMessage"):
            try:
                self.deleteMessage(message_id=message_id, thread_id=thread_id, thread_type=thread_type)
                return True
            except TypeError:
                # có thể tham số khác
                try:
                    self.deleteMessage(thread_id=thread_id, message_id=message_id, thread_type=thread_type)
                    return True
                except Exception:
                    pass
        if hasattr(self, "delMessage"):
            try:
                self.delMessage(thread_id, message_id)
                return True
            except Exception:
                pass
        if hasattr(self, "delete_msg") or hasattr(self, "deleteMessageById"):
            # thử generic fallback
            try:
                if hasattr(self, "deleteMessageById"):
                    self.deleteMessageById(message_id)
                    return True
                if hasattr(self, "delete_msg"):
                    self.delete_msg(thread_id, message_id)
                    return True
            except Exception:
                pass
        # nếu không có api xóa phù hợp, log và tiếp tục
        logger.warning(f"[TTL] Không tìm được hàm xóa hợp lệ để xóa message {message_id}")
    except Exception as ex:
        logger.exception(f"[TTL] Lỗi khi cố xóa message {message_id}: {ex}")
    return False

def _schedule_delete(self, thread_id, thread_type, message_id, delay_seconds=120):
    """Lên lịch xóa message sau delay_seconds (sử dụng threading.Timer)."""
    try:
        if not message_id:
            return
        def _do_delete():
            try:
                success = _safe_delete_message(self, thread_id, thread_type, message_id)
                if success:
                    logger.info(f"[TTL] Đã xóa message {message_id} sau {delay_seconds}s")
                else:
                    logger.warning(f"[TTL] Không xóa được message {message_id} sau {delay_seconds}s")
            except Exception as e:
                logger.exception(f"[TTL] Exception trong _do_delete: {e}")
        t = threading.Timer(delay_seconds, _do_delete)
        t.daemon = True
        t.start()
    except Exception as e:
        logger.exception(f"[TTL] Lên lịch xóa thất bại: {e}")

def handle_autoreply_message(self, message_object, thread_id, thread_type, author_id, message_text):
    try:
        # Bỏ qua reaction hoặc tin rỗng
        if not message_text or getattr(message_object, "msgType", "") == "chat.reaction":
            return False

        # Kiểm tra ID người gửi hợp lệ
        if str(author_id) == "0" or str(getattr(message_object, "uidFrom", "")) == "0":
            return False

        # Kiểm tra chống spam
        if check_spam(self, author_id, message_object, thread_id, thread_type):
            return True

        # Kiểm tra loại chat
        is_inbox = "user" in str(thread_type).lower() or "private" in str(thread_type).lower()
        if not (is_inbox or autoreply_groups.get(str(thread_id), False)):
            return False

        # Kiểm tra cooldown 1h
        now = datetime.now()
        last_time = last_reply_time.get(author_id)
        if last_time and (now - last_time).total_seconds() < COOLDOWN_SECONDS:
            return True
        last_reply_time[author_id] = now

        # Nội dung trả lời tự động
        reply_text = (
            "🌸 BOT DucDuydzai cuto - PHẢN HỒI TỰ ĐỘNG 🌸\n"
            "🚎════════r════════════════════👋 Chào Bạn Chúc bạn một ngày tốt\n\n"
            "Nếu bạn đang cần\n\n"
            "🟥 Hack map Liên quân chỉ với\n\n"
            "🟩 20k/key 5d\n\n"
            "🟦 30d 100k/key\n\n"
            "🟥 Panel ff\n\n"
            "🔴 10/key 1d\n\n"
            "🟢 100/key 30d\n"
            "(chỉ hỗ trợ pc)\n\n"
            "🟦 Hack iOS\n\n"
            "🔵 ver1 20.000\n\n"
            "🟠 ver2 40.000\n\n"
            "🟡 ver3 60.000 (td 100% anti band k kdl)\n\n"
            "🟢 Mod skin FF 50/file (chỉ hỗ trợ iOS)\n\n"
            "🔹─────────────────────────────📇\n"
        )

        # Gửi tin nhắn trả lời
        try:
            reply_result = self.replyMessage(
                Message(text=reply_text),
                message_object,
                thread_id,
                thread_type,
                ttl=3600000
            )
        except TypeError:
            try:
                reply_result = self.replyMessage(
                    Message(text=reply_text),
                    thread_id,
                    thread_type,
                    ttl=3600000
                )
            except Exception as e:
                logger.error(f"Error sending reply message: {e}")
                return False

        # ================== LOAD NHIỀU UID CARD ==================
        try:
            cards = [
                {"uid": "708891545833852718", "content": "⚡ LH Bii nè 🐧"},
                {"uid": "3490353703164791950", "content": "⚡ Hỗ Trợ Vấn Đề Khác"},
                {"uid": "987654321098765432", "content": "⚡ Hỗ Trợ Mua Key / Tool"},
                {"uid": "1234567890123456789", "content": "⚡ Hỗ Trợ Thanh Toán"},
                {"uid": "223344556677889900", "content": "⚡ Hỗ Trợ Bug / Lỗi Tool"}
            ]

            for card in cards:
                CARD_UID = card.get("uid")
                CARD_CONTENT = card.get("content", "")
                if not CARD_UID:
                    continue

                try:
                    user_info = self.fetchUserInfo(CARD_UID).get(CARD_UID, {})
                    avatar_url = user_info.get("avatar", "")

                    self.sendBusinessCard(
                        userId=CARD_UID,
                        qrCodeUrl=avatar_url,
                        phone=CARD_CONTENT,
                        thread_id=thread_id,
                        thread_type=thread_type,
                        ttl=3600000  # 1 tiếng
                    )

                    logger.info(f"[CARD] ✅ Đã gửi card cho UID {CARD_UID}")
                    time.sleep(0.5)

                except Exception as e:
                    logger.warning(f"[CARD] ❌ Lỗi gửi card cho UID {CARD_UID}: {e}")

        except Exception as e:
            logger.error(f"[CARD] Lỗi khi load danh sách card: {e}")

        # Thả reaction vui
        try:
            reaction_icons = [
                "húp🤨", "Bot Bii", "Bà già🤨", "m chửi ai🤨",
                "gì🤨", "chào em😗", "hi nhô 🐧", "nhậu?🤨",
                "gọi ko nói🤨", "hả🗿"
            ]
            chosen = random.choice(reaction_icons)
            if "group" in str(thread_type).lower():
                self.sendGroupReaction(message_object, chosen, thread_id, thread_type)
            else:
                self.sendReaction(message_object, chosen, thread_id, thread_type)
            logger.info(f"[AUTO REPLY] Đã thả reaction {chosen}")
        except Exception as e:
            logger.warning(f"[AUTO REPLY] Lỗi thả reaction: {e}")

        # Xóa tin nhắn sau 120s
        reply_msg_id = getattr(reply_result, "messageId", None) or getattr(reply_result, "msgId", None)
        if reply_msg_id:
            _schedule_delete(self, thread_id, thread_type, reply_msg_id, delay_seconds=120)

        orig_msg_id = getattr(message_object, "messageId", None) or getattr(message_object, "msgId", None)
        if orig_msg_id:
            _schedule_delete(self, thread_id, thread_type, orig_msg_id, delay_seconds=120)

        return True
    except Exception as e:
        logger.error(f"[BII REPLY] Lỗi xử lý tin: {e}")
        return False
