import requests
import threading
import re
from bs4 import BeautifulSoup
from zlapi.models import Message

des = {
    'version': "1.1.0",
    'credits': "ngbao",
    'description': "Xem giá xăng dầu hôm nay (Sửa lỗi lấy sai giá)",
    'power': "Thành viên"
}

def handle_giaxang_command(message, message_object, thread_id, thread_type, author_id, client):
    def process():
        try:
            client.sendReaction(message_object, "⛽", thread_id, thread_type)
            
            # Sử dụng trang cập nhật giá chính thống
            url = "https://webgia.com/gia-xang-dau/petrolimex/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            response.encoding = 'utf-8' # Đảm bảo không lỗi font tiếng Việt
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Tìm bảng giá xăng dựa trên class/id thực tế của trang webgia
            table = soup.find('table', {'class': 'table table-bordered table-hover'})
            if not table:
                raise Exception("Không tìm thấy bảng dữ liệu")

            rows = table.find_all('tr')
            
            msg = "⛽ [ 𝐆𝐈𝐀́ 𝐗𝐀̆𝐍𝐆 𝐃𝐀̂̀𝐔 𝐇𝐎̂𝐌 𝐍𝐀𝐘 ]\n"
            msg += "──────────────────\n"
            
            count = 0
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    name = cols[0].text.strip()
                    # Chỉ lấy các loại xăng dầu phổ biến để tránh tin nhắn quá dài
                    if any(x in name.upper() for x in ["RON 95", "E5 RON 92", "DIESEL", "DẦU"]):
                        price = cols[1].text.strip()
                        # Làm đẹp giá tiền (ví dụ: 23.500)
                        msg += f"🔹 {name}: {price} VNĐ\n"
                        count += 1
                if count > 5: break # Giới hạn 6 dòng

            msg += "──────────────────\n"
            msg += "🕒 Dữ liệu cập nhật từ Petrolimex"
            
            client.replyMessage(Message(text=msg), message_object, thread_id, thread_type)

        except Exception as e:
            print(f"Lỗi giá xăng: {e}")
            # Dữ liệu dự phòng nếu web lỗi
            error_msg = (
                "⚠️ Không thể kết nối máy chủ Petrolimex.\n"
                "Giá tham khảo vùng 1:\n"
                "🔹 Xăng RON 95-III: 21.000đ\n"
                "🔹 Xăng E5 RON 92: 19.850đ\n"
                "🔹 Dầu Diesel 0,05S: 18.500đ"
            )
            client.replyMessage(Message(text=error_msg), message_object, thread_id, thread_type)

    threading.Thread(target=process, daemon=True).start()

def PTA():
    return {'giaxang': handle_giaxang_command, 'xang': handle_giaxang_command}