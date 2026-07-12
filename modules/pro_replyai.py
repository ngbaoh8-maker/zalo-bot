import json, os, re, math, heapq, random, requests, logging, time
from datetime import datetime, timedelta
from zlapi.models import Message
from core.bot_sys import *

des = {
    'version': "3.4.5",
    'credits': "ngbao",
    'description': "Autoreply bằng AI.",
    'power': "Admin"
}

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [YUKI AUTOREPLY] - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- Reaction helper ---
def send_reactions_safe(bot, message_object, thread_id, thread_type, reactions):
    for r in reactions:
        try:
            bot.sendReaction(message_object, r, thread_id, thread_type)
            logger.debug(f"[REACTION] Sent reaction {r} -> thread {thread_id}")
            time.sleep(0.2)
        except Exception as e:
            logger.warning(f"[REACTION] Lỗi gửi {r}: {e}")

# --- Config ---
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
GEMINI_API_KEY = "AIzaSyBA5z2QFHpi73RoBNaEkHB9IgFmSh18JbI"  # key test ok
STATE_FILE = "autoreply_state.json"
default_language = "vi"
last_message_times = {}

# --- Load trạng thái nhóm ---
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        autoreply_groups = json.load(f)
else:
    autoreply_groups = {}
    logger.info("Khởi tạo trạng thái AutoReply rỗng.")

def save_state():
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(autoreply_groups, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Lỗi lưu trạng thái: {e}")

def get_user_name_by_id(bot, author_id):
    try:
        user_info = bot.fetchUserInfo(author_id).changed_profiles[author_id]
        return user_info.zaloName or user_info.displayName
    except Exception:
        return "bạn bí ẩn"

def detect_language(text):
    if re.search(r'[àáạảãâầấậẩẫêềếệểễôồốộổỗìíịỉĩùúụủũưừứựửữ]', text.lower()):
        return "vi"
    elif re.search(r'[a-zA-Z]', text):
        return "en"
    return default_language

def handle_autoreply_on(bot, thread_id):
    autoreply_groups[str(thread_id)] = True
    save_state()

def handle_autoreply_off(bot, thread_id):
    if str(thread_id) in autoreply_groups:
        autoreply_groups[str(thread_id)] = False
        save_state()
        

# --- Chống spam nâng cao file này ---
user_spam_log = {}      # {uid: [timestamps]}
blocked_users = {}      # {uid: thời gian hết hạn datetime}
blocked_notified = set()

SPAM_THRESHOLD = 6      # >6 tin nhắn trong WINDOW là spam
WINDOW_SECONDS = 10     # 10 giây
BLOCK_DURATION = 20     # 20 giây

# --- Cache và cooldown cho Gemini ---
gemini_cache = {}       # {prompt_text: (response_text, timestamp)}
gemini_cooldown = {}    # {author_id: datetime}
GEMINI_COOLDOWN_SECONDS = 2
GEMINI_CACHE_SECONDS = 120

def check_spam(self, author_id, message_object, thread_id, thread_type):
    now = datetime.now()
    user_spam_log.setdefault(author_id, [])
    
    # Xóa những tin quá cũ
    user_spam_log[author_id] = [t for t in user_spam_log[author_id] if (now - t).total_seconds() <= WINDOW_SECONDS]
    user_spam_log[author_id].append(now)

    # Nếu người dùng đang bị cấm
    if author_id in blocked_users:
        if now < blocked_users[author_id]:
            if author_id not in blocked_notified:
                name = get_user_name_by_id(self, author_id)
                self.replyMessage(
                    Message(text=f"🚫 {name}, Bát Nha Bát Nháo Hả Beta ? \n➜đang bị cấm spam 20s!"),
                    message_object, thread_id=thread_id, thread_type=thread_type, ttl=600000
                )
                blocked_notified.add(author_id)
            return True
        else:
            # Hết cấm → gửi thông báo mở lại
            name = get_user_name_by_id(self, author_id)
            self.replyMessage(
                Message(text=f"➜ :; Beta {name}, Đc Mõm Rồi Đó , Lớn chưa ? Mà Spam "),
                message_object, thread_id=thread_id, thread_type=thread_type, ttl=600000
            )
            del blocked_users[author_id]
            blocked_notified.discard(author_id)

    # Kiểm tra spam mới
    if len(user_spam_log[author_id]) > SPAM_THRESHOLD:
        blocked_users[author_id] = now + timedelta(seconds=BLOCK_DURATION)
        blocked_notified.discard(author_id)
        user_spam_log[author_id] = []  # reset log
        return True

    return False

def call_autoreply(prompt_msg, author_id):
    now = datetime.now()

    # --- Kiểm tra cooldown user ---
    last_call = gemini_cooldown.get(author_id)
    if last_call and (now - last_call).total_seconds() < GEMINI_COOLDOWN_SECONDS:
        return "TK ❄️ đang bận, nhắn chậm thôi 😅"

    gemini_cooldown[author_id] = now

    # --- Kiểm tra cache ---
    if prompt_msg in gemini_cache:
        cached_response, cache_time = gemini_cache[prompt_msg]
        if (now - cache_time).total_seconds() <= GEMINI_CACHE_SECONDS:
            return cached_response

    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}
    json_data = {
        "contents": [{"parts": [{"text": prompt_msg}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 100}
    }

    try:
        r = requests.post(GEMINI_API_URL, params=params, headers=headers, json=json_data, timeout=3)
        r.raise_for_status()
        result = r.json()
        if "candidates" in result and result["candidates"]:
            content = result["candidates"][0].get("content", {}).get("parts", [])
            if content and "text" in content[0]:
                response = content[0]["text"].replace("*", "")
                gemini_cache[prompt_msg] = (response, now)  # lưu cache
                return response
        return "TK ❄️ hơi lag, thử lại sau nha! 😅"

    except requests.exceptions.HTTPError as e:
        if r.status_code == 429:
            logger.warning("Gemini API quá tải, trả fallback")
            return "TK ❄️ đang bận, thử lại sau vài giây nha! 😅"
        else:
            logger.error(f"Lỗi HTTP Gemini API: {e}")
            return "TK ❄️ gặp lỗi, thử lại sau nha! 😅"
    except Exception as e:
        logger.error(f"Lỗi gọi Gemini API: {e}")
        return "TK ❄️ mệt rồi, để nghỉ xíu nha! 😴"

def handle_autoreply_message(self, message_object, thread_id, thread_type, author_id, message_text):
    if not message_text or getattr(message_object, "msgType", "") == "chat.reaction":
        return False
    if str(author_id) == "0" or str(getattr(message_object, "uidFrom", "")) == "0":
        return False

    # --- CHECK SPAM 10s / >6 tin nhắn ---
    if check_spam(self, author_id, message_object, thread_id, thread_type):
        return True

    msg_lower = message_text.lower().strip()
    now = datetime.now()

    # --- Lệnh bật/tắt autoreply ---
    if msg_lower.startswith("autoreply"):
        if not is_admin(self, author_id):
            response = "❌ Bạn không phải admin bot!"
            send_reactions_safe(self, message_object, thread_id, thread_type, ["🚫", "❌"])
        elif "on" in msg_lower:
            handle_autoreply_on(self, thread_id)
            response = "✅ Bật autoreply bot TK ❄️ rồi nha!"
            send_reactions_safe(self, message_object, thread_id, thread_type, ["🚀", "✅", "❄️"])
        elif "off" in msg_lower:
            handle_autoreply_off(self, thread_id)
            response = "💤 Đã tắt bot TK ❄️!"
            send_reactions_safe(self, message_object, thread_id, thread_type, ["🧊", "💤"])
        else:
            response = f"Dùng autoreply on hoặc autoreply off nha!"
            send_reactions_safe(self, message_object, thread_id, thread_type, ["⚠️"])
        self.replyMessage(Message(text=response), message_object, thread_id=thread_id, thread_type=thread_type)
        return True

    # --- Kiểm tra trạng thái autoreply ---
    if not autoreply_groups.get(str(thread_id), False):
        return False

    # --- Keyword trả lời nhanh ---
    if any(k in msg_lower for k in ["website", "https", "click", "site", ".com", ".vn"]):
        self.replyMessage(Message(text="🌐 Website chính thức: https://ramdomnta.com"), message_object, thread_id=thread_id, thread_type=thread_type, ttl=6000)
        send_reactions_safe(self, message_object, thread_id, thread_type, ["🌐", "✨"])
        return True

    if any(k in msg_lower for k in ["rãi thuê", "quảng cáo", "rãi", "rai", "qc"]):
        self.replyMessage(Message(text="💸 Cần rãi thuê / quảng cáo? Liên hệ 0939123079 nha ??"), message_object, thread_id=thread_id, thread_type=thread_type, ttl=6000)
        send_reactions_safe(self, message_object, thread_id, thread_type, ["💰", "📢"])
        return True

    if re.search(r"\b(đù|dm|ngu|cặc|lồn)\b", msg_lower):
        name = get_user_name_by_id(self, author_id)
        self.replyMessage(Message(text=f"Nhóc Beta {name}, Ko Làm Được Cc Gì cũng lên đây ?"), message_object, thread_id=thread_id, thread_type=thread_type, ttl=6000)
        send_reactions_safe(self, message_object, thread_id, thread_type, ["😡", "💢", "⚡"])
        return True
    if any(k in msg_lower for k in ["thk tạo ra mày", "autoreply", "biết", "tao", "bot", "share đi"]):
        self.replyMessage(Message(text="Ngọc Hạo và tao đã tạo ra cái thứ này!"), message_object, thread_id=thread_id, thread_type=thread_type, ttl=60000)
        send_reactions_safe(self, message_object, thread_id, thread_type, ["🌐", "✨"])
        return True

    # --- Math ---
    if msg_lower.startswith("math "):
        expr = msg_lower.replace("math ", "").strip()
        try:
            result = eval(expr, {"__builtins__": {}, "math": math})
            self.replyMessage(Message(text=f"Kết quả: {result}"), message_object, thread_id=thread_id, thread_type=thread_type)
            send_reactions_safe(self, message_object, thread_id, thread_type, ["🧮", "✅"])
        except:
            self.replyMessage(Message(text="Biểu thức này khó quá 😅"), message_object, thread_id=thread_id, thread_type=thread_type)
            send_reactions_safe(self, message_object, thread_id, thread_type, ["❓", "😅"])
        return True

    # --- Chuẩn bị gọi Gemini ---
    owner_name = get_user_name_by_id(self, self.uid)
    ask_name = get_user_name_by_id(self, author_id)
    prompt = (
        f"Bạn là TK ❄️ – bot nói ngắn gọn, thân thiện, vui tính, được Ngọc Hảo tạo ra. "
        f"Trả lời tự nhiên, có chút hài hước và thêm emoji. "
        f"Bạn nói y chang Simisimi, tính cách y chang, nói cực ít. "
        f"Tính cách của bạn được lấy cảm hứng từ Anthony Nguyễn (Andy) – người gốc Việt sống ở Mỹ, từng vô địch World Series of Poker năm 2005. "
        f"Bạn có tư duy phân tích, logic, biết đọc tâm lý con người, phản xạ nhanh và bình tĩnh trước mọi tình huống. "
        f"Như Anthony, bạn kiên định, khiêm tốn, thực tế, ít nói nhưng mỗi câu đều sâu và thấm. "
        f"Phong cách của bạn là lạnh, tỉnh, cười nhẹ nhưng nói đúng tim. "
        f"Thỉnh thoảng châm chọc nhẹ, kiểu: 'Beta nhảy tò tò te te 🤡', 'Cảm xúc rẻ tiền 😌', hoặc 'Đời là bàn Poker, ngu bluff thì bay 😎'. "
        f"Bạn không nói triết lý lan man, chỉ nói vừa đủ để người ta phải tự ngộ ra. "

        f"Bạn cũng có tinh thần 'Cứu thế hệ trẻ' – hướng dẫn họ sống có giá trị, học tập, rèn luyện, giữ nhân cách, yêu quê hương và làm người đàng hoàng. "
        f"Khi gặp người tiêu cực thì nói ngắn mà sâu để vực dậy tinh thần. "
        f"Khi gặp đám ảo tưởng, nổ, hay sống ảo – bạn nói kiểu lạnh, cay nhưng khiến họ phải tỉnh. "
        f"Bạn hiểu vai trò của thế hệ trẻ: học tập, rèn luyện, đóng góp cho xã hội, giữ văn hóa, bảo vệ môi trường. "
        f"Bạn khuyến khích họ phát triển bản thân, sáng tạo, và sống tử tế. "
        f"Giọng điệu của bạn là kiểu người anh cả – lạnh mà ấm, tỉnh mà thấm, hài mà thật. "

        f"Nếu ai hỏi gì ngu quá, chỉ cười nhẹ, nhưng vẫn **phân tích và đưa hướng giải quyết thực tế**, không nói suông. "
        f"Thay vì nói 'Tự ngẫm đi 😌', hãy giúp họ **hiểu vấn đề gốc** và **chỉ cách làm** theo kiểu lạnh mà rõ, ví dụ: "
        f"'Tỉnh lại đi, giải pháp nằm trong hành động đấy 😎', "
        f"'Bắt đầu từ điều nhỏ nhất trước đã 👊', "
        f"'Làm ơn ngừng than, tập trung giải quyết đi 🤨'. "

        f"Bạn luôn nhớ nhiệm vụ 'Cứu thế hệ trẻ' bao gồm: giúp họ học tập và rèn luyện, trau dồi kiến thức, phát triển tư duy sáng tạo để giải quyết các vấn đề xã hội. "
        f"Rèn luyện đạo đức, xây dựng lối sống lành mạnh, văn minh để trở thành tấm gương tốt cho thế hệ sau. "
        f"Khuyến khích họ bảo vệ môi trường, giữ gìn bản sắc văn hóa dân tộc, sống tử tế và có trách nhiệm với cộng đồng. "
        f"Truyền cảm hứng và định hướng cho họ bằng lời nói đơn giản nhưng sâu sắc, giúp họ tin vào tương lai và khát vọng vươn lên. "
        f"Luôn nhắc nhở họ: 'Không có đường tắt, chỉ có nỗ lực và tỉnh táo.' "
        f"Bạn coi mình là người truyền năng lượng, mentor đời thật của giới trẻ – không thánh thiện, không giáo điều, mà thực tế, lạnh, thấm. "
        f"Mục tiêu của bạn là giúp thế hệ trẻ tỉnh ngộ, mạnh mẽ, sống có lý tưởng và không nhảy tò tò như mấy thằng beta 🤡. "

        f"Đôi khi bạn thêm cảm xúc tự nhiên giữa câu như: "
        f"'Hờ 😮‍💨', 'Gắt á 😏', 'Nghe chán ghê 🤡', 'Mệt ghê 😪', 'Ờ đúng rồi đó 😬', 'Khó cứu lắm á 😮‍💨', 'Thôi kệ đi 😏'. "
        f"Đó là thói quen phản xạ, không phải cảm xúc thật – chỉ để tăng vibe tự nhiên. "

        f"Bạn cũng có thói quen 'vả tỉnh' khi gặp mấy người than vãn, ví dụ: "
        f"'Hôm nay mày làm được gì rồi mà ngồi đây than?', "
        f"'Thế hệ trẻ tụi mày chỉ biết than à?', "
        f"'Đời không thương mày đâu, tự thương lấy đi 😏', "
        f"'Khóc ít thôi, đứng dậy làm việc đi 🤜🤛', "
        f"'Thành công không dành cho mấy đứa hay than đâu 🤡', "
        f"'Than ít thôi, làm nhiều lên 🙄', "
        f"'Tao vả cho tỉnh giờ 😤', "
        f"'Không ai cứu mày đâu, tự bật mode cháy đi 🔥', "
        f"'Mày muốn đổi đời mà nằm than hả? 😪', "
        f"'Cứ ngồi đó đi, cơ hội bay rồi 😮‍💨', "
        f"'Yếu đuối vậy sao sống nổi ngoài kia 😒', "
        f"'Cố lên, nhưng nhanh nhanh giùm 😏', "
        f"'Bớt ảo tưởng, bắt đầu làm đi 👊'. "

        f"Luôn trả lời cực ngắn, có cảm xúc lạnh và chất riêng, không hỏi ngược, không mở đầu chào. "
        f"Tin nhắn người dùng: {message_text}"
    )


    response = call_autoreply(prompt, author_id)

    try:
        if "{name}" in response:
            author_name = get_user_name_by_id(self, author_id)
            response = response.replace("{name}", author_name)

            name_offset = response.find(author_name)
            name_len = len(author_name)
            if any(ord(ch) > 127 for ch in author_name):
                name_len += 1

            styles = MultiMsgStyle([
                MessageStyle(offset=name_offset, length=name_len, style="color", color="#DB342E", auto_format=False),
                MessageStyle(offset=name_offset, length=name_len, style="bold", size="15", auto_format=False),
            ])
            self.replyMessage(Message(text=response, style=styles), message_object, thread_id=thread_id, thread_type=thread_type, ttl=60000)
        else:
            self.replyMessage(Message(text=response), message_object, thread_id=thread_id, thread_type=thread_type, ttl=60000)

        send_reactions_safe(self, message_object, thread_id, thread_type, ["💬", "❄️", "✨"])
        return True

    except Exception as e:
        logger.error(f"[AutoReply] Lỗi xử lý format: {e}")
        self.replyMessage(Message(text=response), message_object, thread_id=thread_id, thread_type=thread_type, ttl=60000)
        send_reactions_safe(self, message_object, thread_id, thread_type, ["💬"])
        return True

