# -*- coding: UTF-8 -*-
import requests
import re
from zlapi.models import Message

des = {
    'version': "1.0.0",
    'credits': "Bot DCM",
    'description': "Gửi vị trí định vị theo địa chỉ IP/Domain",
    'power': "Thành Viên"
}

def handle_local_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        text = message
        
        # Tìm pattern: local <nội dung>
        match = re.search(r'local\s+(.*)', text, re.IGNORECASE)
        if not match:
            client.replyMessage(
                Message(text="⚠️ Sai cú pháp!\n\n📌 Cách dùng:\nlocal <IP/Domain>\n\n📍 Ví dụ:\nlocal 8.8.8.8\nlocal google.com"),
                message_object, thread_id, thread_type, ttl=30000
            )
            return
            
        query = match.group(1).strip()
        if not query:
            client.replyMessage(
                Message(text="⚠️ Vui lòng nhập IP hoặc Domain cần định vị!"),
                message_object, thread_id, thread_type, ttl=30000
            )
            return

        # Gọi API lấy thông tin IP
        url = f"http://ip-api.com/json/{query}?lang=vi"
        try:
            res = requests.get(url, timeout=5).json()
        except Exception as e:
            client.replyMessage(
                Message(text=f"❌ Lỗi kết nối đến dịch vụ định vị IP: {e}"),
                message_object, thread_id, thread_type, ttl=30000
            )
            return

        if res.get("status") == "fail":
            error_msg = res.get("message", "Không xác định")
            client.replyMessage(
                Message(text=f"❌ Định vị thất bại cho '{query}'!\nLý do: {error_msg}"),
                message_object, thread_id, thread_type, ttl=30000
            )
            return

        lat = res.get("lat")
        lon = res.get("lon")
        ip_addr = res.get("query")
        country = res.get("country", "Không rõ")
        region = res.get("regionName", "Không rõ")
        city = res.get("city", "Không rõ")
        isp = res.get("isp", "Không rõ")
        timezone = res.get("timezone", "Không rõ")

        # Gửi tin nhắn text chi tiết trước
        info_text = (
            f"🔍 THÔNG TIN IP: {ip_addr}\n"
            f"📌 Quốc gia: {country}\n"
            f"📍 Khu vực/Tỉnh: {region}\n"
            f"🏙️ Thành phố: {city}\n"
            f"🏢 Nhà mạng (ISP): {isp}\n"
            f"🌐 Tọa độ: {lat}, {lon}\n"
            f"🕒 Múi giờ: {timezone}"
        )
        
        client.replyMessage(
            Message(text=info_text),
            message_object, thread_id, thread_type, ttl=300000
        )

        # Gửi kèm bản đồ vị trí native Zalo
        if lat is not None and lon is not None:
            client.sendLocation(
                latitude=lat,
                longitude=lon,
                thread_id=thread_id,
                thread_type=thread_type,
                title=f"Vị trí IP: {ip_addr}",
                address=f"{city}, {region}, {country}\nISP: {isp}",
                ttl=300000
            )

    except Exception as e:
        client.replyMessage(
            Message(text=f"❌ Lỗi hệ thống: {e}"),
            message_object, thread_id, thread_type, ttl=30000
        )

def PTA():
    return {
        'local': handle_local_command
    }
