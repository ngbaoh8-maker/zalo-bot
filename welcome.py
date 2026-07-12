from zlapi import ZaloAPI, ZaloAPIException
from zlapi.models import *
from zlapi.models import Message, Mention
from threading import Thread
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import os
import random
import logging

des = {
    'version': "1.0.1",
    'credits': "Tân Xuân Hoàng",
    'description': "Gửi video ngẫu nhiên từ danh sách JSON"
}

logging.basicConfig(level=logging.ERROR, filename="bot_error.log", filemode="a", 
                    format="%(asctime)s - %(levelname)s - %(message)s")

def create_black_background(width, height):
    return Image.new("RGB", (width, height), (0, 0, 0))

def create_gradient_colors(num_colors):
    colors = []
    for _ in range(num_colors):
        colors.append((random.randint(100, 175), random.randint(100, 180), random.randint(100, 170)))
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

def make_round_avatar(avatar):
    avatar_size = avatar.size
    avatar_mask = Image.new("L", avatar_size, 0)
    avatar_draw = ImageDraw.Draw(avatar_mask)
    avatar_draw.ellipse((0, 0, avatar_size[0], avatar_size[0]), fill=255)

    round_avatar = Image.new("RGBA", avatar_size, (255, 255, 255, 0))
    round_avatar.paste(avatar, (0, 0), avatar_mask)
    return round_avatar

def adjust_font_size(draw, text, max_width, font_path, initial_size):
    font_size = initial_size
    font = ImageFont.truetype(font_path, font_size)
    text_width = draw.textbbox((0, 0), text, font=font)[2]
    while text_width > max_width and font_size > 5:
        font_size -= 1
        font = ImageFont.truetype(font_path, font_size)
        text_width = draw.textbbox((0, 0), text, font=font)[2]
    return font

def draw_gradient_text(draw, text, position, font, gradient_colors):
    gradient = interpolate_colors(gradient_colors, text_length=len(text), change_every=4)
    x, y = position
    for i in range(len(text)):
        char = text[i]
        char_color = tuple(gradient[i])
        draw.text((x, y), char, font=font, fill=char_color)
        char_width = draw.textbbox((0, 0), char, font=font)[2]
        x += char_width

def create_welcome_or_farewell_image(group_name, member_name, avatar_url, event_type):
    background = create_black_background(736, 282)
    draw = ImageDraw.Draw(background)

    avatar_response = requests.get(avatar_url)
    avatar_response.raise_for_status()
    avatar = Image.open(BytesIO(avatar_response.content)).convert("RGBA")
    avatar = avatar.resize((150, 150), Image.LANCZOS)
    round_avatar = make_round_avatar(avatar)
    avatar_x = 30
    avatar_y = (background.height - round_avatar.height) // 2
    background.paste(round_avatar, (avatar_x, avatar_y), round_avatar)

    line_x = avatar_x + round_avatar.width + 25
    draw.line([(line_x, avatar_y - 40), (line_x, avatar_y + round_avatar.height + 40)], fill="white", width=4)

    if event_type == "JOIN":
        text_group = f"Welcome To Group | {group_name}"        
        text_member = f"Welcome, {member_name} Đã Join Group"
    elif event_type == "LEAVE":
        text_group = f"Godbye {member_name} Đã Rời Khỏi Nhóm"
        text_member = f"Goodbye {member_name} Đã Rời Khỏi Nhóm"
    elif event_type == "REMOVE_MEMBER":
        text_group = f"Kicked {member_name} Group | {group_name}"
        text_member = f"{member_name} Đã Bị Kick Khỏi Group"

    font_path_group = "font/2.ttf"
    font_path_member = "font/3.ttf"

    max_text_width = background.width - round_avatar.width - 150
    font_group = adjust_font_size(draw, text_group, max_width=max_text_width, font_path=font_path_group, initial_size=33)
    font_member = adjust_font_size(draw, text_member, max_width=max_text_width, font_path=font_path_member, initial_size=29)

    text_group_y = (background.height - 150) // 2 + 66
    text_member_y = text_group_y - 30

    gradient_colors = create_gradient_colors(500)
    draw_gradient_text(draw, text_group, position=(225, text_group_y), font=font_group, gradient_colors=gradient_colors)
    draw_gradient_text(draw, text_member, position=(225, text_member_y), font=font_member, gradient_colors=gradient_colors)

    image_path = "welcome_or_farewell.jpg"
    background.save(image_path)
    return image_path

def delete_file(file_path):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Đã xóa file: {file_path}")
        else:
            print(f"Không tìm thấy file: {file_path}")
    except Exception as e:
        logging.error(f"Lỗi khi xóa file {file_path}: {e}")

def welcome(self, event_data, event_type, ttl=3600000):
    def send():
        if event_type == GroupEventType.UNKNOWN:
            return

        thread_id = event_data['groupId']
        group_info = self.fetchGroupInfo(thread_id)
        if not group_info or 'gridInfoMap' not in group_info or thread_id not in group_info.gridInfoMap:
            print(f"Không thể lấy thông tin nhóm cho thread_id: {thread_id}")
            return

        group_name = group_info.gridInfoMap[thread_id]['name']

        if event_type == GroupEventType.JOIN:
            for member in event_data.updateMembers:
                member_name = member['dName']
                avatar_url = member.get('avatar', '')
                user_id = member.get('uid', '')
                total_members = member.get('totalMember', '')  # Lấy UID của thành viên

                # Tạo ảnh chào mừng
                welcome_image_path = create_welcome_or_farewell_image(group_name, member_name, avatar_url, "JOIN")

                # Tạo nội dung tin nhắn với emoji
                message = Message(text=f"[𝚆𝙴𝙻𝙲𝙾𝙼𝙴 𝚃𝙾] : {group_name}")

                # Gửi tin nhắn và đính kèm ảnh chào mừng
                self.sendLocalImage(
                    welcome_image_path, 
                    thread_id, 
                    ThreadType.GROUP, 
                    message=message, 
                    width=600, 
                    height=225, 
                    ttl=250000
                )
                delete_file(welcome_image_path)

        elif event_type == GroupEventType.LEAVE:
            for member in event_data.updateMembers:
                member_name = member['dName']
                avatar_url = member.get('avatar', '')
                user_id = member.get('uid', '')

                # Tạo ảnh tạm biệt
                farewell_image_path = create_welcome_or_farewell_image(group_name, member_name, avatar_url, "LEAVE")

                # Tạo nội dung tin nhắn với emoji
                message = Message(text=f""""[𝙶𝙾𝙳 𝙱𝚈𝙴] : {member_name}💌""")

                # Gửi ảnh tạm biệt
                self.sendLocalImage(
                    farewell_image_path, 
                    thread_id, 
                    ThreadType.GROUP, 
                    message=message, 
                    width=600, 
                    height=225, 
                    ttl=250000
                )
                delete_file(farewell_image_path)

        elif event_type == GroupEventType.REMOVE_MEMBER:
            for member in event_data.updateMembers:
                member_name = member['dName']
                avatar_url = member.get('avatar', '')
                user_id = member.get('uid', '')

                # Tạo ảnh bị kick
                kick_image_path = create_welcome_or_farewell_image(group_name, member_name, avatar_url, "REMOVE_MEMBER")

                # Tạo nội dung tin nhắn với emoji
                message = Message(text=f"""[𝙺𝙸𝙲𝙺𝙴𝙳]
 : {member_name}""")

                # Gửi ảnh thông báo kick
                self.sendLocalImage(
                    kick_image_path, 
                    thread_id, 
                    ThreadType.GROUP, 
                    message=message, 
                    width=600, 
                    height=225, 
                    ttl=250000
                )
                delete_file(kick_image_path)

    thread = Thread(target=send)
    thread.daemon = True
    thread.start()

def PTA():
    return {
        'wc': None  # Bỏ qua admin kiểm tra
    }