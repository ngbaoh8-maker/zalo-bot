import os
import json
import time
import math
import socket
import platform
import random
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from zlapi.models import Message
from config import PREFIX

des = {
    "version": "1.0.2",
    "credits": "ngbao",
    "description": "Lệnh sysinfo.",
    "power": "Admin"
}

FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
EMOJI_FONT_PATH = "modules/cache/font/NotoEmoji-Bold.ttf"
BACKGROUND_PATH = "background/"

DATA_DIR = "data"
SETTINGS_PATH = os.path.join(DATA_DIR, "sysinfo_settings.json")

CACHE_DIR = "modules/cache/sysinfo"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(BACKGROUND_PATH, exist_ok=True)

START_TIME = time.time()

try:
    import psutil
except Exception:
    psutil = None

def _default_settings():
    return {
        "owner": "DucDuydzai cuto",
        "bot_version": "v2.0.1",
        "title": "SYSTEM MONITOR",
        "online_text": "ONLINE",
        "footer_ok": "✨ Bot đang hoạt động ổn định!",
        "powered_by": "Powered by DucDuydzai cuto ✨",
        "theme": {
            "w": 1536,
            "h": 768,
            "bg1": [10, 14, 22],
            "bg2": [18, 28, 44],
            "panel": [20, 28, 42, 190],
            "panel2": [16, 22, 34, 170],
            "text": [235, 245, 255, 240],
            "muted": [160, 175, 195, 210],
            "stroke": [80, 110, 160, 80],
            "grid": [100, 140, 200, 30]
        }
    }

def load_settings():
    if not os.path.exists(SETTINGS_PATH):
        s = _default_settings()
        save_settings(s)
        return s
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        base = _default_settings()
        base.update({k: data.get(k, base[k]) for k in base.keys()})
        if isinstance(data.get("theme"), dict):
            base["theme"].update(data["theme"])
        return base
    except Exception:
        s = _default_settings()
        save_settings(s)
        return s

def save_settings(data):
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _font(path, size):
    try:
        if path and os.path.exists(path):
            return ImageFont.truetype(path, size)
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()

def get_font(size):
    return _font(FONT_PATH, size)

def get_emoji_font(size):
    return _font(EMOJI_FONT_PATH, size)

def fmt_bytes(n):
    try:
        n = float(n)
    except Exception:
        return "unknown"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while n >= 1024 and i < len(units) - 1:
        n /= 1024.0
        i += 1
    if i <= 1:
        return f"{int(n)} {units[i]}"
    return f"{n:.1f} {units[i]}"

def get_uptime():
    s = int(time.time() - START_TIME)
    days = s // 86400
    s %= 86400
    hours = s // 3600
    s %= 3600
    mins = s // 60
    secs = s % 60
    if days > 0:
        return f"{days}d {hours}h {mins}m {secs}s"
    if hours > 0:
        return f"{hours}h {mins}m {secs}s"
    if mins > 0:
        return f"{mins}m {secs}s"
    return f"{secs}s"

def get_ip_local():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.8)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "unknown"

def measure_ping_ms(host="8.8.8.8", port=53, timeout=1.0):
    try:
        t0 = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        sock.close()
        ms = (time.time() - t0) * 1000.0
        return int(ms)
    except Exception:
        return None

def count_modules_loaded(modules_dir="modules"):
    try:
        if not os.path.exists(modules_dir):
            return None
        cnt = 0
        for root, _, files in os.walk(modules_dir):
            for fn in files:
                if fn.endswith(".py") and fn not in ("__init__.py",):
                    cnt += 1
        return cnt
    except Exception:
        return None

def get_sys_numbers():
    cpu_pct = None
    ram_pct = None
    ram_used = None
    ram_total = None
    disk_pct = None
    disk_used = None
    disk_total = None

    if psutil:
        try:
            cpu_pct = psutil.cpu_percent(interval=0.15)
        except Exception:
            cpu_pct = None

        try:
            vm = psutil.virtual_memory()
            ram_pct = float(vm.percent)
            ram_used = fmt_bytes(vm.used)
            ram_total = fmt_bytes(vm.total)
        except Exception:
            pass

        try:
            du = psutil.disk_usage("/")
            disk_pct = float(du.percent)
            disk_used = fmt_bytes(du.used)
            disk_total = fmt_bytes(du.total)
        except Exception:
            pass

    return {
        "cpu_pct": cpu_pct,
        "ram_pct": ram_pct,
        "ram_used": ram_used,
        "ram_total": ram_total,
        "disk_pct": disk_pct,
        "disk_used": disk_used,
        "disk_total": disk_total
    }

def rounded(draw, box, r, fill=None, outline=None, width=2):
    draw.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)

def add_glass_panel(base, box, r=22, fill=(20, 28, 42, 180), stroke=(80, 110, 160, 80), glow=(90, 160, 255, 110)):
    x0, y0, x1, y1 = box
    crop = base.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(6))
    base.paste(crop, (x0, y0))

    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    rounded(od, box, r, fill=fill, outline=stroke, width=2)

    glow_layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_layer)
    rounded(gd, box, r, fill=None, outline=glow, width=8)
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(10))

    base.alpha_composite(glow_layer)
    base.alpha_composite(overlay)

def get_random_background(W, H):
    try:
        if os.path.exists(BACKGROUND_PATH):
            image_files = [f for f in os.listdir(BACKGROUND_PATH) 
                          if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp'))]
            if image_files:
                bg_file = random.choice(image_files)
                bg_path = os.path.join(BACKGROUND_PATH, bg_file)
                bg_img = Image.open(bg_path).convert("RGBA")
                
                bg_width, bg_height = bg_img.size
                
                target_ratio = W / H
                bg_ratio = bg_width / bg_height
                
                if bg_ratio > target_ratio:
                    new_height = H
                    new_width = int(new_height * bg_ratio)
                else:
                    new_width = W
                    new_height = int(new_width / bg_ratio)
                
                bg_img = bg_img.resize((new_width, new_height), Image.LANCZOS)
                
                left = (new_width - W) // 2
                top = (new_height - H) // 2
                right = left + W
                bottom = top + H
                
                cropped = bg_img.crop((left, top, right, bottom))
                
                return cropped
    except Exception:
        pass
    
    return None

def draw_bg(w, h, theme):
    random_bg = get_random_background(w, h)
    if random_bg:
        bg = random_bg
    else:
        bg = Image.new("RGBA", (w, h), tuple(theme["bg1"]) + (255,))
        d = ImageDraw.Draw(bg)
        for y in range(h):
            t = y / max(1, h - 1)
            r = int(theme["bg1"][0] * (1 - t) + theme["bg2"][0] * t)
            g = int(theme["bg1"][1] * (1 - t) + theme["bg2"][1] * t)
            b = int(theme["bg1"][2] * (1 - t) + theme["bg2"][2] * t)
            d.line((0, y, w, y), fill=(r, g, b, 255))

    grid = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid)
    step = 56
    col = tuple(theme["grid"])
    for x in range(0, w, step):
        gd.line((x, 0, x, h), fill=col, width=1)
    for y in range(0, h, step):
        gd.line((0, y, w, y), fill=col, width=1)
    bg.alpha_composite(grid)
    
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 80))
    bg.alpha_composite(overlay)
    
    return bg

def hsv_to_rgb(h, s=1.0, v=1.0):
    i = int(h * 6.0)
    f = (h * 6.0) - i
    p = int(255 * v * (1.0 - s))
    q = int(255 * v * (1.0 - f * s))
    t = int(255 * v * (1.0 - (1.0 - f) * s))
    v = int(255 * v)
    i %= 6
    if i == 0: return (v, t, p)
    if i == 1: return (q, v, p)
    if i == 2: return (p, v, t)
    if i == 3: return (p, q, v)
    if i == 4: return (t, p, v)
    return (v, p, q)

def draw_rainbow_arc(draw, bbox, start_deg, end_deg, width, alpha=255):
    span = end_deg - start_deg
    steps = max(40, int(abs(span) * 2))
    for i in range(steps):
        t0 = i / steps
        t1 = (i + 1) / steps
        a0 = start_deg + span * t0
        a1 = start_deg + span * t1
        col = hsv_to_rgb(t0)
        draw.arc(bbox, start=a0, end=a1, fill=(col[0], col[1], col[2], alpha), width=width)

def draw_gradient_text(base, x, y, text, font, glow=True):
    w = int(font.getlength(text)) + 10
    h = font.size + 14

    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask)
    md.text((0, 0), text, font=font, fill=255)

    grad = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad, "RGBA")
    for i in range(w):
        t = i / max(1, w - 1)
        col = hsv_to_rgb(t)
        gd.line((i, 0, i, h), fill=(col[0], col[1], col[2], 255))

    if glow:
        gl = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        gld = ImageDraw.Draw(gl, "RGBA")
        gld.text((0, 0), text, font=font, fill=(255, 255, 255, 120))
        gl = gl.filter(ImageFilter.GaussianBlur(5))
        base.alpha_composite(gl, (x, y))

    base.paste(grad, (x, y), mask)

def draw_gauge(base, cx, cy, radius, thickness, pct, label, subtext, icon_emoji, theme, style="gold"):
    draw = ImageDraw.Draw(base, "RGBA")

    start = 225
    end = -45
    span = 360 - (start - end)

    box = (cx - radius, cy - radius, cx + radius, cy + radius)
    draw.arc(box, start=start, end=start + span, fill=(70, 90, 120, 120), width=thickness)

    if pct is None:
        fill_span = 0
        pct_text = "N/A"
    else:
        pct = max(0.0, min(100.0, float(pct)))
        fill_span = span * (pct / 100.0)
        pct_text = f"{pct:.1f}%"

    if fill_span > 0:
        if style == "gold":
            col = (255, 200, 120, 240)
            glow_col = (255, 220, 140, 130)
        else:
            col = (140, 220, 255, 240)
            glow_col = (140, 220, 255, 130)

        glow = Image.new("RGBA", base.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow, "RGBA")
        gd.arc(box, start=start, end=start + fill_span, fill=glow_col, width=thickness + 8)
        glow = glow.filter(ImageFilter.GaussianBlur(12))
        base.alpha_composite(glow)

        draw.arc(box, start=start, end=start + fill_span, fill=col, width=thickness)

        ang = math.radians(start + fill_span)
        px = cx + int(math.cos(ang) * (radius - thickness // 2))
        py = cy + int(math.sin(ang) * (radius - thickness // 2))
        draw.ellipse((px - 7, py - 7, px + 7, py + 7), fill=(255, 255, 255, 230))

    f_icon = get_emoji_font(42)
    f_big = get_font(38)
    f_small = get_font(16)
    f_sub = get_font(14)

    iw = f_icon.getlength(icon_emoji)
    draw.text((cx - iw / 2, cy - 56), icon_emoji, font=f_icon, fill=tuple(theme["text"]))

    tw = f_big.getlength(pct_text)
    draw.text((cx - tw / 2, cy - 8), pct_text, font=f_big, fill=tuple(theme["text"]))

    lw = f_small.getlength(label)
    draw.text((cx - lw / 2, cy + 32), label, font=f_small, fill=tuple(theme["muted"]))

    if subtext:
        sw = f_sub.getlength(subtext)
        draw.text((cx - sw / 2, cy + 52), subtext, font=f_sub, fill=(160, 180, 210, 200))

def draw_title(base, x, y, text, size=44):
    font = get_font(size)
    base_draw = ImageDraw.Draw(base, "RGBA")
    base_draw.text((x, y), text, font=font, fill=(210, 225, 245, 240))

def build_sysinfo_image(settings, user_name=None):
    th = settings["theme"]
    W, H = int(th["w"]), int(th["h"])

    bg = draw_bg(W, H, th)
    draw = ImageDraw.Draw(bg, "RGBA")

    main_box = (30, 30, W - 30, H - 30)
    add_glass_panel(
        bg, main_box, r=26,
        fill=tuple(th["panel"]),
        stroke=tuple(th["stroke"]),
        glow=(90, 160, 255, 95)
    )

    f_ico = get_emoji_font(42)
    draw.text((40, 55), "💻", font=f_ico, fill=tuple(th["text"]))
    draw_title(bg, 90, 60, settings.get("title", "SYSTEM MONITOR"), size=44)

    pill_text = settings.get("online_text", "ONLINE")
    f_pill = get_font(18)
    pw = f_pill.getlength(pill_text)
    px1 = W - 70
    px0 = int(px1 - pw - 40)
    py0 = 60
    py1 = 92
    rounded(draw, (px0, py0, px1, py1), 16, fill=(30, 60, 45, 200), outline=(70, 210, 130, 200), width=2)
    draw.text((px0 + 20, py0 + 7), pill_text, font=f_pill, fill=(120, 255, 180, 240))

    sysn = get_sys_numbers()
    cpu_pct = sysn["cpu_pct"]
    ram_pct = sysn["ram_pct"]
    disk_pct = sysn["disk_pct"]

    cy = 220
    radius = 105
    thickness = 16

    draw_gauge(bg, cx=320, cy=cy, radius=radius, thickness=thickness,
               pct=cpu_pct, label="CPU", subtext="", icon_emoji="🧠", theme=th, style="blue")

    ram_sub = f"{sysn['ram_used']}/{sysn['ram_total']}" if sysn["ram_used"] and sysn["ram_total"] else ""
    draw_gauge(bg, cx=770, cy=cy, radius=radius, thickness=thickness,
               pct=ram_pct, label="RAM", subtext=ram_sub, icon_emoji="💾", theme=th, style="gold")

    disk_sub = f"{sysn['disk_used']}/{sysn['disk_total']}" if sysn["disk_used"] and sysn["disk_total"] else ""
    draw_gauge(bg, cx=1185, cy=cy, radius=radius, thickness=thickness,
               pct=disk_pct, label="Storage", subtext=disk_sub, icon_emoji="🗄️", theme=th, style="gold")

    card_w = 450
    card_h = 85
    gap_x = 25
    gap_y = 18
    x0 = 110
    y0 = 350

    def info_card(x, y, icon, title, value, accent_rgb=(120, 255, 200), rainbow_value=False, value_color=None):
        box = (x, y, x + card_w, y + card_h)
        add_glass_panel(
            bg, box, r=18,
            fill=tuple(th["panel2"]),
            stroke=(90, 130, 190, 80),
            glow=(accent_rgb[0], accent_rgb[1], accent_rgb[2], 90)
        )
        d = ImageDraw.Draw(bg, "RGBA")
        fi = get_emoji_font(28)
        ft = get_font(18)
        fv = get_font(26)

        d.text((x + 18, y + 24), icon, font=fi, fill=tuple(th["text"]))
        d.text((x + 60, y + 18), title, font=ft, fill=tuple(th["muted"]))

        if rainbow_value:
            draw_gradient_text(bg, x + 60, y + 40, value, fv, glow=True)
        else:
            if value_color is None:
                value_color = tuple(th["text"])
            d.text((x + 60, y + 40), value, font=fv, fill=value_color)

    os_name = platform.system() or "unknown"
    pyver = platform.python_version() or "unknown"
    botver = settings.get("bot_version", "v2.0.1")
    ip = get_ip_local()
    mods = count_modules_loaded("modules")
    ping = measure_ping_ms()
    ping_text = f"{ping}ms" if ping is not None else "unknown"
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    uptime = get_uptime()
    
    owner = user_name if user_name else settings.get("owner", "DucDuydzai cuto")
    powered_by = f"Powered by {owner} ✨"

    info_card(x0, y0, "⚙️", "Operating System", os_name, (120, 220, 255), rainbow_value=False, value_color=(170, 200, 255, 240))
    info_card(x0 + card_w + gap_x, y0, "🐍", "Python Version", pyver, (120, 255, 200), rainbow_value=False, value_color=(120, 255, 200, 240))
    info_card(x0 + (card_w + gap_x) * 2, y0, "🤖", "Bot Version", botver, (255, 200, 130), rainbow_value=False, value_color=(255, 160, 160, 240))

    info_card(x0, y0 + card_h + gap_y, "🌐", "IP Address", ip, (120, 220, 255), rainbow_value=False, value_color=(120, 255, 200, 240))
    info_card(x0 + card_w + gap_x, y0 + card_h + gap_y, "📦", "Modules Loaded",
              f"{mods} modules" if mods is not None else "unknown", (120, 255, 200), rainbow_value=False, value_color=(120, 255, 200, 240))
    info_card(x0 + (card_w + gap_x) * 2, y0 + card_h + gap_y, "📡", "Network Ping", ping_text,
              (120, 255, 200), rainbow_value=False, value_color=(120, 255, 200, 240))

    info_card(x0, y0 + (card_h + gap_y) * 2, "⏱️", "Uptime", uptime, (120, 255, 200), rainbow_value=False, value_color=(120, 255, 200, 240))
    info_card(x0 + card_w + gap_x, y0 + (card_h + gap_y) * 2, "📅", "Current Time", now, (180, 200, 255), rainbow_value=False)
    info_card(x0 + (card_w + gap_x) * 2, y0 + (card_h + gap_y) * 2, "👑", "Owner", owner, (255, 220, 140), rainbow_value=False, value_color=(255, 220, 140, 240))

    f_footer = get_font(20)
    draw.text((70, H - 90), settings.get("footer_ok", "✨ Bot đang hoạt động ổn định!"),
              font=f_footer, fill=(120, 255, 180, 220))

    f_pw = get_font(18)
    pwtxt = powered_by
    pw_w = f_pw.getlength(pwtxt)
    draw.text((W - 70 - pw_w, H - 90), pwtxt, font=f_pw, fill=(170, 150, 255, 200))

    return bg.convert("RGB")

def save_image(img):
    path = os.path.join(CACHE_DIR, f"sysinfo_{int(time.time() * 1000)}.jpg")
    img.save(path, "JPEG", quality=95)
    return path

def handle_sysinfo_command(message, message_object, thread_id, thread_type, author_id, client):
    parts = (message or "").strip().split()
    
    try:
        user_info = client.fetchUserInfo(author_id)
        user_name = user_info[author_id].name if author_id in user_info else None
    except Exception:
        user_name = None
    
    if len(parts) >= 2 and parts[1].lower() == "text":
        ip = get_ip_local()
        sysn = get_sys_numbers()
        ping = measure_ping_ms()
        mods = count_modules_loaded("modules")
        txt = (
            "📌 SYSINFO\n"
            f"• OS: {platform.system()}\n"
            f"• Python: {platform.python_version()}\n"
            f"• IP: {ip}\n"
            f"• CPU: {sysn['cpu_pct'] if sysn['cpu_pct'] is not None else 'N/A'}%\n"
            f"• RAM: {sysn['ram_pct'] if sysn['ram_pct'] is not None else 'N/A'}%\n"
            f"• Disk: {sysn['disk_pct'] if sysn['disk_pct'] is not None else 'N/A'}%\n"
            f"• Modules: {mods if mods is not None else 'unknown'}\n"
            f"• Ping: {ping if ping is not None else 'unknown'}ms\n"
            f"• Uptime: {get_uptime()}"
        )
        client.replyMessage(Message(text=txt), message_object, thread_id, thread_type, ttl=20000)
        return

    try:
        s = load_settings()
        s["theme"]["w"] = 1536
        s["theme"]["h"] = 768

        img = build_sysinfo_image(s, user_name)
        path = save_image(img)
        
        display_name = user_name if user_name else s.get('owner', 'DucDuydzai cuto')
        client.sendLocalImage(
            path,
            thread_id=thread_id,
            thread_type=thread_type,
            width=img.size[0],
            height=img.size[1],
            message=Message(text=f"📟 System Information • {display_name}"),
            ttl=120000
        )
        try:
            os.remove(path)
        except Exception:
            pass
    except Exception as e:
        client.replyMessage(
            Message(text=f"⚠️ Lỗi tạo sysinfo: {e}"),
            message_object, thread_id, thread_type, ttl=15000
        )

def PTA():
    return {"sysinfo": handle_sysinfo_command}