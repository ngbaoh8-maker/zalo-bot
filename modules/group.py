from zlapi.models import Message
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from datetime import datetime
import io
import requests
import os
import random
import tempfile

des = {
    'version': "1.0.2",
    'credits': "ngbao",
    'description': "Infographic hiển thị thông tin nhóm (nền/font từ cache, toggle realtime)",
    'power': "Thành Viên"
}

# ---------------- Config theo user ----------------
FONT_TITLE_FILE = "BeVietnamPro-Bold.ttf"
FONT_INFO_FILE = "BeVietnamPro-Medium.ttf"
# font_setting: nếu không có BeVietnamPro-Regular thì lấy file ttf đầu tiên
SIZE_TITLE = 52
SIZE_INFO = 32
SIZE_SETTING = 26

CANVAS_W = 1200
CANVAS_H = 720

# ---------------- Helpers ----------------
def fetch_image(url, timeout=30):
    if not url:
        return None
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return Image.open(io.BytesIO(r.content)).convert("RGBA")
    except Exception as e:
        print("fetch_image error:", e)
        return None

def choose_font_file(preferred_name):
    font_dir = "modules/cache/font"
    if not os.path.isdir(font_dir):
        return None
    # try preferred
    pref_path = os.path.join(font_dir, preferred_name)
    if os.path.isfile(pref_path):
        return pref_path
    # else return first ttf in dir
    for f in os.listdir(font_dir):
        if f.lower().endswith(".ttf"):
            return os.path.join(font_dir, f)
    return None

def load_font_by_name(filename, size):
    # filename can be None or path
    if filename:
        try:
            return ImageFont.truetype(filename, size)
        except Exception as e:
            print("load_font error:", e)
    return ImageFont.load_default()

def load_background():
    bg_dir = "modules/cache/backgrounds"
    if not os.path.isdir(bg_dir):
        return Image.new("RGBA", (CANVAS_W, CANVAS_H), (40, 120, 120, 255))
    files = [f for f in os.listdir(bg_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
    if not files:
        return Image.new("RGBA", (CANVAS_W, CANVAS_H), (40, 120, 120, 255))
    path = os.path.join(bg_dir, random.choice(files))
    try:
        img = Image.open(path).convert("RGBA")
        # resize to canvas while keeping aspect (center crop/fit)
        img = img.resize((CANVAS_W, CANVAS_H))
        return img
    except Exception as e:
        print("load_background error:", e)
        return Image.new("RGBA", (CANVAS_W, CANVAS_H), (40, 120, 120, 255))

def rounded_box(draw, xy, radius, fill, outline=None, outline_width=2):
    # Pillow >=5 supports rounded_rectangle
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=outline_width)

def draw_text_wrapped(draw, text, x, y, font, max_width, line_spacing=6, fill=(255,255,255)):
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        test = (cur + " " + w).strip()
        bbox = draw.textbbox((0,0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        h = draw.textbbox((0,0), line, font=font)[3] - draw.textbbox((0,0), line, font=font)[1]
        y += h + line_spacing
    return y

def draw_toggle(draw, top_left, size, on):
    # size = (width, height)
    x, y = top_left
    w, h = size
    radius = h // 2
    track_fill_on = (61, 193, 114, 255)   # green
    track_fill_off = (130, 130, 130, 255) # gray
    track_outline = (80, 80, 80, 160)
    draw.rounded_rectangle([x, y, x+w, y+h], radius=radius, fill=track_fill_on if on else track_fill_off, outline=track_outline)
    # thumb
    thumb_r = h - 6
    if on:
        cx = x + w - radius
    else:
        cx = x + radius
    cy = y + h//2
    # thumb shadow
    shadow = Image.new("RGBA", (thumb_r+6, thumb_r+6), (0,0,0,0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse([3,3,thumb_r+3,thumb_r+3], fill=(0,0,0,100))
    # Paste shadow by returning it to main image (we don't have direct main image here, so draw a muted ellipse underneath)
    draw.ellipse([cx - thumb_r/2, cy - thumb_r/2, cx + thumb_r/2, cy + thumb_r/2], fill=(255,255,255,255))
    return

# ---------------- Main handler ----------------
def handle_infographic_small(message, message_object, thread_id, thread_type, author_id, client):
    try:
        # fetch group info
        group = client.fetchGroupInfo(thread_id).gridInfoMap.get(thread_id)
        if not group:
            client.replyMessage(Message(text="Không tìm thấy thông tin nhóm!"), message_object, thread_id, thread_type)
            return

        # prepare canvas
        canvas = load_background().copy()
        draw = ImageDraw.Draw(canvas, "RGBA")

        # load fonts
        font_dir = "modules/cache/font"
        title_path = choose_font_file(FONT_TITLE_FILE)
        info_path = choose_font_file(FONT_INFO_FILE)
        # For setting font, prefer regular; else fallback to any ttf
        setting_candidate = choose_font_file("BeVietnamPro-Regular.ttf")
        if not setting_candidate:
            setting_candidate = None  # choose_font_file will pick first if given name not found; but we want to allow None fallback
        font_title = load_font_by_name(title_path, SIZE_TITLE)
        font_info = load_font_by_name(info_path, SIZE_INFO)
        font_setting = load_font_by_name(setting_candidate or title_path or info_path, SIZE_SETTING)

        padding = 30

        # Draw header title (with slight shadow)
        group_name = group.name or "Không tên"
        txt_x = 220
        txt_y = 70
        # shadow
        draw.text((txt_x+2, txt_y+4), group_name, font=font_title, fill=(0,0,0,120))
        draw.text((txt_x, txt_y), group_name, font=font_title, fill=(120,35,210,255))  # purple-ish

        # Draw QR code if possible (use qrcode library if installed)
        try:
            import qrcode
            qr_data = f"group:{getattr(group, 'groupId', '')}"
            qr = qrcode.QRCode(box_size=6, border=1)
            qr.add_data(qr_data)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
            qr_w = 160
            qr_img = qr_img.resize((qr_w, qr_w))
            canvas.paste(qr_img, (CANVAS_W - qr_w - padding, padding))
        except Exception:
            pass  # no qrcode lib -> skip

        # Draw avatar (circular) with white border
        avatar_url = getattr(group, "fullAvt", None)
        avatar_img = fetch_image(avatar_url)
        avatar_size = 160
        av_x = padding
        av_y = 40
        if avatar_img:
            avatar_img = avatar_img.resize((avatar_size, avatar_size)).convert("RGBA")
            # create mask
            mask = Image.new("L", (avatar_size, avatar_size), 0)
            md = ImageDraw.Draw(mask)
            md.ellipse((0,0,avatar_size,avatar_size), fill=255)
            # white border circle beneath
            border_img = Image.new("RGBA", (avatar_size+10, avatar_size+10), (255,255,255,0))
            bd = ImageDraw.Draw(border_img)
            bd.ellipse((0,0,avatar_size+10,avatar_size+10), fill=(255,255,255,200))
            canvas.paste(border_img, (av_x-5, av_y-5), border_img)
            canvas.paste(avatar_img, (av_x, av_y), mask)

        # Start writing info boxes
        box_x = 200
        box_w = CANVAS_W - box_x - padding
        current_y = 150

        # small helper to draw semi-transparent black box with white border
        def draw_info_box(x, y, w, h, radius=18):
            # fill black transparent, outline white translucent
            rounded_box(draw, [x, y, x+w, y+h], radius, fill=(0,0,0,150), outline=(255,255,255,180), outline_width=2)

        # Box for ID (small)
        id_text = f"ID: {getattr(group, 'groupId', 'None')}"
        # compute height for one-line box
        bbox = draw.textbbox((0,0), id_text, font=font_info)
        line_h = bbox[3] - bbox[1] + 18
        draw_info_box(box_x, current_y, 520, line_h, radius=14)
        draw.text((box_x + 20, current_y + 8), id_text, font=font_info, fill=(255,255,255,255))
        current_y += line_h + 12

        # Box for creator / desc (medium)
        creator_name = "Không xác định"
        try:
            userinfo = client.fetchUserInfo(group.creatorId)
            creator_name = userinfo.changed_profiles[group.creatorId].zaloName
        except Exception:
            creator_name = "Tài khoản bị khóa" if getattr(group, "creatorId", None) is None else "Không xác định"

        creator_text = f"Trưởng nhóm: {creator_name}"
        draw_info_box(box_x, current_y, 740, line_h+8, radius=14)
        draw.text((box_x + 20, current_y + 8), creator_text, font=font_info, fill=(255,255,255,255))
        current_y += line_h + 18

        # Large info box for description / create time / global id
        large_box_h = 120
        draw_info_box(box_x, current_y, box_w, large_box_h, radius=22)
        inner_x = box_x + 30
        inner_y = current_y + 14
        desc = getattr(group, "desc", "") or "Không có mô tả"
        # wrapped desc (one line or two)
        inner_y = draw_text_wrapped(draw, f"Mô tả: {desc}", inner_x, inner_y, font_info, max_width=box_w-60, line_spacing=6, fill=(255,255,255,230))
        # created time
        try:
            ct = datetime.fromtimestamp(group.createdTime/1000).strftime("%H:%M %d/%m/%Y")
        except:
            ct = "Không xác định"
        draw.text((inner_x, inner_y+6), f"Thời gian tạo: {ct}", font=font_info, fill=(255,255,255,255))
        draw.text((inner_x, inner_y+46), f"Global ID: {getattr(group, 'globalId', 'None')}", font=font_info, fill=(255,255,255,255))
        current_y += large_box_h + 28

        # Settings area: draw grid of boxes with toggle on right
        # keys mapping to labels (you can extend)
        key_translation = {
            'blockName': 'Thay đổi tên, ảnh box',
            'signAdminMsg': 'Ghim tin admin box',
            'addMemberOnly': 'Chỉ QTV thêm thành viên',
            'setTopicOnly': 'Tạo ghi chú',
            'enableMsgHistory': 'Xem lịch sử tin',
            'lockCreatePost': 'Tạo ghi chú, nhắc hẹn',
            'lockCreatePoll': 'Tạo bình chọn',
            'joinAppr': 'Duyệt thành viên',
            'bannFeature': 'Tính năng cấm',
            'dirtyMedia': 'Nội dung nhạy cảm',
            'banDuration': 'Thời gian cấm',
            'lockSendMsg': 'Khóa gửi tin nhắn',
            'lockViewMember': 'Khóa xem thành viên'
        }
        setting = getattr(group, "setting", {}) or {}

        # layout: two columns
        col1_x = box_x
        col2_x = box_x + (box_w//2) + 20
        row_h = 64
        gap_y = 14
        toggle_w = 84
        toggle_h = 36

        # iterate settings in deterministic order
        keys = list(key_translation.keys())
        # We'll draw rows pairwise
        r_y = current_y
        for i, key in enumerate(keys):
            col = 1 if (i % 2 == 0) else 2
            idx = i // 2  # row index (integer division rounding down)
            y = current_y + idx * (row_h + gap_y)
            x = col1_x if col == 1 else col2_x
            box_w_single = (box_w // 2) - 10
            # draw box
            draw_info_box(x, y, box_w_single, row_h, radius=14)
            # label
            label = key_translation.get(key, key)
            draw.text((x + 20, y + (row_h - SIZE_SETTING)//2 - 2), label, font=font_setting, fill=(255,255,255,230))
            # determine on/off
            val = setting.get(key, 0)
            # some values may be dict or string; interpret truthy/int(1)
            try:
                on = bool(int(val)) if isinstance(val, (int, str)) else bool(val)
            except:
                on = bool(val)
            # draw toggle at right side inside box
            tx = x + box_w_single - toggle_w - 20
            ty = y + (row_h - toggle_h)//2
            # track
            track_radius = toggle_h // 2
            track_color = (61,193,114,255) if on else (140,140,140,255)
            draw.rounded_rectangle([tx, ty, tx + toggle_w, ty + toggle_h], radius=track_radius, fill=track_color)
            # thumb
            thumb_r = toggle_h - 8
            if on:
                cx = tx + toggle_w - thumb_r/2 - 4
            else:
                cx = tx + thumb_r/2 + 4
            cy = ty + toggle_h/2
            draw.ellipse([cx - thumb_r/2, cy - thumb_r/2, cx + thumb_r/2, cy + thumb_r/2], fill=(255,255,255,255))
        # finish y for next if needed
        last_rows = (len(keys)+1)//2
        current_y = current_y + last_rows * (row_h + gap_y) + 18

        # Save temp file
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            out_path = tmp.name
            canvas.convert("RGB").save(out_path, "JPEG", quality=90)

        # send
        client.sendLocalImage(out_path, thread_id=thread_id, thread_type=thread_type)
        os.remove(out_path)

    except Exception as e:
        print("Lỗi xử lý infographic:", e)
        try:
            client.replyMessage(Message(text="❌ Lỗi xử lý infographic!"), message_object, thread_id, thread_type)
        except:
            pass

# PTA entry
def PTA():
    return {
        'in4gr': handle_infographic_small
    }