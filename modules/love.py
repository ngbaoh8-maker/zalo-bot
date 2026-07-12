# love.py - Ghép đôi + chế độ admin (0-2%) + lệnh love admin on/off
import os
import time
import random
import requests
import glob
import json
from io import BytesIO
from zlapi.models import Message, ThreadType
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from config import PREFIX, ADMIN  # ADMIN là list hoặc set các UID admin

# ---------- CONFIG ----------
DEBUG = False
FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
CACHE_DIR = "modules/cache"
TEMP_DIR = os.path.join(CACHE_DIR, "love_temp")
BACKGROUND_DIR = os.path.join(CACHE_DIR, "backgrounds")
DATA_FILE = os.path.join(CACHE_DIR, "love_admin_mode.json")  # lưu trạng thái admin mode

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(BACKGROUND_DIR, exist_ok=True)

FINAL_SIZE = (1280, 720)
AVT1_PATH = os.path.join(CACHE_DIR, "avt_1.png")
AVT2_PATH = os.path.join(CACHE_DIR, "avt_2.png")

# Trạng thái admin mode (mặc định tắt)
ADMIN_MODE = False

# Tự tạo và load trạng thái
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"admin_mode": False}, f, ensure_ascii=False, indent=2)
else:
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            ADMIN_MODE = data.get("admin_mode", False)
    except:
        ADMIN_MODE = False

des = {
    'version': "3.9.0",
    'credits': "ngbao",
    'description': "Ghép đôi + chế độ admin (0-2%)",
    'power': "Thành Viên"
}

# ---------- UTIL ----------
def save_admin_mode(state: bool):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"admin_mode": state}, f, ensure_ascii=False, indent=2)

def get_font(sz):
    try:
        return ImageFont.truetype(FONT_PATH, sz)
    except:
        return ImageFont.load_default()

def is_url(s):
    return isinstance(s, str) and (s.startswith("http://") or s.startswith("https://"))

# ---------- OBJECT -> DICT helpers ----------
def _as_dict(obj):
    if obj is None: return {}
    if isinstance(obj, dict): return obj
    if hasattr(obj, "to_dict") and callable(getattr(obj, "to_dict")):
        try: return obj.to_dict() or {}
        except: pass
    try: return vars(obj)
    except:
        d = {}
        for k in ("id","user_id","uid","display_name","displayName","name","avatar","avatar_url","photo","changed_profiles","members","fullname","full_name","username","nick","text"):
            try:
                v = getattr(obj, k)
                if not callable(v) and v is not None:
                    d[k] = v
            except: pass
        return d

def _extract_name_avatar(item):
    if not item: return (None, None)
    if isinstance(item, dict):
        name = item.get("display_name") or item.get("displayName") or item.get("name") or item.get("full_name") or item.get("username") or item.get("text")
        avatar = item.get("avatar") or item.get("avatar_url") or item.get("photo")
        if is_url(name):
            avatar = name
            name = None
        return (name, avatar)
    d = _as_dict(item)
    name = d.get("display_name") or d.get("displayName") or d.get("name") or d.get("full_name") or d.get("username") or getattr(item, "display_name", None) or getattr(item, "name", None) or getattr(item, "text", None)
    avatar = d.get("avatar") or d.get("avatar_url") or d.get("photo") or getattr(item, "avatar", None)
    if is_url(name):
        avatar = name
        name = None
    return (name, avatar)

def _get_any_id(item):
    d = _as_dict(item)
    for k in ("id","user_id","uid","userId"):
        if k in d and d[k] is not None:
            return str(d[k])
    for a in ("id","user_id","uid"):
        try:
            v = getattr(item, a)
            if v is not None: return str(v)
        except: pass
    return None

# ---------- high-level getters ----------
def get_user_display_name(client, user_id, thread_id=None, thread_type=None):
    try:
        data = client.fetchUserInfo(user_id)
        if data:
            cp = data.get("changed_profiles", {})
            user_data = cp.get(str(user_id), {})
            name, _ = _extract_name_avatar(user_data)
            if name: return name
    except: pass
    return f"Người {user_id}"

def get_user_avatar_url(client, user_id, thread_id=None, thread_type=None):
    try:
        data = client.fetchUserInfo(user_id)
        if data:
            cp = data.get("changed_profiles", {})
            user_data = cp.get(str(user_id), {})
            _, avatar = _extract_name_avatar(user_data)
            if avatar and is_url(avatar): return avatar
    except: pass
    return None

# ---------- download avatar ----------
def download_avatar_slot(url, slot=1, timeout=8):
    if not url or not is_url(url): return None
    target = AVT1_PATH if slot == 1 else AVT2_PATH
    try:
        resp = requests.get(url, timeout=timeout, stream=True)
        resp.raise_for_status()
        with open(target, "wb") as f:
            f.write(resp.content)
        return target
    except:
        return None

# ---------- initial avatar ----------
def create_initial_avatar(name_or_id, out_path, size=400):
    try:
        s = str(name_or_id).strip()
        if is_url(s): text = "U"
        else:
            parts = [p for p in s.replace("_"," ").split() if p]
            text = (parts[0][0] + parts[-1][0]).upper() if len(parts)>1 else parts[0][:2].upper() if parts else "?"
        h = abs(hash(str(name_or_id))) % (256*256*256)
        r = int((h >> 16 & 255) + 255)/2
        g = int((h >> 8  & 255) + 255)/2
        b = int((h       & 255) + 255)/2
        img = Image.new("RGBA", (size, size), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((0,0,size-1,size-1), fill=(int(r),int(g),int(b),255))
        inner = Image.new("RGBA", (size,size), (0,0,0,0))
        ImageDraw.Draw(inner).ellipse((int(size*0.06),int(size*0.06),size-int(size*0.06)-1,size-int(size*0.06)-1), fill=(255,255,255,20))
        img = Image.alpha_composite(img, inner)
        f = get_font(int(size*0.42))
        tb = draw.textbbox((0,0), text, font=f)
        tw, th = tb[2]-tb[0], tb[3]-tb[1]
        draw.text(((size-tw)//2,(size-th)//2), text, font=f, fill=(255,255,255,255))
        img.save(out_path, "PNG")
        return out_path
    except: return None

# ---------- image helpers ----------
def open_round(path, size):
    if not path or not os.path.exists(path): return None
    im = Image.open(path).convert("RGBA").resize((size,size))
    mask = Image.new("L", (size,size), 0)
    ImageDraw.Draw(mask).ellipse((0,0,size-1,size-1), fill=255)
    im.putalpha(mask)
    return im

def pick_background(sz):
    files = []
    for ext in ("*.jpg","*.png","*.jpeg","*.webp"):
        files += glob.glob(os.path.join(BACKGROUND_DIR, ext))
    if files:
        p = random.choice(files)
        try:
            img = Image.open(p).convert("RGBA")
            return ImageOps.fit(img, sz, Image.Resampling.LANCZOS)
        except: pass
    # fallback gradient
    w,h = sz
    img = Image.new("RGBA", sz)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y/(h-1)
        r = int(255*(1-t) + 255*t)
        g = int(240*(1-t) + 202*t)
        b = int(245*(1-t) + 228*t)
        draw.line((0,y,w,y), fill=(r,g,b))
    return img

def draw_vector_heart(size, broken=False):
    img = Image.new("RGBA", (size,size), (0,0,0,0))
    d = ImageDraw.Draw(img)
    cx = size//2; r = int(size*0.28)
    d.ellipse((cx-r//2-r, int(size*0.33)-r, cx-r//2+r, int(size*0.33)+r), fill=(255,20,147,255))
    d.ellipse((cx+r//2-r, int(size*0.33)-r, cx+r//2+r, int(size*0.33)+r), fill=(255,20,147,255))
    d.polygon([(cx-int(r*1.4), int(size*0.48)), (cx+int(r*1.4), int(size*0.48)), (cx, size-int(size*0.12))], fill=(255,20,147,255))
    img = img.filter(ImageFilter.GaussianBlur(0.5))
    if broken:
        cd = ImageDraw.Draw(img)
        pts = [(cx-int(size*0.02),int(size*0.12)), (cx+int(size*0.03),int(size*0.27)),
               (cx-int(size*0.03),int(size*0.42)), (cx+int(size*0.05),int(size*0.56)),
               (cx-int(size*0.05),int(size*0.70)), (cx+int(size*0.02),int(size*0.84))]
        cd.line(pts, fill=(255,255,255,220), width=max(3,int(size*0.05)))
    return img

def phrase_for_percent(p):
    if p < 10: return ("Trời ơi... trái tim tan tành 💔\nMức độ hợp đôi quá thấp.\nCó lẽ không phải duyên phận rồi.\nThôi thì làm bạn bè đi.\nBiết đâu sau này thay đổi.", (200,40,40))
    if p < 20: return ("Rất ít hy vọng — trái tim vỡ nát 💔\nCần nỗ lực nhiều hơn nữa.\nBiết đâu có phép màu xảy ra.\nHãy thử trò chuyện thêm xem sao.\nĐừng vội bỏ cuộc nhé.", (210,60,60))
    if p < 40: return ("Còn chút hi vọng... cố gắng nhé 💬\nHãy tìm hiểu nhau thêm đi.\nCó thể sẽ tốt đẹp hơn đấy.\nChia sẻ sở thích chung đi.\nTừ từ xây dựng tình cảm.", (230,90,120))
    if p < 60: return ("Tạm ổn — tìm hiểu thêm nhé 💭\nĐôi bên có điểm chung.\nXây dựng tình cảm dần dần.\nHẹn gặp mặt thử xem.\nCó tiềm năng phát triển đấy.", (255,140,180))
    if p < 80: return ("Hợp khá — có tiềm năng 💖\nHai bạn khá ăn ý nhau.\nHãy thử hẹn hò xem sao.\nChia sẻ nhiều hơn nữa.\nTương lai sáng sủa lắm.", (255,105,180))
    return ("Siêu hợp luôn! Trâu bò 🥰\nDuyên phận trời định rồi.\nChúc hạnh phúc mãi mãi nhé.\nHai bạn sinh ra dành cho nhau.\nYêu đương thắm thiết đi.", (255,20,147))

# ---------- draw card ----------
def draw_card(name1, a1_path, name2, a2_path, percent, decor_url=None):
    W, H = FINAL_SIZE
    bg = pick_background((W, H))
    canvas = Image.new("RGBA", (W, H))
    canvas.paste(bg, (0, 0))
    draw = ImageDraw.Draw(canvas)

    pw, ph = int(W*0.9), int(H*0.72)
    px, py = (W-pw)//2, (H-ph)//2
    panel = Image.new("RGBA", (pw, ph), (255,255,255,180))
    pd = ImageDraw.Draw(panel)
    pd.rounded_rectangle((0,0,pw,ph), radius=50, fill=(255,255,255,180), outline=(255,105,180,230), width=6)
    canvas.paste(panel, (px, py), panel)

    # avatar
    av_size = int(ph * 0.52)
    left_x  = px + int(pw*0.06)
    right_x = px + pw - int(pw*0.06) - av_size
    av_y    = py + (ph - av_size)//2 + 5

    av1 = open_round(a1_path, av_size) if a1_path else None
    av2 = open_round(a2_path, av_size) if a2_path else None
    if not av1:
        tmp = os.path.join(TEMP_DIR, f"init1_{int(time.time()*1000)}.png")
        create_initial_avatar(name1, tmp, av_size)
        av1 = open_round(tmp, av_size)
    if not av2:
        tmp = os.path.join(TEMP_DIR, f"init2_{int(time.time()*1000)}.png")
        create_initial_avatar(name2, tmp, av_size)
        av2 = open_round(tmp, av_size)

    def paste_shadow(base, img, x, y, sz):
        sh = Image.new("RGBA", (sz+48, sz+48), (0,0,0,0))
        sd = ImageDraw.Draw(sh)
        sd.ellipse((12,12,sz+11,sz+11), fill=(0,0,0,200))
        sh = sh.filter(ImageFilter.GaussianBlur(14))
        base.paste(sh, (x-24, y-10), sh)
        base.paste(img, (x, y), img)

    paste_shadow(canvas, av1, left_x, av_y, av_size)
    paste_shadow(canvas, av2, right_x, av_y, av_size)

    # viền avatar
    ow = max(6, int(av_size*0.07))
    draw.ellipse((left_x-ow, av_y-ow, left_x+av_size+ow, av_y+av_size+ow), outline=(255,182,193,220), width=ow)
    draw.ellipse((right_x-ow, av_y-ow, right_x+av_size+ow, av_y+av_size+ow), outline=(255,182,193,220), width=ow)

    # heart
    heart_s = int(ph * 0.36)
    heart = draw_vector_heart(heart_s, broken=(percent<20))
    hx = px + pw//2 - heart_s//2
    hy = av_y + av_size//2 - heart_s//2
    glow = heart.filter(ImageFilter.GaussianBlur(8))
    canvas.paste(glow, (hx, hy), glow)
    canvas.paste(heart, (hx, hy), heart)

    # tên
    nf = get_font(max(24, int(av_size*0.12)))
    def centered_text(xc, y, text, font):
        w = draw.textbbox((0,0), text, font=font)[2] - draw.textbbox((0,0), text, font=font)[0]
        x = xc - w//2
        for dx in (-2,-1,0,1,2):
            for dy in (-2,-1,0,1,2):
                draw.text((x+dx, y+dy), text, font=font, fill=(0,0,0,150))
        draw.text((x, y), text, font=font, fill=(255,255,255,255))
    centered_text(left_x + av_size//2, av_y + av_size + 14, name1, nf)
    centered_text(right_x + av_size//2, av_y + av_size + 14, name2, nf)

    # thanh %
    bw, bh = int(pw*0.28), 18
    bx = px + pw//2 - bw//2; by = py + ph - int(ph*0.16)
    draw.rounded_rectangle((bx-2,by-2,bx+bw+2,by+bh+2), radius=12, fill=(0,0,0,40))
    draw.rounded_rectangle((bx,by,bx+bw,by+bh), radius=12, fill=(255,255,255,120))
    fill_w = int(bw * percent / 100)
    fill_c = (255,20,147,220) if percent >= 20 else (210,40,40,220)
    draw.rounded_rectangle((bx,by,bx+fill_w,by+bh), radius=12, fill=fill_c)

    pfont = get_font(22)
    ptxt = f"{percent}%"
    tw = draw.textbbox((0,0), ptxt, font=pfont)[2] - draw.textbbox((0,0), ptxt, font=pfont)[0]
    for dx in (-2,-1,0,1,2):
        for dy in (-2,-1,0,1,2):
            draw.text((bx + (bw-tw)//2 + dx, by - 28 + dy), ptxt, font=pfont, fill=(0,0,0,160))
    draw.text((bx + (bw-tw)//2, by - 28), ptxt, font=pfont, fill=(255,255,255,255))

    # câu nói
    phrase, color = phrase_for_percent(percent)
    pf = get_font(24)
    lines = phrase.split('\n')
    for i, line in enumerate(lines):
        wid = draw.textbbox((0,0), line, font=pf)[2] - draw.textbbox((0,0), line, font=pf)[0]
        x = px + (pw - wid)//2
        y = by + bh + 8 + i * 28
        for dx in (-2,-1,0,1,2):
            for dy in (-2,-1,0,1,2):
                draw.text((x+dx, y+dy), line, font=pf, fill=(0,0,0,150))
        draw.text((x, y), line, font=pf, fill=(*color, 255))

    out_path = os.path.join(TEMP_DIR, f"love_{int(time.time()*1000)}.png")
    canvas.convert("RGB").save(out_path, "PNG", quality=95)
    return out_path

# ---------- handler ----------
def handle_love_command(message, message_object, thread_id, thread_type, author_id, client):
    global ADMIN_MODE
    try:
        text = str(message).strip().lower()
        parts = text.split()

        # lệnh bật/tắt admin mode
        if len(parts) >= 3 and parts[1] == "admin":
            if str(author_id) not in ADMIN:
                client.sendMessage(Message(text="⚠️ Chỉ ADMIN mới được dùng lệnh này!"), thread_id, thread_type)
                return
            if parts[2] in ("on", "bật"):
                ADMIN_MODE = True
                save_admin_mode(True)
                client.sendMessage(Message(text="✅ Đã BẬT chế độ ADMIN (love chỉ ra 0-2%)"), thread_id, thread_type)
            elif parts[2] in ("off", "tắt"):
                ADMIN_MODE = False
                save_admin_mode(False)
                client.sendMessage(Message(text="✅ Đã TẮT chế độ ADMIN (love ra bình thường)"), thread_id, thread_type)
            return

        # ghép đôi bình thường
        if thread_type == ThreadType.USER:
            client.sendMessage(Message(text="Lệnh chỉ dùng trong nhóm!"), thread_id, thread_type)
            return

        mentions = getattr(message_object, "mentions", None)
        if not mentions or len(mentions) < 2:
            client.sendMessage(Message(text="Tag đủ 2 người để ghép đôi nha!"), thread_id, thread_type)
            return

        # lấy info 2 người
        m1, m2 = mentions[0], mentions[1]
        uid1 = str(_get_any_id(m1))
        uid2 = str(_get_any_id(m2))

        name1 = _extract_name_avatar(m1)[0] or get_user_display_name(client, uid1, thread_id, thread_type)
        name2 = _extract_name_avatar(m2)[0] or get_user_display_name(client, uid2, thread_id, thread_type)

        av1_url = _extract_name_avatar(m1)[1] or get_user_avatar_url(client, uid1, thread_id, thread_type)
        av2_url = _extract_name_avatar(m2)[1] or get_user_avatar_url(client, uid2, thread_id, thread_type)

        a1_path = download_avatar_slot(av1_url, slot=1) if av1_url else None
        a2_path = download_avatar_slot(av2_url, slot=2) if av2_url else None

        # Xác định % love
        is_admin_pair = uid1 in ADMIN or uid2 in ADMIN
        if ADMIN_MODE or is_admin_pair:
            percent = random.randint(0, 2)   # admin mode: 0-2%
        else:
            percent = random.randint(0, 100)

        img_path = draw_card(name1, a1_path, name2, a2_path, percent)

        # Gửi ảnh với kích thước đầy đủ để tránh cắt
        try:
            client.sendLocalImage(imagePath=img_path, thread_id=thread_id, thread_type=thread_type, width=FINAL_SIZE[0], height=FINAL_SIZE[1])
        except:
            client.sendLocalImage(img_path, thread_id, thread_type)

        caption = (f"{'🌟' if ADMIN_MODE else '💘'} **CẶP ĐÔI HÔM NAY** {'🌟' if ADMIN_MODE else '💘'}\n"
                   f"❤️ {name1} 💞 {name2}\n"
                   f"💟 Mức độ hợp đôi: {percent}%\n"
                   f"🌹 Chúc hai bạn trăm năm hạnh phúc 🌹")
        client.sendMessage(Message(text=caption), thread_id, thread_type)

        # dọn dẹp
        try: os.remove(img_path)
        except: pass

    except Exception as e:
        client.sendMessage(Message(text=f"Lỗi love: {e}"), thread_id, thread_type)

def PTA():
    return {'love': handle_love_command}