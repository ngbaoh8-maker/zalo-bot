import os
import json
import time
import tempfile
import logging
import concurrent.futures
from io import BytesIO
from datetime import datetime

import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from zlapi.models import Message
from config import PREFIX

logger = logging.getLogger(__name__)

des = {
    "version": "2.1.0",
    "credits": "Tân Xuân Hoàng",
    "description": "bot on/off/on all/off all/list",
    "power": "Admin"
}

BOT_NAME = "Tân Xuân Hoàng Dz"

DATA_DIR = "data"
SETTINGS_FILE = os.path.join(DATA_DIR, "bot_status.json")
os.makedirs(DATA_DIR, exist_ok=True)

FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
EMOJI_FONT_PATH = "modules/cache/font/NotoEmoji-Bold.ttf"


def _font(path, size):
    try:
        if path and os.path.exists(path):
            return ImageFont.truetype(path, size)
    except Exception:
        pass
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


def get_font(size):
    return _font(FONT_PATH, size)


def get_emoji_font(size):
    if EMOJI_FONT_PATH and os.path.exists(EMOJI_FONT_PATH):
        return _font(EMOJI_FONT_PATH, size)
    return get_font(size)


IMG_W = 1600
IMG_H = 860

BG1 = (12, 16, 24)
BG2 = (18, 26, 38)
GRID = (130, 160, 210, 26)

PANEL = (18, 22, 30, 185)
PANEL2 = (16, 20, 28, 170)
STROKE = (130, 150, 180, 70)

TXT = (240, 245, 250, 235)
MUTED = (140, 150, 165, 210)

ACC_ON = (80, 220, 170)
ACC_OFF = (235, 95, 105)
ACC_ALL = (130, 200, 255)

CACHE_DIR = "modules/cache/bot_control"
os.makedirs(CACHE_DIR, exist_ok=True)


def _rounded(draw, box, r, fill=None, outline=None, width=2):
    draw.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def _glass_panel(base, box, r=26, fill=PANEL, stroke=STROKE, glow=(140, 160, 190, 70)):
    x0, y0, x1, y1 = map(int, box)

    crop = base.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(7))
    base.paste(crop, (x0, y0))

    glow_layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_layer, "RGBA")
    _rounded(gd, (x0, y0, x1, y1), r, fill=None, outline=glow, width=10)
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(12))
    base.alpha_composite(glow_layer)

    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay, "RGBA")
    _rounded(od, (x0, y0, x1, y1), r, fill=fill, outline=stroke, width=2)
    base.alpha_composite(overlay)


def _draw_bg(w, h):
    bg = Image.new("RGBA", (w, h), BG1 + (255,))
    d = ImageDraw.Draw(bg, "RGBA")

    for y in range(h):
        t = y / max(1, h - 1)
        r = int(BG1[0] * (1 - t) + BG2[0] * t)
        g = int(BG1[1] * (1 - t) + BG2[1] * t)
        b = int(BG1[2] * (1 - t) + BG2[2] * t)
        d.line((0, y, w, y), fill=(r, g, b, 255))

    grid = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid, "RGBA")
    step = 56
    for x in range(0, w, step):
        gd.line((x, 0, x, h), fill=GRID, width=1)
    for y in range(0, h, step):
        gd.line((0, y, w, y), fill=GRID, width=1)
    bg.alpha_composite(grid)

    vign = Image.new("L", (w, h), 0)
    vd = ImageDraw.Draw(vign)
    vd.ellipse((-w * 0.2, -h * 0.5, w * 1.2, h * 1.4), fill=235)
    vign = vign.filter(ImageFilter.GaussianBlur(int(min(w, h) * 0.08)))
    dark = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    bg = Image.composite(bg, dark, vign).convert("RGBA")
    return bg


def _fit_text(draw, text, font, max_w):
    if not text:
        return ""
    if draw.textlength(text, font=font) <= max_w:
        return text
    t = text
    while t and draw.textlength(t + "...", font=font) > max_w:
        t = t[:-1]
    return (t + "...") if t else "..."


def _save_rgb(img):
    p = os.path.join(CACHE_DIR, f"bot_control_{int(time.time() * 1000)}.jpg")
    img.convert("RGB").save(p, "JPEG", quality=95, optimize=True)
    return p


def _circle_icon(base, cx, cy, r, accent_rgb, icon="🤖"):
    draw = ImageDraw.Draw(base, "RGBA")
    glow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow, "RGBA")
    gd.ellipse(
        (cx - r - 6, cy - r - 6, cx + r + 6, cy + r + 6),
        outline=(accent_rgb[0], accent_rgb[1], accent_rgb[2], 95),
        width=10,
    )
    glow = glow.filter(ImageFilter.GaussianBlur(10))
    base.alpha_composite(glow)

    draw.ellipse(
        (cx - r, cy - r, cx + r, cy + r),
        fill=(18, 22, 30, 200),
        outline=(accent_rgb[0], accent_rgb[1], accent_rgb[2], 210),
        width=5,
    )

    f = get_emoji_font(int(r * 1.1))
    iw = draw.textlength(icon, font=f)
    draw.text((cx - iw / 2, cy - r * 0.65), icon, font=f, fill=(245, 250, 255, 230))


def _pill(draw, x0, y0, x1, y1, label, accent_rgb):
    _rounded(
        draw,
        (x0, y0, x1, y1),
        18,
        fill=(14, 18, 26, 210),
        outline=(accent_rgb[0], accent_rgb[1], accent_rgb[2], 200),
        width=2,
    )
    f = get_font(22)
    draw.text(
        ((x0 + x1) / 2, (y0 + y1) / 2 + 1),
        label,
        font=f,
        fill=(accent_rgb[0], accent_rgb[1], accent_rgb[2], 235),
        anchor="mm",
    )


def build_bot_control_image(status, actor_name, group_name, group_id, note_text="", all_count=0):
    if status == "ON":
        accent = ACC_ON
        pill = "ON"
        title_big = "BẬT • Nhóm hiện tại"
        subtitle = "Bot đang bật"
    elif status == "OFF":
        accent = ACC_OFF
        pill = "OFF"
        title_big = "TẮT • Nhóm hiện tại"
        subtitle = "Bot đang tắt"
    elif status == "ON_ALL":
        accent = ACC_ALL
        pill = "ON ALL"
        title_big = "BẬT • Tất cả nhóm"
        subtitle = f"Đã bật bot trong {all_count} nhóm"
    else:
        accent = ACC_OFF
        pill = "OFF ALL"
        title_big = "TẮT • Tất cả nhóm"
        subtitle = "Đã tắt bot trong tất cả nhóm"

    base = _draw_bg(IMG_W, IMG_H)
    draw = ImageDraw.Draw(base, "RGBA")

    outer = (40, 40, IMG_W - 40, IMG_H - 40)
    _glass_panel(base, outer, r=34, fill=PANEL, stroke=STROKE, glow=(accent[0], accent[1], accent[2], 60))

    header = (70, 70, IMG_W - 70, 210)
    _glass_panel(base, header, r=28, fill=PANEL2, stroke=(140, 160, 190, 55), glow=(accent[0], accent[1], accent[2], 45))
    _circle_icon(base, 120, 140, 44, accent, icon="🤖")

    f_title = get_font(54)
    f_sub = get_font(24)
    draw.text((200, 112), "BOT CONTROL", font=f_title, fill=TXT)
    now = datetime.now().strftime("%d/%m/%Y • %H:%M:%S")
    draw.text((200, 166), now, font=f_sub, fill=(170, 180, 195, 220))
    _pill(draw, IMG_W - 330, 124, IMG_W - 110, 186, pill, accent)

    content = (70, 240, IMG_W - 70, IMG_H - 120)
    _glass_panel(base, content, r=28, fill=PANEL2, stroke=(140, 160, 190, 55), glow=(accent[0], accent[1], accent[2], 45))

    cx0, cy0, cx1, cy1 = content
    left_pad = 140
    top_pad = 36

    f_big = get_font(58)
    f_mid = get_font(28)
    f_line = get_font(30)
    f_note = get_font(24)

    title_y = cy0 + top_pad
    draw.text((cx0 + left_pad, title_y), title_big, font=f_big, fill=TXT)

    title_h = f_big.getbbox("Ag")[3] - f_big.getbbox("Ag")[1]
    sub_y = title_y + title_h + 10
    draw.text((cx0 + left_pad, sub_y), subtitle, font=f_mid, fill=(accent[0], accent[1], accent[2], 220))

    clean_group_name = (group_name or "Không xác định").strip()
    group_id = str(group_id or "N/A").strip()

    x_icon = cx0 + left_pad
    x_label = x_icon + 50
    x_value = cx0 + 520
    y = sub_y + 78

    def info_row(icon, label, value, value_color):
        nonlocal y
        draw.text((x_icon, y), icon, font=get_emoji_font(26), fill=(235, 240, 245, 230))
        draw.text((x_label, y), label, font=f_line, fill=(175, 185, 200, 220))

        max_w = (cx1 - 60) - x_value
        value = _fit_text(draw, str(value), f_line, max_w)
        draw.text((x_value, y), value, font=f_line, fill=value_color)
        y += 60

    info_row("👤", "Người thao tác:", actor_name or "Không xác định", (accent[0], accent[1], accent[2], 230))
    info_row("👥", "Nhóm:", clean_group_name, (accent[0], accent[1], accent[2], 230))
    if status in ("ON", "OFF"):
        info_row("🆔", "Group ID:", group_id, (accent[0], accent[1], accent[2], 230))

    st_txt = "Đang hoạt động" if status in ("ON", "ON_ALL") else "Đang ngủ"
    info_row("📡", "Trạng thái:", st_txt, (accent[0], accent[1], accent[2], 230))

    if note_text:
        note_h = f_note.getbbox("Ag")[3] - f_note.getbbox("Ag")[1]
        note_y = y + 12
        bottom_limit = cy1 - 26 - note_h
        if note_y > bottom_limit:
            note_y = bottom_limit
        draw.text((cx0 + left_pad, note_y), note_text, font=f_note, fill=(175, 185, 200, 220))

    footer_w, footer_h = 560, 82
    fx1, fy1 = IMG_W - 90, IMG_H - 95
    fx0, fy0 = fx1 - footer_w, fy1 - footer_h
    _glass_panel(
        base,
        (fx0, fy0, fx1, fy1),
        r=22,
        fill=(15, 18, 26, 165),
        stroke=(145, 160, 180, 60),
        glow=(accent[0], accent[1], accent[2], 40),
    )
    draw.text((fx0 + 22, fy0 + 14), f"Powered by {BOT_NAME}", font=get_font(22), fill=(200, 210, 225, 205))
    draw.text((fx0 + 22, fy0 + 46), f"{PREFIX}bot / {PREFIX}aibot", font=get_font(20), fill=(160, 170, 185, 215))

    return base.convert("RGB")


def get_user_name(client, uid):
    try:
        user_info = client.fetchUserInfo(uid)
        author_info = user_info.changed_profiles.get(str(uid), {}) if user_info and user_info.changed_profiles else {}
        return author_info.get("zaloName", "Không xác định")
    except Exception:
        return "Không xác định"


def get_group_name_only(client, gid):
    try:
        gi = client.fetchGroupInfo(gid)
        info = {}
        if hasattr(gi, "gridInfoMap") and gi.gridInfoMap:
            info = gi.gridInfoMap.get(str(gid), {}) or {}
        name = info.get("name") or info.get("groupName") or "Nhóm"
        return str(name).strip()
    except Exception:
        return "Nhóm"


BG_COLOR = (29, 32, 41)
CARD_COLOR = (44, 48, 61)
SHADOW_COLOR = (18, 20, 26, 128)
TEXT_COLOR = (230, 235, 240)
HEADER_COLOR = (130, 230, 255)
ID_COLOR = (150, 155, 170)
ICON_COLOR = (255, 255, 255)


def create_circular_avatar(img, size):
    img = img.resize(size, Image.Resampling.LANCZOS)
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + size, fill=255)
    output = Image.new("RGBA", size, (0, 0, 0, 0))
    output.paste(img.convert("RGBA"), (0, 0), mask)
    return output


def fetch_and_process_avatar(group_info, avatar_size):
    group_id = group_info[0]
    avatar_url = group_info[2]

    try:
        if avatar_url:
            response = requests.get(avatar_url, timeout=5)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content)).convert("RGB")
            return group_id, create_circular_avatar(img, (avatar_size, avatar_size))
    except Exception:
        pass

    placeholder = Image.new("RGB", (avatar_size, avatar_size), CARD_COLOR)
    try:
        placeholder_font = ImageFont.truetype(EMOJI_FONT_PATH, int(avatar_size * 0.6)) if EMOJI_FONT_PATH and os.path.exists(EMOJI_FONT_PATH) else get_emoji_font(int(avatar_size * 0.6))
        draw = ImageDraw.Draw(placeholder)
        icon = "👥"
        bbox = draw.textbbox((0, 0), icon, font=placeholder_font)
        draw.text(
            ((avatar_size - (bbox[2] - bbox[0])) / 2, (avatar_size - (bbox[3] - bbox[1])) / 2 - 10),
            icon,
            font=placeholder_font,
            fill=ICON_COLOR
        )
    except Exception:
        pass
    return group_id, create_circular_avatar(placeholder, (avatar_size, avatar_size))


def create_group_list_image(group_list_info, page=1, items_per_page=10):
    paginated_list = group_list_info[(page - 1) * items_per_page: page * items_per_page]
    total_pages = (len(group_list_info) + items_per_page - 1) // items_per_page
    if not paginated_list:
        return None

    try:
        if FONT_PATH and os.path.exists(FONT_PATH):
            header_font = ImageFont.truetype(FONT_PATH, 50)
            name_font = ImageFont.truetype(FONT_PATH, 38)
            id_font = ImageFont.truetype(FONT_PATH, 28)
            footer_font = ImageFont.truetype(FONT_PATH, 28)
        else:
            raise IOError()
    except Exception:
        header_font = ImageFont.load_default()
        name_font = ImageFont.load_default()
        id_font = ImageFont.load_default()
        footer_font = ImageFont.load_default()

    avatar_size = 90
    avatars = {}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_avatar = {executor.submit(fetch_and_process_avatar, group_info, avatar_size): group_info for group_info in paginated_list}
        for future in concurrent.futures.as_completed(future_to_avatar):
            group_id, avatar_img = future.result()
            avatars[group_id] = avatar_img

    img_width = 1280
    padding = 60
    header_height = 150
    card_height = 120
    card_spacing = 20
    footer_height = 90
    content_height = len(paginated_list) * (card_height + card_spacing)
    img_height = header_height + content_height + footer_height

    image = Image.new("RGB", (img_width, img_height), BG_COLOR)
    draw = ImageDraw.Draw(image, "RGBA")

    header_text = "BOT ĐANG HOẠT ĐỘNG TRONG CÁC NHÓM"
    bbox = draw.textbbox((0, 0), header_text, font=header_font)
    draw.text(((img_width - (bbox[2] - bbox[0])) / 2, padding), header_text, font=header_font, fill=HEADER_COLOR)

    current_y = header_height
    for i, (group_id, group_name, avatar_url) in enumerate(paginated_list):
        draw.rounded_rectangle(
            (padding + 6, current_y + 6, img_width - padding + 6, current_y + card_height + 6),
            radius=20,
            fill=SHADOW_COLOR
        )
        draw.rounded_rectangle(
            (padding, current_y, img_width - padding, current_y + card_height),
            radius=20,
            fill=CARD_COLOR
        )

        avatar_img = avatars.get(group_id)
        if avatar_img:
            y_avatar = current_y + (card_height - avatar_size) // 2
            image.paste(avatar_img, (padding + 20, y_avatar), avatar_img)

        text_x = padding + avatar_size + 45
        max_name_width = img_width - text_x - padding - 20
        gname = group_name
        if draw.textlength(gname, font=name_font) > max_name_width:
            while draw.textlength(gname + "...", font=name_font) > max_name_width and len(gname) > 0:
                gname = gname[:-1]
            gname += "..."
        draw.text((text_x, current_y + 25), gname, font=name_font, fill=TEXT_COLOR)
        draw.text((text_x, current_y + 75), f"ID: {group_id}", font=id_font, fill=ID_COLOR)

        current_y += card_height + card_spacing

    footer_text = f"Trang {page}/{total_pages}  •  Tổng cộng: {len(group_list_info)} nhóm"
    bbox = draw.textbbox((0, 0), footer_text, font=footer_font)
    draw.text(((img_width - (bbox[2] - bbox[0])) / 2, img_height - footer_height + 30), footer_text, font=footer_font, fill=HEADER_COLOR)

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tf:
        image.save(tf.name, "JPEG", quality=95, optimize=True)
        return tf.name, image.width, image.height


class BotStatusHandler:
    def __init__(self, client):
        self.client = client
        self.bot_enabled_groups = self.load_settings()

    def load_settings(self):
        try:
            if not os.path.exists(SETTINGS_FILE):
                return []
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return [str(x) for x in data]
            return []
        except Exception:
            return []

    def save_settings(self):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(sorted(list(set(self.bot_enabled_groups))), f, ensure_ascii=False, indent=2)

    def is_enabled(self, tid):
        return str(tid) in set(self.bot_enabled_groups)

    def is_bot_enabled(self, thread_id=None):
        try:
            if thread_id is None:
                return True
            return self.is_enabled(thread_id)
        except Exception:
            return True

    def set_bot_enabled(self, thread_id, enabled: bool):
        try:
            tid = str(thread_id)
            if enabled:
                if tid not in self.bot_enabled_groups:
                    self.bot_enabled_groups.append(tid)
            else:
                self.bot_enabled_groups = [x for x in self.bot_enabled_groups if str(x) != tid]
            self.save_settings()
            return True
        except Exception:
            return False

    def _admin_ok(self, author_id):
        admin_list = getattr(self.client, "ADMIN", [])
        if isinstance(admin_list, (str, int)):
            admin_list = [str(admin_list)]
        elif not isinstance(admin_list, (list, tuple, set)):
            admin_list = [str(admin_list)]
        admin_set = set(str(x) for x in admin_list)
        return str(author_id) in admin_set

    def handle_bot_command(self, message_text, message_object, thread_id, thread_type, author_id):
        if not self._admin_ok(author_id):
            self.client.replyMessage(
                Message(text="⚠️ Chỉ ADMIN mới dùng được lệnh bot on/off."),
                message_object,
                thread_id,
                thread_type,
                ttl=60000,
            )
            return

        parts = (message_text or "").strip().split()
        args = [p.lower() for p in parts[1:]] if len(parts) > 1 else []
        if not args:
            self.client.replyMessage(
                Message(text=f"📌 Dùng: {PREFIX}bot on/off/on all/off all/list [page]"),
                message_object,
                thread_id,
                thread_type,
                ttl=60000,
            )
            return

        action = args[0]
        is_all = len(args) >= 2 and args[1] == "all"

        actor_name = get_user_name(self.client, author_id)
        group_name = get_group_name_only(self.client, thread_id)
        group_id = str(thread_id)

        if action == "list":
            page = 1
            if len(args) >= 2 and args[1].isdigit():
                page = int(args[1])
            if not self.bot_enabled_groups:
                self.client.replyMessage(
                    Message(text="❌ Hiện không có nhóm nào đang bật bot."),
                    message_object,
                    thread_id,
                    thread_type,
                    ttl=60000,
                )
                return

            group_list = []
            for gid in self.bot_enabled_groups:
                gname = get_group_name_only(self.client, gid)
                group_list.append((str(gid), gname, None))

            result = create_group_list_image(group_list, page=page, items_per_page=10)
            if not result:
                self.client.replyMessage(
                    Message(text=f"❌ Không có dữ liệu ở trang {page}."),
                    message_object,
                    thread_id,
                    thread_type,
                    ttl=60000,
                )
                return

            path, w, h = result
            try:
                self.client.sendLocalImage(path, thread_id=thread_id, thread_type=thread_type, width=w, height=h, ttl=120000)
            finally:
                try:
                    os.remove(path)
                except Exception:
                    pass
            return

        if action == "on" and is_all:
            all_ids = []
            try:
                g = self.client.fetchAllGroups()
                if hasattr(g, "gridVerMap") and g.gridVerMap:
                    all_ids = [str(x) for x in g.gridVerMap.keys()]
            except Exception:
                all_ids = []

            if not all_ids:
                self.client.replyMessage(
                    Message(text="❌ Không lấy được danh sách nhóm để ON ALL."),
                    message_object,
                    thread_id,
                    thread_type,
                    ttl=60000,
                )
                return

            enabled = set(self.bot_enabled_groups)
            all_set = set(all_ids)

            if all_set.issubset(enabled):
                img = build_bot_control_image(
                    "ON_ALL",
                    actor_name,
                    "Tất cả nhóm",
                    "N/A",
                    note_text="Bot đã ON ALL trước đó rồi.",
                    all_count=len(all_ids),
                )
            else:
                enabled.update(all_set)
                self.bot_enabled_groups = list(enabled)
                self.save_settings()
                img = build_bot_control_image(
                    "ON_ALL",
                    actor_name,
                    "Tất cả nhóm",
                    "N/A",
                    note_text=f"Đã ON ALL {len(all_ids)} nhóm.",
                    all_count=len(all_ids),
                )

            p = _save_rgb(img)
            try:
                self.client.sendLocalImage(p, thread_id=thread_id, thread_type=thread_type, width=img.size[0], height=img.size[1], ttl=120000)
            finally:
                try:
                    os.remove(p)
                except Exception:
                    pass
            return

        if action == "off" and is_all:
            if not self.bot_enabled_groups:
                img = build_bot_control_image("OFF_ALL", actor_name, "Tất cả nhóm", "N/A", note_text="Bot đã OFF ALL trước đó rồi.")
            else:
                self.bot_enabled_groups = []
                self.save_settings()
                img = build_bot_control_image("OFF_ALL", actor_name, "Tất cả nhóm", "N/A", note_text="Đã OFF ALL tất cả nhóm.")

            p = _save_rgb(img)
            try:
                self.client.sendLocalImage(p, thread_id=thread_id, thread_type=thread_type, width=img.size[0], height=img.size[1], ttl=120000)
            finally:
                try:
                    os.remove(p)
                except Exception:
                    pass
            return

        if action == "on":
            if self.is_enabled(thread_id):
                img = build_bot_control_image("ON", actor_name, group_name, group_id, note_text="Bot đã ON trước đó rồi.")
            else:
                self.bot_enabled_groups.append(str(thread_id))
                self.save_settings()
                img = build_bot_control_image("ON", actor_name, group_name, group_id, note_text="Đã bật bot trong nhóm này.")

            p = _save_rgb(img)
            try:
                self.client.sendLocalImage(p, thread_id=thread_id, thread_type=thread_type, width=img.size[0], height=img.size[1], ttl=12000)
            finally:
                try:
                    os.remove(p)
                except Exception:
                    pass
            return

        if action == "off":
            if not self.is_enabled(thread_id):
                img = build_bot_control_image("OFF", actor_name, group_name, group_id, note_text="Bot đã OFF trước đó rồi.")
            else:
                self.bot_enabled_groups = [x for x in self.bot_enabled_groups if str(x) != str(thread_id)]
                self.save_settings()
                img = build_bot_control_image("OFF", actor_name, group_name, group_id, note_text="Đã tắt bot trong nhóm này.")

            p = _save_rgb(img)
            try:
                self.client.sendLocalImage(p, thread_id=thread_id, thread_type=thread_type, width=img.size[0], height=img.size[1], ttl=12000)
            finally:
                try:
                    os.remove(p)
                except Exception:
                    pass
            return

        self.client.replyMessage(
            Message(text=f"❓ Lệnh không hợp lệ. Dùng: {PREFIX}bot on/off/on all/off all/list [page]"),
            message_object,
            thread_id,
            thread_type,
            ttl=60000,
        )


_handler_pool = {}


def _get_handler(client):
    key = id(client)
    if key not in _handler_pool:
        _handler_pool[key] = BotStatusHandler(client)
    return _handler_pool[key]


def _bot_command(message, message_object, thread_id, thread_type, author_id, client):
    return _get_handler(client).handle_bot_command(message, message_object, thread_id, thread_type, author_id)


def PTA():
    return {"bot": _bot_command}