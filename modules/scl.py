import os
import logging
import requests
from bs4 import BeautifulSoup
import re
import time
import tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO
from config import PREFIX
from zlapi.models import Message, ThreadType
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
EMOJI_FONT_PATH = "modules/cache/font/NotoEmoji-Bold.ttf"

des = {
    'version': "3.1.0",
    'credits': "ngbao",
    'description': "Tải nhạc SoundCloud (no ffmpeg)",
    'power': "Thành viên"
}

SEARCH_TIMEOUT = 120
os.makedirs(os.path.join(os.path.dirname(__file__), 'cache'), exist_ok=True)

client_id_cache = None

# ================= USER NAME =================
def get_user_name(client, uid):
    try:
        user_info = client.fetchUserInfo(uid)
        author_info = user_info.changed_profiles.get(str(uid), {}) if user_info and user_info.changed_profiles else {}
        return author_info.get('zaloName', 'Không xác định')
    except:
        return 'Không xác định'

# ================= HEADERS =================
def get_headers():
    return {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://soundcloud.com/"
    }

# ================= FONT =================
def get_font(size):
    try: return ImageFont.truetype(FONT_PATH, size)
    except: return ImageFont.load_default()

def get_emoji_font(size):
    try: return ImageFont.truetype(EMOJI_FONT_PATH, size)
    except: return ImageFont.load_default()

# ================= DELETE FILE =================
def delete_file(file_path):
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except:
        pass

# ================= AUTOSAVE =================
def autosave(img, quality=92):
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tf:
        img.convert("RGB").save(tf.name, "JPEG", quality=quality)
        return tf.name

# ================= TMPFILES UPLOAD =================
def upload_to_temp_service(file_path):
    import random, string
    
    # 1. Pixeldrain (Nhanh nhất)
    try:
        with open(file_path, 'rb') as f:
            response = requests.post("https://pixeldrain.com/api/file", files={"file": f}, timeout=15)
            if response.status_code in [200, 201]:
                return f"https://pixeldrain.com/api/file/{response.json()['id']}"
    except: pass

    # 2. Uguu.se (Rất nhanh)
    try:
        with open(file_path, 'rb') as f:
            files = {'files[]': (os.path.basename(file_path), f)}
            response = requests.post('https://uguu.se/upload.php', files=files, timeout=15)
            data = response.json()
            if data.get('success'):
                return data['files'][0]['url']
    except: pass

    # 3. Filebin (Dự phòng ổn định)
    try:
        bin_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))
        with open(file_path, 'rb') as f:
            response = requests.post(f"https://filebin.net/{bin_id}/{os.path.basename(file_path)}", data=f, timeout=20)
            if response.status_code == 201:
                return f"https://filebin.net/{bin_id}/{os.path.basename(file_path)}"
    except: pass

    # 4. Tmpfiles (Fallback chậm)
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f)}
            response = requests.post('https://tmpfiles.org/api/v1/upload', files=files, timeout=60)
            data = response.json()
            if data.get('status') == 'success':
                return data['data']['url'].replace('tmpfiles.org/', 'tmpfiles.org/dl/')
    except: pass

    raise Exception("Tất cả server upload đều thất bại")

# ================= CLIENT ID =================
def get_client_id():
    global client_id_cache
    if client_id_cache: return client_id_cache
    try:
        res = requests.get('https://soundcloud.com/', headers=get_headers(), timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        for s in soup.find_all('script', {'crossorigin': True}):
            src = s.get('src')
            if src and src.startswith('https'):
                js = requests.get(src, headers=get_headers(), timeout=10).text
                m = re.search(r'client_id\s*:\s*"([^"]+)"', js)
                if m:
                    client_id_cache = m.group(1)
                    return client_id_cache
    except:
        pass
    return None

def wait_for_client_id():
    cid = get_client_id()
    retry = 5
    while not cid and retry > 0:
        time.sleep(2)
        cid = get_client_id()
        retry -= 1
    if not cid:
        raise Exception("Không lấy được client_id")
    return cid

# ================= TIME =================
def ms_to_mmss(ms):
    try:
        s = ms // 1000
        return f"{s//60:02}:{s%60:02}"
    except:
        return "??:??"

# ================= SONG DETAIL =================
def get_song_details(link):
    try:
        cid = wait_for_client_id()
        api = f"https://api-v2.soundcloud.com/resolve?url={link}&client_id={cid}"
        r = requests.get(api, headers=get_headers(), timeout=10).json()
        return {
            "duration": ms_to_mmss(r.get("duration", 0)),
            "duration_ms": r.get("duration", 0),
            "playback_count": r.get("playback_count", 0),
            "likes_count": r.get("likes_count", 0),
            "comment_count": r.get("comment_count", 0),
            "artist": r.get("user", {}).get("username", "Unknown Artist")
        }
    except:
        return {
            "duration": "??:??",
            "duration_ms": 0,
            "playback_count": 0,
            "likes_count": 0,
            "comment_count": 0,
            "artist": "Unknown Artist"
        }

# ================= SEARCH =================
def search_songs(query):
    songs = []
    url = f"https://m.soundcloud.com/search?q={requests.utils.quote(query)}"
    r = requests.get(url, headers=get_headers(), timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    for a in soup.select("a"):
        href = a.get("href", "")
        if re.match(r"^/[^/]+/[^/]+$", href):
            title = a.get("aria-label", "").strip()
            if not title:
                continue
            link = "https://soundcloud.com" + href
            detail = get_song_details(link)
            cover = get_track_cover(link)
            songs.append((link, title, cover,
                          detail["duration"],
                          detail["playback_count"],
                          detail["likes_count"],
                          detail["comment_count"],
                          detail["artist"]))
        if len(songs) >= 15:
            break
    return songs

# ================= STREAM =================
def get_music_stream_url(link):
    try:
        cid = wait_for_client_id()
        api = f"https://api-v2.soundcloud.com/resolve?url={link}&client_id={cid}"
        data = requests.get(api, headers=get_headers(), timeout=10).json()
        for t in data.get("media", {}).get("transcodings", []):
            if t.get("format", {}).get("protocol") == "progressive":
                s = requests.get(
                    f"{t['url']}?client_id={cid}&track_authorization={data.get('track_authorization')}",
                    headers=get_headers(), timeout=10
                ).json()
                return s.get("url")
    except:
        pass
    return None

# ================= COVER =================
def get_track_cover(link):
    try:
        cid = wait_for_client_id()
        api = f"https://api-v2.soundcloud.com/resolve?url={link}&client_id={cid}"
        r = requests.get(api, headers=get_headers(), timeout=10).json()
        cover = r.get("artwork_url") or r.get("user", {}).get("avatar_url")
        return cover.replace("-large", "-t500x500") if cover else None
    except:
        return None

# ================= DOWNLOAD =================
def download_audio(url, title):
    safe = re.sub(r'[\\/*?:"<>|]', "", title)[:50]
    path = os.path.join(os.path.dirname(__file__), "cache", safe + ".aac")
    r = requests.get(url, headers=get_headers(), stream=True, timeout=120)
    with open(path, "wb") as f:
        for c in r.iter_content(65536):
            if c: f.write(c)
    return path

# ================= HELPERS =================
def _crop_square(img_pil):
    w, h = img_pil.size
    s = min(w, h)
    left = (w - s) // 2
    top = (h - s) // 2
    return img_pil.crop((left, top, left + s, top + s))

def _load_cover(url, size):
    try:
        data = requests.get(url, headers=get_headers(), timeout=3).content
        ci = Image.open(BytesIO(data)).convert("RGBA")
        return _crop_square(ci).resize((size, size), Image.LANCZOS)
    except:
        return None

def _round_cover(img_pil, radius=10):
    w, h = img_pil.size
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w, h], radius=radius, fill=255)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(img_pil, mask=mask)
    return out

def _truncate(text, font, max_w):
    if font.getlength(text) <= max_w:
        return text
    while len(text) > 3 and font.getlength(text + "..") > max_w:
        text = text[:-1]
    return text + ".."

# ================= DRAW SONG LIST =================
def draw_song_list_image(songs):
    WIDTH, HEIGHT = 1280, 640
    img = Image.new("RGBA", (WIDTH, HEIGHT), (10, 10, 15, 255))

    # Blurred background
    if songs and songs[0][2]:
        bg = _load_cover(songs[0][2], max(WIDTH, HEIGHT))
        if bg:
            bg = bg.resize((WIDTH, HEIGHT), Image.LANCZOS).filter(ImageFilter.GaussianBlur(40))
            dark_overlay = Image.new("RGBA", (WIDTH, HEIGHT), (10, 10, 15, 180))
            bg = Image.alpha_composite(bg, dark_overlay)
            img.paste(bg, (0, 0))

    draw = ImageDraw.Draw(img)

    f_feat_title = get_font(32)
    f_feat_artist = get_font(18)
    f_top = get_font(38)
    f_01 = get_font(56)
    
    f_rt = get_font(18)
    f_ra = get_font(13)
    f_rn = get_font(32)
    f_wm = get_font(120)

    # Watermark
    if songs:
        try:
            wm = songs[0][1]
            ww = f_wm.getlength(wm)
            draw.text((WIDTH//2 - ww//2, HEIGHT//2 - 60), wm, font=f_wm, fill=(255, 255, 255, 25))
        except:
            pass

    PAD_X, PAD_Y = 40, 40
    WRAP_W = WIDTH - PAD_X*2
    WRAP_H = HEIGHT - PAD_Y*2

    # Main wrappers
    draw.rounded_rectangle([PAD_X, PAD_Y, PAD_X+WRAP_W, PAD_Y+WRAP_H], radius=45, outline=(255,255,255,40), width=2, fill=(30, 30, 40, 120))
    draw.rounded_rectangle([PAD_X+10, PAD_Y+10, PAD_X+WRAP_W-10, PAD_Y+WRAP_H-10], radius=35, outline=(255,255,255,20), width=1, fill=(20, 20, 30, 160))

    # === LEFT PANEL ===
    L_W = 360
    L_X = PAD_X + 25
    L_Y = PAD_Y + 25
    L_H = WRAP_H - 50
    draw.rounded_rectangle([L_X, L_Y, L_X+L_W, L_Y+L_H], radius=30, outline=(255,255,255,30), width=1, fill=(15, 15, 20, 200))

    feat = songs[0]
    cover_sz = L_W - 50
    cx = L_X + 25
    cy = L_Y + 25

    if feat[2]:
        ci = _load_cover(feat[2], cover_sz)
        if ci:
            ci = _round_cover(ci, radius=24)
            img.paste(ci, (cx, cy), ci)

    ty = cy + cover_sz + 25
    draw.text((cx, ty), _truncate(feat[1], f_feat_title, L_W-50), font=f_feat_title, fill=(255,255,255,255))
    draw.text((cx, ty+45), _truncate(feat[7], f_feat_artist, L_W-50), font=f_feat_artist, fill=(180,180,190,255))

    # TOP 01 badge
    badge_y = L_Y + L_H - 75
    draw.text((cx, badge_y+10), "TOP", font=f_top, fill=(255,255,255,0), stroke_width=1, stroke_fill=(180,180,190,255))
    top_w = f_top.getlength("TOP") + 15
    draw.text((cx+top_w, badge_y), "01", font=f_01, fill=(255,255,255,0), stroke_width=2, stroke_fill=(255,255,255,255))

    # === RIGHT PANEL ===
    R_X = L_X + L_W + 25
    R_W = WRAP_W - L_W - 75
    
    remaining = songs[1:15]
    mid = 7
    col1 = remaining[:mid]
    col2 = remaining[mid:]
    
    COL_W = (R_W - 20) // 2
    row_h = 62
    gap = 10
    
    for ci_idx, col_list in enumerate([col1, col2]):
        col_x = R_X + ci_idx * (COL_W + 20)
        for ri, sdata in enumerate(col_list):
            _, s_title, s_cover, _, _, _, _, s_artist = sdata
            idx = 2 + ci_idx*mid + ri
            y = L_Y + ri * (row_h + gap)
            
            # Row pill
            draw.rounded_rectangle([col_x, y, col_x + COL_W, y + row_h], radius=row_h//2, outline=(255,255,255,50), width=1, fill=(45, 45, 60, 120))

            # Small cover
            th_sz = row_h - 14
            if s_cover:
                th = _load_cover(s_cover, th_sz)
                if th:
                    th = _round_cover(th, radius=12)
                    img.paste(th, (col_x + 7, y + 7), th)

            tx = col_x + th_sz + 22
            draw.text((tx, y + 12), _truncate(s_title, f_rt, COL_W - th_sz - 80), font=f_rt, fill=(255,255,255,255))
            draw.text((tx, y + 36), _truncate(s_artist, f_ra, COL_W - th_sz - 80), font=f_ra, fill=(180,180,190,255))

            # Number (Hollow)
            ns = f"{idx:02d}"
            nw = f_rn.getlength(ns)
            draw.text((col_x + COL_W - nw - 20, y + 14), ns, font=f_rn, fill=(255,255,255,0), stroke_width=1, stroke_fill=(200,200,210,255))

    return autosave(img)

# ================= DRAW DETAIL =================
def format_number(num):
    try:
        n = int(num)
        if n >= 1000000: return f"{n/1000000:.1f}M"
        if n >= 1000: return f"{n/1000:.1f}K"
        return str(n)
    except:
        return str(num)

def draw_song_detail_image(title, artist, duration, playback_count, like_count, comment_count, cover):
    WIDTH, HEIGHT = 1200, 440
    img = Image.new("RGBA", (WIDTH, HEIGHT), (255, 255, 255, 0))
    
    # 1. Background blurred from cover
    if cover:
        bg = _load_cover(cover, max(WIDTH, HEIGHT))
        if bg:
            bg = bg.resize((WIDTH, HEIGHT), Image.LANCZOS).filter(ImageFilter.GaussianBlur(80))
            dark_overlay = Image.new("RGBA", (WIDTH, HEIGHT), (10, 10, 12, 180))
            bg = Image.alpha_composite(bg, dark_overlay)
            img.paste(bg, (0, 0))

    draw = ImageDraw.Draw(img)

    # 2. Main Dark Capsule
    PAD_X, PAD_Y = 50, 40
    CW = WIDTH - PAD_X*2
    CH = HEIGHT - PAD_Y*2
    
    # Capsule surface
    draw.rounded_rectangle([PAD_X, PAD_Y, PAD_X+CW, PAD_Y+CH], radius=CH//2, fill=(35, 35, 42, 255))
    
    # Left shadow for cover depth
    draw.rounded_rectangle([PAD_X, PAD_Y, PAD_X+CH, PAD_Y+CH], radius=CH//2, fill=(0,0,0,30))

    # 3. Circular Cover Image
    cover_sz = CH - 40 # 20px padding
    cx = PAD_X + 20
    cy = PAD_Y + 20
    if cover:
        cimg = _load_cover(cover, cover_sz)
        if cimg:
            cimg = _round_cover(cimg, radius=cover_sz//2)
            img.paste(cimg, (cx, cy), cimg)

    # 4. Title and Artist
    tx = cx + cover_sz + 40
    f_title = get_font(52)
    f_artist = get_font(28)
    
    # Title
    draw.text((tx, cy + 5), _truncate(title, f_title, CW - cover_sz - 80), font=f_title, fill=(255,255,255,255))
    
    # Artist
    draw.text((tx, cy + 70), artist, font=f_artist, fill=(180,180,190,255))
    
    # Verified badge
    art_w = f_artist.getlength(artist)
    vx = tx + art_w + 12
    vy = cy + 76
    draw.ellipse([vx, vy, vx+20, vy+20], fill=(29, 155, 240, 255))
    draw.line([(vx+5, vy+10), (vx+9, vy+14), (vx+15, vy+6)], fill=(255,255,255,255), width=2)

    # 5. Pills
    py = cy + 125
    ph = 30
    def draw_pill(px, text, icon, icon_color, is_emoji=False):
        f_pill = get_font(15)
        tw = f_pill.getlength(text)
        pw = tw + 45 if icon else tw + 30
        draw.rounded_rectangle([px, py, px+pw, py+ph], radius=15, fill=(55, 55, 62, 255), outline=(70, 70, 80, 255), width=1)
        if icon:
            if is_emoji:
                draw.text((px+12, py+1), icon, font=get_emoji_font(18), fill=icon_color)
            else:
                # Custom icon (e.g. lossless bars)
                draw.line([(px+12, py+10), (px+12, py+20)], fill=icon_color, width=2)
                draw.line([(px+16, py+12), (px+16, py+18)], fill=icon_color, width=2)
                draw.line([(px+20, py+8), (px+20, py+22)], fill=icon_color, width=2)
                draw.line([(px+24, py+14), (px+24, py+16)], fill=icon_color, width=2)
            draw.text((px+36, py+5), text, font=f_pill, fill=(220,220,230,255))
        else:
            draw.text((px+15, py+5), text, font=f_pill, fill=(220,220,230,255))
        return px + pw + 15

    px = tx
    px = draw_pill(px, "Liked", "❤", (255,60,60,255), True)
    px = draw_pill(px, "Lossless", "bars", (180,180,190,255), False)
    px = draw_pill(px, "Dolby Atmos", None, None, False)

    # 6. Audio Waveform
    wy = cy + 190
    ww = CW - cover_sz - 80
    import math, random
    wave_color = (120, 120, 130, 255)
    for i in range(0, int(ww), 6):
        h = 6 + 25 * math.sin(i * 0.1) + random.randint(0, 10)
        h = max(4, min(40, h))
        draw.rounded_rectangle([tx + i, wy - h/2, tx + i + 2, wy + h/2], radius=1, fill=wave_color)

    # 7. Timeline
    tly = cy + 240
    tlw = CW - cover_sz - 80
    draw.line([(tx, tly), (tx+tlw, tly)], fill=(80, 80, 90, 255), width=4)
    prog = int(tlw * 0.35)
    draw.line([(tx, tly), (tx+prog, tly)], fill=(255, 255, 255, 255), width=4)
    draw.ellipse([tx+prog-6, tly-6, tx+prog+6, tly+6], fill=(255, 255, 255, 255))
    
    # 8. Bottom Controls
    cy_ctrl = cy + 295
    cx_ctrl = tx + 160

    def draw_circle_btn(bcx, r, is_solid=False):
        if is_solid:
            draw.ellipse([bcx-r, cy_ctrl-r, bcx+r, cy_ctrl+r], fill=(60,60,68,255), outline=(80,80,90,255), width=1)
        else:
            draw.ellipse([bcx-r, cy_ctrl-r, bcx+r, cy_ctrl+r], outline=(80,80,90,255), width=1)

    # Shuffle
    draw_circle_btn(cx_ctrl - 120, 16)
    sx = cx_ctrl - 120
    draw.line([(sx-5, cy_ctrl-3), (sx+5, cy_ctrl+3)], fill=(180,180,190,255), width=2)
    draw.line([(sx-5, cy_ctrl+3), (sx+5, cy_ctrl-3)], fill=(180,180,190,255), width=2)

    # Prev
    draw_circle_btn(cx_ctrl - 60, 20)
    px = cx_ctrl - 60
    draw.polygon([(px+3, cy_ctrl-5), (px+3, cy_ctrl+5), (px-3, cy_ctrl)], fill=(255,255,255,255))
    draw.polygon([(px-3, cy_ctrl-5), (px-3, cy_ctrl+5), (px-9, cy_ctrl)], fill=(255,255,255,255))

    # Play (Solid center)
    draw_circle_btn(cx_ctrl, 28, is_solid=True)
    draw.polygon([(cx_ctrl-5, cy_ctrl-10), (cx_ctrl-5, cy_ctrl+10), (cx_ctrl+10, cy_ctrl)], fill=(255,255,255,255))

    # Next
    draw_circle_btn(cx_ctrl + 60, 20)
    nx = cx_ctrl + 60
    draw.polygon([(nx-3, cy_ctrl-5), (nx-3, cy_ctrl+5), (nx+3, cy_ctrl)], fill=(255,255,255,255))
    draw.polygon([(nx+3, cy_ctrl-5), (nx+3, cy_ctrl+5), (nx+9, cy_ctrl)], fill=(255,255,255,255))

    # Repeat
    draw_circle_btn(cx_ctrl + 120, 16)
    rx = cx_ctrl + 120
    draw.arc([rx-5, cy_ctrl-5, rx+5, cy_ctrl+5], 0, 270, fill=(180,180,190,255), width=2)

    # SOUNDCLOUD pill
    sc_w = 150
    sc_h = 32
    sc_x = WIDTH - PAD_X - sc_w - 30
    sc_y = cy_ctrl - sc_h//2
    draw.rounded_rectangle([sc_x, sc_y, sc_x+sc_w, sc_y+sc_h], radius=16, fill=(55,55,62,255), outline=(70,70,80,255), width=1)
    # Cloud icon
    draw.ellipse([sc_x+10, sc_y+8, sc_x+28, sc_y+26], fill=(255,85,0,255))
    f_sc = get_font(12)
    draw.text((sc_x+40, sc_y+9), "SOUNDCLOUD", font=f_sc, fill=(255,255,255,255))

    return autosave(img)

# ================= RECALL =================
def _recall_list_image(client, state):
    """Thu hồi ảnh danh sách nhạc."""
    try:
        msg_id = state.get('list_msg_id')
        cli_msg_id = state.get('list_cli_msg_id', 0)
        tid = state.get('list_thread_id')
        ttype = state.get('list_thread_type')
        if msg_id and tid:
            client.undoMessage(msg_id, cli_msg_id, tid, ttype)
            print(f"[SCL] ✅ Thu hồi ảnh thành công! msgId={msg_id}")
        else:
            print(f"[SCL] ⚠️ Không có msgId để thu hồi (msg_id={msg_id})")
    except Exception as e:
        print(f"[SCL] ⚠️ Lỗi thu hồi: {e}")

def _extract_msg_id(res):
    if not res: return None
    try:
        if isinstance(res, dict):
            if 'msgId' in res: return res['msgId']
            if 'data' in res and isinstance(res['data'], dict) and 'msgId' in res['data']:
                return res['data']['msgId']
            if 'send_message_response' in res and isinstance(res['send_message_response'], dict):
                return res['send_message_response'].get('msgId')
        else:
            return getattr(res, 'msgId', None)
    except:
        pass
    return None

def _undo_msg_safe(client, msg_res, tid, ttype):
    m_id = _extract_msg_id(msg_res)
    if m_id:
        try:
            client.undoMessage(m_id, 0, tid, ttype)
        except:
            pass

# ================= HANDLER =================
def handle_scl_command(message_text, message_object, thread_id, thread_type, author_id, client):
    if not hasattr(client, 'scl_user_states'):
        client.scl_user_states = {}
    name = get_user_name(client, author_id)
    parts = message_text.strip().split()
    query_or_choice = " ".join(parts[1:]) if len(parts) > 1 else ""

    if query_or_choice.isdigit() and author_id in client.scl_user_states:
        state = client.scl_user_states[author_id]

        if time.time() - state['time_of_search'] > SEARCH_TIMEOUT:
            _recall_list_image(client, state)
            del client.scl_user_states[author_id]
            client.replyMessage(Message(text=f"➜ {name}, kết quả đã hết hạn."), message_object, thread_id, thread_type)
            return

        index = int(query_or_choice) - 1
        songs = state['songs']

        if not (0 <= index < len(songs)):
            client.replyMessage(Message(text=f"➜ {name}, lựa chọn không hợp lệ."), message_object, thread_id, thread_type)
            return

        # Thu hồi ảnh danh sách
        _recall_list_image(client, state)
        del client.scl_user_states[author_id]

        link, title, _, _, _, _, _, artist = songs[index]
        detail = get_song_details(link)

        load_msg = client.replyMessage(
            Message(text=f"➜ Đang tải '{title}', vui lòng chờ..."),
            message_object, thread_id, thread_type
        )

        stream_url = get_music_stream_url(link)
        file_path = download_audio(stream_url, title)
        
        _undo_msg_safe(client, load_msg, thread_id, thread_type)

        sent_local = False
        try:
            if hasattr(client, '_uploadAttachment'):
                res = client._uploadAttachment(file_path, thread_id, thread_type)
                if res and "fileUrl" in res:
                    client.sendRemoteVoice(
                        res["fileUrl"],
                        thread_id=thread_id,
                        thread_type=thread_type,
                        fileSize=os.path.getsize(file_path),
                        ttl=1800000
                    )
                    sent_local = True
            elif hasattr(client, 'sendLocalVoice'):
                client.sendLocalVoice(file_path, thread_id, thread_type)
                sent_local = True
            elif hasattr(client, 'sendLocalAudio'):
                client.sendLocalAudio(file_path, thread_id, thread_type)
                sent_local = True
        except Exception as e:
            logging.error(f"Zlapi Uphost failed: {e}")

        if not sent_local:
            voice_url = upload_to_temp_service(file_path)
            client.sendRemoteVoice(
                voice_url,
                thread_id=thread_id,
                thread_type=thread_type,
                fileSize=os.path.getsize(file_path),
                ttl=1800000
            )

        cover = get_track_cover(link)
        img_path = draw_song_detail_image(
            title, artist, detail['duration'],
            detail['playback_count'], detail['likes_count'], detail['comment_count'],
            cover
        )

        with Image.open(img_path) as im:
            w, h = im.size

        client.sendLocalImage(
            img_path,
            thread_id=thread_id,
            thread_type=thread_type,
            width=w,
            height=h,
            message=Message(text=f"> From SoundCloud <\n{title} - {artist}")
        )

        delete_file(file_path)
        delete_file(img_path)
        return

    if not query_or_choice:
        client.replyMessage(
            Message(text=f"➜ {name}, dùng: {PREFIX}scl <tên bài>"),
            message_object, thread_id, thread_type
        )
        return

    search_msg = client.replyMessage(
        Message(text=f"➜ Đang tìm '{query_or_choice}'..."),
        message_object, thread_id, thread_type
    )

    songs = search_songs(query_or_choice)
    _undo_msg_safe(client, search_msg, thread_id, thread_type)
    
    if not songs:
        client.replyMessage(
            Message(text=f"➜ {name}, không tìm thấy kết quả."),
            message_object, thread_id, thread_type
        )
        return

    img_path = draw_song_list_image(songs)
    with Image.open(img_path) as im:
        w, h = im.size

    # 1. Khởi tạo state TRƯỚC KHI gửi ảnh để tránh lỗi bị ghi đè bởi main.py bắt echo muộn
    client.scl_user_states[author_id] = {
        "songs": songs,
        "time_of_search": time.time(),
        "list_msg_id": None,
        "list_cli_msg_id": 0,
        "list_thread_id": thread_id,
        "list_thread_type": thread_type
    }

    list_msg_res = client.sendLocalImage(
        img_path,
        thread_id=thread_id,
        thread_type=thread_type,
        width=w,
        height=h,
        message=Message(text=f"➜ {name}, reply số để tải.")
    )

    # 2. Bắt luôn msgId từ response để đảm bảo chắc chắn có thể thu hồi
    m_id = _extract_msg_id(list_msg_res)
    if m_id:
        client.scl_user_states[author_id]["list_msg_id"] = m_id

    delete_file(img_path)

# ================= EXPORT =================
def PTA():
    return {'scl': handle_scl_command}