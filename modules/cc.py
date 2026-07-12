import os
import time
import requests
import random
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
from zlapi.models import Message, MessageStyle, MultiMsgStyle


des = {
    'version': "1.0.0",
    'credits': "ngbao",
    'description': "Capcut",
    'power': "member"
}

CONFIG = {
    'base_url': 'https://edit-api-sg.capcut.com',
    'search_path': '/lv/v1/cc_web/replicate/search_templates',
    'headers': {
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json',
        'origin': 'https://www.capcut.com',
        'referer': 'https://www.capcut.com/',
        'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N)',
        'sign': '8c69245fb9e23bbe2401518a277ef9d4',
        'sign-ver': '1',
        'priority': 'u=1, i',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'lan': 'vi-VN',
        'loc': 'va',
        'pf': '7',
        'appvr': '5.8.0',
        'app-sdk-version': '48.0.0',
        'device-time': '1734146729'
    }
}


dynamic_cache = {}
CACHE_DIR = os.path.join(os.path.dirname(__file__), 'cache')
MENU_OUTPUT = os.path.join(CACHE_DIR, 'capcut_menu.png')
LIST_OUTPUT = os.path.join(CACHE_DIR, 'capcut_list.jpg')
os.makedirs(CACHE_DIR, exist_ok=True)




def download_avatar(avatar_url, save_path=os.path.join(CACHE_DIR, "user_avatar.png")):
    try:
        if not avatar_url:
            return None
        resp = requests.get(avatar_url, stream=True, timeout=5)
        if resp.status_code == 200:
            with open(save_path, "wb") as f:
                for chunk in resp.iter_content(1024):
                    f.write(chunk)
            return save_path
    except Exception:
        pass
    return None


def random_contrast_color(box_color):
    import random
    r, g, b, _ = box_color if len(box_color) == 4 else (*box_color, 255)
    box_luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    if box_luminance > 0.5:
        r = random.randint(0, 50); g = random.randint(0, 50); b = random.randint(0, 50)
    else:
        r = random.randint(200, 255); g = random.randint(200, 255); b = random.randint(200, 255)
    return (r, g, b, 255)


def generate_menu_image_capcut(client, author_id, thread_id, thread_type):
    
    try:
        from datetime import datetime, timezone, timedelta
        import colorsys
        import random
        import glob

        size = (1280, 380)
        
        bg_paths = []
        bg_dir = os.path.join(os.path.dirname(__file__), '..', 'background')
        bg_dir_local = os.path.join(os.path.dirname(__file__), 'background')
        for d in (bg_dir, bg_dir_local):
            if os.path.isdir(d):
                for ext in ('*.jpg', '*.png', '*.jpeg'):
                    bg_paths += glob.glob(os.path.join(d, ext))

        if not bg_paths:
            bg_image = Image.new('RGBA', (1920, 600), (18, 24, 35, 255))
        else:
            bg_image = Image.open(random.choice(bg_paths)).convert('RGBA').resize((1920, 600), Image.Resampling.LANCZOS)
            try:
                bg_image = bg_image.filter(ImageFilter.GaussianBlur(radius=7))
            except Exception:
                pass

        overlay = Image.new('RGBA', (1920, 600), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        
        def get_dominant_color_local(image_path):
            try:
                if not os.path.exists(image_path):
                    return (0,0,0)
                img = Image.open(image_path).convert('RGB')
                img = img.resize((150,150), Image.Resampling.LANCZOS)
                pixels = img.getdata()
                r=g=b=0
                total = 0
                for p in pixels:
                    r+=p[0]; g+=p[1]; b+=p[2]; total+=1
                if total==0: return (0,0,0)
                return (r//total, g//total, b//total)
            except:
                return (0,0,0)

        box_colors = [
            (255, 20, 147, 110),
            (128, 0, 128, 110),
            (0, 100, 0, 110),
            (0, 0, 139, 110),
            (184, 134, 11, 110),
            (138, 3, 3, 110),
            (0, 0, 0, 90)
        ]
        box_color = random.choice(box_colors)

        # fonts
        try:
            font_arial_path = "font/DejaVuSans.ttf"
            font_text_large = ImageFont.truetype(font_arial_path, 76)
            font_text_big = ImageFont.truetype(font_arial_path, 68)
            font_text_small = ImageFont.truetype(font_arial_path, 64)
            font_text_bot = ImageFont.truetype(font_arial_path, 58)
            font_time = ImageFont.truetype(font_arial_path, 56)
            font_icon = ImageFont.truetype("font/NotoEmoji-Regular.ttf", 60)
            font_icon_large = ImageFont.truetype("font/NotoEmoji-Regular.ttf", 175)
            font_name = ImageFont.truetype("font/NotoEmoji-Regular.ttf", 60)
        except Exception:
            font_text_large = ImageFont.load_default()
            font_text_big = ImageFont.load_default()
            font_text_small = ImageFont.load_default()
            font_text_bot = ImageFont.load_default()
            font_time = ImageFont.load_default()
            font_icon = ImageFont.load_default()
            font_icon_large = ImageFont.load_default()
            font_name = ImageFont.load_default()

        def draw_text_with_shadow(draw_obj, position, text, font, fill, shadow_color=(0,0,0,200), shadow_offset=(2,2)):
            x,y = position
            draw_obj.text((x+shadow_offset[0], y+shadow_offset[1]), text, font=font, fill=shadow_color)
            draw_obj.text((x,y), text, font=font, fill=fill)

        
        vietnam_now = datetime.now(timezone(timedelta(hours=7)))
        hour = vietnam_now.hour
        formatted_time = vietnam_now.strftime("%H:%M")
        time_icon = "🌤️" if 6 <= hour < 18 else "🌙"
        time_text = f" {formatted_time}"

        
        size_box = (1920 - 180, 600 - 120)
        box_x1, box_y1 = 90, 60
        box_x2, box_y2 = box_x1 + size_box[0], box_y1 + size_box[1]
        draw.rounded_rectangle([(box_x1, box_y1), (box_x2, box_y2)], radius=75, fill=box_color)

        
        try:
            user_info = client.fetchUserInfo(author_id)
            if user_info and hasattr(user_info, 'changed_profiles') and author_id in user_info.changed_profiles:
                user = user_info.changed_profiles[author_id]
                user_name = getattr(user, 'name', None) or getattr(user, 'displayName', None) or f"ID_{author_id}"
                avatar = getattr(user, 'avatar', None)
            else:
                user_name = f"ID_{author_id}"
                avatar = None
        except Exception:
            user_name = f"ID_{author_id}"
            avatar = None

        greeting_name = user_name
        bot_name = user_name
        bot_version = des.get('version', '1.0')
        bot_update = getattr(des, 'date_update', 'N/A') if isinstance(des, dict) else 'N/A'

        emoji_colors = {
            "🎵": random_contrast_color(box_color),
            "😁": random_contrast_color(box_color),
            "🖤": random_contrast_color(box_color),
            "💞": random_contrast_color(box_color),
            "🤖": random_contrast_color(box_color),
            "💻": random_contrast_color(box_color),
            "📅": random_contrast_color(box_color),
            "🎧": random_contrast_color(box_color),
            "🌙": random_contrast_color(box_color),
            "🌤️": (200,150,50,255)
        }

        text_lines = [
            f"Hi, {greeting_name}",
            f"💞 Chào Bạn, tôi có thể giúp gì cho bạn ạ?",
            "😁 Bot Sẵn Sàng Phục 🖤",
            f"🤖Bot: {bot_name} 💻Version: {bot_version}"
        ]

        
        time_x = box_x2 - 250
        time_y = box_y1 + 10
        try:
            icon_x = time_x - 75
            icon_color = random_contrast_color(box_color)
            draw_text_with_shadow(draw, (icon_x, time_y - 8), time_icon, font_icon, icon_color, shadow_offset=(2,2))
            draw.text((time_x, time_y), time_text, font=font_time, fill=(255,255,255,220))
        except Exception:
            pass

        
        avatar_path = download_avatar(avatar, save_path=os.path.join(CACHE_DIR, f"capcut_avatar_{author_id}.png")) if avatar else None
        if avatar_path and os.path.exists(avatar_path):
            try:
                avatar_size = 200
                avatar_img = Image.open(avatar_path).convert('RGBA').resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)
                mask = Image.new('L', (avatar_size, avatar_size), 0)
                ImageDraw.Draw(mask).ellipse((0,0,avatar_size,avatar_size), fill=255)
                border_size = avatar_size + 10
                rainbow_border = Image.new('RGBA', (border_size, border_size), (0,0,0,0))
                draw_border = ImageDraw.Draw(rainbow_border)
                steps = 360
                for i in range(steps):
                    h = i/steps
                    r,g,b = colorsys.hsv_to_rgb(h,1.0,1.0)
                    draw_border.arc([(0,0),(border_size-1,border_size-1)], i, i + (360/steps), fill=(int(r*255),int(g*255),int(b*255),255), width=5)
                avatar_y = (box_y1 + box_y2 - avatar_size)//2
                overlay.paste(rainbow_border, (box_x1 + 40, avatar_y), rainbow_border)
                overlay.paste(avatar_img, (box_x1 + 45, avatar_y + 5), mask)
            except Exception:
                draw.text((box_x1 + 60, (box_y1 + box_y2)//2 - 140), "🐳", font=font_icon, fill=(0,139,139,255))
        else:
            draw.text((box_x1 + 60, (box_y1 + box_y2)//2 - 140), "🐳", font=font_icon, fill=(0,139,139,255))

        
        color1 = random_contrast_color(box_color)
        color2 = random_contrast_color(box_color)
        while color1 == color2:
            color2 = random_contrast_color(box_color)
        text_colors = [color1, color2, (255,255,255,220), (255,255,255,220)]
        text_fonts = [font_text_large, font_text_big, font_text_bot, font_text_small]

        line_spacing = 85
        start_y = box_y1 + 10

        current_line_idx = 0
        for i, line in enumerate(text_lines):
            if not line:
                current_line_idx += 1
                continue

            parts = []
            current_part = ""
            for char in line:
                if ord(char) > 0xFFFF:
                    if current_part:
                        parts.append(current_part); current_part = ""
                    parts.append(char)
                else:
                    current_part += char
            if current_part:
                parts.append(current_part)

            current_font = text_fonts[i] if i < len(text_fonts) else font_text_small

            total_width = 0
            part_widths = []
            for part in parts:
                width = draw.textbbox((0,0), part, font=font_icon if any(ord(c) > 0xFFFF for c in part) else current_font)[2]
                part_widths.append(width); total_width += width

            max_width = box_x2 - box_x1 - 300
            if total_width > max_width:
                font_size = int(current_font.size * max_width / total_width * 0.9) if hasattr(current_font, 'size') else 40
                if font_size < 50:
                    font_size = 50
                try:
                    current_font = ImageFont.truetype(font_arial_path, font_size)
                except Exception:
                    current_font = ImageFont.load_default()
                total_width = 0; part_widths = []
                for part in parts:
                    width = draw.textbbox((0,0), part, font=font_icon if any(ord(c) > 0xFFFF for c in part) else current_font)[2]
                    part_widths.append(width); total_width += width

            text_x = (box_x1 + box_x2 - total_width)//2
            text_y = start_y + current_line_idx * line_spacing + (getattr(current_font, 'size', 40)//2)

            current_x = text_x
            for part, width in zip(parts, part_widths):
                if any(ord(c) > 0xFFFF for c in part):
                    emoji_color = emoji_colors.get(part, random_contrast_color(box_color))
                    draw_text_with_shadow(draw, (current_x, text_y), part, font_icon, emoji_color, shadow_offset=(2,2))
                else:
                    if i < 2:
                        draw_text_with_shadow(draw, (current_x, text_y), part, current_font, text_colors[i], shadow_offset=(2,2))
                    else:
                        draw.text((current_x, text_y), part, font=current_font, fill=text_colors[i])
                current_x += width
            current_line_idx += 1

        
        right_icon = "🎧"
        icon_right_x = box_x2 - 225
        icon_right_y = (box_y1 + box_y2 - 180)//2
        draw_text_with_shadow(draw, (icon_right_x, icon_right_y), right_icon, font_icon_large, emoji_colors.get(right_icon, (80,80,80,255)), shadow_offset=(2,2))

        final_image = Image.alpha_composite(bg_image, overlay)
        final_image = final_image.resize((1280,380), Image.Resampling.LANCZOS)
        final_image.save(MENU_OUTPUT, 'PNG', quality=95)
        return MENU_OUTPUT

    except Exception as e:
        print(f"[generate_menu_image_capcut] Lỗi: {e}")
        return None



def create_capcut_list_image(templates, limit=9):
    try:
        scale = 2
        from colorsys import hsv_to_rgb, rgb_to_hsv
        import glob, emoji
        font_path = "font/DejaVuSans.ttf"
        emoji_font_path = "font/NotoEmoji-Regular.ttf"
        font = ImageFont.truetype(font_path, 28 * scale) if os.path.exists(font_path) else ImageFont.load_default()
        emoji_font = ImageFont.truetype(emoji_font_path, 28 * scale) if os.path.exists(emoji_font_path) else ImageFont.load_default()
        number_font = ImageFont.truetype(font_path, 40 * scale) if os.path.exists(font_path) else ImageFont.load_default()
        info_font = ImageFont.truetype(font_path, 14 * scale) if os.path.exists(font_path) else ImageFont.load_default()
        info_emoji_font = ImageFont.truetype(emoji_font_path, 14 * scale) if os.path.exists(emoji_font_path) else ImageFont.load_default()

        card_height = 105 * scale
        card_width = 583 * scale
        thumb_size = 90 * scale
        padding = 20 * scale
        spacing_y = 10 * scale
        card_padding = 8 * scale
        count = min(limit, len(templates))

        img_width = card_width + 2 * padding
        img_height = padding * 2 + count * card_height + (count - 1) * spacing_y

        background_images = []
        base_dir = os.path.dirname(__file__)
        cand_dirs = [os.path.join(base_dir, '..', 'background'), os.path.join(base_dir, 'background')]
        for d in cand_dirs:
            if os.path.isdir(d):
                for ext in ('*.jpg', '*.png', '*.jpeg'):
                    background_images += glob.glob(os.path.join(d, ext))

        if not background_images:
            background = Image.new("RGBA", (img_width, img_height), (20, 20, 20, 255))
        else:
            background_path = random.choice(background_images)
            background = Image.open(background_path).convert("RGBA").resize((img_width, img_height), Image.Resampling.LANCZOS)
            background = background.filter(ImageFilter.GaussianBlur(radius=7))

        image = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
        image.paste(background, (0, 0))
        draw = ImageDraw.Draw(image)

        def random_contrast_color_local(base_color):
            r, g, b, _ = base_color if len(base_color) == 4 else (*base_color, 255)
            box_luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            if box_luminance > 0.5:
                r = random.randint(0, 50); g = random.randint(0, 50); b = random.randint(0, 50)
            else:
                r = random.randint(200, 255); g = random.randint(200, 255); b = random.randint(200, 255)
            h, s, v = rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            s = min(1.0, s + 0.9)
            v = min(1.0, v + 0.9)
            r, g, b = hsv_to_rgb(h, s, v)
            return (int(r * 255), int(g * 255), int(b * 255), 255)

        def format_number(number):
            try:
                return f"{int(number):,}".replace(",", ".")
            except:
                return "0"

        box_colors = [
            (255, 20, 147, 110),
            (128, 0, 128, 110),
            (0, 100, 0, 110),
            (0, 0, 139, 110),
            (184, 134, 11, 110),
            (138, 3, 3, 110),
            (0, 0, 0, 80)
        ]
        box_color = random.choice(box_colors)
        title_color = random_contrast_color_local(box_color)
        icon_colors = {"🎧": (0, 255, 0, 255), "🖤": (255, 0, 0, 255), "💬": (255, 215, 0, 255)}
        info_color = (255, 255, 255, 255)
        number_color = random_contrast_color_local(box_color)

        def get_text_width(text, font_used):
            bbox = draw.textbbox((0, 0), text, font=font_used)
            return bbox[2] - bbox[0]

        def truncate_text(text, max_width, font_text, font_emoji):
            result = ''
            total_width = 0
            for char in text:
                font_used = font_emoji if emoji.is_emoji(char) else font_text
                char_width = get_text_width(char, font_used)
                if total_width + char_width > max_width:
                    result += '...'
                    break
                result += char
                total_width += char_width
            return result

        def draw_text_with_shadow_local(draw_obj, position, text, font_used, fill, shadow_color=(0,0,0,150), shadow_offset=(2,2)):
            x, y = position
            draw_obj.text((x + shadow_offset[0], y + shadow_offset[1]), text, font=font_used, fill=shadow_color)
            draw_obj.text((x, y), text, font=font_used, fill=fill)

        for i, tpl in enumerate(templates[:count]):
            left = padding
            top = padding + i * (card_height + spacing_y)
            card_img = Image.new("RGBA", (card_width, card_height), (0, 0, 0, 0))
            card_draw = ImageDraw.Draw(card_img)
            radius = 20 * scale
            card_draw.rounded_rectangle([0, 0, card_width, card_height], radius=radius, fill=box_color)
            image.paste(card_img, (left, top), card_img.split()[3])

            # --- Avatar + Rainbow Border ---
            try:
                resp = requests.get(tpl.get('cover_url') or tpl.get('thumbnail') or tpl.get('thumb') or '', timeout=4)
                av = Image.open(BytesIO(resp.content)).convert("RGBA").resize((thumb_size, thumb_size))
                mask = Image.new("L", av.size, 0)
                ImageDraw.Draw(mask).ellipse((0, 0) + av.size, fill=255)
                av.putalpha(mask)

                border_size = thumb_size + 10
                rainbow_border = Image.new("RGBA", (border_size, border_size), (0, 0, 0, 0))
                draw_border = ImageDraw.Draw(rainbow_border)
                steps = 360
                for j in range(steps):
                    h = j / steps
                    r, g, b = hsv_to_rgb(h, 1.0, 1.0)
                    draw_border.arc([(0, 0), (border_size-1, border_size-1)], j, j + (360 / steps), fill=(int(r * 255), int(g * 255), int(b * 255), 255), width=5)

                image.paste(rainbow_border, (left + card_padding + 7, top + card_padding + 5), rainbow_border)
                image.paste(av, (left + card_padding + 12, top + card_padding + 10), av)
            except Exception:
                draw.ellipse((left + card_padding + 12, top + card_padding + 10, left + card_padding + 12 + thumb_size, top + card_padding + 10 + thumb_size), fill=(90, 90, 90))

            
            title_x = left + card_padding + thumb_size + 35
            title_y = top + card_padding + 6
            max_text_width = card_width - thumb_size - 3 * card_padding - 20 * scale
            raw_title = (tpl.get("title") or "Không có tiêu đề").replace("\n", " ").strip()
            truncated_title = truncate_text(raw_title, max_text_width, font, emoji_font)
            x_text = title_x
            for char in truncated_title:
                font_used = emoji_font if emoji.is_emoji(char) else font
                draw_text_with_shadow_local(draw, (x_text, title_y), char, font_used, title_color)
                x_text += get_text_width(char, font_used)

            
            info_text = f"🎧 {format_number(tpl.get('play_amount') or tpl.get('views') or tpl.get('view_count') or 0)}  🖤 {format_number(tpl.get('like_count') or tpl.get('likes') or 0)}  💬 {format_number(tpl.get('usage_amount') or tpl.get('usage') or tpl.get('used_count') or 0)}"
            x_info = title_x
            info_height = info_font.size if hasattr(info_font, 'size') else 14 * scale
            y_info = top + card_height - card_padding - info_height
            for char in info_text:
                font_used = info_emoji_font if emoji.is_emoji(char) else info_font
                fill_color = icon_colors.get(char, info_color)
                draw_text_with_shadow_local(draw, (x_info, y_info), char, font_used, fill_color, shadow_offset=(1,1))
                x_info += get_text_width(char, font_used)

            
            number_text = str(i + 1)
            number_width = get_text_width(number_text, number_font)
            number_x = left + card_width - number_width - card_padding
            number_y = top + (card_height - (number_font.size if hasattr(number_font, 'size') else 40 * scale)) // 2
            draw_text_with_shadow_local(draw, (number_x, number_y), number_text, number_font, number_color)

        cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
        os.makedirs(cache_dir, exist_ok=True)
        file_path = os.path.join(cache_dir, "capcut_list_hd.png")
        image.save(file_path, format="PNG")  # PNG giữ chất lượng tốt hơn JPEG
        return file_path
    except Exception as e:
        print("Error in create_capcut_list_image:", e)
        return None




def handle_capcut_command(message, message_object, thread_id, thread_type, author_id, client):
    
    try:
        parts = message.strip().split(maxsplit=1)
    except Exception:
        parts = [""]

    if len(parts) < 2 or not parts[1].strip():
        
        try:
            image_path = generate_menu_image_capcut(client, author_id, thread_id, thread_type)
            caption = "🚦 Gõ capcut <từ khóa> để tìm video CapCut. Ví dụ: capcut trend"
            if image_path and os.path.exists(image_path):
                with Image.open(image_path) as img:
                    w, h = img.size
                client.sendLocalImage(imagePath=image_path, thread_id=thread_id, thread_type=thread_type, width=w, height=h, ttl=600000, message=Message(text=caption))
                try:
                    os.remove(image_path)
                except:
                    pass
                return
        except Exception as e:
            print('[handle_capcut_command - menu] ', e)
            
        msg = "🚦 Vui lòng nhập từ khóa để tìm Video CapCut hoặc chọn số sau khi tìm."
        return client.replyMessage(
            Message(text=msg, style=MultiMsgStyle([MessageStyle(0, len(msg), 'font', size=13, auto_format=False),
                                                   MessageStyle(0, len(msg), 'bold', auto_format=False)])),
            message_object, thread_id, thread_type
        )

    
    if len(parts) == 2 and parts[1].isdigit():
        return handle_capcut_number(int(parts[1]), author_id, thread_id, thread_type, message_object, client)

    query = parts[1].strip()
    payload = {
        'cc_web_version': 0,
        'count': 10,
        'cursor': '0',
        'enter_from': 'workspace',
        'query': query,
        'scene': 1,
        'sdk_version': '86.0.0',
        'search_version': 2
    }

    try:
        resp = requests.post(
            CONFIG['base_url'] + CONFIG['search_path'],
            json=payload,
            headers=CONFIG['headers'],
            timeout=10
        )
        data = resp.json()
        templates = data.get('data', {}).get('video_templates', [])
        if not templates:
            msg = f"🚦 Không tìm thấy video nào cho từ khóa: {query}."
            return client.replyMessage(
                Message(text=msg, style=MultiMsgStyle([MessageStyle(0, len(msg), 'font', size=13, auto_format=False),
                                                       MessageStyle(0, len(msg), 'bold', auto_format=False)])),
                message_object, thread_id, thread_type
            )

        image_path = create_capcut_list_image(templates)
        if image_path and os.path.exists(image_path):
            with Image.open(image_path) as img:
                w, h = img.size
            client.sendLocalImage(
                imagePath=image_path,
                thread_id=thread_id,
                thread_type=thread_type,
                width=w,
                height=h,
                ttl=600000,
                message=Message(text="🚦 Danh sách kết quả tìm kiếm🚦 Gõ capcut [số] để chọn video.")
            )
            try: os.remove(image_path)
            except: pass
        else:
            client.replyMessage(Message(text="🚦 Không thể tạo ảnh danh sách."), message_object, thread_id, thread_type)

        dynamic_cache[f"{author_id}_{thread_id}"] = {'templates': templates, 'timestamp': time.time()}

    except Exception as e:
        err = f"🚦 Lỗi khi xử lý: {e}"
        print(f"[CapCutCommand] {err}")
        return client.replyMessage(
            Message(text=err, style=MultiMsgStyle([MessageStyle(0, len(err), 'font', size=13, auto_format=False),
                                                  MessageStyle(0, len(err), 'bold', auto_format=False)])),
            message_object, thread_id, thread_type
        )


def handle_capcut_number(index, author_id, thread_id, thread_type, message_object, client):
    key = f"{author_id}_{thread_id}"
    if key not in dynamic_cache or time.time() - dynamic_cache[key]['timestamp'] > 300:
        return client.replyMessage(
            Message(
                text="🚦 Danh sách Video đã hết hạn. Hãy tìm lại bằng capcut [từ khóa].",
                style=MultiMsgStyle([
                    MessageStyle(0, 50, 'font', size=13, auto_format=False),
                    MessageStyle(0, 50, 'italic', auto_format=False)
                ])
            ),
            message_object, thread_id, thread_type
        )

    templates = dynamic_cache[key]['templates']
    if index < 1 or index > len(templates):
        return client.replyMessage(
            Message(
                text="🚦 Số không hợp lệ. Vui lòng chọn số trong danh sách.",
                style=MultiMsgStyle([
                    MessageStyle(0, 30, 'font', size=13, auto_format=False),
                    MessageStyle(0, 30, 'bold', auto_format=False)
                ])
            ),
            message_object, thread_id, thread_type
        )

    tpl = templates[index - 1]
    title = tpl.get('title', 'Không có tiêu đề')
    video_url = tpl.get('video_url') or tpl.get('demo_video_url')
    thumbnail_url = tpl.get('cover_url') or "https://i.imgur.com/tAmVhh5.jpg"
    template_id = tpl.get('id') or tpl.get('id_str')
    duration_ms = tpl.get('duration')
    view_count = tpl.get('play_amount') or 0
    like_count = tpl.get('like_count') or 0
    usage_count = tpl.get('usage_amount') or 0

    capcut_url = f"https://www.capcut.com/template/{template_id}" if template_id else "https://www.capcut.com"
    video_direct_link = video_url

    if not video_url:
        return client.replyMessage(
            Message(
                text="🚦 Video không có video demo.",
                style=MultiMsgStyle([
                    MessageStyle(0, 30, 'font', size=13, auto_format=False),
                    MessageStyle(0, 30, 'bold', auto_format=False)
                ])
            ),
            message_object, thread_id, thread_type
        )

    try:
        info = client.fetchUserInfo(author_id).changed_profiles[author_id]
        sender_name = getattr(info, 'zaloName', None) or getattr(info, 'displayName', None) or "Bạn"
    except:
        sender_name = "Bạn"

    caption = (
        f"🚦 {sender_name}\n"
        f"Video: {title}\n"
        f"Thời Lượng: {str(int(duration_ms / 1000)) + 's' if duration_ms else 'Không rõ'}\n"
        f"Lượt Xem: {view_count}\n"
        f"Lượt Thích: {like_count}\n"
        f"Đã Dùng: {usage_count}\n"
    )

    client.sendRemoteVideo(
        videoUrl=video_url,
        thumbnailUrl=thumbnail_url,
        duration=duration_ms or 15000,
        width=1080,
        height=1920,
        thread_id=thread_id,
        thread_type=thread_type,
        message=Message(text=caption),
        ttl=20 * 60 * 1000
    )


def PTA():
    return {'cc': handle_capcut_command}