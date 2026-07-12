import os
import importlib
import tempfile
import random
import requests
from io import BytesIO
from zlapi.models import Message
from config import PREFIX
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ----------------- CẤU HÌNH -----------------
FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
EMOJI_FONT_PATH = "modules/cache/font/NotoEmoji-Bold.ttf"

BG_IMAGES_DIR = "modules/cache/backgrounds"
CARD_BG_DIR = "modules/cache/backgroundmini"
FALLBACK_BG_PATH = "modules/cache/PTA.jpg"

PAGE_BG_MAPPING = {
    1:"gai1.jpg",2:"gai2.jpg",3:"gai3.jpg",4:"gai4.jpg",
    5:"gai5.jpg",6:"gai6.jpg",7:"gai7.jpg",8:"gai8.jpg",
    9:"gai9.jpg",10:"gai10.jpg",11:"gai11.jpg",12:"gai12.jpg"
}

CARD_BG_MAPPING = {}

CACHE_DIR = "modules/cache/menu_temp"
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(BG_IMAGES_DIR, exist_ok=True)
os.makedirs(CARD_BG_DIR, exist_ok=True)

des = {
    'version': "4.2.1",
    'credits': "ngbao",
    'description': "Menu lệnh bot.",
    'power': "Thành viên"
}

# ----------------- FONT -----------------
def get_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except:
        return ImageFont.load_default()

def get_emoji_font(size):
    try:
        return ImageFont.truetype(EMOJI_FONT_PATH, size)
    except:
        return ImageFont.load_default()

# ----------------- UTILS ẢNH -----------------
def load_image_from_url(url):
    resp = requests.get(url, timeout=10)
    return Image.open(BytesIO(resp.content)).convert("RGBA")

def _list_images_in_dir(d):
    try:
        return [f for f in os.listdir(d) if f.lower().endswith(('.jpg','.jpeg','.png','.webp'))]
    except:
        return []

def get_bg_image(size, page=None):
    # Danh sách ảnh nền random
    bg_urls = [
        "https://files.catbox.moe/y5fg9j.jpg",
        "https://files.catbox.moe/t31gfd.jpg",
        "https://files.catbox.moe/77c4by.jpg",
        "https://files.catbox.moe/d7p28q.jpg"
    ]

    try:
        # Random 1 ảnh bất kỳ
        url = random.choice(bg_urls)
        img = load_image_from_url(url)
        return img.convert("RGBA").resize(size, Image.LANCZOS)

    except:
        # fallback nếu lỗi
        return Image.new("RGBA", size, (22,18,35,255))

def autosave(img, quality=97):
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tf:
        img.convert("RGB").save(
            tf,"JPEG",
            quality=quality,
            dpi=(180,180),
            optimize=True,
            progressive=True,
            subsampling=0
        )
        return tf.name

def _smart_resize(img, w, h):
    iw, ih = img.size
    sc = min(w/iw, h/ih, 1.0)
    return img.resize((int(iw*sc), int(ih*sc)), Image.LANCZOS)

# ----------------- GLASS CARD -----------------
def glass_card(bg, cx, cy, card_w, card_h, radius=46):
    area = bg.crop((cx, cy, cx+card_w, cy+card_h)).filter(ImageFilter.GaussianBlur(8))
    overlay = Image.new("RGBA", (card_w, card_h), (22, 28, 45, 110))
    glass = Image.alpha_composite(area.convert("RGBA"), overlay)

    mask = Image.new("L", (card_w, card_h), 0)
    mDraw = ImageDraw.Draw(mask)
    mDraw.rounded_rectangle([0,0,card_w,card_h], radius=radius, fill=255)

    bg.paste(glass, (cx,cy), mask)

# ----------------- TEXT WRAP -----------------
def wrap_text(text, font, max_width, indent=0):
    lines, line = [], ""
    for p in text.split("\n"):
        for word in p.split():
            test = line + (" " if line else "") + word
            if font.getlength(test) + indent > max_width and line:
                lines.append(line)
                line = word
            else:
                line = test
        if line:
            lines.append(line)
        line = ""
    return lines

def fit_text(text, font, max_width, max_lines=2, ellipsis="..."):
    fs = getattr(font,"size",48)
    while fs >= 10:
        f = get_font(fs)
        lines = wrap_text(text,f,max_width)
        if len(lines)<=max_lines and all(f.getlength(i)<=max_width for i in lines):
            return lines, fs
        fs -= 1
    f = get_font(10)
    lines = wrap_text(text,f,max_width)
    if len(lines)>max_lines:
        lines = lines[:max_lines]
        if len(lines[-1])>3:
            lines[-1] = lines[-1][:-3] + ellipsis
    return lines, 10

def fit_desc_height(text, font, max_width, max_height):
    fs = getattr(font,"size",28)
    while fs>=15:
        f = get_font(fs)
        lines = wrap_text(text,f,max_width)
        if len(lines)*(f.size+3) <= max_height:
            return lines, f
        fs-=1
    f = get_font(15)
    return wrap_text(text,f,max_width), f

# ----------------- LẤY DANH SÁCH LỆNH -----------------
def get_all_PTA_with_info():
    PTA_info = {}
    for module_name in os.listdir("modules"):
        if module_name.endswith(".py") and module_name!="__init__.py":
            try:
                m = importlib.import_module(f"modules.{module_name[:-3]}")
                if hasattr(m,"PTA"):
                    cmds = m.PTA()
                    if cmds:
                        ds = getattr(m,"des",{})
                        PTA_info[module_name[:-3]] = {
                            "aliases": list(cmds.keys()),
                            "version": ds.get("version","1.0"),
                            "description": ds.get("description","Chưa mô tả"),
                            "power": ds.get("power","Thành viên")
                        }
            except Exception as e:
                print(e)
    return PTA_info

def paginate_menu(PTA_info,page=1,page_size=8):
    total_pages = (len(PTA_info)+page_size-1)//page_size or 1
    if page<1 or page>total_pages:
        return None, total_pages
    start = (page-1)*page_size
    end = start+page_size
    return list(PTA_info.items())[start:end], total_pages

# ----------------- RENDER MENU CHÍNH -----------------
def draw_menu_menu_img(menu_on_page, page, total_pages, total_cmds, color_palette, icons):
    WIDTH, HEIGHT = 1360, 1440

    bg = get_bg_image((WIDTH,HEIGHT), page=page)
    draw = ImageDraw.Draw(bg)

    font_title = get_font(78)
    font_info = get_font(36)
    font_footer = get_font(30)

    # ===== TITLE =====
    title = "Menu Bot By ngbao Dz"
    draw.text(
        (WIDTH//2 - font_title.getlength(title)//2, 60),
        title,
        font=font_title,
        fill=(0,255,255,255)
    )

    sub = f"Trang {page}/{total_pages} • {total_cmds} lệnh"
    draw.text(
        (WIDTH//2 - font_info.getlength(sub)//2,155),
        sub, font=font_info,
        fill=(210,230,255,230)
    )

    # GRID
    grid_x0 = 40
    grid_x1 = WIDTH - 100
    COLS,ROWS = 4,2
    gap_x = 38
    gap_y = 48
    card_w = (grid_x1-grid_x0-(COLS-1)*gap_x)//COLS + 16
    card_h = (HEIGHT-250-210-(ROWS-1)*gap_y)//ROWS + 32

    font_card_title = get_font(48)
    font_card_desc  = get_font(27)
    font_card_sub   = get_font(28)

    icon_radius = 63

    # ICON LIST (MỖI LỆNH 1 ICON)
    icon_urls = [
    "https://files.catbox.moe/ijpxb5.jpg",
    "https://files.catbox.moe/1fd4ad.jpg",
    "https://files.catbox.moe/uy8o28.jpg",
    "https://files.catbox.moe/6pvn60.jpg",

    "https://files.catbox.moe/tiwpfk.jpg",
    "https://files.catbox.moe/e99aaq.jpg",
    "https://files.catbox.moe/br526z.jpg",
    "https://files.catbox.moe/pagrpt.jpg"
    ]

    # ===================== DRAW EACH CARD =====================
    for idx,(module_key,info) in enumerate(menu_on_page):
        row,col = divmod(idx,COLS)
        cx = grid_x0 + col*(card_w+gap_x)
        cy = 210 + row*(card_h+gap_y)

        # ===== NEON BORDER =====
        neon = [
            (255,0,0,140),(255,127,0,140),(255,255,0,140),
            (0,255,0,140),(0,255,255,140),(0,127,255,140),
            (139,0,255,140)
        ]
        for g,c in enumerate(neon,1):
            draw.rounded_rectangle(
                [cx-g,cy-g,cx+card_w+g,cy+card_h+g],
                radius=46+g,
                outline=c,
                width=2
            )

        # ===== GLASS =====
        glass_card(bg, cx, cy, card_w, card_h, radius=46)

        # ===== ICON =====
        icon_x = cx + card_w//2
        icon_y = cy + 38 + icon_radius - 5
        rgb = color_palette[idx % len(color_palette)]

        # ===== ICON GLOW (VÒNG SÁNG NGOÀI) =====
        glow_layer = Image.new("RGBA", bg.size, (0,0,0,0))
        gdraw = ImageDraw.Draw(glow_layer)

        for r in range(8, 0, -1):
            gdraw.ellipse(
                [icon_x - icon_radius - r, icon_y - icon_radius - r,
                 icon_x + icon_radius + r, icon_y + icon_radius + r],
                fill=(rgb[0], rgb[1], rgb[2], 40)
            )

        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(12))
        bg.alpha_composite(glow_layer)

        # ===== VÒNG TRÒN NỀN CHO ICON =====
        draw.ellipse(
            [icon_x - icon_radius, icon_y - icon_radius,
             icon_x + icon_radius, icon_y + icon_radius],
            fill=rgb+(235,),
            outline=(22,28,45),
            width=5
        )

        # ===== ICON ẢNH (BO TRÒN, KHÔNG VIỀN ĐEN) =====
        icon_url = icon_urls[idx % len(icon_urls)]
        icon_img = load_image_from_url(icon_url)

        # Resize icon nhỏ hơn nền
        icon_size = icon_radius * 2 - 10
        icon_img = icon_img.resize((icon_size, icon_size), Image.LANCZOS)

        # Mask hình tròn
        mask = Image.new("L", (icon_size, icon_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, icon_size, icon_size), fill=255)

        # Icon đã bo tròn
        rounded_icon = Image.new("RGBA", (icon_size, icon_size), (0, 0, 0, 0))
        rounded_icon.paste(icon_img, (0, 0), mask)

        # Dán icon bo tròn lên card
        bg.paste(
            rounded_icon,
            (icon_x - icon_radius + 5, icon_y - icon_radius + 5),
            rounded_icon
        )

        # ===== TEXT =====
        y = icon_y + icon_radius + 10

        title = module_key.upper()
        lines, fsize = fit_text(title, font_card_title, card_w-40, 2)
        for line in lines:
            draw.text(
                (cx + card_w//2 - get_font(fsize).getlength(line)//2, y),
                line, font=get_font(fsize),
                fill=(255,255,255,250)
            )
            y += get_font(fsize).size + 2

        alias = "Alias: " + ", ".join(info["aliases"][:2])
        if len(info["aliases"])>2:
            alias += " ..."
        a_lines = wrap_text(alias, font_card_sub, card_w-70)
        for line in a_lines:
            draw.text(
                (cx + card_w//2 - font_card_sub.getlength(line)//2, y),
                line, font=font_card_sub,
                fill=(0,255,255,230)
            )
            y += font_card_sub.size+3

        ver = f"v{info['version']}"
        draw.text(
            (cx+card_w//2-font_card_sub.getlength(ver)//2, y),
            ver, font=font_card_sub,
            fill=(180,200,220)
        )
        y += font_card_sub.size+3

        powt= f"Quyền: {info['power']}"
        plines,_ = fit_text(powt, font_card_sub, card_w-50, 2)
        for line in plines:
            draw.text(
                (cx+card_w//2-font_card_sub.getlength(line)//2, y),
                line, font=font_card_sub,
                fill=(150,170,190)
            )
            y += font_card_sub.size+2

        desc_space = cy + card_h - y - 20
        d_lines, d_font = fit_desc_height(info["description"], font_card_desc, card_w-35, desc_space)
        for line in d_lines:
            draw.text(
                (cx + card_w//2 - d_font.getlength(line)//2, y),
                line, font=d_font,
                fill=(210,220,240)
            )
            y += d_font.size+3

    # ===== FOOTER =====
    footer = f" Bot By ngbao, Zalo: 0911037051"
    draw.text(
        (WIDTH//2 - font_footer.getlength(footer)//2, HEIGHT-80),
        footer, font=font_footer,
        fill=(0,255,255)
    )

    img = _smart_resize(bg,1280,1280)
    return autosave(img,97)

def draw_menu_detail_img(term, module_key, aliases, version, description, power, color_palette):
    WIDTH, HEIGHT = 1100, 1500

    # ===== BACKGROUND =====
    bg = get_bg_image((WIDTH,HEIGHT))
    draw = ImageDraw.Draw(bg)

    font_title = get_font(90)
    font_label = get_font(45)
    font_text  = get_font(40)
    font_small = get_font(34)

    # ===== GLASS CARD =====
    cx, cy = 90, 210
    card_w, card_h = WIDTH - 180, HEIGHT - 330
    glass_card(bg, cx, cy, card_w, card_h, radius=50)

    # ===== NEON BORDER =====
    neon = [
        (255,0,0,130),(255,127,0,130),(255,255,0,130),
        (0,255,0,130),(0,255,255,130),(0,127,255,130),
        (139,0,255,130)
    ]
    for g,c in enumerate(neon,1):
        draw.rounded_rectangle(
            [cx-g, cy-g, cx+card_w+g, cy+card_h+g],
            radius=50+g,
            outline=c,
            width=2
        )

    # ===== TITLE =====
    title = module_key.upper()
    draw.text(
        (WIDTH//2 - font_title.getlength(title)//2, 70),
        title, font=font_title, fill=(0,255,255)
    )

    # ===== CONTENT INSIDE CARD =====
    tx = cx + 60
    ty = cy + 60

    # Alias
    draw.text((tx, ty), "📌 Alias:", font=font_label, fill=(255,255,255))
    ty += 65
    draw.text((tx+20, ty), ", ".join(aliases), font=font_text, fill=(0,255,255))
    ty += 80

    # Version
    draw.text((tx, ty), "📦 Version:", font=font_label, fill=(255,255,255))
    ty += 65
    draw.text((tx+20, ty), version, font=font_text, fill=(200,230,255))
    ty += 80

    # Power
    draw.text((tx, ty), "🔰 Quyền yêu cầu:", font=font_label, fill=(255,255,255))
    ty += 65
    draw.text((tx+20, ty), power, font=font_text, fill=(255,200,120))
    ty += 80

    # Description
    draw.text((tx, ty), "📄 Mô tả:", font=font_label, fill=(255,255,255))
    ty += 65

    max_w = card_w - 150
    desc_lines = wrap_text(description, font_small, max_w)

    for line in desc_lines:
        draw.text((tx+20, ty), line, font=font_small, fill=(210,220,240))
        ty += font_small.size + 6

    # Footer
    footer = f"🔍 Chi tiết lệnh: {term}"
    draw.text(
        (WIDTH//2 - font_small.getlength(footer)//2, HEIGHT - 90),
        footer, font=font_small, fill=(0,255,255)
    )

    return autosave(bg, 97)


# ----------------- SEARCH -----------------
def search_commands(PTA_info, term):
    s = term.lower()
    return {k:v for k,v in PTA_info.items()
            if s in k.lower() or any(s in a.lower() for a in v["aliases"])}

# ----------------- HANDLE MENU -----------------
def handle_menu_menu(message, message_object, thread_id, thread_type, author_id, client):
    parts = message.split()
    PTA_info = get_all_PTA_with_info()

    color_palette = [
        (255, 0, 0), (255,127,0), (255,255,0),
        (0,255,0), (0,255,255), (0,127,255),
        (139,0,255)
    ]

    icons = ["⚡️","⚙️","📈","🕹️","💻","💾","🔗","🔑","🤖","📊","🧩","🖥️"]

    def send_img(path, reaction):
        try:
            if not os.path.exists(path) or os.path.getsize(path)==0:
                client.replyMessage(
                    Message(text="⚠️ Lỗi tạo ảnh menu!"),
                    message_object, thread_id, thread_type
                )
                return
            client.sendLocalImage(path, thread_id, thread_type)
            client.sendReaction(message_object, reaction, thread_id, thread_type)
        except:
            client.replyMessage(
                Message(text="❌ Không thể gửi ảnh!"),
                message_object, thread_id, thread_type
            )

    if len(parts)<2 or parts[1].lower()=="help":
        page_data, total_pages = paginate_menu(PTA_info, 1, 8)
        img = draw_menu_menu_img(page_data, 1, total_pages, len(PTA_info), color_palette, icons)
        send_img(img,"ℹ️")
        return

    if parts[1].isdigit():
        pg = int(parts[1])
        page_data, total_pages = paginate_menu(PTA_info, pg, 8)
        if page_data is None:
            client.replyMessage(
                Message(text=f"⚠️ Trang {pg} không hợp lệ!"),
                message_object, thread_id, thread_type
            )
            return
        img = draw_menu_menu_img(page_data, pg, total_pages, len(PTA_info), color_palette, icons)
        send_img(img,"📜")
        return

    term = parts[1].lower()
    found = search_commands(PTA_info, term)

    if not found:
        client.replyMessage(
            Message(text=f"❌ Không tìm thấy lệnh '{term}'!"),
            message_object, thread_id, thread_type
        )
        return

    if len(found)==1:
        key, info = list(found.items())[0]
        img = draw_menu_detail_img(term, key, info["aliases"], info["version"], info["description"], info["power"], color_palette)
        send_img(img,"🔍")
        return

    page_data, total_pages = paginate_menu(found, 1, 8)
    img = draw_menu_menu_img(page_data, 1, total_pages, len(found), color_palette, icons)
    send_img(img,"🔍")

# ----------------- REGISTER -----------------
def PTA():
    return {"menu": handle_menu_menu}
