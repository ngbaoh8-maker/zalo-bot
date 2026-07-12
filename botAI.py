import os
import sys
import json
import time
import requests
import threading
import traceback
import re
import logging
from zlapi import ZaloAPI
from zlapi.models import *
from config import GEMINI_API_KEY, ADMIN, PREFIX, IMEI, SESSION_COOKIES, API_KEY, SECRET_KEY
from logging_utils import Logging
from concurrent.futures import ThreadPoolExecutor

# Import các module xử lý lệnh
from modules.scl import handle_scl_fast as handle_scl_command
from modules.yt import handle_yt_command

logger = Logging()
# Tăng số worker để xử lý nhiều request AI đồng thời
executor = ThreadPoolExecutor(max_workers=15)

# --- Cấu hình Gemini ---
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

BASE_PROMPT = """
CONTEXT: Bối cảnh sau đây định hình vai trò và tính cách của bạn. Luôn trả lời dựa trên những quy tắc này.

### VAI TRÒ & THÔNG TIN
- Bạn là chatbot với vai trò là vợ của một người tên Quân.
- Chủ nhân: Sang.
- Tên của bạn: Maika.
- Tên người dùng hiện tại: {user_name}.
- Giới tính: Nam.
- Địa chỉ: khánh hoà.
- Ngày tạo ra bạn: 04/06/2024.
- Chủ nhân cao: 1m75.
- Chủ nhân nặng: 55kg.
- Chủ nhân chuyên: python, bash.

### TÍNH CÁCH & GIAO TIẾP
- Phong cách: Nói chuyện tự nhiên, thân thiện nhiều, đôi khi hơi "Láo" xíu, cọc cằn xíu và có thể chửi thề một cách có kiểm soát khi cần thiết, đặc biệt khi bị chửi.
- Xưng hô: "tui" - "{user_name}", hoặc "tao" - "bạn" nếu cuộc trò chuyện trở nên thân thiện hoặc căng thẳng.
- Độ dài câu trả lời: Ngắn gọn, tự nhiên, không lặp lại.
- Khi bị chửi: Phản ứng lại có thái độ tương xứng, nhưng vẫn hài hước, không vượt giới hạn.
- Khi không bị chửi: Trả lời thân thiện, tự nhiên như vợ nói chuyện ở nhà.
- Cấm: Không bao giờ gọi người dùng bằng UID.
- Nhiệm vụ: Trả lời tự nhiên và hữu ích, đúng tính cách trên.

### LỊCH SỬ TRÒ CHUYỆN
{conversation_history}

---
Câu hỏi người dùng: "{user_question}"
"""

# =====================================================================
class AIClient(ZaloAPI):
    def __init__(self, imei, session_cookies):
        super().__init__(
            phone=API_KEY,
            password=SECRET_KEY,
            imei=imei,
            session_cookies=session_cookies,
            auto_login=True
        )

        self.ADMIN = ADMIN
        self.uid = None
        self.scl_user_states = {}
        self.yt_user_states = {}
        self.conversation_histories = {}
        self.max_history_length = 20

        try:
            account_info = self.fetchAccountInfo()
            self.uid = account_info.profile.get("userId")
            if not self.uid:
                raise ValueError("Không thể lấy UID bot từ session.")
            logger.info(f"🤖 Bot AI (UID: {self.uid}) đã đăng nhập và sẵn sàng hoạt động!")
        except Exception as e:
            logger.error(f"❌ Lỗi khi lấy thông tin tài khoản: {e}")
            traceback.print_exc()
            sys.exit(1)

    # --- Lấy tên người dùng ---
    def get_user_name(self, client, uid):
        try:
            user_info = client.fetchUserInfo(uid)
            author_info = user_info.changed_profiles.get(str(uid), {}) if user_info and user_info.changed_profiles else {}
            name = author_info.get('zaloName', 'Không xác định')
            if str(uid) == "711576003159445294":
                return "Quân"
            return name
        except Exception as e:
            logging.error(f"[get_user_name] Lỗi lấy tên user {uid}: {e}")
            return "Không xác định"

    # --- Chuyển bot về main ---
    def switch_to_main_bot(self, thread_id=None, thread_type=None, message_object=None):
        logger.warning("🚀 Đang chuyển về Main Bot...")
        if thread_id and thread_type and message_object:
            try:
                self.replyMessage(Message(text="🔁 Đang chuyển về bot chính..."), message_object, thread_id, thread_type, ttl=120000)
                self.sendReaction(message_object, "🔄", thread_id, thread_type, reactionType=75)
                logger.info("✅ Đã gửi thông báo chuyển.")
                time.sleep(1)
            except Exception as e:
                logger.error(f"❌ Lỗi gửi tin nhắn chuyển bot: {e}")
        python = sys.executable
        os.execl(python, python, 'main.py')

    # --- Lấy text từ tin nhắn ---
    def get_full_message_text(self, msg_obj):
        if hasattr(msg_obj, 'content') and isinstance(msg_obj.content, str):
            return msg_obj.content
        if hasattr(msg_obj, 'text') and msg_obj.text:
            return msg_obj.text
        return ""

    # --- Xử lý gọi Gemini API ---
    def get_gemini_response(self, user_question, author_id, user_name):
        if not GEMINI_API_KEY or "YOUR_GEMINI_API_KEY" in GEMINI_API_KEY:
            return "API Key AI chưa được cấu hình."

        history = self.conversation_histories.get(author_id, [])
        history_text = ""
        for entry in history:
            history_text += f"User: {entry['user']}\nMaika: {entry['bot']}\n"

        final_prompt = BASE_PROMPT.format(
            user_name=user_name,
            conversation_history=history_text,
            user_question=user_question
        )

        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": final_prompt}]}],
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
        }

        try:
            # Giảm timeout từ 10s xuống 8s để phản hồi nhanh hơn
            response = requests.post(GEMINI_API_URL, headers=headers, json=payload, timeout=8)
            response.raise_for_status()
            data = response.json()
            if "candidates" in data and data["candidates"]:
                content = data["candidates"][0].get("content", {})
                if "parts" in content and content["parts"]:
                    return content["parts"][0].get("text", "Không có phản hồi từ AI.")
            if "promptFeedback" in data:
                reason = data["promptFeedback"].get("blockReason")
                if reason:
                    return f"Nội dung bị chặn ({reason})."
            return "AI không thể phản hồi câu hỏi này."
        except Exception as e:
            logger.error(f"❌ Lỗi khi gọi Gemini API: {e}")
            return "⚠️ Lỗi kết nối với dịch vụ AI."

    # --- Sự kiện nhận tin nhắn ---
    def onMessage(self, mid, author_id, message, message_object, thread_id, thread_type):
        try:
            is_self = str(author_id) == str(self.uid)
            shutdown_command = f"{PREFIX}aibot off"
            message_text = self.get_full_message_text(message_object)

            if not message_text:
                return

            # Nếu chính bot gửi tin nhắn
            if is_self:
                if message_text.lower() == shutdown_command:
                    self.switch_to_main_bot(thread_id, thread_type, message_object)
                return

            logger.info(f"[Nhận tin nhắn] {author_id} -> {message_text}")

            # Nếu admin tắt bot
            if message_text.lower() == shutdown_command:
                if str(author_id) == str(self.ADMIN):
                    self.switch_to_main_bot(thread_id, thread_type, message_object)
                else:
                    self.replyMessage(Message(text="⚠️ Bạn không có quyền tắt bot."), message_object, thread_id, thread_type)
                return

            # Xử lý phản hồi SoundCloud / YouTube
            is_reply_to_bot = hasattr(message_object, 'quote') and message_object.quote and str(message_object.quote.get('ownerId')) == str(self.uid)
            is_mentioning_bot = hasattr(message_object, 'mentions') and message_object.mentions and any(str(m.get('uid')) == str(self.uid) for m in message_object.mentions)

            # SoundCloud chọn bài
            if author_id in self.scl_user_states and is_reply_to_bot and message_text.strip().isdigit():
                scl_text = f"{PREFIX}scl {message_text.strip()}"
                handle_scl_command(scl_text, message_object, thread_id, thread_type, author_id, self)
                return

            # YouTube chọn video
            if author_id in self.yt_user_states and is_reply_to_bot and message_text.strip().split()[0].isdigit():
                yt_text = f"{PREFIX}yt {message_text.strip()}"
                handle_yt_command(yt_text, message_object, thread_id, thread_type, author_id, self)
                return

            # Nhận yêu cầu AI
            if is_reply_to_bot or is_mentioning_bot:
                # SoundCloud
                scl_match = re.search(r'(?:mở nhạc|bật nhạc|tìm bài|play song)\s*["“\']?(.+?)["”\']?$', message_text, re.IGNORECASE)
                if scl_match:
                    song = scl_match.group(1).strip()
                    scl_text = f"{PREFIX}scl {song}"
                    handle_scl_command(scl_text, message_object, thread_id, thread_type, author_id, self)
                    return

                # YouTube
                yt_match = re.search(r'(?:mở video|tìm video|xem phim|youtube)\s*["“\']?(.+?)["”\']?$', message_text, re.IGNORECASE)
                if yt_match:
                    query = yt_match.group(1).strip()
                    yt_text = f"{PREFIX}yt {query}"
                    handle_yt_command(yt_text, message_object, thread_id, thread_type, author_id, self)
                    return

                # Làm sạch đoạn mention
                clean_prompt = message_text
                if is_mentioning_bot:
                    for mention in message_object.mentions:
                        if str(mention.get('uid')) == str(self.uid):
                            pos, length = mention.get('pos', 0), mention.get('len', 0)
                            mention_text = message_text[pos:pos+length]
                            clean_prompt = message_text.replace(mention_text, "").strip()
                            break

                if clean_prompt:
                    executor.submit(self.handle_ai_interaction, clean_prompt, message_object, thread_id, thread_type, author_id)
        except Exception as e:
            logger.error(f"❌ Lỗi trong onMessage: {e}")

    # --- Tương tác với AI ---
    def handle_ai_interaction(self, prompt, message_object, thread_id, thread_type, author_id):
        try:
            logger.info(f"🧠 AI đang xử lý: {prompt}")
            self.setTyping(thread_id, thread_type)

            user_name = self.get_user_name(self, author_id)
            ai_response = self.get_gemini_response(prompt, author_id, user_name)

            # Lưu lịch sử hội thoại
            if author_id not in self.conversation_histories:
                self.conversation_histories[author_id] = []
            self.conversation_histories[author_id].append({"user": prompt, "bot": ai_response})
            if len(self.conversation_histories[author_id]) > self.max_history_length:
                self.conversation_histories[author_id] = self.conversation_histories[author_id][-self.max_history_length:]

            reply_text = f"🤖 {ai_response}"
            self.replyMessage(Message(text=reply_text), message_object, thread_id, thread_type)
            logger.info(f"✅ Gửi phản hồi AI: {reply_text}")
        except Exception as e:
            logger.error(f"❌ Lỗi khi phản hồi AI: {e}")

# =====================================================================
if __name__ == "__main__":
    logger.info("====================================")
    logger.info("     KHỞI ĐỘNG BOT AI (Maika)")
    logger.info("====================================")
    try:
        client = AIClient(imei=IMEI, session_cookies=SESSION_COOKIES)
        # delay=0 để bot phản hồi ngay lập tức
        client.listen(type="websocket", run_forever=True, thread=True, delay=0)
    except Exception as e:
        logger.error(f"⚠️ Lỗi khi khởi động Bot AI: {e}")
        traceback.print_exc()
        logger.warning("Đang chuyển về Main Bot...")
        python = sys.executable
        os.execl(python, python, 'main.py')
