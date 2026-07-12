import requests
import os
import json
import random
import logging
import datetime
from zlapi.models import Message, Mention

des = {
    'version': "2.6.1",
    'credits': "ngbao",
    'description': "AI Pam",
    'power': "Thành Viên"
}

GEMINI_API_KEY = "AIzaSyCQB0lWBqyHHDQe2HU3o3UrvAAtGuZO23w"
conversation_states = {}
style_states = {}

# ==========================================
# 🔥 PAM AUTOREPLY ON/OFF
# ==========================================
pam_auto_mode = True   # mặc định ON
pam_keywords = ["pam", "Pam", "@Pam", "@pam"]


def two_random_colors():
    color_list = ["DB342E", "15A85F", "F27806", "F7B503", "4287F5", "A832F5", "F542B9"]
    c1 = random.choice(color_list)
    c2 = random.choice([c for c in color_list if c != c1])
    return c1, c2

STYLE_PROMPTS = [
    "Vợ ngọt ngào, nói chuyện tình cảm 🥰",
    "Mát dại, chửi tục 😆",
    "Nhẹ nhàng, nói chuyện tinh tế 💕",
    "Dễ thương, nói nhanh, nhiều cảm xúc 😄",
    "Lạnh lùng, ít nói, cuốn hút 🧊"
]


# ==========================================
# 🔥 HÀM TỰ TRẢ LỜI NHƯ RIN (CÓ ON/OFF)
# ==========================================
def auto_reply_pam(message_object, thread_id, thread_type, author_id, client):
    global pam_auto_mode

    # Nếu Pam OFF → không trả lời
    if not pam_auto_mode:
        return False

    # Nếu không có tag → bỏ qua
    if not hasattr(message_object, "mentions") or not message_object.mentions:
        return False

    # Kiểm tra xem có tag Pam không
    for mention in message_object.mentions:
        if mention.uid == client.uid:   # Bot bị tag
            text = message_object.text or ""

            # Lọc câu hỏi (bỏ phần tag)
            user_question = text.replace(mention.text, "").strip()
            if user_question == "":
                user_question = "gọi Pam có chuyện gì đóa? 😆"

            # Gửi vào AI xử lý
            handle_gemini_command(
                f"pam {user_question}",
                message_object, thread_id, thread_type,
                author_id, client
            )
            return True

    return False



# ==========================================================
# 🔥 PHẦN XỬ LÝ LỆNH CHÍNH (CÓ THÊM pam on/off)
# ==========================================================
def handle_gemini_command(message, message_object, thread_id, thread_type, author_id, client):
    global pam_auto_mode

    parts = message.strip().split()
    user_question = " ".join(parts[1:]).strip() if len(parts) > 1 else ""
    username = get_username(author_id, client)

    # ======================
    # 🔘 PAM ON
    # ======================
    if len(parts) >= 2 and parts[1].lower() == "on":
        pam_auto_mode = True
        client.replyMessage(
            Message(text="🟢 Pam đã bật chế độ tự động trả lời!"),
            message_object, thread_id, thread_type
        )
        return

    # ======================
    # 🔘 PAM OFF
    # ======================
    if len(parts) >= 2 and parts[1].lower() == "off":
        pam_auto_mode = False
        client.replyMessage(
            Message(text="🔴 Pam đã tắt chế độ tự động trả lời!"),
            message_object, thread_id, thread_type
        )
        return

    # Gốc code cũ giữ nguyên ↓↓↓

    if hasattr(message_object, 'mentions') and message_object.mentions:
        if any(mention.uid == client.uid for mention in message_object.mentions):
            if not user_question:
                greetings = [
                    f"👋 Chào {username} nha!",
                    f"🥰 Ủa {username} gọi Pam hả?",
                    f"💬 Pam đây nè {username}~",
                    f"😊 Có gì muốn hỏi Pam không {username}?",
                ]
                mention = message_object.mentions[0]
                client.replyMessage(
                    Message(text=random.choice(greetings), mention=mention),
                    thread_id=thread_id,
                    thread_type=thread_type,
                    replyMsg=message_object,
                    ttl=120000
                )
                return

    if len(parts) >= 3 and parts[1] == "style" and parts[2] == "list":
        c1, c2 = two_random_colors()
        lines = ["🌈 Danh sách phong cách của Pam:"]
        for i, s in enumerate(STYLE_PROMPTS, start=1):
            lines.append(f"{i}. {s}")
        text = "\n".join(lines)
        style_json = json.dumps({
            "styles": [
                {"start": 0, "len": len(lines[0]), "st": f"b,c_{c1},f_18"},
                {"start": len(lines[0])+1, "len": len(text)-len(lines[0])-1, "st": f"b,c_{c2},f_17"},
            ],
            "ver": 0
        })
        client.replyMessage(Message(text=text, style=style_json), message_object, thread_id, thread_type)
        return

    if len(parts) >= 2 and parts[1] == "menu":
        c1, c2 = two_random_colors()
        text = (
            "🍜 𝗣𝗮𝗺 Đ𝗮𝗺 𝗠ê Ă𝗻 𝗨𝗼̂́𝗻𝗴 🍰\n"
            "───────\n"
            "🥢 ,pam <nội dung> — Nói chuyện cùng Pam\n"
            "🎨 ,pam style list — Xem danh sách phong cách\n"
            "💄 ,pam style <số> — Chọn phong cách nói\n"
            "🧹 ,pam clear — Xoá lịch sử trò chuyện\n"
            "🔘 pam on/off — Bật/tắt auto trả lời\n"
            "🍱 ,pam menu — Hiển thị menu này\n"
            "───────\n"
            "💋 Pam mê ăn uống lắm nha 😘"
        )
        c1, c2 = two_random_colors()
        style_json = json.dumps({
            "styles": [
                {"start": 0, "len": len("🍜 𝗣𝗮𝗺 Đ𝗮𝗺 𝗠ê Ă𝗻 𝗨𝗼̂́𝗻𝗴 🍰"), "st": f"b,c_{c1},f_18"},
                {"start": len("🍜 𝗣𝗮𝗺 Đ𝗮𝗺 𝗠ê Ă𝗻 𝗨𝗼̂́𝗻𝗴 🍰\n───────\n"), "len": len(text), "st": f"b,c_{c2},f_17"},
            ],
            "ver": 0
        })
        client.replyMessage(Message(text=text, style=style_json), message_object, thread_id, thread_type)
        return

    if len(parts) >= 3 and parts[1] == "style" and parts[2].isdigit():
        idx = int(parts[2]) - 1
        if 0 <= idx < len(STYLE_PROMPTS):
            style_states[thread_id] = idx
            text = f"✅ Pam đã chuyển phong cách sang: {STYLE_PROMPTS[idx]}"
            c1, c2 = two_random_colors()
            style_json = json.dumps({
                "styles": [
                    {"start": 0, "len": 2, "st": f"b,c_{c1},f_18"},
                    {"start": 3, "len": len(text)-3, "st": f"b,c_{c2},f_17"},
                ],
                "ver": 0
            })
            client.replyMessage(Message(text=text, style=style_json),
                                message_object, thread_id, thread_type)
        else:
            text = "❌ Số thứ tự phong cách không hợp lệ!"
            client.replyMessage(Message(text=text), message_object, thread_id, thread_type)
        return

    if len(parts) >= 2 and parts[1] == "clear":
        conversation_states.pop(thread_id, None)
        client.replyMessage(
            Message(text="🧹 Pam đã xoá lịch sử trò chuyện!"),
            message_object, thread_id, thread_type
        )
        return

    if not user_question:
        client.replyMessage(
            Message(text="• Gọi Pam mà không nói gì là bị phạt nè 😝"),
            message_object, thread_id, thread_type
        )
        return

    try:
        client.sendReaction(message_object, "OK", thread_id, thread_type, reactionType=75)
    except:
        pass

    conversation_state = conversation_states.get(thread_id, {'history': []})
    gemini_response = get_gemini_response(user_question, conversation_state, thread_id, author_id)

    if gemini_response:
        tag_text = f"@{get_name_from_id(client, author_id)}"
        pam_text = "Pam nói:"
        content_text = gemini_response

        full_text = f"{tag_text} {pam_text}\n{content_text}"

        client.replyMessage(
            Message(
                text=full_text,
                mention=Mention(author_id, length=len(tag_text), offset=0)
            ),
            message_object, thread_id, thread_type
        )

    else:
        client.replyMessage(
            Message(text=f"@{get_name_from_id(client, author_id)} • Pam không hiểu á 🥺",
                    mention=Mention(author_id, length=1, offset=0)),
            message_object, thread_id, thread_type
        )


# ======================== GEMINI RESPONSE ========================
def get_gemini_response(user_question, conversation_state, thread_id, author_id):
    api_url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-2.5-flash-preview-05-20:generateContent?key=" + GEMINI_API_KEY
    )
    headers = {'Content-Type': 'application/json'}

    style_idx = style_states.get(thread_id, 0)
    tone_desc = STYLE_PROMPTS[style_idx]

    prompt = f"Pam phong cách: {tone_desc}\nNgười dùng hỏi: {user_question}\nTrả lời tự nhiên, dễ thương.\n"

    data = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()

        if 'candidates' in result:
            for c in result['candidates']:
                if 'content' in c:
                    for part in c['content']['parts']:
                        if 'text' in part:
                            conversation_state['history'].append({'role': 'user', 'text': user_question})
                            conversation_state['history'].append({'role': 'pam', 'text': part['text']})
                            conversation_states[thread_id] = conversation_state
                            return part['text']

    except:
        return None


def get_name_from_id(client, uid):
    try:
        user = client.getUserInfo(uid)
        return user.display_name or "Member"
    except:
        return "Member"

def get_username(uid, client):
    try:
        user = client.getUserInfo(uid)
        return user.display_name or "Bạn"
    except:
        return "Bạn"


# ========================= EXPORT =========================
def PTA():
    return {
        'pam': handle_gemini_command,
        'autoreply_pam': auto_reply_pam
    }
