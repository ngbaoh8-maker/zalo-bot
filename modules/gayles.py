import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import requests
import random
import time
import concurrent.futures
from datetime import datetime
from zlapi.models import Message, Mention

# --- CONFIG ---
from config import PREFIX

des = {
    'version': "1.5.2",
    'credits': "ngbao",
    'description': "Phán đoán chính xác xu hướng tính dục (Gay/Les)",
    'power': "Thành viên"
}

# Đường dẫn cache
CACHE_PATH = "modules/cache"
FONT_DIR = os.path.join(CACHE_PATH, "font")
FONT_PATH = os.path.join(FONT_DIR, "BeVietnamPro-Bold.ttf")
EMOJI_FONT_PATH = os.path.join(FONT_DIR, "NotoEmoji-Bold.ttf")

if not os.path.exists(FONT_DIR):
    os.makedirs(FONT_DIR)

# ================= HÀM HỖ TRỢ =================

def get_font(size):
    try: 
        return ImageFont.truetype(FONT_PATH, size)
    except:
        try: 
            return ImageFont.truetype("arial.ttf", size)
        except: 
            return ImageFont.load_default()

def get_emoji_font(size):
    try: 
        return ImageFont.truetype(EMOJI_FONT_PATH, size)
    except: 
        return ImageFont.load_default()

def fetch_image(url):
    if not url: 
        return None
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, stream=True, timeout=10)
        response.raise_for_status()
        return Image.open(BytesIO(response.content)).convert("RGBA")
    except: 
        return None

def fit_text_font(text, max_width, initial_size, min_size=15):
    """Hàm điều chỉnh font size cho vừa chiều rộng"""
    current_size = initial_size
    font = get_font(current_size)
    text_str = str(text)
    
    while font.getlength(text_str) > max_width and current_size > min_size:
        current_size -= 2
        font = get_font(current_size)
    
    if font.getlength(text_str) > max_width:
        while font.getlength(text_str + "...") > max_width and len(text_str) > 3:
            text_str = text_str[:-1]
        text_str += "..."
    
    return font, text_str

def wrap_text(text, font, max_width, max_lines=None):
    """Hàm tách text thành nhiều dòng với khoảng cách hợp lý"""
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = f"{current_line} {word}".strip() if current_line else word
        
        if font.getlength(test_line) <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
            
            # Giới hạn số dòng nếu cần
            if max_lines and len(lines) >= max_lines:
                if current_line:
                    lines.append(current_line + "...")
                break
    
    if current_line and (not max_lines or len(lines) < max_lines):
        lines.append(current_line)
    
    return lines

def calculate_text_height(font, lines, line_spacing=1.2):
    """Tính chiều cao tổng của text với các dòng"""
    # Ước tính chiều cao của một dòng (1.2 lần font size)
    line_height = int(font.size * line_spacing)
    return len(lines) * line_height

def create_glass_rect(draw, x, y, w, h, radius=15):
    """Tạo hình chữ nhật với hiệu ứng kính"""
    draw.rounded_rectangle((x, y, x+w, y+h), radius=radius, 
                          fill=(30, 30, 30, 180), 
                          outline=(255, 255, 255, 40), 
                          width=1)

# ================= PHÂN TÍCH GIỚI TÍNH & XU HƯỚNG =================

def detect_gender_advanced(profile_data):
    """Phân tích giới tính từ thông tin profile nâng cao"""
    gender_value = profile_data.get('gender', -1)
    
    # Map gender từ Zalo: 0 = Nam, 1 = Nữ
    gender_map = {0: "NAM", 1: "NỮ"}
    base_gender = gender_map.get(gender_value, "KHÔNG RÕ")
    
    # Nếu không có gender trong profile, phân tích từ tên
    if base_gender == "KHÔNG RÕ":
        name = profile_data.get('name', '').lower()
        
        # Từ chỉ nam trong tiếng Việt
        male_keywords = ['anh', 'ông', 'bố', 'cha', 'chú', 'bác', 'cậu', 'nam', 'thầy', 'sư', 'trai']
        female_keywords = ['chị', 'cô', 'bà', 'mẹ', 'má', 'dì', 'thím', 'mợ', 'nữ', 'gái', 'nàng']
        
        male_score = sum(1 for word in male_keywords if word in name)
        female_score = sum(1 for word in female_keywords if word in name)
        
        if male_score > female_score:
            return "NAM"
        elif female_score > male_score:
            return "NỮ"
        else:
            # Phân tích đuôi tên
            male_endings = ['văn', 'đức', 'hùng', 'cường', 'tuấn', 'sơn', 'phong', 'long', 'khánh', 'quang', 'minh', 'dũng', 'kiên']
            female_endings = ['thị', 'anh', 'linh', 'ngọc', 'mai', 'hà', 'lan', 'hương', 'trang', 'vy', 'my', 'ngân', 'nhi', 'uyên']
            
            for ending in male_endings:
                if name.endswith(ending):
                    return "NAM"
            
            for ending in female_endings:
                if name.endswith(ending):
                    return "NỮ"
            
            return "KHÔNG RÕ"
    
    return base_gender

def analyze_sexual_orientation(profile_data, gender):
    """Phân tích xu hướng tính dục dựa trên nhiều yếu tố"""
    name = profile_data.get('name', 'Unknown')
    avatar_url = profile_data.get('avatar', '')
    dob = profile_data.get('dob', 0)
    
    # Tạo seed ổn định từ nhiều yếu tố
    seed_str = f"{name}{avatar_url}{dob}{gender}"
    seed = sum(ord(c) for c in seed_str)
    random.seed(seed)
    
    if gender == "NAM":
        # Nam: Tập trung vào GAY
        gay_base = random.randint(20, 95)
        gay_bonus = 0
        
        # Phân tích avatar (giả lập)
        if 'profile' in avatar_url.lower():
            gay_bonus += random.randint(5, 20)
        
        # Phân tích tên
        name_lower = name.lower()
        gay_names = ['minh', 'khoa', 'khôi', 'nam', 'phúc', 'thiện', 'huy', 'duy']
        for gay_name in gay_names:
            if gay_name in name_lower:
                gay_bonus += random.randint(5, 15)
        
        gay_score = min(gay_base + gay_bonus, 100)
        les_score = random.randint(0, 15)  # Rất thấp cho nam
        straight_score = 100 - gay_score
        
        # Xác định level
        if gay_score >= 80:
            orientation = "GAY CHÍNH HIỆU 🏳️‍🌈"
            confidence = "Rất cao"
            description = "Bạn có xu hướng đồng tính nam rất rõ ràng!"
        elif gay_score >= 60:
            orientation = "GAY CÓ THIÊN HƯỚNG 🌈"
            confidence = "Cao"
            description = "Bạn có thiên hướng đồng tính nam khá rõ."
        elif gay_score >= 40:
            orientation = "BISEXUAL (NAM) 💜"
            confidence = "Trung bình"
            description = "Bạn có thể hứng thú với cả hai giới."
        elif gay_score >= 20:
            orientation = "STRAIGHT NHƯNG MỞ 🌟"
            confidence = "Thấp"
            description = "Bạn chủ yếu là straight nhưng có thể cởi mở."
        else:
            orientation = "STRAIGHT 100% 👨‍❤️‍👨"
            confidence = "Rất cao"
            description = "Bạn có xu hướng dị tính nam rõ ràng."
            
        emoji = "🏳️‍🌈" if gay_score > 50 else "👨‍❤️‍👨"
        
    elif gender == "NỮ":
        # Nữ: Tập trung vào LES
        les_base = random.randint(20, 95)
        les_bonus = 0
        
        # Phân tích tên
        name_lower = name.lower()
        les_names = ['linh', 'anh', 'trang', 'my', 'vy', 'ngọc', 'hương', 'lan']
        for les_name in les_names:
            if les_name in name_lower:
                les_bonus += random.randint(5, 15)
        
        les_score = min(les_base + les_bonus, 100)
        gay_score = random.randint(0, 15)  # Rất thấp cho nữ
        straight_score = 100 - les_score
        
        # Xác định level
        if les_score >= 80:
            orientation = "LESBIAN CHÍNH HIỆU 🏳️‍🌈"
            confidence = "Rất cao"
            description = "Bạn có xu hướng đồng tính nữ rất rõ ràng!"
        elif les_score >= 60:
            orientation = "LESBIAN CÓ THIÊN HƯỚNG 🌸"
            confidence = "Cao"
            description = "Bạn có thiên hướng đồng tính nữ khá rõ."
        elif les_score >= 40:
            orientation = "BISEXUAL (NỮ) 💜"
            confidence = "Trung bình"
            description = "Bạn có thể hứng thú với cả hai giới."
        elif les_score >= 20:
            orientation = "STRAIGHT NHƯNG MỞ 🌟"
            confidence = "Thấp"
            description = "Bạn chủ yếu là straight nhưng có thể cởi mở."
        else:
            orientation = "STRAIGHT 100% 👩‍❤️‍👨"
            confidence = "Rất cao"
            description = "Bạn có xu hướng dị tính nữ rõ ràng."
            
        emoji = "🏳️‍🌈" if les_score > 50 else "👩‍❤️‍👨"
        
    else:
        # Không rõ giới tính
        gay_score = random.randint(0, 100)
        les_score = random.randint(0, 100)
        straight_score = 100 - (gay_score + les_score) // 2
        
        # Đảm bảo tổng 100%
        total = gay_score + les_score + straight_score
        if total != 100:
            gay_score = int(gay_score * 100 / total)
            les_score = int(les_score * 100 / total)
            straight_score = 100 - gay_score - les_score
        
        orientation = "KHÔNG XÁC ĐỊNH ⚧️"
        confidence = "Không rõ"
        description = "Xu hướng của bạn khá đa dạng và phong phú. Có thể bạn thuộc cộng đồng LGBT+ hoặc có sở thích đặc biệt."
        emoji = "⚧️"
    
    return {
        'gender': gender,
        'gay_score': gay_score,
        'les_score': les_score,
        'straight_score': straight_score,
        'orientation': orientation,
        'confidence': confidence,
        'description': description,
        'emoji': emoji,
        'analysis_date': datetime.now().strftime("%d/%m/%Y %H:%M")
    }

# ================= TẠO ẢNH KẾT QUẢ =================

def create_orientation_banner(profile_data, analysis_result):
    width, height = 1200, 800
    bg = Image.new("RGBA", (width, height), (25, 25, 40))
    
    # Nền gradient
    draw = ImageDraw.Draw(bg)
    for i in range(height):
        r = int(25 + i * 0.05)
        g = int(25 + i * 0.03)
        b = int(40 + i * 0.02)
        draw.line((0, i, width, i), fill=(r, g, b))
    
    # ====== PHẦN AVATAR ======
    avatar_url = profile_data.get('avatar', '')
    avt_size = 180  # Giảm kích thước để có thêm không gian
    avt_x, avt_y = 60, 80  # Điều chỉnh vị trí
    
    avatar_img = fetch_image(avatar_url)
    if not avatar_img:
        # Tạo avatar mặc định với màu theo giới tính
        if analysis_result['gender'] == "NAM":
            ava_color = (70, 130, 200)
        elif analysis_result['gender'] == "NỮ":
            ava_color = (200, 120, 180)
        else:
            ava_color = (150, 100, 220)
        avatar_img = Image.new("RGBA", (avt_size, avt_size), ava_color)
    
    # Avatar hình tròn
    mask = Image.new("L", (avt_size, avt_size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, avt_size, avt_size), fill=255)
    
    avatar_resized = avatar_img.resize((avt_size, avt_size), Image.Resampling.LANCZOS)
    avatar_circle = Image.new("RGBA", (avt_size, avt_size))
    avatar_circle.paste(avatar_resized, mask=mask)
    
    # Viền avatar theo xu hướng
    if analysis_result['gender'] == "NAM" and analysis_result['gay_score'] > 50:
        border_color = (0, 180, 255)  # Xanh da trời sáng
    elif analysis_result['gender'] == "NỮ" and analysis_result['les_score'] > 50:
        border_color = (255, 120, 200)  # Hồng sáng
    else:
        border_color = (180, 180, 180)  # Xám sáng
    
    # Vẽ viền avatar
    border_width = 6
    draw.ellipse((avt_x-border_width, avt_y-border_width, 
                  avt_x+avt_size+border_width, avt_y+avt_size+border_width), 
                outline=border_color, width=border_width)
    
    bg.paste(avatar_circle, (avt_x, avt_y), avatar_circle)
    
    # ====== PHẦN THÔNG TIN CHÍNH ======
    text_x, text_y = 280, 100  # Điều chỉnh vị trí
    
    # Tên - ĐẢM BẢO KHÔNG ĐÈ LÊN NHAU
    name = profile_data.get('name', 'Người dùng')
    name_font, name_text = fit_text_font(name, 850, 52, min_size=30)
    draw.text((text_x, text_y), name_text, font=name_font, fill=(255, 255, 255))
    
    # Giới tính
    gender_y = text_y + 65  # Tăng khoảng cách
    gender_text = f"Giới tính: {analysis_result['gender']} {analysis_result['emoji']}"
    draw.text((text_x, gender_y), gender_text, font=get_font(32), fill=(200, 220, 255))
    
    # Xu hướng chính - TĂNG KHOẢNG CÁCH
    orient_y = gender_y + 50
    draw.rounded_rectangle((text_x, orient_y, text_x + 650, orient_y + 55), 
                          radius=12, fill=(40, 40, 60))
    
    # Vẽ icon và label xu hướng
    draw.text((text_x + 20, orient_y + 15), "🎯", 
              font=get_emoji_font(28), fill=(255, 255, 200))
    draw.text((text_x + 55, orient_y + 12), "XU HƯỚNG:", 
              font=get_font(26), fill=(255, 255, 200))
    
    # Xu hướng chính (điều chỉnh kích thước)
    orient_font, orient_text = fit_text_font(analysis_result['orientation'], 500, 28)
    orient_color = (0, 255, 150) if "GAY" in analysis_result['orientation'] or "LES" in analysis_result['orientation'] else (255, 220, 100)
    draw.text((text_x + 220, orient_y + 15), orient_text, font=orient_font, fill=orient_color)
    
    # ====== BOX PHÂN TÍCH CHI TIẾT ======
    box_x, box_y = 60, 320  # Điều chỉnh vị trí box thấp hơn
    box_width, box_height = 1080, 400
    create_glass_rect(draw, box_x, box_y, box_width, box_height, radius=20)
    
    # Tiêu đề box
    draw.text((box_x + 30, box_y + 25), "📊 PHÂN TÍCH CHI TIẾT", 
              font=get_font(34), fill=(255, 255, 255))
    
    # ====== BIỂU ĐỒ CHỈ SỐ ======
    indicators = [
        ("STRAIGHT", analysis_result['straight_score'], (100, 220, 100)),
        ("GAY", analysis_result['gay_score'], (0, 180, 255)),
        ("LESBIAN", analysis_result['les_score'], (255, 120, 180))
    ]
    
    bar_start_y = box_y + 80  # Tăng khoảng cách từ tiêu đề
    bar_height = 38  # Tăng chiều cao thanh
    bar_spacing = 25  # Tăng khoảng cách giữa các thanh
    
    for i, (label, value, color) in enumerate(indicators):
        y_pos = bar_start_y + i * (bar_height + bar_spacing)
        
        # Nhãn
        draw.text((box_x + 40, y_pos + 8), label, font=get_font(26), fill=(240, 240, 240))
        
        # Thanh giá trị
        bar_width = int((value / 100) * 820)  # Giảm chiều rộng tối đa
        bar_x = box_x + 200  # Dịch sang phải để tránh đè
        
        # Vẽ thanh nền
        draw.rounded_rectangle((bar_x, y_pos, bar_x + 820, y_pos + bar_height), 
                              radius=6, fill=(50, 50, 70))
        
        # Vẽ thanh giá trị
        if bar_width > 0:
            draw.rounded_rectangle((bar_x, y_pos, bar_x + bar_width, y_pos + bar_height), 
                                  radius=6, fill=color)
        
        # Giá trị phần trăm - ĐẢM BẢO VỊ TRÍ KHÔNG ĐÈ
        value_text = f"{value}%"
        value_font = get_font(30)
        value_width = value_font.getlength(value_text)
        
        # Đặt phần trăm bên phải thanh
        value_x = bar_x + 830
        if value_x + value_width > box_x + box_width - 20:
            value_x = box_x + box_width - value_width - 20
        
        draw.text((value_x, y_pos + 4), value_text, font=value_font, fill=(255, 255, 255))
    
    # ====== MÔ TẢ - FIX LỖI ĐÈ CHỮ ======
    desc_font = get_font(24)
    max_desc_width = 1000
    max_desc_lines = 3  # Giới hạn số dòng
    
    # Tách mô tả thành các dòng
    desc_lines = wrap_text(analysis_result['description'], desc_font, max_desc_width, max_desc_lines)
    
    # Tính vị trí bắt đầu cho mô tả
    desc_start_y = bar_start_y + len(indicators) * (bar_height + bar_spacing) + 30
    
    # Vẽ từng dòng với khoảng cách hợp lý
    line_spacing = 32  # Khoảng cách giữa các dòng
    for i, line in enumerate(desc_lines):
        line_y = desc_start_y + i * line_spacing
        
        # Kiểm tra không vượt quá box
        if line_y + line_spacing > box_y + box_height - 60:
            break
            
        draw.text((box_x + 40, line_y), line, 
                 font=desc_font, fill=(240, 240, 240))
    
    # ====== FOOTER ======
    footer_y = box_y + box_height - 45
    
    # Độ tin cậy
    confidence_text = f"Độ tin cậy: {analysis_result['confidence']}"
    draw.text((box_x + 40, footer_y), confidence_text, 
              font=get_font(20), fill=(180, 200, 180))
    
    # Ngày phân tích
    date_text = f"Ngày phân tích: {analysis_result['analysis_date']}"
    date_font = get_font(18)
    date_width = date_font.getlength(date_text)
    draw.text((box_x + box_width - date_width - 40, footer_y), date_text, 
              font=date_font, fill=(180, 180, 180))
    
    # Watermark
    watermark_text = "Phân tích xu hướng tính dục • v1.5.2"
    watermark_font = get_font(16)
    watermark_width = watermark_font.getlength(watermark_text)
    draw.text((width - watermark_width - 30, height - 30), watermark_text, 
              font=watermark_font, fill=(100, 100, 120))
    
    return bg.convert("RGB")

# ================= XỬ LÝ LỆNH =================

def handle_orientation_command(message, message_object, thread_id, thread_type, author_id, client):
    target_id = author_id
    if message_object.mentions:
        target_id = message_object.mentions[0]['uid']
    elif message_object.quote:
        target_id = message_object.quote.ownerId

    client.sendReaction(message_object, "🔍", thread_id, thread_type)

    try:
        user_info = client.fetchUserInfo(target_id)
        if not user_info or not hasattr(user_info, 'changed_profiles'):
            client.replyMessage(Message(text="❌ Không thể lấy thông tin người dùng."), 
                              message_object, thread_id, thread_type)
            return

        profile = user_info.changed_profiles.get(str(target_id), {})
        
        # Chuẩn bị dữ liệu
        profile_data = {
            'name': profile.get('zaloName', 'Người dùng'),
            'avatar': profile.get('avatar', ''),
            'gender': profile.get('gender', -1),
            'dob': profile.get('dob', 0),
            'cover': profile.get('cover', ''),
            'globalId': profile.get('globalId', '')
        }
        
        # Phân tích giới tính
        detected_gender = detect_gender_advanced(profile_data)
        
        # Phân tích xu hướng
        analysis_result = analyze_sexual_orientation(profile_data, detected_gender)
        
        # Tạo ảnh
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(create_orientation_banner, profile_data, analysis_result)
            image = future.result()

        timestamp = int(time.time())
        img_path = os.path.join(CACHE_PATH, f"orientation_{timestamp}.jpg")
        
        if not os.path.exists(CACHE_PATH):
            os.makedirs(CACHE_PATH)
            
        image.save(img_path, quality=95)
        
        # Tin nhắn kết quả
        result_text = f"{analysis_result['emoji']} KẾT QUẢ PHÂN TÍCH {profile_data['name']}:\n"
        result_text += f"🎯 Giới tính: {analysis_result['gender']}\n"
        result_text += f"🧭 Xu hướng: {analysis_result['orientation']}\n"
        result_text += f"📊 Chi tiết:\n"
        result_text += f"  • STRAIGHT: {analysis_result['straight_score']}%\n"
        result_text += f"  • GAY: {analysis_result['gay_score']}%\n"
        result_text += f"  • LESBIAN: {analysis_result['les_score']}%\n"
        result_text += f"🔍 Độ tin cậy: {analysis_result['confidence']}\n\n"
        result_text += f"💬 {analysis_result['description']}"
        
        client.sendLocalImage(
            img_path,
            thread_id=thread_id,
            thread_type=thread_type,
            width=1200,
            height=800,
            message=Message(text=result_text),
            ttl=120000
        )
        
        client.sendReaction(message_object, "✅", thread_id, thread_type)
        try: 
            os.remove(img_path)
        except: 
            pass

    except Exception as e:
        client.replyMessage(Message(text=f"❌ Lỗi phân tích: {str(e)}"), 
                          message_object, thread_id, thread_type)

def PTA():
    return {
        'phandoan': handle_orientation_command,
        'gayles': handle_orientation_command,
        'xuphuong': handle_orientation_command,
        'orientation': handle_orientation_command,
        'kiemtragay': handle_orientation_command,
        'kiemtrales': handle_orientation_command,
        'phandoantinhduc': handle_orientation_command
    }