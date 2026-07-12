# -*- coding: utf-8 -*-
import os, tempfile, requests
from io import BytesIO
from zlapi.models import Message

des = {
    "version": "1.1",
    "credits": "ngbao",
    "description": "Check user Roblox",
    "power": "Thành Viên"
}

ROBLOX_API = "https://users.roblox.com/v1"
THUMB_API = "https://thumbnails.roblox.com/v1/users/avatar-headshot"

# ================= ROBLOX UTILS =================
def get_user_id(username):
    url = f"{ROBLOX_API}/usernames/users"
    payload = {
        "usernames": [username],
        "excludeBannedUsers": False
    }
    r = requests.post(url, json=payload, timeout=10)
    data = r.json()
    if data.get("data"):
        return data["data"][0]["id"]
    return None

def get_user_info(user_id):
    return requests.get(f"{ROBLOX_API}/users/{user_id}", timeout=10).json()

def get_friends_count(user_id):
    return requests.get(
        f"https://friends.roblox.com/v1/users/{user_id}/friends/count",
        timeout=10
    ).json().get("count", 0)

def get_followers_count(user_id):
    return requests.get(
        f"https://friends.roblox.com/v1/users/{user_id}/followers/count",
        timeout=10
    ).json().get("count", 0)

def get_followings_count(user_id):
    return requests.get(
        f"https://friends.roblox.com/v1/users/{user_id}/followings/count",
        timeout=10
    ).json().get("count", 0)

def get_avatar_url(user_id):
    url = f"{THUMB_API}?userIds={user_id}&size=420x420&format=Png&isCircular=false"
    data = requests.get(url, timeout=10).json()
    if data.get("data"):
        return data["data"][0].get("imageUrl")
    return None

def download_image(url):
    try:
        r = requests.get(url, timeout=10)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f:
            f.write(r.content)
            return f.name
    except:
        return None

# ================= HANDLE =================
def handle_roblox(message, msg_obj, thread_id, thread_type, author_id, client):
    args = message.split(maxsplit=1)
    if len(args) < 2:
        client.replyMessage(
            Message(text="❗ Dùng: roblox <username>"),
            msg_obj, thread_id, thread_type
        )
        return

    username = args[1].strip()
    uid = get_user_id(username)

    if not uid:
        client.replyMessage(
            Message(text="❌ Không tìm thấy user Roblox."),
            msg_obj, thread_id, thread_type
        )
        return

    info = get_user_info(uid)
    friends = get_friends_count(uid)
    followers = get_followers_count(uid)
    followings = get_followings_count(uid)
    avatar_url = get_avatar_url(uid)

    text = (
        "🎮 ROBLOX USER INFO\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👤 Username: {info.get('name')}\n"
        f"🆔 User ID: {uid}\n"
        f"📅 Ngày tạo: {info.get('created')}\n\n"
        f"🧑‍🤝‍🧑 Bạn bè: {friends}\n"
        f"❤️ Followers: {followers}\n"
        f"👥 Following: {followings}\n\n"
        f"🔗 Profile:\nhttps://www.roblox.com/users/{uid}/profile"
    )

    # 👉 GỬI ẢNH AVATAR (NẾU CÓ)
    if avatar_url:
        img_path = download_image(avatar_url)
        if img_path:
            client.sendLocalImage(
                img_path,
                thread_id=thread_id,
                thread_type=thread_type,
                message=Message(text=text)
            )
            os.remove(img_path)
            return

    # fallback text
    client.replyMessage(
        Message(text=text),
        msg_obj,
        thread_id,
        thread_type
    )

# ================= REGISTER =================
def PTA():
    return {
        "roblox": handle_roblox
    }
