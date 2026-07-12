# -*- coding: utf-8 -*-
import os
import traceback
from io import BytesIO
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import requests
from zlapi.models import Message

des = {
    'version': "2.6.7",
    'credits': "ngbao",
    'description': "Hiển thị Thông tin nhóm - Chủ & Phó nhóm",
    'power': "Thành viên"
}

CACHE_PATH = "modules/cache/"
os.makedirs(CACHE_PATH, exist_ok=True)
FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
DEFAULT_AVATAR_PATH = "modules/cache/default_avatar.png"
if not os.path.isfile(DEFAULT_AVATAR_PATH):
    Image.new("RGBA", (100, 100), (100, 100, 100, 255)).save(DEFAULT_AVATAR_PATH)

def fetch_image(url):
    if not url:
        return None
    try:
        r = requests.get(url, stream=True, timeout=10)
        r.raise_for_status()
        return Image.open(BytesIO(r.content)).convert("RGBA")
    except:
        return None

def circle_crop(img, size):
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size[0], size[1]), fill=255)
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    img = img.resize(size)
    out.paste(img, (0, 0), mask)
    return out

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
        return avatar
    except:
        return None

def prepare_group_data(group, client):
    def get_user(uid):
        try:
            info = client.fetchUserInfo(uid)
            if isinstance(info, dict):
                if "changed_profiles" in info and str(uid) in info["changed_profiles"]:
                    name = info["changed_profiles"][str(uid)].get("zaloName", "Người dùng")
                else:
                    name = info.get("name", "Người dùng")
            else:
                name = getattr(info, "name", "Người dùng")
            avatar = get_user_avatar(client, uid)
            return name, avatar
        except:
            return "Người dùng", None

    creator_id = getattr(group, 'creatorId', None)
    creator_name, creator_avatar = get_user(creator_id)

    admins = []
    for uid in getattr(group, 'adminIds', []):
        n, av = get_user(uid)
        admins.append((uid, n, av))

    group_name = getattr(group, 'name', getattr(group, 'groupName', "Nhóm"))
    group_avatar = getattr(group, 'fullAvt', None)
    created_time = None
    if hasattr(group, "createdTime") and group.createdTime:
        try:
            created_time = datetime.fromtimestamp(group.createdTime / 1000).strftime('%d/%m/%Y lúc %H:%M')
        except:
            created_time = None

    return creator_name, creator_avatar, admins, group_name, group_avatar, created_time

def create_group_admin_card(creator_name, creator_avatar, admins, group_name, group_avatar, account_avatar, created_time=None):
    width = 1200
    row_height = 160
    users = [{"name": creator_name, "role": "Chủ Nhóm", "avatar": creator_avatar}]
    for uid, name, av in admins:
        users.append({"name": name, "role": "Phó Nhóm", "avatar": av})
    rows = (len(users) + 1) // 2
    height = 300 + rows * row_height + 50
    img = Image.new("RGBA", (width, height), (20, 10, 40))
    draw = ImageDraw.Draw(img)

    font_title = ImageFont.truetype(FONT_PATH, 60)
    font_group = ImageFont.truetype(FONT_PATH, 42)
    font_name = ImageFont.truetype(FONT_PATH, 32)
    font_role = ImageFont.truetype(FONT_PATH, 28)
    font_stt = ImageFont.truetype(FONT_PATH, 36)
    font_time = ImageFont.truetype(FONT_PATH, 24)

    title = "DANH SÁCH KEY NHÓM"
    tx = (width - draw.textlength(title, font=font_title)) // 2
    draw.text((tx, 30), title, fill=(255, 255, 255), font=font_title)

    group_avt_size = 120
    gx = (width // 2) - group_avt_size - 10
    gy = 130
    if group_avatar:
        gr_avt = fetch_image(group_avatar)
        if gr_avt:
            gr_avt = circle_crop(gr_avt, (group_avt_size, group_avt_size))
            img.paste(gr_avt, (gx, gy), gr_avt)
    else:
        gr_avt = circle_crop(Image.open(DEFAULT_AVATAR_PATH), (group_avt_size, group_avt_size))
        img.paste(gr_avt, (gx, gy), gr_avt)

    name_x = gx + group_avt_size + 20
    name_y = gy + (group_avt_size - 42) // 2
    draw.text((name_x, name_y), group_name, fill=(255, 215, 0), font=font_group)

    if account_avatar:
        av = circle_crop(account_avatar, (120, 120))
        img.paste(av, (width - 160, 25), av)

    x_left = 60
    x_right = 620
    y = 300

    for i, u in enumerate(users):
        x = x_left if i % 2 == 0 else x_right
        rect_w, rect_h = 520, 130
        draw.rounded_rectangle(
            (x, y, x + rect_w, y + rect_h),
            radius=22,
            outline=(255, 200, 0),
            width=4
        )

        user_avt_url = u["avatar"]
        if user_avt_url:
            av_img = fetch_image(user_avt_url)
            if av_img:
                av_img = circle_crop(av_img, (90, 90))
            else:
                av_img = circle_crop(Image.open(DEFAULT_AVATAR_PATH), (90, 90))
        else:
            av_img = circle_crop(Image.open(DEFAULT_AVATAR_PATH), (90, 90))

        img.paste(av_img, (x + 80, y + 20), av_img)

        stt_x = x + 15
        stt_y = y + (rect_h - font_stt.size) // 2
        draw.text((stt_x, stt_y), f"#{i + 1}", fill=(255, 200, 0), font=font_stt)

        text_x = x + 200
        draw.text((text_x, y + 30), u["name"], fill=(255, 255, 255), font=font_name)
        role_color = (220, 220, 220) if u["role"] == "Phó Nhóm" else (255, 215, 0)
        draw.text((text_x, y + 75), u["role"], fill=role_color, font=font_role)

        if i % 2 == 1:
            y += row_height

    if created_time:
        text_width = draw.textlength(created_time, font=font_time)
        draw.text((width - text_width - 20, height - 30), created_time, fill=(180, 180, 180), font=font_time)

    return img

def handle_groupinfo_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        acc = client.fetchAccountInfo()
        acc_avatar_url = getattr(acc, "avatar", None)
        acc_avatar = fetch_image(acc_avatar_url) if acc_avatar_url else None

        group_info_map = client.fetchGroupInfo(thread_id).gridInfoMap
        group = group_info_map.get(thread_id) if isinstance(group_info_map, dict) else group_info_map
        if not group:
            raise ValueError("Không lấy được thông tin nhóm.")

        creator_name, creator_avatar, admins, group_name, group_avatar, created_time = prepare_group_data(group, client)

        print("Group name:", group_name)
        print("Creator:", creator_name)
        print("Admins:", admins)
        print("Created time:", created_time)

        img = create_group_admin_card(creator_name, creator_avatar, admins, group_name, group_avatar, acc_avatar, created_time)

        output_path = os.path.join(CACHE_PATH, "group_admin_card.png")
        img.save(output_path)

        client.sendLocalImage(
            output_path,
            thread_id=thread_id,
            thread_type=thread_type,
            width=img.width,
            height=img.height,
            ttl=120000
        )

    except Exception as e:
        print("Lỗi:", e)
        traceback.print_exc()
        client.sendMessage(
            Message(text="❌ Có lỗi khi tạo ảnh thông tin nhóm."),
            thread_id=thread_id,
            thread_type=thread_type,
            ttl=120000
        )

def PTA():
    return {
        "key": handle_groupinfo_command
    }