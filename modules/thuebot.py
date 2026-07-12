import os
import logging
import json
from zlapi.models import Message, Mention, ThreadType
import datetime
import threading
import time
import unicodedata
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

des = {
    'version': "1.1.1",
    'credits': "ngbao",
    'description': "Quản lý user thuê bot, thêm, sửa, xóa hạn thuê bot.",
    'power': "Thành viên"
}

USER_DATA_FILE = 'data/user_bot_rental.json'

def init_user_data():
    if not os.path.exists('data'):
        os.makedirs('data')
    if not os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=4)

def read_user_data():
    try:
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"[read_user_data] Error: {e}")
        init_user_data()
        return {}

def write_user_data(data):
    try:
        with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(f"[write_user_data] Error: {e}")

def validate_date(date_str):
    try:
        return datetime.datetime.strptime(date_str, '%d/%m/%Y')
    except ValueError:
        logging.warning(f"[validate_date] Invalid date format: {date_str}")
        return None

def get_remaining_days(end_date_str):
    end_date = validate_date(end_date_str)
    if not end_date:
        return None
    today = datetime.datetime.now()
    delta = end_date.date() - today.date()
    return max(0, delta.days)

def is_primary_admin(author_id):
    try:
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'seting.json')
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return str(author_id) == str(data.get('admin'))
    except Exception as e:
        logging.error(f"[is_primary_admin] Error: {e}")
        return False

def get_user_name(client, uid):
    try:
        user_info = client.fetchUserInfo(uid)
        if not user_info or not hasattr(user_info, 'changed_profiles') or not user_info.changed_profiles:
            logging.warning(f"[get_user_name] No user info or changed_profiles for UID: {uid}")
            return 'Không xác định'

        author_info = user_info.changed_profiles.get(uid, {})
        name = author_info.get('zaloName', 'Không xác định')
        return name
    except Exception as e:
        logging.error(f"[get_user_name] Failed to fetch name for user {uid}: {e}")
        return 'Không xác định'

def normalize_username(name):
    if not isinstance(name, str):
        return ""
    name = name.lower()
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('utf-8')
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def find_user_by_normalized_name(user_data, target_name):
    normalized_target = normalize_username(target_name)
    if not normalized_target:
        return None

    for stored_username, _ in user_data.items():
        if normalize_username(stored_username) == normalized_target:
            return stored_username
    return None

def send_expiry_warning_auto(client, user_id, thread_id, username, author_id=None, message_object=None):
    msg_text = f"Cảnh báo: Thời hạn thuê bot của {username} đã hết! Vui lòng gia hạn để tiếp tục sử dụng."
    msg = Message(text=msg_text)
    sent = False

    try:
        client.sendMessage(msg, thread_id=user_id, thread_type=ThreadType.USER)
        logging.info(f"[send_expiry_warning_auto] Sent expiry warning to user {user_id} (thread_id={user_id}, thread_type=USER)")
        sent = True
    except Exception as e:
        logging.error(f"[send_expiry_warning_auto] Failed to send expiry warning to user {user_id}: {e}")

    if thread_id and thread_id != user_id:
        try:
            thread_type = ThreadType.GROUP if thread_id.startswith('g') else ThreadType.USER
            client.sendMessage(msg, thread_id=thread_id, thread_type=thread_type)
            logging.info(f"[send_expiry_warning_auto] Sent expiry warning in thread {thread_id} for user {user_id}")
            sent = True
        except Exception as e:
            logging.error(f"[send_expiry_warning_auto] Failed to send expiry warning in thread {thread_id}: {e}")

    if author_id and author_id not in [user_id, thread_id]:
        try:
            client.sendMessage(msg, thread_id=author_id, thread_type=ThreadType.USER)
            logging.info(f"[send_expiry_warning_auto] Sent expiry warning to author {author_id} for user {user_id}")
            sent = True
        except Exception as e:
            logging.error(f"[send_expiry_warning_auto] Failed to send expiry warning to author {author_id}: {e}")

    if message_object and not sent:
        try:
            thread_type = ThreadType.GROUP if message_object.thread_id.startswith('g') else ThreadType.USER
            client.replyMessage(msg, message_object, thread_id, thread_type, ttl=12000)
            logging.info(f"[send_expiry_warning_auto] Replied expiry warning in thread {thread_id} for user {user_id}")
            sent = True
        except Exception as e:
            logging.error(f"[send_expiry_warning_auto] Failed to reply expiry warning in thread {thread_id}: {e}")

    return sent

def check_expiry_and_notify(client):
    logging.info("[check_expiry_and_notify] Scheduler started")
    while True:
        try:
            user_data = read_user_data()
            today = datetime.datetime.now()
            nearest_expiry = None

            expired_users = []
            for username, info in user_data.items():
                end_date = validate_date(info['end_date'])
                if not end_date:
                    logging.warning(f"[check_expiry_and_notify] Invalid end_date for user {username}: {info['end_date']}")
                    continue

                if end_date.date() <= today.date():
                    user_id = info['user_id']
                    thread_id = info.get('thread_id', user_id)
                    author_id = info.get('added_by')
                    send_expiry_warning_auto(client, user_id, thread_id, username, author_id)
                    expired_users.append(username)
                else:
                    if nearest_expiry is None or end_date < nearest_expiry:
                        nearest_expiry = end_date

            if expired_users:
                for username in expired_users:
                    if username in user_data:
                        del user_data[username]
                        logging.info(f"[check_expiry_and_notify] Removed expired user {username} from data")
                write_user_data(user_data)

            time_to_wait = 300
            if nearest_expiry:
                time_to_next_check_seconds = (nearest_expiry - today).total_seconds()
                time_to_wait = max(60, min(time_to_next_check_seconds + 60, 86400)) 

            logging.info(f"[check_expiry_and_notify] Next check in {time_to_wait / 60:.1f} minutes")
            time.sleep(time_to_wait)
        except Exception as e:
            logging.error(f"[check_expiry_and_notify] Scheduler exception: {e}")
            time.sleep(60)

def handle_usbot_command(message, message_object, thread_id, thread_type, author_id, client):
    if not is_primary_admin(author_id):
        client.replyMessage(
            Message(
                text="Chỉ admin mới được dùng lệnh này.",
                mention=Mention(author_id, length=len("@member"), offset=0)
            ),
            message_object, thread_id, thread_type, ttl=12000
        )
        return

    init_user_data()
    args = message.strip().split()

    if len(args) < 3:
        client.replyMessage(
            Message(
                text="@member Dùng sai rồi bro, cú pháp: nsbot <ngày/tháng/năm thuê> <ngày/tháng/năm hết hạn> <@tag> (trong nhóm) hoặc nsbot <ngày/tháng/năm thuê> <ngày/tháng/năm hết hạn> (nhắn riêng)",
                mention=Mention(author_id, length=len("@member"), offset=0)
            ),
            message_object, thread_id, thread_type, ttl=12000
        )
        return

    start_date = args[1]
    end_date = args[2]

    start_datetime = validate_date(start_date)
    end_datetime = validate_date(end_date)

    if not start_datetime or not end_datetime:
        client.replyMessage(
            Message(
                text="@member Ngày sai format rồi bro, phải là dd/mm/yyyy nha",
                mention=Mention(author_id, length=len("@member"), offset=0)
            ),
            message_object, thread_id, thread_type, ttl=12000
        )
        return

    if start_datetime > end_datetime:
        client.replyMessage(
            Message(
                text="@member Ngày thuê phải trước ngày hết hạn chứ bro, check lại đi",
                mention=Mention(author_id, length=len("@member"), offset=0)
            ),
            message_object, thread_id, thread_type, ttl=12000
        )
        return

    user_id_to_add = None
    username_to_add = None

    if thread_type == ThreadType.USER:
        user_id_to_add = author_id
        username_to_add = get_user_name(client, user_id_to_add)
    else:
        if not message_object.mentions or not message_object.mentions[0].get('uid'):
            client.replyMessage(
                Message(
                    text="@member Phải tag người dùng trong nhóm bro, kiểu @user nha",
                    mention=Mention(author_id, length=len("@member"), offset=0)
                ),
                message_object, thread_id, thread_type, ttl=12000
            )
            return
        user_id_to_add = message_object.mentions[0]['uid']
        username_to_add = get_user_name(client, user_id_to_add)

    if username_to_add == 'Không xác định':
        client.replyMessage(
            Message(
                text="@member Không lấy được tên user bro, thử lại đi",
                mention=Mention(author_id, length=len("@member"), offset=0)
            ),
            message_object, thread_id, thread_type, ttl=12000
        )
        return

    user_data = read_user_data()

    existing_username_key = find_user_by_normalized_name(user_data, username_to_add)

    if existing_username_key:
        current_end_date_str = user_data[existing_username_key]['end_date']
        current_end_datetime = validate_date(current_end_date_str)
        if current_end_datetime and current_end_datetime >= datetime.datetime.now():
            client.replyMessage(
                Message(
                    text=f"@member User {existing_username_key} hiện đang còn hạn đến {current_end_date_str}. Nếu muốn cập nhật, hãy dùng lệnh nsbot lại hoặc add thêm ngày với addusbot.",
                    mention=Mention(author_id, length=len("@member"), offset=0)
                ),
                message_object, thread_id, thread_type, ttl=12000
            )
            return
        del user_data[existing_username_key]


    user_data[username_to_add] = {
        'start_date': start_date,
        'end_date': end_date,
        'added_by': author_id,
        'user_id': user_id_to_add,
        'thread_id': thread_id,
        'added_at': datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    }
    write_user_data(user_data)
    logging.info(f"[handle_usbot_command] Added user {username_to_add} with end_date {end_date}")

    client.replyMessage(
        Message(
            text=f"@member Đã set thuê bot từ {start_date} đến {end_date} cho {username_to_add}, ổn áp vcl",
            mention=Mention(author_id, length=len("@member"), offset=0)
        ),
        message_object, thread_id, thread_type, ttl=720000
    )

def handle_addusbot_command(message, message_object, thread_id, thread_type, author_id, client):
    if not is_primary_admin(author_id):
        client.replyMessage(
            Message(
                text="Chỉ admin mới được dùng lệnh này.",
                mention=Mention(author_id, length=len("@member"), offset=0)
            ),
            message_object, thread_id, thread_type, ttl=12000
        )
        return

    init_user_data()
    args = message.strip().split()

    target_name_input = None
    days_to_add = None

    if thread_type == ThreadType.USER:
        if len(args) < 2 or not args[1].isdigit():
            client.replyMessage(
                Message(
                    text="@member Dùng sai rồi bro, cú pháp: addusbot <số ngày thêm> (nhắn riêng)",
                    mention=Mention(author_id, length=len("@member"), offset=0)
                ),
                message_object, thread_id, thread_type, ttl=12000
            )
            return
        target_name_input = get_user_name(client, author_id)
        days_to_add = int(args[1])
    else:
        if len(args) < 3 or not args[-1].isdigit():
            client.replyMessage(
                Message(
                    text="@member Dùng sai rồi bro, cú pháp: addusbot <tên user> <số ngày thêm> (trong nhóm)",
                    mention=Mention(author_id, length=len("@member"), offset=0)
                ),
                message_object, thread_id, thread_type, ttl=12000
            )
            return
        days_to_add = int(args[-1])
        target_name_input = " ".join(args[1:-1]).strip()

    if target_name_input == 'Không xác định' or not target_name_input:
        client.replyMessage(
            Message(
                text="@member Không lấy được tên user hoặc tên user trống bro, thử lại đi",
                mention=Mention(author_id, length=len("@member"), offset=0)
            ),
            message_object, thread_id, thread_type, ttl=12000
        )
        return

    if days_to_add <= 0:
        client.replyMessage(
            Message(
                text="@member Số ngày thêm phải là số dương nha bro.",
                mention=Mention(author_id, length=len("@member"), offset=0)
            ),
            message_object, thread_id, thread_type, ttl=12000
        )
        return

    user_data = read_user_data()
    username_key_in_data = find_user_by_normalized_name(user_data, target_name_input)

    if not username_key_in_data:
        client.replyMessage(
            Message(
                text=f"@member User '{target_name_input}' không có trong danh sách thuê bot bro. Dùng nsbot để thêm mới trước nha.",
                mention=Mention(author_id, length=len("@member"), offset=0)
            ),
            message_object, thread_id, thread_type, ttl=12000
        )
        return

    info = user_data[username_key_in_data]

    current_end_date_str = info['end_date']
    current_end_datetime = validate_date(current_end_date_str)

    if not current_end_datetime:
        client.replyMessage(
            Message(
                text=f"@member Lỗi: Ngày hết hạn của {username_key_in_data} không hợp lệ. Vui lòng cập nhật lại.",
                mention=Mention(author_id, length=len("@member"), offset=0)
            ),
            message_object, thread_id, thread_type, ttl=12000
        )
        return

    new_end_datetime = current_end_datetime
    if current_end_datetime.date() < datetime.datetime.now().date():
        new_end_datetime = datetime.datetime.now()
        logging.info(f"[handle_addusbot_command] User {username_key_in_data} was expired. Resetting expiry to today + {days_to_add} days.")


    new_end_datetime += datetime.timedelta(days=days_to_add)
    new_end_date_str = new_end_datetime.strftime('%d/%m/%Y')

    user_data[username_key_in_data]['end_date'] = new_end_date_str
    write_user_data(user_data)
    logging.info(f"[handle_addusbot_command] Added {days_to_add} days to {username_key_in_data}. New end_date: {new_end_date_str}")

    client.replyMessage(
        Message(
            text=f"@member Đã thêm {days_to_add} ngày cho {username_key_in_data}. Hạn mới là {new_end_date_str}. Ngon lành cành đào!",
            mention=Mention(author_id, length=len("@member"), offset=0)
        ),
        message_object, thread_id, thread_type, ttl=720000
    )

def handle_rmusbot_command(message, message_object, thread_id, thread_type, author_id, client):
    if not is_primary_admin(author_id):
        client.replyMessage(
            Message(
                text="Chỉ admin mới được dùng lệnh này.",
                mention=Mention(author_id, length=len("@member"), offset=0)
            ),
            message_object, thread_id, thread_type, ttl=12000
        )
        return

    init_user_data()
    args = message.strip().split()

    target_name_input = None

    if thread_type == ThreadType.USER:
        target_name_input = get_user_name(client, author_id)
        if len(args) > 1:
            client.replyMessage(
                Message(
                    text="@member Dùng sai rồi bro, cú pháp: rmusbot (nhắn riêng để xóa chính bạn) hoặc rmusbot <tên user> (trong nhóm)",
                    mention=Mention(author_id, length=len("@member"), offset=0)
                ),
                message_object, thread_id, thread_type, ttl=12000
            )
            return
    else:
        if len(args) < 2:
            client.replyMessage(
                Message(
                    text="@member Dùng sai rồi bro, cú pháp: rmusbot <tên user> (trong nhóm)",
                    mention=Mention(author_id, length=len("@member"), offset=0)
                ),
                message_object, thread_id, thread_type, ttl=12000
            )
            return
        target_name_input = " ".join(args[1:]).strip()

    if target_name_input == 'Không xác định' or not target_name_input:
        client.replyMessage(
            Message(
                text="@member Không lấy được tên user hoặc tên user trống bro, thử lại đi",
                mention=Mention(author_id, length=len("@member"), offset=0)
            ),
            message_object, thread_id, thread_type, ttl=12000
        )
        return

    user_data = read_user_data()
    username_key_in_data = find_user_by_normalized_name(user_data, target_name_input)

    if not username_key_in_data:
        client.replyMessage(
            Message(
                text=f"@member User '{target_name_input}' không có trong danh sách thuê bot bro, không xóa được.",
                mention=Mention(author_id, length=len("@member"), offset=0)
            ),
            message_object, thread_id, thread_type, ttl=12000
        )
        return

    del user_data[username_key_in_data]
    write_user_data(user_data)
    logging.info(f"[handle_rmusbot_command] Removed user {username_key_in_data} from data.")

    client.replyMessage(
        Message(
            text=f"@member Đã xóa user {username_key_in_data} khỏi danh sách thuê bot. Xong việc!",
            mention=Mention(author_id, length=len("@member"), offset=0)
        ),
        message_object, thread_id, thread_type, ttl=720000
    )

def handle_rmallusbot_command(message, message_object, thread_id, thread_type, author_id, client):
    if not is_primary_admin(author_id):
        client.replyMessage(
            Message(
                text="Chỉ admin mới được dùng lệnh này.",
                mention=Mention(author_id, length=len("@member"), offset=0)
            ),
            message_object, thread_id, thread_type, ttl=12000
        )
        return

    init_user_data()
    args = message.strip().split()

    if len(args) < 2 or args[1].lower() != "confirm":
        client.replyMessage(
            Message(
                text="@member Lệnh này sẽ xóa TẤT CẢ user thuê bot. Để xác nhận, dùng: rmallusbot confirm",
                mention=Mention(author_id, length=len("@member"), offset=0)
            ),
            message_object, thread_id, thread_type, ttl=12000
        )
        return

    user_data = read_user_data()
    if not user_data:
        client.replyMessage(
            Message(
                text="@member Không có user nào trong danh sách thuê bot để xóa cả bro.",
                mention=Mention(author_id, length=len("@member"), offset=0)
            ),
            message_object, thread_id, thread_type, ttl=12000
        )
        return

    write_user_data({})
    logging.info(f"[handle_rmallusbot_command] All user rental data has been cleared by admin {author_id}.")

    client.replyMessage(
        Message(
            text="@member Đã xóa TẤT CẢ user khỏi danh sách thuê bot. Sạch sẽ luôn!",
            mention=Mention(author_id, length=len("@member"), offset=0)
        ),
        message_object, thread_id, thread_type, ttl=720000
    )

def handle_listusbot_command(message, message_object, thread_id, thread_type, author_id, client):
    if not is_primary_admin(author_id):
        client.replyMessage(
            Message(
                text="Chỉ admin mới được dùng lệnh này.",
                mention=Mention(author_id, length=len("@member"), offset=0)
            ),
            message_object, thread_id, thread_type, ttl=12000
        )
        return

    init_user_data()
    user_data = read_user_data()

    if not user_data:
        client.replyMessage(
            Message(
                text="@member Chưa có ai thuê bot cả bro, buồn vcl",
                mention=Mention(author_id, length=len("@member"), offset=0)
            ),
            message_object, thread_id, thread_type, ttl=12000
        )
        return

    response = "@member Danh sách user thuê bot:\n"
    today = datetime.datetime.now()

    sorted_users = sorted(user_data.items(), key=lambda item: validate_date(item[1]['end_date']) or datetime.datetime.max)

    for username, info in sorted_users:
        end_date = validate_date(info['end_date'])
        remaining_days = get_remaining_days(info['end_date'])

        status_text = ""
        if end_date:
            if end_date.date() < today.date():
                status_text = "Đã hết hạn"
            elif end_date.date() == today.date():
                status_text = "Hết hạn hôm nay"
            elif remaining_days is not None:
                status_text = f"Còn {remaining_days} ngày"
        else:
            status_text = "Lỗi ngày hết hạn"

        response += f"- {username}: Hết hạn {info['end_date']} ({status_text})\n"

    client.replyMessage(
        Message(text=response, mention=Mention(author_id, length=len("@member"), offset=0)),
        message_object, thread_id, thread_type, ttl=720000
    )

def handle_checkusbot_command(message, message_object, thread_id, thread_type, author_id, client):
    if not is_primary_admin(author_id):
        client.replyMessage(
            Message(
                text="Chỉ admin mới được dùng lệnh này.",
                mention=Mention(author_id, length=len("@member"), offset=0)
            ),
            message_object, thread_id, thread_type, ttl=12000
        )
        return

    init_user_data()
    args = message.strip().split()

    target_name_input = None
    if thread_type == ThreadType.USER:
        if len(args) > 1:
            client.replyMessage(
                Message(
                    text="@member Dùng sai rồi bro, cú pháp: checkuser (nhắn riêng để kiểm tra chính bạn) hoặc checkuser <tên user> (trong nhóm)",
                    mention=Mention(author_id, length=len("@member"), offset=0)
                ),
                message_object, thread_id, thread_type, ttl=12000
            )
            return
        target_name_input = get_user_name(client, author_id)
    else:
        if len(args) < 2:
            client.replyMessage(
                Message(
                    text="@member Dùng sai rồi bro, cú pháp: checkuser <tên user> (trong nhóm) hoặc checkuser (nhắn riêng)",
                    mention=Mention(author_id, length=len("@member"), offset=0)
                ),
                message_object, thread_id, thread_type, ttl=12000
            )
            return
        target_name_input = " ".join(args[1:]).strip()

    if target_name_input == 'Không xác định' or not target_name_input:
        client.replyMessage(
            Message(
                text="@member Không lấy được tên user hoặc tên user trống bro, thử lại đi",
                mention=Mention(author_id, length=len("@member"), offset=0)
            ),
            message_object, thread_id, thread_type, ttl=12000
        )
        return

    user_data = read_user_data()
    username_key_in_data = find_user_by_normalized_name(user_data, target_name_input)


    if not username_key_in_data:
        client.replyMessage(
            Message(
                text=f"@member User '{target_name_input}' không có trong danh sách thuê bot bro, check lại đi",
                mention=Mention(author_id, length=len("@member"), offset=0)
            ),
            message_object, thread_id, thread_type, ttl=12000
        )
        return

    info = user_data[username_key_in_data]
    end_date = validate_date(info['end_date'])
    today = datetime.datetime.now()
    
    status_text = ""
    remaining_days_text = "N/A"
    if end_date:
        if end_date.date() < today.date():
            status_text = "Đã hết hạn"
        elif end_date.date() == today.date():
            status_text = "Hết hạn hôm nay"
        else:
            remaining_days = get_remaining_days(info['end_date'])
            status_text = "Còn hạn"
            if remaining_days is not None:
                remaining_days_text = f"{remaining_days} ngày"
    else:
        status_text = "Lỗi ngày hết hạn"

    added_by_name = get_user_name(client, info['added_by'])

    response = f"@member\n"
    response += f"Thông tin thuê bot của {username_key_in_data}:\n"
    response += f"- Thuê từ: {info['start_date']}\n"
    response += f"- Hết hạn: {info['end_date']}\n"
    response += f"- Số ngày còn lại: {remaining_days_text}\n"
    response += f"- Trạng thái: {status_text}\n"
    response += f"- Thêm bởi: {added_by_name}\n"
    response += f"- Thêm lúc: {info['added_at']}\n"

    client.replyMessage(
        Message(text=response, mention=Mention(author_id, length=len("@member"), offset=0)),
        message_object, thread_id, thread_type, ttl=720000
    )

def start_expiry_check(client):
    thread = threading.Thread(target=check_expiry_and_notify, args=(client,), daemon=True)
    thread.start()
    logging.info("[start_expiry_check] Expiry check thread started")

def PTA():
    return {
        'nsbot': handle_usbot_command,
        'lusbot': handle_listusbot_command,
        'checkuser': handle_checkusbot_command,
        'addusbot': handle_addusbot_command,
        'rmusbot': handle_rmusbot_command,
        'rmallusbot': handle_rmallusbot_command
    }