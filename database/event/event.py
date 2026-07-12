import os
import json
import random
import requests
from io import BytesIO
from datetime import datetime
from threading import Thread
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps
from zlapi.models import *

EVENT_SETTINGS_FILE = "data/welcome_setting.json"
CACHE_DIR = "modules/cache"
FONT_DIR = "font"

# ============ Lời chào / tạm biệt ngẫu nhiên ============
WELCOME_TEXTS = [
    "Chào Mừng Bạn Đến Với Nhóm! 🎉",
    "Welcome! Chúc Bạn Vui Vẻ! 💖",
    "Xin Chào! Rất Vui Được Gặp Bạn! ✨",
    "Chào Mừng Thành Viên Mới! 🌟",
    "Welcome To The Group! 🔥",
    "Hoan Nghênh Bạn! 💫",
    "Chào Bạn Mới! Hãy Cùng Vui Nào! 🎊",
    "Xin Chào & Chào Mừng! 🥳",
]

GOODBYE_TEXTS = [
    "Tạm Biệt Bạn! Hẹn Gặp Lại! 👋",
    "Goodbye! Chúc Bạn May Mắn! 💔",
    "Tạm Biệt Nhé! 🥺",
    "Bye Bye! Sẽ Nhớ Bạn! 😢",
    "Hẹn Gặp Lại Bạn! 🌙",
    "Goodbye & Take Care! 💫",
    "Tạm Biệt! Chúc Bạn Bình An! 🍃",
]

KICK_TEXTS = [
    "Đã Bị Kick Khỏi Nhóm! ⚡",
    "Bạn Đã Bị Mời Ra! 🚫",
    "Kicked Out! Bye Bye! 👢",
    "Đã Bị Loại Khỏi Nhóm! 💥",
]

# ============ Màu gradient đẹp ============
GRADIENT_PALETTES = [
    [(138, 43, 226), (0, 191, 255)],    # Purple → Cyan
    [(255, 0, 128), (255, 165, 0)],      # Pink → Orange
    [(0, 206, 209), (148, 0, 211)],      # Teal → Violet
    [(255, 69, 0), (255, 215, 0)],       # Red → Gold
    [(0, 255, 127), (0, 100, 255)],      # Green → Blue
    [(255, 20, 147), (138, 43, 226)],    # DeepPink → Purple
    [(0, 191, 255), (255, 105, 180)],    # DeepSkyBlue → HotPink
]


def load_allowed_groups():
    if os.path.exists(EVENT_SETTINGS_FILE):
        with open(EVENT_SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("groups", [])
    return []


def get_font(name, size):
    """Lấy font, fallback nếu không tìm thấy."""
    paths = [
        os.path.join(FONT_DIR, name),
        os.path.join(FONT_DIR, "BeVietnamPro-Bold.ttf"),
        os.path.join(FONT_DIR, "arial.ttf"),
        os.path.join(FONT_DIR, "NotoSans-Bold.ttf"),
        "BeVietnamPro-Bold.ttf",
        "BeVietnamPro-SemiBold.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def download_image(url):
    """Tải ảnh từ URL, trả về Image hoặc None."""
    if not url:
        return None
    try:
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        return Image.open(BytesIO(resp.content)).convert("RGBA")
    except Exception:
        return None


def make_circle_avatar(img, size):
    """Tạo avatar tròn với viền gradient."""
    img = img.resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    output.paste(img, (0, 0), mask)
    return output


def draw_circle_border(draw, cx, cy, radius, color1, color2, width=4):
    """Vẽ viền tròn gradient cho avatar."""
    for i in range(360):
        t = i / 360.0
        r = int(color1[0] * (1 - t) + color2[0] * t)
        g = int(color1[1] * (1 - t) + color2[1] * t)
        b = int(color1[2] * (1 - t) + color2[2] * t)
        import math
        angle = math.radians(i)
        for w in range(width):
            x = cx + int((radius + w) * math.cos(angle))
            y = cy + int((radius + w) * math.sin(angle))
            try:
                draw.point((x, y), fill=(r, g, b, 255))
            except Exception:
                pass


def create_gradient_overlay(width, height, color1, color2, alpha=180):
    """Tạo overlay gradient ngang."""
    overlay = Image.new("RGBA", (width, height))
    for x in range(width):
        t = x / width
        r = int(color1[0] * (1 - t) + color2[0] * t)
        g = int(color1[1] * (1 - t) + color2[1] * t)
        b = int(color1[2] * (1 - t) + color2[2] * t)
        for y in range(height):
            overlay.putpixel((x, y), (r, g, b, alpha))
    return overlay


def create_event_image(
    member_name, member_avatar_url, member_cover_url, bot_avatar_url,
    group_name, group_cover_url, event_type
):
    """
    Tạo ảnh sự kiện đẹp:
    [Avatar người join/out] --- [Lời chào/tạm biệt] --- [Avatar bot]
    Nền: bia user hoặc bia nhóm với overlay gradient
    """
    W, H = 900, 320

    # === 1. Nền: lấy bia user hoặc bia nhóm hoặc tạo gradient ===
    palette = random.choice(GRADIENT_PALETTES)
    c1, c2 = palette

    bg_url = member_cover_url if member_cover_url else (member_avatar_url if member_avatar_url else group_cover_url)
    cover_img = download_image(bg_url)
    if cover_img:
        cover_img = ImageOps.fit(cover_img.convert("RGBA"), (W, H), method=Image.LANCZOS, centering=(0.5, 0.42))
        # Làm mờ nhẹ và tối đi
        cover_img = cover_img.filter(ImageFilter.GaussianBlur(radius=4))
        enhancer = ImageEnhance.Brightness(cover_img)
        cover_img = enhancer.enhance(0.45)
        bg = cover_img
    else:
        bg = create_gradient_overlay(W, H, c1, c2, alpha=255)

    # Overlay gradient bán trong suốt
    overlay = create_gradient_overlay(W, H, c1, c2, alpha=90)
    bg = Image.alpha_composite(bg, overlay)

    draw = ImageDraw.Draw(bg)

    # === 2. Khung viền đẹp ===
    border_w = 3
    # Viền ngoài
    draw.rounded_rectangle(
        [border_w, border_w, W - border_w, H - border_w],
        radius=18, outline=(*c1, 200), width=border_w
    )
    # Viền trong
    draw.rounded_rectangle(
        [border_w + 5, border_w + 5, W - border_w - 5, H - border_w - 5],
        radius=14, outline=(*c2, 120), width=2
    )

    # === 3. Avatar người join/out (bên trái) ===
    avatar_size = 140
    member_img = download_image(member_avatar_url)
    if not member_img:
        member_img = Image.new("RGBA", (avatar_size, avatar_size), (*c1, 255))
    member_avatar = make_circle_avatar(member_img, avatar_size)

    avatar_x = 45
    avatar_y = (H - avatar_size) // 2
    bg.paste(member_avatar, (avatar_x, avatar_y), member_avatar)

    # Viền avatar member
    cx = avatar_x + avatar_size // 2
    cy = avatar_y + avatar_size // 2
    draw_circle_border(draw, cx, cy, avatar_size // 2, c1, c2, width=3)

    # === 4. Avatar bot (bên phải) ===
    bot_img = download_image(bot_avatar_url)
    if not bot_img:
        bot_img = Image.new("RGBA", (avatar_size, avatar_size), (*c2, 255))
    bot_avatar = make_circle_avatar(bot_img, avatar_size)

    bot_x = W - avatar_size - 45
    bot_y = (H - avatar_size) // 2
    bg.paste(bot_avatar, (bot_x, bot_y), bot_avatar)

    # Viền avatar bot
    bcx = bot_x + avatar_size // 2
    bcy = bot_y + avatar_size // 2
    draw_circle_border(draw, bcx, bcy, avatar_size // 2, c2, c1, width=3)

    # === 5. Text ở giữa ===
    text_area_left = avatar_x + avatar_size + 30
    text_area_right = bot_x - 30
    text_max_w = text_area_right - text_area_left
    text_center_x = (text_area_left + text_area_right) // 2

    # Chọn lời chào/tạm biệt ngẫu nhiên
    if event_type == "JOIN":
        greeting = random.choice(WELCOME_TEXTS)
        event_label = "WELCOME"
        label_color = (0, 255, 180, 255)
    elif event_type == "LEAVE":
        greeting = random.choice(GOODBYE_TEXTS)
        event_label = "GOODBYE"
        label_color = (255, 100, 100, 255)
    else:
        greeting = random.choice(KICK_TEXTS)
        event_label = "KICKED"
        label_color = (255, 80, 80, 255)

    # Font
    font_label = get_font("BeVietnamPro-Bold.ttf", 26)
    font_name = get_font("BeVietnamPro-Bold.ttf", 22)
    font_greeting = get_font("3.ttf", 17)
    font_group = get_font("2.ttf", 14)

    # --- Event Label (WELCOME / GOODBYE / KICKED) ---
    label_bbox = draw.textbbox((0, 0), event_label, font=font_label)
    label_w = label_bbox[2] - label_bbox[0]
    label_x = text_center_x - label_w // 2
    label_y = H // 2 - 75

    # Shadow
    draw.text((label_x + 2, label_y + 2), event_label, font=font_label, fill=(0, 0, 0, 150))
    draw.text((label_x, label_y), event_label, font=font_label, fill=label_color)

    # --- Đường kẻ trang trí ---
    line_y = label_y + 35
    line_half = min(text_max_w // 2 - 10, 120)
    draw.line(
        [(text_center_x - line_half, line_y), (text_center_x + line_half, line_y)],
        fill=(*c2, 150), width=2
    )

    # --- Tên thành viên ---
    # Cắt tên nếu quá dài
    display_name = member_name
    name_bbox = draw.textbbox((0, 0), display_name, font=font_name)
    if (name_bbox[2] - name_bbox[0]) > text_max_w:
        while len(display_name) > 5:
            display_name = display_name[:-1]
            bb = draw.textbbox((0, 0), display_name + "...", font=font_name)
            if (bb[2] - bb[0]) <= text_max_w:
                display_name += "..."
                break

    name_bbox = draw.textbbox((0, 0), display_name, font=font_name)
    name_w = name_bbox[2] - name_bbox[0]
    name_x = text_center_x - name_w // 2
    name_y = line_y + 10

    draw.text((name_x + 1, name_y + 1), display_name, font=font_name, fill=(0, 0, 0, 120))
    draw.text((name_x, name_y), display_name, font=font_name, fill=(255, 255, 255, 255))

    # --- Lời chào/tạm biệt ---
    gr_bbox = draw.textbbox((0, 0), greeting, font=font_greeting)
    gr_w = gr_bbox[2] - gr_bbox[0]
    gr_x = text_center_x - gr_w // 2
    gr_y = name_y + 32

    draw.text((gr_x + 1, gr_y + 1), greeting, font=font_greeting, fill=(0, 0, 0, 100))
    draw.text((gr_x, gr_y), greeting, font=font_greeting, fill=(220, 220, 255, 255))

    # --- Tên nhóm (nhỏ, dưới cùng) ---
    grp_text = f"⌘ {group_name}"
    grp_bbox = draw.textbbox((0, 0), grp_text, font=font_group)
    grp_w = grp_bbox[2] - grp_bbox[0]
    grp_x = text_center_x - grp_w // 2
    grp_y = gr_y + 28

    draw.text((grp_x, grp_y), grp_text, font=font_group, fill=(180, 180, 200, 200))

    # === 6. Mũi tên kết nối (member → text ← bot) ===
    arrow_y = H // 2
    # Trái
    draw.line(
        [(avatar_x + avatar_size + 8, arrow_y), (text_area_left - 8, arrow_y)],
        fill=(*c1, 80), width=2
    )
    # Phải
    draw.line(
        [(text_area_right + 8, arrow_y), (bot_x - 8, arrow_y)],
        fill=(*c2, 80), width=2
    )

    # === 7. Timestamp nhỏ góc dưới ===
    time_str = datetime.now().strftime("%H:%M %d/%m/%Y")
    time_font = get_font("2.ttf", 11)
    draw.text((W - 155, H - 25), time_str, font=time_font, fill=(150, 150, 170, 150))

    # === Lưu ===
    os.makedirs(CACHE_DIR, exist_ok=True)
    out_path = os.path.join(CACHE_DIR, f"event_{random.randint(1000,9999)}.png")
    bg = bg.convert("RGB")
    bg.save(out_path, quality=95)
    return out_path


# ============ Build messages ============

def buildWelcomeMessage(self, groupName, joinMembers, sourceId=None, group_type_name="Nhóm"):
    member_list = ", ".join([m.get("dName") for m in joinMembers])

    if sourceId:
        adder_info = self.fetchUserInfo(sourceId)
        adder_name = (
            adder_info.get("changed_profiles", {})
            .get(sourceId, {})
            .get("displayName", "Không xác định")
        )

        if not any(sourceId == m.get("id") for m in joinMembers):
            return f"{groupName}\nChào Mừng {member_list}\nĐã Tham Gia {group_type_name}\nDuyệt Bởi {adder_name}"
        else:
            return f"{groupName}\nChào Mừng {member_list}\nĐã Tham Gia {group_type_name}\nThêm Bởi {adder_name}"

    return f"{groupName}\nChào Mừng {member_list}\nĐã Tham Gia {group_type_name}"


def buildLeaveMessage(self, groupName, updateMembers, eventType, sourceId=None, group_type_name="Nhóm"):
    name = updateMembers[0].get("dName")

    if eventType == GroupEventType.LEAVE:
        return f"Member Left The Group\n{name}\nVừa Rời Khỏi {group_type_name}\n{groupName}"

    if eventType == GroupEventType.REMOVE_MEMBER:
        remover_info = self.fetchUserInfo(sourceId)
        remover_name = (
            remover_info.get("changed_profiles", {})
            .get(sourceId, {})
            .get("displayName", "Không xác định")
        )
        return f"Kick Out Member\n{name}\nĐã Bị {remover_name} Kick Khỏi {group_type_name}\n{groupName}"

    return ""


def buildAdminMessage(self, eventData, eventType, group_type_name):
    groupName = eventData.get("groupName", "Nhóm")
    member = eventData.get("updateMembers", [])[0]
    member_name = member.get("dName")
    sourceId = eventData.get("sourceId")

    src_info = self.fetchUserInfo(sourceId)
    src_name = (
        src_info.get("changed_profiles", {})
        .get(sourceId, {})
        .get("displayName", "Không xác định")
    )

    if eventType == GroupEventType.ADD_ADMIN:
        return f"{groupName}\nQuản Trị Viên Mới\n{member_name}\nBổ nhiệm bởi {src_name}"

    if eventType == GroupEventType.REMOVE_ADMIN:
        return f"{groupName}\nGỡ Quyền Admin\n{member_name}\nBởi {src_name}"

    return ""


def get_bot_avatar(self):
    """Lấy avatar URL của bot đang chạy."""
    try:
        acc = self.fetchAccountInfo()
        if acc and acc.profile:
            return acc.profile.get("avatar", "")
    except Exception:
        pass
    return ""


def get_group_cover(self, groupId):
    """Lấy ảnh bìa nhóm."""
    try:
        ginfo = self.fetchGroupInfo(groupId)
        if ginfo and hasattr(ginfo, 'gridInfoMap') and groupId in ginfo.gridInfoMap:
            info = ginfo.gridInfoMap[groupId]
            # Thử lấy cover/avatar nhóm
            cover = info.get("cover", "") or info.get("avt", "") or info.get("avatar", "")
            return cover
    except Exception:
        pass
    return ""


def send_event_image(self, member_id, member_name, member_avatar, member_cover, groupId, groupName, event_type_str, text_msg, mention=False):
    """Tạo và gửi ảnh sự kiện."""
    try:
        bot_avatar = get_bot_avatar(self)
        group_cover = get_group_cover(self, groupId)

        img_path = create_event_image(
            member_name=member_name,
            member_avatar_url=member_avatar,
            member_cover_url=member_cover,
            bot_avatar_url=bot_avatar,
            group_name=groupName,
            group_cover_url=group_cover,
            event_type=event_type_str
        )

        if not img_path or not os.path.exists(img_path):
            print("⚠ Không thể tạo ảnh sự kiện")
            return

        if mention and member_id:
            self.sendLocalImage(
                img_path,
                thread_id=groupId,
                thread_type=ThreadType.GROUP,
                width=900,
                height=320,
                message=Message(
                    text=f"@{member_name}",
                    mention=Mention(member_id, length=len(f"@{member_name}"), offset=0)
                ),
                ttl=300000
            )
        else:
            self.sendLocalImage(
                img_path,
                thread_id=groupId,
                thread_type=ThreadType.GROUP,
                width=900,
                height=320,
                message=Message(text=text_msg),
                ttl=300000
            )

        # Xóa file tạm
        try:
            os.remove(img_path)
        except Exception:
            pass

    except Exception as e:
        print(f"⚠ Send Event Error: {e}")


def handleGroupEvent(self, eventData, eventType):
    groupId = eventData.get("groupId")
    if not groupId:
        return

    if groupId not in load_allowed_groups():
        return

    try:
        ginfo = self.fetchGroupInfo(groupId).gridInfoMap[groupId]
        group_type_name = "Cộng Đồng" if ginfo.get("type") == 2 else "Nhóm"
        groupName = eventData.get("groupName", "Group")
    except Exception:
        group_type_name = "Nhóm"
        groupName = eventData.get("groupName", "Group")

    if eventType == GroupEventType.JOIN:
        members = eventData.get("updateMembers", [])
        sourceId = eventData.get("sourceId")
        if not members:
            return

        text = buildWelcomeMessage(self, groupName, members, sourceId, group_type_name)

        for m in members:
            member_id = m.get("id", "")
            member_name = m.get("dName", "User")
            member_avatar = m.get("avatar", "")

            # Nếu không có avatar từ event, thử fetch
            member_cover = ""
            if member_id:
                try:
                    uinfo = self.fetchUserInfo(member_id)
                    profile = uinfo.get("changed_profiles", {}).get(member_id, {})
                    if not member_avatar:
                        member_avatar = profile.get("avatar", "")
                    member_cover = profile.get("coverUrl", "") or profile.get("cover", "")
                except Exception:
                    pass

            def _send(mid=member_id, mname=member_name, mavt=member_avatar, mcov=member_cover, txt=text):
                send_event_image(self, mid, mname, mavt, mcov, groupId, groupName, "JOIN", txt, mention=True)

            Thread(target=_send, daemon=True).start()

    elif eventType in {GroupEventType.LEAVE, GroupEventType.REMOVE_MEMBER}:
        members = eventData.get("updateMembers", [])
        sourceId = eventData.get("sourceId")
        if not members:
            return

        evt_str = "LEAVE" if eventType == GroupEventType.LEAVE else "KICK"
        text = buildLeaveMessage(self, groupName, members, eventType, sourceId, group_type_name)

        m = members[0]
        member_id = m.get("id", "")
        member_name = m.get("dName", "User")
        member_avatar = m.get("avatar", "")
        member_cover = ""

        if member_id:
            try:
                uinfo = self.fetchUserInfo(member_id)
                profile = uinfo.get("changed_profiles", {}).get(member_id, {})
                if not member_avatar:
                    member_avatar = profile.get("avatar", "")
                member_cover = profile.get("coverUrl", "") or profile.get("cover", "")
            except Exception:
                pass

        def _send():
            send_event_image(self, member_id, member_name, member_avatar, member_cover, groupId, groupName, evt_str, text, mention=False)

        Thread(target=_send, daemon=True).start()

    elif eventType in {GroupEventType.ADD_ADMIN, GroupEventType.REMOVE_ADMIN}:
        text = buildAdminMessage(self, eventData, eventType, group_type_name)
        member = eventData.get("updateMembers", [])[0]
        member_id = member.get("id", "")
        member_name = member.get("dName", "User")
        member_avatar = member.get("avatar", "")

        if not member_avatar and member_id:
            try:
                uinfo = self.fetchUserInfo(member_id)
                profile = uinfo.get("changed_profiles", {}).get(member_id, {})
                member_avatar = profile.get("avatar", "")
            except Exception:
                pass

        def _send():
            send_event_image(self, member_id, member_name, member_avatar, groupId, groupName, "JOIN", text, mention=True)

        Thread(target=_send, daemon=True).start()