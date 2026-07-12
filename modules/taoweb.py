import os
import time
import json
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from zlapi.models import Message
from config import PREFIX

# ====== CẤU HÌNH ======
FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
EMOJI_FONT_PATH = "modules/cache/font/NotoEmoji-Bold.ttf"
CACHE_DIR = "modules/cache/checkhost_menu_temp"
os.makedirs(CACHE_DIR, exist_ok=True)

API_BASE = "https://check-host.net"

des = {
    'version': "3.2.0",
    'credits': "ngbao",
    'description': "check host + ip host.",
    'power': "Thành Viên"
}

# ====== FONT ======
def get_font(size): return ImageFont.truetype(FONT_PATH, size)
def get_emoji_font(size): return ImageFont.truetype(EMOJI_FONT_PATH, size)

# ====== GỌI API CHECK-HOST ======
def get_check_result(host):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        }

        def safe_json(url, params=None):
            r = requests.get(url, params=params, headers=headers, timeout=10)
            if r.status_code != 200:
                return {"error": f"HTTP {r.status_code}"}
            try:
                return r.json()
            except Exception:
                text_preview = r.text[:200]
                return {"error": f"Phản hồi không phải JSON. Dữ liệu đầu: {text_preview}"}

        # ✅ Gọi API có thêm &json để ép định dạng
        ping_req = safe_json(f"{API_BASE}/check-ping?host={host}&max_nodes=1&json")
        http_req = safe_json(f"{API_BASE}/check-http?host={host}&max_nodes=1&json")
        if "error" in ping_req: return ping_req
        if "error" in http_req: return http_req

        ping_id = ping_req.get("request_id")
        http_id = http_req.get("request_id")
        if not ping_id or not http_id:
            return {"error": "Không lấy được request_id từ API"}

        # đợi kết quả xử lý (API cần vài giây)
        time.sleep(2.5)

        ping_res = safe_json(f"{API_BASE}/check-result/{ping_id}?json")
        http_res = safe_json(f"{API_BASE}/check-result/{http_id}?json")

        return {"ping": ping_res, "http": http_res}
    except Exception as e:
        return {"error": str(e)}


# ====== PHÂN TÍCH DỮ LIỆU ======
def parse_results(host, data):
    if "error" in data:
        return {"error": data["error"]}

    ping_data = data.get("ping", {})
    http_data = data.get("http", {})

    ping_values = []
    countries = []
    ips = []

    # Xử lý ping
    for loc, val in ping_data.items():
        if not val: continue
        result = val[0]
        if isinstance(result, list) and len(result) >= 4:
            ip = result[1]
            delay = result[2]
            country = loc.split("-")[0].upper()
            if delay is not None:
                ping_values.append(delay)
            if ip and ip not in ips:
                ips.append(ip)
            if country not in countries:
                countries.append(country)

    avg_ping = round(sum(ping_values)/len(ping_values), 2) if ping_values else "N/A"

    # Xử lý HTTP
    http_codes = []
    for loc, val in http_data.items():
        if not val: continue
        result = val[0]
        if isinstance(result, list) and len(result) >= 4:
            code = result[2]
            http_codes.append(str(code))
    http_status = http_codes[0] if http_codes else "N/A"

    return {
        "host": host,
        "avg_ping": avg_ping,
        "ips": ", ".join(ips) if ips else "Không rõ",
        "http": http_status,
        "countries": ", ".join(countries) if countries else "Không rõ"
    }

# ====== VẼ ẢNH KẾT QUẢ ======
def draw_result_image(result):
    image_width, image_height = 1000, 550
    bg = Image.new("RGBA", (image_width, image_height), (38, 30, 75, 255))
    draw = ImageDraw.Draw(bg)
    font_big = get_font(36)
    font = get_font(28)
    emoji_font = get_emoji_font(32)

    # Header
    draw.rounded_rectangle([40, 30, image_width-40, 100], radius=25, fill=(159,108,255,100))
    draw.text((image_width/2 - 220, 45), "🌐 KẾT QUẢ KIỂM TRA HOST 🌐", font=font_big, fill=(255,230,255))

    # Card chính
    draw.rounded_rectangle([60, 130, image_width-60, 480], radius=30, fill=(60,70,120,230), outline=(159,108,255), width=3)

    lines = [
        f"🌍 Host: {result['host']}",
        f"📡 IP: {result['ips']}",
        f"⚡ Ping trung bình: {result['avg_ping']} ms",
        f"🧩 HTTP Status: {result['http']}",
        f"🏳️ Quốc gia: {result['countries']}"
    ]
    y = 170
    for l in lines:
        draw.text((120, y), l, font=font, fill=(220,255,255))
        y += 65

    footer = f"⏰ Kiểm tra lúc: {time.strftime('%H:%M:%S %d/%m/%Y')}"
    draw.text((120, y + 30), footer, font=get_font(22), fill=(200,200,255))

    outpath = os.path.join(CACHE_DIR, f"checkhost_{int(time.time())}.jpg")
    bg = bg.convert("RGB")
    bg.save(outpath, "JPEG", quality=100, optimize=True)
    return outpath

# ====== MENU HƯỚNG DẪN ======
def show_menu_image():
    image_width, image_height = 900, 500
    bg = Image.new("RGBA", (image_width, image_height), (38, 30, 75, 255))
    draw = ImageDraw.Draw(bg)
    font = get_font(28)
    emoji_font = get_emoji_font(30)

    draw.rounded_rectangle([50, 30, image_width-50, 100], radius=30, fill=(159,108,255,110))
    draw.text((image_width/2 - 180, 50), "📡 CHECK HOST BOT MENU", font=get_font(36), fill=(255,225,255))

    lines = [
        f"💠 {PREFIX}checkhost <host> • Kiểm tra ping + HTTP",
        f"🧩 {PREFIX}checkhost google.com • Ví dụ kiểm tra",
        f"⚙️ {PREFIX}checkhost help • Hiện menu hướng dẫn",
        "",
        f"📜 Nguồn dữ liệu: check-host.net"
    ]

    y = 160
    for l in lines:
        draw.text((80, y), l, font=font, fill=(210,255,255))
        y += 60

    outpath = os.path.join(CACHE_DIR, f"checkhost_menu_{int(time.time())}.jpg")
    bg = bg.convert("RGB")
    bg.save(outpath, "JPEG", quality=100, optimize=True)
    return outpath

# ====== XỬ LÝ LỆNH ======
def handle_checkhost_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        msg_text = message_object.text.strip() if hasattr(message_object, "text") else str(message)
    except Exception:
        msg_text = str(message)

    args = msg_text.split()
    if len(args) < 2 or args[1].lower() in ["help", "menu"]:
        img_path = show_menu_image()
        with Image.open(img_path) as img:
            w, h = img.size
        client.sendLocalImage(img_path, thread_id, thread_type, width=w, height=h, ttl=120000)
        os.remove(img_path)
        return

    host = args[1]
    client.replyMessage(Message(text=f"🔍 Đang kiểm tra host `{host}`..."), message_object, thread_id, thread_type)

    data = get_check_result(host)
    result = parse_results(host, data)
    if "error" in result:
        client.replyMessage(Message(text=f"❌ Lỗi khi kiểm tra: {result['error']}"), message_object, thread_id, thread_type)
        return

    img_path = draw_result_image(result)
    with Image.open(img_path) as img:
        w, h = img.size
    client.sendLocalImage(img_path, thread_id, thread_type, width=w, height=h, ttl=120000)
    os.remove(img_path)

# ====== TRẢ VỀ ======
def PTA():
    return {'checkhost': handle_checkhost_command}
