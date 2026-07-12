import time
import os
import random
from PIL import Image, ImageDraw, ImageFont
from zlapi.models import Message, Mention
from config import PREFIX

des = {
    'version': "1.0.2",
    'credits': "ngbao",
    'description': "Xem thời gian bot hoạt động",
    'power': "Thành viên"
}

start_time = time.time()

def create_gradient_colors(num_colors=None):
    if num_colors is None:
        num_colors = random.randint(0, 300)
    colors = []
    for _ in range(num_colors):
        colors.append((
            random.randint(0, 300),
            random.randint(0, 300),
            random.randint(0, 300)
        ))
    return colors

def interpolate_colors(colors, text_length, change_every):
    gradient = []
    num_segments = len(colors) - 1
    steps_per_segment = (text_length // change_every) + 1

    for i in range(num_segments):
        for j in range(steps_per_segment):
            if len(gradient) < text_length:
                ratio = j / steps_per_segment
                interpolated_color = (
                    int(colors[i][0] * (1 - ratio) + colors[i + 1][0] * ratio),
                    int(colors[i][1] * (1 - ratio) + colors[i + 1][1] * ratio),
                    int(colors[i][2] * (1 - ratio) + colors[i + 1][2] * ratio)
                )
                gradient.append(interpolated_color)

    while len(gradient) < text_length:
        gradient.append(colors[-1])

    return gradient[:text_length]

def draw_text(draw, text, position, font, gradient_fill):
    x, y = position
    shadow_offset = 2
    for index, char in enumerate(text):
        shadow_color = (0, 0, 0)
        draw.text((x + shadow_offset, y + shadow_offset), char, fill=shadow_color, font=font)
        draw.text((x, y), char, fill=gradient_fill[index], font=font)
        x += draw.textbbox((0, 0), char, font=font)[2] - draw.textbbox((0, 0), char, font=font)[0]

def handle_uptime_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        current_time = time.time()
        uptime_seconds = int(current_time - start_time)

        days = uptime_seconds // (24 * 3600)
        uptime_seconds %= (24 * 3600)
        hours = uptime_seconds // 3600
        uptime_seconds %= 3600
        minutes = uptime_seconds // 60
        seconds = uptime_seconds % 60

        line_1 = "THỜI GIAN BOT ĐÃ ONLINE"
        line_2 = f"{days} Ngày {hours} Giờ {minutes} Phút {seconds} Giây"
        image_folder = "modules/cache/image"
        output_path = "modules/cache/temp_image_with_uptime.jpg"

        image_files = [f for f in os.listdir(image_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if not image_files:
            raise Exception("Không có ảnh nào trong thư mục.")

        random_image = random.choice(image_files)
        image_path = os.path.join(image_folder, random_image)

        image = Image.open(image_path)
        draw = ImageDraw.Draw(image)

        font_path = "modules/cache/font/BeVietnamPro-Bold.ttf"
        font_small = ImageFont.truetype(font_path, size=48)
        font_large = ImageFont.truetype(font_path, size=78)
        image_width, image_height = image.size

        bbox_1 = draw.textbbox((0, 0), line_1, font=font_small)
        text_width_1 = bbox_1[2] - bbox_1[0]

        bbox_2 = draw.textbbox((0, 0), line_2, font=font_large)
        text_width_2 = bbox_2[2] - bbox_2[0]

        x1 = (image_width - text_width_1) // 2
        y1 = 40

        x2 = (image_width - text_width_2) // 2
        y2 = (image_height - (bbox_2[3] - bbox_2[1])) // 2

        gradient_colors_1 = create_gradient_colors()
        gradient_colors_2 = create_gradient_colors()
        gradient_1_fill = interpolate_colors(gradient_colors_1, len(line_1), change_every=1)
        gradient_2_fill = interpolate_colors(gradient_colors_2, len(line_2), change_every=1)

        draw_text(draw, line_1, (x1, y1), font_small, gradient_1_fill)
        draw_text(draw, line_2, (x2, y2), font_large, gradient_2_fill)

        image.save(output_path)
        if os.path.exists(output_path):
            client.sendLocalImage(
                output_path,
                message=Message(text="@Member", mention=Mention(author_id, length=len("@Member"), offset=0)),
                thread_id=thread_id,
                thread_type=thread_type,
                width=1280,
                height=758,
            )
            os.remove(output_path)

    except Exception as e:
        mention = Mention(author_id, length=len("@Member"), offset=0)
        error_message = Message(text=f"Đã xảy ra lỗi: {str(e)}", mention=mention)
        client.sendMessage(error_message, thread_id, thread_type)

def PTA():
    return {
        'uptime': handle_uptime_command
    }
