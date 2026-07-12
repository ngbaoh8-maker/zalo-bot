import requests
import threading
import time
import random
import re
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from zlapi.models import Message, MultiMsgStyle, MessageStyle

des = {
    'version': "1.0.0",
    'credits': "Bot System",
    'description': "SMS Ảo - Lấy số điện thoại ảo VN miễn phí & nhận mã OTP trong 360s",
    'power': "Thành viên"
}

# ============ CẤU HÌNH ============
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'vi,en-US;q=0.9,en;q=0.8',
}
POLL_INTERVAL = 5       # Giây giữa mỗi lần kiểm tra
MAX_WAIT = 360          # Tổng thời gian chờ tối đa (giây)
COOLDOWN = 60           # Cooldown giữa các lần dùng (giây)

# Lưu trạng thái người dùng
_user_sessions = {}     # author_id -> { 'phone', 'thread_id', 'stop', 'timestamp' }
_user_cooldowns = {}    # author_id -> last_use_timestamp


# ============ HÀM SCRAPE SỐ ĐIỆN THOẠI VN TỪ SMS24.ME ============
def get_vn_numbers():
    """Lấy danh sách số điện thoại VN miễn phí từ sms24.me"""
    try:
        r = requests.get('https://sms24.me/en/countries/vn', headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return []
        soup = BeautifulSoup(r.text, 'html.parser')
        numbers = []
        for a in soup.find_all('a'):
            href = a.get('href', '')
            if '/numbers/' in href:
                num = href.rstrip('/').split('/')[-1]
                if num.startswith('84') and num.isdigit():
                    numbers.append(num)
        return list(set(numbers))
    except Exception as e:
        logging.error(f"[SMSAO] Lỗi lấy danh sách số VN: {e}")
        return []


# ============ HÀM ĐỌC TIN NHẮN CỦA MỘT SỐ ============
def get_messages_for_number(phone_number):
    """Đọc tất cả tin nhắn gần đây của một số điện thoại từ sms24.me"""
    try:
        url = f"https://sms24.me/en/numbers/{phone_number}"
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return []
        soup = BeautifulSoup(r.text, 'html.parser')
        messages = []

        # Tìm bảng tin nhắn
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')
            for row in rows[1:]:  # Bỏ header
                cols = row.find_all('td')
                if len(cols) >= 3:
                    sender = cols[0].text.strip()
                    text = cols[1].text.strip()
                    time_str = cols[2].text.strip()
                    messages.append({
                        'sender': sender,
                        'text': text,
                        'time': time_str
                    })
            return messages

        # Fallback: tìm div class message hoặc sms-item
        for div in soup.find_all('div', class_=re.compile(r'message|sms|item')):
            text = div.text.strip()
            if text and len(text) > 5:
                messages.append({
                    'sender': 'Unknown',
                    'text': text[:300],
                    'time': 'N/A'
                })

        return messages
    except Exception as e:
        logging.error(f"[SMSAO] Lỗi đọc tin nhắn {phone_number}: {e}")
        return []


# ============ FALLBACK: SỐ TỪ SMS-ONLINE.CO ============
def get_all_numbers():
    """Lấy danh sách số từ sms-online.co (quốc tế)"""
    try:
        r = requests.get('https://sms-online.co/receive-free-sms', headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return []
        numbers = list(set(re.findall(r'/receive-free-sms/(\d+)', r.text)))
        return numbers
    except Exception:
        return []


def get_messages_smsonline(phone_number):
    """Đọc tin nhắn từ sms-online.co"""
    try:
        url = f"https://sms-online.co/receive-free-sms/{phone_number}"
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return []
        soup = BeautifulSoup(r.text, 'html.parser')
        messages = []
        for item in soup.find_all('div', class_='list-item'):
            header_div = item.find('div', class_='list-item-header')
            content_div = item.find('div', class_='list-item-content')
            if not header_div or not content_div:
                continue
            title_h3 = header_div.find('h3', class_='list-item-title')
            sender = title_h3.text.strip() if title_h3 else "Unknown"
            meta_span = header_div.find('span', class_='list-item-meta')
            time_str = meta_span.text.strip() if meta_span else "N/A"
            text = content_div.text.strip()
            messages.append({
                'sender': sender,
                'time': time_str,
                'text': text
            })
        return messages
    except Exception as e:
        logging.error(f"[SMSAO] Lỗi đọc tin nhắn sms-online {phone_number}: {e}")
        return []


# ============ TRÍCH XUẤT MÃ OTP TỪ TIN NHẮN ============
def extract_otp(text):
    """Tìm mã OTP (4-8 chữ số) trong nội dung tin nhắn"""
    patterns = [
        r'\b(\d{6})\b',  # 6 số
        r'\b(\d{4})\b',  # 4 số
        r'\b(\d{5})\b',  # 5 số
        r'\b(\d{8})\b',  # 8 số
    ]
    for p in patterns:
        match = re.search(p, text)
        if match:
            return match.group(1)
    return None


# ============ LUỒNG POLLING TIN NHẮN ============
def poll_messages_thread(phone_number, source, author_id, thread_id, thread_type, message_object, client):
    """Thread chạy nền: kiểm tra tin nhắn mới mỗi 5 giây trong 360 giây"""
    start_time = time.time()

    # Lấy tin nhắn ban đầu (để so sánh tìm tin mới)
    if source == 'sms24':
        old_msgs = get_messages_for_number(phone_number)
    else:
        old_msgs = get_messages_smsonline(phone_number)

    old_texts = set()
    for m in old_msgs:
        old_texts.add(m['text'][:100])

    found_count = 0

    while True:
        # Kiểm tra dừng
        session = _user_sessions.get(author_id)
        if not session or session.get('stop'):
            break

        elapsed = time.time() - start_time
        if elapsed >= MAX_WAIT:
            # Hết thời gian
            remaining_msg = (
                f"⏰ [ HẾT THỜI GIAN ] ⏰\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📱 Số: +{phone_number}\n"
                f"⏳ Đã chờ: {MAX_WAIT}s\n"
                f"📩 Tin nhắn mới: {found_count}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"💡 Dùng lại: smsao"
            )
            try:
                client.replyMessage(
                    Message(text=remaining_msg),
                    message_object, thread_id, thread_type
                )
            except Exception:
                pass
            break

        time.sleep(POLL_INTERVAL)

        # Lấy tin nhắn mới
        try:
            if source == 'sms24':
                new_msgs = get_messages_for_number(phone_number)
            else:
                new_msgs = get_messages_smsonline(phone_number)
        except Exception:
            continue

        # So sánh tìm tin nhắn mới
        for m in new_msgs:
            key = m['text'][:100]
            if key not in old_texts:
                old_texts.add(key)
                found_count += 1

                otp = extract_otp(m['text'])
                otp_line = f"🔑 Mã OTP: {otp}\n" if otp else ""

                sms_msg = (
                    f"📩 [ TIN NHẮN MỚI ] 📩\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"📱 Số nhận: +{phone_number}\n"
                    f"👤 Người gửi: {m['sender']}\n"
                    f"🕐 Thời gian: {m['time']}\n"
                    f"{otp_line}"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"💬 Nội dung:\n{m['text'][:500]}\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"⏳ Còn lại: {int(MAX_WAIT - elapsed)}s"
                )
                try:
                    client.replyMessage(
                        Message(text=sms_msg),
                        message_object, thread_id, thread_type
                    )
                except Exception:
                    pass

    # Dọn dẹp session
    if author_id in _user_sessions:
        del _user_sessions[author_id]


# ============ LỆNH CHÍNH ============
def handle_smsao(message, message_object, thread_id, thread_type, author_id, client):
    parts = message.strip().split()
    cmd = parts[1].lower() if len(parts) > 1 else ""

    # --- Hiển thị hướng dẫn ---
    if cmd in ['help', 'hdsd', '']:
        if cmd == '' and len(parts) == 1:
            # Mặc định: lấy số mới
            pass  # Tiếp tục xuống dưới
        else:
            help_text = (
                "📲 [ SMS ẢO - HƯỚNG DẪN ] 📲\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🔹 smsao → Lấy số VN ảo & chờ SMS 360s\n"
                "🔹 smsao list → Xem danh sách số VN\n"
                "🔹 smsao read <số> → Đọc tin nhắn của số\n"
                "🔹 smsao stop → Dừng chờ tin nhắn\n"
                "🔹 smsao global → Lấy số quốc tế\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "💡 Tự động đào số miễn phí\n"
                "⏳ Chờ tin nhắn tối đa 360 giây\n"
                "🔑 Tự trích xuất mã OTP"
            )
            client.replyMessage(
                Message(text=help_text),
                message_object, thread_id, thread_type
            )
            return

    # --- Dừng chờ ---
    if cmd == 'stop':
        session = _user_sessions.get(author_id)
        if session:
            session['stop'] = True
            client.replyMessage(
                Message(text="🛑 Đã dừng chờ tin nhắn!"),
                message_object, thread_id, thread_type
            )
        else:
            client.replyMessage(
                Message(text="❌ Bạn không có phiên SMS ảo nào đang chạy."),
                message_object, thread_id, thread_type
            )
        return

    # --- Xem danh sách số VN ---
    if cmd == 'list':
        try:
            client.sendReaction(message_object, "🔍", thread_id, thread_type)
        except Exception:
            pass
        numbers = get_vn_numbers()
        if not numbers:
            client.replyMessage(
                Message(text="❌ Không tìm thấy số VN nào. Thử lại sau!"),
                message_object, thread_id, thread_type
            )
            return
        num_list = "\n".join([f"  📱 +{n}" for n in numbers[:15]])
        msg = (
            f"📋 [ DANH SÁCH SỐ VN ẢO ] 📋\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{num_list}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 Tổng: {len(numbers)} số\n"
            f"💡 Dùng: smsao read <số> để xem tin nhắn"
        )
        client.replyMessage(
            Message(text=msg),
            message_object, thread_id, thread_type
        )
        return

    # --- Đọc tin nhắn của số cụ thể ---
    if cmd == 'read':
        if len(parts) < 3:
            client.replyMessage(
                Message(text="❌ Cú pháp: smsao read <số>\nVí dụ: smsao read 84357963610"),
                message_object, thread_id, thread_type
            )
            return
        phone = parts[2].strip().replace('+', '')
        try:
            client.sendReaction(message_object, "📖", thread_id, thread_type)
        except Exception:
            pass

        if phone.startswith('84'):
            msgs = get_messages_for_number(phone)
        else:
            msgs = get_messages_smsonline(phone)

        if not msgs:
            client.replyMessage(
                Message(text=f"📭 Không có tin nhắn nào cho số +{phone}"),
                message_object, thread_id, thread_type
            )
            return

        result = f"📬 [ TIN NHẮN CỦA +{phone} ] 📬\n━━━━━━━━━━━━━━━━━━\n"
        for i, m in enumerate(msgs[:10]):
            otp = extract_otp(m['text'])
            otp_tag = f" 🔑{otp}" if otp else ""
            result += f"[{i+1}] 👤{m['sender']} ({m['time']}){otp_tag}\n💬 {m['text'][:120]}\n\n"
        result += f"━━━━━━━━━━━━━━━━━━\n📊 Hiển thị {min(len(msgs), 10)}/{len(msgs)} tin"

        client.replyMessage(
            Message(text=result),
            message_object, thread_id, thread_type
        )
        return

    # --- Lấy số quốc tế ---
    if cmd == 'global':
        try:
            client.sendReaction(message_object, "🌍", thread_id, thread_type)
        except Exception:
            pass
        numbers = get_all_numbers()
        if not numbers:
            client.replyMessage(
                Message(text="❌ Không lấy được số quốc tế. Thử lại sau!"),
                message_object, thread_id, thread_type
            )
            return
        num_list = "\n".join([f"  📱 +{n}" for n in numbers[:10]])
        msg = (
            f"🌍 [ SỐ QUỐC TẾ MIỄN PHÍ ] 🌍\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{num_list}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 Tổng: {len(numbers)} số\n"
            f"💡 Dùng: smsao read <số> để xem tin nhắn"
        )
        client.replyMessage(
            Message(text=msg),
            message_object, thread_id, thread_type
        )
        return

    # ============ MẶC ĐỊNH: LẤY SỐ VN & CHỜ SMS ============

    # Kiểm tra session đang chạy
    if author_id in _user_sessions:
        client.replyMessage(
            Message(text="⚠️ Bạn đang có phiên SMS ảo đang chạy!\nDùng: smsao stop để dừng trước."),
            message_object, thread_id, thread_type
        )
        return

    # Kiểm tra cooldown
    now = time.time()
    last_use = _user_cooldowns.get(author_id, 0)
    if now - last_use < COOLDOWN:
        wait = int(COOLDOWN - (now - last_use))
        client.replyMessage(
            Message(text=f"⏳ Cooldown: Vui lòng đợi {wait} giây."),
            message_object, thread_id, thread_type
        )
        return

    try:
        client.sendReaction(message_object, "📲", thread_id, thread_type)
    except Exception:
        pass

    # Lấy số VN
    client.replyMessage(
        Message(text="🔄 Đang đào số điện thoại VN ảo miễn phí..."),
        message_object, thread_id, thread_type
    )

    numbers = get_vn_numbers()
    source = 'sms24'

    if not numbers:
        # Fallback sang sms-online.co (quốc tế)
        numbers = get_all_numbers()
        source = 'smsonline'

    if not numbers:
        client.replyMessage(
            Message(text="❌ Không tìm được số điện thoại ảo nào. Vui lòng thử lại sau!"),
            message_object, thread_id, thread_type
        )
        return

    # Chọn ngẫu nhiên
    phone = random.choice(numbers)
    _user_cooldowns[author_id] = now

    # Tạo session
    _user_sessions[author_id] = {
        'phone': phone,
        'thread_id': thread_id,
        'stop': False,
        'timestamp': now
    }

    time_str = datetime.now().strftime("%H:%M:%S - %d/%m/%Y")
    country = "🇻🇳 Việt Nam" if source == 'sms24' else "🌍 Quốc tế"

    start_msg = (
        f"📲 [ SMS ẢO - SỐ MỚI ] 📲\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 Số điện thoại: +{phone}\n"
        f"🌐 Nguồn: {country}\n"
        f"⏰ Bắt đầu: {time_str}\n"
        f"⏳ Thời gian chờ: {MAX_WAIT}s (6 phút)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Đang lắng nghe tin nhắn...\n"
        f"📩 Mỗi khi có SMS mới sẽ gửi ngay!\n"
        f"🔑 Tự động trích xuất mã OTP\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 Dùng số trên để đăng ký dịch vụ\n"
        f"🛑 Gõ: smsao stop để dừng"
    )

    try:
        client.sendReaction(message_object, "✅", thread_id, thread_type)
    except Exception:
        pass

    client.replyMessage(
        Message(text=start_msg),
        message_object, thread_id, thread_type
    )

    # Bắt đầu thread polling
    t = threading.Thread(
        target=poll_messages_thread,
        args=(phone, source, author_id, thread_id, thread_type, message_object, client),
        daemon=True
    )
    t.start()


def PTA():
    return {
        'smsao': handle_smsao
    }
