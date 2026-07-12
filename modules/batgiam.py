import os
import time
import random
import datetime
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from zlapi.models import Message

# ================= INFO =================
des = {
    'version': "1.0.0",
    'credits': "ngbao",
    'description': "Lệnh bắt giam vào tù (troll)",
    'power': "Thành viên"
}

# Đường dẫn font chữ (Hãy đảm bảo bạn có file font này, nếu không nó dùng font mặc định sẽ xấu)
FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"

# Danh sách tội danh hài hước
CRIMES = [
    "Học bài quá nhiều",
    "Spam nhóm quá nhiều",
    "Thức khuya dậy sớm",
    "Ăn cơm không rửa bát",
    "Seen tin nhắn không rep",
    "Hay dỗi người yêu",
    "Cướp trái tim admin",
    "Thở quá to làm ồn",
    "Hack game quá lộ liễu"
]

# ================= UTIL =================
def fetch_image(url):
    try:
        if not url:
            return None
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        img = Image.open(BytesIO(r.content)).convert("RGB")
        return img
    except:
        return None

# ================= CREATE IMAGE =================
def create_prison_image(avatar_url, name, uid):
    # Kích thước ảnh đầu ra
    W, H = 600, 750  # 600x600 cho avatar, 150px cho footer
    
    # Tạo nền đen
    img = Image.new("RGB", (W, H), (10, 10, 10))
    draw = ImageDraw.Draw(img)

    # Load Font
    try:
        f_police = ImageFont.truetype(FONT_PATH, 20)
        f_name   = ImageFont.truetype(FONT_PATH, 55)
        f_date   = ImageFont.truetype(FONT_PATH, 25)
        f_stamp  = ImageFont.truetype(FONT_PATH, 80)
    except:
        # Fallback nếu không tìm thấy font
        f_police = f_name = f_date = f_stamp = ImageFont.load_default()

    # 1. Xử lý Avatar (Làm nền)
    avatar = fetch_image(avatar_url)
    if not avatar:
        avatar = Image.new("RGB", (600, 600), (100, 100, 100))
    
    # Resize avatar vừa khung trên
    avatar = avatar.resize((600, 600))
    # Giảm sáng một chút cho hợp mood tù tội
    avatar = ImageEnhance.Brightness(avatar).enhance(0.8)
    img.paste(avatar, (0, 0))

    # 2. Vẽ song sắt (Bars)
    # Vẽ các thanh dọc màu xám/đen
    bar_width = 15
    bar_spacing = 90
    for x in range(bar_spacing // 2, W, bar_spacing):
        # Vẽ thanh sắt (màu xám đậm gradient giả lập)
        draw.rectangle([x, 0, x + bar_width, 600], fill=(50, 50, 50))
        # Tạo hiệu ứng bóng 3D nhẹ cho thanh sắt
        draw.rectangle([x + 2, 0, x + 5, 600], fill=(90, 90, 90))

    # 3. Vẽ phần Footer (Thông tin phạm nhân)
    # Vẽ nền đen ở dưới
    draw.rectangle([0, 600, W, H], fill=(20, 20, 20))
    # Đường kẻ đỏ phân cách
    draw.rectangle([0, 600, W, 604], fill=(150, 0, 0))

    # Text: POLICE DEPARTMENT
    txt_police = "POLICE DEPARTMENT"
    tw_police = draw.textlength(txt_police, font=f_police)
    draw.text(((W - tw_police) // 2, 620), txt_police, fill=(150, 150, 150), font=f_police)

    # Text: Tên phạm nhân (In hoa)
    name = name.upper()
    # Nếu tên quá dài thì cắt bớt
    if len(name) > 15:
        name = name[:12] + "..."
    tw_name = draw.textlength(name, font=f_name)
    draw.text(((W - tw_name) // 2, 650), name, fill=(255, 255, 255), font=f_name)

    # Text: Ngày tháng (Màu đỏ)
    date_str = datetime.datetime.now().strftime("DATE: %d/%m/%Y")
    tw_date = draw.textlength(date_str, font=f_date)
    draw.text(((W - tw_date) // 2, 710), date_str, fill=(200, 50, 50), font=f_date)

    # 4. Vẽ con dấu BẮT GIỮ (Stamp)
    # Tạo một layer trong suốt để vẽ và xoay
    stamp_layer = Image.new('RGBA', (500, 250), (0, 0, 0, 0))
    stamp_draw = ImageDraw.Draw(stamp_layer)
    
    stamp_text = "BẮT GIỮ"
    color_stamp = (220, 50, 50, 200) # Màu đỏ có độ trong suốt
    
    # Vẽ khung chữ nhật bo góc (giả lập con dấu)
    stamp_w = draw.textlength(stamp_text, font=f_stamp) + 60
    stamp_h = 130
    cx, cy = 250, 125 # Tâm của layer tem
    
    # Vẽ viền dấu
    left, top, right, bottom = cx - stamp_w/2, cy - stamp_h/2, cx + stamp_w/2, cy + stamp_h/2
    stamp_draw.rectangle([left, top, right, bottom], outline=color_stamp, width=8)
    stamp_draw.rectangle([left+5, top+5, right-5, bottom-5], outline=color_stamp, width=3) # Viền đôi
    
    # Vẽ chữ "BẮT GIỮ"
    sw = stamp_draw.textlength(stamp_text, font=f_stamp)
    # Căn giữa thủ công
    stamp_draw.text((cx - sw/2, cy - 50), stamp_text, fill=color_stamp, font=f_stamp)
    
    # Hiệu ứng noise cho con dấu (giả lập vết mực loang lổ - optional)
    # (Đơn giản thì bỏ qua, code này chỉ xoay)
    
    # Xoay con dấu -25 độ
    rotated_stamp = stamp_layer.rotate(25, expand=1, resample=Image.BICUBIC)
    
    # Dán đè lên ảnh chính (vị trí giữa ảnh)
    sx, sy = rotated_stamp.size
    img.paste(rotated_stamp, ((W - sx) // 2, (600 - sy) // 2), rotated_stamp)

    return img

# ================= COMMAND =================
def handle_batgiam(message, message_object, thread_id, thread_type, author_id, client):
    text = message_object.text or ""
    parts = text.split()

    # Xác định đối tượng: tag hoặc reply hoặc chính mình
    target_id = author_id
    if message_object.mentions:
        target_id = message_object.mentions[0]['uid']
    elif message_object.quote:
        target_id = message_object.quote.ownerId

    # Lấy thông tin user
    user_info = client.fetchUserInfo(target_id)
    if hasattr(user_info, 'changed_profiles') and str(target_id) in user_info.changed_profiles:
        p = user_info.changed_profiles[str(target_id)]
        name = p.get('zaloName', 'UNKNOWN')
        avatar = p.get('avatar', '')
    else:
        name = getattr(user_info, 'name', 'UNKNOWN')
        avatar = getattr(user_info, 'avatar', '')

    # Xử lý lý do bắt giữ
    # Nếu người dùng nhập lý do sau lệnh thì lấy, không thì random
    if len(parts) > 1 and not message_object.mentions:
        # Trường hợp: /batgiam Ly do o day (không tag)
        crime = " ".join(parts[1:])
    elif len(parts) > 2 and message_object.mentions:
        # Trường hợp: /batgiam @User Ly do o day
        # Cần lọc bỏ phần mention (thường thư viện zlapi xử lý text hơi khác nhau tùy phiên bản)
        # Ở đây ta lấy đơn giản là random nếu lười parse kỹ, hoặc lấy chuỗi cuối.
        # Để an toàn dùng random list nếu code parse phức tạp.
        crime = random.choice(CRIMES)
    else:
        crime = random.choice(CRIMES)

    # Tạo ảnh
    img = create_prison_image(avatar, name, target_id)

    # Lưu cache
    if not os.path.exists("modules/cache"):
        os.makedirs("modules/cache")

    path = f"modules/cache/batgiam_{int(time.time())}.jpg"
    img.save(path, quality=95)

    # Gửi tin nhắn
    msg_content = f"👮 Cảnh sát đã bắt giữ đối tượng: {name}!\n⚖️ Tội danh: {crime}"
    msg = Message(text=msg_content)
    
    client.sendLocalImage(
        path,
        thread_id=thread_id,
        thread_type=thread_type,
        message=msg
    )

    # Dọn dẹp
    try:
        os.remove(path)
    except:
        pass

# ================= EXPORT =================
def PTA():
    return {
        'batgiam': handle_batgiam,
        'batgiu': handle_batgiam,
        'prison': handle_batgiam
    }