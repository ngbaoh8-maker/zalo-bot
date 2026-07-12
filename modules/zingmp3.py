import os
import logging
import requests
import hashlib
import hmac
import time
import re
import tempfile
import subprocess
from io import BytesIO
import json
from PIL import Image, ImageDraw, ImageFont 

from zlapi.models import Message, ThreadType 

des = {
    'version': "2.0.0",
    'credits': "ngbao",
    'description': "Tải xuống nhạc từ Zing MP3",
    'power': "Quản trị viên Bot"
}


URL = "https://zingmp3.vn"
API_KEY = "X5BM3w8N7MKozC0B85o4KMlzLZKhV00y"
SECRET_KEY = "acOrvUS15XRW2o9JksiK1KgQ6Vbds8ZW"
VERSION = "1.11.13"

FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf" # RE-ADDED
EMOJI_FONT_PATH = "modules/cache/font/NotoEmoji-Bold.ttf" # RE-ADDED
HASH_KEYS = ["ctime", "id", "type", "page", "count", "version"] 

SEARCH_TIMEOUT = 120
AUDIO_QUALITY_PRESET = '128kbps_Fast' 
CACHE_DIR_ZMP3 = os.path.join(os.path.dirname(__file__), 'cache_zingmp3')
os.makedirs(CACHE_DIR_ZMP3, exist_ok=True)

des = {
    'version': "1.0.9 (Vẽ Ảnh + Tốc Độ Cao)", 
    'credits': "Người dịch & Gemini",
    'description': "Tải nhạc Zing MP3, xem lời bài hát và vẽ ảnh danh sách/thông tin (Tối ưu tốc độ).",
    'power': "Thành viên"
}

def get_user_name(client, uid):
    try:
        user_info = client.fetchUserInfo(uid)
        author_info = user_info.changed_profiles.get(str(uid), {}) if user_info and user_info.changed_profiles else {}
        return author_info.get('zaloName', 'Không xác định')
    except Exception:
        return 'Không xác định'

def delete_file(file_path):
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logging.info(f"[delete_file] Đã xóa file tạm: {file_path}")
    except Exception as e:
        logging.error(f"[delete_file] Lỗi khi xóa file {file_path}: {e}")

def get_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9", "Referer": 'https://zingmp3.vn/', "Upgrade-Insecure-Requests": "1"
    }

def get_font(size):
    try: return ImageFont.truetype(FONT_PATH, size)
    except: return ImageFont.load_default()

def get_emoji_font(size):
    try: return ImageFont.truetype(EMOJI_FONT_PATH, size)
    except: return ImageFont.load_default()

def autosave(img, quality=92):
    """Lưu ảnh và trả về đường dẫn tạm thời."""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tf:
        img.convert("RGB").save(tf.name, "JPEG", quality=quality, dpi=(100, 100), optimize=True, progressive=True, subsampling=0)
        return tf.name

def upload_to_temp_service(file_path):
    try:
        logging.info(f"Đang tải {os.path.basename(file_path)} lên dịch vụ lưu trữ tạm thời...")
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f)}
            response = requests.post('https://tmpfiles.org/api/v1/upload', files=files, timeout=60) 
            response.raise_for_status()

        data = response.json()
        if data.get('status') == 'success':
            url = data['data']['url'].replace('tmpfiles.org/', 'tmpfiles.org/dl/')
            logging.info(f"Tải lên dịch vụ tạm thời thành công. URL: {url}")
            return url
        else:
            error_msg = data.get('error', {}).get('message', 'Lỗi không xác định từ tmpfiles.org')
            raise Exception(f"Tải file lên server tạm thời thất bại: {error_msg}")
    except requests.exceptions.Timeout:
        logging.error("[upload_to_temp_service] Request timed out.")
        raise Exception("Không thể tải file lên server tạm thời: Quá thời gian chờ (60s).")
    except Exception as e:
        logging.error(f"[upload_to_temp_service] Error: {e}")
        raise Exception(f"Không thể tải file lên server tạm thời: {e}")

def process_audio(audio_url, title):
    """Tải file raw (128kbps) và upload lên dịch vụ tạm thời, bỏ qua FFmpeg."""
    raw_file_path = None
    try:
        safe_title = re.sub(r'[\\/*?:"<>|]', "", title)[:50]
        temp_id = int(time.time() * 1000)

        logging.info(f"[process_audio] Bắt đầu tải file raw từ Zing MP3...")
        response = requests.get(audio_url, headers=get_headers(), stream=True, timeout=60)
        response.raise_for_status()
        
        file_extension = '.mp3' if 'mp3' in audio_url.lower() else ('.aac' if 'aac' in audio_url.lower() else '.mp3')
        raw_file_path = os.path.join(CACHE_DIR_ZMP3, f"{safe_title}_{temp_id}_raw{file_extension}")
        
        with open(raw_file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192): f.write(chunk)
        
        logging.info(f"[process_audio] Đã tải về thành công. Kích thước: {os.path.getsize(raw_file_path)} bytes.")
        
        public_url = upload_to_temp_service(raw_file_path)
        
        return public_url, raw_file_path
    finally:
        pass 

def draw_zingmp3_song_list_image(songs):
    CARD_W, CARD_H = 560, 150; PADDING = 30; CARD_TOP_OFFSET = 60; CARD_GAP = 6
    COLS = 1 if len(songs) <= 3 else 2; ROWS = (len(songs) + COLS - 1) // COLS
    WIDTH = CARD_W * COLS + PADDING * (COLS + 1); HEIGHT = CARD_H * ROWS + PADDING * (ROWS + 1) + 30 + CARD_TOP_OFFSET - (CARD_GAP * (ROWS - 1))
    bg_color = (34, 34, 58); card_color = (255, 255, 255, 238)
    font_title = get_font(28); font_small = get_font(19); font_artist = get_font(22); font_index = get_font(26)
    emoji_font = get_emoji_font(32)
    
    img = Image.new("RGBA", (WIDTH, HEIGHT), bg_color); draw = ImageDraw.Draw(img)
    
    for idx, song in enumerate(songs):
        title = song['title']
        artist = song['artistsNames']
        cover = song['thumbnail']

        row = idx // COLS; col = idx % COLS
        cx = PADDING + col * (CARD_W + PADDING); cy = PADDING + row * (CARD_H + CARD_GAP + PADDING) + CARD_TOP_OFFSET - CARD_GAP * row
        
        draw.rounded_rectangle([cx, cy, cx+CARD_W, cy+CARD_H], radius=24, fill=card_color)
        
        draw.text((cx+10, cy+7), "🎶", font=emoji_font, fill=(50,150,250,255))
        
        if cover:
            try:
                # Giảm timeout tải ảnh để tránh tắc nghẽn
                cover_data = requests.get(cover, headers=get_headers(), timeout=3).content
                with Image.open(BytesIO(cover_data)) as cover_img:
                    cover_img = cover_img.convert("RGBA"); min_side = min(cover_img.width, cover_img.height)
                    left = (cover_img.width - min_side) // 2; top = (cover_img.height - min_side) // 2
                    cover_img = cover_img.crop((left, top, left+min_side, top+min_side)).resize((95, 95), Image.LANCZOS)
                    img.paste(cover_img, (cx+44, cy+5), cover_img)
            except Exception as e: logging.warning(f"Không thể tải ảnh bìa Zing MP3 (tốc độ cao): {e}")
            
        title_x = cx + 160; title_y = cy + 22; max_title_width = CARD_W - 185
        title_lines = []; line = ""
        for word in title.split():
            test_line = (line + " " if line else "") + word
            if font_title.getlength(test_line) > max_title_width and line: title_lines.append(line); line = word
            else: line = test_line
        if line: title_lines.append(line)
        for l in title_lines[:2]: draw.text((title_x, title_y), l, font=font_title, fill=(40, 40, 70)); title_y += font_title.size + 1
        
        artist_text = f"👤 Nghệ sĩ: {artist}"
        draw.text((title_x, cy + 22 + font_title.size * 2 + 10), artist_text, font=font_artist, fill=(100, 100, 200))
        
        idx_box_w, idx_box_h = 44, 36; idx_x = cx + CARD_W - idx_box_w - 8; idx_y = cy + 10
        draw.rounded_rectangle([idx_x, idx_y, idx_x+idx_box_w, idx_y+idx_box_h], radius=14, fill=(210,220,250,255))
        draw.text((idx_x + idx_box_w//2 - font_index.getlength(str(idx+1))//2, idx_y+6), f"{idx+1}", font=font_index, fill=(97, 97, 180))
       
    main_title = "KẾT QUẢ TÌM KIẾM ZING MP3"
    draw.text((WIDTH//2 - get_font(36).getlength(main_title)//2, 18), main_title, font=get_font(36), fill=(255,255,255,240))
    footer = f"➜ Nhập: zingmp3 <số> hoặc chỉ cần reply số để tải nhạc/xem lời. Bạn có {SEARCH_TIMEOUT}s để chọn."
    draw.text((WIDTH//2 - font_small.getlength(footer)//2, HEIGHT-28), footer, font=font_small, fill=(210,210,230))
    
    out_path = autosave(img)
    return out_path

def draw_zingmp3_song_detail_image(title, artist, quality, cover):
    CARD_W = 560; PADDING = 30; BASE_CARD_H = 150
    font_title = get_font(28); font_small = get_font(19); font_quality = get_font(24); emoji_info_font = get_emoji_font(23)
    
    title_x = PADDING + 160; max_title_width = CARD_W - 185; formatted_title = f"{title}"
    title_lines = []; line = ""
    for word in formatted_title.split():
        test_line = (line + " " if line else "") + word
        if font_title.getlength(test_line) > max_title_width and line: title_lines.append(line); line = word
        else: line = test_line
    if line: title_lines.append(line)
    num_title_lines = min(len(title_lines), 2); extra_height = (font_title.size + 1) * (num_title_lines - 1)
    CARD_H = BASE_CARD_H + extra_height; WIDTH = CARD_W + 2 * PADDING; HEIGHT = CARD_H + 2 * PADDING
    
    bg_color = (34, 34, 58); card_color = (255, 255, 255, 238); img = Image.new("RGBA", (WIDTH, HEIGHT), bg_color); draw = ImageDraw.Draw(img)
    cx, cy = PADDING, PADDING; draw.rounded_rectangle([cx, cy, cx + CARD_W, cy + CARD_H], radius=24, fill=card_color)
    
    if cover:
        try:
            cover_data = requests.get(cover, headers=get_headers(), timeout=3).content
            with Image.open(BytesIO(cover_data)) as cover_img:
                cover_img = cover_img.convert("RGBA"); min_side = min(cover_img.width, cover_img.height)
                left = (cover_img.width - min_side) // 2; top = (cover_img.height - min_side) // 2
                cover_img = cover_img.crop((left, top, left + min_side, top + min_side)).resize((95, 95), Image.LANCZOS)
                img.paste(cover_img, (cx + 44, cy + 25), cover_img)
        except Exception as e: logging.warning(f"Không thể tải ảnh bìa chi tiết Zing MP3: {e}")
        
    title_y = cy + 22
    for l in title_lines[:2]: draw.text((title_x, title_y), l, font=font_title, fill=(40, 40, 70)); title_y += font_title.size + 1
    
    artist_y = cy + 22 + (font_title.size + 1) * num_title_lines + 10
    draw.text((title_x, artist_y), f"👤 {artist}", font=font_small, fill=(100, 100, 200))
    
    from_y = artist_y + font_small.size + 5; draw.text((title_x, from_y), "From Zing MP3", font=font_small, fill=(200, 100, 50))
    
    info_y = cy + CARD_H - 48; info_x = title_x
    draw.text((info_x, info_y), "🔊", font=emoji_info_font, fill=(90, 120, 140))
    draw.text((info_x + emoji_info_font.getlength("🔊") + 5, info_y + 2), f"Chất lượng: {quality}", font=font_quality, fill=(90, 120, 140))
    
    out_path = autosave(img)
    return out_path

def get_hash256(string): return hashlib.sha256(string.encode()).hexdigest()
def get_hmac512(string, key): return hmac.new(key.encode(), string.encode(), hashlib.sha512).hexdigest()

def get_sig(path, params):
    filtered_params = {}
    for key in sorted(params.keys()):
        if key in HASH_KEYS and params.get(key) is not None and params.get(key) != "":
            filtered_params[key] = params[key]
    param_string = ''.join(f"{key}={filtered_params[key]}" for key in filtered_params.keys())
    logging.debug(f"Chuỗi Param Hash cho {path}: {param_string}") 
    return get_hmac512(path + get_hash256(param_string), SECRET_KEY)

def get_cookie():
    response = requests.get(URL, headers=get_headers(), timeout=5)
    return response.cookies.get_dict()

def request_zing_mp3(path, params):
    try:
        cookies = get_cookie()
        response = requests.get(f"{URL}{path}", params=params, cookies=cookies, headers=get_headers(), timeout=10)
        response.raise_for_status()
        json_data = response.json()
        return json_data
    except Exception as e:
        logging.error(f"[request_zing_mp3] Lỗi khi gọi API {path}: {e}")
        return {"err": -1, "msg": f"Lỗi kết nối Zing MP3: {e}"}

def search_music(keyword):
    ctime = str(int(time.time()))
    path = "/api/v2/search"
    sig_params = {"q": keyword, "type": "song", "count": 10, "ctime": ctime, "version": VERSION}
    params = {"q": keyword, "type": "song", "count": 10, "ctime": ctime, "version": VERSION, "apiKey": API_KEY, "sig": get_sig(path, sig_params)}
    return request_zing_mp3(path, params)

def get_streaming_song(song_id):
    ctime = str(int(time.time()))
    path = "/api/v2/song/get/streaming"
    sig_params = {"id": song_id, "ctime": ctime, "version": VERSION}
    params = {"id": song_id, "ctime": ctime, "version": VERSION, "apiKey": API_KEY, "sig": get_sig(path, sig_params)}
    return request_zing_mp3(path, params)

def get_lyrics(song_id):
    try:
        response = requests.get("https://m.zingmp3.vn/xhr/lyrics/get-lyrics", params={"media_id": song_id}, headers=get_headers(), timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"[get_lyrics] Lỗi khi lấy lời bài hát cho {song_id}: {e}")
        return {"err": -1, "msg": "Failed to fetch lyrics"}

def handle_zing_command(message_text, message_object, thread_id, thread_type, author_id, client):
    if not hasattr(client, 'zingmp3_user_states'):
        client.zingmp3_user_states = {}
    user_states = client.zingmp3_user_states
    
    name = get_user_name(client, author_id)
    parts = message_text.strip().split()
    query_or_choice = " ".join(parts[1:]) if len(parts) > 1 else ""
    raw_file_path_to_delete = None 

    try:
        want_lyrics = query_or_choice.lower().endswith("lyric")
        index = -1
        
        if want_lyrics:
            choice_parts = query_or_choice.split()
            if len(choice_parts) >= 2:
                try: index = int(choice_parts[0]) - 1
                except ValueError: pass
        elif query_or_choice.isdigit():
            index = int(query_or_choice) - 1

        if index >= 0 and author_id in user_states:
            state = user_states[author_id]
            if time.time() - state['time_of_search'] > SEARCH_TIMEOUT:
                del user_states[author_id]
                client.replyMessage(Message(text=f"➜ {name}, kết quả đã hết hạn, vui lòng tìm lại."), message_object, thread_id, thread_type, ttl=60000)
                return

            songs = state['songs']
            if not (0 <= index < len(songs)):
                client.replyMessage(Message(text=f"➜ {name}, lựa chọn không hợp lệ. Vui lòng nhập số từ 1 đến {len(songs)}."), message_object, thread_id, thread_type, ttl=60000)
                return

            del user_states[author_id]
            song = songs[index]
            song_id = song["encodeId"]
            title = song["title"]
            artist = song["artistsNames"]


            if not want_lyrics:
                
                streaming_data = get_streaming_song(song_id)
                if streaming_data.get('err') != 0 or not streaming_data.get('data'):
                    raise Exception("Không thể tải bài hát này. Lỗi API hoặc nhạc VIP.")

                audio_url = streaming_data['data'].get('128') # Ưu tiên 128kbps để tải nhanh
                quality = "128kbps"
                
                if not audio_url or audio_url == "VIP":
                    audio_url = streaming_data['data'].get('320')
                    quality = "320kbps"
                    
                if not audio_url or audio_url == "VIP":
                    raise Exception("Không tìm thấy nguồn audio khả dụng.")

                client.replyMessage(Message(text=f"➜ Bắt đầu tải và upload bài hát '{title}' ({quality})... Vui lòng chờ 1 lát!"), message_object, thread_id, thread_type, ttl=60000)

                public_url, raw_file_path_to_delete = process_audio(audio_url, title) 
                voice_url = public_url

                file_size = os.path.getsize(raw_file_path_to_delete) if raw_file_path_to_delete and os.path.exists(raw_file_path_to_delete) else 0

                client.sendRemoteVoice(
                    voice_url,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    fileSize=int(file_size),
                    ttl=1800000
                )

                thumbnail_url = song.get('thumbnail')
                
                detail_image_path = draw_zingmp3_song_detail_image(
                    title, artist, quality, thumbnail_url
                )
                
                info_text = f"> From Zing MP3 <\n"
                info_text += f"Nhạc Bạn Chọn Đây!!!\n"
                info_text += f"🎵 {title} - {artist}"
                
                with Image.open(detail_image_path) as im: width, height = im.size
                client.sendLocalImage(
                    detail_image_path,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    width=width,
                    height=height,
                    message=Message(text=info_text),
                    ttl=210000
                )
                delete_file(detail_image_path) # Xóa file ảnh tạm
            
            else:
                client.replyMessage(Message(text=f"➜ Đang tìm lời bài hát '{title}'..."), message_object, thread_id, thread_type, ttl=60000)
                lyrics_data = get_lyrics(song_id)
                if lyrics_data.get('err') == 0 and lyrics_data.get('data') and len(lyrics_data['data']) > 0 and lyrics_data['data'][0].get('content'):
                    lyrics = re.sub(r'<br\s*/?>', '\n', lyrics_data['data'][0]['content']).strip()
                    text_lyrics = f"Lời bài hát: {title}\n\n{lyrics}"
                    client.replyMessage(Message(text=text_lyrics), message_object, thread_id, thread_type, ttl=300000)
                else:
                    client.replyMessage(Message(text=f"🚫 {name}, không tìm thấy lời bài hát cho '{title}'."), message_object, thread_id, thread_type, ttl=60000)
            
            return

        if not query_or_choice or index != -1: 
            client.replyMessage(Message(text=f"➜ {name}, vui lòng nhập tên bài hát. Ví dụ: zingmp3 Hạnh Phúc Nhé"), message_object, thread_id, thread_type, ttl=60000)
            return

        client.replyMessage(Message(text=f"➜ Đang tìm kiếm '{query_or_choice}' trên Zing MP3..."), message_object, thread_id, thread_type, ttl=30000)
        search_result = search_music(query_or_choice)

        if search_result.get('err') != 0 or not search_result.get('data') or not search_result['data'].get('items'):
            error_msg = search_result.get('msg', 'Lỗi không xác định.')
            client.replyMessage(Message(text=f"➜ {name}, tìm kiếm thất bại. Lỗi: {error_msg}. Vui lòng kiểm tra lại Key/Secret hoặc Zing MP3 đã chặn truy cập."), message_object, thread_id, thread_type, ttl=60000)
            return

        songs = search_result['data']['items'][:10]
        
        img_path = draw_zingmp3_song_list_image(songs)

        user_states[author_id] = {'songs': songs, 'time_of_search': time.time()}

        with Image.open(img_path) as im: width, height = im.size
        
        client.sendLocalImage(
            img_path, thread_id=thread_id, thread_type=thread_type, width=width, height=height,
            message=Message(text=f"➜ {name}, đây là kết quả cho '{query_or_choice}'."),
            ttl=120000
        )
        delete_file(img_path) 

    except Exception as e:
        logging.error(f"Lỗi trong handle_zingmp3_command: {e}", exc_info=True)
        client.replyMessage(Message(text=f"➜ {name}, đã xảy ra lỗi nghiêm trọng: {e}"), message_object, thread_id, thread_type, ttl=60000)
    finally:
        if raw_file_path_to_delete: 
            delete_file(raw_file_path_to_delete)


def PTA():
    return {
        'zingmp3': handle_zing_command
    }