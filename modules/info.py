import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import requests
import base64
import emoji
from datetime import datetime
import json
import random
import textwrap
from zlapi.models import *

des = {'version': "1.3.0", 'credits': "ngbao", 'description': "Thông tin người dùng", 'power': "Thành Viên"}

FONT_DIR = "modules/cache/font/"
ARIAL_FONT = os.path.join(FONT_DIR, "BeVietnamPro-Bold.ttf")
NOTO_EMOJI_FONT = os.path.join(FONT_DIR, "NotoEmoji-Bold.ttf")
BEVIETNAMPRO_BOLD = os.path.join(FONT_DIR, "BeVietnamPro-Bold.ttf")

def get_safe_font(font_path, size):
    if os.path.exists(font_path):
        return ImageFont.truetype(font_path, size)
    print(f"Cảnh báo: Không tìm thấy font tại {font_path}. Đang sử dụng font mặc định.")
    try:
        return ImageFont.truetype("arial.ttf", size) 
    except Exception:
        try:
            return ImageFont.load_default(size) 
        except Exception:
            return ImageFont.truetype("DejaVuSans.ttf", size) 

def draw_text_with_emojis(draw, text, x, y, font, emoji_font, text_color):
    current_x = x
    for char in text:
        f = emoji_font if emoji.emoji_count(char) and emoji_font else font
        draw.text((current_x, y), char, fill=text_color, font=f)
        current_x += f.getlength(char)

def wrap_text(text, font, emoji_font, max_width):
    lines = []
    if not text:
        return [""]
    
    avg_char_width = font.getlength("a") 
    if avg_char_width == 0: avg_char_width = font.size * 0.6
    
    max_chars_per_line_approx = int(max_width / avg_char_width) if avg_char_width > 0 else 50
    if max_chars_per_line_approx < 1: max_chars_per_line_approx = 1
    
    wrapped_paragraphs = []
    for paragraph in text.splitlines():
        wrapped_paragraphs.extend(textwrap.wrap(paragraph, width=max_chars_per_line_approx, break_long_words=False, replace_whitespace=False))
    
    final_lines = []
    for line in wrapped_paragraphs:
        current_line_width = 0
        for char in line:
            f = emoji_font if emoji.emoji_count(char) and emoji_font else font
            current_line_width += f.getlength(char)
        
        if current_line_width > max_width and len(line.split(' ')) > 1:
            words = line.split(' ')
            temp_line = []
            temp_line_width = 0
            for word in words:
                word_width = 0
                for char in word:
                    f = emoji_font if emoji.emoji_count(char) and emoji_font else font
                    word_width += f.getlength(char)
                
                space_width = font.getlength(' ')
                
                if temp_line_width + word_width + (space_width if temp_line else 0) <= max_width:
                    temp_line.append(word)
                    temp_line_width += word_width + (space_width if temp_line else 0)
                else:
                    if temp_line:
                        final_lines.append(' '.join(temp_line))
                    temp_line = [word]
                    temp_line_width = word_width
            if temp_line:
                final_lines.append(' '.join(temp_line))
        else:
            final_lines.append(line)
            
    return final_lines

def calculate_text_display_height(text, font, emoji_font, max_width, line_spacing_multiplier=1.4):
    wrapped_lines = wrap_text(text, font, emoji_font, max_width)
    if not wrapped_lines:
        return 0
    try:
        line_height_base = font.getbbox("Ay")[3] - font.getbbox("Ay")[1]
    except Exception:
        line_height_base = font.size * 1.2
    line_spacing = int(line_height_base * line_spacing_multiplier)
    return len(wrapped_lines) * line_spacing

def create_text(draw, text, font, emoji_font, position, text_color, max_width=None, align="left", line_spacing_multiplier=1.4):
    x, y = position
    
    wrapped_lines = wrap_text(text, font, emoji_font, max_width) if max_width else text.splitlines()
    
    try:
        line_height_base = font.getbbox("Ay")[3] - font.getbbox("Ay")[1]
    except Exception:
        line_height_base = font.size * 1.2
    
    line_spacing = int(line_height_base * line_spacing_multiplier)
    
    for line in wrapped_lines:
        line_x = x
        if align == "center":
            line_width = 0
            for char in line:
                f = emoji_font if emoji.emoji_count(char) and emoji_font else font
                line_width += f.getlength(char)
            line_x = x - line_width // 2
        elif align == "right":
            line_width = 0
            for char in line:
                f = emoji_font if emoji.emoji_count(char) and emoji_font else font
                line_width += f.getlength(char)
            line_x = x - line_width
        
        draw_text_with_emojis(draw, line, line_x, y, font, emoji_font, text_color)
        y += line_spacing

def add_round_corners(image, radius, border_width=0, border_color=(0,0,0,0)):
    mask = Image.new('L', image.size, 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rounded_rectangle((0, 0, image.width, image.height), radius, fill=255)
    
    final_image = image.copy()
    final_image.putalpha(mask)

    if border_width > 0:
        border_mask = Image.new('L', image.size, 0)
        draw_border_mask = ImageDraw.Draw(border_mask)
        draw_border_mask.rounded_rectangle((0, 0, image.width, image.height), radius, fill=255, outline=255, width=border_width)
        
        border_image = Image.new('RGBA', image.size, border_color)
        border_image.putalpha(border_mask)
        
        final_image = Image.alpha_composite(border_image, final_image)

    return final_image

def get_user_name_by_id(client, uid):
    try:
        user_info = client.fetchUserInfo(uid)
        user = user_info.changed_profiles.get(uid)
        return user.displayName if user and user.displayName else "Người dùng không xác định"
    except Exception:
        return "Người dùng không xác định"

def fetch_image(url):
    if not url:
        return None
    try:
        if url.startswith('data:image'):
            header, encoded_data = url.split(',', 1)
            try:
                decoded_data = base64.b64decode(encoded_data)
            except:
                return None
            return Image.open(BytesIO(decoded_data)).convert("RGBA")
        
        r = requests.get(url, stream=True, timeout=5)
        r.raise_for_status()
        return Image.open(BytesIO(r.content)).convert("RGBA")
    except Exception as e:
        print(f"Lỗi khi tải ảnh từ {url}: {e}")
        return None

def format_timestamp(ts, default="Không xác định"):
    if isinstance(ts, (int, float)):
        try:
            if ts > 4_102_444_800_000:
                ts /= 1000
            elif ts < 1_000_000_000 and ts != 0:
                return default
            
            if ts <= 0:
                 return default

            return datetime.fromtimestamp(ts).strftime("%H:%M %d/%m/%Y")
        except (ValueError, OSError):
            return default
    return default


def info(message, message_object, thread_id, thread_type, author_id, client):
    try:
        mentions = message_object.mentions
        if mentions:
            target_id = mentions[0]['uid']
        else:
            msg_parts = message.split()
            if len(msg_parts) > 1:
                input_value = msg_parts[1]
                try:
                    user_id_data = client.fetchPhoneNumber(input_value, language="en")
                    target_id = user_id_data.get('uid', input_value) if user_id_data else input_value
                except Exception:
                    target_id = input_value
            else:
                target_id = author_id

        user_info = client.fetchUserInfo(target_id)
        user = user_info.changed_profiles.get(target_id)

        if not user:
            client.send(
                Message(text="Không thể lấy thông tin người dùng này hoặc ID không hợp lệ."),
                thread_id=thread_id,
                thread_type=thread_type
            )
            return

        img_width = 1280
        card_margin = 50
        card_width = img_width - 2 * card_margin
        card_radius = 40

        text_mode = 'light'
        text_color = (255, 255, 255)
        
        card_bg_color = (50, 50, 50, 180)

        name_font_size = 50
        name_font = get_safe_font(ARIAL_FONT, name_font_size)
        emoji_font_name = get_safe_font(NOTO_EMOJI_FONT, name_font_size)

        detail_font_size = 22
        detail_font = get_safe_font(ARIAL_FONT, detail_font_size)
        emoji_detail_font = get_safe_font(NOTO_EMOJI_FONT, detail_font_size)
        
        bio_font_size = 28
        bio_font = get_safe_font(ARIAL_FONT, bio_font_size)
        emoji_bio_font = get_safe_font(NOTO_EMOJI_FONT, bio_font_size)

        status_font_size = 35
        status_font = get_safe_font(ARIAL_FONT, status_font_size)
        emoji_font_status = get_safe_font(NOTO_EMOJI_FONT, status_font_size)

        fetched_avatar_image = fetch_image(user.avatar) if hasattr(user, 'avatar') else None
        fetched_cover_image = fetch_image(user.cover) if hasattr(user, 'cover') else None

        initial_header_fixed_height = 280 
        avatar_size = 200
        
        name_pos_y_relative_to_card_top = initial_header_fixed_height + 15 
        
        info_padding_x = 50 
        info_section_width = card_width - 2 * info_padding_x
        column_width = info_section_width // 2 - 10 

        info_items = [
            {"label": "🆔 ID:", "value": str(user.userId)},
            {"label": "🎂 Sinh nhật:", "value": format_timestamp(user.dob, default="Ẩn")},
            {"label": "💡 Hoạt động:", "value": format_timestamp(user.lastActionTime)},
            {"label": "💼 Business:", "value": "Có" if hasattr(user, 'bizPkg') and user.bizPkg and user.bizPkg.label else "Không"},
            {"label": "🚻 Giới tính:", "value": 'Nam' if user.gender == 0 else ('Nữ' if user.gender == 1 else 'Không xác định')},
            {"label": "🗓️ Ngày tạo:", "value": format_timestamp(user.createdTs)},
            {"label": "🌍 Global ID:", "value": str(user.globalId) if hasattr(user, 'globalId') else "Không có"},
            {"label": "📱 Số điện thoại:", "value": "Ẩn"}
        ]

        current_height_left_col = 0
        current_height_right_col = 0
        vertical_spacing_between_items = 10 

        for i, item in enumerate(info_items):
            full_text = f"{item['label']} {item['value']}"
            item_height = calculate_text_display_height(full_text, detail_font, emoji_detail_font, column_width, line_spacing_multiplier=1.6)
            
            if i % 2 == 0:
                current_height_left_col += item_height + vertical_spacing_between_items
            else:
                current_height_right_col += item_height + vertical_spacing_between_items
        
        info_section_actual_height = max(current_height_left_col, current_height_right_col)
        

        bio_text = user.status if user.status else "Chưa có tiểu sử."
        bio_width = card_width - 2 * info_padding_x
        bio_height = calculate_text_display_height(bio_text, bio_font, emoji_bio_font, bio_width, line_spacing_multiplier=1.4)
        
        status_icons_display = "📱 "
        if user.isActivePC == 1:
            status_icons_display += "💻 "
        if user.isActiveWeb == 1:
            status_icons_display += "🌐 "
        status_icons_display = status_icons_display.strip()
        status_icons_height = calculate_text_display_height(status_icons_display, status_font, emoji_font_status, card_width, line_spacing_multiplier=1.4)

        padding_after_name = 30
        padding_after_info = 30
        padding_after_bio = 15

        total_content_height_in_card = (
            name_pos_y_relative_to_card_top + 
            int(name_font_size * 1.4) + 
            padding_after_name +
            info_section_actual_height + 
            padding_after_info +
            bio_height + 
            padding_after_bio +
            status_icons_height
        )
        
        min_card_height = 600 
        
        card_height = max(min_card_height, total_content_height_in_card)

        avatar_y_center_adjusted = int(initial_header_fixed_height // 2) 
        
        img_height = card_height + 2 * card_margin 
        
        img_width = int(img_width)
        img_height = int(img_height)

        background_canvas = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))

        BACKGROUND_DIR = "background" 
        background_files = [os.path.join(BACKGROUND_DIR, f) for f in os.listdir(BACKGROUND_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if background_files:
            try:
                main_bg_path = random.choice(background_files)
                main_bg_image = Image.open(main_bg_path).convert("RGBA")
                main_bg_image = main_bg_image.resize((img_width, img_height), Image.LANCZOS)
                
                enhancer = ImageEnhance.Brightness(main_bg_image)
                main_bg_image = enhancer.enhance(0.4)

                blurred_bg = main_bg_image.filter(ImageFilter.GaussianBlur(radius=15))
                background_canvas.paste(blurred_bg, (0,0))
                
                overlay_color = (0, 0, 0, 50)
                background_canvas.paste(Image.new("RGBA", (img_width, img_height), overlay_color), (0,0), Image.new("L", (img_width, img_height), 255))

            except Exception as e:
                print(f"Lỗi khi tải hoặc xử lý ảnh nền ngẫu nhiên: {e}. Sử dụng màu đơn sắc.")
                background_canvas.paste(Image.new("RGBA", (img_width, img_height), (50, 50, 50, 255)), (0,0))
        else:
            print("Không tìm thấy ảnh trong thư mục 'background'. Sử dụng màu đơn sắc.")
            background_canvas.paste(Image.new("RGBA", (img_width, img_height), (50, 50, 50, 255)), (0,0))

        main_card = Image.new("RGBA", (card_width, card_height), card_bg_color)
        main_card = add_round_corners(main_card, card_radius)
        
        background_canvas.paste(main_card, (card_margin, card_margin), main_card)
        main_draw = ImageDraw.Draw(background_canvas)

        header_height = initial_header_fixed_height
        
        header_mask = Image.new('L', (card_width, header_height), 0)
        mask_draw = ImageDraw.Draw(header_mask)
        mask_draw.rounded_rectangle((0, 0, card_width, header_height + card_radius), card_radius, fill=255)
        mask_draw.rectangle((0, header_height, card_width, header_height + card_radius), fill=255)

        if fetched_cover_image:
            aspect_ratio_cover = fetched_cover_image.width / fetched_cover_image.height
            if aspect_ratio_cover > card_width / header_height:
                new_width = int(aspect_ratio_cover * header_height)
                processed_cover_image = fetched_cover_image.resize((new_width, header_height), Image.LANCZOS)
                x_offset = int((new_width - card_width) // 2)
                processed_cover_image = processed_cover_image.crop((x_offset, 0, x_offset + card_width, header_height))
            else:
                new_height = int(card_width / aspect_ratio_cover)
                processed_cover_image = fetched_cover_image.resize((card_width, new_height), Image.LANCZOS)
                y_offset = int((new_height - header_height) // 2)
                processed_cover_image = processed_cover_image.crop((0, y_offset, card_width, y_offset + header_height))
            
            processed_cover_image = processed_cover_image.filter(ImageFilter.GaussianBlur(radius=8))
            header_area_img = Image.new("RGBA", (card_width, header_height), (0, 0, 0, 0)) 
            header_area_img.paste(processed_cover_image, (0, 0), processed_cover_image)
            
            gradient_overlay = Image.new('RGBA', (card_width, header_height), (0, 0, 0, 0))
            draw_gradient = ImageDraw.Draw(gradient_overlay)
            for i in range(header_height):
                alpha = int(200 * (i / header_height)**1.5)
                draw_gradient.line([(0, i), (card_width, i)], fill=(0, 0, 0, alpha))
            header_area_img = Image.alpha_composite(header_area_img, gradient_overlay)

        else: 
            header_area_img = Image.new("RGBA", (card_width, header_height), (50, 50, 50, 200))

        header_area_img.putalpha(header_mask)
        background_canvas.paste(header_area_img, (card_margin, card_margin), header_area_img)

        avatar_x_center = card_margin + card_width // 2
        avatar_y = card_margin + avatar_y_center_adjusted 

        if fetched_avatar_image: 
            processed_avatar_image = fetched_avatar_image.resize((avatar_size, avatar_size), Image.LANCZOS)
            mask = Image.new("L", processed_avatar_image.size, 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.ellipse((0, 0, avatar_size, avatar_size), fill=255)
            processed_avatar_image.putalpha(mask)
            
            avatar_with_border = Image.new("RGBA", (avatar_size + 10, avatar_size + 10), (0, 0, 0, 0))
            border_mask = Image.new("L", (avatar_size + 10, avatar_size + 10), 0)
            draw_border = ImageDraw.Draw(border_mask)
            draw_border.ellipse((0, 0, avatar_size + 9, avatar_size + 9), fill=255)
            
            draw_border_fill = ImageDraw.Draw(avatar_with_border)
            draw_border_fill.ellipse((0, 0, avatar_size + 9, avatar_size + 9), fill=(255, 255, 255, 255))
            avatar_with_border.putalpha(border_mask)
            
            avatar_with_border.paste(processed_avatar_image, (5, 5), processed_avatar_image)
            
            background_canvas.paste(avatar_with_border, 
                                    (int(avatar_x_center - (avatar_size + 10) // 2), int(avatar_y - (avatar_size + 10) // 2)), 
                                    avatar_with_border)

        user_display_name = user.displayName
        max_name_width = card_width - 100
        
        name_length = 0
        for char in user_display_name:
            f = emoji_font_name if emoji.emoji_count(char) and emoji_font_name else name_font
            name_length += f.getlength(char)

        while name_length > max_name_width and name_font_size > 30:
            name_font_size -= 5
            name_font = get_safe_font(ARIAL_FONT, name_font_size)
            emoji_font_name = get_safe_font(NOTO_EMOJI_FONT, name_font_size)
            name_length = 0
            for char in user_display_name:
                f = emoji_font_name if emoji.emoji_count(char) and emoji_font_name else name_font
                name_length += f.getlength(char)
            
        name_pos_y_abs = card_margin + name_pos_y_relative_to_card_top
        create_text(main_draw, user_display_name, name_font, emoji_font_name, 
                    (card_margin + card_width // 2, name_pos_y_abs), text_color, max_width=max_name_width, align="center")

        qr_data = client.getQRLink(target_id)
        if qr_data and target_id in qr_data:
            qr_link = qr_data[target_id]
            qr_image = fetch_image(qr_link)
            if qr_image:
                qr_size = 100
                qr_image = qr_image.resize((qr_size, qr_size), Image.LANCZOS)
                qr_image = add_round_corners(qr_image, 10)
                
                qr_pos_x = card_margin + card_width - qr_size - 25
                qr_pos_y = card_margin + 25
                background_canvas.paste(qr_image, (qr_pos_x, qr_pos_y), qr_image)
            else:
                print(f"Cảnh báo: Không thể tải ảnh QR từ {qr_link}. Bỏ qua mã QR.")
        else:
            print(f"Cảnh báo: Không thể lấy link QR cho {target_id}. Bỏ qua mã QR.")

        current_y_for_details = name_pos_y_abs + int(name_font_size * 1.4) + padding_after_name

        current_y_left_col_draw = current_y_for_details
        current_y_right_col_draw = current_y_for_details

        for i, item in enumerate(info_items):
            full_text = f"{item['label']} {item['value']}"
            
            if i % 2 == 0:
                x_pos = card_margin + info_padding_x
                y_pos = current_y_left_col_draw
            else:
                x_pos = card_margin + info_padding_x + column_width + 20
                y_pos = current_y_right_col_draw

            create_text(main_draw, full_text, detail_font, emoji_detail_font, 
                        (x_pos, y_pos), text_color, max_width=column_width, align="left")
            
            item_height = calculate_text_display_height(full_text, detail_font, emoji_detail_font, column_width, line_spacing_multiplier=1.6)
            
            if i % 2 == 0:
                current_y_left_col_draw += item_height + vertical_spacing_between_items
            else:
                current_y_right_col_draw += item_height + vertical_spacing_between_items

        bio_y_start = max(current_y_left_col_draw, current_y_right_col_draw) + padding_after_info
        
        create_text(main_draw, bio_text, bio_font, emoji_bio_font, 
                    (card_margin + card_width // 2, bio_y_start), text_color, 
                    max_width=bio_width, align="center")

        status_pos_y = bio_y_start + bio_height + padding_after_bio
        
        status_text_width = 0
        for char in status_icons_display:
            f = emoji_font_status if emoji.emoji_count(char) and emoji_font_status else status_font
            status_text_width += f.getlength(char)
            
        status_pos_x = card_margin + card_width // 2 - status_text_width // 2

        create_text(main_draw, status_icons_display, status_font, emoji_font_status, 
                    (status_pos_x, status_pos_y), text_color, align="left")


        output_image_path = "modules/cache/info.png"
        os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
        background_canvas.save(output_image_path, quality=95)
        
        user_name = user.displayName
        message_info = f"🚦 {get_user_name_by_id(client, author_id)} profile {user_name} của bạn đây ✅"
        
        client.sendLocalImage(
            imagePath=output_image_path,
            thread_id=thread_id,
            thread_type=thread_type,
            message=Message(text=message_info, mention=Mention(author_id, length=len(f"{get_user_name_by_id(client, author_id)}"), offset=3)),
            height=img_height, 
            width=img_width,
            ttl=6000000
        )
        
    except Exception as e:
        print(f"Lỗi trong lệnh info: {e}")
        import traceback
        traceback.print_exc()
        client.send(
            Message(text=f"Đã xảy ra lỗi khi lấy thông tin người dùng: {str(e)}"),
            thread_id=thread_id,
            thread_type=thread_type
        )
    finally:
        if 'output_image_path' in locals() and os.path.exists(output_image_path):
            os.remove(output_image_path)

def PTA():
    return {
        'info': info
    }