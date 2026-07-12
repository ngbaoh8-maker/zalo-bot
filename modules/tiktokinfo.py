import requests
import tempfile
import os
import re
from zlapi.models import *

des = {
    "version": "1.4",
    "credits": "ngbao",
    "description": "Check TikTok user + avatar",
    "power": "Thành Viên"
}

API_TEMPLATE = "https://adidaphat.site/tiktok?type=userinfo&unique_id={username}"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# ================= PARSE NUMBER (K / M) =================
def parse_number(val):
    if val is None:
        return 0

    if isinstance(val, (int, float)):
        return int(val)

    if isinstance(val, str):
        v = val.replace(",", "").strip().upper()
        if v.endswith("K"):
            return int(float(v[:-1]) * 1_000)
        if v.endswith("M"):
            return int(float(v[:-1]) * 1_000_000)
        if v.isdigit():
            return int(v)

    return 0

# ================= TÌM KEY TRONG JSON =================
def deep_find(data, keys):
    if isinstance(data, dict):
        for k, v in data.items():
            if k in keys:
                return v
            res = deep_find(v, keys)
            if res is not None:
                return res
    elif isinstance(data, list):
        for i in data:
            res = deep_find(i, keys)
            if res is not None:
                return res
    return None

# ================= TÌM AVATAR =================
def find_avatar(data):
    return deep_find(data, [
        "avatar",
        "avatar_url",
        "avatarThumb",
        "avatarMedium",
        "avatarLarger"
    ])

# ================= DOWNLOAD ẢNH =================
def download_image(url):
    r = requests.get(url, headers=HEADERS, timeout=10)
    r.raise_for_status()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    tmp.write(r.content)
    tmp.close()
    return tmp.name

# ================= HANDLE =================
def handle_tiktok(message, message_object, thread_id, thread_type, author_id, client):
    args = message.split()
    if len(args) < 2:
        client.replyMessage(
            Message(text="❌ Dùng: .tiktok <username>"),
            message_object, thread_id, thread_type
        )
        return

    username = args[1].strip()
    url = API_TEMPLATE.format(username=username)

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        data = res.json()
    except Exception as e:
        client.replyMessage(
            Message(text=f"⚠️ API lỗi: {e}"),
            message_object, thread_id, thread_type
        )
        return

    root = data.get("data", data)

    uid = deep_find(root, ["unique_id", "username"]) or username
    nickname = deep_find(root, ["nickname"]) or "—"
    bio = deep_find(root, ["signature", "bio"]) or "—"

    follower = parse_number(
        deep_find(root, ["followerCount", "follower_count", "followers"])
    )
    following = parse_number(
        deep_find(root, ["followingCount", "following_count"])
    )
    like = parse_number(
        deep_find(root, ["heartCount", "heart_count", "likes"])
    )
    video = parse_number(
        deep_find(root, ["videoCount", "video_count", "videos"])
    )

    verified = bool(deep_find(root, ["verified", "is_verified"]))

    avatar_url = find_avatar(root)

    caption = (
        f"🎵 TIKTOK USER\n"
        f"━━━━━━━━━━━━━━\n"
        f"👤 @{uid}\n"
        f"📛 {nickname}\n"
        f"⭐ Verified: {'Có' if verified else 'Không'}\n"
        f"👥 Follower: {follower:,}\n"
        f"👣 Following: {following:,}\n"
        f"💗 Tim: {like:,}\n"
        f"🎬 Video: {video}\n"
        f"📝 Bio: {bio}"
    )

    # gửi ảnh + text chung
    if avatar_url and isinstance(avatar_url, str):
        try:
            img_path = download_image(avatar_url)
            client.sendLocalImage(
                imagePath=img_path,
                message=Message(text=caption),
                thread_id=thread_id,
                thread_type=thread_type
            )
            os.remove(img_path)
            return
        except:
            pass

    client.sendMessage(
        Message(text=caption),
        thread_id,
        thread_type
    )

# ================= REGISTER =================
def PTA():
    return {
        "tiktok": handle_tiktok
    }