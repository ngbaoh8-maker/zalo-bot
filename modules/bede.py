import os
import json
from config import ADMIN
from zlapi.models import MultiMsgStyle, Mention,MessageStyle
from zlapi.models import Message
import random
import datetime
from datetime import datetime
from config import PREFIX
import random

des = {
    'version': "1.0.9",
    'credits': "ngbao",
    'description': "Check độ bê đê",
    'power': "Thành viên"
  }
# Đường dẫn tới tệp lưu trữ thông tin sử dụng
GAY_TEST_FILE = 'gay_test_usage.json'

# Hàm tải thông tin sử dụng từ tệp JSON
def load_usage_data():
    if os.path.exists(GAY_TEST_FILE):
        with open(GAY_TEST_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

# Hàm lưu thông tin sử dụng vào tệp JSON
def save_usage_data(data):
    with open(GAY_TEST_FILE, 'w') as f:
        json.dump(data, f)

# Hàm xử lý đo độ gay
def handle_gay_test(message, message_object, thread_id, thread_type, author_id, client):
    mentions = message_object.mentions  # Lấy danh sách người dùng được tag
    usage_data = load_usage_data()  # Tải thông tin sử dụng

    # Kiểm tra nếu không có ai được tag
    if not mentions or len(mentions) < 1:
        client.replyMessage(
            Message(text="Vui lòng nhập cú pháp: 'gay @name'"),
            message_object, thread_id, thread_type,ttl=10000
        )
        return

    # Lấy ID và tên của người được tag
    person_id = mentions[0].id
    person_name = mentions[0].name

    # Kiểm tra số lần sử dụng
    now = datetime.now()

    # Nếu người này đã từng được tính phần trăm trước đó, lấy lại giá trị đó
    if person_id in usage_data:
        gay_percentage = usage_data[person_id]['gay_percentage']
        last_used = datetime.fromisoformat(usage_data[person_id]['last_used'])
        count = usage_data[person_id]['count']

        # Kiểm tra xem đã sử dụng quá số lần cho phép trong 24 giờ chưa
        if count >= 2 and now < last_used + timedelta(days=1):
            time_remaining = (last_used + timedelta(days=1) - now).total_seconds()
            hours_remaining = int(time_remaining // 3600)
            minutes_remaining = int((time_remaining % 3600) // 60)
            client.replyMessage(
                Message(text=f"{person_name} đã sử dụng quá số lần cho phép. Vui lòng quay lại sau {hours_remaining} giờ {minutes_remaining} phút."),
                message_object, thread_id, thread_type,ttl=10000
            )
            return

        # Cập nhật số lần sử dụng và thời gian gần nhất
        usage_data[person_id]['count'] += 1
        usage_data[person_id]['last_used'] = str(now)
    else:
        # Nếu đây là lần đầu tiên, tạo ngẫu nhiên phần trăm độ gay và lưu lại
        gay_percentage = random.randint(80, 100)
        usage_data[person_id] = {
            'gay_percentage': gay_percentage,
            'count': 1,
            'last_used': str(now)
        }

    # Lưu lại thông tin sử dụng
    save_usage_data(usage_data)

    # Phản hồi kết quả với phần trăm gay đã lưu
    client.replyMessage(
        Message(text=f"🏳️‍🌈 Thằng được bạn tag có độ bê đê là {gay_percentage}%! 🏳️‍🌈"),
        message_object, thread_id, thread_type, ttl=120000
    )

# Hàm trả về lệnh của bot
def PTA():
    return {
        'bede': handle_gay_test
    }