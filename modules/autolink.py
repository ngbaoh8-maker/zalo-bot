import json
import os
import time
import threading
from zlapi.models import *
from config import ADMIN, PREFIX
from datetime import datetime

des = {
    'version': '1.0.1',
    'credits': "ngbao",
    'description': 'Tự động gửi link quảng cáo.',
    'power': 'Quản trị viên Bot'
}

AUTOLINK_CONFIG_PATH = 'modules/cache/autolink_config.json'
AUTOLINK_STATUS_PATH = 'modules/cache/autolink_status.json'
AUTOLINK_DISABLE_PATH = 'modules/cache/autolink_disable.json'

json_lock = threading.Lock()

def is_admin(author_id):
    return author_id == ADMIN

def load_json(path, default):
    with json_lock:
        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            return default
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"[AUTOLINK] Lỗi định dạng JSON {path}: {e}. Khôi phục cài đặt mặc định.")
            return default
        except Exception as e:
            print(f"[AUTOLINK] Lỗi đọc JSON {path}: {e}")
            return default

def save_json(path, data):
    with json_lock:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[AUTOLINK] Lỗi ghi JSON {path}: {e}")

def get_user_name(client, author_id):
    try:
        user_info = client.fetchUserInfo(author_id)
        author_info = user_info.changed_profiles.get(author_id, {}) if user_info and user_info.changed_profiles else {}
        return author_info.get('zaloName', 'Không xác định')
    except Exception as e:
        print(f"[AUTOLINK] Lỗi lấy tên người dùng {author_id}: {e}")
        return 'Không xác định'

def autolink_broadcast(client):
    config = load_json(AUTOLINK_CONFIG_PATH, {'links': []})
    status = load_json(AUTOLINK_STATUS_PATH, {'on': False, 'interval_min': 60, 'last_autolink_time': 0})
    autolink_disable = load_json(AUTOLINK_DISABLE_PATH, [])

    if not status.get('on', False) or not config.get('links'):
        print("[AUTOLINK] Không gửi: autolink đang tắt hoặc chưa có link nào được cấu hình.")
        return

    try:
        all_groups = list(client.fetchAllGroups().gridVerMap.keys())
    except Exception as e:
        print(f"[AUTOLINK] Lỗi lấy danh sách nhóm: {e}")
        return

    processed_groups = set()
    failed, disabled, success = [], [], []

    for group_id in all_groups:
        if group_id in processed_groups:
            continue
        if group_id in autolink_disable:
            disabled.append(group_id)
            continue

        try:
            for link_data in config['links']:
                linkUrl = link_data.get('linkUrl')
                title = link_data.get('title', '')
                thumbnailUrl = link_data.get('thumbnailUrl', '')
                domainUrl = link_data.get('domainUrl', '')
                desc = link_data.get('desc', '')
                message_text = link_data.get('message_text', '')

                if not linkUrl:
                    print(f"[AUTOLINK] Bỏ qua link không có URL hợp lệ trong cấu hình cho nhóm {group_id}.")
                    continue

                client.sendLink(
                    linkUrl=linkUrl,
                    title=title,
                    thread_id=group_id,
                    thread_type=ThreadType.GROUP,
                    thumbnailUrl=thumbnailUrl,
                    domainUrl=domainUrl,
                    desc=desc,
                    message=Message(text=message_text) if message_text else None,
                    ttl=400000
                )
                time.sleep(2)

            success.append(group_id)
            processed_groups.add(group_id)
            time.sleep(2)
        except Exception as e:
            failed.append(f"{group_id} (Lỗi: {e})")
            processed_groups.add(group_id)
            
    if success:
        status['last_autolink_time'] = int(time.time())
        save_json(AUTOLINK_STATUS_PATH, status)

    print(f"[AUTOLINK] Gửi thành công: {len(success)}, thất bại: {len(failed)}, bị tắt: {len(disabled)}")

def autolink_scheduler(client):
    print("[AUTOLINK] Scheduler đã khởi động.")
    last_status_state = None
    while True:
        try:
            status = load_json(AUTOLINK_STATUS_PATH, {'on': False, 'interval_min': 60, 'last_autolink_time': 0})
            current_on_state = status.get('on', False)

            if last_status_state is None or last_status_state != current_on_state:
                print(f"[AUTOLINK] Trạng thái autolink: {'Đang BẬT' if current_on_state else 'Đang TẮT'}.")
                last_status_state = current_on_state

            if current_on_state:
                interval = int(status.get('interval_min', 60)) * 60
                last_autolink_time = status.get('last_autolink_time', 0)
                current_time = int(time.time())
                time_since_last_autolink = current_time - last_autolink_time

                if time_since_last_autolink >= interval:
                    print("[AUTOLINK] Đã đến lúc gửi link tự động.")
                    autolink_broadcast(client)
                    print(f"[AUTOLINK] Hoàn tất gửi. Ngủ {interval // 60} phút.")
                    time.sleep(interval)
                else:
                    time_to_wait = interval - time_since_last_autolink
                    print(f"[AUTOLINK] Chờ {time_to_wait // 60} phút nữa để gửi link tự động.")
                    time.sleep(time_to_wait)
            else:
                time.sleep(10)
        except Exception as e:
            print(f"[AUTOLINK] Lỗi trong scheduler: {e}")
            time.sleep(30)

def start_autolink_scheduler(client):
    t = threading.Thread(target=autolink_scheduler, args=(client,), daemon=True)
    t.start()
    print("[AUTOLINK] Đã khởi động luồng scheduler.")

def handle_autolink_command(message, message_object, thread_id, thread_type, author_id, client):
    parts = message.strip().split()
    
    if not is_admin(author_id):
        name = get_user_name(client, author_id)
        rest_text = "Bạn không có quyền sử dụng lệnh này. 🚦"
        msg = f"{name}\n➜{rest_text}"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
        ])
        client.replyMessage(Message(text=msg, style=styles),
                            message_object, thread_id, thread_type, ttl=30000)
        return

    name = get_user_name(client, author_id)

    def send_styled_reply(text_content, ttl=30000):
        msg = f"{name}\n➜{text_content}"
        styles = MultiMsgStyle([
            MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
        ])
        client.replyMessage(Message(text=msg, style=styles),
                            message_object, thread_id, thread_type, ttl=ttl)

    def get_primary_link_data(config):
        return config['links'][0] if config and config.get('links') and config['links'] else None

    if len(parts) < 2:
        send_styled_reply(
            f"Hướng dẫn sử dụng lệnh {PREFIX}atlk:\n"
            f"  ➜ {PREFIX}atlk on - Bật tự động gửi link\n"
            f"  ➜ {PREFIX}atlk off - Tắt tự động gửi link\n"
            f"  ➜ {PREFIX}atlk addlink <link_url> <title> <thumbnail_url> <domain_url> <description> <message_text>\n"
            f"   (Dùng '_' cho khoảng trắng hoặc để trống, VD: {PREFIX}atlk addlink url _ _ _ _ Chào_mừng!)\n"
            f"  ➜ {PREFIX}atlk seturl <new_url> - Cập nhật URL link chính\n"
            f"  ➜ {PREFIX}atlk settitle <new_title> - Cập nhật tiêu đề link chính (dùng '_' cho khoảng trắng/trống)\n"
            f"  ➜ {PREFIX}atlk setdesc <new_description> - Cập nhật mô tả link chính (dùng '_' cho khoảng trắng/trống)\n"
            f"  ➜ {PREFIX}atlk setdomain <new_domain> - Cập nhật domain link chính (dùng '_' cho khoảng trắng/trống)\n"
            f"  ➜ {PREFIX}atlk setthumb <new_thumbnail_url> - Cập nhật ảnh thumbnail link chính (dùng '_' cho khoảng trắng/trống)\n"
            f"  ➜ {PREFIX}atlk interval <phút> - Đặt khoảng thời gian giữa các lần gửi\n"
            f"  ➜ {PREFIX}atlk disable [group_id] - Không gửi link vào nhóm\n"
            f"  ➜ {PREFIX}atlk enable [group_id] - Cho phép gửi link vào nhóm\n"
            f"  ➜ {PREFIX}atlk info - Xem thông tin cấu hình tự động gửi link và link hiện tại",
            ttl=120000
        )
        return

    cmd = parts[1].lower()
    config = load_json(AUTOLINK_CONFIG_PATH, {'links': []})
    status = load_json(AUTOLINK_STATUS_PATH, {'on': False, 'interval_min': 60, 'last_autolink_time': 0})
    autolink_disable = load_json(AUTOLINK_DISABLE_PATH, [])

    if cmd == 'addlink':
        cmd_and_action_len = len(parts[0]) + len(parts[1]) + 2

        if len(message) <= cmd_and_action_len:
            send_styled_reply(
                f"Lệnh {PREFIX}atlk addlink cần đủ 6 tham số.\n"
                f"📋 Cách dùng: {PREFIX}atlk addlink <link_url> <title> <thumbnail_url> <domain_url> <description> <message_text>\n"
                f"   (Dùng '_' cho khoảng trắng hoặc để trống)\n"
                f"Ví dụ: {PREFIX}atlk addlink https://zalo.me/g/hefryt116 Tham_gia_nhom https://imgur.com/example.jpg example.com Mo_ta_ngan_gon Day_la_tin_nhan_quang_cao"
            )
            return
        
        message_args_str = message.strip()[cmd_and_action_len:].strip()
        link_args = message_args_str.split(' ', 5)

        if len(link_args) < 6:
            send_styled_reply(
                f"Lệnh {PREFIX}atlk addlink cần đủ 6 tham số.\n"
                f"📋 Cách dùng: {PREFIX}atlk addlink <link_url> <title> <thumbnail_url> <domain_url> <description> <message_text>\n"
                f"   (Dùng '_' cho khoảng trắng hoặc để trống)\n"
                f"Ví dụ: {PREFIX}atlk addlink https://zalo.me/g/hefryt116 Tham_gia_nhom https://imgur.com/example.jpg example.com Mo_ta_ngan_gon Day_la_tin_nhan_quang_cao"
            )
            return

        linkUrl = link_args[0]
        title = link_args[1].replace('_', ' ') if link_args[1] != '_' else ''
        thumbnailUrl = link_args[2].replace('_', ' ') if link_args[2] != '_' else ''
        domainUrl = link_args[3].replace('_', ' ') if link_args[3] != '_' else ''
        desc = link_args[4].replace('_', ' ') if link_args[4] != '_' else ''
        message_text = link_args[5].replace('_', ' ') if link_args[5] != '_' else ''

        if not linkUrl.startswith(('http://', 'https://', 'zalo://')):
            send_styled_reply("URL link không hợp lệ. Vui lòng bắt đầu bằng http://, https:// hoặc zalo:// 🚦")
            return

        new_link = {
            'linkUrl': linkUrl,
            'title': title,
            'thumbnailUrl': thumbnailUrl,
            'domainUrl': domainUrl,
            'desc': desc,
            'message_text': message_text
        }

        found = False
        for i, item in enumerate(config['links']):
            if item.get('linkUrl') == linkUrl:
                config['links'][i] = new_link
                found = True
                break
        if not found:
            config['links'].append(new_link)

        save_json(AUTOLINK_CONFIG_PATH, config)
        send_styled_reply(f"đã {'cập nhật' if found else 'thêm'} link quảng cáo: {linkUrl}! 🔗")
        return

    def update_primary_link_field(field_name, new_value, value_type="text"):
        primary_link = get_primary_link_data(config)
        if not primary_link:
            send_styled_reply(f"Chưa có link quảng cáo nào được cấu hình. Vui lòng dùng '{PREFIX}atlk addlink' để thêm link trước. 📋")
            return
        
        processed_value = new_value.replace('_', ' ') if new_value != '_' else ''
        if value_type == "url" and not processed_value.startswith(('http://', 'https://', 'zalo://')) and processed_value != '':
            send_styled_reply(f"URL {field_name} không hợp lệ. Vui lòng bắt đầu bằng http://, https:// hoặc zalo:// (hoặc '_' để trống). 🚦")
            return

        primary_link[field_name] = processed_value
        config['links'][0] = primary_link
        save_json(AUTOLINK_CONFIG_PATH, config)
        send_styled_reply(f"đã cập nhật {field_name.replace('Url', ' URL').replace('desc', 'mô tả').replace('title', 'tiêu đề').replace('message_text', 'tin nhắn')}: {processed_value} cho link chính! ✅")

    if cmd == 'seturl':
        if len(parts) < 3:
            send_styled_reply(f"Lệnh {PREFIX}atlk seturl cần URL mới.\n"
                               f"📋 Cách dùng: {PREFIX}atlk seturl <new_url>")
            return
        new_url = parts[2]
        update_primary_link_field('linkUrl', new_url, "url")
        return

    if cmd == 'settitle':
        if len(parts) < 3:
            send_styled_reply(f"Lệnh {PREFIX}atlk settitle cần tiêu đề mới.\n"
                               f"📋 Cách dùng: {PREFIX}atlk settitle <new_title> (dùng '_' cho khoảng trắng/trống)")
            return
        new_title = ' '.join(parts[2:])
        update_primary_link_field('title', new_title)
        return
    
    if cmd == 'setdesc':
        if len(parts) < 3:
            send_styled_reply(f"Lệnh {PREFIX}atlk setdesc cần mô tả mới.\n"
                               f"📋 Cách dùng: {PREFIX}atlk setdesc <new_description> (dùng '_' cho khoảng trắng/trống)")
            return
        new_desc = ' '.join(parts[2:])
        update_primary_link_field('desc', new_desc)
        return

    if cmd == 'setdomain':
        if len(parts) < 3:
            send_styled_reply(f"Lệnh {PREFIX}atlk setdomain cần domain mới.\n"
                               f"📋 Cách dùng: {PREFIX}atlk setdomain <new_domain> (dùng '_' cho khoảng trắng/trống)")
            return
        new_domain = ' '.join(parts[2:])
        update_primary_link_field('domainUrl', new_domain)
        return

    if cmd == 'setthumb':
        if len(parts) < 3:
            send_styled_reply(f"Lệnh {PREFIX}atlk setthumb cần URL thumbnail mới.\n"
                               f"📋 Cách dùng: {PREFIX}atlk setthumb <new_thumbnail_url> (dùng '_' cho khoảng trắng/trống)")
            return
        new_thumb = parts[2]
        update_primary_link_field('thumbnailUrl', new_thumb, "url")
        return
        
    if cmd == 'removelink':
        if len(parts) < 3:
            send_styled_reply(f"Lệnh {PREFIX}atlk removelink cần URL link cần xóa.\n"
                               f"📋 Cách dùng: {PREFIX}atlk removelink <link_url>\n"
                               f"Ví dụ: {PREFIX}atlk removelink https://zalo.me/g/hefryt116")
            return
        
        link_to_remove = parts[2]
        original_len = len(config['links'])
        config['links'] = [link for link in config['links'] if link.get('linkUrl') != link_to_remove]
        
        if len(config['links']) < original_len:
            save_json(AUTOLINK_CONFIG_PATH, config)
            send_styled_reply(f"đã xóa link quảng cáo: {link_to_remove}! 🗑️")
        else:
            send_styled_reply(f"Không tìm thấy link: {link_to_remove} để xóa. 🚦")
        return
        
    if cmd == 'listlinks':
        if not config['links']:
            send_styled_reply("Chưa có link quảng cáo nào được cấu hình. 📋")
            return
        
        link_list_str = "Danh sách link quảng cáo đã lưu:\n"
        for i, link in enumerate(config['links']):
            link_list_str += (
                f"{i+1}. URL: {link.get('linkUrl', 'N/A')}\n"
                f"   Tiêu đề: '{link.get('title', '[Trống]')}'\n"
                f"   Thumbnail: '{link.get('thumbnailUrl', '[Trống]')}'\n"
                f"   Domain: '{link.get('domainUrl', '[Trống]')}'\n"
                f"   Mô tả: '{link.get('desc', '[Trống]')}'\n"
                f"   Tin nhắn: '{link.get('message_text', '[Trống]')}'\n"
                f"---------------------------------------------------\n"
            )
        send_styled_reply(link_list_str, ttl=120000)
        return

    if cmd == 'interval':
        if len(parts) < 3:
            send_styled_reply(f"Lệnh {PREFIX}atlk interval cần số phút.\n"
                               f"📋 Cách dùng: {PREFIX}atlk interval <phút>\n"
                               f"Ví dụ: {PREFIX}atlk interval 60")
            return
        try:
            interval = int(parts[2])
            if interval <= 0:
                send_styled_reply("Khoảng thời gian phải là số nguyên dương. 🚦")
                return
            status['interval_min'] = interval
            save_json(AUTOLINK_STATUS_PATH, status)
            send_styled_reply(f"đã đặt khoảng thời gian gửi link tự động là {interval} phút! ⏰")
        except ValueError:
            send_styled_reply("Vui lòng nhập một số nguyên hợp lệ cho khoảng thời gian. 🚦")
        return

    if cmd == 'disable':
        group_id = parts[2] if len(parts) >= 3 else thread_id
        if group_id not in autolink_disable:
            autolink_disable.append(group_id)
            save_json(AUTOLINK_DISABLE_PATH, autolink_disable)
            send_styled_reply(f"đã tắt tự động gửi link cho nhóm {group_id}! 🚫")
        else:
            send_styled_reply(f"Nhóm {group_id} đã được tắt tự động gửi link trước đó. 🚦")
        return

    if cmd == 'enable':
        group_id = parts[2] if len(parts) >= 3 else thread_id
        if group_id in autolink_disable:
            autolink_disable.remove(group_id)
            save_json(AUTOLINK_DISABLE_PATH, autolink_disable)
            send_styled_reply(f"đã bật lại tự động gửi link cho nhóm {group_id}! ✅")
        else:
            send_styled_reply(f"Nhóm {group_id} chưa từng bị tắt tự động gửi link. 🚦")
        return

    if cmd == 'on':
        current_state = status.get('on', False)
        if current_state:
            send_styled_reply("Tự động gửi link đã được bật sẵn rồi! 🚦")
        else:
            status['on'] = True
            save_json(AUTOLINK_STATUS_PATH, status)
            send_styled_reply("Đã bật tự động gửi link! 🚀")
        return

    elif cmd == 'off':
        current_state = status.get('on', False)
        if not current_state:
            send_styled_reply("Tự động gửi link đã được tắt rồi! 🚦")
        else:
            status['on'] = False
            save_json(AUTOLINK_STATUS_PATH, status)
            send_styled_reply("Đã tắt tự động gửi link! 💤")
        return

    if cmd == 'info':
        try:
            groups = list(client.fetchAllGroups().gridVerMap.keys())
        except Exception as e:
            groups = []
            print(f"[AUTOLINK] Lỗi lấy danh sách nhóm khi xem info: {e}")

        last_autolink_time = status.get('last_autolink_time', 0)
        last_autolink_str = (
            datetime.fromtimestamp(last_autolink_time).strftime("%H:%M:%S, %A, ngày %d tháng %m năm %Y")
            if last_autolink_time > 0
            else 'Chưa có'
        )
        day_map = {
            'Monday': 'Thứ Hai', 'Tuesday': 'Thứ Ba', 'Wednesday': 'Thứ Tư',
            'Thursday': 'Thứ Năm', 'Friday': 'Thứ Sáu', 'Saturday': 'Thứ Bảy', 'Sunday': 'Chủ Nhật'
        }
        if last_autolink_time > 0:
            day_name = datetime.fromtimestamp(last_autolink_time).strftime("%A")
            last_autolink_str = last_autolink_str.replace(day_name, day_map.get(day_name, day_name))

        links_count = len(config.get('links', []))
        
        info_text = (
            f"Cấu hình tự động gửi link:\n"
            f"➜ Trạng thái: {'✅ Bật' if status.get('on', False) else '❌ Tắt'}\n"
            f"➜ Khoảng thời gian: {status.get('interval_min', 60)} phút\n"
            f"➜ Số lượng link đã lưu: {links_count}\n"
            f"➜ Số nhóm hiện tại: {len(groups)}\n"
            f"➜ Số nhóm bị tắt: {len(autolink_disable)}\n"
            f"➜ Lần gửi cuối: {last_autolink_str}\n"
        )
        
        primary_link = get_primary_link_data(config)
        if primary_link:
            info_text += (
                f"\nThông tin link chính hiện tại:\n"
                f"➜ URL: {primary_link.get('linkUrl', '[Trống]')}\n"
                f"➜ Tiêu đề: {primary_link.get('title', '[Trống]')}\n"
                f"➜ Mô tả: {primary_link.get('desc', '[Trống]')}\n"
                f"➜ Domain: {primary_link.get('domainUrl', '[Trống]')}\n"
                f"➜ Thumbnail URL: {primary_link.get('thumbnailUrl', '[Trống]')}\n"
                f"➜ Tin nhắn kèm: {primary_link.get('message_text', '[Trống]')}"
            )
        else:
            info_text += "\nChưa có link quảng cáo nào được cấu hình."

        send_styled_reply(info_text, ttl=120000)
        return

    send_styled_reply(
        f"Lệnh không hợp lệ: {cmd}\n"
        f"📋 Hướng dẫn sử dụng lệnh {PREFIX}atlk:\n"
        f"  ➜ {PREFIX}atlk on - Bật tự động gửi link\n"
        f"  ➜ {PREFIX}atlk off - Tắt tự động gửi link\n"
        f"  ➜ {PREFIX}atlk addlink <link_url> <title> <thumbnail_url> <domain_url> <description> <message_text>\n"
        f"   (Dùng '_' cho khoảng trắng hoặc để trống, VD: {PREFIX}atlk addlink url _ _ _ _ Chào_mừng!)\n"
        f"  ➜ {PREFIX}atlk seturl <new_url> - Cập nhật URL link chính\n"
        f"  ➜ {PREFIX}atlk settitle <new_title> - Cập nhật tiêu đề link chính (dùng '_' cho khoảng trắng/trống)\n"
        f"  ➜ {PREFIX}atlk setdesc <new_description> - Cập nhật mô tả link chính (dùng '_' cho khoảng trắng/trống)\n"
        f"  ➜ {PREFIX}atlk setdomain <new_domain> - Cập nhật domain link chính (dùng '_' cho khoảng trắng/trống)\n"
        f"  ➜ {PREFIX}atlk setthumb <new_thumbnail_url> - Cập nhật ảnh thumbnail link chính (dùng '_' cho khoảng trắng/trống)\n"
        f"  ➜ {PREFIX}atlk interval <phút> - Đặt khoảng thời gian giữa các lần gửi\n"
        f"  ➜ {PREFIX}atlk disable [group_id] - Không gửi link vào nhóm\n"
        f"  ➜ {PREFIX}atlk enable [group_id] - Cho phép gửi link vào nhóm\n"
        f"  ➜ {PREFIX}atlk info - Xem thông tin cấu hình tự động gửi link và link hiện tại",
        ttl=120000
    )

def PTA():
    return {
        'atlk': handle_autolink_command,
    }