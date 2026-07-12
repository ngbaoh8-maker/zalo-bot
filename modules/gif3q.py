import os
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio
from zlapi.models import Message

des = {
    'version': "1.0.0",
    'credits': "ngbao",
    'description': "GIF động hero 3Q cực đẹp",
    'power': "Thành Viên"
}

FONT_PATH = "modules/cache/font/arial.ttf"
EMOJI_FONT = "modules/cache/font/NotoEmoji-Bold.ttf"
GIF_PATH = "modules/cache/gif3q.gif"

# Danh sách tướng 3Q
HEROES = [
    "Triệu Vân 🐉", "Tào Tháo ⚔️", "Lữ Bố 🔥", "Gia Cát Lượng 🧠", "Điêu Thuyền 💕",
    "Quan Vũ 💪", "Trương Phi 😤", "Tôn Quyền 🦁", "Chu Du 🎶", "Cam Ninh ⚡",
    "Lữ Linh Khởi 💥", "Tư Mã Ý 🕶️", "Hạ Hầu Đôn 🛡️", "Tiểu Kiều 🌸", "Đại Kiều 🌼",
    "Hoàng Cái ⚓", "Trương Liêu ⚔️", "Mã Siêu 🐎", "Hạ Hầu Uyên 🐯", "Tôn Sách 🦅"
]


def gradient_color(step, total, c1, c2):
    """Tạo màu chuyển gradient"""
    return tuple(int(c1[i] + (c2[i] - c1[i]) * (step / total)) for i in range(3))


def draw_glow(draw, text, font, x, y, glow_color):
    """Vẽ hiệu ứng sáng xung quanh chữ"""
    for r in range(6, 1, -1):
        draw.text((x, y), text, font=font, fill=glow_color)


def create_hero_gif(hero_name):
    """Tạo GIF hero 3Q"""
    os.makedirs("modules/cache", exist_ok=True)
    frames = []
    total_frames = 40
    w, h = 500, 300

    font_big = ImageFont.truetype(FONT_PATH, 40)
    font_emoji = ImageFont.truetype(EMOJI_FONT, 70)

    emojis = ["⚡", "🔥", "💥", "🌪️", "✨", "🌈", "💫", "🌟"]

    for i in range(total_frames):
        img = Image.new("RGBA", (w, h), (10, 10, 25, 255))
        draw = ImageDraw.Draw(img)

        # Gradient nền
        for y in range(h):
            color = gradient_color(y, h, (0, 100, 255), (255, 255, 150))
            draw.line([(0, y), (w, y)], fill=color, width=1)

        # Vẽ hero
        text_w, text_h = draw.textbbox((0, 0), hero_name, font=font_big)[2:]
        offset = (i * 6) % (w + text_w)
        x = w - offset
        y = h // 2 - text_h // 2

        # Hiệu ứng sáng chữ
        glow_color = random.choice([(255, 255, 150), (0, 255, 255), (255, 100, 50)])
        draw_glow(draw, hero_name, font_big, x, y, glow_color)
        draw.text((x, y), hero_name, font=font_big, fill=(255, 255, 255))

        # Emoji bay
        for _ in range(6):
            ex = random.randint(0, w)
            ey = random.randint(0, h)
            e = random.choice(emojis)
            draw.text((ex, ey), e, font=font_emoji, fill=(255, 255, 255, random.randint(180, 255)))

        img = img.filter(ImageFilter.GaussianBlur(0.7))
        frames.append(img)

    frames[0].save(GIF_PATH, save_all=True, append_images=frames[1:], duration=70, loop=0)
    return GIF_PATH


def handle_gif3q_command(message, message_object, thread_id, thread_type, author_id, client):
    args = message.strip().split()
    if len(args) < 2:
        client.replyMessage(
            Message(text="🎯 Dùng: ,gif3q list (xem danh sách) hoặc ,gif3q <số tướng>"),
            message_object,
            thread_id,
            thread_type
        )
        return

    cmd = args[1].lower()
    if cmd == "list":
        hero_list = "\n".join([f"{i+1}. {HEROES[i]}" for i in range(len(HEROES))])
        client.replyMessage(
            Message(text=f"🎮 Danh sách tướng 3Q:\n{hero_list}"),
            message_object,
            thread_id,
            thread_type
        )
        return

    try:
        index = int(cmd) - 1
        if index < 0 or index >= len(HEROES):
            raise ValueError
    except ValueError:
        client.replyMessage(
            Message(text="⚠️ Số tướng không hợp lệ!"),
            message_object,
            thread_id,
            thread_type
        )
        return

    hero_name = HEROES[index]
    gif_path = create_hero_gif(hero_name)

    client.sendLocalGif(
        gifPath=gif_path,
        thumbnailUrl=None,
        thread_id=thread_id,
        thread_type=thread_type,
        gifName="gif3q.gif",
        width=500,
        height=300,
        ttl=0
    )

    client.replyMessage(
        Message(text=f"✨ Hero 3Q: {hero_name}"),
        message_object,
        thread_id,
        thread_type
    )


def PTA():
    return {
        'gif3q': handle_gif3q_command
    }
