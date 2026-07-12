import os
import json
import time
import random
import threading
import requests
import urllib.parse
from zlapi.models import Message, MultiMsgStyle, MessageStyle

des = {
    'version': "1.2.0",
    'credits': "ngbao",
    'description': "Auto dự báo thời tiết",
    'power': "Thành Viên"
}

# ===================================
# ⚙️ Cấu hình cơ bản
# ===================================
DATA_FILE = "modules/data/weather/weather_data.json"
INTERVAL = 1800  # 30 phút
AUTO_WEATHER_THREAD = None
AUTO_WEATHER_RUNNING = False
ADMIN = ["700542342650452398", "YOUR_OTHER_ADMIN_ID"]

# 🎬 TikTok API
API_URL = "https://bj-tiktok-search.ma-coder-x.workers.dev/?query={}"

# ===================================
# 🧩 Hàm phụ trợ
# ===================================
def _reply_styled_message(client, content, message_object, thread_id, thread_type, author_id):
    try:
        user_info = client.fetchUserInfo(author_id)
        author_name = user_info.changed_profiles.get(str(author_id), {}).get('zaloName', 'Không xác định') \
            if user_info and user_info.changed_profiles else 'Không xác định'
    except Exception:
        author_name = "Không xác định"

    msg = f"{author_name}\n➜ {content}"
    styles = MultiMsgStyle([
        MessageStyle(offset=0, length=len(author_name), style="bold", auto_format=False),
        MessageStyle(offset=0, length=len(author_name), style="color", color="#1e90ff", auto_format=False),
    ])
    client.replyMessage(
        Message(text=msg, style=styles),
        message_object,
        thread_id,
        thread_type,
        ttl=12000
    )


def _load_data():
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    if not os.path.exists(DATA_FILE):
        return {"enabled": False, "location": "Ho Chi Minh"}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"enabled": False, "location": "Ho Chi Minh"}


def _save_data(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def _get_weather(location):
    try:
        url = f"https://wttr.in/{location}?format=%C+🌡️%t+💧%h"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            return res.text.strip()
        return "❌ Không lấy được dữ liệu thời tiết."
    except Exception as e:
        return f"⚠️ Lỗi khi lấy dữ liệu: {e}"


# ===================================
# 🎬 Gửi video TikTok
# ===================================
def _send_tiktok_video(client, thread_id, thread_type, caption_text, keyword="weather sky"):
    try:
        encoded = urllib.parse.quote(keyword)
        res = requests.get(f"https://bj-tiktok-search.ma-coder-x.workers.dev/?query={encoded}", timeout=10)
        res.raise_for_status()
        data = res.json()
        if data.get("status") and data.get("data"):
            vids = data["data"]
            v = random.choice(vids)
            play_url = v.get("no_watermark")
            cover_url = v.get("cover")
            if play_url:
                client.sendRemoteVideo(
                    videoUrl=play_url,
                    thumbnailUrl=cover_url,
                    duration=15000,
                    message=Message(text=caption_text),
                    thread_id=thread_id,
                    thread_type=thread_type,
                    width=1080,
                    height=1920,
                    ttl=600000
                )
                print(f"[AUTO-WEATHER] 🎬 Đã gửi video TikTok ({keyword})")
                return True
    except Exception as e:
        print(f"[AUTO-WEATHER] ⚠️ Lỗi gửi video: {e}")
    return False


# ===================================
# 🔁 Auto loop
# ===================================
def _auto_weather_loop(client, thread_id, thread_type, location):
    global AUTO_WEATHER_RUNNING

    first = True
    while AUTO_WEATHER_RUNNING:
        try:
            if not first:
                time.sleep(INTERVAL)
            first = False

            weather_info = _get_weather(location)
            msg_text = (
                " BẢN TIN THỜI TIẾT (AUTO)\n"
                f"🏙️ Khu vực: {location}\n"
                f"🕒 Thời gian: {time.strftime('%H:%M:%S - %d/%m/%Y')}\n"
                f"🌡️ Tình hình: {weather_info}\n"
                "🪶 Chúc bạn một ngày tuyệt vời \n"
                "⏳ Lần cập nhật tiếp theo sau 30 phút\n"
            )

            sent = _send_tiktok_video(client, thread_id, thread_type, msg_text, keyword="weather scenery")
            if not sent:
                client.sendMessage(Message(text=msg_text), thread_id, thread_type, ttl=400000)

        except Exception as e:
            print(f"[AUTO-WEATHER] ⚠️ Lỗi vòng lặp: {e}")
            time.sleep(30)

    print("[AUTO-WEATHER] 🔴 Đã dừng auto weather.")


# ===================================
# 💬 Command handler
# ===================================
def handle_weather_command(message, message_object, thread_id, thread_type, author_id, client):
    global AUTO_WEATHER_RUNNING, AUTO_WEATHER_THREAD

    args = message.strip().split(maxsplit=2)
    subcmd = args[1].lower() if len(args) > 1 else None
    data = _load_data()



    if subcmd == "on":
        if AUTO_WEATHER_RUNNING:
            _reply_styled_message(client, "⚠️ Auto weather đã bật sẵn!", message_object, thread_id, thread_type, author_id)
            return
        AUTO_WEATHER_RUNNING = True
        data["enabled"] = True
        _save_data(data)
        AUTO_WEATHER_THREAD = threading.Thread(
            target=_auto_weather_loop,
            args=(client, thread_id, thread_type, data.get("location", "Ho Chi Minh")),
            daemon=True
        )
        AUTO_WEATHER_THREAD.start()
        _reply_styled_message(client, "✅ Đã bật auto weather (mỗi 30 phút).", message_object, thread_id, thread_type, author_id)
        return

    elif subcmd == "off":
        if not AUTO_WEATHER_RUNNING:
            _reply_styled_message(client, "⚠️ Auto weather chưa bật.", message_object, thread_id, thread_type, author_id)
            return
        AUTO_WEATHER_RUNNING = False
        data["enabled"] = False
        _save_data(data)
        _reply_styled_message(client, "🛑 Đã tắt auto weather.", message_object, thread_id, thread_type, author_id)
        return

    elif subcmd == "set":
        if len(args) < 3:
            _reply_styled_message(client, "⚠️ Vui lòng nhập địa điểm.\nVí dụ: weather set Ha Noi", message_object, thread_id, thread_type, author_id)
            return
        new_loc = args[2]
        data["location"] = new_loc
        _save_data(data)
        _reply_styled_message(client, f"✅ Đã đổi khu vực thành: {new_loc}", message_object, thread_id, thread_type, author_id)
        return

    elif subcmd == "now":
        location = data.get("location", "Ho Chi Minh")
        weather_info = _get_weather(location)
        msg_text = f"🌦️ **Thời tiết hiện tại tại {location}:**\n{weather_info}"
        sent = _send_tiktok_video(client, thread_id, thread_type, msg_text, keyword="weather landscape")
        if not sent:
            _reply_styled_message(client, msg_text, message_object, thread_id, thread_type, author_id)
        return

    else:
        _reply_styled_message(client,
            "⚙️ Cú pháp hợp lệ:\n"
            "• autoweather now → Xem thời tiết hiện tại\n"
            "• autoweather on → Bật auto (admin)\n"
            "• autoweather off → Tắt auto (admin)\n"
            "• autoweather set <khu vực> → Đặt địa điểm (admin)",
            message_object, thread_id, thread_type, author_id
        )


# ✅ Đăng ký lệnh
def PTA():
    return {'autoweather': handle_weather_command}
