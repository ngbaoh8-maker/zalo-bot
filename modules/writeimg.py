# -*- coding: utf-8 -*-
import os
from PIL import Image, ImageDraw
from zlapi.models import Message
from modules.menu import get_font, autosave, get_bg_image
import textwrap

des = {
    'version': "1.0.5",
    'credits': "ngbao",
    'description': "Văn bản lên ảnh",
    'power': "Thành viên"
}

BG_DIR = "modules/cache/backgrounds"
CACHE_BG = os.path.join(BG_DIR, "bg.png")

def write_text_on_image(message, message_object, thread_id, thread_type, author_id, client):
    TTL = 60000  # 60 giây
    try:
        text = ""
        if message_object is not None:
            text = getattr(message_object, "text", "") or getattr(message_object, "content", "")
        if not isinstance(text, str) or len(text.strip()) == 0:
            client.replyMessage(Message("⚠️ Vui lòng nhập nội dung để viết lên ảnh!"), message_object, thread_id, thread_type, ttl=TTL)
            return

        parts = text.strip().split()
        if len(parts) > 1:
            text = " ".join(parts[1:])
        else:
            client.replyMessage(Message("⚠️ Vui lòng nhập nội dung sau lệnh .writeimg"), message_object, thread_id, thread_type, ttl=TTL)
            return

        if os.path.exists(CACHE_BG):
            img = Image.open(CACHE_BG).convert("RGBA")
        else:
            img = get_bg_image((1000,1000)).convert("RGBA")

        W, H = img.size
        draw = ImageDraw.Draw(img)
        font = get_font(64)

        max_width = W - 100  # padding 50px 2 bên
        lines = []
        words = text.split()
        while words:
            line = ""
            for i, word in enumerate(words):
                test_line = line + (" " if line else "") + word
                bbox = draw.textbbox((0,0), test_line, font=font)
                text_w = bbox[2] - bbox[0]
                if text_w > max_width:
                    break
                line = test_line
            lines.append(line)
            words = words[len(line.split()):]

        total_text_height = sum([draw.textbbox((0,0), l, font=font)[3] - draw.textbbox((0,0), l, font=font)[1] for l in lines]) \
                            + (len(lines)-1)*10  # gap giữa dòng
        y_start = (H - total_text_height)/2

        for line in lines:
            bbox = draw.textbbox((0,0), line, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            x = (W - text_w)/2
            draw.text((x, y_start), line, font=font, fill=(255,255,255,255),
                      stroke_width=2, stroke_fill=(0,0,0,180))
            y_start += text_h + 10  # gap giữa dòng

        path = autosave(img)
        client.sendLocalImage(path, thread_id=thread_id, thread_type=thread_type, ttl=TTL)
        try: os.remove(path)
        except: pass

    except Exception as e:
        print("Lỗi write_text_on_image:", e)
        client.replyMessage(Message(f"⚠️ Lỗi khi ghi chữ lên ảnh: {e}"), message_object, thread_id, thread_type, ttl=TTL)

def PTA():
    return {'writeimg': write_text_on_image}