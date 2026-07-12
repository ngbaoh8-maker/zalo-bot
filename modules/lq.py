import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zlapi.models import Message
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter, ImageEnhance
import colorsys

TYPE_MAP = {
    "dausi": 28,
    "dodon": 31,
    "phapsu": 29,
    "satthu": 32,
    "trothu": 30,
    "xathu": 33,
    "tatca": None
}

des = {
    'version': "1.0.0",
    'credits': "ngbao",
    'description': "Liên Quân Mobile",
    'power': "Thành Viên"
}

try:
    from config import PREFIX, ADMIN_ID
except Exception:
    PREFIX = None
    ADMIN_ID = None

CACHE_DIR = "modules/cache"
os.makedirs(CACHE_DIR, exist_ok=True)

LAST_HERO = {}       
SESSION_PAGE = {}    


def safe_name(name):
    if not name:
        return ""
    try:
        return str(name).encode('utf-8', errors='ignore').decode('utf-8', errors='ignore').strip()
    except:
        try:
            return str(name).strip()
        except:
            return ""


def download_file(url, path, timeout=12):
    if not url:
        return None
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, stream=True, timeout=timeout, headers=headers)
        if r.status_code == 200:
            with open(path, "wb") as f:
                for chunk in r.iter_content(1024):
                    if not chunk:
                        break
                    f.write(chunk)
            return path
    except:
        pass
    return None


def download_avatar(url, path=os.path.join(CACHE_DIR, "user_avatar.png")):
    return download_file(url, path)


def fetch_hero_list():
    url = "https://lienquan.garena.vn/hoc-vien/tuong-skin/"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=12)
        response.raise_for_status()
    except:
        return []
    soup = BeautifulSoup(response.text, "html.parser")
    hero_list_div = soup.find("div", class_="st-heroes__list")
    if not hero_list_div:
        return []
    heroes = hero_list_div.find_all("a", class_="st-heroes__item")
    hero_data = []
    for hero in heroes:
        name_tag = hero.find("h2", class_="st-heroes__item--name")
        img_tag = hero.find("img")
        link = hero.get("href")
        ten_tuong = name_tag.text.strip() if name_tag else "Không rõ"
        img_url = None
        if img_tag:
            img_url = img_tag.get("src") or img_tag.get("data-src")
        type_str = hero.get("data-type", "") or ""
        hero_data.append({
            "name": ten_tuong.lower(),
            "display_name": ten_tuong,
            "img": img_url,
            "link": link,
            "type_str": type_str
        })
    return hero_data


def filter_heroes_by_type(hero_data, mode):
    type_id = TYPE_MAP.get(mode)
    if type_id is None:
        return hero_data
    return [h for h in hero_data if f"[{type_id}]" in h["type_str"]]


def search_hero_by_name(hero_data, query):
    q = query.lower()
    return [h for h in hero_data if q in safe_name(h["name"]).lower() or q in safe_name(h["display_name"]).lower()]


def _extract_skin_rarity(skin_tag):
    
    try:
        
        candidates = []
        for sel in ["span", "small", "em", "i", "div"]:
            for t in skin_tag.find_all(sel):
                txt = (t.get_text(" ", strip=True) or "").strip()
                if not txt:
                    continue
                
                if any(k in txt.lower() for k in ["bậc", "rank", "rare", "epic", "legend", "ss", "s", "bạc", "vàng", "kim"]):
                    return txt
                if len(txt) <= 6 and any(ch.isalpha() or ch.isdigit() for ch in txt):
                    
                    candidates.append(txt)
        
        for key in ["data-rarity", "data-rank", "rarity"]:
            if skin_tag.get(key):
                return skin_tag.get(key)
        if candidates:
            return candidates[0]
    except:
        pass
    return ""


def get_hero_details_struct(hero_url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(hero_url, headers=headers, timeout=12)
        resp.raise_for_status()
    except:
        return {"skins": [], "skills": []}
    soup = BeautifulSoup(resp.text, "html.parser")
    out = {"skins": [], "skills": []}
    skin_section = soup.select_one(".p-academy__main .hero .hero__skins")
    if skin_section:
        skins = skin_section.select(".hero__skins--detail")
        for skin in skins:
            ten_skin = skin.find("h3").get_text(strip=True) if skin.find("h3") else ""
            img_full = None
            picture = skin.find("picture")
            if picture:
                img_tag = picture.find("img")
                if img_tag:
                    img_full = img_tag.get("src") or img_tag.get("data-src")
            thumb_img_tag = None
            try:
                thumb_img_tag = skin.find("h3").find("img") if skin.find("h3") else None
            except:
                thumb_img_tag = None
            img_thumb = thumb_img_tag.get("src") if thumb_img_tag else (img_full)
            rarity = _extract_skin_rarity(skin)
            out["skins"].append({
                "name": ten_skin,
                "thumb": img_thumb,
                "full": img_full,
                "rarity": rarity
            })
    skill_section = soup.select_one(".p-academy__main .hero .hero__skills")
    if skill_section:
        skill_list_items = skill_section.select(".hero__skills--list li a")
        skill_images = []
        for item in skill_list_items:
            img = item.find("img")
            if img:
                skill_images.append({
                    "name": img.get("alt").strip() if img.get("alt") else "",
                    "img": img.get("src") or img.get("data-src")
                })
        skill_details = skill_section.select(".hero__skills--detail")
        for idx, detail in enumerate(skill_details):
            ten_skill = detail.find("h3").get_text(strip=True) if detail.find("h3") else ""
            thong_tin = ""
            article = detail.find("article")
            if article:
                thong_tin = article.get_text(separator=" ", strip=True)
            icon_url = skill_images[idx]["img"] if idx < len(skill_images) else None
            out["skills"].append({
                "name": ten_skill,
                "info": thong_tin,
                "icon": icon_url
            })
    return out


def _paginate_list(items, page=1, per_page=30):
    total = len(items)
    total_pages = max(1, (total + per_page - 1) // per_page)
    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages
    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end], page, total_pages, total


def _circle_avatar(im, size):
    try:
        im = im.convert("RGBA")
        im = ImageOps.fit(im, (size, size), centering=(0.5, 0.5))
        mask = Image.new("L", (size, size), 0)
        md = ImageDraw.Draw(mask)
        md.ellipse((0, 0, size, size), fill=255)
        out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        out.paste(im, (0, 0), mask)
        return out
    except:
        return None


def draw_text_box(draw, text, font, box, fill=(255, 255, 255, 255), line_spacing=4, max_lines=None):
    x1, y1, x2, y2 = box
    width = x2 - x1
    height = y2 - y1
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        test = (cur + " " + w).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        tw = bbox[2] - bbox[0]
        if tw <= width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
        if len(lines) >= 1000:
            break
    if cur:
        lines.append(cur)
    if max_lines is None:
        lh = draw.textbbox((0, 0), "Ay", font=font)[3] - draw.textbbox((0, 0), "Ay", font=font)[1]
        max_lines_fit = max(1, (height + line_spacing) // (lh + line_spacing))
    else:
        max_lines_fit = max_lines
    if len(lines) > max_lines_fit:
        lines = lines[:max_lines_fit]
        last = lines[-1]
        ell = "..."
        while True:
            test = last + ell
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] <= width:
                lines[-1] = test
                break
            if len(last) <= 1:
                lines[-1] = ell
                break
            last = last[:-1]
    lh = draw.textbbox((0, 0), "Ay", font=font)[3] - draw.textbbox((0, 0), "Ay", font=font)[1]
    cur_y = y1
    for ln in lines:
        if cur_y + lh > y2:
            break
        draw.text((x1, cur_y), ln, font=font, fill=fill)
        cur_y += lh + line_spacing
    return cur_y


def create_skin_card(output_path, hero, skin, details, author_avatar_path=None):
    W, H = 1400, 920
    font_path = "font/DejaVuSans.ttf"
    if os.path.exists(font_path):
        title_font = ImageFont.truetype(font_path, 54)
        skin_font = ImageFont.truetype(font_path, 40)
        hname_font = ImageFont.truetype(font_path, 30)
        body_font = ImageFont.truetype(font_path, 22)
    else:
        title_font = skin_font = hname_font = body_font = ImageFont.load_default()
    card = Image.new("RGBA", (W, H), (20, 20, 20, 255))

    # background: ưu tiên ảnh full skin, fallback hero img
    bg_path = None
    if skin.get("full"):
        bg_path = download_file(skin.get("full"), os.path.join(CACHE_DIR, "skin_full.png"))
    if not bg_path and hero.get("img"):
        bg_path = download_file(hero.get("img"), os.path.join(CACHE_DIR, "hero_bg_fallback.png"))
    if bg_path and os.path.exists(bg_path):
        try:
            bg = Image.open(bg_path).convert("RGBA")
            bg = bg.resize((W, H), Image.LANCZOS)
            enhancer = ImageEnhance.Brightness(bg)
            bg = enhancer.enhance(0.45)
            blur = bg.filter(ImageFilter.GaussianBlur(4))
            card.paste(blur, (0, 0))
        except:
            pass

    draw = ImageDraw.Draw(card)
    left_w = 440
    avatar_size = 340

    
    skin_avatar_path = None
    if skin.get("full"):
        skin_avatar_path = download_file(skin.get("full"), os.path.join(CACHE_DIR, "skin_avatar_full.png"))
    elif hero.get("img"):
        skin_avatar_path = download_file(hero.get("img"), os.path.join(CACHE_DIR, "hero_avatar.png"))

    if skin_avatar_path and os.path.exists(skin_avatar_path):
        try:
            av = Image.open(skin_avatar_path).convert("RGBA")
            circ = _circle_avatar(av, avatar_size)
            if circ:
                border = Image.new("RGBA", (avatar_size + 22, avatar_size + 22), (0, 0, 0, 0))
                bdraw = ImageDraw.Draw(border)
                for i in range(360):
                    color = tuple(int(x * 255) for x in colorsys.hsv_to_rgb(i / 360, 1, 1)) + (255,)
                    bdraw.arc((0, 0, avatar_size + 22, avatar_size + 22), start=i, end=i + 1, fill=color, width=6)
                bx = 40
                by = 70
                card.paste(border, (bx, by), border)
                card.paste(circ, (bx + 11, by + 11), circ)
        except:
            pass

    name_x = left_w + 60
    name_y = 90
    hero_name = hero.get("display_name", "").strip()
    draw.text((name_x, name_y), hero_name, font=title_font, fill=(200, 255, 200, 255))
    skin_name = skin.get("name", "").strip()
    draw.text((name_x, name_y + 72), skin_name, font=skin_font, fill=(200, 240, 255, 255))

    

    draw.line((name_x, name_y + 160, W - 60, name_y + 160), fill=(255, 255, 255, 80), width=2)

    skills = details.get("skills", []) or []
    start_x = name_x
    cur_y = name_y + 190
    icon_size = 72
    gap = 18
    for i, sk in enumerate(skills):
        if cur_y + 120 > H - 80:
            break
        ic_path = None
        if sk.get("icon"):
            ic_path = download_file(sk.get("icon"), os.path.join(CACHE_DIR, f"skill_icon_{i}.png"))
        if ic_path and os.path.exists(ic_path):
            try:
                ic = Image.open(ic_path).convert("RGBA")
                ic = ImageOps.fit(ic, (icon_size, icon_size), centering=(0.5, 0.5))
                circle_bg = Image.new("RGBA", (icon_size + 12, icon_size + 12), (30, 30, 30, 200))
                mask = Image.new("L", circle_bg.size, 0)
                md = ImageDraw.Draw(mask)
                md.ellipse((0, 0, circle_bg.size[0], circle_bg.size[1]), fill=255)
                cx = start_x
                card.paste(circle_bg, (cx, cur_y), mask)
                card.paste(ic, (cx + 6, cur_y + 6), ic)
            except:
                draw.rectangle((start_x, cur_y, start_x + icon_size, cur_y + icon_size), fill=(60, 60, 60, 180))
        else:
            draw.ellipse((start_x, cur_y, start_x + icon_size, cur_y + icon_size), fill=(60, 60, 60, 180))
            tb = draw.textbbox((0, 0), "?", font=hname_font)
            tw, th = tb[2] - tb[0], tb[3] - tb[1]
            draw.text((start_x + (icon_size - tw) // 2, cur_y + (icon_size - th) // 2), "?", font=hname_font,
                      fill=(220, 220, 220, 255))
        text_x = start_x + icon_size + gap + 6
        draw.text((text_x, cur_y), sk.get("name", ""), font=hname_font, fill=(190, 240, 255, 255))
        info_box = (text_x, cur_y + 30, W - 60, cur_y + 30 + 88)
        draw_text_box(draw, (sk.get("info") or ""), body_font, info_box, fill=(230, 230, 230, 255), line_spacing=4,
                      max_lines=4)
        sep_y = cur_y + 30 + 88 + 10
        draw.line((text_x, sep_y, W - 60, sep_y), fill=(255, 255, 255, 40), width=1)
        cur_y = sep_y + 18

    try:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        card.save(output_path, format="PNG")
    except:
        return None
    finally:
        for f in ["skin_full.png", "hero_bg_fallback.png", "skin_avatar_full.png", "hero_avatar.png"]:
            try:
                p = os.path.join(CACHE_DIR, f)
                if os.path.exists(p):
                    os.remove(p)
            except:
                pass
        for i in range(10):
            try:
                p = os.path.join(CACHE_DIR, f"skill_icon_{i}.png")
                if os.path.exists(p):
                    os.remove(p)
            except:
                pass
    return output_path


def create_menu_text(bot_name, hero_list, page=1, per_page=30):
    now = datetime.now()
    today = now.strftime("%d-%m-%Y")
    hour = now.strftime("%H:%M")
    items, cur_page, total_pages, total = _paginate_list(hero_list, page, per_page)
    lines = []
    lines.append("=== LIÊN QUÂN MOBILE - DANH SÁCH TƯỚNG ===")
    lines.append(f"Ngày: {today} | Giờ: {hour}")
    lines.append(f"Trang: {cur_page}/{total_pages} | Tổng số: {total} tướng")
    lines.append("-----------------------------------------\n")
    for i, hero in enumerate(items, start=(cur_page - 1) * per_page + 1):
        name = hero.get('display_name') or hero.get('name') or '???'
        lines.append(f"{str(i).zfill(2)}. {name}")
    lines.append("\n-----------------------------------------")
    lines.append("Hướng dẫn:")
    lines.append("- lq <số> : xem trang số đó")
    lines.append("- sau xem trang, gõ: lq <số_tướng_trong_trang> để chọn tướng trên trang đó")
    lines.append("- lq <tên_tướng> : xem danh sách skin")
    lines.append("- lq <tên_tướng> <số_skin> : xem skin")
    lines.append("- Sau xem tướng, gõ: lq <số_skin> để lấy skin (một lần, sau đó kết phiên)")
    lines.append("-----------------------------------------")
    return "\n".join(lines)


def create_skin_list_text(hero, details):
    lines = []
    lines.append(f"=== SKIN CỦA {hero.get('display_name','???')} ===")
    skins = details.get("skins", [])
    if not skins:
        lines.append("Không tìm thấy skin nào.")
        return "\n".join(lines)
    for i, sk in enumerate(skins, start=1):
        label = sk.get("name", "???")
        if sk.get("rarity"):
            label = f"{label} [{sk.get('rarity')}]"
        lines.append(f"{i:02d}. {label}")
    lines.append("\nGõ: lq <tên_tướng> <số_skin>")
    lines.append("Hoặc sau khi xem tướng, gõ: lq <số_skin>")
    return "\n".join(lines)


def handle_lq(message, msg_obj, thread_id, thread_type, author_id, client):
    raw = (message or "").strip()
    parts = raw.split()
    if len(parts) >= 1:
        parts = parts[1:]
    per_page = 30

    hero_data = fetch_hero_list()
    if not hero_data:
        try:
            client.sendMessage(Message(text="Không thể lấy danh sách tướng."), thread_id=thread_id, thread_type=thread_type)
        except:
            pass
        return

    bot_name = "Bot"
    try:
        uid = getattr(client, "uid", None)
        info = client.fetchUserInfo(uid) if hasattr(client, "fetchUserInfo") else {}
        if isinstance(info, dict):
            bot_name = info.get("zaloName") or info.get("displayName") or bot_name
    except:
        pass
    bot_name = safe_name(bot_name)

    if len(parts) == 0:
        page = 1
        menu_text = create_menu_text(bot_name=bot_name, hero_list=hero_data, page=page, per_page=per_page)
        try:
            client.sendMessage(Message(text=menu_text), thread_id=thread_id, thread_type=thread_type)
        except:
            pass
        return

    if parts[0].lower() == "search":
        query = " ".join(parts[1:]).strip()
        if not query:
            try:
                client.sendMessage(Message(text="Gõ: lq search <tên tướng>"), thread_id=thread_id, thread_type=thread_type)
            except:
                pass
            return
        results = search_hero_by_name(hero_data, query)
        if not results:
            try:
                client.sendMessage(Message(text=f"Không tìm thấy tướng với từ khóa: {query}"), thread_id=thread_id, thread_type=thread_type)
            except:
                pass
            return
        menu_text = create_menu_text(bot_name=bot_name, hero_list=results, page=1, per_page=per_page)
        try:
            client.sendMessage(Message(text=menu_text), thread_id=thread_id, thread_type=thread_type)
        except:
            pass
        return

    if parts[0].lower() in TYPE_MAP:
        mode = parts[0].lower()
        page = 1
        if len(parts) >= 2 and parts[1].isdigit():
            page = max(1, int(parts[1]))
        filtered = filter_heroes_by_type(hero_data, mode)
        if not filtered:
            try:
                client.sendMessage(Message(text=f"Không tìm thấy tướng loại: {mode}"), thread_id=thread_id, thread_type=thread_type)
            except:
                pass
            return
        menu_text = create_menu_text(bot_name=bot_name, hero_list=filtered, page=page, per_page=per_page)
        try:
            client.sendMessage(Message(text=menu_text), thread_id=thread_id, thread_type=thread_type)
        except:
            pass
        return

    if len(parts) == 1 and parts[0].isdigit():
        page = max(1, int(parts[0]))
        menu_text = create_menu_text(bot_name=bot_name, hero_list=hero_data, page=page, per_page=per_page)
        try:
            client.sendMessage(Message(text=menu_text), thread_id=thread_id, thread_type=thread_type)
        except:
            pass
        return

    if parts and parts[-1].isdigit():
        skin_token = parts[-1]
        name_query = " ".join(parts[:-1]).strip()
        query = name_query
    else:
        skin_token = None
        query = " ".join(parts).strip()

    results = search_hero_by_name(hero_data, query)
    if not results:
        try:
            client.sendMessage(Message(text=f"Không tìm thấy tướng: {query}"), thread_id=thread_id, thread_type=thread_type)
        except:
            pass
        return

    if len(results) == 1:
        hero = results[0]
        details = get_hero_details_struct(hero.get("link") or "")
        skins = details.get("skins", [])
        if skin_token:
            idx = int(skin_token) - 1
            if 0 <= idx < len(skins):
                skin = skins[idx]
                card_path = os.path.join(CACHE_DIR, "hero_skin_card.png")
                create_skin_card(card_path, hero, skin, details)
                try:
                    client.sendLocalImage(imagePath=card_path, message=Message(text=""), thread_id=thread_id, thread_type=thread_type, width=1000, height=650, ttl=60000)
                except:
                    try:
                        client.sendMessage(Message(text=f"{hero.get('display_name')} - {skin.get('name')}"), thread_id=thread_id, thread_type=thread_type)
                    except:
                        pass
                try:
                    if os.path.exists(card_path):
                        os.remove(card_path)
                except:
                    pass
                return
            else:
                try:
                    client.sendMessage(Message(text="❌ Số skin không hợp lệ."), thread_id=thread_id, thread_type=thread_type)
                except:
                    pass
                return
        msg = create_skin_list_text(hero, details)
        try:
            client.sendMessage(Message(text=msg), thread_id=thread_id, thread_type=thread_type)
        except:
            pass
        return

    menu_text = create_menu_text(bot_name=bot_name, hero_list=results, page=1, per_page=per_page)
    try:
        client.sendMessage(Message(text=menu_text), thread_id=thread_id, thread_type=thread_type)
    except:
        pass


def PTA():
    return {
        "lq": handle_lq
    }
