import os
import re

def main():
    with open('main.py', 'r', encoding='utf-8') as f:
        main_content = f.read()
        
    with open('event/event.py', 'r', encoding='utf-8') as f:
        event_content = f.read()

    # 1. Bỏ import từ event/event.py
    main_content = re.sub(r'from event\.event import handleGroupEvent\n', '', main_content)

    # 2. Cập nhật import PIL trong main.py
    main_content = re.sub(
        r'from PIL import Image\n', 
        'from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps\nfrom io import BytesIO\n', 
        main_content
    )

    # 3. Trích xuất tất cả các biến, hằng số và hàm từ event.py (Bỏ các dòng import ở đầu)
    # Lấy phần sau các import
    event_logic = re.sub(r'^(import .*|from .*)\n', '', event_content, flags=re.MULTILINE)
    event_logic = event_logic.strip()

    # 4. Chèn event_logic vào ngay trước class Client
    insert_pos = main_content.find('class Client(ZaloAPI):')
    if insert_pos == -1:
        print("Không tìm thấy class Client(ZaloAPI):")
        return
        
    new_main_content = main_content[:insert_pos] + "\n# ==================== EVENT LOGIC ====================\n" + event_logic + "\n\n# =====================================================\n\n" + main_content[insert_pos:]

    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(new_main_content)

    print("Done")

if __name__ == '__main__':
    main()
