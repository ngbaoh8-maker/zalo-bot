import os
import random
import datetime
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from zlapi.models import Message, Mention

des = {
    'version': "3.5.0",
    'credits': "ngbao",
    'description': "Tạo thính",
    'power': "Thành viên"
}

CACHE_PATH = "modules/cache/"
BG_DIR = "background/"
os.makedirs(CACHE_PATH, exist_ok=True)
os.makedirs(BG_DIR, exist_ok=True)

FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
EMOJI_FONT_PATH = "modules/cache/font/NotoEmoji-Bold.ttf"

LOVE_STICKERS = [
    {"sticker_type": 3, "sticker_id": "21296", "category_id": "10093"},
    {"sticker_type": 3, "sticker_id": "21297", "category_id": "10093"},
    {"sticker_type": 3, "sticker_id": "21301", "category_id": "10093"},
]

love_emojis = ["💖","❤️","💘","💞","💓","💗","💝","💌","💕"]
dream_emojis = ["🌙","🌠","✨","🌌","🪐","🌟","🦋"]
nature_emojis = ["🌸","🌻","🌼","🌷","🍃","🌹","🌺"]
weather_emojis = ["☀️","🌧️","🌤️","⛅","🌈","❄️","🌪️"]
other_emojis = ["📜","🎵","💬","🕰️","📅","📖","🫶"]

def get_font(size, is_emoji=False):
    path = EMOJI_FONT_PATH if is_emoji else FONT_PATH
    if os.path.exists(path):
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def pick_unique_emojis(n):
    return random.sample(love_emojis + dream_emojis + nature_emojis + weather_emojis + other_emojis, n)

def generate_love_poem(name: str) -> str:
    templates = [
        "{0}{name} ơi, em là ánh nắng {1},\nSoi sáng tim anh từng ngày {2}.\nDẫu gió cuốn qua bao mùa {3},\nYêu em là điều chẳng thể đổi thay {4}.",
        "{name}, anh gửi yêu thương theo làn gió {0},\nMong rằng em sẽ đón nhận {1}.\nTình anh trao trọn chẳng phai {2},\nNhư cánh hoa giữa trời lộng gió {3}."
    ]
    emoji_set = pick_unique_emojis(5)
    template = random.choice(templates)
    poem = template.format(*emoji_set, name=name)
    date = datetime.datetime.now().strftime("%d/%m/%Y")
    return f"*Thơ tỏ tình dành cho {name} - {date}*\n\n{poem}"

def download_avatar(url, save_path=os.path.join(CACHE_PATH,"avatar.png")):
    try:
        r = requests.get(url, stream=True, timeout=10)
        if r.status_code == 200:
            with open(save_path, "wb") as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
            return save_path
    except:
        return None
    return None

def get_random_background(width, height):
    try:
        files = [f for f in os.listdir(BG_DIR) if f.lower().endswith(('.png','.jpg','.jpeg'))]
        if not files:
            return Image.new("RGBA",(width,height),(240,245,255,255))
        path = os.path.join(BG_DIR, random.choice(files))
        bg = Image.open(path).convert("RGBA")
        bg = bg.resize((width,height), Image.LANCZOS)
        return bg.filter(ImageFilter.GaussianBlur(20))
    except:
        return Image.new("RGBA",(width,height),(240,245,255,255))

def wrap_text(text, font, max_width):
    lines=[]
    for line in text.split("\n"):
        words=line.split(" ")
        cur=""
        for w in words:
            if font.getlength(cur+w+" ")<=max_width:
                cur+=w+" "
            else:
                if cur: lines.append(cur.strip())
                cur=w+" "
        if cur: lines.append(cur.strip())
    return lines

def handle_lovebykai_command(message, message_object, thread_id, thread_type, author_id, client):
    text = (message or "").split()
    if len(text)<2:
        client.sendMessage(Message(text="🚦 Vui lòng nhập tên người bạn muốn tỏ tình. Ví dụ: love Kthah"), thread_id, thread_type, ttl=60000)
        return
    name = " ".join(text[1:]).strip().title()
    poem = generate_love_poem(name)

    # Tạo ảnh
    WIDTH, HEIGHT = 1080, 1440
    font_title = get_font(50)
    font_poem = get_font(38)
    font_emoji = get_font(42, is_emoji=True)

    bg = get_random_background(WIDTH, HEIGHT)
    overlay = Image.new("RGBA",(WIDTH,HEIGHT),(0,0,0,0))
    draw = ImageDraw.Draw(overlay)

    # Avatar
    try:
        info = client.fetchUserInfo(author_id)
        avatar_url = info.changed_profiles[author_id].avatar if author_id in info.changed_profiles else None
        avatar_path = download_avatar(avatar_url)
        if avatar_path:
            avatar = Image.open(avatar_path).convert("RGBA").resize((120,120))
            mask = Image.new("L",(120,120),0)
            ImageDraw.Draw(mask).ellipse((0,0,120,120),fill=255)
            overlay.paste(avatar,(50,50),mask)
        user_name = getattr(info.changed_profiles[author_id],"name","ID_"+str(author_id))
        draw.text((200,80), user_name, font=font_title, fill=(255,255,255,255))
    except:
        pass

    # Thơ tự động xuống dưới avatar
    max_width = WIDTH-100
    lines = wrap_text(poem, font_poem, max_width)
    start_y = 200  # bắt đầu bên dưới avatar
    for line in lines:
        draw.text((50,start_y), line, font=font_poem, fill=(255,255,255,255))
        start_y+=50

    final_img = Image.alpha_composite(bg, overlay)
    output_path = os.path.join(CACHE_PATH,"thathinh.jpg")
    final_img.convert("RGB").save(output_path,"JPEG")

    # gửi ảnh
    client.sendLocalImage(output_path, thread_id=thread_id, thread_type=thread_type, width=WIDTH, height=HEIGHT, ttl=120000)

    # gửi reaction
    for r in random.sample(love_emojis+dream_emojis+nature_emojis,3):
        try:
            client.addReaction(r, message_object, thread_id, thread_type)
        except: pass

    # gửi sticker
    try:
        sticker = random.choice(LOVE_STICKERS)
        client.sendSticker(sticker['sticker_type'], sticker['sticker_id'], sticker['category_id'], thread_id, thread_type, ttl=120000)
    except: pass

def PTA():
    return {
        'thathinh': handle_lovebykai_command
    }