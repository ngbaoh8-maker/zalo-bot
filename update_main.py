import re

def update_file():
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add get_member_cover_url
    avatar_func = '''def get_member_avatar_url(self, member_id, member_data=None):
    if isinstance(member_data, dict):
        avatar = member_data.get("avatar") or member_data.get("avatarUrl") or member_data.get("avatar_url") or ""
        if avatar:
            return avatar

    if not member_id:
        return ""

    try:
        info = self.fetchUserInfo(member_id)
        changed_profiles = getattr(info, "changed_profiles", None)
        if isinstance(info, dict):
            changed_profiles = info.get("changed_profiles", changed_profiles)

        if isinstance(changed_profiles, dict):
            for key in (member_id, str(member_id)):
                profile = changed_profiles.get(key)
                if isinstance(profile, dict):
                    avatar = profile.get("avatarUrl") or profile.get("avatar") or profile.get("avatar_url") or ""
                else:
                    avatar = getattr(profile, "avatarUrl", "") or getattr(profile, "avatar", "") or ""
                if avatar:
                    return avatar
    except Exception:
        pass

    return ""'''
    
    cover_func = '''def get_member_cover_url(self, member_id, member_data=None):
    if isinstance(member_data, dict):
        cover = member_data.get("cover") or member_data.get("coverUrl") or member_data.get("cover_url") or ""
        if cover:
            return cover

    if not member_id:
        return ""

    try:
        info = self.fetchUserInfo(member_id)
        changed_profiles = getattr(info, "changed_profiles", None)
        if isinstance(info, dict):
            changed_profiles = info.get("changed_profiles", changed_profiles)

        if isinstance(changed_profiles, dict):
            for key in (member_id, str(member_id)):
                profile = changed_profiles.get(key)
                if isinstance(profile, dict):
                    cover = profile.get("coverUrl") or profile.get("cover") or profile.get("cover_url") or ""
                else:
                    cover = getattr(profile, "coverUrl", "") or getattr(profile, "cover", "") or ""
                if cover:
                    return cover
    except Exception:
        pass

    return ""'''

    if avatar_func in content:
        content = content.replace(avatar_func, avatar_func + '\n\n\n' + cover_func)
    else:
        print("Could not find get_member_avatar_url")
        return

    # 2. Replace create_event_card
    start_card = 'def create_event_card('
    end_card = 'return out_path'
    
    pattern_card = r'def create_event_card\(.*?return out_path'
    
    new_card = '''def create_event_card(member_name, member_avatar_url, member_cover_url, bot_avatar_url, group_name, group_cover_url, event_type):
    width, height = 960, 320
    c1, c2 = random.choice(EVENT_PALETTES)

    bg_url = member_cover_url if member_cover_url else member_avatar_url
    member_bg = download_image(bg_url)
    if member_bg:
        background = ImageOps.fit(
            member_bg.convert("RGBA"),
            (width, height),
            method=Image.LANCZOS,
            centering=(0.5, 0.42)
        )
        background = background.filter(ImageFilter.GaussianBlur(radius=5))
        background = ImageEnhance.Brightness(background).enhance(0.5)
    else:
        background = create_gradient_overlay(width, height, c1, c2, alpha=255)

    draw = ImageDraw.Draw(background)
    draw.rounded_rectangle(
        (10, 10, width - 10, height - 10),
        radius=20,
        outline=(255, 255, 255, 200),
        width=4
    )

    avatar_size = 140
    left_x = 50
    right_x = width - avatar_size - 50
    avatar_y = (height - avatar_size) // 2

    member_img = download_image(member_avatar_url)
    if not member_img:
        member_img = Image.new("RGBA", (avatar_size, avatar_size), (*c1, 255))
    member_avatar = make_round_avatar(member_img, avatar_size)
    background.paste(member_avatar, (left_x, avatar_y), member_avatar)
    draw.ellipse((left_x - 3, avatar_y - 3, left_x + avatar_size + 3, avatar_y + avatar_size + 3), outline=(255, 255, 255, 200), width=4)

    bot_img = download_image(bot_avatar_url)
    if not bot_img:
        bot_img = Image.new("RGBA", (avatar_size, avatar_size), (*c2, 255))
    bot_avatar = make_round_avatar(bot_img, avatar_size)
    background.paste(bot_avatar, (right_x, avatar_y), bot_avatar)
    draw.ellipse((right_x - 3, avatar_y - 3, right_x + avatar_size + 3, avatar_y + avatar_size + 3), outline=(255, 255, 255, 200), width=4)

    if event_type == "JOIN":
        label = "CHÀO MỪNG"
        greeting = random.choice(WELCOME_TEXTS)
        accent = (0, 235, 190, 255)
    elif event_type == "LEAVE":
        label = "TẠM BIỆT"
        greeting = random.choice(GOODBYE_TEXTS)
        accent = (255, 120, 120, 255)
    else:
        label = "KICK"
        greeting = random.choice(KICK_TEXTS)
        accent = (255, 80, 80, 255)

    center_x = width // 2
    max_text_width = right_x - (left_x + avatar_size) - 40

    font_label = fit_font(draw, label, max_text_width, 36, "BeVietnamPro-Bold.ttf", bold=True)
    font_name = fit_font(draw, member_name, max_text_width, 42, "BeVietnamPro-Bold.ttf", bold=True)
    font_greeting = fit_font(draw, greeting, max_text_width, 24, "BeVietnamPro-SemiBold.ttf", bold=False)

    def draw_center_text(text, font, y, fill, shadow=(0, 0, 0, 200)):
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        x = center_x - text_w // 2
        draw.text((x + 2, y + 2), text, font=font, fill=shadow)
        draw.text((x, y), text, font=font, fill=fill)
        return bbox[3] - bbox[1]

    spacing = 15
    h_label = draw.textbbox((0, 0), label, font=font_label)[3] - draw.textbbox((0, 0), label, font=font_label)[1]
    h_name = draw.textbbox((0, 0), member_name, font=font_name)[3] - draw.textbbox((0, 0), member_name, font=font_name)[1]
    h_greeting = draw.textbbox((0, 0), greeting, font=font_greeting)[3] - draw.textbbox((0, 0), greeting, font=font_greeting)[1]

    total_text_height = h_label + h_name + h_greeting + (spacing * 2)
    start_y = (height - total_text_height) // 2

    cur_y = start_y
    draw_center_text(label, font_label, cur_y, accent)
    cur_y += h_label + spacing
    
    draw_center_text(member_name, font_name, cur_y, (255, 255, 255, 255))
    cur_y += h_name + spacing

    draw_center_text(greeting, font_greeting, cur_y, (225, 230, 240, 255))

    time_str = datetime.now().strftime("%H:%M %d/%m/%Y")
    time_font = get_font("BeVietnamPro-SemiBold.ttf", 14, bold=False)
    time_bbox = draw.textbbox((0, 0), time_str, font=time_font)
    draw.text((width - (time_bbox[2] - time_bbox[0]) - 20, height - 30), time_str, font=time_font, fill=(255, 255, 255, 180))

    os.makedirs("temp_images", exist_ok=True)
    out_path = os.path.join("temp_images", f"welcome_{random.randint(1000, 9999)}.png")
    background.convert("RGB").save(out_path, quality=95)
    return out_path'''

    content = re.sub(pattern_card, new_card, content, flags=re.DOTALL)
    
    # 3. send_event_image
    old_send = '''def send_event_image(self, member_id, member_name, member_avatar, group_id, group_name, event_type):
    try:
        bot_avatar = get_bot_avatar_url(self)
        image_path = create_event_card(member_name, member_avatar, bot_avatar, group_name, None, event_type)'''
    
    new_send = '''def send_event_image(self, member_id, member_name, member_avatar, member_cover, group_id, group_name, event_type):
    try:
        bot_avatar = get_bot_avatar_url(self)
        image_path = create_event_card(member_name, member_avatar, member_cover, bot_avatar, group_name, None, event_type)'''
        
    content = content.replace(old_send, new_send)

    # 4. handleGroupEvent
    # For JOIN
    old_join = '''            member_avatar = get_member_avatar_url(self, member_id, member)

            def _send(mid=member_id, mname=member_name, mavt=member_avatar):
                send_event_image(self, mid, mname, mavt, group_id, group_name, "JOIN")'''
    new_join = '''            member_avatar = get_member_avatar_url(self, member_id, member)
            member_cover = get_member_cover_url(self, member_id, member)

            def _send(mid=member_id, mname=member_name, mavt=member_avatar, mcov=member_cover):
                send_event_image(self, mid, mname, mavt, mcov, group_id, group_name, "JOIN")'''
    content = content.replace(old_join, new_join)

    # For LEAVE
    old_leave = '''        member_avatar = get_member_avatar_url(self, member_id, member)

        def _send(mid=member_id, mname=member_name, mavt=member_avatar):
            send_event_image(self, mid, mname, mavt, group_id, group_name, "LEAVE")'''
    new_leave = '''        member_avatar = get_member_avatar_url(self, member_id, member)
        member_cover = get_member_cover_url(self, member_id, member)

        def _send(mid=member_id, mname=member_name, mavt=member_avatar, mcov=member_cover):
            send_event_image(self, mid, mname, mavt, mcov, group_id, group_name, "LEAVE")'''
    content = content.replace(old_leave, new_leave)

    # For KICK
    old_kick = '''        member_avatar = get_member_avatar_url(self, member_id, member)

        def _send(mid=member_id, mname=member_name, mavt=member_avatar):
            send_event_image(self, mid, mname, mavt, group_id, group_name, "KICK")'''
    new_kick = '''        member_avatar = get_member_avatar_url(self, member_id, member)
        member_cover = get_member_cover_url(self, member_id, member)

        def _send(mid=member_id, mname=member_name, mavt=member_avatar, mcov=member_cover):
            send_event_image(self, mid, mname, mavt, mcov, group_id, group_name, "KICK")'''
    content = content.replace(old_kick, new_kick)
    
    # 5. Remove sticker logic
    sticker_logic = '''                        # ===== GỬI STICKER (ĐỌC TỪ FILE) =====
                        try:
                            stickers = self.load_tag_stickers()
                            if stickers:
                                sticker = random.choice(stickers)
                                self.sendSticker(
                                    1,
                                    sticker["id"],
                                    sticker["catId"],
                                    thread_id,
                                    thread_type
                                )
                        except Exception as e:
                            print(f"[TAG-STICKER] Lỗi gửi sticker: {e}")'''
    content = content.replace(sticker_logic, '# Đã xóa tự động gửi sticker khi tag')
    
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
        
    print("Done")

if __name__ == "__main__":
    update_file()
