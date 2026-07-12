import time
import os
import random
from PIL import Image, ImageDraw, ImageFont
from zlapi.models import Message, Mention
from config import PREFIX

des = {
    'version': "1.3.0",
    'credits': "ngbao",
    'description': "Hiển thị thời gian bot hoạt động bằng GIF động có hiệu ứng gradient và nền đẹp.",
    'power': "Thành Viên"
}

# Ghi thời điểm bot khởi động
start_time = time.time()

# ========================= HÀM HỖ TRỢ =========================

def create_gradient_colors(num_colors=None):
    """Tạo danh sách màu ngẫu nhiên (ít nhất 2)."""
    if num_colors is None or num_colors < 2:
        num_colors = random.randint(2, 6)
    return [(random.randint(0, 255),
             random.randint(0, 255),
             random.randint(0, 255)) for _ in range(num_colors)]

def interpolate_colors(colors, text_length, change_every=1):
    """Tạo dải màu chuyển tiếp cho text."""
    if not colors or text_length <= 0:
        return [(255, 255, 255)] * text_length
    if len(colors) == 1:
        return [colors[0]] * text_length

    gradient = []
    num_segments = len(colors) - 1
    steps_per_segment = max(1, (text_length // (num_segments * change_every)) + 1)

    for i in range(num_segments):
        for j in range(steps_per_segment * change_every):
            if len(gradient) >= text_length:
                break
            ratio = j / max(1, (steps_per_segment * change_every))
            a, b = colors[i], colors[i + 1]
            interpolated = (
                int(a[0] * (1 - ratio) + b[0] * ratio),
                int(a[1] * (1 - ratio) + b[1] * ratio),
                int(a[2] * (1 - ratio) + b[2] * ratio)
            )
            gradient.append(interpolated)

    while len(gradient) < text_length:
        gradient.append(colors[-1])
    return gradient[:text_length]

def draw_text(draw, text, pos, font, gradient):
    """Vẽ chữ có bóng + gradient."""
    x, y = pos
    for i, ch in enumerate(text):
        color = gradient[i] if i < len(gradient) else (255, 255, 255)
        draw.text((x + 2, y + 2), ch, fill=(0, 0, 0), font=font)
        draw.text((x, y), ch, fill=color, font=font)
        left, top, right, bottom = draw.textbbox((0, 0), ch, font=font)
        x += (right - left) if (right - left) > 0 else font.size * 0.6

def format_uptime(seconds):
    """Trả về uptime theo ngày/giờ/phút/giây."""
    d = seconds // 86400
    h = (seconds % 86400) // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return d, h, m, s

# ========================= LỆNH CHÍNH =========================

def handle_uptime_command(message, message_object, thread_id, thread_type, author_id, client):
    """Tạo GIF động thể hiện uptime và gửi bằng sendLocalGif."""
    try:
        now = time.time()
        base_uptime = int(now - start_time)

        anim_dur = 5  # giây
        fps = 6
        frame_count = anim_dur * fps
        frame_ms = int(1000 / fps)

        line1 = "THỜI GIAN BOT ĐÃ ONLINE"
        bg_folder = "background"
        output_path = "modules/cache/temp_uptime.gif"

        # chọn nền
        images = [f for f in os.listdir(bg_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if not images:
            raise Exception("Không tìm thấy ảnh nền trong modules/cache/image")
        bg_path = os.path.join(bg_folder, random.choice(images))

        # font
        font_path = "modules/cache/font/BeVietnamPro-Bold.ttf"
        if os.path.exists(font_path):
            font_small = ImageFont.truetype(font_path, 48)
            font_large = ImageFont.truetype(font_path, 78)
        else:
            font_small = ImageFont.load_default()
            font_large = ImageFont.load_default()

        base = Image.open(bg_path).convert("RGBA")
        W, H = base.size

        # gradient dòng 1
        grad1 = interpolate_colors(create_gradient_colors(), len(line1))
        tmp_draw = ImageDraw.Draw(base)
        bbox1 = tmp_draw.textbbox((0, 0), line1, font=font_small)
        text_w1 = bbox1[2] - bbox1[0]
        x1 = (W - text_w1) // 2
        y1 = 50

        frames = []
        for i in range(frame_count):
            uptime = base_uptime + i // fps
            d, h, m, s = format_uptime(uptime)
            line2 = f"{d} Ngày {h} Giờ {m} Phút {s} Giây"
            grad2 = interpolate_colors(create_gradient_colors(), len(line2))

            frame = base.copy()
            draw = ImageDraw.Draw(frame)

            # dòng 1
            draw_text(draw, line1, (x1, y1), font_small, grad1)

            # dòng 2 căn giữa
            bbox2 = draw.textbbox((0, 0), line2, font=font_large)
            text_w2 = bbox2[2] - bbox2[0]
            text_h2 = bbox2[3] - bbox2[1]
            x2 = (W - text_w2) // 2
            y2 = (H - text_h2) // 2

            # overlay mờ
            overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
            ov_draw = ImageDraw.Draw(overlay)
            pad_x, pad_y = 30, 10
            ov_draw.rectangle(
                [x2 - pad_x, y2 - pad_y, x2 + text_w2 + pad_x, y2 + text_h2 + pad_y],
                fill=(0, 0, 0, 100)
            )
            frame = Image.alpha_composite(frame, overlay)
            draw = ImageDraw.Draw(frame)
            draw_text(draw, line2, (x2, y2), font_large, grad2)
            frames.append(frame.convert("RGB"))

        # lưu GIF
        if os.path.exists(output_path):
            os.remove(output_path)
        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            duration=frame_ms,
            loop=0,
            optimize=True,
            quality=85
        )

        mention = Mention(author_id, length=len("@Member"), offset=0)
        msg = Message(text="@Member", mention=mention)

        sent = False
        try:
            # dùng hàm sendLocalGif chuẩn của bạn
            client.sendLocalGif(
                gifPath=output_path,
                thumbnailUrl=None,
                thread_id=thread_id,
                thread_type=thread_type,
                gifName="uptime.gif",
                width=W,
                height=H,
                ttl=0
            )
            sent = True
        except Exception as e:
            print(f"[Uptime] sendLocalGif lỗi: {e}")
            sent = False

        if not sent:
            try:
                client.sendLocalImage(
                    output_path,
                    message=msg,
                    thread_id=thread_id,
                    thread_type=thread_type
                )
            except Exception as e:
                print(f"[Uptime] Fallback sendLocalImage lỗi: {e}")

        try:
            if os.path.exists(output_path):
                os.remove(output_path)
        except:
            pass

    except Exception as e:
        mention = Mention(author_id, length=len("@Member"), offset=0)
        err = Message(text=f"⚠️ Lỗi khi tạo uptime GIF: {str(e)}", mention=mention)
        try:
            client.sendMessage(err, thread_id, thread_type)
        except:
            pass


def PTA():
    """Đăng ký lệnh uptime"""
    return {
        "uptimeg": handle_uptime_command
    }
