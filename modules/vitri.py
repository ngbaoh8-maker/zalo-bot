from zlapi.models import *
import time
import re

des = {
    'version': "1.0.0",
    'credits': "Bot DCM",
    'description': "Gửi vị trí định vị theo tọa độ",
    'power': "Thành Viên"
}

def handle_vitri_command(message, message_object, thread_id, thread_type, author_id, client):
    """
    Lệnh gửi vị trí theo tọa độ nhập vào.
    
    Cách dùng:
        !vitri <latitude>,<longitude>
        !vitri <latitude>,<longitude> <tên địa điểm>
    
    Ví dụ:
        !vitri 10.762622,106.660172
        !vitri 10.762622,106.660172 Quận 5, TP.HCM
        !vitri 130.120,102.120
    """
    try:
        # Lấy phần text sau lệnh vitri
        # Hỗ trợ cả prefix và không prefix
        text = message
        
        # Loại bỏ phần lệnh, lấy phần tọa độ
        # Tìm pattern: vitri <nội dung>
        match = re.search(r'vitri\s+(.*)', text, re.IGNORECASE)
        if not match:
            client.replyMessage(
                Message(text="⚠️ Sai cú pháp!\n\n📌 Cách dùng:\nvitri <lat>,<lng>\nvitri <lat>,<lng> <tên địa điểm>\n\n📍 Ví dụ:\nvitri 10.762622,106.660172\nvitri 10.762622,106.660172 Quận 5 HCM"),
                message_object, thread_id, thread_type, ttl=30000
            )
            return
        
        content = match.group(1).strip()
        
        # Tách tọa độ và tên địa điểm (nếu có)
        # Hỗ trợ các format:
        #   10.762622,106.660172
        #   10.762622, 106.660172
        #   10.762622,106.660172 Tên địa điểm
        coord_match = re.match(r'([+-]?\d+\.?\d*)\s*[,]\s*([+-]?\d+\.?\d*)(.*)', content)
        if not coord_match:
            client.replyMessage(
                Message(text="⚠️ Tọa độ không hợp lệ!\n\n📌 Format: <latitude>,<longitude>\n📍 Ví dụ: vitri 10.762622,106.660172"),
                message_object, thread_id, thread_type, ttl=30000
            )
            return
        
        latitude = float(coord_match.group(1))
        longitude = float(coord_match.group(2))
        title = coord_match.group(3).strip() if coord_match.group(3) else None
        
        # Gửi vị trí
        if title:
            client.sendLocation(
                latitude=latitude,
                longitude=longitude,
                thread_id=thread_id,
                thread_type=thread_type,
                title=title,
                address=f"📍 {title}\nLat: {latitude}, Lng: {longitude}",
                ttl=300000
            )
        else:
            client.sendLocation(
                latitude=latitude,
                longitude=longitude,
                thread_id=thread_id,
                thread_type=thread_type,
                title=f"📍 Vị trí: {latitude}, {longitude}",
                address=f"Lat: {latitude}, Lng: {longitude}",
                ttl=300000
            )
        
        # Thông báo đã gửi
        client.replyMessage(
            Message(text=f"✅ Đã gửi vị trí!\n📍 Tọa độ: {latitude}, {longitude}" + (f"\n📌 Địa điểm: {title}" if title else "")),
            message_object, thread_id, thread_type, ttl=15000
        )
        
    except ValueError as e:
        client.replyMessage(
            Message(text=f"⚠️ Tọa độ không hợp lệ! Vui lòng nhập đúng số.\n📍 Ví dụ: vitri 10.762622,106.660172"),
            message_object, thread_id, thread_type, ttl=30000
        )
    except Exception as e:
        client.replyMessage(
            Message(text=f"❌ Lỗi khi gửi vị trí: {e}"),
            message_object, thread_id, thread_type, ttl=30000
        )

def PTA():
    return {
        'vitri': handle_vitri_command
    }
