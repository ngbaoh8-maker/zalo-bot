import os
import time
import random
import requests
import textwrap
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from zlapi.models import Message

# ================= INFO =================
des = {
    'version': "1.0.0",
    'credits': "ngbao",
    'description': "Tạo bằng khen vinh danh hoặc troll",
    'power': "Thành viên"
}

FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"

# Các danh hiệu mặc định nếu người dùng không nhập
AWARDS = [
    "Học viên ưu tú ngành lặn nhóm",
    "Chiến thần thả thính xuyên biên giới",
    "Đệ nhất lười biếng của năm",
    "Chuyên gia dùng cả thanh xuân để Seen",
    "Bậc thầy tấu hài cấp quốc tế",
    "Người có nhan sắc gây chấn động địa cầu"
]

# ================= UTIL =================
def fetch_image(url):
    try:
        if not url: return None
        r = requests.get(url, timeout=10)
        return Image.open(BytesIO(r.content)).convert("RGBA")
    except: return None

def create_certificate(avatar_url, name, award_content):
    # Kích thước bằng khen chuẩn (ngang)
    W, H = 1000, 700
    img = Image.new("RGB", (W, H), (255, 252, 240)) # Nền giấy hơi vàng
    draw = ImageDraw.Draw(img)

    try:
        f_title = ImageFont.truetype(FONT_PATH, 80)
        f_sub = ImageFont.truetype(FONT_PATH, 30)
        f_name = ImageFont.truetype(FONT_PATH, 60)
        f_award = ImageFont.truetype(FONT_PATH, 40)
        f_sig = ImageFont.truetype(FONT_PATH, 25)
    except:
        f_title = f_sub = f_name = f_award = f_sig = ImageFont.load_default()

    # 1. VẼ KHUNG VIỀN (BORDERS)
    # Viền ngoài
    draw.rectangle([20, 20, W-20, H-20], outline=(180, 140, 50), width=10)
    # Viền trong mỏng
    draw.rectangle([40, 40, W-40, H-40], outline=(210, 170, 70), width=3)

    # 2. TIÊU ĐỀ
    txt_header = "BẰNG KHEN"
    tw = draw.textlength(txt_header, font=f_title)
    draw.text(((W-tw)//2, 80), txt_header, fill=(200, 0, 0), font=f_title)

    txt_sub = "CHỨNG NHẬN TẶNG CHO"
    tsw = draw.textlength(txt_sub, font=f_sub)
    draw.text(((W-tsw)//2, 180), txt_sub, fill=(50, 50, 50), font=f_sub)

    # 3. TÊN NGƯỜI NHẬN
    name = name.upper()
    tnw = draw.textlength(name, font=f_name)
    draw.text(((W-tnw)//2, 240), name, fill=(0, 0, 0), font=f_name)
    # Đường kẻ dưới tên
    draw.line([(W//2 - 200, 310), (W//2 + 200, 310)], fill=(0, 0, 0), width=2)

    # 4. NỘI DUNG DANH HIỆU (Xử lý xuống dòng nếu dài)
    award_text = f"Đã có thành tích xuất sắc: {award_content}"
    lines = textwrap.wrap(award_text, width=45)
    y_award = 350
    for line in lines:
        alw = draw.textlength(line, font=f_award)
        draw.text(((W-alw)//2, y_award), line, fill=(100, 70, 20), font=f_award)
        y_award += 50

    # 5. AVATAR (Gắn như một cái tem nhỏ ở góc)
    avatar = fetch_image(avatar_url)
    if avatar:
        avatar = avatar.resize((150, 150))
        # Bo tròn avatar
        mask = Image.new("L", (150, 150), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 150, 150), fill=255)
        img.paste(avatar, (W-220, 80), mask)
        draw.ellipse((W-225, 75, W-65, 235), outline=(210, 170, 70), width=5)

    # 6. DẤU MỘC ĐỎ & CHỮ KÝ
    # Vẽ vòng tròn dấu mộc
    stamp_x, stamp_y = 750, 530
    draw.ellipse((stamp_x, stamp_y, stamp_x+120, stamp_y+120), outline=(220, 0, 0, 180), width=5)
    draw.text((stamp_x+25, stamp_y+45), "ADMIN", fill=(220, 0, 0, 180), font=f_sig)
    
    draw.text((150, 520), "Ngày cấp: " + time.strftime("%d/%m/%Y"), fill=(50, 50, 50), font=f_sig)
    draw.text((150, 560), "Ký tên: Chủ tịch Bot", fill=(0, 0, 0), font=f_sig)

    return img

# ================= COMMAND =================
def handle_bangkhen(message, message_object, thread_id, thread_type, author_id, client):
    target_id = author_id
    if message_object.mentions:
        target_id = message_object.mentions[0]['uid']
    elif message_object.quote:
        target_id = message_object.quote.ownerId

    user_info = client.fetchUserInfo(target_id)
    if hasattr(user_info, 'changed_profiles') and str(target_id) in user_info.changed_profiles:
        p = user_info.changed_profiles[str(target_id)]
        name = p.get('zaloName', 'Thành viên')
        avatar = p.get('avatar', '')
    else:
        name = getattr(user_info, 'name', 'Thành viên')
        avatar = getattr(user_info, 'avatar', '')

    # Lấy nội dung khen thưởng
    text = message_object.text or ""
    parts = text.split()
    if len(parts) > 1 and not message_object.mentions:
        award = " ".join(parts[1:])
    else:
        award = random.choice(AWARDS)

    img = create_certificate(avatar, name, award)
    path = f"modules/cache/cert_{int(time.time())}.png"
    if not os.path.exists("modules/cache"): os.makedirs("modules/cache")
    img.save(path)

    client.sendLocalImage(path, thread_id=thread_id, thread_type=thread_type, message=Message(text=f"📜 Chúc mừng {name} đã nhận được bằng khen!"))
    os.remove(path)

# ================= EXPORT =================
def PTA():
    return {
        'bangkhen': handle_bangkhen,
        'certificate': handle_bangkhen,
        'vinhdanh': handle_bangkhen
    }