# -*- coding: utf-8 -*-
import os
import json
import random
import datetime
import requests
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from zlapi.models import Message

# ==================== MÔ TẢ MODULE ====================
des = {
    'version': "4.5.0",
    'credits': "ngbao",
    'description': "Top Chat Nhiều Nhất",
    'power': "Thành viên"
}

# ==================== THƯ MỤC CACHE & FONT ====================
CACHE_PATH = "modules/cache/"
AVT_CACHE = os.path.join(CACHE_PATH, "avatar")
BG_DIR = "background/"
os.makedirs(CACHE_PATH, exist_ok=True)
os.makedirs(AVT_CACHE, exist_ok=True)
os.makedirs(BG_DIR, exist_ok=True)

FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
EMOJI_FONT_PATH = "modules/cache/font/NotoEmoji-Bold.ttf"

rank_info_path = Path.cwd() / "rank-info.json"
import threading
rank_lock = threading.Lock()

# ==================== BỐ ĐỆM GHI FILE (chỉ ghi mỗi 30s) ====================
_rank_data_cache = None       # Dữ liệu để trong RAM
_rank_dirty = False           # Flag: có thay đổi chưa ghi
_rank_last_flush = 0          # Thời gian flush gần nhất
FLUSH_INTERVAL = 30           # Ghi xuống disk mỗi 30 giây

def _flush_rank_info():
    """Ghi rank-info.json xuống disk nếu có thay đổi (gọi từ background thread)."""
    global _rank_dirty, _rank_last_flush, _rank_data_cache
    import time
    while True:
        time.sleep(FLUSH_INTERVAL)
        with rank_lock:
            if _rank_dirty and _rank_data_cache is not None:
                try:
                    tmp = str(rank_info_path) + ".tmp"
                    with open(tmp, "w", encoding="utf-8") as f:
                        json.dump(_rank_data_cache, f, ensure_ascii=False)
                    import shutil
                    shutil.move(tmp, str(rank_info_path))
                    _rank_dirty = False
                    _rank_last_flush = time.time()
                except OSError as e:
                    import errno as _errno
                    if e.errno == _errno.ENOSPC:
                        print("⚠️ [topchat] Server hết dung lượng đĩa! Không thể ghi rank-info.json")
                    else:
                        print("❌ Lỗi ghi rank-info.json:", e)
                except Exception as e:
                    print("❌ Lỗi ghi rank-info.json:", e)

# Khởi động background flush thread
_flush_thread = threading.Thread(target=_flush_rank_info, daemon=True)
_flush_thread.start()

def read_rank_info():
    global _rank_data_cache
    with rank_lock:
        if _rank_data_cache is not None:
            return dict(_rank_data_cache)  # trả về bản sao
        try:
            if not rank_info_path.exists():
                _rank_data_cache = {"groups": {}}
                return dict(_rank_data_cache)
            with open(rank_info_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    _rank_data_cache = {"groups": {}}
                    return dict(_rank_data_cache)
                data = json.loads(content)
            if "groups" not in data:
                data["groups"] = {}
            _rank_data_cache = data
            return dict(_rank_data_cache)
        except Exception as e:
            print("❌ Lỗi đọc rank-info.json:", e)
            _rank_data_cache = {"groups": {}}
            return dict(_rank_data_cache)

def save_rank_info(data):
    """Cập nhật cache và đánh dấu dirty — sẽ ghi xuống disk sau đủ {FLUSH_INTERVAL}s."""
    global _rank_data_cache, _rank_dirty
    with rank_lock:
        _rank_data_cache = data
        _rank_dirty = True

# ==================== FONT & BACKGROUND ====================
def get_font(size, is_emoji=False):
    path = EMOJI_FONT_PATH if is_emoji else FONT_PATH
    if os.path.exists(path):
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def get_random_background(width, height):
    try:
        files = [f for f in os.listdir(BG_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if not files:
            return Image.new("RGBA", (width, height), (240, 245, 255, 255))
        path = os.path.join(BG_DIR, random.choice(files))
        bg = Image.open(path).convert("RGBA")
        bg = bg.resize((width, height), Image.LANCZOS)
        return bg.filter(ImageFilter.GaussianBlur(25))
    except:
        return Image.new("RGBA", (width, height), (240, 245, 255, 255))

# ==================== LẤY TÊN & AVATAR NGƯỜI DÙNG ====================
def _extract_name_from_profile(profile):
    if not profile or not isinstance(profile, dict):
        return None
    keys = [
        "name", "display_name", "displayName", "fullname", "full_name",
        "first_name", "last_name", "nick", "nickname", "display"
    ]
    for k in keys:
        v = profile.get(k)
        if v and isinstance(v, str) and v.strip():
            return v.strip()
    for possible in ("profile", "changed_profiles", "user", "data"):
        nested = profile.get(possible)
        if isinstance(nested, dict):
            for key, val in nested.items():
                if isinstance(val, dict):
                    n = _extract_name_from_profile(val)
                    if n:
                        return n
            n = _extract_name_from_profile(nested)
            if n:
                return n
    return None

def get_user_name_by_id(client, uid):
    try:
        info = None
        try:
            info = client.fetchUserInfo(uid)
        except Exception:
            try:
                info = client.getUserInfo(uid)
            except Exception:
                info = None

        if info and isinstance(info, dict):
            name = _extract_name_from_profile(info)
            if name:
                return name
            cp = info.get("changed_profiles") or info.get("changedProfile") or info.get("profiles")
            if isinstance(cp, dict):
                p = cp.get(str(uid)) or cp.get(uid)
                if isinstance(p, dict):
                    name = _extract_name_from_profile(p)
                    if name:
                        return name
            for k in ("user", "data", "profile"):
                p = info.get(k)
                if isinstance(p, dict):
                    name = _extract_name_from_profile(p)
                    if name:
                        return name
        try:
            alt = None
            if hasattr(client, "getProfile"):
                alt = client.getProfile(uid)
            elif hasattr(client, "get_user"):
                alt = client.get_user(uid)
            if isinstance(alt, dict):
                name = _extract_name_from_profile(alt)
                if name:
                    return name
        except:
            pass
    except Exception:
        pass
    return str(uid)

def get_user_avatar(client, uid):
    try:
        info = client.fetchUserInfo(uid)
        avatar = None
        if isinstance(info, dict):
            p = (
                info.get("changed_profiles", {}).get(str(uid))
                or info.get("profile")
                or info.get("data")
                or info
            )
            if isinstance(p, dict):
                for k in ("avatar", "avatarUrl", "avatar_url", "photo"):
                    if k in p and isinstance(p[k], str) and p[k].startswith("http"):
                        avatar = p[k]
                        break

        if not avatar:
            return None

        save_path = os.path.join(AVT_CACHE, f"{uid}.jpg")
        if not os.path.exists(save_path):
            r = requests.get(avatar, timeout=5)
            if r.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(r.content)
        return save_path
    except Exception:
        return None

# ==================== CẬP NHẬT ĐIỂM NGƯỜI DÙNG ====================
def update_user_rank(client, thread_id, author_id):
    data = read_rank_info()
    group = data["groups"].setdefault(str(thread_id), {"users": []})
    users = group.setdefault("users", [])

    user_name = get_user_name_by_id(client, author_id)
    found = False
    for user in users:
        if str(user["UserID"]) == str(author_id):
            user["Rank"] += 1
            user["UserName"] = user_name
            user["LastActive"] = datetime.datetime.now().isoformat()
            found = True
            break
    if not found:
        users.append({
            "UserID": author_id,
            "UserName": user_name,
            "Rank": 1,
            "LastActive": datetime.datetime.now().isoformat()
        })
    save_rank_info(data)

# ==================== TẠO ẢNH TOP CHAT ====================
def create_topchat_image(sorted_users, client, requester_name):
    WIDTH, HEIGHT = 1080, 1440
    bg = get_random_background(WIDTH, HEIGHT)
    overlay = Image.new("RGBA", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(overlay)

    font_title = get_font(70)
    font_name = get_font(42)
    font_count = get_font(40)
    font_footer = get_font(28)

    title = "🏆 TOP NHẮN NHIỀU NHẤT"
    bbox = draw.textbbox((0, 0), title, font=font_title)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((WIDTH - tw) / 2, 100), title, font=font_title, fill=(20, 20, 20, 255))

    y = 280
    row_height = 130
    colors = [(255, 215, 0), (192, 192, 192), (205, 127, 50)]

    for idx, user in enumerate(sorted_users[:10]):
        real_name = get_user_name_by_id(client, user["UserID"])
        rank_color = colors[idx] if idx < 3 else (255, 255, 255)
        y_box = y + idx * (row_height + 20)

        box_x1, box_y1 = 100, y_box
        box_x2, box_y2 = WIDTH - 100, y_box + row_height
        draw.rounded_rectangle((box_x1, box_y1, box_x2, box_y2), radius=50, fill=(255, 255, 255, 180))

        circle_radius = 35
        circle_x = box_x1 + 40
        circle_y = box_y1 + row_height / 2
        draw.ellipse((circle_x - circle_radius, circle_y - circle_radius, circle_x + circle_radius, circle_y + circle_radius), fill=rank_color)
        rank_text = str(idx + 1)
        rbbox = draw.textbbox((0, 0), rank_text, font=font_name)
        rw, rh = rbbox[2] - rbbox[0], rbbox[3] - rbbox[1]
        draw.text((circle_x - rw / 2, circle_y - rh / 2), rank_text, font=font_name, fill=(0, 0, 0))

        avatar_path = get_user_avatar(client, user["UserID"])
        if avatar_path and os.path.exists(avatar_path):
            try:
                avatar = Image.open(avatar_path).convert("RGBA")
                avatar = avatar.resize((90, 90))
                mask = Image.new("L", (90, 90), 0)
                ImageDraw.Draw(mask).ellipse((0, 0, 90, 90), fill=255)
                overlay.paste(avatar, (circle_x + 60, int(circle_y - 45)), mask)
            except:
                pass

        name_x = circle_x + 170
        name_y = box_y1 + (row_height - 45) / 2
        draw.text((name_x, name_y), real_name, font=font_name, fill=(0, 0, 0))

        count_text = f"{user['Rank']} tin nhắn"
        cbbox = draw.textbbox((0, 0), count_text, font=font_count)
        cw, ch = cbbox[2] - cbbox[0], cbbox[3] - cbbox[1]
        draw.text((box_x2 - cw - 50, name_y), count_text, font=font_count, fill=(0, 0, 0))

    footer = f"Bot: {des['credits']} | v{des['version']}"
    fbbox = draw.textbbox((0, 0), footer, font=font_footer)
    fw, fh = fbbox[2] - fbbox[0], fbbox[3] - fbbox[1]
    draw.text(((WIDTH - fw) / 2, HEIGHT - 80), footer, font=font_footer, fill=(255, 255, 255, 220))

    final_img = Image.alpha_composite(bg, overlay)
    output_path = os.path.join(CACHE_PATH, "topchat.jpg")
    final_img.convert("RGB").save(output_path, "JPEG", quality=95)
    return output_path

# ==================== XỬ LÝ LỆNH ====================
def handle_topchat_command(message, message_object, thread_id, thread_type, author_id, client):
    user_name = get_user_name_by_id(client, author_id)
    msg_text = str(message).strip().lower()

    # Reset dữ liệu nhóm (ai cũng có thể dùng)
    if msg_text in ["topchat rs", "!topchat rs", "/topchat rs"]:
        data = read_rank_info()
        if str(thread_id) in data.get("groups", {}):
            data["groups"].pop(str(thread_id))
            save_rank_info(data)
            client.sendMessage(
                Message(text=f"♻️ Đã reset dữ liệu top chat của nhóm!\n\n[Thực hiện bởi: {user_name}]"),
                thread_id, thread_type, ttl=20000
            )
        else:
            client.sendMessage(
                Message(text=f"⚠️ Nhóm này chưa có dữ liệu để reset."),
                thread_id, thread_type, ttl=20000
            )
        return

    # Hiển thị top chat
    rank_info = read_rank_info()
    group_data = rank_info["groups"].setdefault(str(thread_id), {"users": []})
    group_users = group_data.get("users", [])

    if not group_users:
        client.sendMessage(
            Message(text=f"📭 Chưa có dữ liệu xếp hạng.\n\n[Ask by: {user_name}]"),
            thread_id, thread_type, ttl=20000
        )
        return

    sorted_users = sorted(group_users, key=lambda x: x["Rank"], reverse=True)
    img_path = create_topchat_image(sorted_users, client, user_name)
    client.sendLocalImage(img_path, thread_id=thread_id, thread_type=thread_type, width=1080, height=1440, ttl=60000)

# ==================== ĐĂNG KÝ LỆNH ====================
def PTA():
    return {
        "topchat": handle_topchat_command
    }