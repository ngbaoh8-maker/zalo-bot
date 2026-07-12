import os
import time
import requests
from PIL import Image, ImageDraw, ImageFont
from zlapi.models import Message

# ================= INFO =================
des = {
    'version': "1.3.0",
    'credits': "ngbao",
    'description': "Giá vàng SJC Pro - Tự động sửa lỗi kết nối",
    'power': "Thành viên"
}

FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"

# ================= UTIL =================
def fetch_gold_data():
    """Thử lấy dữ liệu từ nhiều nguồn khác nhau để tránh lỗi kết nối"""
    # Nguồn 1: API Web2M (Dữ liệu JSON sạch)
    try:
        url = "https://api.web2m.com/historygold/sjc"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=10).json()
        if res.get('status') and res.get('data'):
            return time.strftime("%H:%M - %d/%m/%Y"), res['data'][:8]
    except:
        pass

    # Nguồn 2: API dự phòng (Nếu nguồn 1 tạch)
    try:
        url_backup = "https://api.giavang.net/api/v1/gold-prices/sjc"
        res = requests.get(url_backup, timeout=10).json()
        # Chuyển đổi format tùy theo API backup
        if res:
            return time.strftime("%H:%M - %d/%m/%Y"), res[:8]
    except:
        pass
        
    return None, None

def make_square(img, bg_color=(20, 20, 20)):
    """Làm vuông ảnh để hiện đầy đủ ở ngoài khung chat Zalo"""
    w, h = img.size
    side = max(w, h) + 60
    new_img = Image.new("RGB", (side, side), bg_color)
    new_img.paste(img, ((side - w) // 2, (side - h) // 2))
    return new_img

# ================= COMMAND =================
def handle_giavang(message, message_object, thread_id, thread_type, author_id, client):
    # Gửi thông báo nhỏ để khách hàng biết bot đang xử lý
    client.replyMessage(Message(text="🔍 Đang quét dữ liệu từ sàn SJC..."), message_object, thread_id, thread_type)
    
    updated_time, data = fetch_gold_data()
    
    if not data:
        # Phương án cuối cùng: Gửi văn bản thô nếu tạo ảnh lỗi
        return client.replyMessage(Message(text="❌ Hiện tại máy chủ SJC và các nguồn dự phòng đều đang bảo trì. Bạn vui lòng thử lại sau 5-10 phút!"), message_object, thread_id, thread_type)

    # 1. Vẽ giao diện bảng giá
    W, H = 850, 650
    img = Image.new("RGB", (W, H), (20, 20, 20))
    draw = ImageDraw.Draw(img)

    try:
        f_title = ImageFont.truetype(FONT_PATH, 50)
        f_header = ImageFont.truetype(FONT_PATH, 28)
        f_content = ImageFont.truetype(FONT_PATH, 24)
        f_sub = ImageFont.truetype(FONT_PATH, 18)
    except:
        f_title = f_header = f_content = f_sub = ImageFont.load_default()

    # Vẽ khung Header
    draw.rectangle([0, 0, W, 110], fill=(255, 204, 0))
    draw.text((40, 30), "THÔNG TIN GIÁ VÀNG SJC", fill=(0, 0, 0), font=f_title)
    
    # Nội dung bảng
    y = 140
    draw.text((40, y), f"Cập nhật: {updated_time}", fill=(150, 150, 150), font=f_sub)
    
    y = 200
    draw.text((40, y), "LOẠI VÀNG", fill=(255, 204, 0), font=f_header)
    draw.text((400, y), "MUA VÀO", fill=(255, 204, 0), font=f_header)
    draw.text((650, y), "BÁN RA", fill=(255, 204, 0), font=f_header)
    
    draw.line([(40, y+45), (810, y+45)], fill=(80, 80, 80), width=1)
    
    y += 70
    for item in data:
        name = item.get('type', 'SJC').replace('SJC', '').strip() or "Vàng SJC"
        buy = str(item.get('buy', '0'))
        sell = str(item.get('sell', '0'))

        draw.text((40, y), name[:22], fill=(255, 255, 255), font=f_content)
        draw.text((400, y), buy, fill=(0, 255, 127), font=f_content)
        draw.text((650, y), sell, fill=(255, 69, 0), font=f_content)
        y += 50

    # 2. Làm vuông ảnh
    img_square = make_square(img)
    
    # 3. Lưu và gửi
    path = f"modules/cache/gold_fix_{int(time.time())}.png"
    if not os.path.exists("modules/cache"): os.makedirs("modules/cache")
    img_square.save(path)

    client.sendLocalImage(path, thread_id=thread_id, thread_type=thread_type, message=Message(text=f"💰 Giá vàng SJC cập nhật lúc {updated_time}"))
    
    if os.path.exists(path): os.remove(path)

def PTA():
    return {'giavang': handle_giavang, 'vang': handle_giavang}