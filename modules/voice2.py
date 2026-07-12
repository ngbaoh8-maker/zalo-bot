import os
import time
import requests
from gtts import gTTS
from zlapi.models import Message
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from config import PREFIX

FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
CACHE_DIR = "modules/cache/voice_temp"
os.makedirs(CACHE_DIR, exist_ok=True)

des = {
    'version': "1.0.0",
    'credits': "ngbao",
    'description': "Chuyển văn bản thành giọng nói (Text → Voice)",
    'power': "Thành Viên"
}

# ========== FONT ==========

def get_font(size):
    return ImageFont.truetype(FONT_PATH, size)

# ========== IMAGE MENU ==========

def draw_menu_image():
    w, h = 1000, 620
    bg = Image.new("RGBA", (w, h), (38, 30, 75, 255))
    draw = ImageDraw.Draw(bg)
    font = get_font(28)

    title = "🎙️ LỆNH CHUYỂN VĂN BẢN → GIỌNG NÓI 🎙️"
    draw.text((w//2 - font.getlength(title)//2, 40), title, font=font, fill=(255,230,255))

    lines = [
        f"💬 {PREFIX}voice <văn bản> • Tạo file giọng nói từ văn bản.",
        "📢 Bot sẽ gửi lại file .mp3 bạn có thể nghe hoặc tải.",
        "",
        f"🌐 Phiên bản: {des['version']}",
        f"👤 Tác giả: {des['credits']}",
        f"🔑 Quyền: {des['power']}"
    ]

    y = 140
    for line in lines:
        draw.text((80, y), line, font=get_font(26), fill=(210,240,255))
        y += 50

    out_path = os.path.join(CACHE_DIR, f"voice_menu_{os.getpid()}_{int(time.time())}.jpg")
    bg = bg.convert("RGB")
    bg.save(out_path, "JPEG", quality=100, optimize=True)
    return out_path

# ========== CORE FUNCTION ==========

def handle_voice_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        if not message or message.strip() in ["help", "menu"]:
            img_path = draw_menu_image()
            from PIL import Image
            with Image.open(img_path) as im:
                width, height = im.size
            client.sendLocalImage(img_path, thread_id, thread_type, width=width, height=height, ttl=120000)
            if os.path.exists(img_path):
                os.remove(img_path)
            return

        text = message.strip()
        if len(text) < 3:
            client.replyMessage(Message(text="⚠️ Vui lòng nhập văn bản cần chuyển thành giọng nói."), message_object, thread_id, thread_type)
            return

        # === Tạo file voice bằng gTTS ===
        voice_file = os.path.join(CACHE_DIR, f"voice_{int(time.time())}.mp3")
        tts = gTTS(text=text, lang='vi')
        tts.save(voice_file)

        # === Upload lên Uguu ===
        uploaded_url = upload_to_uguu(voice_file)
        if not uploaded_url:
            client.replyMessage(Message(text="❌ Lỗi upload file voice, thử lại sau."), message_object, thread_id, thread_type)
            return

        # === Gửi voice ===
        if hasattr(client, 'sendRemoteVoice'):
            client.sendRemoteVoice(uploaded_url, thread_id, thread_type)
        else:
            client.send_message(thread_id, thread_type, f"🎧 Voice: {uploaded_url}")

        if os.path.exists(voice_file):
            os.remove(voice_file)

    except Exception as e:
        print(f"❌ Voice command error: {e}")
        client.replyMessage(Message(text="⚠️ Lỗi khi tạo giọng nói, thử lại sau."), message_object, thread_id, thread_type)


def upload_to_uguu(file_path):
    """Upload file voice lên Uguu"""
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        with open(file_path, 'rb') as f:
            files = {'files[]': f}
            r = requests.post("https://uguu.se/upload", files=files, headers=headers)
        if r.status_code == 200:
            js = r.json()
            if js.get("success"):
                return js["files"][0]["url"]
        return None
    except Exception as e:
        print(f"Uguu upload error: {e}")
        return None

# ========== EXPORT MODULE ==========

def PTA():
    return {
        'voice2': handle_voice_command
    }
