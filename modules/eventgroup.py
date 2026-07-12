from zlapi.models import Message, ThreadType, GroupEventType
import json
import os
import time
from zlapi import *
from zlapi.models import *
from io import BytesIO
import os
import string
import random
# from config import SETTING_FILE
from PIL import Image, ImageDraw, ImageFont, ImageOps
import emoji
import requests
import threading
des = {"version": "1.0.2", "credits": "ngbao", "description": "welcomeImg"}


def delete_file(file_path):
    """Xóa tệp sau khi sử dụng."""
    try:
        os.remove(file_path)
        print(f"Đã xóa tệp: {file_path}")
    except Exception as e:
        print(f"Lỗi khi xóa tệp: {e}")
        
def create_gradient_colors(num_colors):
    colors = []
    for _ in range(num_colors):
        colors.append((random.randint(30, 255), random.randint(30, 255), random.randint(30, 255)))
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


def create_text(draw, text, font, emoji_font, text_position, gradient_colors):
    gradient = interpolate_colors(gradient_colors, text_length=len(text), change_every=4) 
    current_x = text_position[0]
    
    for i in range(len(text)):
        char = text[i]
        
        if is_emoji(char):
            color = tuple(gradient[i]) 
            draw.text((current_x, text_position[1]), char, fill=color, font=emoji_font)  
            text_bbox = draw.textbbox((current_x, text_position[1]), char, font=emoji_font)  
        else:
            color = tuple(gradient[i]) 
            draw.text((current_x, text_position[1]), char, fill=color, font=font) 
            text_bbox = draw.textbbox((current_x, text_position[1]), char, font=font)  
        
        text_width = text_bbox[2] - text_bbox[0]
        current_x += text_width



def draw_gradient_border(draw, center_x, center_y, radius, border_thickness, gradient_colors):
    num_segments = 80
    gradient = interpolate_colors(gradient_colors, num_segments, change_every=10)  

    for i in range(num_segments):
        start_angle = i * (360 / num_segments)
        end_angle = (i + 1) * (360 / num_segments)

        color = tuple(gradient[i])
        draw.arc(
            [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
            start=start_angle, end=end_angle, fill=color, width=border_thickness
        )


def is_emoji(character):
    return character in emoji.EMOJI_DATA


def load_image_from_url(url):
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    return img


def generate_short_filename(length=10):
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    filename = f"{random_string}"
    return filename



font_dir = "modules/cache/font/"
font_path_main = os.path.join(font_dir, "UTM AvoBold.ttf")
font_path_emoji = os.path.join(font_dir, "NotoEmoji-Bold.ttf")
font_path_arial = os.path.join(font_dir, "arial.ttf")



def create_banner(client, member_id, member_name, total_member, group_name, avatar_url, ow_name, t=1):
    print("create...")
    #member_info = bot.fetchUserInfo(uid).changed_profiles[uid]
    #avatar_url = f'{avatar_url}'
    member_info = client.fetchUserInfo(member_id).changed_profiles[member_id]
    avatar_url =member_info.avatar
    user_name = f'{member_name}'
    notification_icon= total_member#"soiz" #int(client.group_info_cache[thread_id]['total_member'])
    if t==1:
        main_text=f'Chào mừng, {user_name}💜'
        additional_texts=[f"Đã tham gia nhóm {group_name}", "                                          convert by ©Soiz"]#xoá cre làm choá :)))
    elif t ==2:
        main_text=f'Tạm biệt, {user_name}💔'
        additional_texts=[f"Đã rời nhóm {group_name}", "                                          convert by ©Soiz"]#có phải anh chiều em quá nên em hư đúng không 
    else:
        main_text=f' Thằng oắt con {user_name}💢'
        additional_texts=[f"đã bị {ow_name} sút khỏi nhóm {group_name}", "                                          convert by ©Soiz"]#thôi được rồi -)))

    banner_width = 1000
    banner_height = 300
    border_thickness = 12 
    
    background_color = (random.randint(0, 40), random.randint(0, 40), random.randint(0, 40 ))
    
    banner = Image.new('RGB', (banner_width, banner_height), background_color)
    
 
    avatar = load_image_from_url(avatar_url).convert("RGBA")
    avatar = avatar.resize((200, 200), Image.LANCZOS)
    
    mask = Image.new("L", avatar.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, 200, 200), fill=255)
    avatar = Image.composite(avatar, Image.new("RGBA", avatar.size), mask)

    avatar_x = 40
    avatar_y = (banner_height - avatar.height) // 2
    

    gradient_colors = create_gradient_colors(10)


    draw_banner = ImageDraw.Draw(banner)
    radius = 100 + border_thickness // 2
    draw_gradient_border(draw_banner, avatar_x + 100, avatar_y + 100, radius, border_thickness, gradient_colors)
    
    banner.paste(avatar, (avatar_x, avatar_y), avatar)

    draw = ImageDraw.Draw(banner)

    if not any("Soiz" in word for text in additional_texts for word in text.split()) or notification_icon == "soiz":
        main_text = "⚠️ WARNING ⚠️"
        additional_texts = base64.b64decode('VGVycmlibGUuLi4gU28gZGlzYXBwb2ludGluZyEgV2h5IGRpZCB5b3UgcmVtb3ZlIHRoZSBhdXRob3IncyBjb3B5cmlnaHQ/IENow7pjIG3hu6tuZyBi4bqhbiDEkcOjIHF1YXkgdsOgbyDDtCBiw7NwIHrDoWkga2tr').decode("utf-8").split(' ')#Đến được đây thì em xin lỗi tiền bối kkkk, badwords nên che )))
    padding_left = 30  
    padding_right = 0  
    main_text_position_x = avatar_x + avatar.width + padding_left
    max_text_width = banner_width - main_text_position_x - padding_right 

   
    font_size = 120
    main_font = ImageFont.truetype(font_path_main, font_size)


    while True:
        main_text_bbox = draw.textbbox((0, 0), main_text, font=main_font)
        main_text_width = main_text_bbox[2] - main_text_bbox[0]

        if main_text_width <= max_text_width: 
            break
        font_size -= 1  
        main_font = ImageFont.truetype(font_path_main, font_size)

   
    main_text_height = main_text_bbox[3] - main_text_bbox[1]
    main_text_position = (main_text_position_x, avatar_y-20)


    emoji_font = ImageFont.truetype(font_path_emoji, font_size)

    main_gradient_colors = create_gradient_colors(5)
    create_text(draw, main_text, main_font, emoji_font,main_text_position, main_gradient_colors)


    additional_y_offset = 30
    remaining_height = banner_height - (main_text_position[1] + main_text_height + 20) 
    num_additional_texts = len(additional_texts)


    max_text_width = banner_width - 100 - main_text_position[0]

    for i, additional_text in enumerate(additional_texts):
        additional_font_size = 50
        additional_font = ImageFont.truetype(font_path_arial , additional_font_size)


        while True:
            additional_text_bbox = draw.textbbox((0, 0), additional_text, font=additional_font)
            additional_text_width = additional_text_bbox[2] - additional_text_bbox[0]
            additional_text_height = additional_text_bbox[3] - additional_text_bbox[1]

            if additional_text_width <= max_text_width and additional_text_height * num_additional_texts <= remaining_height:
                break
            additional_font_size -= 1
            additional_font = ImageFont.truetype(font_path_arial , additional_font_size)
        emoji_font = ImageFont.truetype(font_path_emoji, additional_font_size)

        if i == 0:
            additional_text_position = (main_text_position[0], main_text_position[1] + main_text_height + additional_y_offset)
        else:
            additional_text_position = (main_text_position[0], main_text_position[1] +70+ main_text_height + additional_y_offset + i * additional_y_offset)

        
    
        additional_gradient_colors = create_gradient_colors(10)
        
        if i == 0:
            create_text(draw, additional_text, additional_font, emoji_font, additional_text_position, additional_gradient_colors)
        else:
            create_text(draw, additional_text, ImageFont.truetype(font_path_arial , additional_font_size-18), ImageFont.truetype(font_path_emoji, additional_font_size-18), additional_text_position, additional_gradient_colors)


    if notification_icon is not None:
      
        notification_position = (avatar_x + 150, avatar_y + 10)


        notification_font_size = 30 
        notification_font = ImageFont.truetype(font_path_main, notification_font_size)


        notification_text = str(notification_icon)
        notification_text_bbox = draw.textbbox((0, 0), notification_text, font=notification_font)
        notification_text_width = notification_text_bbox[2] - notification_text_bbox[0]
        notification_text_height = notification_text_bbox[3] - notification_text_bbox[1]

     
        circle_radius = 35  
        while notification_text_width > 3 * circle_radius or notification_text_height > 3 * circle_radius:
            notification_font_size -= 2 
            notification_font = ImageFont.truetype(font_path_main, notification_font_size)

      
            notification_text_bbox = draw.textbbox((0, 0), notification_text, font=notification_font)
            notification_text_width = notification_text_bbox[2] - notification_text_bbox[0]
            notification_text_height = notification_text_bbox[3] - notification_text_bbox[1]


        if t==1:
            random_background_color = (30,144,255)
        else:
            random_background_color = (255, 0, 0) 


        circle_bbox = [
            notification_position[0] - circle_radius, notification_position[1] - circle_radius,
            notification_position[0] + circle_radius, notification_position[1] + circle_radius
        ]
        draw.ellipse(circle_bbox, fill=random_background_color)

 
        circle_center_x = (circle_bbox[0] + circle_bbox[2]) // 2
        circle_center_y = (circle_bbox[1] + circle_bbox[3]) // 2


        centered_position = (
            circle_center_x - notification_text_width // 2,
            circle_center_y - notification_text_height
        )


        draw.text(centered_position, notification_text, font=notification_font, fill=(255, 255, 255))

    file_name = f"banner_{generate_short_filename()}.jpeg"
    banner.save(file_name)
    return file_name

def handle_event(client, event_data, event_type):
    """Xử lý sự kiện nhóm."""
    try:
        if not hasattr(event_data, 'groupId'):
            return

        thread_id = str(event_data.groupId)
        thread_type = ThreadType.GROUP
        
        group_info = client.fetchGroupInfo(thread_id)
        if not group_info or not hasattr(group_info, 'gridInfoMap'):
            return
            
        group_data = group_info.gridInfoMap.get(thread_id)
        if not group_data:
            return
            
        group_name = getattr(group_data, 'name', 'nhóm')
        total_member = getattr(group_data, 'totalMember', '0')
        
        ow_id = str(event_data.sourceId)
        ow_name = "Người dùng"
        try:
            ow_info = client.fetchUserInfo(ow_id)
            if ow_info and hasattr(ow_info, 'changed_profiles') and ow_info.changed_profiles:
                p = ow_info.changed_profiles.get(ow_id)
                if p:
                    ow_name = getattr(p, 'displayName', ow_name)
        except:
            pass

        if not hasattr(event_data, 'updateMembers') or not event_data.updateMembers:
            return

        for member in event_data.updateMembers:
            member_id = str(member.get('id'))
            member_name = member.get('dName', 'Người dùng')
            
            avatar_url = ""
            try:
                user_info = client.fetchUserInfo(member_id)
                if user_info and hasattr(user_info, 'changed_profiles') and user_info.changed_profiles:
                    p = user_info.changed_profiles.get(member_id)
                    if p:
                        avatar_url = getattr(p, 'avatar', '')
            except:
                pass

            if event_type == GroupEventType.JOIN:
                banner_path = create_banner(client, member_id, member_name, total_member, group_name, avatar_url, ow_name, 1)
                msg = f"🎉 Chào mừng {member_name} đã gia nhập {group_name.upper()}! 🎉"
                mention = Mention(uid=member_id, length=len(member_name), offset=len("🎉 Chào mừng "))
                try:
                    client.sendLocalImage(banner_path, thread_id=thread_id, thread_type=thread_type, width=1000, height=300, message=Message(text=msg, mention=mention), ttl=60000 * 60)
                    delete_file(banner_path)
                except Exception as e:
                    logger.error(f"Lỗi gửi ảnh chào mừng: {e}")
                    
            elif event_type == GroupEventType.LEAVE:
                banner_path = create_banner(client, member_id, member_name, total_member, group_name, avatar_url, ow_name, 2)
                msg = Message(text=f"💔 Chào tạm biệt {member_name} 🤧")
                try:
                    client.sendLocalImage(banner_path, thread_id=thread_id, thread_type=thread_type, width=1000, height=300, message=msg, ttl=60000 * 60)
                    delete_file(banner_path)
                except Exception as e:
                    logger.error(f"Lỗi gửi ảnh tạm biệt: {e}")
                    
            elif event_type == GroupEventType.REMOVE_MEMBER:
                banner_path = create_banner(client, member_id, member_name, total_member, group_name, avatar_url, ow_name, 3)
                msg = Message(text=f"Thằng oắt con {member_name}\nVừa bị {ow_name.upper()} sút khỏi nhóm {group_name.upper()}")
                try:
                    client.sendLocalImage(banner_path, thread_id=thread_id, thread_type=thread_type, width=1234, height=345, message=msg, ttl=60000 * 60)
                    delete_file(banner_path)
                except Exception as e:
                    logger.error(f"Lỗi gửi ảnh kickout: {e}")
                    
            elif event_type == GroupEventType.ADD_ADMIN:
                msg = Message(text=f'Chúc mừng {member_name} đã được {ow_name} bổ nhiệm làm quản trị viên của nhóm {group_name.upper()}')
                client.sendMessage(msg, thread_id, thread_type, mark_message='important', ttl=60000*69)
                
            elif event_type == GroupEventType.REMOVE_ADMIN:
                msg = Message(text=f'Chúc mừng {member_name} đã bị {ow_name} cắt chức -))) ')
                client.sendMessage(msg, thread_id, thread_type, mark_message='important', ttl=60000*69)
                
            elif event_type == GroupEventType.UPDATE:
                msg = Message(text=f'Quản trị viên {ow_name} đã cập nhật mô tả của nhóm {group_name.upper()}')
                client.sendMessage(msg, thread_id, thread_type, mark_message='important', ttl=60000*69)

    except Exception as e:
        logger.error(f"Lỗi khi xử lý event: {e}")
        
def get_mitaizl():
    return{}
