import requests
import threading
import random
import os
from PIL import Image, ImageDraw, ImageFont
from zlapi.models import Message

# Tạo cache
CACHE_PATH = "./modules/cache"
if not os.path.exists(CACHE_PATH): os.makedirs(CACHE_PATH)

des = {
    'version': "1.0.0",
    'credits': "ngbao",
    'description': "Check độ Gay/Les với giao diện Scanner",
    'power': "Thành Viên"
}

def create_scan_image(user_name, user_avatar_url, mode="gay"):
    # Cấu hình màu sắc
    if mode == "gay":
        main_color = (0, 225, 255) # Xanh Neon
        title_text = "KIỂM TRA ĐỘ GAY"
        prob_label = "GAY PROBABILITY:"
    else:
        main_color = (255, 50, 150) # Hồng Neon
        title_text = "KIỂM TRA ĐỘ LES"
        prob_label = "LESBIAN PROBABILITY:"

    # 1. Tạo nền
    w, h = 1000, 560
    img = Image.new('RGB', (w, h), color=(15, 15, 20))
    draw = ImageDraw.Draw(img)
    
    # Vẽ lưới điểm (Grid dots)
    for x in range(0, w, 50):
        for y in range(0, h, 50):
            draw.point((x, y), fill=(50, 50, 70))

    # 2. Xử lý Avatar (Thêm try/except để tránh die bot nếu link avt lỗi)
    try:
        avt_data = requests.get(user_avatar_url, timeout=10).content
        with open(f"{CACHE_PATH}/temp_avt.png", 'wb') as f: f.write(avt_data)
        avt = Image.open(f"{CACHE_PATH}/temp_avt.png").convert("RGB").resize((250, 250))
    except:
        avt = Image.new('RGB', (250, 250), color=main_color) # Nếu lỗi avt thì tạo ô màu thay thế

    img.paste(avt, (80, 130))
    draw.rectangle([75, 125, 335, 385], outline=main_color, width=5) # Khung avt
    draw.line([(70, 255), (345, 255)], fill=main_color, width=4) # Thanh quét

    # 3. Chèn text (Dùng font mặc định nếu không tìm thấy file font)
    try:
        # Bạn nên thay đường dẫn font thực tế của bạn vào đây
        f_path = "./modules/cache/font/BeVietnamPro-Bold.ttf"
        font_t = ImageFont.truetype(f_path, 55)
        font_m = ImageFont.truetype(f_path, 45)
        font_s = ImageFont.truetype(f_path, 25)
        font_b = ImageFont.truetype(f_path, 120)
    except:
        font_t = font_m = font_s = font_b = ImageFont.load_default()

    draw.text((w//2, 60), title_text, font=font_t, fill=main_color, anchor="mm")
    draw.text((420, 130), f"ID: {user_name.upper()}", font=font_m, fill=(255,255,255))
    draw.text((420, 195), prob_label, font=font_s, fill=main_color)
    
    percent = random.randint(1, 100)
    draw.text((420, 230), f"{percent}%", font=font_b, fill=main_color)
    
    # Progress Bar
    draw.rectangle([420, 350, 900, 365], outline=main_color, width=2)
    draw.rectangle([422, 352, 422 + int(476*(percent/100)), 363], fill=main_color)

    log_msg = "LOG: CẢNH BÁO: TÍN HIỆU RẤT MẠNH!" if percent > 50 else "LOG: TRẠNG THÁI: BÌNH THƯỜNG."
    draw.text((420, 390), log_msg, font=font_s, fill=(200, 200, 200))

    out_path = f"{CACHE_PATH}/final_{mode}.png"
    img.save(out_path)
    return out_path

def handle_check(message, message_object, thread_id, thread_type, author_id, client):
    def process():
        path = None
        try:
            mode = "les" if "les" in message.lower() else "gay"
            
            # Sửa lỗi NoneType: Kiểm tra kỹ thông tin user
            user_data = client.fetchUserInfo(author_id)
            if user_data and author_id in user_data:
                name = user_data[author_id].name
                avatar = user_data[author_id].avatar
            else:
                name = "Người dùng"
                avatar = "https://th.bing.com/th/id/OIP.aud97p57p2_68InY0S9Y_wHaHa" # Ảnh mặc định

            path = create_scan_image(name, avatar, mode)
            client.sendLocalImage(path, thread_id, thread_type, message=Message(text=f"✅ Đã phân tích xong {name}"))
            
        except Exception as e:
            print(f"Lỗi rồi: {e}")
        finally:
            if path and os.path.exists(path): os.remove(path)

    threading.Thread(target=process, daemon=True).start()

def PTA():
    return {'checkgay': handle_check, 'checkles': handle_check}